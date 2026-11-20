select source_customer_id,customer_role,sum(sales_amount) as sales_amount,sum(units_sold) as units_sold,
 sum(invoice_count) as invoice_count,min(invoice_date) as first_invoice_date,max(invoice_date) as last_invoice_date,
 {{ build_metadata() }}
from {{ ref('mart_customer_sales') }} group by source_customer_id,customer_role
