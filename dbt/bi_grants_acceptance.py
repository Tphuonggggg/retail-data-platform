"""Owner-authorized, bounded BI grants rebuild and read-only before/after evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import sys
from uuid import UUID

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'dbt'), str(ROOT/'docs/analytics/sales-discovery-01')]
from acceptance import connect
from analyze import fingerprints, query_suite
from configuration import load
from execute import SALES_BI_MODELS
from ingestion.common.config import settings
from ingestion.incremental import assert_version
from ingestion.loaders.postgres import PostgresTarget

PIN = 'c825b18e-fc62-4cf1-8837-b37b4c9f9668'
OUTPUT = ROOT/'powerbi/persistent-grants-verification.json'
ALLOWLIST = {
    **{f'dw_core.{n}':n for n in SALES_BI_MODELS[:5]},
    **{f'dw_intermediate.{n}':n for n in SALES_BI_MODELS[5:7]},
    **{f'sales_marts.{n}':n for n in SALES_BI_MODELS[7:]},
}


def canonical(value):
    return json.loads(json.dumps(value, default=str))


def reader_connect():
    profile = json.loads((ROOT/'.local/powerbi/connection.json').read_text())
    assert (profile['host'],profile['port'],profile['database'],profile['user']) == (
        '127.0.0.1',55434,'retail_raw','retail_bi_reader')
    profile['dbname'] = profile.pop('database')
    return psycopg.connect(**profile, autocommit=True)


def snapshot(db, raw):
    assert db.execute('SELECT pg_try_advisory_lock(941062)').fetchone()[0]
    try:
        assert assert_version(db, UUID(PIN)) == 'INCREMENTAL'
        rows = db.execute("SELECT n.nspname||'.'||c.relname,c.oid,c.relkind,pg_get_userbyid(c.relowner) FROM pg_class c JOIN pg_namespace n ON c.relnamespace=n.oid WHERE c.relkind IN ('r','p','v','m') AND n.nspname !~ '^pg_' AND n.nspname<>'information_schema' ORDER BY 1").fetchall()
        relations = {r[0]: {'oid':r[1], 'kind':r[2], 'owner':r[3]} for r in rows}
        for name in ALLOWLIST:
            assert relations[name]['owner'] == 'retail_transform'
            assert relations[name]['kind'] == ('v' if name.startswith('dw_intermediate.') else 'r')
        content = fingerprints(db, ('dw_staging','dw_core','sales_marts','dq'))
        for name in ALLOWLIST:
            if name.startswith('dw_intermediate.'):
                count,digest = db.execute(sql.SQL("SELECT count(*),md5(string_agg(h,'' ORDER BY h)) FROM (SELECT md5(row_to_json(t)::text) h FROM {} t) a").format(sql.Identifier(*name.split('.')))).fetchone()
                content[name] = {'rows':count, 'content_digest':digest}
        with reader_connect() as reader:
            assert reader.execute('SELECT current_user').fetchone()[0] == 'retail_bi_reader'
            assert reader.execute('SHOW default_transaction_read_only').fetchone()[0] == 'on'
            accessible = reader.execute("SELECT n.nspname||'.'||c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind IN ('r','p','v','m','f') AND n.nspname !~ '^pg_' AND n.nspname<>'information_schema' AND has_table_privilege(c.oid,'SELECT') ORDER BY 1").fetchall()
            assert {r[0] for r in accessible} == set(ALLOWLIST)
            schema_access = reader.execute("SELECT nspname,has_schema_privilege(oid,'USAGE'),has_schema_privilege(oid,'CREATE') FROM pg_namespace WHERE nspname !~ '^pg_' AND nspname<>'information_schema' ORDER BY 1").fetchall()
            assert not any(r[2] for r in schema_access)
            assert not any(r[1] for r in schema_access if r[0] in ('raw','dw_staging','dq','ingestion_meta','dbt_sales_test'))
            privileges = {}
            for name in ALLOWLIST:
                values = {p:reader.execute('SELECT has_table_privilege(%s,%s)',(name,p)).fetchone()[0] for p in ('SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER')}
                assert values == {'SELECT':True, **{p:False for p in ('INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER')}}
                groups = reader.execute(sql.SQL('SELECT _capture_id::text,count(*) FROM {} GROUP BY 1').format(sql.Identifier(*name.split('.')))).fetchall()
                assert len(groups) == 1 and groups[0][0] == PIN
                privileges[name] = {'privileges':values, 'rows':groups[0][1], 'version':PIN}
        metrics = {}
        # Approved Q01 headline plus independent mart totals; no fact-to-fact joins.
        q = next(q for key,title,q in query_suite() if key == 'Q01')
        cursor = db.execute(q, {'pin':PIN})
        metrics['headline'] = dict(zip([c.name for c in cursor.description],cursor.fetchone()))
        for table in ('mart_sales_daily','mart_sales_monthly','mart_sales_product_daily','mart_customer_sales'):
            columns = 'sum(sales_amount),sum(units_sold)'
            metrics[table] = db.execute('SELECT '+columns+' FROM sales_marts.'+table+' WHERE _capture_id=%s',(PIN,)).fetchone()
        for totals in (metrics[k] for k in metrics if k!='headline'):
            h = metrics['headline']
            assert totals == (h['sales'],h['source_units'])
        assert metrics['headline']['invoice_count'] == 70510
        assert metrics['headline']['order_count'] == 73595
        return canonical({'relations':relations, 'warehouse_content':content,
            'raw_meta_content':fingerprints(raw,('raw','ingestion_meta')),
            'reader':privileges,'schema_access':schema_access,'metrics':metrics,
            'publication':db.execute('SELECT * FROM ingestion_meta.raw_current').fetchall(),
            'versions':db.execute('SELECT version_id,parent_id,base_run_id,status,acknowledged_publication_id FROM ingestion_meta.incremental_versions ORDER BY depth').fetchall()})
    finally:
        db.execute('SELECT pg_advisory_unlock(941062)')


def manifest_check(path):
    manifest = json.loads(path.read_text())
    models = {n['name']:n for n in manifest['nodes'].values() if n['resource_type']=='model'}
    assert len(models) == 21
    granted = {name:n['config']['grants'] for name,n in models.items() if n['config'].get('grants')}
    assert granted == {n:{'select':['retail_bi_reader']} for n in SALES_BI_MODELS}
    assert manifest['metadata']['dbt_version'].startswith('1.11.')
    for name in ALLOWLIST:
        n = models[ALLOWLIST[name]]
        assert n['schema'] == name.split('.')[0]
        assert n['config']['materialized'] == ('view' if name.startswith('dw_intermediate.') else 'table')
    return manifest, granted


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute', action='store_true')
    args = p.parse_args()
    if not args.execute:
        p.print_help(); return 0
    result = {'status':'IN_PROGRESS','started_at':datetime.now(timezone.utc).isoformat(),
              'version':PIN,'dependencies':{n:version(n) for n in ('dbt-core','dbt-postgres','psycopg')},'commands':[]}
    db = raw = None; phase = 'preflight'
    try:
        db = connect(); raw = PostgresTarget(settings(ROOT/'.env')); raw.connect()
        for conn in (db,raw.connection):
            conn.execute('SET default_transaction_read_only=on')
            conn.execute("SET work_mem='64MB'")
            conn.execute('SET jit=off');conn.execute('SET max_parallel_workers_per_gather=0')
            conn.execute('SET statement_timeout=120000')
        # Block ingestion for this whole experiment. Runner owns the separate dbt lock.
        assert raw.connection.execute('SELECT pg_try_advisory_lock(941061)').fetchone()[0]
        result['before'] = snapshot(db,raw.connection)
        result['contract'] = {k:load()[k] for k in ('ruleset_version','measure_version')}
        immutable_paths = list((ROOT/'dbt/models').rglob('*'))+list((ROOT/'dbt/config').rglob('*'))+list((ROOT/'dbt/macros').rglob('*'))
        result['model_contract_hashes'] = {str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in immutable_paths if path.is_file()}
        for command in ('compile','build','test'):
            phase = command
            argv = [sys.executable,'dbt/run_dbt.py',command,'--input-kind','INCREMENTAL',
                    '--capture-id',PIN,'--select',*SALES_BI_MODELS]
            proc = subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=600)
            # dbt redacts DBT_ENV_SECRET_PASSWORD; keep verbose logs private anyway.
            (ROOT/f'.local/powerbi-access-02-{command}.log').write_bytes(proc.stdout+proc.stderr)
            assert proc.returncode == 0
            latest = json.loads((ROOT/'.local/dbt/latest.json').read_text())
            project = ROOT/'.local/dbt/invocations'/latest['invocation']
            manifest,grants = manifest_check(project/'target/manifest.json')
            step = {'command':command,'argv':argv[1:],'exit_code':proc.returncode,
                    'execution':latest,'manifest_grants':grants}
            if command != 'compile':
                run = json.loads((project/'target/run_results.json').read_text())
                step['results'] = [{k:r[k] for k in ('unique_id','status','execution_time')} for r in run['results']]
                assert all(r['status'] in ('success','pass') for r in run['results'])
                built = {r['unique_id'].split('.')[-1] for r in run['results'] if r['unique_id'].startswith('model.')}
                assert built == (set(SALES_BI_MODELS) if command=='build' else set())
                assert any(r['unique_id'].startswith('test.') for r in run['results'])
            result['commands'].append(step)
            OUTPUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
        phase = 'after'
        result['after'] = snapshot(db,raw.connection)
        before,after = result['before'],result['after']
        for key in ('warehouse_content','raw_meta_content','reader','schema_access','metrics','publication','versions'):
            assert before[key] == after[key], key
        assert set(before['relations']) == set(after['relations'])
        changed = {name for name in before['relations'] if before['relations'][name] != after['relations'][name]}
        assert changed == set(ALLOWLIST)
        for name in ALLOWLIST:
            assert before['relations'][name]['owner'] == after['relations'][name]['owner'] == 'retail_transform'
            assert before['relations'][name]['kind'] == after['relations'][name]['kind']
        result['rebuilt_objects'] = sorted(changed)
        # Keep bulky fixture catalog details private; persist exact outside-scope
        # catalog fingerprints and the twelve useful before/after object identities.
        for state in (before,after):
            outside = {n:r for n,r in state['relations'].items() if n not in ALLOWLIST}
            state['outside_relations'] = {'count':len(outside),
                'sha256':hashlib.sha256(json.dumps(outside,sort_keys=True).encode()).hexdigest()}
            state['relations'] = {n:r for n,r in state['relations'].items() if n in ALLOWLIST}
        result['status'] = 'POWERBI_PERSISTENT_GRANTS_ACCEPTED'
    except Exception as error:
        result['status'] = 'FAIL'; result['phase'] = phase; result['error_type'] = type(error).__name__
    finally:
        if db is not None: db.close()
        if raw is not None: raw.close()
        OUTPUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps({'status':result['status'],'phase':result.get('phase'),
                          'completed_commands':[s['command'] for s in result['commands']]}))
    return int(result['status'] != 'POWERBI_PERSISTENT_GRANTS_ACCEPTED')


if __name__ == '__main__':
    raise SystemExit(main())
