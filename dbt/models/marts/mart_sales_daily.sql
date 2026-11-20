with lines as (
 select invoice_date,sum(quantity) as quantity,
 sum(invoiced_sales_before_tax) as invoiced_sales_before_tax,
 sum(tax_amount) as tax_amount,sum(invoice_amount_including_tax) as invoice_amount_including_tax,
 sum(source_reported_line_profit) as source_reported_line_profit
 from {{ ref('fact_invoice_line') }} group by invoice_date
), headers as (
 select invoice_date,count(*) as invoice_count
 from {{ ref('int_invoice_header') }} group by invoice_date
)
select h.invoice_date,to_char(h.invoice_date,'YYYYMMDD')::integer as invoice_date_key,
 h.invoice_count,coalesce(l.quantity,0) as quantity,
 coalesce(l.invoiced_sales_before_tax,0)::numeric as invoiced_sales_before_tax,
 coalesce(l.tax_amount,0)::numeric as tax_amount,
 coalesce(l.invoice_amount_including_tax,0)::numeric as invoice_amount_including_tax,
 coalesce(l.source_reported_line_profit,0)::numeric as source_reported_line_profit,
 coalesce(l.invoiced_sales_before_tax,0)::numeric/nullif(h.invoice_count,0) as average_invoice_value_before_tax,
 {{ capture_id() }} as _capture_id,'DEVELOPMENT_UNCERTIFIED'::text as certification_status
from headers h left join lines l using(invoice_date)
