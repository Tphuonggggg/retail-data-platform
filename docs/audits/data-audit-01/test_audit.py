"""Audit harness checks only; no source/target connection or synthetic DB records."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from decimal import Decimal
from unittest.mock import MagicMock
import unittest

spec=importlib.util.spec_from_file_location('data_audit',Path(__file__).with_name('audit.py'))
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

class HarnessTests(unittest.TestCase):
    def test_decimal_exact_and_float_rejected(self):
        self.assertEqual(audit.canonical(Decimal('9999999999999999.99'),'decimal(18,2)')[1],'9999999999999999.99')
        with self.assertRaises(ValueError):audit.canonical(1.1,'decimal(18,2)')
    def test_adjacent_100ns_distinct(self):
        a=audit.canonical('2016-05-31T00:00:00.0000001','datetime2(7)')
        b=audit.canonical('2016-05-31T00:00:00.0000002','datetime2(7)')
        self.assertNotEqual(a,b)
        with self.assertRaises(ValueError):audit.canonical('2016-05-31T00:00:00.000001','datetime2(7)')
    def test_unicode_not_normalized(self):
        self.assertNotEqual(audit.canonical('é','nvarchar(10)'),audit.canonical('e\u0301','nvarchar(10)'))
    def test_null_not_empty(self):
        self.assertNotEqual(audit.canonical(None,'nvarchar(max)'),audit.canonical('','nvarchar(max)'))
    def test_multiplicity_and_order(self):
        obj=SimpleNamespace(primary_key='id',columns=[SimpleNamespace(name='id',source_type='int')])
        a,b,c=(audit.Stats(obj) for _ in range(3))
        for r in [(1,),(2,),(1,)]:a.add(r)
        for r in [(1,),(1,),(2,)]:b.add(r)
        for r in [(1,),(2,)]:c.add(r)
        self.assertEqual(a.hashes,b.hashes);self.assertEqual(a.digest,b.digest)
        self.assertNotEqual(a.hashes,c.hashes);self.assertNotEqual(a.digest,c.digest)
    def test_percent_literal_without_parameters(self):
        a=object.__new__(audit.Audit);a.queries=[];db=MagicMock();cur=db.cursor.return_value.__enter__.return_value
        a.q(db,"select relname from pg_class where relname like 'fixture_%'")
        cur.execute.assert_called_once_with("select relname from pg_class where relname like 'fixture_%'",None)
    def test_parameters_remain_bound(self):
        a=object.__new__(audit.Audit);a.queries=[];db=MagicMock();cur=db.cursor.return_value.__enter__.return_value
        a.q(db,'select %s',(audit.PIN,));cur.execute.assert_called_once_with('select %s',(audit.PIN,))

if __name__=='__main__':unittest.main()
