"""B9 precision PoC: read-only SQL source, optional isolated PostgreSQL test sink."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import re
import sys
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any

import pyodbc
import psycopg


# Verbatim expression from evidence section 5.1; do not replace with client formatting.
F2_SQL = """CASE WHEN v.source_value IS NULL THEN CAST(NULL AS varchar(27))
            ELSE CONVERT(char(19), v.source_value, 126) + '.' +
                 RIGHT('0000000' + CONVERT(varchar(7),
                       DATEPART(NANOSECOND, v.source_value) / 100), 7)
       END"""

FIXTURES: tuple[tuple[str, str | None], ...] = (
    ('V1', '2026-11-15T12:34:56.1234567'),
    ('V2', '2026-11-15T12:34:56.1234568'),
    ('ZERO', '2026-11-15T12:34:56.0000000'),
    ('ONE_TICK', '2026-11-15T12:34:56.0000001'),
    ('TAIL_NINE', '2026-11-15T12:34:56.0000009'),
    ('FRACTION_MAX', '2026-11-15T12:34:56.9999999'),
    ('NEXT_SECOND', '2026-11-15T12:34:57.0000000'),
    ('MIN', '0001-01-01T00:00:00.0000000'),
    ('MIN_PLUS_TICK', '0001-01-01T00:00:00.0000001'),
    ('MAX_MINUS_TICK', '9999-12-31T23:59:59.9999998'),
    ('SENTINEL', '9999-12-31T23:59:59.9999999'),
    ('TRAILING_ZERO', '2026-11-15T12:34:56.1234560'),
    ('LEAP_DAY', '2000-02-29T00:00:00.0000000'),
    ('NULL_VALUE', None),
)

FORMAT = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}')


class PrecisionError(ValueError):
    """Stop immediately when an exactness invariant fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PrecisionError(message)


def validate_value(value: object, expected: str | None, label: str) -> None:
    """Validate transport without parsing/coercing the authoritative text."""
    if expected is None:
        require(value is None, f'{label}: SQL NULL was not Python None')
        return
    require(type(value) is str, f'{label}: driver did not return str')
    require(value == expected, f'{label}: exact value mismatch')
    require(len(value) == 27 and FORMAT.fullmatch(value) is not None,
            f'{label}: noncanonical representation')
    require(value.isascii() and value.encode('ascii') == expected.encode('ascii'),
            f'{label}: byte mismatch')


def fixture_cte() -> tuple[str, list[str | None]]:
    rows = ','.join('(CAST(? AS varchar(32)),CAST(? AS varchar(27)))' for _ in FIXTURES)
    sql = f"""WITH inputs AS (
 SELECT * FROM (VALUES {rows}) x(fixture_id,expected_text)
), source_values AS (
 SELECT fixture_id,expected_text,CONVERT(datetime2(7),expected_text,126) AS source_value
 FROM inputs
), formatted AS (
 SELECT v.*, {F2_SQL} AS exact_text FROM source_values v
)
"""
    return sql, [value for fixture in FIXTURES for value in fixture]


def fetch(cursor: Any, sql: str, parameters: list[str | None] | None = None) -> list[dict[str, Any]]:
    if parameters is None:
        cursor.execute(sql)
    else:
        cursor.execute(sql, parameters)
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def sample_sql() -> str:
    # TOP selectors intentionally preserve multiplicity; no customer identifiers/payload exported.
    return f"""WITH samples AS (
 SELECT 'Customers/current' AS origin,ValidFrom,ValidTo FROM
 (SELECT TOP (2) CustomerID,ValidFrom,ValidTo FROM Sales.Customers ORDER BY CustomerID) a
 UNION ALL SELECT 'Customers/history',ValidFrom,ValidTo FROM
 (SELECT TOP (2) CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive
  ORDER BY CustomerID,ValidFrom,ValidTo) b
 UNION ALL SELECT 'StockItems/current',ValidFrom,ValidTo FROM
 (SELECT TOP (2) StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems ORDER BY StockItemID) c
 UNION ALL SELECT 'StockItems/history',ValidFrom,ValidTo FROM
 (SELECT TOP (2) StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems_Archive
  ORDER BY StockItemID,ValidFrom,ValidTo) d
 UNION ALL SELECT 'Customers/history/zero-duration',ValidFrom,ValidTo FROM
 (SELECT TOP (1) CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive
  WHERE ValidFrom=ValidTo ORDER BY CustomerID,ValidFrom,ValidTo) e
), formatted AS (
 SELECT origin,p.column_name,v.source_value,{F2_SQL} AS exact_text
 FROM samples CROSS APPLY (VALUES ('ValidFrom',ValidFrom),('ValidTo',ValidTo)) p(column_name,dt)
 CROSS APPLY (VALUES (p.dt)) v(source_value)
)
SELECT origin,column_name,exact_text,LEN(exact_text) AS source_length,
 DATEPART(NANOSECOND,source_value) AS source_nanosecond,
 CASE WHEN TRY_CONVERT(datetime2(7),exact_text,126)=source_value THEN 1 ELSE 0 END AS reverse_equal,
 CONVERT(char(19),source_value,126) AS expected_prefix
FROM formatted ORDER BY origin,column_name,exact_text;"""


