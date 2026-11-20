select record_identity from {{ ref('validation_violations') }}
group by capture_id,record_identity,ruleset_version,rule_id having count(*)<>1
union all
select record_identity from {{ ref('quarantine_records') }}
group by capture_id,record_identity,ruleset_version having count(*)<>1
