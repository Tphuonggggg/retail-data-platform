import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('retail_worker',ROOT/'airflow/worker.py')
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
V='c825b18e-fc62-4cf1-8837-b37b4c9f9668'


class WorkerTests(unittest.TestCase):
    def test_nonzero_cli_never_parses_success(self):
        from types import SimpleNamespace
        with patch.object(worker.subprocess,'run',return_value=SimpleNamespace(returncode=1,stdout='secret')):
            with self.assertRaises(RuntimeError):worker.cli(['-m','ingestion.incremental','run'],{'PASS'})

    def test_no_data_test_or_failed_test_cannot_complete(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);identifier=str(uuid4())
            receipt={'invocation':identifier,'command':'build','input_kind':'INCREMENTAL','capture_id':V,'exit_code':0}
            p=root/'.local/dbt/invocations'/identifier/'target/run_results.json';p.parent.mkdir(parents=True)
            for results in ([],[{'unique_id':'model.x','status':'success'}],[{'unique_id':'test.x','status':'fail'}],[{'unique_id':'test.x','status':'warn'}]):
                p.write_text(json.dumps({'results':results}))
                with patch.object(worker,'ROOT',root):
                    with self.assertRaises(ValueError):worker.validate_build_receipt(receipt,V)
            p.write_text(json.dumps({'results':[{'unique_id':'test.x','status':'pass'},{'unique_id':'model.x','status':'success'}]}))
            with patch.object(worker,'ROOT',root):worker.validate_build_receipt(receipt,V)
            with self.assertRaises(ValueError):worker.validate_build_receipt(receipt,str(uuid4()))

    def test_writes_disabled_even_when_worker_called_directly(self):
        with self.assertRaises(ValueError):worker.perform({'action':'ingest','parent':V,'version':str(uuid4()),'allow_writes':False})

    def test_version_guard_never_uses_parent_as_fallback(self):
        from unittest.mock import MagicMock
        pg=MagicMock()
        with patch('ingestion.incremental.assert_version',return_value='FULL'):
            with self.assertRaises(ValueError):worker.validate_version(pg,V,str(uuid4()))


if __name__=='__main__':unittest.main()
