"""Validated YAML -> private invocation project vars -> ordinary non-admin dbt."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import UUID,uuid4
import yaml
from configuration import load

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from infrastructure.scripts.check_raw_connection import read_env_file,load_config

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
      threads: THREADS
      sslmode: disable
      connect_timeout: 10
      retries: 0
'''

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['validate','debug','compile','run','test','build','deps'])
    p.add_argument('--capture-id',required=True)
    p.add_argument('--config-dir',type=Path)
    args=p.parse_args()
    guard=None
    try:
        if str(UUID(args.capture_id))!=args.capture_id:raise ValueError('Explicit canonical capture required')
        contract=load(args.config_dir)
        if args.command=='validate':
            print(json.dumps({'status':'PASS_CONFIG','rules':len(contract['rules']),
                              'ruleset':contract['ruleset_version'],'measures':contract['measure_version']}));return 0
        import psycopg
        cfg=load_config(read_env_file(ROOT/'.env'))
        if cfg.port!=55434:raise ValueError('Wrong target')
        local=ROOT/'.local/dbt'
        secret=json.loads((local/'connection.json').read_text(encoding='utf-8'))['password']
        guard=psycopg.connect(host=cfg.host,port=55434,dbname='retail_raw',user='retail_transform',password=secret,
                             autocommit=True,connect_timeout=5,options='-c default_transaction_read_only=on')
        if guard.execute('select current_database(),current_user').fetchone()!=('retail_raw','retail_transform'):raise ValueError('Wrong identity')
        if not guard.execute('select pg_try_advisory_lock(941062)').fetchone()[0]:raise ValueError('Another transformation is active')
        guard.execute('select dw_staging.assert_capture(%s)',(args.capture_id,))
        invocation=str(uuid4()); project=local/'invocations'/invocation
        project.mkdir(parents=True)
        base=ROOT/'dbt'
        for folder in ('models','macros','tests'):
            shutil.copytree(base/folder,project/folder,ignore=shutil.ignore_patterns('__pycache__','*.py','*.pyc'))
        configuration=yaml.safe_load((base/'dbt_project.yml').read_text(encoding='utf-8'))
        configuration['vars']={'sales_contract':contract}
        if contract['documents']['performance']['indexes']:
            indexes={
                'record_status':[{'columns':['record_identity','ruleset_version'],'unique':True}],
                'dim_customer':[{'columns':['customer_key'],'unique':True}],
                'dim_product':[{'columns':['product_key'],'unique':True}],
                'fact_invoice_line':[{'columns':['source_invoice_line_id'],'unique':True}],
                'fact_order_line':[{'columns':['source_order_line_id'],'unique':True}],
            }
            # Inject only an enumerated index contract; no arbitrary column/expression input.
            for group,names in [('quality',['record_status']),('core',['dim_customer','dim_product','fact_invoice_line','fact_order_line'])]:
                for name in names:configuration['models']['retail_sales'][group][name]={'+indexes':indexes[name]}
        (project/'dbt_project.yml').write_text(yaml.safe_dump(configuration,sort_keys=False),encoding='utf-8')
        (project/'profiles.yml').write_text(PROFILE.replace('THREADS',str(contract['documents']['performance']['threads'])),encoding='utf-8')
        env=dict(os.environ,WWI_DBT_CAPTURE_ID=args.capture_id,WWI_DBT_HOST=cfg.host,DBT_ENV_SECRET_PASSWORD=secret,
                 DBT_SEND_ANONYMOUS_USAGE_STATS='false',DBT_USE_COLORS='false',DBT_PARTIAL_PARSE='false',PYTHONUTF8='1')
        executable=Path(sys.executable).with_name('dbt.exe' if os.name=='nt' else 'dbt')
        started=time.perf_counter()
        result=subprocess.run([str(executable),args.command,'--project-dir',str(project),'--profiles-dir',str(project)],
                              env=env,cwd=ROOT)
        evidence={'invocation':invocation,'command':args.command,'capture_id':args.capture_id,
                  'ruleset':contract['ruleset_version'],'measure_version':contract['measure_version'],
                  'threads':contract['documents']['performance']['threads'],
                  'indexes':contract['documents']['performance']['indexes'],
                  'elapsed_seconds':round(time.perf_counter()-started,3),'exit_code':result.returncode}
        (project/'execution.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
        (local/'latest.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
        print(json.dumps(evidence));return result.returncode
    except Exception as error:
        print(json.dumps({'status':'FAIL','error_type':type(error).__name__,
                          'message':'Configuration/capture/execution gate failed; no secrets logged'}));return 1
    finally:
        if guard is not None:guard.close()

if __name__=='__main__':raise SystemExit(main())