def verify_ordering(rows: list[dict[str, Any]], values: dict[str, str | None]) -> None:
    expected_pairs = {(a, b) for a, x in values.items() for b, y in values.items()
                      if x is not None and y is not None}
    actual_pairs = [(r['left_id'], r['right_id']) for r in rows]
    require(len(actual_pairs) == len(expected_pairs) and set(actual_pairs) == expected_pairs,
            'ordering: missing or duplicate pair')
    for row in rows:
        left, right = values[row['left_id']], values[row['right_id']]
        require(left is not None and right is not None, 'ordering: unexpected NULL')
        python_cmp = (left > right) - (left < right)
        require(python_cmp == row['source_cmp'] == row['text_cmp'],
                f"ordering: mismatch {row['left_id']}/{row['right_id']}")


def run_source(server: str, report: dict[str, Any]) -> None:
    require(re.fullmatch(r'tcp:[A-Za-z0-9_.-]+,[0-9]{1,5}', server) is not None,
            'Use an explicit approved TCP host,port endpoint')
    connection_string = (
        'DRIVER={ODBC Driver 18 for SQL Server};'
        f'SERVER={server};DATABASE=WideWorldImporters;'
        'Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=no;'
    )
    report['queries'] = {}
    # ODBC read-only access mode is a client request, not a least-privilege identity proof.
    with closing(pyodbc.connect(connection_string, autocommit=True, timeout=5,
                                attrs_before={pyodbc.SQL_ATTR_ACCESS_MODE: 1})) as connection:
        connection.timeout = 20
        report['driver'] = {
            'pyodbc': pyodbc.version,
            'odbc_driver_name': connection.getinfo(pyodbc.SQL_DRIVER_NAME),
            'odbc_driver_version': connection.getinfo(pyodbc.SQL_DRIVER_VER),
            'dbms_version': connection.getinfo(pyodbc.SQL_DBMS_VER),
        }
        with closing(connection.cursor()) as cursor:
            identity_sql = """SELECT @@SERVERNAME AS server_name,DB_NAME() AS database_name,
 IS_SRVROLEMEMBER('sysadmin') AS interactive_is_sysadmin,
 CAST(c.encrypt_option AS varchar(10)) AS encrypt_option,c.net_transport,c.auth_scheme,
 CONVERT(varchar(33),SYSUTCDATETIME(),126) AS observed_at_utc,
 d.snapshot_isolation_state_desc,d.is_read_committed_snapshot_on,d.is_read_only
 FROM sys.dm_exec_connections c CROSS JOIN sys.databases d
 WHERE c.session_id=@@SPID AND d.database_id=DB_ID();"""
            report['queries']['identity'] = identity_sql
            report['connection'] = fetch(cursor, identity_sql)[0]
            require(report['connection']['encrypt_option'] == 'TRUE', 'Encryption not verified')
            require(report['connection']['net_transport'] == 'TCP', 'TCP transport not verified')
            report['connection']['status'] = 'PASS'

            cte, params = fixture_cte()
            fixture_sql = cte + """SELECT fixture_id,exact_text,LEN(exact_text) AS source_length,
 DATEPART(NANOSECOND,source_value) AS source_nanosecond,
 CASE WHEN TRY_CONVERT(datetime2(7),exact_text,126)=source_value
 OR (source_value IS NULL AND exact_text IS NULL) THEN 1 ELSE 0 END AS reverse_equal
 FROM formatted ORDER BY fixture_id;"""
            report['queries']['fixtures'] = fixture_sql
            report['fixtures'] = fetch(cursor, fixture_sql, params)
            report['fixture_parameters'] = list(FIXTURES)
            expected = dict(FIXTURES)
            require(len(report['fixtures']) == len(expected)
                    and {r['fixture_id'] for r in report['fixtures']} == set(expected),
                    'Fixture population mismatch')
            values: dict[str, str | None] = {}
            for row in report['fixtures']:
                name = row['fixture_id']
                validate_value(row['exact_text'], expected[name], name)
                require(row['reverse_equal'] == 1, f'{name}: SQL typed round-trip mismatch')
                require(row['source_length'] == (27 if expected[name] is not None else None),
                        f'{name}: source length mismatch')
                ns = int(expected[name][-7:]) * 100 if expected[name] is not None else None
                require(row['source_nanosecond'] == ns, f'{name}: fractional component mismatch')
                row['python_type'] = type(row['exact_text']).__name__
                row['status'] = 'PASS'
                values[name] = row['exact_text']

            order_sql = cte + """SELECT a.fixture_id AS left_id,b.fixture_id AS right_id,
 CASE WHEN a.source_value<b.source_value THEN -1
 WHEN a.source_value>b.source_value THEN 1 ELSE 0 END AS source_cmp,
 CASE WHEN a.exact_text COLLATE Latin1_General_100_BIN2 < b.exact_text COLLATE Latin1_General_100_BIN2 THEN -1
 WHEN a.exact_text COLLATE Latin1_General_100_BIN2 > b.exact_text COLLATE Latin1_General_100_BIN2 THEN 1 ELSE 0 END AS text_cmp
 FROM formatted a CROSS JOIN formatted b
 WHERE a.source_value IS NOT NULL AND b.source_value IS NOT NULL;"""
            report['queries']['ordering'] = order_sql
            report['ordering'] = fetch(cursor, order_sql, params)
            verify_ordering(report['ordering'], values)

            report['queries']['temporal_samples'] = sample_sql()
            report['temporal_samples'] = fetch(cursor, sample_sql())
            require(bool(report['temporal_samples']), 'No actual temporal samples returned')
            for row in report['temporal_samples']:
                expected_text = row['expected_prefix'] + '.' + str(row['source_nanosecond'] // 100).zfill(7)
                validate_value(row['exact_text'], expected_text, row['origin'])
                require(row['reverse_equal'] == 1 and row['source_length'] == 27,
                        'Actual temporal SQL reverse equality/length failed')
                row['python_type'] = type(row['exact_text']).__name__
                row['status'] = 'PASS'
    report['sql_to_python_status'] = 'PASS'


def validate_pg_config(config: dict[str, Any]) -> None:
    """Reject targets outside the explicitly named local B9 sandbox."""
    require(config.get('sandbox') == 'retail-b9-pg-poc', 'Unrecognized sandbox marker')
    require(config.get('host') == '127.0.0.1', 'Only localhost B9 sandbox is allowed')
    require(config.get('dbname') == 'b9_precision_poc', 'Not the B9 test database')
    require(config.get('user') == 'b9_poc', 'Not the dedicated B9 test account')
    require(type(config.get('port')) is int and 1024 <= config['port'] <= 65535,
            'Invalid sandbox port')
    require(type(config.get('password')) is str and len(config['password']) >= 24,
            'Missing local sandbox credential')


def validate_readback(rows: list[dict[str, Any]], expected: dict[str, str | None]) -> None:
    require(len(rows) == len(expected) and {r['fixture_id'] for r in rows} == set(expected),
            'Persisted fixture population mismatch')
    for row in rows:
        name = row['fixture_id']
        validate_value(row['canonical_temporal_text'], expected[name], name)
        validate_value(row['expected_temporal_text'], expected[name], name + '/control')


def run_target(config_path: Path, report: dict[str, Any]) -> None:
    require(report.get('sql_to_python_status') == 'PASS', 'Source proof required before target')
    target: dict[str, Any] = {'status': 'IN_PROGRESS', 'phase': 'configuration', 'queries': {}}
    report['postgresql'] = target
    report['postgresql_parameters'] = {'status': 'NOT RUN'}
    report['postgresql_persistence'] = {'status': 'NOT RUN'}
    require(config_path.resolve().is_relative_to(Path(sys.prefix).resolve()),
            'Target credentials must be inside the ignored local venv')
    config = json.loads(config_path.read_text(encoding='utf-8'))
    validate_pg_config(config)
    connection_args = {k: config[k] for k in ('host', 'port', 'dbname', 'user', 'password')}
    connection_args.update(connect_timeout=5, application_name='retail-b9-precision-poc',
                           options='-c statement_timeout=20000')
    expected = {r['fixture_id']: r['exact_text'] for r in report['fixtures']}
    batch_id = str(uuid.uuid4())
    target.update(batch_id=batch_id, table='public.b9_temporal_text_poc')
    target['driver'] = {'psycopg': psycopg.__version__, 'pq_impl': psycopg.pq.__impl__,
                        'libpq_version': psycopg.pq.version()}
    metadata_sql = """SELECT version() AS version,current_setting('server_version') AS server_version,
 current_database() AS database_name,current_user AS database_user,pg_backend_pid() AS backend_pid,
 current_setting('server_encoding') AS server_encoding,datcollate AS lc_collate,
 datctype AS lc_ctype,datlocprovider AS locale_provider,datlocale AS locale_name
 FROM pg_database WHERE datname=current_database();"""
    target['queries']['metadata'] = metadata_sql
    with closing(psycopg.connect(**connection_args)) as writer:
        with writer.cursor() as cursor:
            target['environment'] = fetch(cursor, metadata_sql)[0]
            require(target['environment']['database_name'] == 'b9_precision_poc', 'Database mismatch')
            require(target['environment']['database_user'] == 'b9_poc', 'Database account mismatch')
            binding_sql = """SELECT %s::text AS actual,pg_typeof(%s::text)::text AS pg_type,
 char_length(%s::text) AS char_length,octet_length(%s::text) AS octet_length,
 %s::text IS NULL AS is_null;"""
            target['queries']['parameter_binding'] = binding_sql
            target['parameter_results'] = []
            target['phase'] = 'parameters'
            for name, value in expected.items():
                row = fetch(cursor, binding_sql, [value] * 5)[0]
                row.update(fixture_id=name, expected=value)
                target['parameter_results'].append(row)
                validate_value(row['actual'], value, name)
                length = None if value is None else 27
                require(row['pg_type'] == 'text' and row['char_length'] == length
                        and row['octet_length'] == length and row['is_null'] == (value is None),
                        f'{name}: PG type/length/NULL mismatch')
                row['status'] = 'PASS'
            report['postgresql_parameters'] = {'status': 'PASS', 'cases': len(expected)}
            target['phase'] = 'persistence'

            exists_sql = "SELECT to_regclass('public.b9_temporal_text_poc')::text AS table_name;"
            target['queries']['table_exists'] = exists_sql
            if fetch(cursor, exists_sql)[0]['table_name'] is None:
                ddl = """CREATE TABLE public.b9_temporal_text_poc (
 fixture_id TEXT NOT NULL,
 canonical_temporal_text TEXT COLLATE "C",
 expected_temporal_text TEXT COLLATE "C",
 test_batch_id TEXT NOT NULL,
 PRIMARY KEY (test_batch_id,fixture_id)
);"""
                target['queries']['create_test_table'] = ddl
                cursor.execute(ddl)
            schema_sql = """SELECT column_name,data_type,collation_name,is_nullable
 FROM information_schema.columns WHERE table_schema='public' AND table_name='b9_temporal_text_poc'
 ORDER BY ordinal_position;"""
            target['queries']['table_columns'] = schema_sql
            columns = fetch(cursor, schema_sql)
            require([(c['column_name'], c['data_type'], c['collation_name'], c['is_nullable']) for c in columns]
                    == [('fixture_id', 'text', None, 'NO'),
                        ('canonical_temporal_text', 'text', 'C', 'YES'),
                        ('expected_temporal_text', 'text', 'C', 'YES'),
                        ('test_batch_id', 'text', None, 'NO')], 'Unexpected test table schema')
            target['table_columns'] = columns
            # Explicit synthetic second occurrence; timestamp is not a uniqueness key.
            persisted_expected = {**expected, 'V1_SECOND_OCCURRENCE': expected['V1']}
            insert_sql = """INSERT INTO public.b9_temporal_text_poc
 (fixture_id,canonical_temporal_text,expected_temporal_text,test_batch_id)
 VALUES (%s,%s,%s,%s);"""
            target['queries']['insert'] = insert_sql
            cursor.executemany(insert_sql, [(name, value, value, batch_id)
                                           for name, value in persisted_expected.items()])
        writer.commit()
        target['committed'] = True
    target['writer_closed'] = writer.closed
    target['phase'] = 'readback'

    with closing(psycopg.connect(**connection_args)) as reader:
        with reader.cursor() as cursor:
            target['read_environment'] = fetch(cursor, metadata_sql)[0]
            require(target['read_environment']['backend_pid'] != target['environment']['backend_pid'],
                    'Read-back did not use a new backend')
            read_sql = """SELECT fixture_id,canonical_temporal_text,expected_temporal_text,
 char_length(canonical_temporal_text) AS char_length,octet_length(canonical_temporal_text) AS octet_length
 FROM public.b9_temporal_text_poc WHERE test_batch_id=%s ORDER BY fixture_id;"""
            target['queries']['persisted_readback'] = read_sql
            target['readback'] = fetch(cursor, read_sql, [batch_id])
            validate_readback(target['readback'], persisted_expected)
            require(all(r['char_length'] == r['octet_length'] ==
                        (None if persisted_expected[r['fixture_id']] is None else 27)
                        for r in target['readback']), 'Persisted length mismatch')

            order_sql = """SELECT a.fixture_id AS left_id,b.fixture_id AS right_id,
 CASE WHEN a.canonical_temporal_text COLLATE "C" < b.canonical_temporal_text COLLATE "C" THEN -1
 WHEN a.canonical_temporal_text COLLATE "C" > b.canonical_temporal_text COLLATE "C" THEN 1 ELSE 0 END AS text_cmp
 FROM public.b9_temporal_text_poc a CROSS JOIN public.b9_temporal_text_poc b
 WHERE a.test_batch_id=%s AND b.test_batch_id=%s AND a.canonical_temporal_text IS NOT NULL
 AND b.canonical_temporal_text IS NOT NULL AND a.fixture_id<>'V1_SECOND_OCCURRENCE'
 AND b.fixture_id<>'V1_SECOND_OCCURRENCE';"""
            target['queries']['ordering'] = order_sql
            target['phase'] = 'comparisons'
            target['ordering'] = fetch(cursor, order_sql, [batch_id, batch_id])
            source_pairs = {(r['left_id'], r['right_id']): r['source_cmp'] for r in report['ordering']}
            for row in target['ordering']:
                row['source_cmp'] = source_pairs[(row['left_id'], row['right_id'])]
            verify_ordering(target['ordering'], expected)

            range_sql = """SELECT fixture_id FROM public.b9_temporal_text_poc
 WHERE test_batch_id=%s AND canonical_temporal_text COLLATE "C" >= %s::text COLLATE "C"
 AND canonical_temporal_text COLLATE "C" < %s::text COLLATE "C" ORDER BY fixture_id;"""
            target['queries']['ranges'] = range_sql
            target['ranges'] = []
            ranges = [('adjacent', expected['V1'], expected['V2']),
                      ('zero_duration', expected['V1'], expected['V1']),
                      ('whole_second', expected['ZERO'], expected['NEXT_SECOND']),
                      ('minimum_tick', expected['MIN'], expected['MIN_PLUS_TICK']),
                      ('sentinel_adjacent', expected['MAX_MINUS_TICK'], expected['SENTINEL'])]
            for label, low, high in ranges:
                required = sorted(k for k, value in persisted_expected.items()
                                  if value is not None and low <= value < high)
                actual = [r['fixture_id'] for r in fetch(cursor, range_sql, [batch_id, low, high])]
                target['ranges'].append({'case': label, 'low': low, 'high': high,
                                          'expected': required, 'actual': actual})
                require(actual == required, f'{label}: range mismatch')
            equality_sql = """SELECT fixture_id FROM public.b9_temporal_text_poc
 WHERE test_batch_id=%s AND canonical_temporal_text COLLATE "C" = %s::text COLLATE "C"
 ORDER BY fixture_id;"""
            target['queries']['equality'] = equality_sql
            target['equality'] = []
            for name, value in expected.items():
                required = sorted(k for k, v in persisted_expected.items() if v == value) if value is not None else []
                actual = [r['fixture_id'] for r in fetch(cursor, equality_sql, [batch_id, value])]
                require(actual == required, f'{name}: equality/collision mismatch')
                target['equality'].append({'fixture_id': name, 'expected': required, 'actual': actual})
            null_sql = """SELECT fixture_id FROM public.b9_temporal_text_poc
 WHERE test_batch_id=%s AND canonical_temporal_text IS NULL ORDER BY fixture_id;"""
            target['queries']['nulls'] = null_sql
            target['null_rows'] = fetch(cursor, null_sql, [batch_id])
            require(target['null_rows'] == [{'fixture_id': 'NULL_VALUE'}], 'NULL persistence mismatch')
        reader.rollback()  # End the read-only verification transaction; persisted rows remain.
    target['reader_closed'] = reader.closed
    target['status'] = 'PASS'
    target['phase'] = 'complete'
    report['postgresql_persistence'] = {'status': 'PASS', 'rows': len(persisted_expected),
                                       'commit_close_reconnect': True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', required=True, help='Approved tcp:hostname,port endpoint')
    parser.add_argument('--output', type=Path, required=True, help='New JSON path inside ignored .venv')
    parser.add_argument('--pg-config', type=Path, help='Ignored JSON configuration for the authorized B9 sandbox')
    args = parser.parse_args()
    venv = Path(sys.prefix).resolve()
    output = args.output.resolve()
    if sys.prefix == sys.base_prefix or venv.name != '.venv' or not output.is_relative_to(venv):
        parser.error('Run in project-local .venv and write raw evidence inside it')
    if output.exists() or not output.parent.is_dir():
        parser.error('Choose a new output file in an existing ignored .venv directory')
    report: dict[str, Any] = {
        'python': platform.python_version(), 'platform': platform.platform(),
        'packages': {d.metadata['Name']: d.version for d in importlib.metadata.distributions()},
        'source_endpoint': args.server, 'f2_sql': F2_SQL,
        'postgresql_parameters': {'status': 'NOT RUN', 'reason': 'No --pg-config supplied; source-only invocation'},
        'postgresql_persistence': {'status': 'NOT RUN', 'reason': 'Target invocation not requested'},
        'b9': 'APPROVED — Physical Raw Temporal Representation (scoped)',
    }
    exit_code = 0
    try:
        run_source(args.server, report)
        if args.pg_config is not None:
            run_target(args.pg_config, report)
    except PrecisionError as exc:
        if 'postgresql' in report:
            report['postgresql']['status'] = 'FAIL'
            if report['postgresql']['phase'] == 'parameters':
                report['postgresql_parameters']['status'] = 'FAIL'
            elif report['postgresql']['phase'] != 'configuration':
                report['postgresql_persistence']['status'] = 'FAIL'
        else:
            report['sql_to_python_status'] = 'FAIL'
        report['error'] = str(exc)
        exit_code = 1
    except (OSError, pyodbc.Error, psycopg.Error) as exc:
        if 'postgresql' in report:
            report['postgresql']['status'] = 'BLOCKED' if isinstance(exc, (OSError, psycopg.OperationalError)) else 'FAIL'
        else:
            report['sql_to_python_status'] = 'BLOCKED'
        report['error'] = {'type': type(exc).__name__, 'sqlstate': getattr(exc, 'sqlstate', None)}
        exit_code = 1 if report.get('postgresql', {}).get('status') == 'FAIL' else 2
    with output.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(json.dumps({'sql_to_python': report.get('sql_to_python_status'),
                      'fixtures': len(report.get('fixtures', [])),
                      'ordered_pairs': len(report.get('ordering', [])),
                      'temporal_cells': len(report.get('temporal_samples', [])),
                      'postgresql': report['postgresql_parameters']['status'],
                      'persistence': report['postgresql_persistence']['status'],
                      'raw_evidence': str(args.output)}, ensure_ascii=True))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
