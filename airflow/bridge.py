"""WSL task bridge. Configuration contains paths, never database credentials."""
from pathlib import Path
import json
import os
import subprocess
from uuid import UUID, uuid5, NAMESPACE_URL


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
    if execution and config.get('allow_pipeline_writes') is not True:
        raise ValueError('Pipeline write gate is disabled')
    request = {'action': action, 'parent': parent, 'version': version,
               'allow_writes': execution and config.get('allow_pipeline_writes') is True}
    # WSL interop invokes python.exe directly; no PowerShell or shell interpolation.
    command = [config['windows_python_wsl'], '-X', 'utf8',
               config['worker_path_windows']]
    try:
        result = subprocess.run(command, input=json.dumps(request), text=True,
                                capture_output=True, cwd=config['repository_wsl'],
                                timeout=3600, check=False)
    except subprocess.TimeoutExpired:
        raise RuntimeError('Bridge timed out; inspect durable version before rerun') from None
    if result.returncode:
        try:
            failure = json.loads(result.stdout)
            category = failure.get('error_type', 'UnknownFailure')
        except ValueError:
            category = 'UnknownFailure'
        if not isinstance(category, str) or not category.isidentifier():
            category = 'UnknownFailure'
        raise RuntimeError('Bridge action failed: ' + action + ' (' + category + ')')
    try:
        output = json.loads(result.stdout)
    except ValueError:
        raise RuntimeError('Bridge did not return one structured result') from None
    if (output.get('status'), output.get('version'), output.get('parent'), output.get('action')) != ('PASS',version,parent,action):
        raise RuntimeError('Bridge result contract mismatch')
    return {'status': 'PASS', 'version': version, 'parent': parent, 'action': action}
