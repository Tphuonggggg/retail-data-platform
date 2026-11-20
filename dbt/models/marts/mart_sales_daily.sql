with lines as (
 select invoice_date,{{ metric('S05') }} as sales_amount,{{ metric('S03') }} as invoice_amount_including_tax,
 {{ metric('S04') }} as tax_amount,{{ metric('UNITS') }} as units_sold
 from {{ ref('fact_invoice_line') }} where is_sales_eligible group by invoice_date
), invoices as (
 select invoice_date,{{ metric('S02') }} as invoice_count from {{ ref('int_invoice_header') }}
 where is_sales_eligible group by invoice_date
), orders as (
 select order_date,{{ metric('S01') }} as order_count from {{ ref('int_order_header') }}
 where is_order_eligible group by order_date
)
select d.calendar_date as sales_date,d.date_key,coalesce(i.invoice_count,0) as invoice_count,
 coalesce(o.order_count,0) as order_count,coalesce(l.sales_amount,0)::numeric as sales_amount,
 coalesce(l.tax_amount,0)::numeric as tax_amount,coalesce(l.invoice_amount_including_tax,0)::numeric as invoice_amount_including_tax,
 coalesce(l.units_sold,0) as units_sold,
 {{ ratio('coalesce(l.sales_amount,0)','i.invoice_count') }} as average_invoice_value_before_tax,
 {{ build_metadata() }}
from {{ ref('dim_date') }} d left join lines l on l.invoice_date=d.calendar_date
left join invoices i on i.invoice_date=d.calendar_date left join orders o on o.order_date=d.calendar_date
