-- ANALYTICS-DISCOVERY-01. SELECT-only; %(pin)s is bound by analyze.py.
-- S05 is invoiced sales before tax, not recognized revenue. Ratios are recomputed.

-- Q01 Coverage and approved headline measures
SELECT min(invoice_date) first_invoice_date,max(invoice_date) last_invoice_date,
 count(*) invoice_lines,count(distinct source_invoice_id) invoices_with_lines,
 sum(invoiced_sales_before_tax) sales,sum(tax_amount) tax,
 sum(invoice_amount_including_tax) including_tax,sum(quantity) source_units,
 count(*) FILTER(WHERE invoiced_sales_before_tax<0) negative_sales_lines,
 count(*) FILTER(WHERE invoiced_sales_before_tax=0) zero_sales_lines,
 (SELECT count(*) FROM dw_core.fact_invoice_line WHERE _capture_id=%(pin)s AND is_sales_eligible IS NOT TRUE) excluded_lines,
 (SELECT count(*) FROM dw_intermediate.int_invoice_header WHERE _capture_id=%(pin)s AND is_sales_eligible) invoice_count,
 (SELECT count(*) FROM dw_intermediate.int_order_header WHERE _capture_id=%(pin)s AND is_order_eligible) order_count,
 sum(invoiced_sales_before_tax)/nullif((SELECT count(*) FROM dw_intermediate.int_invoice_header WHERE _capture_id=%(pin)s AND is_sales_eligible),0) aiv
FROM dw_core.fact_invoice_line WHERE _capture_id=%(pin)s AND is_sales_eligible;

-- Q02 Calendar density and gaps within observed coverage
SELECT min(d.calendar_date) first_date,max(d.calendar_date) last_date,count(*) calendar_rows,
 count(distinct d.calendar_date) distinct_dates,(max(d.calendar_date)-min(d.calendar_date)+1) expected_days,
 count(*) FILTER(WHERE m.sales_date IS NULL) missing_daily_mart_dates,
 count(*) FILTER(WHERE m.invoice_count=0) zero_invoice_dates,
 count(*) FILTER(WHERE m.order_count=0) zero_order_dates,
 count(*) FILTER(WHERE m.sales_amount=0) zero_sales_dates,
 (SELECT count(*) FROM sales_marts.mart_sales_monthly WHERE _capture_id=%(pin)s) months,
 (SELECT count(*) FROM sales_marts.mart_sales_monthly WHERE _capture_id=%(pin)s AND NOT full_calendar_month) boundary_incomplete_months
FROM dw_core.dim_date d LEFT JOIN sales_marts.mart_sales_daily m
 ON m.sales_date=d.calendar_date AND m._capture_id=d._capture_id WHERE d._capture_id=%(pin)s;

-- Q03 Monthly activity, weighted AIV and stored coverage-aware growth
WITH orders AS (
 SELECT date_trunc('month',order_date)::date m,count(*) n FROM dw_intermediate.int_order_header
 WHERE _capture_id=%(pin)s AND is_order_eligible GROUP BY 1
)
SELECT s.sales_month,s.sales_amount,s.invoice_count,s.units_sold,o.n order_count,
 s.sales_amount/nullif(s.invoice_count,0) aiv,s.full_calendar_month,
 s.mom_sales_growth,s.yoy_sales_growth
FROM sales_marts.mart_sales_monthly s LEFT JOIN orders o ON o.m=s.sales_month
WHERE s._capture_id=%(pin)s ORDER BY s.sales_month;

-- Q04 Annual activity; incomplete years are explicitly labelled
SELECT extract(year FROM sales_date)::integer AS year,sum(sales_amount) sales,
 sum(invoice_count) invoice_count,sum(order_count) order_count,sum(units_sold) units,
 sum(sales_amount)/nullif(sum(invoice_count),0) aiv,
 min(sales_date) first_date,max(sales_date) last_date,
 count(distinct date_trunc('month',sales_date)) observed_months,
 count(*) FILTER(WHERE invoice_count>0) active_invoice_days
