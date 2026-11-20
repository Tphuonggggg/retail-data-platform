"""Synthetic/fake-driver WWI-06A tests. No source/target/Docker connections."""
from __future__ import annotations

import ast
from contextlib import contextmanager, redirect_stdout
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from ingestion.common.codecs import RowDigest, admit, admit_row
from ingestion.common.config import Settings, SOURCE_PRINCIPAL, settings
from ingestion.common.contracts import Column, F2_SQL, catalog, contract_hash, select_objects
from ingestion.common.errors import PipelineError
from ingestion.common.evidence import SourceEvidence
from ingestion.extractors.sqlserver import SqlServerSource
from ingestion.full_load import main, run_full_load
from ingestion.loaders.postgres import PostgresTarget
from ingestion.loaders.schema import full_load_ddl
from infrastructure.scripts.check_raw_connection import RawConfig

ROOT=Path(__file__).resolve().parents[2]


def fixture_row(obj, key=1):
    values=[]
    for c in obj.columns:
        t=c.source_type
        if c.nullable: value=None
        elif t=='int': value=key
        elif t=='bit': value=True
        elif t=='date': value=date(2025,1,1)
        elif t.startswith('decimal'): value=Decimal('1.000') if t.endswith(',3)') else Decimal('1.00')
        elif t=='datetime2(7)': value='2025-01-01T00:00:00.0000001'
        elif t.startswith('nvarchar'): value='x'
        else: value=b'\x00\xff'
        values.append(value)
    return tuple(values)


class FakeSource:
    def __init__(self, data, page_size=2, changed_count=False, fail=False):
        self.data=data;self.page_size=page_size;self.changed_count=changed_count;self.fail=fail
        self.connects=0;self.counts={}
    def connect(self): self.connects+=1
    def preflight(self,objects): pass
    def count(self,obj):
        self.counts[obj.name]=self.counts.get(obj.name,0)+1
        return len(self.data.get(obj.name,[]))+(int(self.changed_count) if self.counts[obj.name]>1 else 0)
    def batches(self,obj):
        rows=self.data.get(obj.name,[])
        for i in range(0,len(rows),self.page_size):
            yield rows[i:i+self.page_size]
            if self.fail: raise RuntimeError('synthetic-private-driver-detail')


class FakeTarget:
    """Transaction fixture models durable metadata vs all-or-nothing capture state."""
    def __init__(self, fail_write=False, corrupt=False, commit_ack_lost=False):
        self.runs={};self.payload={};self.audits={};self.pointer=None
        self.fail_write=fail_write;self.corrupt=corrupt;self.commit_ack_lost=commit_ack_lost
        self.batch_sizes=[];self.rollbacks=0;self.in_transaction=False
    def preflight(self,objects): pass
    def acquire_lock(self): pass
    def existing(self,rid,objects):
        row=self.runs.get(rid)
        if row and row['scope']!=[o.name for o in objects]: raise PipelineError('RUN_SCOPE_OR_CONTRACT_CONFLICT')
        return row['status'] if row else None
    def begin_run(self,rid,cid,objects,retry_of,source_context):
        if retry_of and self.existing(retry_of,objects)!='FAILED': raise PipelineError('RETRY_REQUIRES_FAILED_PREDECESSOR')
        self.runs[rid]={'status':'RUNNING','scope':[o.name for o in objects],'capture':cid,'retry':retry_of}
    @contextmanager
    def transaction(self):
        before=deepcopy((self.runs,self.payload,self.audits,self.pointer));self.in_transaction=True
        try: yield
        except BaseException:
            self.runs,self.payload,self.audits,self.pointer=before;self.rollbacks+=1;raise
        else:
            if self.commit_ack_lost: raise RuntimeError('synthetic lost ACK after durable commit')
        finally:self.in_transaction=False
    def start_object(self,rid,obj): pass
    def write(self,obj,rid,start,rows):
        assert self.in_transaction
        self.batch_sizes.append(len(rows))
        if self.fail_write: raise RuntimeError('synthetic-private-driver-detail')
        target=self.payload.setdefault((rid,obj.name),[])
        if start!=len(target)+1: raise PipelineError('ORDINAL_COLLISION')
        target.extend(rows)
    def rows(self,obj,rid):
        rows=self.payload.get((rid,obj.name),[])
        return iter(rows[:-1] if self.corrupt and rows else rows)
    def finish_object(self,rid,obj,count,digest): self.audits[(rid,obj.name)]=(count,digest)
    def finish_run(self,rid,evidence_ref): self.runs[rid].update(status='SUCCEEDED',reference=evidence_ref)
    def publish(self,rid):
        assert self.in_transaction
        if not self.runs[rid]['reference']: raise PipelineError('SOURCE_CONSISTENCY_UNVERIFIED')
        self.pointer=rid;return uuid4()
    def fail_run(self,rid,code,progress=None): self.runs[rid].update(status='FAILED',error=code,progress=progress)
    def reconcile(self,rid,objects):
        result=[]
        for obj in objects:
            digest=RowDigest()
            for row in self.rows(obj,rid):digest.add(admit_row(obj,row))
            if (digest.count,digest.hexdigest)!=self.audits.get((rid,obj.name)):
                raise PipelineError('DURABLE_RECONCILIATION_FAILED')
            result.append({'object':obj.name,'rows':digest.count})
        return result


