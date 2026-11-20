"""Incremental invariants and generated migration contract; no runtime connections."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import unittest

from ingestion.common.contracts import Column,SourceObject
from ingestion.common.errors import PipelineError
from ingestion.incremental import compare, fingerprint, objects, state_sql, SALES
from ingestion.loaders.incremental_schema import migration

SAMPLE=SourceObject('Sales','Sample',(Column('ID','int',False),Column('Amount','decimal(18,2)',True),
    Column('Text','nvarchar(max)',True),Column('Stamp','datetime2(7)',True),Column('Bytes','varbinary(max)',True)),
    'ID',('ID',),'SYNTHETIC_FIXTURE')
ROW=(1,Decimal('1.23'),'Tiếng Việt 😀','2016-01-01T00:00:00.0000001',b'\x00\xff')


class IncrementalTests(unittest.TestCase):
    def test_close_failure_does_not_leak_driver_message(self):
        from contextlib import redirect_stdout
        import io
        from unittest.mock import Mock,patch
        from ingestion.incremental import main
        pg=Mock();pg.connection.execute.return_value.fetchone.return_value=('id','parent','base','VALIDATED',1,{},None,None)
        pg.close.side_effect=RuntimeError('private-driver-secret-marker')
        output=io.StringIO()
        with patch('ingestion.incremental.settings'),patch('ingestion.incremental.PostgresTarget',return_value=pg),patch('ingestion.incremental.IncrementalTarget'),redirect_stdout(output):
            code=main(['inspect','--version-id','c825b18e-fc62-4cf1-8837-b37b4c9f9668'])
        self.assertEqual(code,1)
        self.assertIn('CLOSE_FAILED_INSPECT_VERSION',output.getvalue())
        self.assertNotIn('private-driver-secret-marker',output.getvalue())
    def changes(self,a,b):return list(compare(SAMPLE,a,b))
    def test_insert_update_delete_unchanged(self):
        before=[ROW,replace_row(ROW,0,2),replace_row(ROW,0,4)]
        after=[replace_row(ROW,1,Decimal('1.24')),replace_row(ROW,0,3),replace_row(ROW,0,4)]
        self.assertEqual([r.kind for r in self.changes(before,after)],['UPDATE','DELETE','INSERT','UNCHANGED'])
    def test_empty(self):self.assertEqual(self.changes([],[]),[])
    def test_null_empty(self):
        self.assertEqual(self.changes([replace_row(ROW,2,None)],[replace_row(ROW,2,'')])[0].kind,'UPDATE')
    def test_null_to_value_and_back(self):
        for a,b in [(None,'x'),('x',None)]:
            self.assertEqual(self.changes([replace_row(ROW,2,a)],[replace_row(ROW,2,b)])[0].kind,'UPDATE')
    def test_decimal_cent(self):self.assertNotEqual(fingerprint(ROW),fingerprint(replace_row(ROW,1,Decimal('1.24'))))
    def test_seven_digits(self):
        self.assertEqual(self.changes([ROW],[replace_row(ROW,3,ROW[3][:-1]+'2')])[0].kind,'UPDATE')
    def test_binary(self):self.assertNotEqual(fingerprint(ROW),fingerprint(replace_row(ROW,4,b'\xff\x00')))
    def test_unicode(self):self.assertNotEqual(fingerprint(ROW),fingerprint(replace_row(ROW,2,'Tieng Viet')))
    def test_hash_deterministic(self):self.assertEqual(fingerprint(ROW),fingerprint(tuple(ROW)))
    def test_duplicate_key(self):
        with self.assertRaisesRegex(PipelineError,'INCREMENTAL_DUPLICATE'):self.changes([],[ROW,ROW])
    def test_unordered(self):
        with self.assertRaisesRegex(PipelineError,'INCREMENTAL_DUPLICATE'):self.changes([replace_row(ROW,0,2),ROW],[])
    def test_partial_extraction_raises(self):
        def stream():
            yield ROW
            raise OSError('synthetic broken stream')
        with self.assertRaises(OSError):self.changes([ROW,replace_row(ROW,0,2)],stream())
    def test_missing_key(self):
        with self.assertRaises(PipelineError):list(compare(replace(SAMPLE,primary_key=None),[],[]))
    def test_decimal_loss_rejected(self):
        with self.assertRaises(PipelineError):self.changes([],[replace_row(ROW,1,Decimal('1.234'))])
    def test_datetime_object_rejected(self):
        from datetime import datetime
        with self.assertRaises(PipelineError):self.changes([],[replace_row(ROW,3,datetime.now())])
    def test_scope_exact_lineage(self):
        self.assertEqual(len(objects()),6);self.assertNotIn('Sales.CustomerTransactions',SALES)
        for obj in objects():self.assertIn('%s',state_sql(obj))
    def test_migration_file_matches_generator(self):
        path=Path(__file__).resolve().parents[2]/'infrastructure/postgres/incremental.sql'
        self.assertEqual(path.read_text(encoding='utf-8'),migration())
    def test_all_sales_models_and_tests_use_version_selection(self):
        import re
        root=Path(__file__).resolve().parents[2]/'dbt'
        for folder in ('models','tests'):
            for path in (root/folder).rglob('*.sql'):
                self.assertIsNone(re.search(r"source\('wwi_raw'",path.read_text(encoding='utf-8')),str(path))
    def test_migration_no_legacy_modification(self):
        ddl=migration()
        for token in ('DROP ','TRUNCATE ','SECURITY DEFINER','CREATE ROLE','ALTER ROLE','GRANT ALL'):
            self.assertNotIn(token,ddl.upper())
        self.assertEqual(ddl.count('CREATE TABLE raw."delta_'),6)
        self.assertEqual(ddl.count('CREATE FUNCTION raw."sales_state_'),6)
        self.assertIn('acknowledged_publication_id IS NULL',ddl)
        self.assertNotIn('UPDATE ingestion_meta.raw_current',ddl)
    def test_full_and_incremental_dbt_selection(self):
        from jinja2 import Environment
        from types import SimpleNamespace
        text=(Path(__file__).resolve().parents[2]/'dbt/macros/capture.sql').read_text(encoding='utf-8')
        def render(kind):
            class Errors:
                def raise_compiler_error(self,m):raise ValueError(m)
            context={'source':lambda a,b:'raw.'+b,'var':lambda name,default=None:kind,
                     'env_var':lambda n:'5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8',
                     'modules':SimpleNamespace(re=__import__('re')),'return':lambda x:x,'exceptions':Errors()}
            return Environment().from_string(text).make_module(context).sales_raw_input('sales_orders').strip()
        self.assertEqual(render('FULL'),'raw.sales_orders')
        self.assertIn('sales_state_sales_orders',render('INCREMENTAL'))
        with self.assertRaises(ValueError):render('LATEST')


def replace_row(row,index,value):return row[:index]+(value,)+row[index+1:]


if __name__=='__main__':unittest.main()
