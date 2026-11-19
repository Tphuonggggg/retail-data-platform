"""Explicit read-only acceptance checks. Outputs aggregates, never business rows or secrets."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import sys
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ingestion.common.config import settings
from ingestion.common.contracts import select_objects, ms_quote, pg_quote
from ingestion.extractors.sqlserver import SqlServerSource
from ingestion.loaders.postgres import PostgresTarget


def scalar(value):
    if isinstance(value, Decimal):
        text = format(value, 'f')
        return text.rstrip('0').rstrip('.') if '.' in text else text
    return value


def measures(obj, postgres=False):
    quote = pg_quote if postgres else ms_quote
    count = 'COUNT(*)' if postgres else 'COUNT_BIG(*)'
    fields = [('rows', count)]
    if obj.primary_key:
        fields.append(('distinct_keys', ('COUNT' if postgres else 'COUNT_BIG') + '(DISTINCT ' + quote(obj.primary_key) + ')'))
    for col in obj.columns:
        name = quote(col.name)
        fields.append(('null:' + col.name, 'COALESCE(SUM(CASE WHEN ' + name + ' IS NULL THEN CAST(1 AS bigint) ELSE 0 END),0)'))
        if col.source_type == 'int' or col.source_type.startswith('decimal'):
            fields.append(('sum:' + col.name, 'SUM(CAST(' + name + ' AS decimal(38,6)))'))
        if col.source_type == 'datetime2(7)':
            expr = name if postgres else col.projection.rsplit(' AS ', 1)[0]
            fields.extend((('min:' + col.name, 'MIN(' + expr + ')'), ('max:' + col.name, 'MAX(' + expr + ')')))
    return fields


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Explicit SELECT-only network checks')
    parser.add_argument('--run-id', type=UUID)
    parser.add_argument('--object', action='append', dest='objects')
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    args = parser.parse_args()
    if not args.execute:
        parser.print_help(); return 0
    source = SqlServerSource(settings(args.env_file))
    target = None
    try:
        objects = select_objects(args.objects)
        source.connect(); source.preflight(objects)
        output = {'observed_at': datetime.now(timezone.utc).isoformat(), 'objects': [], 'read_only': True}
        if args.run_id:
            target = PostgresTarget(source.config); target.connect(); target.preflight(objects)
        for obj in objects:
            fields = measures(obj)
            with source.connection.cursor() as cursor:
                row = cursor.execute('SELECT ' + ','.join(v for _, v in fields) + ' FROM ' + obj.ms_table).fetchone()
            baseline = {k: scalar(v) for (k, _), v in zip(fields, row, strict=True)}
            result = {'object': obj.name, 'source': baseline}
            if target:
                fields = measures(obj, True)
                row = target.connection.execute('SELECT ' + ','.join(v for _, v in fields) + ' FROM ' + obj.pg_table + ' WHERE _run_id=%s', (args.run_id,)).fetchone()
                actual = {k: scalar(v) for (k, _), v in zip(fields, row, strict=True)}
                result.update(target=actual, status='PASS' if baseline == actual else 'FAIL')
            output['objects'].append(result)
        if target:
            output['durable_reconciliation'] = target.reconcile(args.run_id, objects)
            output['run_metadata'] = list(target.connection.execute('SELECT status,consistency_state FROM ingestion_meta.runs WHERE run_id=%s', (args.run_id,)).fetchone())
            output['publication_pointer'] = str(target.connection.execute('SELECT publication_id FROM ingestion_meta.raw_current WHERE singleton').fetchone()[0])
        print(json.dumps(output))
        return int(any(o.get('status') == 'FAIL' for o in output['objects']))
    except Exception as error:
        print(json.dumps({'status': 'FAIL', 'category': getattr(error, 'code', 'DRIVER_OR_CONFIGURATION_FAILURE'), 'error_type': type(error).__name__}))
        return 1
    finally:
        source.close()
        if target: target.close()


if __name__ == '__main__':
    raise SystemExit(main())
