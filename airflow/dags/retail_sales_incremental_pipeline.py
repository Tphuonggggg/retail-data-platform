"""Manual by default; optional daily timetable, no secrets or connections at parse."""
from datetime import timedelta
from pathlib import Path
import importlib.util
import json
import logging
import os

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowFailException
from airflow.timetables.trigger import CronTriggerTimetable

spec=importlib.util.spec_from_file_location('retail_scheduling',Path(__file__).resolve().parents[1]/'scheduling.py')
scheduling=importlib.util.module_from_spec(spec);spec.loader.exec_module(scheduling)
schedule_config=scheduling.settings(os.environ)


def load_bridge():
    # Import the small repository bridge at task execution, never during parsing.
    path = Path(__file__).resolve().parents[1] / 'bridge.py'
    spec = importlib.util.spec_from_file_location('retail_airflow_bridge', path)
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    return bridge


def execute_stage(action, upstream=None, **context):
    bridge = load_bridge()
    run = context['dag_run']
    info = {'run_id':run.run_id,'task_id':context['ti'].task_id,'attempt':context['ti'].try_number,
            'action':action}
    log = logging.getLogger(__name__)
    try:
        previous = context['ti'].xcom_pull(task_ids=upstream) if upstream else None
        parent = scheduling.parent_for_run(run,context.get('params',{}).get('scheduled_parent_version'),previous)
        version = bridge.version_for_run(run.run_id)
        info.update(parent=parent, version=version)
        if upstream:
            if not previous or previous.get('status') != 'PASS' or previous.get('version') != version or previous.get('parent') != parent:
                raise ValueError('Missing or conflicting upstream handoff')
        log.info('retail_stage_start %s', json.dumps(info))
        result = bridge.launch(action, parent, version, execution=action in ('ingest','build'))
    except Exception as error:
        category = error.category if isinstance(error, bridge.BridgeFailure) else 'HANDOFF_OR_CONFIGURATION_INVALID'
        failed = {**info,'error_category':category}
        if isinstance(error, bridge.BridgeFailure) and error.command_exit_code is not None:
            failed['command_exit_code'] = error.command_exit_code
            if action == 'build':failed.update(dbt_command='build', dbt_exit_code=error.command_exit_code)
        log.error('retail_stage_failed %s', json.dumps(failed))
        if isinstance(error, bridge.BridgeFailure) and error.retriable:
            raise
        # Permanent validation/permission/unknown-commit failures must not consume a retry.
        raise AirflowFailException('Retail stage failed: ' + category) from None
    log.info('retail_stage_success %s', json.dumps({**info,**result}))
    return result


with DAG(
    'retail_sales_incremental_pipeline',
    schedule=None if schedule_config['mode']=='manual' else CronTriggerTimetable(schedule_config['cron'],timezone=scheduling.TIMEZONE),catchup=False,
    start_date=pendulum.datetime(2026,1,1,tz=scheduling.TIMEZONE) if schedule_config['mode']=='manual' else pendulum.instance(schedule_config['not_before']).in_timezone(scheduling.TIMEZONE),
    params={'scheduled_parent_version':schedule_config['parent'] or ''},
    max_active_runs=1, is_paused_upon_creation=True, dagrun_timeout=timedelta(hours=5),
    default_args={'owner':'retail','retries':0,'execution_timeout':timedelta(minutes=65)},
    tags=['retail','manual','snapshot-diff'],
) as dag:
    previous = None
    stages = [('preflight_source','source'),('preflight_target','target'),
              ('run_incremental_ingestion','ingest'),('validate_ingestion_batch','validate'),
              ('resolve_dbt_read_version','resolve'),('run_dbt_build','build'),
              ('validate_sales_marts','marts'),('pipeline_complete','complete')]
    for task_id, action in stages:
        task = PythonOperator(task_id=task_id, python_callable=execute_stage,
                              op_kwargs={'action':action,'upstream':previous.task_id if previous else None},
                              retries=1 if action in ('source','target') else 0,
                              retry_delay=timedelta(seconds=30))
        if previous:
            previous >> task
        previous = task
