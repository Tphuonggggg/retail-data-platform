{{ config(pre_hook='{{ enforce_quality_gate() }}') }}
select {{ observed_key('PRODUCT','stock_item_id') }} as product_key,
 stock_item_id as source_stock_item_id, stock_item_name, brand, size, color_id,
 unit_package_id, outer_package_id, quantity_per_outer, is_chiller_stock,
 valid_from as source_valid_from, valid_to as source_valid_to,
 'OBSERVED_CURRENT_CAPTURE'::text as history_basis,
 true as is_observed_current, _capture_id,record_identity,source_object,source_business_key,_raw_row_ordinal,
 ruleset_version,evaluation_id,{{ measure_version() }} as measure_version,
 q.dq_status,q.is_valid,q.has_warning,q.is_quarantined
from {{ ref('stg_warehouse_stockitems') }} s
join {{ ref('record_status') }} q using(record_identity,ruleset_version,evaluation_id,source_object,source_business_key,_raw_row_ordinal)
