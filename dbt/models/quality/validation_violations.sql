-- Dependencies registered explicitly: relation rules must not infer missing refs.
{% for o in var('sales_contract')['objects'] %} -- depends_on: {{ ref(o.model) }}
{% endfor %}
{% for o in var('sales_contract')['objects'] %}
select s._capture_id as capture_id,s.source_object,s.record_identity,s.source_business_key,
 s._raw_row_ordinal,{{ ruleset() }} as ruleset_version,{{ evaluation_id() }} as evaluation_id,
 v.rule_id,v.severity,v.action,v.column_name,v.actual_value,v.expected_constraint,v.reason
from (select x.*,count(*) over(partition by _capture_id,{{ o.key }}) as _key_count
 from {{ ref(o.model) }} x) s
{{ o.joins_sql }}
cross join lateral (values
{% for r in var('sales_contract')['rules'] if r.object==o.source_object %}
 ({{ sql_literal(r.rule_id) }},({{ r.failure_sql }}),{{ sql_literal(r.severity) }},
 {{ sql_literal(r.action) }},{{ sql_literal(r.column) }},
 case when ({{ r.failure_sql }}) then
   case when s.{{ r.column }} is null then 'NULL' else 'md5:'||md5(s.{{ r.column }}::text) end
 else NULL::text end,
 {{ sql_literal(tojson(r.expected)) }},{{ sql_literal(r.message) }}){% if not loop.last %},{% endif %}
{% endfor %}
) v(rule_id,failed,severity,action,column_name,actual_value,expected_constraint,reason)
where v.failed is true
{% if not loop.last %}union all{% endif %}
{% endfor %}