FROM sales_marts.mart_sales_daily WHERE _capture_id=%(pin)s GROUP BY 1 ORDER BY 1;

-- Q05 Like-for-like MMDD window through last observed invoice date; NOT current-year YTD
WITH cutoff AS (SELECT to_char(max(invoice_date),'MMDD') mmdd FROM dw_intermediate.int_invoice_header WHERE _capture_id=%(pin)s),
 y AS (
 SELECT extract(year FROM sales_date)::integer AS year,sum(sales_amount) sales,
 sum(invoice_count) invoices,sum(order_count) orders,sum(units_sold) units,
 sum(sales_amount)/nullif(sum(invoice_count),0) aiv,count(*) calendar_days,
 count(*) FILTER(WHERE invoice_count>0) active_invoice_days,
 sum(sales_amount)/nullif(count(*) FILTER(WHERE invoice_count>0),0) sales_per_active_day,
 sum(invoice_count)::numeric/nullif(count(*) FILTER(WHERE invoice_count>0),0) invoices_per_active_day
 FROM sales_marts.mart_sales_daily CROSS JOIN cutoff
 WHERE _capture_id=%(pin)s AND to_char(sales_date,'MMDD')<=cutoff.mmdd GROUP BY 1
), p AS (SELECT *,lag(sales) OVER(ORDER BY year) previous_sales,
 lag(invoices) OVER(ORDER BY year) previous_invoices,lag(aiv) OVER(ORDER BY year) previous_aiv,
 lag(sales_per_active_day) OVER(ORDER BY year) previous_sales_per_active_day,
 lag(invoices_per_active_day) OVER(ORDER BY year) previous_invoices_per_active_day FROM y)
SELECT *,sales/nullif(previous_sales,0)-1 sales_growth,
 invoices::numeric/nullif(previous_invoices,0)-1 invoice_growth,aiv/nullif(previous_aiv,0)-1 aiv_growth,
 (invoices-previous_invoices)*previous_aiv volume_component,
 previous_invoices*(aiv-previous_aiv) aiv_component,
 (invoices-previous_invoices)*(aiv-previous_aiv) interaction_component,
 sales_per_active_day/nullif(previous_sales_per_active_day,0)-1 sales_per_active_day_growth,
 invoices_per_active_day/nullif(previous_invoices_per_active_day,0)-1 invoices_per_active_day_growth
FROM p ORDER BY year;

-- Q06 Complete product rankings, exposure and current observed labels
WITH p AS (
 SELECT source_stock_item_id,sum(sales_amount) sales,sum(units_sold) units,
 min(invoice_date) first_sale,max(invoice_date) last_sale,
 count(distinct date_trunc('month',invoice_date)) active_months,count(*) active_dates
 FROM sales_marts.mart_sales_product_daily WHERE _capture_id=%(pin)s GROUP BY 1
), r AS (SELECT *,row_number() OVER(ORDER BY sales DESC,source_stock_item_id) sales_rank,
 row_number() OVER(ORDER BY units DESC,source_stock_item_id) units_rank FROM p)
SELECT r.*,d.stock_item_name current_product_label,d.brand current_brand,
 r.sales/nullif(r.units,0) sales_per_source_unit,
 r.sales/nullif(r.active_months,0) sales_per_observed_active_month
FROM r LEFT JOIN dw_core.dim_product d ON d.source_stock_item_id=r.source_stock_item_id AND d._capture_id=%(pin)s
ORDER BY r.sales_rank;

