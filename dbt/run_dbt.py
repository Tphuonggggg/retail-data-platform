"""Run capture-pinned dbt locally as a dedicated non-admin transformation role."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import UUID

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from infrastructure.scripts.check_raw_connection import read_env_file, load_config

PROFILE='''retail_sales:
  target: development
  outputs:
    development:
      type: postgres
      host: "{{ env_var('WWI_DBT_HOST') }}"
      port: 55434
      dbname: retail_raw
      user: retail_transform
      password: "{{ env_var('DBT_ENV_SECRET_PASSWORD') }}"
      schema: dw_staging
      threads: 2
      sslmode: disable
      connect_timeout: 10
      retries: 0
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['debug','compile','run','test','deps','build'])
    p.add_argument('--capture-id',required=True)
    a=p.parse_args()
    try:
        if str(UUID(a.capture_id))!=a.capture_id: raise ValueError('Non-canonical UUID')
        cfg=load_config(read_env_file(ROOT/'.env'))
        if cfg.port!=55434: raise ValueError('Wrong target')
        private=ROOT/'.local/dbt'
        secret=json.loads((private/'connection.json').read_text(encoding='utf-8'))['password']
        (private/'profiles.yml').write_text(PROFILE,encoding='utf-8')
        env=dict(os.environ,WWI_DBT_CAPTURE_ID=a.capture_id,WWI_DBT_HOST=cfg.host,
                 DBT_ENV_SECRET_PASSWORD=secret,DBT_SEND_ANONYMOUS_USAGE_STATS='false',
                 DBT_USE_COLORS='false',PYTHONUTF8='1',DBT_PARTIAL_PARSE='false')
        executable=Path(sys.executable).with_name('dbt.exe' if os.name=='nt' else 'dbt')
        return subprocess.run([str(executable),a.command,'--project-dir',str(ROOT/'dbt'),
            '--profiles-dir',str(private)],env=env,cwd=ROOT).returncode
    except Exception as error:
        print(json.dumps({'status':'FAIL','error_type':type(error).__name__,
                          'message':'Check local dbt configuration; no credentials logged'})); return 1


if __name__=='__main__': raise SystemExit(main())
