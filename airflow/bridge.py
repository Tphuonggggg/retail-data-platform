"""WSL task bridge. Configuration contains paths, never database credentials."""
from pathlib import Path
import json
import os
import subprocess
import re
from uuid import UUID, uuid5, NAMESPACE_URL


class BridgeFailure(RuntimeError):
    def __init__(self, action, category, retriable=False, command_exit_code=None):
        self.category = category
        self.retriable = retriable
        self.command_exit_code = command_exit_code if type(command_exit_code) is int else None
        super().__init__('Bridge action failed: ' + action + ' (' + category + ')')


def authorize_write(config, action, parent, version):
    scope = config.get('write_scope')
    if config.get('allow_pipeline_writes') is not True or not isinstance(scope, dict):
        raise ValueError('A bounded pipeline write scope is required')
    actions = scope.get('actions')
    if (scope.get('parent') != parent or scope.get('version') != version
            or not isinstance(actions, list) or not actions
            or len(set(actions)) != len(actions) or not set(actions) <= {'ingest', 'build'}
            or action not in actions):
        raise ValueError('Pipeline action is outside the authorized write scope')
    return scope


def canonical(value):
    result = str(UUID(value))
    if value != result:
        raise ValueError('Canonical UUID required')
    return result


def version_for_run(run_id):
    if not isinstance(run_id, str) or not run_id or len(run_id) > 512:
        raise ValueError('Invalid Airflow run identity')
    return str(uuid5(NAMESPACE_URL, 'retail_sales_incremental_pipeline/' + run_id))


def launch(action, parent, version, execution=False):
    canonical(parent)
    canonical(version)
    config = json.loads(Path(os.environ['RETAIL_AIRFLOW_CONFIG']).read_text())
    required = ('windows_python_wsl', 'worker_path_wsl', 'repository_wsl')
    if not all(Path(config[k]).exists() for k in required):
        raise ValueError('Bridge paths unavailable')
    if execution != (action in ('ingest', 'build')):
        raise ValueError('Execution flag does not match action semantics')
    scope = authorize_write(config, action, parent, version) if execution else None
    request = {'action': action, 'parent': parent, 'version': version,
               'allow_writes': execution, 'write_scope': scope}
    # WSL interop invokes python.exe directly; no PowerShell or shell interpolation.
    command = [config['windows_python_wsl'], '-X', 'utf8',
               config['worker_path_windows']]
    try:
        result = subprocess.run(command, input=json.dumps(request), text=True,
                                capture_output=True, cwd=config['repository_wsl'],
                                timeout=3600, check=False)
    except subprocess.TimeoutExpired:
        raise BridgeFailure(action, 'BRIDGE_TIMEOUT_INSPECT_CHILD_AND_VERSION') from None
    if result.returncode:
        try:
            failure = json.loads(result.stdout)
            if not isinstance(failure, dict):failure = {}
            category = failure.get('error_category', 'UNKNOWN_WORKER_FAILURE')
        except ValueError:
            failure = {}
            category = 'UNKNOWN_WORKER_FAILURE'
        if not isinstance(category, str) or not re.fullmatch(r'[A-Z][A-Z0-9_]{0,79}', category):
            category = 'UNKNOWN_WORKER_FAILURE'
        retriable = (action in ('source', 'target') and category == 'CONNECTION_UNAVAILABLE'
                     and failure.get('retriable') is True)
        raise BridgeFailure(action, category, retriable, failure.get('command_exit_code'))
    try:
        output = json.loads(result.stdout)
    except ValueError:
        raise RuntimeError('Bridge did not return one structured result') from None
    if (output.get('status'), output.get('version'), output.get('parent'), output.get('action')) != ('PASS',version,parent,action):
        raise RuntimeError('Bridge result contract mismatch')
    handoff = {'status': 'PASS', 'version': version, 'parent': parent, 'action': action}
    # Only enumerated, validated receipt fields may reach native logs or XCom.
    if action == 'build' and 'dbt_invocation' in output:
        handoff.update(dbt_invocation=canonical(output['dbt_invocation']), dbt_command='build', dbt_exit_code=0)
    if action == 'ingest' and output.get('ingestion_status') in ('VALIDATED_UNPUBLISHED_CANDIDATE','ALREADY_VALIDATED_NO_REEXTRACTION'):
        handoff['ingestion_status'] = output['ingestion_status']
    return handoff
