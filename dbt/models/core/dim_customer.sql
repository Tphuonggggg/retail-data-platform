{{ config(pre_hook='{{ enforce_quality_gate() }}') }}
select {{ observed_key('CUSTOMER','customer_id') }} as customer_key,
 customer_id as source_customer_id, customer_name, customer_category_id, buying_group_id,
 bill_to_customer_id as current_bill_to_customer_id,
 valid_from as source_valid_from, valid_to as source_valid_to,
 'OBSERVED_CURRENT_CAPTURE'::text as history_basis,
 true as is_observed_current, _capture_id,record_identity,source_object,source_business_key,_raw_row_ordinal,
 ruleset_version,evaluation_id,{{ measure_version() }} as measure_version,
 q.dq_status,q.is_valid,q.has_warning,q.is_quarantined
from {{ ref('stg_sales_customers') }} s
join {{ ref('record_status') }} q using(record_identity,ruleset_version,evaluation_id,source_object,source_business_key,_raw_row_ordinal)
