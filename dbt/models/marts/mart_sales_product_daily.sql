select invoice_date,to_char(invoice_date,'YYYYMMDD')::integer as invoice_date_key,
 source_stock_item_id,count(distinct source_invoice_id) as product_filtered_invoice_count,
 sum(quantity) as quantity,sum(invoiced_sales_before_tax) as invoiced_sales_before_tax,
 sum(tax_amount) as tax_amount,sum(invoice_amount_including_tax) as invoice_amount_including_tax,
 sum(source_reported_line_profit) as source_reported_line_profit,
 {{ capture_id() }} as _capture_id,'DEVELOPMENT_UNCERTIFIED'::text as certification_status
from {{ ref('fact_invoice_line') }} group by invoice_date,source_stock_item_id
