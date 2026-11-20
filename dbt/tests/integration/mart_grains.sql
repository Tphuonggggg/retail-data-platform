select 'daily' as model from {{ ref('mart_sales_daily') }} group by sales_date having count(*)<>1
union all select 'product' from {{ ref('mart_sales_product_daily') }} group by invoice_date,source_stock_item_id having count(*)<>1
union all select 'customer' from {{ ref('mart_customer_sales') }} group by invoice_date,source_customer_id,customer_role having count(*)<>1
union all select 'customer_summary' from {{ ref('mart_sales_customer_summary') }} group by source_customer_id,customer_role having count(*)<>1
union all select 'monthly' from {{ ref('mart_sales_monthly') }} group by sales_month having count(*)<>1
