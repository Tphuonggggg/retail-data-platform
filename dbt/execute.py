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
from configuration import load,ContractError

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

SALES_BI_MODELS = (
    'dim_date', 'dim_customer', 'dim_product', 'fact_invoice_line', 'fact_order_line',
    'int_invoice_header', 'int_order_header', 'mart_sales_daily', 'mart_sales_monthly',
    'mart_sales_product_daily', 'mart_customer_sales', 'mart_sales_customer_summary',
)


def selection_arguments(names):
    """Bounded rebuild: no graph expansion or arbitrary dbt selector expressions."""
    if names is None:
        return []
    if not names or len(set(names)) != len(names) or any(n not in SALES_BI_MODELS for n in names):
        raise ValueError('Only explicit, unique approved Sales BI models are allowed')
    return ['--select', *names, '--indirect-selection', 'cautious']


def session_pgoptions(existing,work_mem):
    if type(work_mem) is not int or work_mem not in {4,16,64}:
        raise ValueError('Unregistered session memory')
    return (existing+f' -c work_mem={work_mem}MB -c max_parallel_workers_per_gather=0 -c jit=off').strip()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['validate','debug','compile','run','test','build','deps'])
    p.add_argument('--capture-id',required=True)
    p.add_argument('--input-kind',choices=['FULL','INCREMENTAL'],default='FULL')
    p.add_argument('--work-mem-mb',type=int,choices=[4,16,64],help='Session-only memory per PostgreSQL operation; default incremental64/full4')
    p.add_argument('--config-dir',type=Path)
    p.add_argument('--select',nargs='+',choices=SALES_BI_MODELS,help='Explicit approved BI models only; no + graph expansion')
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
        if args.input_kind=='INCREMENTAL':
            from ingestion.incremental import assert_version
            if assert_version(guard,UUID(args.capture_id))!='INCREMENTAL':raise ValueError('Incremental version required')
        else:guard.execute('select dw_staging.assert_capture(%s)',(args.capture_id,))
        invocation=str(uuid4()); project=local/'invocations'/invocation
        project.mkdir(parents=True)
        base=ROOT/'dbt'
        for folder in ('models','macros','tests'):
            shutil.copytree(base/folder,project/folder,ignore=shutil.ignore_patterns('__pycache__','*.py','*.pyc'))
        configuration=yaml.safe_load((base/'dbt_project.yml').read_text(encoding='utf-8'))
        work_mem=args.work_mem_mb or (64 if args.input_kind=='INCREMENTAL' else 4)
        configuration['vars']={'sales_contract':contract,'sales_input_kind':args.input_kind,'sales_work_mem_mb':work_mem}
        incremental_staging=contract['documents']['performance'].get('incremental_staging_materialization','view')
        if args.input_kind=='INCREMENTAL':
            staging=configuration['models']['retail_sales']['staging']
            staging['+materialized']=incremental_staging
            if incremental_staging=='table':
                staging['+post-hook']=['ANALYZE {{ this }}']
        for group in ('quality','core','marts'):
            configuration['models']['retail_sales'][group]['+post-hook']=['ANALYZE {{ this }}']
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
                for name in names:
                    configuration['models']['retail_sales'][group].setdefault(name,{})['+indexes']=indexes[name]
        (project/'dbt_project.yml').write_text(yaml.safe_dump(configuration,sort_keys=False),encoding='utf-8')
        (project/'profiles.yml').write_text(PROFILE.replace('THREADS',str(contract['documents']['performance']['threads'])),encoding='utf-8')
        env=dict(os.environ,WWI_DBT_CAPTURE_ID=args.capture_id,WWI_DBT_HOST=cfg.host,DBT_ENV_SECRET_PASSWORD=secret,
                 DBT_SEND_ANONYMOUS_USAGE_STATS='false',DBT_USE_COLORS='false',DBT_PARTIAL_PARSE='false',PYTHONUTF8='1')
        # libpq honors PGOPTIONS. This adapter version ignores a profile 'options'
        # key; preserve inherited read-only safeguards rather than replacing them.
        env['PGOPTIONS']=session_pgoptions(os.environ.get('PGOPTIONS',''),work_mem)
        executable=Path(sys.executable).with_name('dbt.exe' if os.name=='nt' else 'dbt')
        started=time.perf_counter()
        result=subprocess.run([str(executable),args.command,'--project-dir',str(project),'--profiles-dir',str(project),*selection_arguments(args.select)],
                              env=env,cwd=ROOT)
        evidence={'invocation':invocation,'command':args.command,'capture_id':args.capture_id,'input_kind':args.input_kind,
                  'selected_models':args.select,'indirect_selection':'cautious' if args.select else None,
                  'ruleset':contract['ruleset_version'],'measure_version':contract['measure_version'],
                  'threads':contract['documents']['performance']['threads'],
                  'work_mem_mb':work_mem,'max_parallel_workers_per_gather':0,'jit':False,
                  'incremental_staging_materialization':incremental_staging if args.input_kind=='INCREMENTAL' else None,
                  'indexes':contract['documents']['performance']['indexes'],
                  'elapsed_seconds':round(time.perf_counter()-started,3),'exit_code':result.returncode}
        (project/'execution.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
        (local/'latest.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
        print(json.dumps(evidence));return result.returncode
    except Exception as error:
        print(json.dumps({'status':'FAIL','error_type':type(error).__name__,
                          'message':str(error) if isinstance(error,ContractError) else
                          'Configuration/capture/execution gate failed; no secrets logged'}));return 1
    finally:
        if guard is not None:guard.close()

if __name__=='__main__':raise SystemExit(main())
