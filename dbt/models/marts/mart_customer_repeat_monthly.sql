select date_trunc('month',order_date)::date as order_month,source_buyer_customer_id,
 count(distinct source_order_id) as order_count,1::integer as active_buyer,
 (count(distinct source_order_id)>=2)::integer as repeat_buyer,
 {{ capture_id() }} as _capture_id,'DEVELOPMENT_UNCERTIFIED'::text as certification_status
from {{ ref('int_order_header') }}
group by date_trunc('month',order_date)::date,source_buyer_customer_id
