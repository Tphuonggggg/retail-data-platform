with lines as (
 select invoice_date,{{ customer_column() }} as source_customer_id,
 {{ metric('S05') }} as sales_amount,{{ metric('UNITS') }} as units_sold
 from {{ ref('fact_invoice_line') }} where is_sales_eligible group by 1,2
), headers as (
 select invoice_date,{{ customer_column() }} as source_customer_id,count(*) as invoice_count
 from {{ ref('int_invoice_header') }} where is_sales_eligible group by 1,2
)
select h.invoice_date,h.source_customer_id,{{ sql_literal(var('sales_contract')['customer_role']) }} as customer_role,
 h.invoice_count,coalesce(l.sales_amount,0)::numeric as sales_amount,coalesce(l.units_sold,0) as units_sold,
 {{ build_metadata() }}
from headers h left join lines l using(invoice_date,source_customer_id)