-- Q07 Product Pareto; signed sales checked before interpreting cumulative shares
WITH p AS (SELECT source_stock_item_id,sum(sales_amount) sales,sum(units_sold) units
 FROM sales_marts.mart_sales_product_daily WHERE _capture_id=%(pin)s GROUP BY 1),
 r AS (SELECT *,row_number() OVER(ORDER BY sales DESC,source_stock_item_id) rn,
 row_number() OVER(ORDER BY units DESC,source_stock_item_id) units_rn,
 sum(sales) OVER() total_sales,sum(units) OVER() total_units FROM p),
 c AS (SELECT *,sum(sales) OVER(ORDER BY rn ROWS UNBOUNDED PRECEDING)/nullif(total_sales,0) cumulative_share FROM r)
SELECT count(*) products,min(rn) FILTER(WHERE cumulative_share>=0.8) products_to_80pct,
 min(rn) FILTER(WHERE cumulative_share>=0.8)::numeric/count(*) fraction_products_to_80pct,
 sum(sales) FILTER(WHERE rn<=1)/max(total_sales) top1_sales_share,
 sum(sales) FILTER(WHERE rn<=5)/max(total_sales) top5_sales_share,
 sum(sales) FILTER(WHERE rn<=10)/max(total_sales) top10_sales_share,
 sum(sales) FILTER(WHERE rn<=20)/max(total_sales) top20_sales_share,
 sum(sales) FILTER(WHERE rn<=ceil((SELECT count(*) FROM p)*0.2))/max(total_sales) top20pct_products_sales_share,
 sum(units) FILTER(WHERE rn<=10)::numeric/max(total_units) units_share_of_top10_sales_products,
 sum(units) FILTER(WHERE units_rn<=10)::numeric/max(total_units) top10_units_share,
 count(*) FILTER(WHERE rn<=10 AND units_rn<=10) top10_rank_overlap,
 count(*) FILTER(WHERE sales<0) negative_product_totals FROM c;

-- Q08 Sales attribution roles, NEVER sum across role rows
WITH c AS (
 SELECT role,customer_id,sum(f.invoiced_sales_before_tax) sales
 FROM dw_core.fact_invoice_line f CROSS JOIN LATERAL
 (VALUES ('BUYER',f.source_buyer_customer_id),('BILL_TO',f.source_bill_to_customer_id)) roles(role,customer_id)
 WHERE f._capture_id=%(pin)s AND f.is_sales_eligible GROUP BY 1,2
), r AS (SELECT *,row_number() OVER(PARTITION BY role ORDER BY sales DESC,customer_id) rn,
 sum(sales) OVER(PARTITION BY role) total FROM c),
 s AS (SELECT *,sum(sales) OVER(PARTITION BY role ORDER BY rn ROWS UNBOUNDED PRECEDING)/nullif(total,0) cum FROM r)
SELECT role,count(*) sales_customers,max(total) sales,
 sum(sales) FILTER(WHERE rn=1)/max(total) top1_share,
 sum(sales) FILTER(WHERE rn<=5)/max(total) top5_share,
 sum(sales) FILTER(WHERE rn<=10)/max(total) top10_share,
 sum(sales) FILTER(WHERE rn<=20)/max(total) top20_share,
 min(rn) FILTER(WHERE cum>=0.8) customers_to_80pct
FROM s GROUP BY role ORDER BY role;

-- Q09 Buyer versus Bill-to topology, based on invoice-time roles rather than current CRM mapping
WITH h AS (SELECT * FROM dw_intermediate.int_invoice_header WHERE _capture_id=%(pin)s AND is_sales_eligible),
 b AS (SELECT source_bill_to_customer_id,count(distinct source_buyer_customer_id) buyers FROM h GROUP BY 1),
 c AS (SELECT source_buyer_customer_id,count(distinct source_bill_to_customer_id) bills FROM h GROUP BY 1)
SELECT (SELECT count(*) FROM h) invoices,
 (SELECT count(*) FROM h WHERE source_buyer_customer_id<>source_bill_to_customer_id) invoices_with_different_roles,
 (SELECT count(*) FROM c) buyers,(SELECT count(*) FROM b) bill_to_accounts,
 (SELECT count(*) FROM b WHERE buyers>1) bill_accounts_with_multiple_buyers,
 (SELECT max(buyers) FROM b) maximum_buyers_per_bill_account,
 (SELECT count(*) FROM c WHERE bills>1) buyers_with_multiple_bill_accounts;

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

