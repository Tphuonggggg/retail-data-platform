"""Start/stop no services implicitly: explicit WSL local scheduler/webserver start."""
import argparse
import os
from pathlib import Path
import subprocess
import json
import signal
import sqlite3
import time
from contextlib import closing


def matches_command(command,executable,service):
    args=command.replace('\0',' ').split()
    return ((len(args)>=2 and args[0]==str(executable) and args[1]==service)
            or (len(args)>=3 and args[1]==str(executable) and args[2]==service))


def service_info(pidfile,executable,service,config):
    if not pidfile.exists():return {'service':service,'running':False}
    try:
        pid=int(pidfile.read_text());proc=Path('/proc')/str(pid)
        command=(proc/'cmdline').read_text()
        environment=dict(p.split('=',1) for p in (proc/'environ').read_text().split('\0') if '=' in p)
    except (FileNotFoundError,ProcessLookupError,ValueError):return {'service':service,'running':False}
    owned=(matches_command(command,executable,service) and proc.stat().st_uid==os.getuid()
           and os.getpgid(pid)==pid and environment.get('RETAIL_AIRFLOW_CONFIG')==str(config))
    keys=('RETAIL_AIRFLOW_SCHEDULE','RETAIL_AIRFLOW_DAILY_TIME','RETAIL_AIRFLOW_SCHEDULE_PARENT','RETAIL_AIRFLOW_SCHEDULE_NOT_BEFORE')
    current=tuple(environment.get(k,'manual' if i==0 else '') for i,k in enumerate(keys))
    desired=tuple(os.environ.get(k,'manual' if i==0 else '') for i,k in enumerate(keys))
    same=current==desired or current[0]==desired[0]=='manual'
    return {'service':service,'running':True,'pid':pid,'identity_verified':owned,'schedule_environment_matches':same}


def ensure_idle(home,config):
    private=json.loads(config.read_text())
    if private.get('allow_pipeline_writes') is not False or private.get('write_scope') is not None:
        raise ValueError('Close write gate and scope before service startup/shutdown')
    with closing(sqlite3.connect('file:'+str(home/'airflow/airflow.db')+'?mode=ro',uri=True)) as db:
        if db.execute("SELECT count(*) FROM dag_run WHERE state IN ('running','queued')").fetchone()[0]:
            raise ValueError('Drain active/queued DAG runs first')
        paused=db.execute("SELECT is_paused FROM dag WHERE dag_id='retail_sales_incremental_pipeline'").fetchone()
        if paused and paused!=(1,):raise ValueError('Pause the Retail DAG first')


def stop_services(home,config,executable,logs):
    ensure_idle(home,config)
    services=[service_info(logs/(s+'.pid'),executable,s,config) for s in ('scheduler','webserver')]
    if any(s['running'] and not s['identity_verified'] for s in services):raise ValueError('Unverified PID; inspect manually, no signal sent')
    for state in services:
        if not state['running']:continue
        os.kill(state['pid'],signal.SIGTERM)
        deadline=time.monotonic()+20
        while Path('/proc',str(state['pid'])).exists() and time.monotonic()<deadline:time.sleep(.2)
        if Path('/proc',str(state['pid'])).exists():raise ValueError('Service still exists; no force kill; inspect manually')
        (logs/(state['service']+'.pid')).unlink()
        print(state['service']+': stopped verified local process')


def service_environment(executable, config):
    # SequentialExecutor launches the bare `airflow` command in task subprocesses.
    return dict(os.environ, RETAIL_AIRFLOW_CONFIG=str(config),
                AIRFLOW__CORE__LOAD_EXAMPLES='False',
                PATH=str(executable.parent) + os.pathsep + os.environ.get('PATH', ''))


def main():
    parser = argparse.ArgumentParser()
    options=parser.add_mutually_exclusive_group()
    options.add_argument('--start', action='store_true')
    options.add_argument('--status', action='store_true')
    options.add_argument('--stop', action='store_true')
    args = parser.parse_args()
    if os.name == 'nt':
        raise SystemExit('Run with the existing WSL airflow_env Python')
    home = Path.home()
    executable = home / 'airflow_env/bin/airflow'
    config = home / '.config/retail-airflow/config.json'
    if not executable.is_file() or not config.is_file():
        raise SystemExit('Configure existing Airflow and private path profile first')
    env = service_environment(executable, config)
    logs = home / 'airflow/retail-service-logs'
    if args.status:
        print(json.dumps([service_info(logs/(s+'.pid'),executable,s,config) for s in ('scheduler','webserver')]))
        return
    if args.stop:
        stop_services(home,config,executable,logs)
        return
    subprocess.run([str(executable), 'db', 'check'], env=env, check=True)
    if not args.start:
        return
    ensure_idle(home,config)
    logs.mkdir(exist_ok=True)
    for service in ('scheduler','webserver'):
        pidfile = logs / (service + '.pid')
        state=service_info(pidfile,executable,service,config)
        if state['running']:
            if not state['identity_verified'] or not state['schedule_environment_matches']:
                raise ValueError('Existing PID/config differs; pause/drain/stop and inspect before restart')
            print(service+': verified already running; no duplicate started')
            continue
        with (logs / (service + '.log')).open('ab') as log:
            command = [str(executable), service]
            if service == 'webserver':
                command += ['--hostname','127.0.0.1','--port','8080']
            process = subprocess.Popen(command, env=env, stdout=log, stderr=log,
                                       start_new_session=True)
        pidfile.write_text(str(process.pid))
        print(service + ': started PID ' + str(process.pid))


if __name__ == '__main__':
    main()
