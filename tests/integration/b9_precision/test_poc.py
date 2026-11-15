"""Offline negative controls; no SQL connection or database writes."""

from pathlib import Path
import re
import unittest
import secrets

from poc import (F2_SQL, FIXTURES, PrecisionError, fixture_cte, validate_value,
                 verify_ordering, validate_pg_config, validate_readback)


class PrecisionGuardTests(unittest.TestCase):
    def test_f2_matches_verified_document_expression(self) -> None:
        root = Path(__file__).resolve().parents[3]
        evidence = (root / 'docs/data-models/wwi-dw-03a-evidence-approval-readiness.md').read_text(encoding='utf-8')
        block = evidence.split('### 5.1', 1)[1].split('```sql', 1)[1].split('```', 1)[0]
        actual = re.search(r'CASE WHEN v\.source_value.*?END', block, re.S)
        self.assertIsNotNone(actual)
        self.assertEqual(' '.join(actual.group().split()), ' '.join(F2_SQL.split()))

    def test_exact_values_and_null(self) -> None:
        for label, value in FIXTURES:
            with self.subTest(label=label):
                validate_value(value, value, label)

    def test_dropped_or_changed_seventh_digit_fails(self) -> None:
        expected = dict(FIXTURES)['V1']
        for bad in ['2026-11-15T12:34:56.123456', '2026-11-15T12:34:56.1234560',
                    '2026-11-15T12:34:56.1234568']:
            with self.subTest(bad=bad), self.assertRaises(PrecisionError):
                validate_value(bad, expected, 'V1')

    def test_non_string_carrier_and_string_null_fail(self) -> None:
        for bad in [b'2026-11-15T12:34:56.1234567', None, 123.456, object()]:
            with self.subTest(type=type(bad).__name__), self.assertRaises(PrecisionError):
                validate_value(bad, dict(FIXTURES)['V1'], 'type')
        with self.assertRaises(PrecisionError):
            validate_value('NULL', None, 'null')

    def test_noncanonical_text_fails_even_if_equal(self) -> None:
        for bad in ['2026-11-15T12:34:56', '2026-11-15T12:34:56.1234567Z',
                    '2026-11-15T12:34:56.１２３４５６７']:
            with self.subTest(bad=bad), self.assertRaises(PrecisionError):
                validate_value(bad, bad, 'format')

    def test_parameterized_fixtures_preserve_none(self) -> None:
        sql, params = fixture_cte()
        self.assertEqual(sql.count('?'), 28)
        self.assertEqual(params[-2:], ['NULL_VALUE', None])
        self.assertNotIn('2026-11-15', sql)

    def test_ordering_against_typed_controls(self) -> None:
        values = {'left': '2026-11-15T12:34:56.1234567',
                  'right': '2026-11-15T12:34:56.1234568', 'null': None}
        rows = [{'left_id': a, 'right_id': b, 'source_cmp': (x > y) - (x < y),
                 'text_cmp': (x > y) - (x < y)}
                for a, x in values.items() for b, y in values.items()
                if x is not None and y is not None]
        verify_ordering(rows, values)
        rows[1]['source_cmp'] = 0
        with self.assertRaises(PrecisionError):
            verify_ordering(rows, values)

    def test_missing_or_duplicate_order_pair_fails(self) -> None:
        values = {'a': '0001-01-01T00:00:00.0000000'}
        row = {'left_id': 'a', 'right_id': 'a', 'source_cmp': 0, 'text_cmp': 0}
        for bad in [[], [row, row]]:
            with self.subTest(rows=len(bad)), self.assertRaises(PrecisionError):
                verify_ordering(bad, values)

    def test_target_guard_rejects_non_sandbox_connection(self) -> None:
        config = {'sandbox': 'retail-b9-pg-poc', 'host': '127.0.0.1', 'port': 55433,
                  'dbname': 'b9_precision_poc', 'user': 'b9_poc',
                  'password': secrets.token_urlsafe(36)}
        validate_pg_config(config)
        for key, bad in [('host', '192.0.2.1'), ('dbname', 'warehouse'),
                         ('user', 'postgres'), ('sandbox', 'other'),
                         ('port', 0), ('password', '')]:
            with self.subTest(field=key), self.assertRaises(PrecisionError):
                validate_pg_config({**config, key: bad})

    def test_readback_keeps_distinct_occurrences_with_same_timestamp(self) -> None:
        value = dict(FIXTURES)['V1']
        expected = {'a': value, 'b': value, 'null': None}
        rows = [{'fixture_id': k, 'canonical_temporal_text': v, 'expected_temporal_text': v}
                for k, v in expected.items()]
        validate_readback(rows, expected)
        with self.assertRaises(PrecisionError):
            validate_readback(rows[:1] + rows[2:], expected)

    def test_readback_detects_precision_change(self) -> None:
        value = dict(FIXTURES)['V1']
        with self.assertRaises(PrecisionError):
            validate_readback([{'fixture_id': 'a', 'canonical_temporal_text': value[:-1] + '0',
                                'expected_temporal_text': value}], {'a': value})

    def test_readback_detects_control_value_change(self) -> None:
        value = dict(FIXTURES)['V1']
        with self.assertRaises(PrecisionError):
            validate_readback([{'fixture_id': 'a', 'canonical_temporal_text': value,
                                'expected_temporal_text': None}], {'a': value})


if __name__ == '__main__':
    unittest.main()
