"""Explicit WSL-only Airflow integration checks in a fresh temporary SQLite home.

Uses the existing DAG/operators with a mocked bridge for failure cases. A separate
real SequentialExecutor scheduler exercises two queued runs with fixture workers.
Never connects to WWI/PostgreSQL or uses the normal Airflow metadata/configuration.
"""
import argparse
from collections import Counter
from datetime import timedelta
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
DAG_ID='retail_sales_incremental_pipeline'
P='c825b18e-fc62-4cf1-8837-b37b4c9f9668'


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value)
    return value


def isolated_cases(home,output):
    from airflow.configuration import conf
    from airflow.utils.session import create_session
    from airflow.utils.state import DagRunState
    import pendulum
    assert conf.get('database','sql_alchemy_conn')=='sqlite:///'+str(home/'airflow.db')
    mod=load('retail_reliability_dag',ROOT/'airflow/dags/retail_sales_incremental_pipeline.py')
    bridge=load('retail_reliability_bridge',ROOT/'airflow/bridge.py')
    dag=mod.dag
    # Accelerate the configured 30s delay only in this isolated in-process test.
    for task in dag.tasks:task.retry_delay=timedelta(milliseconds=1)
    cases=[];index=0
    for label,failed_action in [('01_source_unavailable','source'),('02_target_unavailable','target'),('03_ingest_failure','ingest'),('04_dbt_failure','build'),('08_unknown_version','resolve'),('08_unvalidated_version','resolve'),('08_failed_capture','resolve'),('08_missing_metadata','resolve'),('08_version_mismatch','build')]:
        calls=[];validated=set();fail=True
        def launch(action,parent,version,execution=False):
            calls.append({'action':action,'parent':parent,'version':version})
            if action==failed_action and fail:
                raise bridge.BridgeFailure(action,'CONNECTION_UNAVAILABLE' if action in ('source','target') else 'ISOLATED_INJECTED_FAILURE',action in ('source','target'),2 if action=='build' else None)
            if action=='ingest':validated.add(version)
            if action in ('validate','resolve','build','marts','complete'):assert version in validated
            return {'status':'PASS','parent':parent,'version':version,'action':action}
        fake=SimpleNamespace(canonical=bridge.canonical,version_for_run=bridge.version_for_run,BridgeFailure=bridge.BridgeFailure,launch=launch)
        with patch.object(mod,'load_bridge',return_value=fake):
            date=pendulum.datetime(2026,1,2,tz='UTC').add(minutes=index);index+=1
            run=dag.test(execution_date=date,run_conf={'parent_version':P})
            assert run.state=='failed',label
            instances=run.get_task_instances()
            states={ti.task_id:str(ti.state) for ti in instances}
            failed_task=next(t.task_id for t in dag.tasks if t.op_kwargs['action']==failed_action)
            assert states[failed_task]=='failed'
            descendants=dag.get_task(failed_task).get_flat_relative_ids(upstream=False)
            assert all(states[t]=='upstream_failed' for t in descendants),states
            assert calls[-1]['action']==failed_action
            if failed_action in ('source','target'):assert Counter(c['action'] for c in calls)[failed_action]==2
            result={'scenario':label,'method':'ISOLATED_AIRFLOW_MOCK_BRIDGE','status':'PASS','run_id':run.run_id,'calls':list(calls),'states':states}
            if label=='04_dbt_failure':
                version=bridge.version_for_run(run.run_id)
                assert validated=={version}
                tail=['run_dbt_build','validate_sales_marts','pipeline_complete']
                cleared=dag.clear(task_ids=tail,start_date=date,end_date=date,confirm_prompt=False)
                assert cleared==3
                fail=False
                for task_id in tail:
                    ti=run.get_task_instance(task_id);ti.task=dag.get_task(task_id)
                    ti.run(ignore_ti_state=False)
                with create_session() as session:
                    run=dag.get_dagrun(run_id=run.run_id,session=session);run.dag=dag
                    run.update_state(session=session)
                    assert run.state==DagRunState.SUCCESS
                assert Counter(c['action'] for c in calls)['ingest']==1
                assert Counter(c['action'] for c in calls)['build']==2
                assert {c['version'] for c in calls}=={version}
                result['recovery']={'status':'PASS','clear_only':tail,'ingest_calls':1,'build_calls':2,'same_version':version,'final_state':str(run.state)}
            cases.append(result)
    # Two fresh runs with identical logical input have different run-derived UUIDs.
    assert bridge.version_for_run('manual__repeat_1')!=bridge.version_for_run('manual__repeat_2')
    cases.append({'scenario':'05_new_run_vs_same_run','method':'ISOLATED','status':'PASS','same_run_uuid_stable':True,'new_run_uuid_differs':True})
    (output/'dag-failure-cases.json').write_text(json.dumps(cases,indent=2)+'\n')