class CodecTests(unittest.TestCase):
    def test_temporal_boundaries_and_adjacent_values(self):
        c=Column('T','datetime2(7)',True)
        fixtures=['0001-01-01T00:00:00.0000000','9999-12-31T23:59:59.9999999',
                  '2024-02-29T12:00:00.1000000','2025-01-01T00:00:00.0000001','2025-01-01T00:00:00.0000002']
        self.assertEqual([admit(c,x) for x in fixtures],fixtures)
        self.assertIsNone(admit(c,None))
        self.assertLess(fixtures[-2],fixtures[-1])
        for value in (datetime(2025,1,1),fixtures[-1][:-1],'2025-02-29T00:00:00.0000000','2025-01-01T24:00:00.0000000'):
            with self.subTest(kind=type(value).__name__),self.assertRaises(PipelineError):admit(c,value)
    def test_decimal_exactness_not_float_rounding(self):
        c=Column('Amount','decimal(18,2)',False)
        self.assertEqual(admit(c,Decimal('-1234567890123456.78')),Decimal('-1234567890123456.78'))
        for value in (1.23,Decimal('1.001'),Decimal('10000000000000000'),Decimal('NaN')):
            with self.assertRaises(PipelineError):admit(c,value)
    def test_unicode_binary_null_and_no_normalization(self):
        text='Ti\u1ebfng Vi\u1ec7t \U0001f600  '
        self.assertEqual(admit(Column('T','nvarchar(100)',False),text),text)
        self.assertEqual(admit(Column('B','varbinary(max)',True),memoryview(b'\x00\xff')),b'\x00\xff')
        self.assertIsNone(admit(Column('T','nvarchar(max)',True),None))
        for col,value in ((Column('T','nvarchar(2)',False),'abc'),(Column('T','nvarchar(max)',True),'a\x00b'),
                          (Column('I','int',False),None),(Column('I','int',False),True)):
            with self.assertRaises(PipelineError):admit(col,value)
    def test_digest_preserves_null_types_boundaries_and_multiplicity(self):
        def digest(rows):
            h=RowDigest()
            for row in rows:h.add(row)
            return h.hexdigest
        samples=[[(None,)], [('',)], [(b'',)], [('ab','c')], [('a','bc')], [(1,)], [('1',)], [(1,),(1,)]]
        self.assertEqual(len({digest(x) for x in samples}),len(samples))


class ContractTests(unittest.TestCase):
    def test_allowlist_column_count_and_history_no_false_key(self):
        c=catalog();self.assertEqual(len(c),11)
        self.assertEqual(sum(len(o.columns) for o in c.values() if o.origin=='CURRENT'),156)
        self.assertIsNone(c['Sales.Customers_Archive'].primary_key)
        self.assertEqual(c['Sales.Customers'].columns,c['Sales.Customers_Archive'].columns)
    def test_frozen_current_contract_exactly_matches_accepted_dictionary(self):
        import re
        text=(ROOT/'docs/data-models/wwi-metadata-dictionary.md').read_text(encoding='utf-8')
        found={}
        for m in re.finditer(r'## `((?:Sales|Warehouse)\.\w+)` \(\d+[^\n]*\)\n(.*?)(?=\n## |\Z)',text,re.S):
            cols=[]
            for line in m[2].splitlines():
                row=re.match(r'\| `(\w+)` \| `([^`]+)` \| ([^|]+) \|',line)
                if row:cols.append((row[1],row[2],row[3].strip()!='Kh\u00f4ng'))
            found[m[1]]=cols
        self.assertEqual(len(found),9)
        for obj in catalog().values():
            if obj.origin=='CURRENT':self.assertEqual([(c.name,c.source_type,c.nullable) for c in obj.columns],found[obj.name])
    def test_identifier_and_type_injection_rejected(self):
        for names in (['Sales.Orders;DELETE'],['sys.tables'],['Sales.Orders','Sales.Orders']):
            with self.assertRaises(PipelineError):select_objects(names)
        for name,kind in (('x;DROP','int'),('Safe','decimal(18,2);DROP'),('Safe','decimal(50,2)')):
            with self.assertRaises(PipelineError):Column(name,kind,True)
    def test_replay_contract_hash_survives_git_crlf_and_json_formatting(self):
        data=json.loads((ROOT/'ingestion/common/source_contract.json').read_text(encoding='utf-8'))
        expected=contract_hash()
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'contract.json'
            path.write_bytes(json.dumps(data,indent=4,sort_keys=True).replace('\n','\r\n').encode())
            with patch('ingestion.common.contracts.CONTRACT_PATH',path):
                self.assertEqual(contract_hash(),expected)
    def test_verbatim_verified_f2_and_no_native_timestamp_projection(self):
        tree=ast.parse((ROOT/'tests/integration/b9_precision/poc.py').read_text(encoding='utf-8'))
        original=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                      and any(isinstance(t,ast.Name) and t.id=='F2_SQL' for t in n.targets))
        self.assertEqual(F2_SQL,original)
        query=catalog()['Sales.Orders'].query
        self.assertIn('DATEPART(NANOSECOND, [LastEditedWhen]) / 100',query)
        self.assertIn('ORDER BY [OrderID]',query)
    def test_generated_ddl_has_atomic_views_and_no_runtime_admin_or_history_dedup(self):
        ddl=full_load_ddl()
        self.assertEqual((ROOT/'infrastructure/postgres/full_load.sql').read_text(encoding='utf-8'),ddl)
        self.assertEqual(ddl.count('CREATE VIEW raw.'),11)
        self.assertNotIn('DROP ',ddl);self.assertNotIn('TRUNCATE ',ddl);self.assertNotIn('CREATE ROLE',ddl)
        history=ddl.split('CREATE TABLE raw."sales_customers_archive"',1)[1].split('GRANT SELECT',1)[0]
        self.assertNotIn('UNIQUE(_run_id,"CustomerID")',history)
        self.assertIn('PRIMARY KEY(_run_id,_row_ordinal)',history)
        self.assertIn('JOIN ingestion_meta.raw_current',ddl)


