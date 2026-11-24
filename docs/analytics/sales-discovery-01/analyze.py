"""Reproduce Sales discovery using read-only PostgreSQL sessions. No dbt execution."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from uuid import UUID

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
QUERY_PATHS=(ROOT/'powerbi/validation.sql',HERE/'queries.sql')
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'dbt'))
from acceptance import connect
from configuration import load
from ingestion.common.config import settings
from ingestion.loaders.postgres import PostgresTarget
from ingestion.incremental import assert_version

PIN='c825b18e-fc62-4cf1-8837-b37b4c9f9668'
SCHEMAS=('dw_staging','dw_intermediate','dw_core','sales_marts','dq')


def scalar(value):
    if isinstance(value,Decimal):return format(value,'f')
    if hasattr(value,'isoformat'):return value.isoformat()
    if isinstance(value,UUID):return str(value)
    raise TypeError(type(value).__name__)


def query_suite():
    queries={}
    for path in QUERY_PATHS:
        text=path.read_text(encoding='utf-8')
        parts=re.split(r'^-- (Q\d\d) (.+)\n',text,flags=re.M)
        for i in range(1,len(parts),3):
            key,title,sql=parts[i:i+3]
            sql=sql.strip().rstrip(';')
            if not re.match(r'^(SELECT|WITH)\b',sql,re.I):raise ValueError('Only reviewed SELECT queries')
            if key in queries:raise ValueError('Duplicate query id')
            queries[key]=(title,sql)
    if len(queries)!=25:raise ValueError('Incomplete query suite')
    return [(key,*queries[key]) for key in sorted(queries)]


def fingerprints(db,schemas):
    from psycopg import sql
    result={}
    tables=db.execute('SELECT schemaname,tablename FROM pg_tables WHERE schemaname=ANY(%s) ORDER BY 1,2',(list(schemas),)).fetchall()
    for schema,table in tables:
        n,digest=db.execute(sql.SQL("SELECT count(*),md5(string_agg(h,'' ORDER BY h)) FROM "
            "(SELECT md5(row_to_json(t)::text) h FROM {}.{} t) rows").format(sql.Identifier(schema),sql.Identifier(table))).fetchone()
        result[schema+'.'+table]={'rows':n,'content_digest':digest}
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true');p.add_argument('--capture-id',default=PIN)
    p.add_argument('--output',type=Path,default=ROOT/'.local/sales-analysis.json');args=p.parse_args()
    if not args.execute:p.print_help();return 0
    if args.capture_id!=PIN:raise SystemExit('This reviewed discovery is pinned to '+PIN)
    db=None;raw=None;result={'status':'IN_PROGRESS','capture_id':PIN,'started_at':datetime.now(timezone.utc).isoformat(),'queries':{}}
    began=time.perf_counter()
    try:
        contract=load();result['contracts']={k:contract[k] for k in ('ruleset_version','measure_version','customer_role')}
        if contract['customer_role']!='BUYER':raise ValueError('Unexpected default role')
        db=connect();raw=PostgresTarget(settings(ROOT/'.env'));raw.connect()
        for conn in (db,raw.connection):
            conn.execute('SET default_transaction_read_only=on')
            conn.execute("SET work_mem='64MB'");conn.execute('SET jit=off')
            conn.execute('SET max_parallel_workers_per_gather=0');conn.execute('SET statement_timeout=120000')
            conn.execute('SET enable_nestloop=off')
            if conn.execute('SHOW default_transaction_read_only').fetchone()[0]!='on':raise ValueError('Read-only guard missing')
        if not raw.connection.execute('SELECT pg_try_advisory_lock(941061)').fetchone()[0]:raise ValueError('Ingestion active')
        if not db.execute('SELECT pg_try_advisory_lock(941062)').fetchone()[0]:raise ValueError('Transformation active')
        if assert_version(db,UUID(PIN))!='INCREMENTAL':raise ValueError('Validated version missing')
        result['version_record']=dict(zip(('version_id','parent_id','base_run_id','status','depth','source_context','evidence'),
            db.execute('SELECT version_id,parent_id,base_run_id,status,depth,source_context,evidence FROM ingestion_meta.incremental_versions WHERE version_id=%s',(PIN,)).fetchone()))
        # Discover the expected 21 model names from the actual dbt project.
        schema_map={'staging':'dw_staging','intermediate':'dw_intermediate','core':'dw_core','marts':'sales_marts','quality':'dq'}
        expected={(schema_map[path.relative_to(ROOT/'dbt/models').parts[0]],path.stem)
                  for path in (ROOT/'dbt/models').rglob('*.sql')}
        if len(expected)!=21:raise ValueError('Unexpected model population')
        result['lineage']={}
        for schema,table in sorted(expected):
            columns={r[0] for r in db.execute('SELECT column_name FROM information_schema.columns WHERE table_schema=%s AND table_name=%s',(schema,table))}
            pin_column='_capture_id' if '_capture_id' in columns else 'capture_id'
            if pin_column not in columns:raise ValueError('Unpinned model')
            rows=db.execute('SELECT '+pin_column+'::text,ruleset_version,count(*) FROM '+schema+'.'+table+' GROUP BY 1,2').fetchall()
            if rows and any(r[0]!=PIN or r[1]!=contract['ruleset_version'] for r in rows):raise ValueError('Mixed or stale version/rules')
            if not rows and table!='quarantine_records':raise ValueError('Unexpected empty model')
            if 'measure_version' in columns:
                v=db.execute('SELECT DISTINCT measure_version FROM '+schema+'.'+table).fetchall()
                if any(r[0]!=contract['measure_version'] for r in v):raise ValueError('Stale measure contract')
            result['lineage'][schema+'.'+table]={'pin_column':pin_column,'rows':sum(r[2] for r in rows),'version_groups':rows}
        for table,key in [('dim_product','source_stock_item_id'),('dim_customer','source_customer_id')]:
            n,d=db.execute('SELECT count(*),count(distinct '+key+') FROM dw_core.'+table+' WHERE _capture_id=%s',(PIN,)).fetchone()
            if n!=d:raise ValueError('Observed dimension is not unique')
        result['reporting_roles']=db.execute('SELECT DISTINCT customer_role FROM sales_marts.mart_customer_sales').fetchall()
        if result['reporting_roles']!=[('BUYER',)]:raise ValueError('Unexpected mart reporting role')
        result['lineage']['view_definitions']={r[0]+'.'+r[1]:r[2] for r in db.execute("SELECT schemaname,viewname,definition FROM pg_views WHERE schemaname='dw_intermediate' ORDER BY 1,2")}
        result['input_files_sha256']={str(path.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(list((ROOT/'dbt/models').rglob('*.sql'))+list((ROOT/'dbt/config').glob('*.yml'))+[ROOT/'dbt/macros/capture.sql',*QUERY_PATHS])}
        before_raw=fingerprints(raw.connection,('raw','ingestion_meta'))
        before_dw=fingerprints(db,SCHEMAS)
        prior_path=ROOT/'.local/incremental-fixture-evidence.json'
        prior=json.loads(prior_path.read_text(encoding='utf-8'))
        if prior['dbt']['same_version_rebuild']['capture_id']!=PIN or prior['dbt']['same_version_rebuild']['exit_code']!=0:
            raise ValueError('Prior acceptance does not cover this version')
        accepted={m['schema']+'.'+m['model']:{'rows':m['rows'],'content_digest':m['content_digest']}
                  for m in prior['dbt']['models'] if 'content_digest' in m}
        if accepted!=before_dw:raise ValueError('Warehouse differs from reconciled acceptance baseline')
        result['accepted_baseline']={'file':str(prior_path.relative_to(ROOT)).replace('\\','/'),
            'sha256':hashlib.sha256(prior_path.read_bytes()).hexdigest(),'matching_table_digests':len(accepted),
            'invocation':prior['dbt']['same_version_rebuild']['invocation']}
        with db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            for key,title,statement in query_suite():
                started=time.perf_counter()
                cursor=db.execute(statement,{'pin':PIN} if '%(pin)s' in statement else None)
                columns=[c.name for c in cursor.description]
                rows=[dict(zip(columns,row)) for row in cursor.fetchall()]
                result['queries'][key]={'title':title,'seconds':round(time.perf_counter()-started,3),'rows':rows}
                print(key,len(rows),'rows',flush=True)
        after_dw=fingerprints(db,SCHEMAS);after_raw=fingerprints(raw.connection,('raw','ingestion_meta'))
        result['preservation']={'raw_and_metadata_unchanged':before_raw==after_raw,'warehouse_unchanged':before_dw==after_dw,
                                'raw_and_metadata':after_raw,'warehouse':after_dw,
                                'method':'Fresh read-only transactions before/after; tuple multiset MD5, rows; runtime advisory locks held; no mutation statements'}
        if before_raw!=after_raw or before_dw!=after_dw:raise ValueError('Content drift during discovery')
        q=lambda key:result['queries'][key]['rows']
        headline=q('Q01')[0]
        if headline['sales']+headline['tax']!=headline['including_tax']:raise ValueError('Amount identity failed')
        if headline['invoices_with_lines']!=headline['invoice_count']:raise ValueError('Invoice population mismatch')
        if q('Q20')[0]['mismatch_rows']!=0:raise ValueError('Monthly measures do not reconcile')
        if sum(r['sales'] for r in q('Q06'))!=headline['sales']:raise ValueError('Product fan-out')
        if any(r['sales']!=headline['sales'] for r in q('Q08')):raise ValueError('Role population mismatch')
        if sum(r['sales_amount'] for r in q('Q03'))!=headline['sales']:raise ValueError('Monthly totals differ')
        staged=sum(result['lineage']['dw_staging.'+o['model']]['rows'] for o in contract['objects'])
        if sum(r['records'] for r in q('Q25'))!=staged:raise ValueError('DQ population does not reconcile')
        result['cross_checks']={'amount_identity':True,'invoice_population':True,'monthly_fact_header_mart':True,
                               'product_sum':True,'each_role_sum_separately':True,'monthly_sum':True,'dq_population':True,
                               'accepted_warehouse_content':True}
        result['status']='SALES_INSIGHT_DISCOVERY_COMPLETE'
    except Exception as error:
        import traceback
        result['status']='DISCOVERY_BLOCKED'
        result['error']={'type':type(error).__name__,'locations':[(f.name,f.lineno) for f in traceback.extract_tb(error.__traceback__)]}
    finally:
        for resource in (db,raw):
            if resource is not None:
                try:resource.close()
                except Exception:result['status']='DISCOVERY_BLOCKED'
    result['elapsed_seconds']=round(time.perf_counter()-began,3)
    result['finished_at']=datetime.now(timezone.utc).isoformat()
    result['git_head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,default=scalar,ensure_ascii=False,indent=2),encoding='utf-8')
    print(result['status'],result['elapsed_seconds'],'seconds')
    return int(result['status']!='SALES_INSIGHT_DISCOVERY_COMPLETE')


if __name__=='__main__':raise SystemExit(main())
