with expected as (
select record_identity,ruleset_version,bool_or(severity='ERROR') as invalid,
bool_or(severity='WARNING') as warning from {{ ref('validation_violations') }} group by 1,2
)
select s.record_identity from {{ ref('record_status') }} s
left join expected v using(record_identity,ruleset_version)
where (s.dq_status='INVALID') is distinct from coalesce(v.invalid,false)
or s.is_valid is distinct from (s.dq_status<>'INVALID')
or s.has_warning is distinct from coalesce(v.warning,false)
