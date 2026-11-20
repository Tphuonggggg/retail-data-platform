"""Explicit new-only warehouse provisioning; never invoked by ordinary dbt runs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import secrets
import hashlib
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from infrastructure.scripts.check_raw_connection import read_env_file, load_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--approved-sha256')
    args = parser.parse_args()
    if not args.execute:
        parser.print_help(); return 0
    import psycopg
    local = ROOT / '.local/dbt'
    private = local / 'connection.json'
    try:
        values = read_env_file(ROOT / '.env')
        cfg = load_config(values)
        if cfg.port != 55434: raise ValueError('Wrong port')
        info = json.loads(subprocess.check_output(['docker','inspect','retail-raw-postgres-1']))[0]
        if (info['Id'] != '9fd7b79bf3a28ba8a531fef868fa5d8aaf6b0af786d9e042b3407fdb65ca8ddd'
            or info['Config']['Image'] != 'postgres:18'
            or info['NetworkSettings']['Ports']['5432/tcp'] != [{'HostIp':'127.0.0.1','HostPort':'55434'}]
            or not any(m.get('Name')=='retail-raw_pg_data' for m in info['Mounts'])):
            raise ValueError('Wrong container identity')
        if private.exists(): raise ValueError('Private profile exists: inspect, do not overwrite')
        script = (ROOT/'infrastructure/postgres/warehouse/provision.sql').read_bytes()
        approved = '409e65e330e2cc7292c23c87c8cbc914c46121c5d0acd38a08476b9546335477'
        if args.approved_sha256 != approved or hashlib.sha256(script).hexdigest() != approved:
            raise ValueError('Approved script hash mismatch')
        local.mkdir(parents=True, exist_ok=True)
        password = secrets.token_urlsafe(36)
        # Docker-local postgres socket; no change to host authentication or admin password.
        # token_urlsafe has a fixed safe alphabet; the password travels only on stdin.
        with private.open('x',encoding='utf-8') as out:
            json.dump({'password':password},out)
        command = ['docker','exec','-i',info['Id'],'psql','-X','-U','postgres','-d','retail_raw',
                   '-v','ON_ERROR_STOP=1','--single-transaction','-f','-']
        result = subprocess.run(command, input=script +
            ("\nALTER ROLE retail_transform LOGIN PASSWORD '"+password+"';\n").encode(),
            capture_output=True,timeout=60)
        if result.returncode != 0:
            raise RuntimeError('Provisioning failed; inspect state before retry; output suppressed')
        print('WAREHOUSE_PROVISIONING_PASS: new role and six schemas; Raw unchanged')
        return 0
    except Exception as error:
        print(json.dumps({'status':'FAIL','error_type':type(error).__name__,
                          'message':'Inspect private local state before retry; no secrets logged'}))
        return 1


if __name__=='__main__': raise SystemExit(main())
