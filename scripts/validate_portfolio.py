"""Offline dbt parse/docs, documented lineage and YAML checks. No database execution."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import sys
from uuid import uuid4

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'dbt'))
from configuration import load


def main():
    # A fresh invocation avoids stale models from a previous checkout.
    home = ROOT/'.local/portfolio-validation/main'/str(uuid4())
    home.mkdir(parents=True, exist_ok=True)
    for folder in ('models', 'macros', 'tests'):
        shutil.copytree(ROOT/'dbt'/folder, home/folder, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('*.py', '*.pyc', '__pycache__'))
    project = yaml.safe_load((ROOT/'dbt/dbt_project.yml').read_text(encoding='utf-8'))
    project['vars'] = {'sales_contract': load(), 'sales_input_kind': 'FULL', 'sales_work_mem_mb': 4}
    (home/'dbt_project.yml').write_text(yaml.safe_dump(project, allow_unicode=True), encoding='utf-8')
    profile = {'retail_sales': {'target': 'offline', 'outputs': {'offline': {
        'type': 'postgres', 'host': '127.0.0.1', 'port': 1, 'dbname': 'offline_parse',
        'user': 'offline_parse', 'password': 'offline-no-connection', 'schema': 'dw_staging', 'threads': 1}}}}
    (home/'profiles.yml').write_text(yaml.safe_dump(profile), encoding='utf-8')
    env = {k: v for k, v in os.environ.items() if not k.startswith(('DBT_', 'WWI_DBT_', 'PG'))}
    env.update(WWI_DBT_CAPTURE_ID='00000000-0000-4000-8000-000000000001',
               DBT_SEND_ANONYMOUS_USAGE_STATS='false', DBT_PARTIAL_PARSE='false', DBT_USE_COLORS='false')
    for command in [('parse',), ('docs', 'generate', '--empty-catalog', '--no-compile')]:
        result = subprocess.run([sys.executable, '-m', 'dbt.cli.main', *command,
                                 '--project-dir', str(home), '--profiles-dir', str(home)],
                                cwd=ROOT, env=env, capture_output=True, timeout=120)
        (home/('-'.join(command[:2])+'.txt')).write_bytes(result.stdout+result.stderr)
        if result.returncode:
            print('FAIL: offline dbt '+command[0]+'; inspect .local/portfolio-validation/main')
            return 1
    manifest = json.loads((home/'target/manifest.json').read_text(encoding='utf-8'))
    models = {k: n for k, n in manifest['nodes'].items() if n['resource_type'] == 'model'}
    assert len(models) == 21
    assert sum(n['resource_type'] == 'test' for n in manifest['nodes'].values()) == 69
    assert all(n['description'] for n in models.values())
    edges = set()
    for key, node in models.items():
        for parent in node['depends_on']['nodes']:
            if parent in models:
                edges.add((models[parent]['name'], node['name']))
            elif parent in manifest['sources']:
                edges.add(('raw_'+manifest['sources'][parent]['name'], node['name']))
    graph = '```mermaid\nflowchart LR\n' + ''.join(f'    {a} --> {b}\n' for a, b in sorted(edges)) + '```'
    (home/'lineage.txt').write_text(graph, encoding='utf-8')
    readme = (ROOT/'dbt/README.md').read_text(encoding='utf-8')
    assert '<!-- lineage:start -->' in readme and '<!-- lineage:end -->' in readme
    documented = readme.split('<!-- lineage:start -->')[1].split('<!-- lineage:end -->')[0]
    actual = set(re.findall(r'^\s*(\w+) --> (\w+)\s*$', documented, re.M))
    assert actual == edges, 'Documented lineage differs from parsed dbt dependencies'
    (home.parents[1]/'latest.json').write_text(json.dumps({'invocation': str(home.relative_to(ROOT))}), encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'models': len(models), 'model_descriptions': len(models),
                      'lineage_edges': len(edges), 'parse': 'PASS', 'docs_empty_catalog': 'PASS',
                      'live_compile': 'NOT_RUN', 'database_connections': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
