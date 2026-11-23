select sales_date,sum(sales_amount)::numeric(18,2) as sales_amount,sum(quantity) as units_sold
from {{ ref('stg_demo_lines') }} group by sales_date