class EngineTests(unittest.TestCase):
    def setUp(self):self.obj=catalog()['Sales.Orders'];self.objects=(self.obj,)
    def source(self,count=5,**kwargs):return FakeSource({self.obj.name:[fixture_row(self.obj,i) for i in range(1,count+1)]},**kwargs)
    def test_batch_boundaries_and_readback(self):
        target=FakeTarget();result=run_full_load(self.source(),target,self.objects)
        self.assertEqual(target.batch_sizes,[2,2,1]);self.assertEqual(result['objects'][0]['loaded_rows'],5)
        self.assertEqual(result['status'],'VALIDATED_UNPUBLISHED_CANDIDATE');self.assertIsNone(target.pointer)
    def test_empty_population_is_valid_zero_not_missing_input(self):
        result=run_full_load(self.source(0),FakeTarget(),self.objects)
        self.assertEqual(result['objects'][0]['source_rows'],0)
    def test_history_exact_duplicates_and_zero_duration_preserved(self):
        obj=catalog()['Sales.Customers_Archive'];row=fixture_row(obj)
        target=FakeTarget();result=run_full_load(FakeSource({obj.name:[row,row]}),target,(obj,))
        self.assertEqual(result['objects'][0]['loaded_rows'],2)
    def test_binary_photo_unicode_and_decimal_survive_pipeline_readback(self):
        obj=catalog()['Warehouse.StockItems'];row=list(fixture_row(obj))
        row[next(i for i,c in enumerate(obj.columns) if c.name=='Photo')]=b'\x00\xff\x01'
        row[next(i for i,c in enumerate(obj.columns) if c.name=='StockItemName')]='Ti\u1ebfng Vi\u1ec7t \U0001f600  '
        target=FakeTarget();result=run_full_load(FakeSource({obj.name:[tuple(row)]}),target,(obj,))
        self.assertEqual(result['objects'][0]['loaded_rows'],1)
        stored=next(iter(target.payload.values()))[0]
        self.assertIn(b'\x00\xff\x01',stored);self.assertIn('Ti\u1ebfng Vi\u1ec7t \U0001f600  ',stored)
    def test_duplicate_current_key_rolls_back_all_payload(self):
        source=FakeSource({self.obj.name:[fixture_row(self.obj),fixture_row(self.obj)]});target=FakeTarget()
        with self.assertRaisesRegex(PipelineError,'SOURCE_KEY_DUPLICATE'):run_full_load(source,target,self.objects)
        self.assertFalse(target.payload);self.assertEqual(target.rollbacks,1)
        self.assertEqual(next(iter(target.runs.values()))['status'],'FAILED')
    def test_failed_batch_and_source_failure_leave_previous_publication(self):
        for source,target in ((self.source(),FakeTarget(fail_write=True)),(self.source(fail=True),FakeTarget())):
            old=uuid4();target.pointer=old
            with self.assertRaises(PipelineError):run_full_load(source,target,self.objects)
            self.assertFalse(target.payload);self.assertEqual(target.pointer,old)
            self.assertEqual(next(iter(target.runs.values()))['status'],'FAILED')
            progress=next(iter(target.runs.values()))['progress'][self.obj.name]
            self.assertEqual(progress['source_count'],5)
            self.assertEqual(progress['extracted_count'],2)
    def test_missing_target_record_and_mutable_source_count_fail_reconciliation(self):
        for source,target in ((self.source(),FakeTarget(corrupt=True)),(self.source(changed_count=True),FakeTarget())):
            with self.assertRaisesRegex(PipelineError,'RECONCILIATION'):run_full_load(source,target,self.objects)
            self.assertFalse(target.payload)
    def test_succeeded_run_id_replay_checks_content_without_reextract(self):
        source=self.source();target=FakeTarget();rid=uuid4()
        run_full_load(source,target,self.objects,run_id=rid)
        result=run_full_load(source,target,self.objects,run_id=rid)
        self.assertEqual(source.connects,1);self.assertEqual(len(target.payload[(rid,self.obj.name)]),5)
        self.assertEqual(result['status'],'ALREADY_VALIDATED_NO_RELOAD')
        target.corrupt=True
        with self.assertRaisesRegex(PipelineError,'DURABLE_RECONCILIATION'):run_full_load(source,target,self.objects,run_id=rid)
    def test_failed_retry_is_new_capture_and_same_id_cannot_be_reused(self):
        target=FakeTarget(fail_write=True);rid=uuid4()
        with self.assertRaises(PipelineError):run_full_load(self.source(),target,self.objects,run_id=rid)
        with self.assertRaisesRegex(PipelineError,'RUN_ID_REUSE'):run_full_load(self.source(),target,self.objects,run_id=rid)
        target.fail_write=False;new=uuid4()
        run_full_load(self.source(),target,self.objects,run_id=new,retry_of=rid)
        self.assertNotEqual(target.runs[rid]['capture'],target.runs[new]['capture'])
    def test_commit_ack_unknown_is_not_rewritten_as_failed(self):
        target=FakeTarget(commit_ack_lost=True);rid=uuid4()
        with self.assertRaisesRegex(PipelineError,'COMMIT_OUTCOME_UNKNOWN'):run_full_load(self.source(),target,self.objects,run_id=rid)
        self.assertEqual(target.runs[rid]['status'],'SUCCEEDED')
        target.commit_ack_lost=False
        self.assertEqual(run_full_load(self.source(),target,self.objects,run_id=rid)['status'],'ALREADY_VALIDATED_NO_RELOAD')
    def test_registration_ack_unknown_keeps_running_record_for_inspection(self):
        target=FakeTarget();rid=uuid4();original=target.begin_run
        def lost_ack(*args,**kwargs):
            original(*args,**kwargs)
            raise ConnectionError('synthetic registration ACK loss')
        target.begin_run=lost_ack
        with self.assertRaisesRegex(PipelineError,'RUN_REGISTRATION_OUTCOME_UNKNOWN'):
            run_full_load(self.source(),target,self.objects,run_id=rid)
        self.assertEqual(target.runs[rid]['status'],'RUNNING');self.assertFalse(target.payload)
    def test_preflight_failure_has_no_run_side_effect(self):
        source=self.source();target=FakeTarget();source.preflight=MagicMock(side_effect=PipelineError('SOURCE_EFFECTIVE_PERMISSIONS_UNRESOLVED'))
        with self.assertRaises(PipelineError):run_full_load(source,target,self.objects)
        self.assertFalse(target.runs)
    def test_no_partial_scope_or_unverified_source_publication(self):
        with self.assertRaisesRegex(PipelineError,'FULL_SCOPE'):run_full_load(self.source(),FakeTarget(),self.objects,publish=True)
    def test_full_scope_atomic_publication_requires_covering_evidence(self):
        objects=select_objects();data={o.name:[fixture_row(o)] for o in objects};target=FakeTarget()
        now=datetime.now(timezone.utc)
        proof=SourceEvidence('synthetic-test-only',now-timedelta(seconds=10),now+timedelta(seconds=10),frozenset(data),'synthetic-geography-proof')
        result=run_full_load(FakeSource(data),target,objects,evidence=proof,publish=True)
        self.assertEqual(result['status'],'RAW_PUBLISHED');self.assertEqual(len(result['objects']),11)
        expired=SourceEvidence('synthetic-test-only',now-timedelta(days=1),now-timedelta(hours=1),frozenset(data),'synthetic')
        failed=FakeTarget()
        with self.assertRaisesRegex(PipelineError,'WINDOW'):run_full_load(FakeSource(data),failed,objects,evidence=expired,publish=True)
        self.assertIsNone(failed.pointer);self.assertFalse(failed.payload)
    def test_unverified_geography_blocks_publication(self):
        objects=select_objects();data={o.name:[] for o in objects};now=datetime.now(timezone.utc)
        proof=SourceEvidence('synthetic',now-timedelta(seconds=5),now+timedelta(seconds=5),frozenset(data))
        target=FakeTarget()
        with self.assertRaisesRegex(PipelineError,'GEOGRAPHY'):run_full_load(FakeSource(data),target,objects,evidence=proof,publish=True)
        self.assertFalse(target.payload)


