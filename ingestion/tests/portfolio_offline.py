"""Portable portfolio checks; no service connections."""
from decimal import Decimal
from pathlib import Path
import unittest
from unittest.mock import Mock

import yaml
from ingestion import demo
from ingestion.benchmark import fixtures, measure
from ingestion.incremental import compare

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


if __name__ == '__main__':
    unittest.main()
