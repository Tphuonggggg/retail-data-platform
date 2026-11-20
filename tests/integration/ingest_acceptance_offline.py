"""Cross-engine aggregate normalization regression, no network or writes."""
import importlib.util
from pathlib import Path
from decimal import Decimal
import unittest
from unittest.mock import MagicMock, patch
from contextlib import redirect_stdout
import io
from ingestion.common.contracts import select_objects

spec = importlib.util.spec_from_file_location('runtime_checks', Path(__file__).parent/'ingest_runtime.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class AggregateTests(unittest.TestCase):
    def test_cross_engine_count_types_and_exact_amounts(self):
        fields = [('rows',''), ('null:x',''), ('sum:amount','')]
        self.assertEqual(checks.normalize_measures(fields, (227, 0, Decimal('5107.920000'))),
                         checks.normalize_measures(fields, (227, Decimal('0'), Decimal('5107.92'))))

    def test_large_decimal_is_not_rounded_by_context(self):
        value = Decimal('123456789012345678901234567890.123456')
        self.assertEqual(checks.scalar(value), '123456789012345678901234567890.123456')

    def test_empty_sum_and_temporal_remain_distinct(self):
        self.assertIsNone(checks.scalar(None))
        self.assertEqual(checks.scalar('2016-05-31T12:00:00.0000001'), '2016-05-31T12:00:00.0000001')

    def test_reference_checks_close_odbc_cursor_and_isolate_capture(self):
        source, target = MagicMock(), MagicMock()
        cursor = source.connection.cursor.return_value
        cursor.execute.return_value.fetchone.return_value = (0,)
        target.connection.execute.return_value.fetchone.return_value = (0,)
        result = checks.reference_checks(source, target, select_objects(), 'synthetic-run')
        self.assertEqual(len(result), 16)
        self.assertEqual(cursor.close.call_count, 16)
        for call in target.connection.execute.call_args_list:
            self.assertIn('p._run_id=%s', call.args[0])
            self.assertIn('c._run_id=%s', call.args[0])
            self.assertEqual(call.args[1], ('synthetic-run', 'synthetic-run'))

    def test_default_acceptance_probe_never_connects(self):
        with patch('sys.argv', ['probe']), patch.object(checks, 'SqlServerSource') as source, \
                patch.object(checks, 'PostgresTarget') as target, redirect_stdout(io.StringIO()):
            self.assertEqual(checks.main(), 0)
        source.assert_not_called(); target.assert_not_called()

    def test_failure_probe_requires_explicit_execute(self):
        spec = importlib.util.spec_from_file_location('failure_probe', Path(__file__).parent/'ingest_failure_runtime.py')
        failure = importlib.util.module_from_spec(spec); spec.loader.exec_module(failure)
        with patch('sys.argv', ['probe']), patch.object(failure, 'SqlServerSource') as source, \
                patch.object(failure, 'InjectedFailureTarget') as target, redirect_stdout(io.StringIO()):
            self.assertEqual(failure.main(), 0)
        source.assert_not_called(); target.assert_not_called()


if __name__ == '__main__': unittest.main()
