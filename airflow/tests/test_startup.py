import importlib.util
import os
from pathlib import Path
import unittest
import json
import sqlite3
import tempfile
from contextlib import closing
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('retail_start',Path(__file__).resolve().parents[1]/'start_local.py')
startup=importlib.util.module_from_spec(spec);spec.loader.exec_module(startup)


class StartupTests(unittest.TestCase):
    def test_idle_guard_requires_closed_gate_paused_dag_and_no_active_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);(home/'airflow').mkdir();config=home/'config.json'
            config.write_text(json.dumps({'allow_pipeline_writes':False,'write_scope':None}))
            with closing(sqlite3.connect(home/'airflow/airflow.db',isolation_level=None)) as db:
                db.execute('CREATE TABLE dag_run(state text)');db.execute('CREATE TABLE dag(dag_id text,is_paused integer)')
                db.execute("INSERT INTO dag VALUES('retail_sales_incremental_pipeline',1)")
            startup.ensure_idle(home,config)
            config.write_text(json.dumps({'allow_pipeline_writes':True}))
            with self.assertRaises(ValueError):startup.ensure_idle(home,config)
            config.write_text(json.dumps({'allow_pipeline_writes':False}))
            with closing(sqlite3.connect(home/'airflow/airflow.db',isolation_level=None)) as db:db.execute("INSERT INTO dag_run VALUES('running')")
            with self.assertRaises(ValueError):startup.ensure_idle(home,config)
            with closing(sqlite3.connect(home/'airflow/airflow.db',isolation_level=None)) as db:
                db.execute('DELETE FROM dag_run');db.execute('UPDATE dag SET is_paused=0')
            with self.assertRaises(ValueError):startup.ensure_idle(home,config)
    def test_unrelated_or_reused_pid_command_is_not_trusted(self):
        executable=Path('/owned/airflow_env/bin/airflow')
        self.assertTrue(startup.matches_command(str(executable)+'\0scheduler\0',executable,'scheduler'))
        self.assertFalse(startup.matches_command('/usr/bin/python\0unrelated.py',executable,'scheduler'))
        self.assertFalse(startup.matches_command(str(executable)+' webserver',executable,'scheduler'))
        self.assertFalse(startup.matches_command('python unrelated.py --note '+str(executable)+' scheduler',executable,'scheduler'))

    def test_stop_never_signals_an_unverified_pid(self):
        with patch.object(startup,'ensure_idle'),patch.object(startup,'service_info',return_value={'running':True,'identity_verified':False}),patch.object(startup.os,'kill') as kill:
            with self.assertRaises(ValueError):startup.stop_services(Path('home'),Path('config'),Path('airflow'),Path('logs'))
            kill.assert_not_called()
    def test_task_subprocesses_inherit_airflow_bin_before_existing_path(self):
        executable=Path('existing-airflow-env')/'bin'/'airflow'
        config=Path('private-profile.json')
        with patch.dict(os.environ,{'PATH':'original-path'}):
            env=startup.service_environment(executable,config)
        self.assertEqual(env['PATH'],str(executable.parent)+os.pathsep+'original-path')
        self.assertEqual(env['RETAIL_AIRFLOW_CONFIG'],str(config))
        self.assertEqual(env['AIRFLOW__CORE__LOAD_EXAMPLES'],'False')


if __name__=='__main__':unittest.main()
