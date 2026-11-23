select "ID" as line_id,"SalesDate" as sales_date,"Product" as product,
       "Quantity" as quantity,"Sales" as sales_amount,"Note" as note,"Stamp" as source_stamp
from {{ source('demo_raw', 'lines') }}
