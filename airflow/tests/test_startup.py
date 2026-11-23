import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('retail_start',Path(__file__).resolve().parents[1]/'start_local.py')
startup=importlib.util.module_from_spec(spec);spec.loader.exec_module(startup)


class StartupTests(unittest.TestCase):
    def test_task_subprocesses_inherit_airflow_bin_before_existing_path(self):
        executable=Path('existing-airflow-env')/'bin'/'airflow'
        config=Path('private-profile.json')
        with patch.dict(os.environ,{'PATH':'original-path'}):
            env=startup.service_environment(executable,config)
        self.assertEqual(env['PATH'],str(executable.parent)+os.pathsep+'original-path')
        self.assertEqual(env['RETAIL_AIRFLOW_CONFIG'],str(config))
        self.assertEqual(env['AIRFLOW__CORE__LOAD_EXAMPLES'],'False')


if __name__=='__main__':unittest.main()
