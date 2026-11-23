"""Windows worker: existing CLI integration and SELECT-only durable gates."""
from pathlib import Path
import json
import re
import subprocess
import sys
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class CommandFailure(RuntimeError):
    def __init__(self, code, exit_code):
        self.code = code
        self.exit_code = exit_code
        super().__init__(code)


class ContractFailure(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def failure_result(error):
    code = getattr(error, 'code', None)
    if not isinstance(code, str) or not re.fullmatch(r'[A-Z][A-Z0-9_]{0,79}', code):
        code = 'WORKER_CONTRACT_OR_EXECUTION_FAILURE'
    if isinstance(error, subprocess.TimeoutExpired):code = 'CLI_TIMEOUT_INSPECT_CHILD_AND_VERSION'
    state = getattr(error, 'sqlstate', None)
    if state is None and error.args and isinstance(error.args[0], str):
        state = error.args[0] if re.fullmatch(r'[A-Z0-9]{5}', error.args[0]) else None
    transient = isinstance(state, str) and (state.startswith('08') or state in ('HYT00', 'HYT01'))
    # Inspect messages only for classification, never relay them to logs/XCom.
    message = str(error)
    if type(error).__module__.startswith('psycopg') and state is None:
        transient = (type(error).__name__ == 'ConnectionTimeout' or bool(re.search(
            r'connection refused|timeout expired|connection timed out|network is unreachable|no route to host', message, re.I)))
    if re.search(r'certificate|authentication failed|login failed|permission denied', message, re.I):
        transient = False
    result = {'status':'FAIL','error_type':type(error).__name__,
              'error_category':'CONNECTION_UNAVAILABLE' if transient else code,'retriable':transient}
    if isinstance(error, CommandFailure):result['command_exit_code'] = error.exit_code
    return result


def require_write(request):
    scope = request.get('write_scope')
    if (request.get('allow_writes') is not True or not isinstance(scope, dict)
            or scope.get('version') != request['version'] or scope.get('parent') != request['parent']
            or not isinstance(scope.get('actions'), list) or not scope['actions']
            or any(a not in ('ingest','build') for a in scope['actions'])
            or request['action'] not in scope['actions']):
        raise ValueError('Bounded write authorization required')


def cli(arguments, accepted=None):
    result = subprocess.run([sys.executable, '-X', 'utf8', *arguments], cwd=ROOT,
                            capture_output=True, text=True, timeout=3300)
    # Never relay arbitrary driver output into Airflow logs.
    if result.returncode:
        code = 'CLI_COMMAND_FAILED'
        for line in result.stdout.splitlines():
            if not line.startswith('{'):continue
            try:
                parsed = json.loads(line)
                candidate = parsed.get('error_code', parsed.get('error', ''))
            except (ValueError, AttributeError):continue
            if isinstance(candidate, str) and re.fullmatch(r'[A-Z][A-Z0-9_]{0,79}', candidate):code = candidate
        raise CommandFailure(code, result.returncode)
    if accepted:
        rows = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
        if len(rows) != 1 or rows[0].get('status') not in accepted:
            raise RuntimeError('CLI outcome is not an accepted durable outcome')
        return rows[0]
    rows = []
    for line in result.stdout.splitlines():
        if line.startswith('{'):
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    if not rows:
        raise RuntimeError('No dbt execution receipt')
    return rows[-1]


def validate_build_receipt(receipt, version):
    if (receipt.get('command'), receipt.get('capture_id'), receipt.get('input_kind'), receipt.get('exit_code')) != ('build',version,'INCREMENTAL',0):
        raise ContractFailure('DBT_RECEIPT_VERSION_MISMATCH')
    invocation = str(UUID(receipt['invocation']))
    path = ROOT / '.local/dbt/invocations' / invocation / 'target/run_results.json'
    results = json.loads(path.read_text())['results']
    if not results or not any(r['unique_id'].startswith('test.') for r in results):
        raise ContractFailure('DBT_DATA_TESTS_MISSING')
    if any(r['status'] not in ('success','pass') for r in results):
        raise ContractFailure('DBT_BUILD_NOT_SUCCESSFUL')


def target():
    from ingestion.common.config import settings
    from ingestion.loaders.postgres import PostgresTarget
    from ingestion.incremental import IncrementalTarget
    pg = PostgresTarget(settings(ROOT / '.env', 500))
    pg.connect()
    try:
        pg.connection.execute('SET default_transaction_read_only=on')
        IncrementalTarget(pg).preflight()
    except Exception:
        pg.close()
        raise
    return pg


def validate_version(pg, version, parent):
    from ingestion.incremental import assert_version, ALGORITHM
    from ingestion.common.contracts import contract_hash
    try:
        kind = assert_version(pg.connection, UUID(version))
    except Exception as error:
        if getattr(error, 'sqlstate', None) == 'P0001':
            raise ContractFailure('READ_VERSION_NOT_ELIGIBLE') from None
        raise
    if kind != 'INCREMENTAL':
        raise ContractFailure('READ_VERSION_NOT_INCREMENTAL')
    row = pg.connection.execute('SELECT parent_id,status,contract_hash,algorithm,acknowledged_publication_id '
                                'FROM ingestion_meta.incremental_versions WHERE version_id=%s',
                                (UUID(version),)).fetchone()
    if row is None or tuple(row) != (UUID(parent), 'VALIDATED', contract_hash(), ALGORITHM, None):
        raise ContractFailure('READ_VERSION_HANDOFF_MISMATCH')


def marts(version):
    import psycopg
    from psycopg import sql
    from infrastructure.scripts.check_raw_connection import load_config, read_env_file
    cfg = load_config(read_env_file(ROOT / '.env'))
    password = json.loads((ROOT / '.local/dbt/connection.json').read_text())['password']
    names = ('mart_sales_daily', 'mart_sales_monthly', 'mart_sales_product_daily',
             'mart_customer_sales', 'mart_sales_customer_summary')
    with psycopg.connect(host=cfg.host, port=cfg.port, dbname=cfg.database,
                         user='retail_transform', password=password, connect_timeout=5,
                         options='-c default_transaction_read_only=on') as db:
        if db.execute('SELECT current_database(),current_user').fetchone() != ('retail_raw','retail_transform'):
            raise ValueError('Transform target mismatch')
        for name in names:
            count, pins = db.execute(sql.SQL('SELECT count(*),array_agg(DISTINCT _capture_id::text) FROM {}.{}')
                                     .format(sql.Identifier('sales_marts'), sql.Identifier(name))).fetchone()
            if count == 0 or pins != [version]:
                raise ContractFailure('MART_VERSION_OR_POPULATION_MISMATCH')
        actual = db.execute('SELECT sum(sales_amount),sum(invoice_count) FROM sales_marts.mart_sales_daily').fetchone()
        expected = db.execute('SELECT sum(invoiced_sales_before_tax),count(DISTINCT source_invoice_id) '
                              'FROM dw_core.fact_invoice_line WHERE is_sales_eligible AND _capture_id=%s',
                              (version,)).fetchone()
        if actual != expected:
            raise ContractFailure('MART_RECONCILIATION_FAILED')


def perform(request):
    from ingestion.incremental import objects, assert_version
    action, parent, version = (request[k] for k in ('action','parent','version'))
    UUID(parent); UUID(version)
    receipt_fields = {}
    if action == 'source':
        from ingestion.common.config import settings
        from ingestion.extractors.sqlserver import SqlServerSource
        source = SqlServerSource(settings(ROOT / '.env', 500))
        try:
            source.connect(); source.preflight(objects())
        finally:
            source.close()
    elif action == 'ingest':
        require_write(request)
        row = cli(['-m','ingestion.incremental','run','--parent-id',parent,'--version-id',version,'--execute'],
                  {'VALIDATED_UNPUBLISHED_CANDIDATE','ALREADY_VALIDATED_NO_REEXTRACTION'})
        if row.get('version_id') != version:
            raise ValueError('CLI returned wrong version')
        receipt_fields['ingestion_status'] = row['status']
    elif action == 'build':
        require_write(request)
        pg = target()
        try:
            validate_version(pg, version, parent)
        finally:
            pg.close()
        receipt = cli(['dbt/run_dbt.py','build','--input-kind','INCREMENTAL','--capture-id',version])
        validate_build_receipt(receipt, version)
        receipt_fields.update(dbt_invocation=str(UUID(receipt['invocation'])), dbt_command='build', dbt_exit_code=0)
    elif action in ('target','validate','resolve','marts','complete'):
        pg = target()
        try:
            if action == 'target':
                assert_version(pg.connection, UUID(parent))
            else:
                validate_version(pg, version, parent)
        finally:
            pg.close()
        if action == 'validate':
            cli(['-m','ingestion.incremental','reconcile','--version-id',version], {'PASS'})
        if action in ('marts','complete'):
            marts(version)
    else:
        raise ValueError('Unknown action')
    return {'status':'PASS','version':version,'parent':parent,'action':action,**receipt_fields}


if __name__ == '__main__':
    try:
        print(json.dumps(perform(json.load(sys.stdin))))
    except Exception as error:
        print(json.dumps(failure_result(error)))
        raise SystemExit(1)
