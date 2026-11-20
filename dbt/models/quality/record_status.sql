with records as (
{% for o in var('sales_contract')['objects'] %}
select _capture_id as capture_id,source_object,record_identity,source_business_key,
 _raw_row_ordinal,{{ ruleset() }} as ruleset_version,{{ evaluation_id() }} as evaluation_id
from {{ ref(o.model) }} {% if not loop.last %}union all{% endif %}
{% endfor %}
), violations as (
select capture_id,source_object,record_identity,ruleset_version,
 bool_or(severity='ERROR') as invalid,bool_or(severity='WARNING') as warning,
 bool_or(action='quarantine') as quarantine,count(*) as violation_count
from {{ ref('validation_violations') }} group by 1,2,3,4
)
select r.*,case when v.invalid then 'INVALID' when v.warning then 'WARNING' else 'VALID' end::text as dq_status,
 not coalesce(v.invalid,false) as is_valid,coalesce(v.warning,false) as has_warning,
 coalesce(v.quarantine,false) as is_quarantined,coalesce(v.violation_count,0) as violation_count
from records r left join violations v using(capture_id,source_object,record_identity,ruleset_version)
