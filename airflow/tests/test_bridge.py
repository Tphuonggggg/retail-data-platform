import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('retail_bridge',ROOT/'airflow/bridge.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
P='c825b18e-fc62-4cf1-8837-b37b4c9f9668'
V=bridge.version_for_run('manual__test')


class BridgeTests(unittest.TestCase):
    def config(self, path, writes=False):
        cfg={k:str(path) for k in ('windows_python_wsl','worker_path_wsl','repository_wsl')}
        cfg.update(worker_path_windows='D:\\repo\\airflow\\worker.py',allow_pipeline_writes=writes)
        cfg['write_scope']={'parent':P,'version':V,'actions':['ingest','build']} if writes else None
        file=path/'config.json';file.write_text(json.dumps(cfg));return file

    def test_same_run_retries_keep_same_version(self):
        self.assertEqual(V,bridge.version_for_run('manual__test'))
        self.assertNotEqual(V,bridge.version_for_run('manual__new'))

    def test_invalid_parent_cannot_launch(self):
        with patch.object(bridge.subprocess,'run') as run:
            with self.assertRaises(ValueError):bridge.launch('ingest','latest',V,True)
            run.assert_not_called()

    def test_default_gate_prevents_write(self):
        with tempfile.TemporaryDirectory() as t:
            cfg=self.config(Path(t))
            with patch.dict(bridge.os.environ,RETAIL_AIRFLOW_CONFIG=str(cfg)),patch.object(bridge.subprocess,'run') as run:
                with self.assertRaises(ValueError):bridge.launch('ingest',P,V,True)
                run.assert_not_called()

    def test_no_fallback_on_failure_or_invalid_output(self):
        with tempfile.TemporaryDirectory() as t:
            cfg=self.config(Path(t),True)
            with patch.dict(bridge.os.environ,RETAIL_AIRFLOW_CONFIG=str(cfg)):
                for result in [SimpleNamespace(returncode=1,stdout='secret'),SimpleNamespace(returncode=0,stdout='{}'),SimpleNamespace(returncode=0,stdout='not json')]:
                    with patch.object(bridge.subprocess,'run',return_value=result):
                        with self.assertRaises(RuntimeError) as e:bridge.launch('build',P,V,True)
                        self.assertNotIn('secret',str(e.exception))

    def test_direct_argument_list_and_small_xcom(self):
        with tempfile.TemporaryDirectory() as t:
            cfg=self.config(Path(t),True)
            with patch.dict(bridge.os.environ,RETAIL_AIRFLOW_CONFIG=str(cfg)),patch.object(bridge.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps({'status':'PASS','version':V,'parent':P,'action':'build'}))) as run:
                value=bridge.launch('build',P,V,True)
                self.assertEqual(value['version'],V)
                self.assertLess(len(json.dumps(value)),300)
                self.assertIsInstance(run.call_args.args[0],list)
                self.assertNotIn('shell',run.call_args.kwargs)


if __name__=='__main__':unittest.main()
