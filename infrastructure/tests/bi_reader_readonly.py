"""Explicitly invoked, read-only runtime verification of the approved BI reader."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'dbt'), str(ROOT/'docs/analytics/sales-discovery-01')]
from acceptance import connect
from analyze import fingerprints
from ingestion.common.config import settings
from ingestion.loaders.postgres import PostgresTarget

PIN = 'c825b18e-fc62-4cf1-8837-b37b4c9f9668'
OBJECTS = {
    'dw_core.dim_date': 1247, 'dw_core.dim_customer': 663,
    'dw_core.dim_product': 227, 'dw_core.fact_invoice_line': 228265,
    'dw_core.fact_order_line': 231412,
    'dw_intermediate.int_invoice_header': 70510,
    'dw_intermediate.int_order_header': 73595,
    'sales_marts.mart_sales_daily': 1247, 'sales_marts.mart_sales_monthly': 41,
    'sales_marts.mart_sales_product_daily': 141561,
    'sales_marts.mart_customer_sales': 66463,
    'sales_marts.mart_sales_customer_summary': 663,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        parser.print_help()
        return 0
    result = {'status': 'IN_PROGRESS', 'checked_at': datetime.now(timezone.utc).isoformat(),
              'version': PIN, 'checks': {}, 'objects': {}}
    connections = []
    phase = 'connect'
    try:
        private = json.loads((ROOT/'.local/powerbi/connection.json').read_text())
        assert (private['host'], private['port'], private['database'], private['user']) == (
            '127.0.0.1', 55434, 'retail_raw', 'retail_bi_reader')
        kwargs = dict(private)
        kwargs['dbname'] = kwargs.pop('database')
        reader = psycopg.connect(**kwargs, autocommit=True)
        connections.append(reader)
        assert reader.execute('SELECT current_database(),current_user,session_user').fetchone() == (
            'retail_raw', 'retail_bi_reader', 'retail_bi_reader')
        assert reader.execute('SHOW default_transaction_read_only').fetchone()[0] == 'on'
        result['search_path'] = reader.execute('SHOW search_path').fetchone()[0]
        assert result['search_path'] == 'pg_catalog, dw_core, sales_marts, dw_intermediate'
        result['checks']['password_login_identity_defaults'] = 'PASS'
        # Confirm password authentication, rather than a trust-only connection.
        phase = 'negative_password_authentication'
        wrong = dict(kwargs); wrong['password'] = 'intentionally-invalid-bi-auth-probe'
        try:
            unexpected = psycopg.connect(**wrong, connect_timeout=5)
        except psycopg.OperationalError as error:
            assert 'password authentication failed' in str(error).lower()
        else:
            unexpected.close()
            raise AssertionError('Password authentication not enforced')
        result['checks']['invalid_password_rejected'] = 'PASS'
        phase = 'reader_privileges'
        flags = reader.execute("SELECT rolcanlogin,rolinherit,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=current_user").fetchone()
        assert flags == (True, False, False, False, False, False, False)
        assert reader.execute('SELECT count(*) FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=current_user)').fetchone()[0] == 0
        assert reader.execute("SELECT has_database_privilege(current_database(),'CONNECT'),has_database_privilege(current_database(),'CREATE'),has_database_privilege(current_database(),'TEMPORARY')").fetchone() == (True, False, False)
        assert reader.execute("SELECT count(*) FROM pg_namespace WHERE nspowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)").fetchone()[0] == 0
        assert reader.execute("SELECT count(*) FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)").fetchone()[0] == 0
        schema_privileges = reader.execute("SELECT nspname,has_schema_privilege(oid,'USAGE'),has_schema_privilege(oid,'CREATE') FROM pg_namespace WHERE nspname !~ '^pg_' AND nspname <> 'information_schema' ORDER BY 1").fetchall()
        assert not any(r[2] for r in schema_privileges)
        # PUBLIC's existing USAGE on the empty public schema is not an object grant.
        assert {r[0] for r in schema_privileges if r[1] and r[0] != 'public'} == {'dw_core','dw_intermediate','sales_marts'}
        result['schema_privileges'] = schema_privileges
        visible = reader.execute("SELECT n.nspname||'.'||c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind IN ('r','p','v','m','f') AND n.nspname !~ '^pg_' AND n.nspname <> 'information_schema' AND has_schema_privilege(n.oid,'USAGE') AND has_table_privilege(c.oid,'SELECT') ORDER BY 1").fetchall()
        assert {r[0] for r in visible} == set(OBJECTS)
        forbidden = reader.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind IN ('r','p','v','m','f') AND n.nspname=ANY(%s) AND has_table_privilege(c.oid,'SELECT')", (['raw','dw_staging','dq','ingestion_meta','dbt_sales_test'],)).fetchone()[0]
        assert forbidden == 0
        result['checks']['exact_12_select_no_forbidden_select'] = 'PASS'
        for name, expected in OBJECTS.items():
            privileges = {p: reader.execute('SELECT has_table_privilege(%s,%s)', (name,p)).fetchone()[0]
                          for p in ('SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER')}
            assert privileges == {'SELECT': True, **{p:False for p in ('INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER')}}
            columns = {r[0] for r in reader.execute('SELECT column_name FROM information_schema.columns WHERE table_schema=%s AND table_name=%s', tuple(name.split('.')))}
            pin = '_capture_id' if '_capture_id' in columns else 'capture_id'
            counts = reader.execute(sql.SQL('SELECT {}::text,count(*) FROM {} GROUP BY 1').format(
                sql.Identifier(pin), sql.Identifier(*name.split('.')))).fetchall()
            assert counts == [(PIN, expected)]
            result['objects'][name] = {'rows': expected, 'version': PIN, 'privileges': privileges, 'select': 'PASS'}
        result['checks']['reader_select_all12_and_version'] = 'PASS'
        result['checks']['no_dml_ddl_admin_membership_ownership'] = 'PASS'
        # SELECT denial probes only; never execute DML/DDL, even in rollback.
        denied_names = reader.execute("SELECT n.nspname||'.'||min(c.relname) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind='r' AND n.nspname IN ('raw','dq') GROUP BY n.nspname ORDER BY 1").fetchall()
        assert len(denied_names) == 2
        for (name,) in denied_names:
            try:
                reader.execute(sql.SQL('SELECT 1 FROM {} LIMIT 0').format(sql.Identifier(*name.split('.'))))
            except psycopg.errors.InsufficientPrivilege:
                pass
            else:
                raise AssertionError('Unexpected forbidden schema access')
        result['checks']['actual_forbidden_select_denials'] = 'PASS'
        phase = 'preservation'
        original = json.loads((ROOT/'.local/powerbi-access-execution.json').read_text())
        assert original['status'] == 'PROVISIONED_PENDING_READER_VERIFICATION'
        db = connect(); connections.append(db)
        target = PostgresTarget(settings(ROOT/'.env')); target.connect()
        connections.append(target.connection)
        for conn in (db,target.connection):
            conn.execute('SET default_transaction_read_only=on')
            conn.execute("SET work_mem='64MB'")
            conn.execute('SET jit=off'); conn.execute('SET max_parallel_workers_per_gather=0')
            conn.execute('SET statement_timeout=120000')
        assert target.connection.execute('SELECT pg_try_advisory_lock(941061)').fetchone()[0]
        assert db.execute('SELECT pg_try_advisory_lock(941062)').fetchone()[0]
        after = {'raw_meta': fingerprints(target.connection, ('raw','ingestion_meta')),
                 'warehouse': fingerprints(db, ('dw_staging','dw_intermediate','dw_core','sales_marts','dq')),
                 'publication': db.execute('SELECT * FROM ingestion_meta.raw_current').fetchall(),
                 'versions': db.execute('SELECT version_id,parent_id,base_run_id,status,acknowledged_publication_id FROM ingestion_meta.incremental_versions ORDER BY depth').fetchall()}
        after = json.loads(json.dumps(after, default=str))
        assert after == original['before']
        result['preservation'] = {'before': original['before'], 'after': after}
        result['checks']['all44_table_contents_capture_versions_publication_unchanged'] = 'PASS'
        result['sql_sha256'] = original['sql_sha256']
        result['provisioning_steps'] = original['steps']
        result['status'] = 'POWERBI_ACCESS_ACCEPTED'
    except Exception as error:
        result['status'] = 'FAIL'; result['phase'] = phase; result['error_type'] = type(error).__name__
        # Never persist driver text or private connection arguments.
    finally:
        for conn in reversed(connections):
            conn.close()
        output = ROOT/'powerbi/access-verification.json'
        output.write_text(json.dumps(result, default=str, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({k:v for k,v in result.items() if k not in ('preservation','objects')}, default=str))
    return int(result['status'] != 'POWERBI_ACCESS_ACCEPTED')


if __name__ == '__main__':
    raise SystemExit(main())
