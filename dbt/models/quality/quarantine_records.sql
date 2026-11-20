select s.*,('raw.'|| case s.source_object
{% for o in var('sales_contract')['objects'] %}when {{ sql_literal(o.source_object) }} then {{ sql_literal(o.table) }}
{% endfor %}end) as raw_table,
 'See validation_violations for all rule reasons'::text as reason_summary
from {{ ref('record_status') }} s where is_quarantined
