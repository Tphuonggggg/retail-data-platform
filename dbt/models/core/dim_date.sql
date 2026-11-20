with event_dates as (
 select order_date as d from {{ ref('stg_sales_orders') }}
 union all select invoice_date from {{ ref('stg_sales_invoices') }}
), bounds as (select min(d) as lo,max(d) as hi from event_dates), calendar as (
 select lo + s.n as calendar_date from bounds
 cross join lateral generate_series(0,hi-lo) s(n)
)
select to_char(calendar_date,'YYYYMMDD')::integer as date_key, calendar_date,
 extract(year from calendar_date)::integer as calendar_year,
 extract(month from calendar_date)::integer as calendar_month,
 extract(day from calendar_date)::integer as calendar_day,
 extract(quarter from calendar_date)::integer as calendar_quarter,
 date_trunc('month',calendar_date)::date as month_start,
 {{ capture_id() }} as _capture_id
from calendar
