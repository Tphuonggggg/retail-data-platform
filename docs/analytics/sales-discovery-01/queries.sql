-- Supplementary Sales discovery queries; %(pin)s is bound by analyze.py.
-- The 16 shared reader queries are maintained in powerbi/validation.sql.

-- Q10 Exploratory seasonality, normalize year levels and exclude incomplete calendar years
WITH y AS (SELECT extract(year FROM sales_month)::integer AS year,avg(sales_amount) avg_month
 FROM sales_marts.mart_sales_monthly WHERE _capture_id=%(pin)s GROUP BY 1
 HAVING count(*)=12 AND bool_and(full_calendar_month)),
 m AS (SELECT extract(month FROM s.sales_month)::integer AS month,y.year,s.sales_amount/y.avg_month normalized_index
 FROM sales_marts.mart_sales_monthly s JOIN y ON y.year=extract(year FROM s.sales_month)
 WHERE s._capture_id=%(pin)s)
SELECT month,count(*) annual_observations,avg(normalized_index) average_year_normalized_index,
 min(normalized_index) minimum_index,max(normalized_index) maximum_index,
 array_agg(year ORDER BY year) years FROM m GROUP BY month ORDER BY month;

-- Q12 Observed monthly volatility; descriptive, confounded by trend and month length
SELECT extract(year FROM sales_month)::integer AS year,count(*) months,
 avg(sales_amount) average_month_sales,stddev_samp(sales_amount) sample_sd_month_sales,
 stddev_samp(sales_amount)/nullif(avg(sales_amount),0) coefficient_of_variation,
 min(sales_amount) min_month_sales,max(sales_amount) max_month_sales
FROM sales_marts.mart_sales_monthly WHERE _capture_id=%(pin)s GROUP BY 1 ORDER BY 1;

-- Q16 Invoice amount outliers: exploratory Tukey rule, NOT a DQ exclusion
WITH i AS (SELECT source_invoice_id,sum(invoiced_sales_before_tax) sales,count(*) lines
 FROM dw_core.fact_invoice_line WHERE _capture_id=%(pin)s AND is_sales_eligible GROUP BY 1),
 p AS (SELECT percentile_cont(0.25) WITHIN GROUP(ORDER BY sales) q1,
 percentile_cont(0.75) WITHIN GROUP(ORDER BY sales) q3 FROM i)
SELECT count(*) invoices,min(sales) minimum,max(sales) maximum,
 percentile_cont(0.5) WITHIN GROUP(ORDER BY sales) median,
 percentile_cont(0.9) WITHIN GROUP(ORDER BY sales) p90,
 percentile_cont(0.95) WITHIN GROUP(ORDER BY sales) p95,
 percentile_cont(0.99) WITHIN GROUP(ORDER BY sales) p99,
 min(q3+1.5*(q3-q1)) tukey_upper,
 count(*) FILTER(WHERE sales>q3+1.5*(q3-q1)) invoices_above_tukey_upper,
 count(*) FILTER(WHERE sales<=0) nonpositive_invoices,
 count(*) FILTER(WHERE lines=1) single_line_invoices
FROM i CROSS JOIN p;

-- Q18 Backorder links explain structural caveats, NOT fulfillment completion
WITH i AS (SELECT DISTINCT source_order_id FROM dw_intermediate.int_invoice_header
 WHERE _capture_id=%(pin)s AND is_sales_eligible AND source_order_id IS NOT NULL),
 o AS (SELECT s.* FROM dw_staging.stg_sales_orders s JOIN dw_intermediate.int_order_header h
 ON h.source_order_id=s.order_id AND h._capture_id=s._capture_id
 WHERE s._capture_id=%(pin)s AND h.is_order_eligible)
SELECT count(*) FILTER(WHERE direct.source_order_id IS NULL) orders_without_direct_invoice,
 count(*) FILTER(WHERE direct.source_order_id IS NULL AND o.backorder_order_id IS NOT NULL) unmatched_with_backorder_link,
 count(*) FILTER(WHERE direct.source_order_id IS NULL AND child.source_order_id IS NOT NULL) unmatched_with_linked_order_invoiced,
 count(*) FILTER(WHERE direct.source_order_id IS NULL AND o.backorder_order_id IS NULL) unmatched_without_backorder_link,
 min(o.order_date) FILTER(WHERE direct.source_order_id IS NULL) first_unmatched_order_date,
 max(o.order_date) FILTER(WHERE direct.source_order_id IS NULL) last_unmatched_order_date,
 count(*) FILTER(WHERE direct.source_order_id IS NULL AND o.order_date<(SELECT date_trunc('month',max(invoice_date)) FROM dw_intermediate.int_invoice_header WHERE _capture_id=%(pin)s)) unmatched_before_last_invoice_month
FROM o LEFT JOIN i direct ON direct.source_order_id=o.order_id LEFT JOIN i child ON child.source_order_id=o.backorder_order_id;

-- Q20 Independent by-month reconciliation from facts/headers to marts; each population aggregated separately
WITH f AS (SELECT date_trunc('month',invoice_date)::date m,sum(invoiced_sales_before_tax) sales,sum(quantity) units
 FROM dw_core.fact_invoice_line WHERE _capture_id=%(pin)s AND is_sales_eligible GROUP BY 1),
 h AS (SELECT date_trunc('month',invoice_date)::date m,count(*) invoices FROM dw_intermediate.int_invoice_header
 WHERE _capture_id=%(pin)s AND is_sales_eligible GROUP BY 1),
 actual AS (SELECT sales_month m,sales_amount sales,units_sold units,invoice_count invoices
 FROM sales_marts.mart_sales_monthly WHERE _capture_id=%(pin)s),
 expected AS (SELECT f.m,f.sales,f.units,h.invoices FROM f FULL JOIN h USING(m))
