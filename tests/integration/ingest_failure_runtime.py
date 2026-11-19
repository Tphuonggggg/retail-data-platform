"""Opt-in Raw-only rollback probe. Never writes SQL Server or publishes candidates."""
import argparse
import json
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ingestion.common.config import settings
from ingestion.common.contracts import select_objects
from ingestion.common.errors import PipelineError
from ingestion.extractors.sqlserver import SqlServerSource
from ingestion.loaders.postgres import PostgresTarget
from ingestion.full_load import run_full_load


class InjectedFailureTarget(PostgresTarget):
    def write(self, obj, run_id, start_ordinal, rows):
        super().write(obj, run_id, start_ordinal, rows)
        # Real COPY happened in the transaction; now exercise acknowledged rollback.
        raise PipelineError('INJECTED_RUNTIME_COPY_FAILURE')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Writes one failed test capture/metadata to approved Raw only')
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    args = parser.parse_args()
    if not args.execute:
        parser.print_help(); return 0
    config = settings(args.env_file, 64)
    source, target = SqlServerSource(config), InjectedFailureTarget(config)
    run_id = uuid4()
    objects = select_objects(['Warehouse.StockItemHoldings'])
    try:
        target.connect()
        if target.connection.execute("SELECT COUNT(*) FROM ingestion_meta.runs WHERE status='RUNNING'").fetchone()[0]:
            raise PipelineError('ACTIVE_RUN_INSPECT_FIRST')
        pointer = target.connection.execute('SELECT publication_id FROM ingestion_meta.raw_current WHERE singleton').fetchone()[0]
        try:
            run_full_load(source, target, objects, run_id=run_id)
        except PipelineError as error:
            if error.code != 'INJECTED_RUNTIME_COPY_FAILURE': raise
        else:
            raise PipelineError('EXPECTED_FAILURE_NOT_OBSERVED')
        state = target.connection.execute('SELECT status,error_code FROM ingestion_meta.runs WHERE run_id=%s', (run_id,)).fetchone()
        payload = target.connection.execute('SELECT COUNT(*) FROM raw.warehouse_stockitemholdings WHERE _run_id=%s', (run_id,)).fetchone()[0]
        audits = target.connection.execute('SELECT COUNT(*) FROM ingestion_meta.load_audits WHERE run_id=%s', (run_id,)).fetchone()[0]
        after = target.connection.execute('SELECT publication_id FROM ingestion_meta.raw_current WHERE singleton').fetchone()[0]
        passed = tuple(state) == ('FAILED','INJECTED_RUNTIME_COPY_FAILURE') and payload == audits == 0 and pointer == after
        print(json.dumps({'run_id':str(run_id), 'status':'PASS' if passed else 'FAIL', 'run_state':list(state),
                          'payload_rows':payload, 'audit_rows':audits, 'pointer_unchanged':pointer == after}))
        return int(not passed)
    except Exception as error:
        print(json.dumps({'run_id':str(run_id),'status':'FAIL','category':getattr(error,'code','DRIVER_FAILURE')})); return 1
    finally:
        source.close(); target.close()


if __name__ == '__main__': raise SystemExit(main())
