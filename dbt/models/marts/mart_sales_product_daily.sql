select invoice_date,invoice_date_key,source_stock_item_id,{{ metric('S05') }} as sales_amount,
 {{ metric('UNITS') }} as units_sold,count(distinct source_invoice_id) as product_filtered_invoice_count,
 {{ build_metadata() }}
from {{ ref('fact_invoice_line') }} where is_sales_eligible
group by invoice_date,invoice_date_key,source_stock_item_id
