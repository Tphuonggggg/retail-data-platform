select rule_id from {{ ref('validation_violations') }} where action='fail_pipeline'
