{{ config(pre_hook='{{ enforce_quality_gate() }}') }}
select order_id as source_order_id,order_date,
 to_char(order_date,'YYYYMMDD')::integer as order_date_key,
 customer_id as source_buyer_customer_id,
 {{ observed_key('CUSTOMER','customer_id') }} as buyer_observed_customer_key,
 null::text as buyer_customer_key,
 'U'::text as buyer_lookup_status,
 'HISTORICAL_SCD2_DEFERRED'::text as buyer_lookup_reason,
 _capture_id,record_identity,source_object,source_business_key,_raw_row_ordinal,
 ruleset_version,evaluation_id,{{ measure_version() }} as measure_version,
 q.dq_status,q.is_valid,q.has_warning,q.is_quarantined,q.is_valid as is_order_eligible
from {{ ref('stg_sales_orders') }}

join {{ ref('record_status') }} q using(record_identity,ruleset_version,evaluation_id,source_object,source_business_key,_raw_row_ordinal)