class ReadinessDiagnosticsTests(unittest.TestCase):
    def history_connection(self, *, wrong_identity=False, denied_query=False):
        from ingestion.common.config import SOURCE_SID
        from ingestion.scripts.inspect_wwi_source import HISTORY_RIGHTS,HISTORY_PARENTS
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        who={'original_login':SOURCE_PRINCIPAL,'effective_login':SOURCE_PRINCIPAL,'sid':'0x'+SOURCE_SID.hex(),
             'database_user':'wwi_extract','database_name':'WideWorldImporters','machine':'DESKTOP-OBDFK6B',
             'instance':'SQLEXPRESS','version':'17.0.1000.7'}
        if wrong_identity:who['original_login']='DESKTOP-OBDFK6B\\PC'
        def execute(statement,*parameters):
            if 'ORIGINAL_LOGIN() AS' in statement:rows=[who]
            elif statement.startswith('SELECT HAS_PERMS_BY_NAME') and "'OBJECT'" in statement:
                rights={key:0 for key in HISTORY_RIGHTS};rights['SELECT']=1
                if parameters[0] in HISTORY_PARENTS:rights['INSERT']=1
                rows=[rights]
            elif denied_query and "fn_my_permissions(?,'OBJECT')" in statement:
                raise RuntimeError('synthetic-secret-driver-message')
            else:rows=[{'metadata_only':'synthetic'}]
            cursor.description=[(key,) for key in rows[0]] if rows else []
            cursor.fetchall.return_value=[tuple(row.values()) for row in rows]
            return cursor
        cursor.execute.side_effect=execute
        return connection,cursor

    def test_history_mode_rejects_pc_before_any_source_connection(self):
        from ingestion.scripts.inspect_wwi_source import main as diagnostic_main
        stream=io.StringIO()
        with patch('ingestion.scripts.inspect_wwi_source.windows_principal',return_value='DESKTOP-OBDFK6B\\PC'), \
             patch('pyodbc.connect') as connect,redirect_stdout(stream):
            self.assertEqual(diagnostic_main(['--execute','--history-permissions']),1)
        connect.assert_not_called();self.assertIn('DEDICATED_SOURCE_IDENTITY_REQUIRED',stream.getvalue())

    def test_history_collection_keeps_exact_matrix_and_does_not_claim_root_cause(self):
        from ingestion.scripts.inspect_wwi_source import history_permissions,HISTORY_PARENTS
        connection,cursor=self.history_connection();result=history_permissions(connection)
        self.assertEqual(len(result['object_permissions']),11)
        self.assertTrue(result['ordinary_objects_no_dml_alter_control_ownership'])
        self.assertFalse(result['all11_match_existing_strict_permission_matrix'])
        self.assertEqual({r['object'] for r in result['object_permissions'] if r['rights']['INSERT']==1},set(HISTORY_PARENTS))
        self.assertEqual(result['root_cause'],'UNDETERMINED_REQUIRES_EVIDENCE_REVIEW')
        self.assertFalse(result['production_security_policy_changed']);self.assertFalse(result['source_write_probe_executed'])
        for call in cursor.execute.call_args_list:
            self.assertTrue(call.args[0].startswith(('SELECT ','WITH ')))
            self.assertNotIn('EXECUTE AS',call.args[0]);self.assertNotIn('FROM [Sales]',call.args[0])
            self.assertNotIn('FROM [Warehouse]',call.args[0])

    def test_history_collection_requires_actual_login_sid_and_mapping(self):
        from ingestion.scripts.inspect_wwi_source import history_permissions
        connection,cursor=self.history_connection(wrong_identity=True)
        with self.assertRaisesRegex(PipelineError,'DEDICATED_SOURCE_IDENTITY_REQUIRED'):history_permissions(connection)
        self.assertEqual(cursor.execute.call_count,1)

    def test_history_denied_metadata_is_not_masked_or_leaked(self):
        from ingestion.scripts.inspect_wwi_source import history_permissions
        connection,_=self.history_connection(denied_query=True);result=history_permissions(connection)
        self.assertEqual(len(result['unverified_queries']),4)
        self.assertTrue(all(result['evidence'][key]['status']=='NOT_VERIFIED' for key in result['unverified_queries']))
        self.assertNotIn('synthetic-secret-driver-message',json.dumps(result))

    def connection(self, *, schema_drift=False):
        from ingestion.scripts.inspect_wwi_source import COLUMN_SQL,KEY_SQL,TEMPORAL_SQL,PERMISSION_SQL
        from ingestion.common.config import SOURCE_SID
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        def execute(sql,*params):
            result=MagicMock()
            if 'ORIGINAL_LOGIN()' in sql:
                rows=[(SOURCE_PRINCIPAL,SOURCE_PRINCIPAL,SOURCE_SID,'wwi_extract','WideWorldImporters','17.0.1000.7',0)]
            else:
                obj=catalog()[params[0]] if params else next(o for o in catalog().values() if o.ms_table in sql)
                if sql==COLUMN_SQL:
                    rows=[]
                    for c in obj.columns:
                        kind=c.source_type.split('(')[0];length=0;precision=0;scale=0
                        if kind=='nvarchar':length=-1 if 'max' in c.source_type else int(c.source_type[9:-1])*2
                        elif kind=='varbinary':length=-1
                        elif kind=='decimal':precision,scale=map(int,c.source_type[8:-1].split(','))
                        elif kind=='datetime2':scale=7
                        rows.append((c.name,kind,length,precision,scale,c.nullable))
                    if schema_drift and obj.name=='Sales.Orders':
                        rows[0]=(rows[0][0],'bigint',8,19,0,False)
                elif sql==KEY_SQL:rows=[(obj.primary_key,)] if obj.primary_key else []
                elif sql==TEMPORAL_SQL:rows=[('HISTORY_TABLE' if obj.origin=='HISTORY' else 'NON_TEMPORAL_TABLE',None)]
                elif sql==PERMISSION_SQL:rows=[(1,1 if obj.origin=='HISTORY' else 0,0,0,0,0)]
                elif sql.startswith('SELECT TOP (1) '):rows=[fixture_row(obj)]
                else:raise AssertionError('Unexpected diagnostic SQL')
            result.fetchall.return_value=rows;result.fetchone.return_value=rows[0] if rows else None
            return result
        cursor.execute.side_effect=execute
        return connection,cursor
    def test_diagnostic_default_never_connects(self):
        from ingestion.scripts.inspect_wwi_source import main as diagnostic_main
        with patch('pyodbc.connect') as connect,redirect_stdout(io.StringIO()):
            self.assertEqual(diagnostic_main([]),0)
        connect.assert_not_called()
    def test_readonly_diagnostics_report_history_permission_without_gate_approval(self):
        from ingestion.scripts.inspect_wwi_source import inspect
        connection,cursor=self.connection();result=inspect(connection,samples=True)
        self.assertEqual(len(result['objects']),11)
        self.assertTrue(all(o['schema_match'] and o['key_match'] and o['projection_sample']=='PASS' for o in result['objects']))
        history=next(o for o in result['objects'] if o['object']=='Sales.Customers_Archive')
        self.assertEqual(history['own_context_rights_select_insert_update_delete_alter_control'],[1,1,0,0,0,0])
        self.assertEqual(result['identity_scope'],'EXTRACTOR_DIAGNOSTIC_NOT_GATE_PASS')
        self.assertFalse(result['full_load_executed'])
        self.assertTrue(all(call.args[0].startswith('SELECT ') for call in cursor.execute.call_args_list))
        self.assertNotIn('synthetic-profile',json.dumps(result))
    def test_diagnostic_schema_drift_is_reported_and_not_sampled(self):
        from ingestion.scripts.inspect_wwi_source import inspect
        connection,cursor=self.connection(schema_drift=True);result=inspect(connection,samples=True)
        order=next(o for o in result['objects'] if o['object']=='Sales.Orders')
        self.assertFalse(order['schema_match']);self.assertEqual(order['projection_sample'],'NOT_RUN')
        self.assertFalse(any(call.args[0].startswith('SELECT TOP') and '[Sales].[Orders]' in call.args[0]
                             for call in cursor.execute.call_args_list))