-- Q11 Day-of-week structure: observed zero activity is NOT proof of a missing extract or business closure
SELECT extract(isodow FROM sales_date)::integer iso_weekday,count(*) calendar_days,
 count(*) FILTER(WHERE invoice_count>0) active_invoice_days,
 count(*) FILTER(WHERE invoice_count=0) zero_invoice_days,
 sum(sales_amount) sales,sum(invoice_count) invoices,sum(order_count) orders,
 avg(sales_amount) sales_per_calendar_day,
 avg(sales_amount) FILTER(WHERE invoice_count>0) sales_per_active_invoice_day,
 sum(sales_amount)/nullif(sum(invoice_count),0) aiv
FROM sales_marts.mart_sales_daily WHERE _capture_id=%(pin)s GROUP BY 1 ORDER BY 1;

-- Q12 Observed monthly volatility; descriptive, confounded by trend and month length
SELECT extract(year FROM sales_month)::integer AS year,count(*) months,
 avg(sales_amount) average_month_sales,stddev_samp(sales_amount) sample_sd_month_sales,
 stddev_samp(sales_amount)/nullif(avg(sales_amount),0) coefficient_of_variation,
 min(sales_amount) min_month_sales,max(sales_amount) max_month_sales
FROM sales_marts.mart_sales_monthly WHERE _capture_id=%(pin)s GROUP BY 1 ORDER BY 1;

-- Q13 Source LineProfit warning diagnostics, not accounting Gross Profit
SELECT count(*) eligible_invoice_lines,count(*) FILTER(WHERE source_reported_line_profit<0) negative_profit_lines,
 count(*) FILTER(WHERE source_reported_line_profit<0)::numeric/count(*) negative_line_rate,
 count(distinct source_stock_item_id) FILTER(WHERE source_reported_line_profit<0) affected_products,
 count(distinct source_invoice_id) FILTER(WHERE source_reported_line_profit<0) affected_invoices,
 sum(source_reported_line_profit) FILTER(WHERE source_reported_line_profit<0) negative_source_profit_sum,
 sum(invoiced_sales_before_tax) FILTER(WHERE source_reported_line_profit<0) sales_on_warning_lines,
 sum(invoiced_sales_before_tax) FILTER(WHERE source_reported_line_profit<0)/sum(invoiced_sales_before_tax) warning_sales_share,
 count(*) FILTER(WHERE has_warning) all_warning_lines,
 count(*) FILTER(WHERE source_reported_line_profit IS NULL) null_source_profit
FROM dw_core.fact_invoice_line WHERE _capture_id=%(pin)s AND is_sales_eligible;

-- Q14 Product-level warning concentration; all affected products
WITH p AS (SELECT source_stock_item_id,count(*) all_lines,
 count(*) FILTER(WHERE source_reported_line_profit<0) negative_lines,
 sum(source_reported_line_profit) FILTER(WHERE source_reported_line_profit<0) negative_profit_sum,
 sum(invoiced_sales_before_tax) FILTER(WHERE source_reported_line_profit<0) warning_sales
 FROM dw_core.fact_invoice_line WHERE _capture_id=%(pin)s AND is_sales_eligible GROUP BY 1)
SELECT p.*,p.negative_lines::numeric/nullif(p.all_lines,0) negative_line_rate,d.stock_item_name current_product_label
FROM p LEFT JOIN dw_core.dim_product d ON d.source_stock_item_id=p.source_stock_item_id AND d._capture_id=%(pin)s
WHERE negative_lines>0 ORDER BY negative_lines DESC,p.source_stock_item_id;

