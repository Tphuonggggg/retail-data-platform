select q.record_identity from {{ ref('quarantine_records') }} q
left join {{ ref('record_status') }} s using(record_identity,ruleset_version,evaluation_id)
where s.record_identity is null or not s.is_quarantined or s.dq_status<>'INVALID'
or not exists(select 1 from {{ ref('validation_violations') }} v where v.record_identity=q.record_identity
 and v.ruleset_version=q.ruleset_version and v.action='quarantine')
