"""Synthetic isolated demo. Never loads .env or the WWI/Raw configuration."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
from decimal import Decimal
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

from ingestion.common.codecs import RowDigest
from ingestion.common.contracts import Column, SourceObject
from ingestion.incremental import compare

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / '.local/portfolio-demo'
PROJECT = 'retail-portfolio-demo'
DATABASE = 'retail_portfolio_demo'
USER = 'portfolio_demo'
PORT = 55439
SAMPLE = SourceObject('Demo', 'Lines', (
    Column('ID', 'int', False), Column('SalesDate', 'date', False),
    Column('Product', 'nvarchar(50)', False), Column('Quantity', 'int', False),
    Column('Sales', 'decimal(18,2)', False), Column('Note', 'nvarchar(50)', True),
    Column('Stamp', 'datetime2(7)', False)), 'ID', ('ID',), 'SYNTHETIC_PORTFOLIO')


def initial_rows():
    """Authored fixture, no WWI rows or extracted private data."""
    return [(1, date(2024, 1, 1), 'Cà phê', 2, Decimal('20.00'), None, '2024-01-01T00:00:00.0000001'),
            (2, date(2024, 1, 1), 'Trà', 3, Decimal('15.00'), '', '2024-01-01T00:00:00.0000002')]


def changed_rows():
    a, b = initial_rows()
    return [(a[0], a[1], a[2], 3, Decimal('30.00'), a[5], a[6]), b,
            (3, date(2024, 1, 2), 'Cà phê', 1, Decimal('10.00'), 'Mới', '2024-01-02T00:00:00.0000001')]


def digest(rows):
    value = RowDigest()
    for row in rows:
        value.add(row)
    return value.count, value.hexdigest


def environment():
    HOME.mkdir(parents=True, exist_ok=True)
    config = HOME / 'demo.env'
    if not config.exists():
        # Independent generated credential; never printed or passed in argv.
        config.write_text('RETAIL_DEMO_PASSWORD=' + secrets.token_hex(24) + '\n', encoding='utf-8')
        config.chmod(0o600)
    password = config.read_text(encoding='utf-8').strip().removeprefix('RETAIL_DEMO_PASSWORD=')
    if len(password) != 48 or any(c not in '0123456789abcdef' for c in password):
        raise ValueError('DEMO_CREDENTIAL_FILE_INVALID')
    env = {k: v for k, v in os.environ.items() if not k.startswith(('RETAIL_DEMO_', 'PG', 'DBT_'))}
    env['RETAIL_DEMO_PASSWORD'] = password
    (HOME / 'profiles.yml').write_text((ROOT / 'dbt/demo/profiles.yml.example').read_text(encoding='utf-8'), encoding='utf-8')
    env['DBT_PROFILES_DIR'] = str(HOME)
    env['DBT_LOG_PATH'] = str(HOME / 'logs')
    env['DBT_TARGET_PATH'] = str(HOME / 'target')
    env['DBT_SEND_ANONYMOUS_USAGE_STATS'] = 'false'
    env['DBT_USE_COLORS'] = 'false'
    return env


def compose(env, *args):
    result = subprocess.run(['docker', 'compose', '--project-name', PROJECT, '--env-file',
                             str(HOME / 'demo.env'), '-f', str(ROOT / 'infrastructure/docker/compose.demo.yaml'),
                             *args], env=env, cwd=ROOT, capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError('DEMO_COMPOSE_FAILED_CHECK_DOCKER_ENGINE')


def connect(env):
    import psycopg
    return psycopg.connect(host='127.0.0.1', port=PORT, dbname=DATABASE, user=USER,
                          password=env['RETAIL_DEMO_PASSWORD'], connect_timeout=3)


def guard(db):
    if db.execute('SELECT current_database(),current_user').fetchone() != (DATABASE, USER):
        raise ValueError('DEMO_TARGET_IDENTITY_MISMATCH')
    if db.execute("SELECT count(*) FROM pg_namespace WHERE nspname IN ('raw','ingestion_meta','dw_core')").fetchone()[0]:
        raise ValueError('DEMO_TARGET_NOT_ISOLATED')


def initialize(db):
    from psycopg import sql
    guard(db)
    db.execute('CREATE SCHEMA IF NOT EXISTS demo_raw')
    columns = sql.SQL(',').join(sql.SQL('{} {}').format(sql.Identifier(c.name), sql.SQL(c.pg_type))
                               for c in SAMPLE.columns)
    db.execute(sql.SQL('CREATE TABLE IF NOT EXISTS demo_raw.lines ({}, PRIMARY KEY ("ID"))').format(columns))


def require_changes(counts, expected):
    if Counter(counts) != Counter(expected):
        raise ValueError('DEMO_UNEXPECTED_CHANGE_COUNTS')


def apply_snapshot(db, rows, fail=False, *, expected_changes=None):
    """Atomic demo upsert and ordered count/digest read-back using production compare/codecs."""
    from psycopg import sql
    guard(db)
    with db.transaction():
        before = db.execute('SELECT * FROM demo_raw.lines ORDER BY "ID"').fetchall()
        counts = Counter()
        for change in compare(SAMPLE, before, rows):
            counts[change.kind] += 1
            if change.kind == 'DELETE':
                raise ValueError('DEMO_DELETE_UNSUPPORTED')
            if change.kind in {'INSERT', 'UPDATE'}:
                fields = sql.SQL(',').join(sql.Identifier(c.name) for c in SAMPLE.columns)
                updates = sql.SQL(',').join(sql.SQL('{}=EXCLUDED.{}').format(sql.Identifier(c.name), sql.Identifier(c.name))
                                          for c in SAMPLE.columns[1:])
                db.execute(sql.SQL('INSERT INTO demo_raw.lines ({}) VALUES ({}) ON CONFLICT ("ID") DO UPDATE SET {}')
                           .format(fields, sql.SQL(',').join(sql.Placeholder() for _ in SAMPLE.columns), updates), change.after)
        if expected_changes is not None:
            require_changes(counts, expected_changes)
        if fail:
            raise ValueError('DEMO_INJECTED_ROLLBACK')
        stored = db.execute('SELECT * FROM demo_raw.lines ORDER BY "ID"').fetchall()
        if digest(stored) != digest(rows):
            raise ValueError('DEMO_RECONCILIATION_FAILED')
    return {'changes': dict(counts), 'rows': len(rows), 'digest': digest(rows)[1]}


def run(env):
    compose(env, 'up', '-d', '--wait', '--wait-timeout', '90')
    with connect(env) as db:
        initialize(db)
        db.commit()
        # Keep SELECT guards outside apply_snapshot's transaction from nesting it.
        db.autocommit = True
        existing = db.execute('SELECT * FROM demo_raw.lines ORDER BY "ID"').fetchall()
        results = {}
        if existing:
            if digest(existing) != digest(changed_rows()):
                raise ValueError('DEMO_UNEXPECTED_EXISTING_STATE')
            results['completed_rerun'] = apply_snapshot(db, changed_rows(), expected_changes={'UNCHANGED': 3})
        else:
            results['initial'] = apply_snapshot(db, initial_rows(), expected_changes={'INSERT': 2})
            results['no_change'] = apply_snapshot(db, initial_rows(), expected_changes={'UNCHANGED': 2})
            changed = {'UPDATE': 1, 'UNCHANGED': 1, 'INSERT': 1}
            try:
                apply_snapshot(db, changed_rows(), fail=True, expected_changes=changed)
            except ValueError as error:
                if str(error) != 'DEMO_INJECTED_ROLLBACK':
                    raise
            else:
                raise ValueError('DEMO_ROLLBACK_NOT_INJECTED')
            if digest(db.execute('SELECT * FROM demo_raw.lines ORDER BY "ID"').fetchall()) != digest(initial_rows()):
                raise ValueError('DEMO_ROLLBACK_FAILED')
            results['rollback_verified'] = True
            results['recovered'] = apply_snapshot(db, changed_rows(), expected_changes=changed)
        process = subprocess.run([sys.executable, '-m', 'dbt.cli.main', 'build', '--project-dir', str(ROOT / 'dbt/demo'),
                                  '--profiles-dir', str(HOME)], env=env, capture_output=True, timeout=180)
        # dbt console output and artifacts stay local; do not echo driver errors.
        (HOME / 'dbt-output.txt').write_bytes(process.stdout + process.stderr)
        if process.returncode:
            raise RuntimeError('DEMO_DBT_FAILED_INSPECT_PRIVATE_OUTPUT')
        output = db.execute('SELECT sales_date,sales_amount,units_sold FROM demo_analytics.mart_demo_daily ORDER BY 1').fetchall()
        expected = [(date(2024, 1, 1), Decimal('45.00'), 6), (date(2024, 1, 2), Decimal('10.00'), 1)]
        if output != expected:
            raise ValueError('DEMO_ANALYTICAL_OUTPUT_MISMATCH')
        results['daily_output'] = output
        results['status'] = 'PASS'
        if 'initial' in results:
            (HOME / 'initial-result.json').write_text(json.dumps(results, default=str, indent=2), encoding='utf-8')
        (HOME / 'result.json').write_text(json.dumps(results, default=str, indent=2), encoding='utf-8')
        print(json.dumps(results, default=str))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('run', 'config', 'down'))
    args = parser.parse_args(argv)
    try:
        env = environment()
        if args.action == 'run':
            run(env)
        elif args.action == 'config':
            compose(env, 'config', '--quiet')
            print('PASS: isolated Compose configuration; runtime NOT_RUN')
        else:
            compose(env, 'down')
            print('Stopped isolated demo; tmpfs data discarded; no named volumes removed')
        return 0
    except Exception as error:
        print(json.dumps({'status': 'FAIL', 'error_type': type(error).__name__,
                          'detail': 'Demo failed; verify Docker/dependencies and private local artifacts. No live target used.'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