def scheduler_case(home,output,env,executable):
    dags=home/'dags';dags.mkdir(exist_ok=True)
    (dags/'retail_sales_incremental_pipeline.py').symlink_to(ROOT/'airflow/dags/retail_sales_incremental_pipeline.py')
    fixture=home/'fixture_worker.py'
    fixture.write_text("import json,sys,time\nr=json.load(sys.stdin)\nassert r['action'] in ('source','target')\ntime.sleep(1)\nprint(json.dumps({'status':'PASS',**{k:r[k] for k in ('action','parent','version')}}))\n")
    profile=home/'fixture-config.json'
    profile.write_text(json.dumps({'windows_python_wsl':sys.executable,'worker_path_wsl':str(fixture),'worker_path_windows':str(fixture),'repository_wsl':str(ROOT),'allow_pipeline_writes':False,'write_scope':None}))
    env=dict(env,RETAIL_AIRFLOW_CONFIG=str(profile))
    def cli(*args):
        with (output/'scheduler-cli.log').open('ab') as log:
            subprocess.run([str(executable),*args],env=env,cwd=ROOT,stdout=log,stderr=log,check=True,timeout=60)
    cli('dags','reserialize','--subdir',str(dags))
    cli('dags','unpause',DAG_ID)
    for name in ('manual__serial_1','manual__serial_2'):
        cli('dags','trigger',DAG_ID,'--run-id',name,'--conf',json.dumps({'parent_version':P}))
    def rows():
        with sqlite3.connect('file:'+str(home/'airflow.db')+'?mode=ro',uri=True,timeout=5) as db:
            return db.execute("SELECT run_id,state,start_date,end_date FROM dag_run WHERE run_id LIKE 'manual__serial_%' ORDER BY run_id").fetchall()
    assert [r[1] for r in rows()]==['queued','queued']
    samples=[]
    with (output/'isolated-scheduler.log').open('ab') as log:
        process=subprocess.Popen([str(executable),'scheduler','--skip-serve-logs'],env=env,cwd=ROOT,stdout=log,stderr=log,start_new_session=True)
        try:
            deadline=time.monotonic()+160
            while time.monotonic()<deadline:
                snapshot=rows();samples.append(snapshot)
                assert sum(r[1]=='running' for r in snapshot)<=1,'Concurrent runs violated max_active_runs'
                if all(r[1]=='failed' for r in snapshot):break
                if process.poll() is not None:raise AssertionError('Isolated scheduler exited early')
                time.sleep(.25)
            else:raise AssertionError('Isolated scheduler timed out')
        finally:
            process.terminate()
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                # Only this explicitly created isolated scheduler process.
                process.kill();process.wait(timeout=5)
    final=rows()
    assert final[1][2]>=final[0][3],final
    assert max(sum(r[1]=='running' for r in sample) for sample in samples)==1
    with sqlite3.connect('file:'+str(home/'airflow.db')+'?mode=ro',uri=True) as db:
        task_states=db.execute("SELECT run_id,task_id,state FROM task_instance WHERE run_id LIKE 'manual__serial_%' ORDER BY run_id,task_id").fetchall()
    for _,task,state in task_states:
        assert state==('success' if task in ('preflight_source','preflight_target') else 'failed' if task=='run_incremental_ingestion' else 'upstream_failed')
    result={'scenario':'07_concurrent_runs','method':'ISOLATED_REAL_SCHEDULER_FIXTURE_WORKER','status':'PASS','queued_before_start':2,'max_observed_running':1,'final_runs':final,'task_states':task_states,'samples':samples,'writes_disabled':True}
    (output/'scheduler-serialization.json').write_text(json.dumps(result,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-isolated',action='store_true');parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--child-home',type=Path,help=argparse.SUPPRESS)
    args=parser.parse_args()
    if not args.execute_isolated:parser.print_help();return 0
    if os.name=='nt':raise SystemExit('Use the existing WSL Airflow virtual environment')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    if args.child_home:
        isolated_cases(args.child_home,output);return 0
    executable=Path(sys.executable).with_name('airflow')
    with tempfile.TemporaryDirectory(prefix='retail-airflow02-') as tmp:
        home=Path(tmp).resolve()
        env=dict(os.environ,AIRFLOW_HOME=str(home),AIRFLOW__DATABASE__SQL_ALCHEMY_CONN='sqlite:///'+str(home/'airflow.db'),
                 AIRFLOW__CORE__EXECUTOR='SequentialExecutor',AIRFLOW__CORE__LOAD_EXAMPLES='False',
                 AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL='1',AIRFLOW__SCHEDULER__MIN_FILE_PROCESS_INTERVAL='1',
                 AIRFLOW__SCHEDULER__SCHEDULER_HEARTBEAT_SEC='1',PATH=str(executable.parent)+os.pathsep+os.environ.get('PATH',''))
        with (output/'isolated-failures.log').open('wb') as log:
            subprocess.run([str(executable),'db','migrate'],env=env,stdout=log,stderr=log,check=True,timeout=60)
            subprocess.run([sys.executable,str(Path(__file__).resolve()),'--execute-isolated','--child-home',str(home),'--output',str(output)],env=env,stdout=log,stderr=log,check=True,timeout=100)
        scheduler_case(home,output,env,executable)
    print('PASS: isolated DAG failures/clear-rerun and real scheduler serialization; no source/target connections')
    return 0


if __name__=='__main__':raise SystemExit(main())
