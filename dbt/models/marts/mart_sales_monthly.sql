with months as (
select date_trunc('month',sales_date)::date as sales_month,sum(sales_amount) as sales_amount,
 sum(invoice_count) as invoice_count,sum(units_sold) as units_sold
from {{ ref('mart_sales_daily') }} group by 1
), bounds as (
select min(invoice_date) as lo,max(invoice_date) as hi from {{ ref('int_invoice_header') }}
), coverage as (
select m.*,(sales_month>=lo and (sales_month+interval '1 month' - interval '1 day')::date<=hi) as full_calendar_month
from months m cross join bounds
), compared as (
select *,lag(sales_amount) over(order by sales_month) as previous_month_sales,
 lag(sales_amount,12) over(order by sales_month) as previous_year_sales,
 lag(full_calendar_month) over(order by sales_month) as previous_month_complete,
 lag(full_calendar_month,12) over(order by sales_month) as previous_year_complete
from coverage
)
select *,case when full_calendar_month and previous_month_complete then
 {{ ratio('sales_amount-previous_month_sales','previous_month_sales') }} end as mom_sales_growth,
 case when full_calendar_month and previous_year_complete then
 {{ ratio('sales_amount-previous_year_sales','previous_year_sales') }} end as yoy_sales_growth,
 {{ build_metadata() }} from compared
