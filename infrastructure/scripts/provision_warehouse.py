"""Explicit new-only warehouse provisioning; never invoked by ordinary dbt runs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from infrastructure.scripts.check_raw_connection import read_env_file, load_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        parser.print_help(); return 0
    import psycopg
    from psycopg import sql
    local = ROOT / '.local/dbt'
    private = local / 'connection.json'
    try:
        values = read_env_file(ROOT / '.env')
        cfg = load_config(values, require_admin=True)
        if cfg.port != 55434: raise ValueError('Wrong port')
        info = json.loads(subprocess.check_output(['docker','inspect','retail-raw-postgres-1']))[0]
        if (info['Id'] != '9fd7b79bf3a28ba8a531fef868fa5d8aaf6b0af786d9e042b3407fdb65ca8ddd'
            or info['Config']['Image'] != 'postgres:18'
            or info['NetworkSettings']['Ports']['5432/tcp'] != [{'HostIp':'127.0.0.1','HostPort':'55434'}]
            or not any(m.get('Name')=='retail-raw_pg_data' for m in info['Mounts'])):
            raise ValueError('Wrong container identity')
        if private.exists(): raise ValueError('Private profile exists: inspect, do not overwrite')
        local.mkdir(parents=True, exist_ok=True)
        password = secrets.token_urlsafe(36)
        with psycopg.connect(host=cfg.host,port=cfg.port,dbname=cfg.database,user='postgres',
                             password=values['RAW_PG_ADMIN_PASSWORD'],connect_timeout=5) as conn:
            if conn.execute('select current_database(),current_user').fetchone()!=('retail_raw','postgres'):
                raise ValueError('Wrong database identity')
            conn.execute((ROOT/'infrastructure/postgres/warehouse/provision.sql').read_text(encoding='utf-8'))
            # No credentials in command arguments, source files or SQL logs.
            conn.execute(sql.SQL('ALTER ROLE retail_transform LOGIN PASSWORD {}').format(sql.Literal(password)))
            # Save private recovery material before the transaction commits.
            with private.open('x',encoding='utf-8') as out:
                json.dump({'password':password},out)
        print('WAREHOUSE_PROVISIONING_PASS: new role and four schemas; Raw unchanged')
        return 0
    except Exception as error:
        print(json.dumps({'status':'FAIL','error_type':type(error).__name__,
                          'message':'Inspect private local state before retry; no secrets logged'}))
        return 1


if __name__=='__main__': raise SystemExit(main())
