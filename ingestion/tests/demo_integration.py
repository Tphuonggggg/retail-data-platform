"""Explicit demo-only SQL and dbt verification; never selected by offline discovery."""
from __future__ import annotations

import argparse
import json
import subprocess
from uuid import UUID

from ingestion import demo

EXPECTED_OUTPUT = [['2024-01-01', '45.00', 6], ['2024-01-02', '10.00', 1]]
RECEIPT = 'integration-initial.json'


class IntegrationError(ValueError):
    """Fixed verification code, safe to show without private driver text."""


def require(condition, code):
    if not condition:
        raise IntegrationError(code)


def verify_records(initial, current, phase):
    require(initial['status'] == 'PASS' and initial['rollback_verified'] is True, 'INITIAL_OR_ROLLBACK_FAILED')
    initial_digest = demo.digest(demo.initial_rows())[1]
    final_digest = demo.digest(demo.changed_rows())[1]
    for key, counts, rows, digest in [
        ('initial', {'INSERT': 2}, 2, initial_digest),
        ('no_change', {'UNCHANGED': 2}, 2, initial_digest),
        ('recovered', {'INSERT': 1, 'UPDATE': 1, 'UNCHANGED': 1}, 3, final_digest),
    ]:
        require(initial[key] == {'changes': counts, 'rows': rows, 'digest': digest}, 'INITIAL_CHANGE_OR_DIGEST_MISMATCH')
    require(initial['daily_output'] == EXPECTED_OUTPUT, 'INITIAL_ANALYTICS_MISMATCH')
    require(current['status'] == 'PASS' and current['daily_output'] == EXPECTED_OUTPUT, 'CURRENT_ANALYTICS_MISMATCH')
    if phase == 'initial':
        require(current == initial, 'FIRST_RUN_MUST_EXERCISE_INITIAL_LOAD')
    else:
        require(set(current) == {'completed_rerun', 'daily_output', 'status'}, 'EXPECTED_COMPLETED_RERUN')
        require(current['completed_rerun'] == {
            'changes': {'UNCHANGED': 3}, 'rows': 3, 'digest': final_digest}, 'RERUN_NOT_IDEMPOTENT')


def verify_dbt(manifest, results):
    nodes = {key: node for key, node in manifest['nodes'].items() if node['resource_type'] in ('model', 'test')}
    models = {key for key, node in nodes.items() if node['resource_type'] == 'model'}
    tests = set(nodes) - models
    require(models == {'model.retail_portfolio_demo.stg_demo_lines',
                       'model.retail_portfolio_demo.mart_demo_daily'} and len(tests) == 7, 'DBT_SCOPE_MISMATCH')
    executed = {row['unique_id']: row for row in results['results']}
    require(len(executed) == len(results['results']) and set(executed) == set(nodes), 'DBT_INCOMPLETE_OR_DUPLICATE_RESULTS')
    for key, row in executed.items():
        require(row['status'] == ('success' if key in models else 'pass'), 'DBT_NODE_FAILED_OR_SKIPPED')
    invocation = results['metadata']['invocation_id']
    require(str(UUID(invocation)) == invocation and manifest['metadata']['invocation_id'] == invocation, 'DBT_INVOCATION_MISMATCH')
    return invocation


def verify_cleanup():
    for resource, args in [('containers', ['ps', '--all', '--quiet']), ('networks', ['network', 'ls', '--quiet'])]:
        result = subprocess.run(['docker', *args, '--filter', 'label=com.docker.compose.project='+demo.PROJECT],
                                capture_output=True, text=True, timeout=30)
        require(result.returncode == 0 and not result.stdout.strip(), 'DEMO_CLEANUP_INCOMPLETE_'+resource.upper())


def verify(phase):
    home = demo.HOME
    initial = json.loads((home/'initial-result.json').read_text(encoding='utf-8'))
    current = json.loads((home/'result.json').read_text(encoding='utf-8'))
    verify_records(initial, current, phase)
    invocation = verify_dbt(json.loads((home/'target/manifest.json').read_text(encoding='utf-8')),
                            json.loads((home/'target/run_results.json').read_text(encoding='utf-8')))
    if phase == 'rerun':
        receipt = json.loads((home/RECEIPT).read_text(encoding='utf-8'))
        require(receipt['initial'] == initial and receipt['dbt_invocation'] != invocation, 'RERUN_REQUIRES_FRESH_DBT_BUILD')
    # Fixed demo endpoint/credential; a read-only transaction for independent SQL read-back.
    with demo.connect(demo.environment()) as db:
        db.execute('SET TRANSACTION READ ONLY')
        demo.guard(db)
        require(db.execute('SELECT * FROM demo_raw.lines ORDER BY "ID"').fetchall() == demo.changed_rows(),
                'SQL_RAW_STATE_MISMATCH')
        rows = db.execute('SELECT sales_date,sales_amount,units_sold FROM demo_analytics.mart_demo_daily ORDER BY 1').fetchall()
        require([[str(day), str(sales), units] for day, sales, units in rows] == EXPECTED_OUTPUT, 'SQL_ANALYTICS_MISMATCH')
    if phase == 'initial':
        (home/RECEIPT).write_text(json.dumps({'initial': initial, 'dbt_invocation': invocation}), encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'phase': phase, 'raw_rows': 3, 'models': 2, 'data_tests': 7,
                      'sql_readback': True, 'daily_output': EXPECTED_OUTPUT}))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('initial', 'rerun', 'cleanup'))
    args = parser.parse_args(argv)
    try:
        if args.phase == 'cleanup':
            verify_cleanup()
            print('PASS: no demo containers or networks remain')
        else:
            verify(args.phase)
        return 0
    except Exception as error:
        # Keep driver text, profiles and credentials out of CI output.
        print(json.dumps({'status': 'FAIL', 'phase': args.phase, 'error_type': type(error).__name__,
                          'code': str(error) if isinstance(error, IntegrationError) else 'DEMO_INTEGRATION_FAILED'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
