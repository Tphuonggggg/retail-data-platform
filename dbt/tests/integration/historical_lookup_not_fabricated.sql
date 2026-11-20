select record_identity from {{ ref('fact_invoice_line') }} where buyer_customer_key is not null
 or bill_to_customer_key is not null or product_key is not null or buyer_lookup_status<>'U'
 or bill_to_lookup_status<>'U' or product_lookup_status<>'U'
union all
select record_identity from {{ ref('fact_order_line') }} where buyer_customer_key is not null
 or product_key is not null or buyer_lookup_status<>'U' or product_lookup_status<>'U'
