select sales_date from {{ ref('mart_sales_daily') }}
where average_invoice_value_before_tax is distinct from sales_amount/nullif(invoice_count::numeric,0)
