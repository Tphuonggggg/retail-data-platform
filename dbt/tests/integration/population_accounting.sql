with staged as (
{% for o in var('sales_contract')['objects'] %}
select _capture_id as capture_id,source_object,record_identity,ruleset_version from {{ ref(o.model) }}
{% if not loop.last %}union all{% endif %}
{% endfor %}
), evaluated as (
select capture_id,source_object,record_identity,ruleset_version from {{ ref('record_status') }}
)
(select * from staged except all select * from evaluated)
union all (select * from evaluated except all select * from staged)
