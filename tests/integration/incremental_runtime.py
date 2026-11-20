"""Explicit isolated PostgreSQL fixtures; retail_transform-owned dbt_sales_test only.

Production SQL is namespace-rewritten into a unique fixture prefix. No production
Raw DDL/grants, no SQL Server writes, no publication. Test artifacts are retained.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'dbt'))
from acceptance import connect
from ingestion.common.config import settings
from ingestion.common.contracts import select_objects,contract_hash,pg_quote
from ingestion.common.codecs import RowDigest
from ingestion.common.errors import PipelineError
from ingestion.incremental import IncrementalTarget,objects,run,reconcile
from ingestion.loaders.incremental_schema import migration

PIN='5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8'


def build_sales(db,ns,version,project,check,label):
    """Execute freshly compiled dbt SELECTs in isolated tables, not production schemas.

    This proves model SQL propagation; it does not replace a real dbt invocation
    against an approved production incremental candidate.
    """
    from graphlib import TopologicalSorter
    from decimal import Decimal
    manifest=json.loads((project/'target/manifest.json').read_text(encoding='utf-8'))
    execution=json.loads((project/'execution.json').read_text(encoding='utf-8'))
    input_pin=execution['capture_id']
    models={k:v for k,v in manifest['nodes'].items() if v['resource_type']=='model'}
    order=TopologicalSorter({k:{d for d in v['depends_on']['nodes'] if d in models} for k,v in models.items()}).static_order()
    prefix=ns.prefix+label+'_'
    def translate(text):
        if execution.get('input_kind')=='INCREMENTAL' and '"retail_raw"."raw".' in text:
            raise AssertionError('Incremental model/test bypassed version-aware Raw selection')
        text=text.replace(input_pin,str(version))
        for obj in objects():
            text=text.replace('"retail_raw"."raw"."'+obj.target+'"',
                'dbt_sales_test."'+ns.prefix+'sales_state_'+obj.target+'"(\''+str(version)+'\'::uuid)')
            text=text.replace('raw.sales_state_'+obj.target+'(',
                              'dbt_sales_test."'+ns.prefix+'sales_state_'+obj.target+'"(')
        for v in models.values():
            text=text.replace('"retail_raw"."'+v['schema']+'"."'+v['alias']+'"',
                              'dbt_sales_test."'+prefix+v['alias']+'"')
            text=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(v['schema']+'.'+v['alias'])+r'(?![A-Za-z0-9_])',
                        'dbt_sales_test."'+prefix+v['alias']+'"',text)
        return text
    for key in order:
        node=models[key]
        text=node['compiled_code']
        db.execute('CREATE TABLE dbt_sales_test."'+prefix+node['alias']+'" AS '+translate(text))
    def q(query):
        # Only static registered model names in this test harness.
        for v in sorted(models.values(),key=lambda n:len(n['alias']),reverse=True):
            query=re.sub(r'(?<![A-Za-z0-9_])'+v['alias']+r'(?![A-Za-z0-9_])',
                         'dbt_sales_test."'+prefix+v['alias']+'"',query)
        return db.execute(query).fetchall()
    expected=ns.execute('SELECT coalesce(sum(l."ExtendedPrice"-l."TaxAmount"),0),coalesce(sum(l."Quantity"),0) '
        'FROM raw.source_sales_invoicelines l JOIN raw.source_sales_invoices i ON i."InvoiceID"=l."InvoiceID" '
        'JOIN raw.source_sales_customers c ON c."CustomerID"=i."CustomerID" '
        'JOIN raw.source_sales_customers b ON b."CustomerID"=i."BillToCustomerID" '
        'JOIN raw.source_warehouse_stockitems p ON p."StockItemID"=l."StockItemID"').fetchone()
    actual=q('SELECT coalesce(sum(invoiced_sales_before_tax),0),coalesce(sum(quantity),0) FROM fact_invoice_line WHERE is_sales_eligible')[0]
    check(label+'_independent_sales_units',list(expected),list(actual))
    for model in ('mart_sales_daily','mart_sales_product_daily','mart_customer_sales','mart_sales_customer_summary','mart_sales_monthly'):
        values=q('SELECT coalesce(sum(sales_amount),0),coalesce(sum(units_sold),0) FROM '+model)[0]
        check(label+'_'+model,list(expected),list(values))
    check(label+'_fact_grain',0,q('SELECT count(*)-count(distinct source_invoice_line_id) FROM fact_invoice_line')[0][0])
    check(label+'_dq_record_accounting',sum(ns.execute('SELECT count(*) FROM raw.source_'+o.target).fetchone()[0] for o in objects()),q('SELECT count(*) FROM record_status')[0][0])
    expected_versions=[str(version)] if q('SELECT count(*) FROM fact_invoice_line')[0][0] else []
    check(label+'_lineage_one_version',expected_versions,[str(r[0]) for r in q('SELECT distinct _capture_id FROM fact_invoice_line')])
    # Run all model SQL data tests as SELECT failure counts, avoiding adapter DDL.
    tests=[n for n in manifest['nodes'].values() if n['resource_type']=='test']
    failed=[]
    for node in tests:
        text=node['compiled_code'].strip().rstrip(';')
        if db.execute('SELECT count(*) FROM ('+translate(text)+') failed').fetchone()[0]:failed.append(node['name'])
    check(label+'_compiled_dbt_select_tests',[],failed)
    return {'prefix':'dbt_sales_test.'+prefix,'sales':str(actual[0]),'units':str(actual[1]),
            'dq':q('SELECT dq_status,count(*) FROM record_status GROUP BY 1 ORDER BY 1'),
            'quarantine':q('SELECT count(*) FROM quarantine_records')[0][0],
            'daily':[(str(r[0]),str(r[1])) for r in q('SELECT sales_date,sales_amount FROM mart_sales_daily WHERE sales_amount<>0')],
            'customer':[(str(r[0]),str(r[1])) for r in q('SELECT source_customer_id,sales_amount FROM mart_sales_customer_summary WHERE sales_amount<>0')]}


class Namespace:
    def __init__(self,db,prefix):
        self.db=db;self.prefix=prefix
        self.fixture_namespace='dbt_sales_test.'+prefix
        names=['runs','object_runs','load_contracts','load_audits','incremental_versions','incremental_events',
               'assert_sales_version','guard_incremental_ledger','guard_incremental_append']
        for obj in objects():names += [obj.target,'delta_'+obj.target,'source_'+obj.target,'sales_state_'+obj.target]
        self.pattern=re.compile(r'(?<![A-Za-z0-9_])('+'|'.join(sorted(names,key=len,reverse=True))+r')(?![A-Za-z0-9_])')
    def rewrite(self,text):
        if not isinstance(text,str):text=text.as_string(self.db)
        text=text.replace('ingestion_meta.','dbt_sales_test.').replace('raw.','dbt_sales_test.')
        text=text.replace('"raw".','dbt_sales_test.')
        text=text.replace('pg_try_advisory_lock(941061)','pg_try_advisory_lock(941063)')
        return self.pattern.sub(lambda m:self.prefix+m[0],text)
    def execute(self,query,params=None):return self.db.execute(self.rewrite(query),params)
    def transaction(self):return self.db.transaction()
    def cursor(self,*args,**kwargs):return Cursor(self,self.db.cursor(*args,**kwargs))


class Cursor:
    def __init__(self,ns,cursor):self.ns=ns;self.cursor=cursor
    def __enter__(self):self.cursor.__enter__();return self
    def __exit__(self,*args):return self.cursor.__exit__(*args)
    def execute(self,query,params=None):self.cursor.execute(self.ns.rewrite(query),params);return self
    def fetchmany(self,n):return self.cursor.fetchmany(n)
    def copy(self,query):return self.cursor.copy(self.ns.rewrite(query))


class Source:
    fixture_boundary=True
    context={'database':'ISOLATED_POSTGRESQL_FIXTURE','origin':'SYNTHETIC_FIXTURE'}
    def __init__(self,ns):self.ns=ns;self.fail=False;self.disconnect=False
    def preflight(self,scope):
        if [o.name for o in scope]!=[o.name for o in objects()]:raise ValueError('Wrong fixture scope')
    def count(self,obj):
        if self.disconnect:raise ConnectionError('Synthetic disconnected fixture source')
        return self.ns.execute('SELECT count(*) FROM raw.source_'+obj.target).fetchone()[0]
    def batches(self,obj):
        cols=','.join(pg_quote(c.name) for c in obj.columns)
        rows=self.ns.execute('SELECT '+cols+' FROM raw.source_'+obj.target+' ORDER BY '+pg_quote(obj.primary_key)).fetchall()
        for row in rows:
            yield [row]
            if self.fail:raise ConnectionError('Synthetic partial extraction failure')


def setup(db,ns):
    """Bounded synthetic rows derived from shape templates, never accepted Raw writes."""
    from psycopg.types.json import Jsonb
    root=uuid4()
    with db.transaction():
        for name in ('runs','object_runs','load_contracts','load_audits'):
            db.execute('CREATE TABLE dbt_sales_test.'+ns.prefix+name+' (LIKE ingestion_meta.'+name+' INCLUDING ALL)')
        for obj in objects():
            db.execute('CREATE TABLE dbt_sales_test.'+ns.prefix+obj.target+' (LIKE '+obj.pg_table+' INCLUDING ALL)')
            # Source fixtures intentionally permit duplicate keys for negative tests.
            db.execute('CREATE TABLE dbt_sales_test.'+ns.prefix+'source_'+obj.target+' (LIKE '+obj.pg_table+' INCLUDING CONSTRAINTS)')
        ddl=migration()
        ddl=re.sub(r'\\set[^\n]*\n','',ddl)
        ddl=re.sub(r'DO \$\$ BEGIN.*?END \$\$;', '',ddl,count=1,flags=re.S)
        ddl=re.sub(r'(?m)^(?:GRANT|REVOKE) [^\n]*\n','',ddl)
        ddl=ddl.replace('BEGIN;','',1)
        ddl=ddl.rsplit('COMMIT;',1)[0]
        ns.execute(ddl)
        ns.execute("INSERT INTO ingestion_meta.runs(run_id,capture_id,extraction_mode,status,finished_at) VALUES(%s,%s,'FULL','SUCCEEDED',clock_timestamp())",(root,uuid4()))
        ns.execute('INSERT INTO ingestion_meta.load_contracts VALUES(%s,%s,%s,%s)',
                   (root,[o.name for o in select_objects()],contract_hash(),Jsonb({'database':'WideWorldImporters','origin':'SYNTHETIC_FIXTURE_NOT_WWI_CAPTURE'})))
        for obj in select_objects():
            digest=RowDigest()
            if obj.name in [o.name for o in objects()]:
                cols=','.join(pg_quote(c.name) for c in obj.columns)
                template=db.execute('SELECT '+cols+' FROM '+obj.pg_table+' WHERE _run_id=%s ORDER BY '+pg_quote(obj.primary_key)+' LIMIT 1',(PIN,)).fetchone()
                for key in (1,2,3):
                    values=list(template)
                    for i,col in enumerate(obj.columns):
                        if col.name==obj.primary_key:values[i]=key
                        elif col.name=='BackorderOrderID':values[i]=None
                        elif col.name in ('CustomerID','BillToCustomerID','OrderID','InvoiceID','StockItemID'):values[i]=1
                    placeholders=','.join(['%s']*(len(values)+2))
                    ns.execute('INSERT INTO raw.'+obj.target+' VALUES('+placeholders+')',(root,key,*values))
                    ns.execute('INSERT INTO raw.source_'+obj.target+' VALUES('+placeholders+')',(root,key,*values))
                    digest.add(tuple(values))
            ns.execute("INSERT INTO ingestion_meta.object_runs(run_id,source_schema,source_table,status,source_row_count,extracted_row_count,loaded_row_count,reconciliation_state,started_at,finished_at) VALUES(%s,%s,%s,'SUCCEEDED',%s,%s,%s,'PASS',clock_timestamp(),clock_timestamp())",(root,obj.schema,obj.table,digest.count,digest.count,digest.count))
            ns.execute('INSERT INTO ingestion_meta.load_audits VALUES(%s,%s,%s,%s)',(root,obj.name,digest.count,digest.hexdigest))
    return root


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--compiled-project',type=Path);args=p.parse_args()
    if not args.execute:p.print_help();return 0
    db=connect();prefix='inc_'+uuid4().hex[:12]+'_';ns=Namespace(db,prefix)
    results=[]
    def check(name,expected,actual):
        results.append({'check':name,'expected':expected,'actual':actual,'status':'PASS' if expected==actual else 'FAIL'})
        if expected!=actual:raise AssertionError(name)
    try:
        root=setup(db,ns);source=Source(ns)
        target=IncrementalTarget(SimpleNamespace(connection=ns,config=settings(ROOT/'.env',1)))
        target.fixture_boundary=True
        def execute(parent):
            v=uuid4();out=run(source,target,v,parent)
            # Independent SQL equality, not the production hashing helper.
            # EXCEPT ALL verifies values/NULL/binary and multiplicities directly.
            for obj in objects():
                columns=','.join(pg_quote(c.name) for c in obj.columns)
                current='SELECT '+columns+' FROM raw.sales_state_'+obj.target+'(%s)'
                original='SELECT '+columns+' FROM raw.source_'+obj.target
                mismatches=ns.execute('SELECT count(*) FROM (('+current+' EXCEPT ALL '+original+
                    ') UNION ALL ('+original+' EXCEPT ALL '+current+')) differences',(v,v)).fetchone()[0]
                check(str(v)+'_'+obj.name+'_exact_sql_multiset',0,mismatches)
            return v,out
        v0,out=execute(root)
        try:run(source,target,root,v0)
        except PipelineError as e:check('full_load_id_collision','INCREMENTAL_ID_COLLIDES_WITH_FULL_LOAD',e.code)
        else:raise AssertionError('Full Load ID shadowed')
        check('baseline_unchanged',18,sum(o['changes']['UNCHANGED'] for o in out['objects'].values()))
        check('baseline_no_payload_copy',0,sum(o['payload_rows_written'] for o in out['objects'].values()))
        # Actual persisted INSERT, UPDATE and DELETE in a controlled source table.
        ns.execute('INSERT INTO raw.source_sales_orders SELECT _run_id,4,4,"CustomerID","SalespersonPersonID","PickedByPersonID","ContactPersonID","BackorderOrderID","OrderDate","ExpectedDeliveryDate","CustomerPurchaseOrderNumber","IsUndersupplyBackordered","Comments","DeliveryInstructions","InternalComments","PickingCompletedWhen","LastEditedBy","LastEditedWhen" FROM raw.source_sales_orders WHERE "OrderID"=1')
        ns.execute('UPDATE raw.source_sales_orders SET "Comments"=%s WHERE "OrderID"=1',('SYNTHETIC Việt 😀',))
        ns.execute('DELETE FROM raw.source_sales_orders WHERE "OrderID"=2')
        v1,out=execute(v0);counts=out['objects']['Sales.Orders']['changes']
        check('persisted_insert_update_delete',{'INSERT':1,'UPDATE':1,'DELETE':1,'UNCHANGED':1},counts)
        check('current_state_keys',[1,3,4],[r[0] for r in ns.execute('SELECT "OrderID" FROM raw.sales_state_sales_orders(%s) ORDER BY 1',(v1,))])
        check('same_id_no_reextraction','ALREADY_VALIDATED_NO_REEXTRACTION',run(source,target,v1,v0)['status'])
        try:run(source,target,v1,root)
        except PipelineError as e:check('same_id_parent_conflict','INCREMENTAL_RUN_ID_CONFLICT',e.code)
        else:raise AssertionError('Conflicting parent reused')
        def rejected(name,query,params):
            try:ns.execute(query,params)
            except Exception as error:check(name,'P0001',getattr(error,'sqlstate',None))
            else:raise AssertionError(name+' unexpectedly allowed')
        rejected('terminal_ledger_cannot_reopen',"UPDATE ingestion_meta.incremental_versions SET status='RUNNING',finished_at=NULL WHERE version_id=%s",(v1,))
        rejected('validated_events_cannot_append','INSERT INTO ingestion_meta.incremental_events VALUES(%s,%s,999,\'INSERT\',%s,NULL,%s)',(v1,'Sales.Orders',v0,'0'*64))
        rejected('validated_payload_cannot_append','INSERT INTO raw.delta_sales_orders SELECT * FROM raw.delta_sales_orders WHERE _run_id=%s LIMIT 1',(v1,))
        ns.execute('UPDATE raw.source_sales_orders SET "Comments"=NULL WHERE "OrderID"=1')
        v2,out=execute(v1);check('value_to_null',1,out['objects']['Sales.Orders']['changes']['UPDATE'])
        ns.execute('UPDATE raw.source_sales_orders SET "Comments"=%s,"LastEditedWhen"=%s WHERE "OrderID"=1',('', '2016-01-01T00:00:00.0000001'))
        v3,out=execute(v2);check('null_empty_timestamp_change',1,out['objects']['Sales.Orders']['changes']['UPDATE'])
        ns.execute('UPDATE raw.source_sales_orders SET "LastEditedWhen"=%s WHERE "OrderID"=1',('2016-01-01T00:00:00.0000002',))
        ns.execute('UPDATE raw.source_sales_invoicelines SET "UnitPrice"="UnitPrice"+0.01,"ExtendedPrice"="ExtendedPrice"+0.01 WHERE "InvoiceLineID"=1')
        v4,out=execute(v3);check('100ns_and_decimal',2,sum(o['changes']['UPDATE'] for o in out['objects'].values()))
        check('reconciliation_six_objects',6,len(reconcile(target,v4)))
        ns.execute('DELETE FROM raw.source_sales_orders WHERE "OrderID"=3')
        source.fixture_boundary=False;unverified=uuid4()
        try:run(source,target,unverified,v4)
        except PipelineError as e:check('unverified_delete_is_blocked','INCREMENTAL_DELETE_REQUIRES_CONSISTENT_COMPLETE_SNAPSHOT',e.code)
        else:raise AssertionError('Unverified deletion accepted')
        source.fixture_boundary=True
        ns.execute('INSERT INTO raw.source_sales_orders SELECT * FROM raw.sales_orders WHERE "OrderID"=3')
        before=ns.execute('SELECT count(*) FROM ingestion_meta.incremental_events').fetchone()[0]
        ns.execute('UPDATE raw.source_sales_customers SET "CustomerName"=%s WHERE "CustomerID"=1',('SYNTHETIC pending change',))
        failed=uuid4();source.fail=True
        try:run(source,target,failed,v4)
        except PipelineError as e:check('partial_failure_code','INCREMENTAL_SOURCE_OR_TARGET_FAILURE',e.code)
        else:raise AssertionError('Missing partial failure')
        source.fail=False
        check('rollback_events_unchanged',before,ns.execute('SELECT count(*) FROM ingestion_meta.incremental_events').fetchone()[0])
        check('rollback_failed_payloads_zero',0,sum(ns.execute('SELECT count(*) FROM raw.delta_'+o.target+' WHERE _run_id=%s',(failed,)).fetchone()[0] for o in objects()))
        check('failed_ledger_retained','FAILED',ns.execute('SELECT status FROM ingestion_meta.incremental_versions WHERE version_id=%s',(failed,)).fetchone()[0])
        try:run(source,target,failed,v4)
        except PipelineError as e:check('same_failed_id_safe_refusal','INCREMENTAL_FAILED_OR_UNKNOWN_ID_USE_NEW_VERSION',e.code)
        else:raise AssertionError('Failed ID reused')
        retry,out=execute(v4);check('new_id_retry',1,out['objects']['Sales.Customers']['changes']['UPDATE'])
        failed_connection=uuid4();source.disconnect=True
        try:run(source,target,failed_connection,retry)
        except PipelineError as e:check('connection_failure','INCREMENTAL_SOURCE_OR_TARGET_FAILURE',e.code)
        else:raise AssertionError('Missing connection failure')
        source.disconnect=False
        ns.execute('INSERT INTO raw.source_sales_orders SELECT * FROM raw.source_sales_orders WHERE "OrderID"=1')
        duplicate=uuid4()
        try:run(source,target,duplicate,retry)
        except PipelineError as e:check('duplicate_key_guard','INCREMENTAL_DUPLICATE_OR_UNORDERED_KEY',e.code)
        else:raise AssertionError('Duplicate accepted')
        # Remove only the fixture duplicate through ctid; never production rows.
        ns.execute('DELETE FROM raw.source_sales_orders WHERE ctid IN (SELECT ctid FROM raw.source_sales_orders WHERE "OrderID"=1 LIMIT 1)')
        nochange,out=execute(retry);check('no_change_after_recovery',18,sum(o['changes']['UNCHANGED'] for o in out['objects'].values()))
        check('no_acknowledged_checkpoint',0,ns.execute('SELECT count(*) FROM ingestion_meta.incremental_versions WHERE acknowledged_publication_id IS NOT NULL').fetchone()[0])
        propagation={}
        if args.compiled_project:
            propagation['before']=build_sales(db,ns,nochange,args.compiled_project,check,'before')
            ns.execute('UPDATE raw.source_sales_invoices SET "InvoiceDate"=%s,"CustomerID"=2,"BillToCustomerID"=3 WHERE "InvoiceID"=1',('2013-02-01',))
            ns.execute('UPDATE raw.source_sales_invoicelines SET "StockItemID"=2,"ExtendedPrice"="ExtendedPrice"+1.25 WHERE "InvoiceLineID"=1')
            changed,out=execute(nochange)
            propagation['changed']=build_sales(db,ns,changed,args.compiled_project,check,'changed')
            check('old_daily_contribution_removed',True,propagation['changed']['daily']!=propagation['before']['daily'])
            check('buyer_role_reassigned','2',propagation['changed']['customer'][0][0])
            # Broken Product reference becomes quarantined, then valid again.
            ns.execute('UPDATE raw.source_sales_invoicelines SET "StockItemID"=999999 WHERE "InvoiceLineID"=1')
            invalid,out=execute(changed)
            propagation['invalid']=build_sales(db,ns,invalid,args.compiled_project,check,'invalid')
            check('valid_to_invalid_quarantine',1,propagation['invalid']['quarantine'])
            ns.execute('UPDATE raw.source_sales_invoicelines SET "StockItemID"=2 WHERE "InvoiceLineID"=1')
            valid,out=execute(invalid)
            propagation['valid']=build_sales(db,ns,valid,args.compiled_project,check,'valid')
            check('invalid_to_valid_quarantine',0,propagation['valid']['quarantine'])
            check('corrected_sales_restored',propagation['changed']['sales'],propagation['valid']['sales'])
            ns.execute('DELETE FROM raw.source_warehouse_stockitems WHERE "StockItemID"=2')
            removed_product,out=execute(valid)
            propagation['removed_product']=build_sales(db,ns,removed_product,args.compiled_project,check,'removedproduct')
            check('deleted_dimension_quarantined_sales_excluded',1,propagation['removed_product']['quarantine'])
            ns.execute('DELETE FROM raw.source_sales_invoicelines')
            removed_lines,out=execute(removed_product)
            propagation['removed_lines']=build_sales(db,ns,removed_lines,args.compiled_project,check,'removedlines')
            check('deleted_lines_no_stale_sales','0',propagation['removed_lines']['sales'])
        # Reconnect read-back proves fixture ledger/delta persistence across sessions.
        db.close();db=connect();ns=Namespace(db,prefix)
        check('reconnect_validated','VALIDATED',ns.execute('SELECT status FROM ingestion_meta.incremental_versions WHERE version_id=%s',(nochange,)).fetchone()[0])
        check('reconnect_delta_events',3,ns.execute('SELECT count(*) FROM ingestion_meta.incremental_events WHERE version_id=%s',(v1,)).fetchone()[0])
        output={'status':'PASS_FIXTURE_INGESTION_ONLY','namespace':'dbt_sales_test.'+prefix,
                'root':str(root),'final_version':str(nochange),'tests':results,'propagation':propagation,
                'production_raw_migration_executed':False}
        Path('.local/incremental-fixture-evidence.json').write_text(json.dumps(output,default=str,indent=2),encoding='utf-8')
        print(json.dumps(output,default=str));return 0
    except Exception as e:
        import traceback
        print(json.dumps({'status':'FAIL_FIXTURE','namespace':'dbt_sales_test.'+prefix,'error_type':type(e).__name__,
                          'last_check':results[-1] if results else None,
                          'locations':[(f.name,f.lineno) for f in traceback.extract_tb(e.__traceback__)]},default=str))
        return 1
    finally:db.close()


if __name__=='__main__':raise SystemExit(main())
