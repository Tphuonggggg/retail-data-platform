{% for o in var('sales_contract')['objects'] %}
select record_identity from {{ ref(o.model) }} where _capture_id<>{{ capture_id() }}
or ruleset_version<>{{ ruleset() }} or evaluation_id<>{{ evaluation_id() }}
{% if not loop.last %}union all{% endif %}
{% endfor %}
