"""Manual local DAG; no connections, files or secrets read at import time."""
from datetime import timedelta
from pathlib import Path
import importlib.util

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator


def execute_stage(action, upstream=None, **context):
    # Import the small repository bridge at task execution, never during parsing.
    path = Path(__file__).resolve().parents[1] / 'bridge.py'
    spec = importlib.util.spec_from_file_location('retail_airflow_bridge', path)
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    run = context['dag_run']
    parent = bridge.canonical((run.conf or {})['parent_version'])
    version = bridge.version_for_run(run.run_id)
    if upstream:
        previous = context['ti'].xcom_pull(task_ids=upstream)
        if not previous or previous.get('status') != 'PASS' or previous.get('version') != version or previous.get('parent') != parent:
            raise ValueError('Missing or conflicting upstream handoff')
    return bridge.launch(action, parent, version, execution=action in ('ingest','build'))


with DAG(
    'retail_sales_incremental_pipeline', schedule=None, catchup=False,
    start_date=pendulum.datetime(2026, 1, 1, tz='Asia/Ho_Chi_Minh'),
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
