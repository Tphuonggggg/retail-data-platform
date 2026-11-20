-- C03 BUYER only. C04 BILL_TO remains separately available in core, not unioned into this demo mart.
select invoice_date,to_char(invoice_date,'YYYYMMDD')::integer as invoice_date_key,
 source_buyer_customer_id as source_customer_id,'BUYER'::text as customer_role,
 sum(invoiced_sales_before_tax) as invoiced_sales_before_tax,
 sum(tax_amount) as tax_amount,sum(invoice_amount_including_tax) as invoice_amount_including_tax,
 {{ capture_id() }} as _capture_id,'DEVELOPMENT_UNCERTIFIED'::text as certification_status
from {{ ref('fact_invoice_line') }} group by invoice_date,source_buyer_customer_id