class SecurityAndDriverTests(unittest.TestCase):
    def config(self):return Settings(RawConfig('127.0.0.1',55434,'retail_raw','retail_ingest','i'*24),2)
    def test_dedicated_source_identity_sid_database_user_and_timeouts(self):
        from ingestion.common.config import SOURCE_PRINCIPAL, SOURCE_SID
        connection=MagicMock()
        cursor=connection.cursor.return_value.__enter__.return_value
        cursor.execute.return_value.fetchone.side_effect=[
            (SOURCE_PRINCIPAL,SOURCE_PRINCIPAL,SOURCE_SID,'WideWorldImporters','DESKTOP-OBDFK6B','SQLEXPRESS',
             0,0,0,0,0,'wwi_extract'),('17.0.1000.7','synthetic-test-collation')]
        with patch('ingestion.extractors.sqlserver.windows_principal',return_value=SOURCE_PRINCIPAL), \
             patch('pyodbc.connect',return_value=connection) as connect:
            source=SqlServerSource(self.config());source.connect()
        self.assertEqual(connect.call_args.kwargs,{'timeout':5,'autocommit':True,'attrs_before':{101:1}})
        self.assertEqual(connection.timeout,60)
        self.assertEqual(source.context['product_version'],'17.0.1000.7')
        self.assertIsNone(source.context['source_snapshot_id'])
        self.assertIn('USER_NAME()',cursor.execute.call_args_list[0].args[0])
    def test_large_object_source_pages_are_capped_and_target_reads_server_side(self):
        self.assertEqual(catalog()['Warehouse.StockItems'].page_size(500),1)
        self.assertEqual(catalog()['Sales.Customers'].page_size(500),1)
        self.assertEqual(catalog()['Sales.Invoices'].page_size(500),64)
        obj=catalog()['Sales.Orders'];target=PostgresTarget(self.config());target.connection=MagicMock()
        cursor=target.connection.cursor.return_value.__enter__.return_value
        cursor.fetchmany.side_effect=[[fixture_row(obj)],[]]
        self.assertEqual(len(list(target.rows(obj,uuid4()))),1)
        self.assertTrue(target.connection.cursor.call_args.kwargs['name'].startswith('wwi_verify_'))
        cursor.fetchall.assert_not_called();cursor.fetchmany.assert_called_with(2)
    def test_missing_selected_select_stops(self):
        source=SqlServerSource(self.config());source.connection=MagicMock()
        cursor=source.connection.cursor.return_value.__enter__.return_value
        cursor.execute.return_value.fetchone.return_value=(0,)
        with self.assertRaisesRegex(PipelineError,'SOURCE_SELECT_PERMISSION_REQUIRED'):
            source.preflight(select_objects(['Sales.Orders']))
    def test_unrelated_history_not_checked_for_selected_load(self):
        from ingestion.scripts.inspect_wwi_source import COLUMN_SQL
        obj=catalog()['Sales.Orders'];source=SqlServerSource(self.config());source.connection=MagicMock()
        cursor=source.connection.cursor.return_value.__enter__.return_value
        cursor.execute.return_value.fetchone.return_value=(1,)
        rows=[]
        for c in obj.columns:
            kind=c.source_type.split('(')[0];length=0;precision=0;scale=0
            if kind=='nvarchar':length=-1 if '(max)' in c.source_type else int(c.source_type.split('(')[1][:-1])*2
            if kind=='datetime2':scale=7
            rows.append((c.name,kind,length,precision,scale,c.nullable))
        cursor.execute.return_value.fetchall.return_value=rows
        source.preflight((obj,))
        self.assertFalse(any('Archive' in str(call.args) for call in cursor.execute.call_args_list))
        self.assertTrue(all(call.args[0].startswith('SELECT ') for call in cursor.execute.call_args_list))
    def test_source_schema_mismatch_stops_before_payload_extraction(self):
        source=SqlServerSource(self.config());source.connection=MagicMock()
        cursor=source.connection.cursor.return_value.__enter__.return_value
        cursor.execute.return_value.fetchone.side_effect=[(1,)]
        cursor.execute.return_value.fetchall.return_value=[]
        with self.assertRaisesRegex(PipelineError,'SOURCE_SCHEMA_MISMATCH'):source.preflight(select_objects(['Sales.Orders']))
        self.assertFalse(any('COUNT_BIG' in call.args[0] for call in cursor.execute.call_args_list))
    def test_no_tls_bypass_or_secret_summary(self):
        config=self.config();self.assertIn('TrustServerCertificate=no',config.source_connection_string)
        self.assertNotIn('i'*24,repr(config));self.assertNotIn('i'*24,json.dumps(config.summary()))
        with patch.dict('os.environ',{'RAW_PG_PASSWORD':'i'*24,'WWI_SQLSERVER_TRUST_SERVER_CERTIFICATE':'yes'},clear=True):
            with self.assertRaises(PipelineError):settings(None)
    def test_development_trust_and_admin_opt_in(self):
        with patch.dict('os.environ',{'RAW_PG_PASSWORD':'i'*24,'APP_ENV':'development',
             'WWI_SQLSERVER_TRUST_SERVER_CERTIFICATE':'yes','WWI_ALLOW_ADMIN_SOURCE':'yes'},clear=True):
            config=settings(None)
        self.assertIn('TrustServerCertificate=yes',config.source_connection_string)
        self.assertTrue(config.summary()['allow_admin_source'])
        self.assertTrue(config.development)
    def test_admin_role_never_silently_accepted(self):
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.execute.return_value.fetchone.return_value=('dev','dev',b'x','WideWorldImporters','DESKTOP-OBDFK6B','SQLEXPRESS',1,0,0,0,0,'dbo')
        with patch('pyodbc.connect',return_value=connection):
            with self.assertRaisesRegex(PipelineError,'ADMIN_SOURCE_REQUIRES'):
                SqlServerSource(self.config()).connect()
    def test_admin_opt_in_rejected_in_production(self):
        with patch.dict('os.environ',{'RAW_PG_PASSWORD':'i'*24,'WWI_ALLOW_ADMIN_SOURCE':'yes'},clear=True):
            with self.assertRaisesRegex(PipelineError,'DEVELOPMENT_ONLY_SETTING'):settings(None)
    def test_streaming_source_does_not_fetch_all_payload(self):
        obj=catalog()['Sales.Orders'];source=SqlServerSource(self.config());source.connection=MagicMock()
        cursor=source.connection.cursor.return_value.__enter__.return_value
        cursor.fetchmany.side_effect=[[fixture_row(obj)],[]]
        self.assertEqual(len(list(source.batches(obj))),1);cursor.fetchall.assert_not_called()
        cursor.fetchmany.assert_called_with(2)
    def test_driver_copy_is_guarded_by_transaction(self):
        from psycopg.pq import TransactionStatus
        target=PostgresTarget(self.config());target.connection=MagicMock()
        target.connection.info.transaction_status=TransactionStatus.IDLE
        with self.assertRaisesRegex(PipelineError,'TRANSACTION'):target.write(catalog()['Sales.Orders'],uuid4(),1,[])
    def test_missing_target_ddl_never_causes_runtime_create_or_grant(self):
        target=PostgresTarget(self.config());target.connection=MagicMock()
        target.connection.execute.return_value.fetchone.side_effect=[(True,False),(None,)]
        with self.assertRaisesRegex(PipelineError,'TARGET_DDL_REQUIRED'):target.preflight(select_objects(['Sales.Orders']))
        self.assertTrue(all(call.args[0].startswith('SELECT ') for call in target.connection.execute.call_args_list))
    def test_copy_writes_parameterized_typed_rows_inside_transaction(self):
        from psycopg.pq import TransactionStatus
        target=PostgresTarget(self.config());target.connection=MagicMock()
        target.connection.info.transaction_status=TransactionStatus.INTRANS
        obj=catalog()['Sales.Orders'];row=fixture_row(obj);rid=uuid4()
        target.write(obj,rid,1,[row])
        copier=target.connection.cursor.return_value.__enter__.return_value.copy.return_value.__enter__.return_value
        copier.write_row.assert_called_once_with((rid,1,*row))
    def test_failed_reconciliation_is_recorded_after_acknowledged_rollback(self):
        from psycopg.pq import TransactionStatus
        target=PostgresTarget(self.config());target.connection=MagicMock()
        target.connection.closed=False;target.connection.info.transaction_status=TransactionStatus.IDLE
        obj=catalog()['Sales.Orders'];rid=uuid4()
        target.fail_run(rid,'COUNT_OR_CONTENT_RECONCILIATION_FAILED',{
            obj.name:{'started_at':datetime.now(timezone.utc),'source_count':2,'extracted_count':2}})
        statements=[call.args[0] for call in target.connection.execute.call_args_list]
        self.assertTrue(any("reconciliation_state='FAIL'" in sql for sql in statements))
        self.assertTrue(any('loaded_row_count=0' in sql for sql in statements))
        target.connection.info.transaction_status=TransactionStatus.UNKNOWN
        with self.assertRaisesRegex(PipelineError,'ROLLBACK_OUTCOME_UNKNOWN'):
            target.fail_run(rid,'TEST_FAILURE')
    def test_external_evidence_file_must_match_source_and_scope_shape(self):
        now=datetime.now(timezone.utc)
        data={'kind':'OWNER_VERIFIED_NO_WRITES_WINDOW','reviewed':True,'endpoint':'tcp:DESKTOP-OBDFK6B,1433',
              'database':'WideWorldImporters','reference':'synthetic-test-only','scope':['Sales.Orders'],
              'window_start':(now-timedelta(minutes=1)).isoformat(),'window_end':(now+timedelta(minutes=1)).isoformat()}
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'synthetic-evidence.json';path.write_text(json.dumps(data),encoding='utf-8')
            SourceEvidence.read(path).validate(now,now,select_objects(['Sales.Orders']),publish=False)
            for change in ({'reviewed':False},{'endpoint':'other'},{'scope':['Sales.Orders','Sales.Orders']},
                           {'window_end':'not-a-date'},{'geography_roundtrip_reference':True}):
                path.write_text(json.dumps({**data,**change}),encoding='utf-8')
                with self.assertRaises(PipelineError):SourceEvidence.read(path)
    def test_cli_without_execute_never_connects(self):
        stream=io.StringIO()
        with patch('ingestion.full_load.PostgresTarget') as target,redirect_stdout(stream):
            self.assertEqual(main(['load','--all']),1);target.assert_not_called()
        self.assertIn('EXPLICIT_EXECUTION_FLAG_REQUIRED',stream.getvalue())
    def test_cli_reports_generated_run_id_after_unknown_commit(self):
        from uuid import UUID
        stream=io.StringIO()
        with patch('ingestion.full_load.settings',return_value=self.config()), \
             patch('ingestion.full_load.PostgresTarget'),patch('ingestion.full_load.SqlServerSource'), \
             patch('ingestion.full_load.run_full_load',side_effect=PipelineError('COMMIT_OUTCOME_UNKNOWN_INSPECT_RUN_ID')) as load, \
             redirect_stdout(stream):
            self.assertEqual(main(['load','--object','Warehouse.StockItemHoldings','--execute']),1)
        reported=json.loads(stream.getvalue())
        self.assertEqual(UUID(reported['run_id']),load.call_args.kwargs['run_id'])
        self.assertEqual(reported['error_category'],'COMMIT_OUTCOME_UNKNOWN_INSPECT_RUN_ID')
    def test_cli_reports_explicit_run_id_when_connection_fails(self):
        rid=uuid4();stream=io.StringIO()
        with patch('ingestion.full_load.settings',return_value=self.config()), \
             patch('ingestion.full_load.PostgresTarget') as target,redirect_stdout(stream):
            target.return_value.connect.side_effect=RuntimeError('synthetic-secret-credential')
            self.assertEqual(main(['load','--all','--execute','--run-id',str(rid)]),1)
        self.assertEqual(json.loads(stream.getvalue())['run_id'],str(rid))
        self.assertNotIn('synthetic-secret-credential',stream.getvalue())
    def test_cli_driver_error_does_not_leak_password_or_driver_text(self):
        stream=io.StringIO()
        with patch('ingestion.full_load.settings',return_value=self.config()), \
             patch('ingestion.full_load.PostgresTarget') as target,redirect_stdout(stream):
            target.return_value.connect.side_effect=RuntimeError('synthetic-secret-credential')
            self.assertEqual(main(['preflight','--all']),1)
        self.assertNotIn('synthetic-secret-credential',stream.getvalue())


if __name__=='__main__':unittest.main()
