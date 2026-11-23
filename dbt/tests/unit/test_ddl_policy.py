"""Sales-only DDL entry guard; no runtime database connections."""
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock,patch
from contextlib import redirect_stdout
import yaml

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'dbt'))
from ddl_policy import MODELS,VIEWS,verify_project,DDLPolicyError
import execute


class DDLPolicyTests(unittest.TestCase):
    def test_existing_closed_project_and_protected_schemas(self):
        verify_project(ROOT/'dbt')
        self.assertEqual(len(MODELS),21);self.assertEqual(len(VIEWS),2)
        self.assertFalse({'raw','ingestion_meta','public','dbt_sales_test'} & {s for s,_ in MODELS})

    def test_unreviewed_model_or_alias_requires_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            shutil.copytree(ROOT/'dbt/models',root/'models')
            shutil.copyfile(ROOT/'dbt/dbt_project.yml',root/'dbt_project.yml')
            added=root/'models/core/unreviewed.sql';added.write_text('select 1')
            with self.assertRaises(DDLPolicyError):verify_project(root)
            added.unlink()
            target=root/'models/core/dim_date.sql';original=target.read_text()
            target.write_text("{{ config(alias='unrelated') }}\n"+original)
            with self.assertRaises(DDLPolicyError):verify_project(root)
            target.write_text(original)
            config=yaml.safe_load((root/'dbt_project.yml').read_text())
            config['models']['retail_sales']['core']['dim_date']['+alias']='unrelated'
            (root/'dbt_project.yml').write_text(yaml.safe_dump(config))
            with self.assertRaises(DDLPolicyError):verify_project(root)

    def test_rejected_scope_never_launches_dbt_and_releases_lock_connection(self):
        guard=MagicMock();guard.execute.return_value.fetchone.side_effect=[('retail_raw','retail_transform'),(True,)]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);private=root/'.local/dbt';private.mkdir(parents=True)
            (private/'connection.json').write_text(json.dumps({'password':'synthetic-secret-marker'}))
            with patch.object(execute,'ROOT',root),patch.object(execute,'load',return_value={}),patch.object(execute,'read_env_file'),patch.object(execute,'load_config',return_value=SimpleNamespace(port=55434,host='127.0.0.1')),patch('psycopg.connect',return_value=guard),patch('ingestion.incremental.assert_version',return_value='INCREMENTAL'),patch.object(execute,'verify_project'),patch.object(execute,'inspect_scope',side_effect=DDLPolicyError('DDL_UNAPPROVED_CASCADE_DEPENDENCY')),patch.object(execute.subprocess,'run') as process,patch.object(sys,'argv',['run_dbt.py','build','--input-kind','INCREMENTAL','--capture-id','3a2f011d-f3b3-5683-83a2-a64837720f3d']),redirect_stdout(io.StringIO()) as output:
                self.assertEqual(execute.main(),1)
                process.assert_not_called();guard.close.assert_called_once()
                self.assertNotIn('synthetic-secret-marker',output.getvalue())
                self.assertEqual(json.loads(output.getvalue())['error'],'DDL_UNAPPROVED_CASCADE_DEPENDENCY')


if __name__=='__main__':unittest.main()
