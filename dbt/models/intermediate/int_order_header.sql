select order_id as source_order_id,order_date,
 to_char(order_date,'YYYYMMDD')::integer as order_date_key,
 customer_id as source_buyer_customer_id,
 {{ observed_key('CUSTOMER','customer_id') }} as buyer_observed_customer_key,
 null::text as buyer_customer_key,
 'U'::text as buyer_lookup_status,
 'HISTORICAL_SCD2_DEFERRED'::text as buyer_lookup_reason,
 _capture_id
from {{ ref('stg_sales_orders') }}
