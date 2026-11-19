"""Explicit read-only acceptance checks. Outputs aggregates, never business rows or secrets."""
from __future__ import annotations

import argparse
from contextlib import closing
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

REFERENCES = [
    ('Sales.Customers', 'BillToCustomerID', 'Sales.Customers', 'CustomerID'),
    ('Sales.Orders', 'CustomerID', 'Sales.Customers', 'CustomerID'),
    ('Sales.Orders', 'BackorderOrderID', 'Sales.Orders', 'OrderID'),
    ('Sales.OrderLines', 'OrderID', 'Sales.Orders', 'OrderID'),
    ('Sales.OrderLines', 'StockItemID', 'Warehouse.StockItems', 'StockItemID'),
    ('Sales.Invoices', 'OrderID', 'Sales.Orders', 'OrderID'),
    ('Sales.Invoices', 'CustomerID', 'Sales.Customers', 'CustomerID'),
    ('Sales.Invoices', 'BillToCustomerID', 'Sales.Customers', 'CustomerID'),
    ('Sales.InvoiceLines', 'InvoiceID', 'Sales.Invoices', 'InvoiceID'),
    ('Sales.InvoiceLines', 'StockItemID', 'Warehouse.StockItems', 'StockItemID'),
    ('Sales.CustomerTransactions', 'CustomerID', 'Sales.Customers', 'CustomerID'),
    ('Sales.CustomerTransactions', 'InvoiceID', 'Sales.Invoices', 'InvoiceID'),
    ('Warehouse.StockItemHoldings', 'StockItemID', 'Warehouse.StockItems', 'StockItemID'),
    ('Warehouse.StockItemTransactions', 'StockItemID', 'Warehouse.StockItems', 'StockItemID'),
    ('Warehouse.StockItemTransactions', 'InvoiceID', 'Sales.Invoices', 'InvoiceID'),
    ('Warehouse.StockItemTransactions', 'CustomerID', 'Sales.Customers', 'CustomerID'),
]


def reference_checks(source, target, objects, run_id):
    selected = {o.name: o for o in objects}
    results = []
    for child, foreign, parent, key in REFERENCES:
        if child not in selected or parent not in selected:
            continue
        c, p = selected[child], selected[parent]
        with closing(source.connection.cursor()) as cursor:
            source_orphans = cursor.execute('SELECT COUNT_BIG(*) FROM ' + c.ms_table +
                ' c LEFT JOIN ' + p.ms_table + ' p ON c.' + ms_quote(foreign) + '=p.' + ms_quote(key) +
                ' WHERE c.' + ms_quote(foreign) + ' IS NOT NULL AND p.' + ms_quote(key) + ' IS NULL').fetchone()[0]
        target_orphans = target.connection.execute('SELECT COUNT(*) FROM ' + c.pg_table +
            ' c LEFT JOIN ' + p.pg_table + ' p ON c.' + pg_quote(foreign) + '=p.' + pg_quote(key) +
            ' AND p._run_id=%s WHERE c._run_id=%s AND c.' + pg_quote(foreign) +
            ' IS NOT NULL AND p.' + pg_quote(key) + ' IS NULL', (run_id, run_id)).fetchone()[0]
        results.append({'child': child, 'key': foreign, 'parent': parent, 'source_orphans': source_orphans,
                        'target_orphans': target_orphans, 'status': 'PASS' if source_orphans == target_orphans == 0 else 'FAIL'})
    return results


def scalar(value):
    if isinstance(value, Decimal):
        text = format(value, 'f')
        return text.rstrip('0').rstrip('.') if '.' in text else text
    return value


def normalize_measures(fields, row):
    # PostgreSQL SUM(bigint) is numeric; SQL Server SUM(bigint) is bigint.
    # Counts are integers on both engines; amount sums retain exact decimal text.
    return {k: (int(v) if v is not None and (k == 'rows' or k == 'distinct_keys' or k.startswith('null:'))
                else scalar(v)) for (k, _), v in zip(fields, row, strict=True)}


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
            with closing(source.connection.cursor()) as cursor:
                row = cursor.execute('SELECT ' + ','.join(v for _, v in fields) + ' FROM ' + obj.ms_table).fetchone()
            baseline = normalize_measures(fields, row)
            result = {'object': obj.name, 'source': baseline}
            if target:
                fields = measures(obj, True)
                row = target.connection.execute('SELECT ' + ','.join(v for _, v in fields) + ' FROM ' + obj.pg_table + ' WHERE _run_id=%s', (args.run_id,)).fetchone()
                actual = normalize_measures(fields, row)
                result.update(target=actual, status='PASS' if baseline == actual else 'FAIL')
            output['objects'].append(result)
        if target:
            output['durable_reconciliation'] = target.reconcile(args.run_id, objects)
            output['run_metadata'] = list(target.connection.execute('SELECT status,consistency_state FROM ingestion_meta.runs WHERE run_id=%s', (args.run_id,)).fetchone())
            output['publication_pointer'] = str(target.connection.execute('SELECT publication_id FROM ingestion_meta.raw_current WHERE singleton').fetchone()[0])
            output['references'] = reference_checks(source, target, objects, args.run_id)
            output['reference_scope'] = 'WITHIN_SELECTED_POPULATIONS; external Application/Purchasing references not loaded'
            output['temporal_intervals'] = []
            for obj in objects:
                if 'ValidFrom' not in {c.name for c in obj.columns}:
                    continue
                bad = target.connection.execute('SELECT COUNT(*) FROM ' + obj.pg_table +
                    ' WHERE _run_id=%s AND "ValidFrom">"ValidTo"', (args.run_id,)).fetchone()[0]
                output['temporal_intervals'].append({'object': obj.name, 'reversed_intervals': bad,
                                                     'status': 'PASS' if bad == 0 else 'FAIL'})
        print(json.dumps(output))
        return int(any(o.get('status') == 'FAIL' for group in ('objects', 'references', 'temporal_intervals')
                       for o in output.get(group, [])))
    except Exception as error:
        print(json.dumps({'status': 'FAIL', 'category': getattr(error, 'code', 'DRIVER_OR_CONFIGURATION_FAILURE'), 'error_type': type(error).__name__}))
        return 1
    finally:
        source.close()
        if target: target.close()


if __name__ == '__main__':
    raise SystemExit(main())
