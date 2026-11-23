"""Failure classification, bounded authorization and durable version regressions."""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock,patch
from uuid import UUID

ROOT=Path(__file__).resolve().parents[2]
def module(name):
    spec=importlib.util.spec_from_file_location('retail_'+name,ROOT/'airflow'/f'{name}.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
bridge=module('bridge');worker=module('worker')
P='c825b18e-fc62-4cf1-8837-b37b4c9f9668';V='3a2f011d-f3b3-5683-83a2-a64837720f3d'


class ReliabilityTests(unittest.TestCase):
    def test_boolean_write_gate_alone_is_insufficient(self):
        with self.assertRaises(ValueError):bridge.authorize_write({'allow_pipeline_writes':True},'build',P,V)
        scope={'parent':P,'version':V,'actions':['build']}
        cfg={'allow_pipeline_writes':True,'write_scope':scope}
        self.assertEqual(bridge.authorize_write(cfg,'build',P,V),scope)
        for action,parent,version in [('ingest',P,V),('build',V,V),('build',P,P)]:
            with self.assertRaises(ValueError):bridge.authorize_write(cfg,action,parent,version)

    def test_worker_checks_same_write_scope_even_when_called_directly(self):
        for scope in (None,{'parent':P,'version':V,'actions':['ingest']},{'parent':V,'version':V,'actions':['build']}):
            with patch.object(worker,'target') as target:
                with self.assertRaises(ValueError):worker.perform({'action':'build','parent':P,'version':V,'allow_writes':True,'write_scope':scope})
                target.assert_not_called()

    def test_only_connection_errors_are_retriable_and_secrets_are_redacted(self):
        import psycopg
        import pyodbc
        for error in (psycopg.OperationalError('connection refused secret-marker'),pyodbc.OperationalError('08001','connection refused secret-marker')):
            result=worker.failure_result(error)
            self.assertTrue(result['retriable']);self.assertEqual(result['error_category'],'CONNECTION_UNAVAILABLE')
            self.assertNotIn('secret-marker',json.dumps(result))
        for error in (psycopg.OperationalError('password authentication failed secret-marker'),pyodbc.OperationalError('08001','certificate verify failed secret-marker'),ValueError('secret-marker')):
            result=worker.failure_result(error)
            self.assertFalse(result['retriable']);self.assertNotIn('secret-marker',json.dumps(result))

    def test_unknown_commit_is_a_sanitized_manual_recovery_error(self):
        from ingestion.common.errors import PipelineError
        e=PipelineError('INCREMENTAL_COMMIT_OUTCOME_UNKNOWN_INSPECT_VERSION')
        result=worker.failure_result(e)
        self.assertEqual(result['error_category'],e.code);self.assertFalse(result['retriable'])
        with patch.object(worker.subprocess,'run',return_value=SimpleNamespace(returncode=1,stdout=json.dumps({'error':e.code})+'\nsecret-marker')):
            with self.assertRaises(worker.CommandFailure) as caught:worker.cli(['-m','ingestion.incremental','run'])
            self.assertEqual(caught.exception.code,e.code)
            self.assertNotIn('secret-marker',str(caught.exception))
        timeout=worker.subprocess.TimeoutExpired(['secret-marker'],10)
        result=worker.failure_result(timeout)
        self.assertEqual(result['error_category'],'CLI_TIMEOUT_INSPECT_CHILD_AND_VERSION')
        self.assertFalse(result['retriable']);self.assertNotIn('secret-marker',json.dumps(result))

    def test_invalid_versions_never_reach_dbt_cli(self):
        from ingestion.common.errors import PipelineError
        request={'action':'build','parent':P,'version':V,'allow_writes':True,'write_scope':{'parent':P,'version':V,'actions':['build']}}
        for label in ('UNKNOWN_VERSION','UNVALIDATED_VERSION','FAILED_CAPTURE','MISSING_METADATA'):
            pg=MagicMock()
            with patch.object(worker,'target',return_value=pg),patch('ingestion.incremental.assert_version',side_effect=PipelineError(label)),patch.object(worker,'cli') as cli:
                with self.assertRaises(PipelineError):worker.perform(request)
                cli.assert_not_called();pg.close.assert_called_once()
        for row in (None,(UUID(P),'FAILED','hash','algorithm',None),(UUID(V),'VALIDATED','hash','algorithm',None)):
            pg=MagicMock();pg.connection.execute.return_value.fetchone.return_value=row
            with patch.object(worker,'target',return_value=pg),patch('ingestion.incremental.assert_version',return_value='INCREMENTAL'),patch.object(worker,'cli') as cli:
                with self.assertRaises(ValueError):worker.perform(request)
                cli.assert_not_called()

    def test_cli_dbt_version_mismatch_never_returns_success(self):
        request={'action':'build','parent':P,'version':V,'allow_writes':True,'write_scope':{'parent':P,'version':V,'actions':['build']}}
        with patch.object(worker,'target'),patch.object(worker,'validate_version'),patch.object(worker,'cli',return_value={'command':'build','capture_id':P,'input_kind':'INCREMENTAL','exit_code':0}):
            with self.assertRaises(ValueError):worker.perform(request)

    def test_bridge_does_not_retry_a_write_even_if_worker_marks_transient(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);cfg={k:str(p) for k in ('windows_python_wsl','worker_path_wsl','repository_wsl')}
            cfg.update(worker_path_windows='worker.py',allow_pipeline_writes=True,write_scope={'parent':P,'version':V,'actions':['build']})
            f=p/'config.json';f.write_text(json.dumps(cfg))
            response=SimpleNamespace(returncode=1,stdout=json.dumps({'status':'FAIL','error_category':'CONNECTION_UNAVAILABLE','retriable':True,'command_exit_code':2}))
            with patch.dict(bridge.os.environ,RETAIL_AIRFLOW_CONFIG=str(f)),patch.object(bridge.subprocess,'run',return_value=response):
                for action in ('source','target','build'):
                    with self.assertRaises(bridge.BridgeFailure) as caught:bridge.launch(action,P,V,execution=action=='build')
                    self.assertEqual(caught.exception.retriable,action!='build')
                    self.assertEqual(caught.exception.command_exit_code,2)


if __name__=='__main__':unittest.main()
