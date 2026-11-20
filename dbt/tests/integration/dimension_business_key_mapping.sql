select f.record_identity from {{ ref('fact_invoice_line') }} f
left join {{ ref('dim_product') }} p on p.product_key=f.observed_product_key
left join {{ ref('dim_customer') }} b on b.customer_key=f.buyer_observed_customer_key
left join {{ ref('dim_customer') }} t on t.customer_key=f.bill_to_observed_customer_key
left join {{ ref('dim_date') }} d on d.date_key=f.invoice_date_key
where f.is_sales_eligible and (p.source_stock_item_id is distinct from f.source_stock_item_id
 or b.source_customer_id is distinct from f.source_buyer_customer_id
 or t.source_customer_id is distinct from f.source_bill_to_customer_id
 or d.calendar_date is distinct from f.invoice_date)
union all
select f.record_identity from {{ ref('fact_order_line') }} f
left join {{ ref('dim_product') }} p on p.product_key=f.observed_product_key
left join {{ ref('dim_customer') }} b on b.customer_key=f.buyer_observed_customer_key
left join {{ ref('dim_date') }} d on d.date_key=f.order_date_key
where f.is_order_eligible and (p.source_stock_item_id is distinct from f.source_stock_item_id
 or b.source_customer_id is distinct from f.source_buyer_customer_id
 or d.calendar_date is distinct from f.order_date)
