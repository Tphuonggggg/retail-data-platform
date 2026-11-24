"""Portable portfolio checks; no service connections."""
from decimal import Decimal
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import yaml
from ingestion import demo
from ingestion.benchmark import fixtures, measure
from ingestion.incremental import compare
from ingestion.tests import demo_integration

ROOT = Path(__file__).resolve().parents[2]


class PortfolioTests(unittest.TestCase):
    def test_benchmark_exact_changes_and_reconciliation(self):
        for percent in (0, 1, 10):
            with self.subTest(percent=percent):
                before, after, expected = fixtures(1000, percent)
                result = measure(before, after, expected)
                self.assertEqual(result['records_examined'], 1000 + expected['INSERT'])
                self.assertEqual(sum(result['changes'].values()), len(after))
                self.assertGreater(result['peak_traced_bytes'], 0)

    def test_fixture_determinism_and_precision(self):
        self.assertEqual(fixtures(1000, 10), fixtures(1000, 10))
        before, after, _ = fixtures(1000, 10)
        changes = list(compare(demo.SAMPLE, before, after))
        self.assertEqual({c.after[4]-c.before[4] for c in changes if c.kind == 'UPDATE'}, {Decimal('0.01')})

    def test_demo_expected_change_mix(self):
        changes = list(compare(demo.SAMPLE, demo.initial_rows(), demo.changed_rows()))
        self.assertEqual([c.kind for c in changes], ['UPDATE', 'UNCHANGED', 'INSERT'])
        self.assertEqual(sum(r[4] for r in demo.changed_rows()), Decimal('55.00'))
        self.assertNotEqual(demo.digest(demo.initial_rows()), demo.digest(demo.changed_rows()))

    def test_demo_refuses_live_identity(self):
        for identity in [('retail_raw', 'retail_ingest'), ('retail_raw', 'postgres'), (demo.DATABASE, 'postgres')]:
            db = Mock()
            db.execute.return_value.fetchone.return_value = identity
            with self.assertRaisesRegex(ValueError, 'IDENTITY_MISMATCH'):
                demo.initialize(db)
            self.assertEqual(db.execute.call_count, 1)

    def test_demo_refuses_protected_schemas(self):
        db = Mock()
        db.execute.return_value.fetchone.side_effect = [(demo.DATABASE, demo.USER), (1,)]
        with self.assertRaisesRegex(ValueError, 'NOT_ISOLATED'):
            demo.initialize(db)

    def test_demo_compose_isolation(self):
        config = yaml.safe_load((ROOT/'infrastructure/docker/compose.demo.yaml').read_text())
        self.assertEqual(config['name'], demo.PROJECT)
        pg = config['services']['postgres']
        self.assertEqual(pg['ports'], ['127.0.0.1:55439:5432'])
        self.assertEqual(pg['environment']['POSTGRES_DB'], demo.DATABASE)
        self.assertNotIn('volumes', pg)
        self.assertNotIn('volumes', config)
        self.assertEqual(pg['restart'], 'no')

    def test_workflow_static_contract(self):
        config = yaml.safe_load((ROOT/'.github/workflows/ci.yml').read_text())
        # PyYAML YAML 1.1 reads GitHub's unquoted 'on' as True.
        self.assertEqual(config.get('on', config.get(True)), ['push', 'pull_request'])
        self.assertEqual(config['permissions'], {'contents': 'read'})
        steps = config['jobs']['portable']['steps']
        self.assertTrue(any(s.get('run') == 'python scripts/run_checks.py --portable' for s in steps))
        integration = config['jobs']['demo-integration']
        self.assertNotIn('needs', integration)
        commands = [s.get('run', '') for s in integration['steps']]
        self.assertEqual(sum(c.splitlines().count('python -m ingestion.demo run') for c in commands), 2)
        self.assertIn('python -m ingestion.tests.demo_integration initial', '\n'.join(commands))
        self.assertIn('python -m ingestion.tests.demo_integration rerun', '\n'.join(commands))
        cleanup = integration['steps'][-1]
        self.assertEqual(cleanup['if'], '${{ always() }}')
        self.assertEqual(cleanup['run'].splitlines(), ['python -m ingestion.demo down',
                                                     'python -m ingestion.tests.demo_integration cleanup'])
        self.assertNotIn('continue-on-error', cleanup)

    def test_demo_change_counts_fail_closed(self):
        demo.require_changes({'UNCHANGED': 3}, {'UNCHANGED': 3})
        for actual in ({'INSERT': 1, 'UNCHANGED': 2}, {'UPDATE': 1, 'UNCHANGED': 2},
                       {'DELETE': 1, 'UNCHANGED': 3}, {'UNCHANGED': 2}):
            with self.subTest(actual=actual), self.assertRaisesRegex(ValueError, 'UNEXPECTED_CHANGE_COUNTS'):
                demo.require_changes(actual, {'UNCHANGED': 3})

    def test_demo_integration_records_reject_false_success(self):
        initial_digest = demo.digest(demo.initial_rows())[1]
        final_digest = demo.digest(demo.changed_rows())[1]
        initial = {'status': 'PASS', 'rollback_verified': True, 'daily_output': demo_integration.EXPECTED_OUTPUT,
                   'initial': {'changes': {'INSERT': 2}, 'rows': 2, 'digest': initial_digest},
                   'no_change': {'changes': {'UNCHANGED': 2}, 'rows': 2, 'digest': initial_digest},
                   'recovered': {'changes': {'UPDATE': 1, 'INSERT': 1, 'UNCHANGED': 1}, 'rows': 3, 'digest': final_digest}}
        rerun = {'status': 'PASS', 'daily_output': demo_integration.EXPECTED_OUTPUT,
                 'completed_rerun': {'changes': {'UNCHANGED': 3}, 'rows': 3, 'digest': final_digest}}
        demo_integration.verify_records(initial, initial, 'initial')
        demo_integration.verify_records(initial, rerun, 'rerun')
        for field, value in [('rollback_verified', False), ('no_change', {'changes': {'UPDATE': 2}}),
                             ('daily_output', [['2024-01-01', '44.00', 6]])]:
            invalid = deepcopy(initial); invalid[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                demo_integration.verify_records(invalid, rerun, 'rerun')
        invalid = deepcopy(rerun); invalid['completed_rerun']['changes'] = {'INSERT': 1, 'UNCHANGED': 2}
        with self.assertRaisesRegex(ValueError, 'NOT_IDEMPOTENT'):
            demo_integration.verify_records(initial, invalid, 'rerun')
        with self.assertRaisesRegex(ValueError, 'FIRST_RUN'):
            demo_integration.verify_records(initial, rerun, 'initial')

    def test_demo_dbt_failed_skipped_or_missing_tests_are_rejected(self):
        invocation = '00000000-0000-4000-8000-000000000001'
        nodes = {'model.retail_portfolio_demo.'+name: {'resource_type': 'model'}
                 for name in ('stg_demo_lines', 'mart_demo_daily')}
        nodes.update({'test.retail_portfolio_demo.case_'+str(i): {'resource_type': 'test'} for i in range(7)})
        manifest = {'nodes': nodes, 'metadata': {'invocation_id': invocation}}
        results = {'metadata': {'invocation_id': invocation}, 'results': [
            {'unique_id': key, 'status': 'success' if node['resource_type'] == 'model' else 'pass'}
            for key, node in nodes.items()]}
        self.assertEqual(demo_integration.verify_dbt(manifest, results), invocation)
        for status in ('fail', 'error', 'skipped', 'warn'):
            invalid = deepcopy(results); invalid['results'][-1]['status'] = status
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, 'FAILED_OR_SKIPPED'):
                demo_integration.verify_dbt(manifest, invalid)
        for rows in (results['results'][:-1], results['results']+[results['results'][-1]]):
            invalid = deepcopy(results); invalid['results'] = rows
            with self.assertRaisesRegex(ValueError, 'INCOMPLETE_OR_DUPLICATE'):
                demo_integration.verify_dbt(manifest, invalid)

    def test_demo_cleanup_failures_are_visible_and_scoped(self):
        for response in (SimpleNamespace(returncode=1, stdout=''), SimpleNamespace(returncode=0, stdout='remaining-id')):
            with patch.object(demo_integration.subprocess, 'run', return_value=response) as run:
                with self.assertRaisesRegex(ValueError, 'CLEANUP_INCOMPLETE'):
                    demo_integration.verify_cleanup()
                command = run.call_args.args[0]
                self.assertIn('label=com.docker.compose.project='+demo.PROJECT, command)
                self.assertNotIn('prune', command)


if __name__ == '__main__':
    unittest.main()