-- Q15 Warning time distribution with denominator per month
SELECT date_trunc('month',invoice_date)::date AS month,count(*) all_lines,
 count(*) FILTER(WHERE source_reported_line_profit<0) negative_lines,
 count(*) FILTER(WHERE source_reported_line_profit<0)::numeric/count(*) negative_line_rate,
 coalesce(sum(source_reported_line_profit) FILTER(WHERE source_reported_line_profit<0),0) negative_profit_sum
FROM dw_core.fact_invoice_line WHERE _capture_id=%(pin)s AND is_sales_eligible GROUP BY 1 ORDER BY 1;

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

-- Q17 Order cohorts with/without DIRECT invoice; not a conversion, lost-sale or open-order KPI
WITH invoices AS (SELECT source_order_id,count(*) n,min(invoice_date) first_invoice
 FROM dw_intermediate.int_invoice_header WHERE _capture_id=%(pin)s AND is_sales_eligible AND source_order_id IS NOT NULL GROUP BY 1)
SELECT date_trunc('month',o.order_date)::date order_month,count(*) orders,
 count(*) FILTER(WHERE i.n IS NOT NULL) orders_with_direct_invoice,
 count(*) FILTER(WHERE i.n IS NULL) orders_without_direct_invoice,
 max(i.n) max_invoices_per_matched_order,
 min(i.first_invoice-o.order_date) min_observed_lag_days,
 percentile_cont(0.5) WITHIN GROUP(ORDER BY i.first_invoice-o.order_date) median_observed_lag_days,
 percentile_cont(0.95) WITHIN GROUP(ORDER BY i.first_invoice-o.order_date) p95_observed_lag_days
FROM dw_intermediate.int_order_header o LEFT JOIN invoices i ON i.source_order_id=o.source_order_id
WHERE o._capture_id=%(pin)s AND o.is_order_eligible GROUP BY 1 ORDER BY 1;

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

-- Q19 Product exposure and bottom-rank interpretation
WITH p AS (SELECT source_stock_item_id,sum(sales_amount) sales,min(invoice_date) first_sale,
 max(invoice_date) last_sale,count(distinct date_trunc('month',invoice_date)) active_months
 FROM sales_marts.mart_sales_product_daily WHERE _capture_id=%(pin)s GROUP BY 1)
SELECT active_months,count(*) products,sum(sales) sales,min(first_sale) earliest_first_sale,max(first_sale) latest_first_sale
FROM p GROUP BY active_months ORDER BY active_months;

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

-- Q22 Short observed sales histories: compare identical last-year MMDD population instead of lifetime rank
WITH bounds AS (SELECT date_trunc('year',max(invoice_date))::date lo,max(invoice_date) hi
 FROM dw_intermediate.int_invoice_header WHERE _capture_id=%(pin)s),
 p AS (SELECT source_stock_item_id,sum(sales_amount) lifetime_sales,
 count(distinct date_trunc('month',invoice_date)) active_months,min(invoice_date) first_sale,
 sum(sales_amount) FILTER(WHERE invoice_date BETWEEN bounds.lo AND bounds.hi) comparable_sales
 FROM sales_marts.mart_sales_product_daily CROSS JOIN bounds WHERE _capture_id=%(pin)s GROUP BY 1),
 r AS (SELECT *,row_number() OVER(ORDER BY lifetime_sales DESC,source_stock_item_id) lifetime_rank,
 row_number() OVER(ORDER BY comparable_sales DESC,source_stock_item_id) comparable_rank,
 sum(lifetime_sales) OVER() total_lifetime,sum(comparable_sales) OVER() total_comparable FROM p)
SELECT r.*,d.stock_item_name current_product_label FROM r LEFT JOIN dw_core.dim_product d
 ON d.source_stock_item_id=r.source_stock_item_id AND d._capture_id=%(pin)s
WHERE active_months<(SELECT max(active_months) FROM r) ORDER BY comparable_rank;

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