SELECT count(*) mismatch_rows FROM ((SELECT * FROM expected EXCEPT ALL SELECT * FROM actual)
 UNION ALL (SELECT * FROM actual EXCEPT ALL SELECT * FROM expected)) differences;

-- Q21 Incoming as well as outgoing backorder references for orders without direct invoice
WITH i AS MATERIALIZED (SELECT DISTINCT source_order_id FROM dw_intermediate.int_invoice_header
 WHERE _capture_id=%(pin)s AND is_sales_eligible AND source_order_id IS NOT NULL),
 u AS MATERIALIZED (SELECT o.source_order_id FROM dw_intermediate.int_order_header o
 WHERE o._capture_id=%(pin)s AND o.is_order_eligible
 EXCEPT SELECT source_order_id FROM i),
 incoming AS MATERIALIZED (SELECT DISTINCT backorder_order_id id FROM dw_staging.stg_sales_orders
 WHERE _capture_id=%(pin)s AND backorder_order_id IS NOT NULL),
 parent_invoiced AS MATERIALIZED (SELECT DISTINCT p.backorder_order_id id FROM dw_staging.stg_sales_orders p
 JOIN i ON i.source_order_id=p.order_id WHERE p._capture_id=%(pin)s AND p.backorder_order_id IS NOT NULL),
 has_lines AS MATERIALIZED (SELECT DISTINCT source_order_id id FROM dw_core.fact_order_line WHERE _capture_id=%(pin)s AND is_order_eligible)
SELECT count(*) unmatched_orders,count(incoming.id) referenced_as_backorder,
 count(parent_invoiced.id) referenced_by_order_with_invoice,
 count(*) FILTER(WHERE incoming.id IS NULL) no_incoming_link,
 count(*) FILTER(WHERE has_lines.id IS NULL) no_order_lines
FROM u LEFT JOIN incoming ON incoming.id=u.source_order_id
LEFT JOIN parent_invoiced ON parent_invoiced.id=u.source_order_id LEFT JOIN has_lines ON has_lines.id=u.source_order_id;

-- Q23 Validate the concentration of warning events, never automatically exclude them
WITH p AS (SELECT source_stock_item_id,count(*) all_lines,
 count(*) FILTER(WHERE source_reported_line_profit<0) negative_lines,
 coalesce(sum(source_reported_line_profit) FILTER(WHERE source_reported_line_profit<0),0) negative_profit_sum
 FROM dw_core.fact_invoice_line WHERE _capture_id=%(pin)s AND is_sales_eligible GROUP BY 1),
 r AS (SELECT *,row_number() OVER(ORDER BY negative_lines DESC,source_stock_item_id) rn FROM p)
SELECT sum(negative_lines) total_negative_lines,
 sum(negative_lines) FILTER(WHERE rn<=4) top4_negative_lines,
 sum(negative_lines) FILTER(WHERE rn<=4)::numeric/nullif(sum(negative_lines),0) top4_warning_share,
 count(*) FILTER(WHERE rn<=4 AND negative_lines=all_lines) top4_products_with_all_lines_negative,
 sum(negative_profit_sum) FILTER(WHERE rn<=4) top4_negative_source_profit,
 sum(negative_profit_sum) FILTER(WHERE rn<=4)/nullif(sum(negative_profit_sum),0) top4_negative_source_profit_share FROM r;

-- Q24 Calendar-adjusted exploratory month-of-year intensity, three complete years only
WITH a AS (SELECT date_trunc('month',sales_date)::date m,count(*) FILTER(WHERE invoice_count>0) active_days
 FROM sales_marts.mart_sales_daily WHERE _capture_id=%(pin)s GROUP BY 1),
 y AS (SELECT extract(year FROM s.sales_month) yr,sum(s.sales_amount) sales,sum(a.active_days) active_days
 FROM sales_marts.mart_sales_monthly s JOIN a ON a.m=s.sales_month WHERE s._capture_id=%(pin)s
 GROUP BY 1 HAVING count(*)=12 AND bool_and(s.full_calendar_month)),
 m AS (SELECT extract(month FROM s.sales_month)::integer AS month,y.yr,
 (s.sales_amount/nullif(a.active_days,0))/(y.sales/nullif(y.active_days,0)) active_day_normalized_index
 FROM sales_marts.mart_sales_monthly s JOIN a ON a.m=s.sales_month JOIN y ON y.yr=extract(year FROM s.sales_month)
 WHERE s._capture_id=%(pin)s)
SELECT month,count(*) annual_observations,avg(active_day_normalized_index) average_index,
 min(active_day_normalized_index) min_index,max(active_day_normalized_index) max_index
FROM m GROUP BY month ORDER BY month;

-- Q25 Current DQ distribution: count warning/invalid records against their own source population
SELECT source_object,dq_status,count(*) records,count(*) FILTER(WHERE has_warning) warning_records,
 count(*) FILTER(WHERE is_quarantined) quarantined_records,count(*) FILTER(WHERE is_valid) valid_records
FROM dq.record_status WHERE capture_id=%(pin)s GROUP BY 1,2 ORDER BY 1,2;
