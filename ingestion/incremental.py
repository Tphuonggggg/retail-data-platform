"""Sales-only snapshot-diff candidates. No DDL, source writes or publication."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
from typing import Iterable, Iterator
from uuid import UUID, uuid4

from ingestion.common.codecs import RowDigest, admit_row
from ingestion.common.config import settings
from ingestion.common.contracts import SourceObject, contract_hash, pg_quote, select_objects
from ingestion.common.errors import PipelineError
from ingestion.extractors.sqlserver import SqlServerSource
from ingestion.loaders.postgres import PostgresTarget

SALES = ('Sales.Customers', 'Sales.InvoiceLines', 'Sales.Invoices', 'Sales.OrderLines',
         'Sales.Orders', 'Warehouse.StockItems')
ALGORITHM = 'sales-snapshot-diff-v1'
MAX_DEPTH = 32


def objects() -> tuple[SourceObject, ...]:
    return select_objects(list(SALES))


def fingerprint(row: tuple) -> str:
    digest = RowDigest()
    digest.add(row)
    return digest.hexdigest


def checked_rows(obj: SourceObject, rows: Iterable[tuple]) -> Iterator[tuple]:
    """One row per ordered integer business key; no dictionary of source populations."""
    if not obj.primary_key or tuple(obj.order_by) != (obj.primary_key,):
        raise PipelineError('INCREMENTAL_STABLE_KEY_REQUIRED')
    index = next(i for i,c in enumerate(obj.columns) if c.name == obj.primary_key)
    previous = None
    for values in rows:
        row = admit_row(obj, values)
        key = row[index]
        if type(key) is not int or (previous is not None and key <= previous):
            raise PipelineError('INCREMENTAL_DUPLICATE_OR_UNORDERED_KEY')
        previous = key
        yield row


@dataclass(frozen=True)
class Change:
    key: int
    kind: str
    before: tuple | None
    after: tuple | None


def compare(obj: SourceObject, before: Iterable[tuple], after: Iterable[tuple]) -> Iterator[Change]:
    """Merge complete ordered streams. Consumers must not commit until both reach EOF."""
    if not obj.primary_key or obj.primary_key not in {c.name for c in obj.columns}:
        raise PipelineError('INCREMENTAL_STABLE_KEY_REQUIRED')
    key_index = next(i for i,c in enumerate(obj.columns) if c.name == obj.primary_key)
    old, new = iter(checked_rows(obj,before)), iter(checked_rows(obj,after))
    a,b = next(old,None),next(new,None)
    while a is not None or b is not None:
        if b is None or (a is not None and a[key_index] < b[key_index]):
            yield Change(a[key_index],'DELETE',a,None)
            a=next(old,None)
        elif a is None or b[key_index] < a[key_index]:
            yield Change(b[key_index],'INSERT',None,b)
            b=next(new,None)
        else:
            # Exact typed equality also protects against a SHA256 collision.
            yield Change(a[key_index],'UNCHANGED' if a==b else 'UPDATE',a,b)
            a,b=next(old,None),next(new,None)


def state_sql(obj: SourceObject) -> str:
    """Pinned typed overlay, with no implicit latest version or mutable global pointer."""
    if obj.name not in SALES:
        raise PipelineError('INCREMENTAL_OUT_OF_SCOPE')
    # The migration creates matching SECURITY INVOKER functions. No identifiers
    # or fragments come from CLI/YAML. Function result ordinals are stable PKs.
    return 'SELECT '+','.join(pg_quote(c.name) for c in obj.columns)+ \
        ' FROM raw.'+pg_quote('sales_state_'+obj.target)+'(%s) ORDER BY '+pg_quote(obj.primary_key)


def assert_version(db, version: UUID) -> str:
    """Independent from dbt's model graph; existing Full Load guard remains intact."""
    db.execute('SELECT ingestion_meta.assert_sales_version(%s)',(version,))
    row=db.execute('SELECT status,contract_hash,algorithm FROM ingestion_meta.incremental_versions '
                   'WHERE version_id=%s',(version,)).fetchone()
    if row is None:
        return 'FULL'
    if tuple(row)!=('VALIDATED',contract_hash(),ALGORITHM):
        raise PipelineError('INCREMENTAL_VERSION_NOT_VALIDATED')
    audits=db.execute('SELECT evidence FROM ingestion_meta.incremental_versions WHERE version_id=%s',(version,)).fetchone()[0]
    if set(audits.get('objects',{}))!=set(SALES):
        raise PipelineError('INCREMENTAL_INCOMPLETE_SCOPE')
    return 'INCREMENTAL'


class IncrementalTarget:
    def __init__(self, target: PostgresTarget):
        self.target=target
        self.db=target.connection

    def preflight(self):
        self.target.preflight(objects())
        expected_columns={
            'incremental_versions':{'version_id','parent_id','base_run_id','depth','contract_hash','algorithm','status',
                                    'source_context','evidence','error_code','started_at','finished_at','acknowledged_publication_id'},
            'incremental_events':{'version_id','object_name','business_key','change_type','before_version','before_fingerprint','after_fingerprint'}}
        for table in ('incremental_versions','incremental_events'):
            if self.db.execute('SELECT to_regclass(%s)',('ingestion_meta.'+table,)).fetchone()[0] is None:
                raise PipelineError('INCREMENTAL_MIGRATION_REQUIRES_OWNER_APPROVAL')
            owner=self.db.execute('SELECT tableowner FROM pg_tables WHERE schemaname=%s AND tablename=%s',
                                   ('ingestion_meta',table)).fetchone()
            if owner!=('postgres',):raise PipelineError('INCREMENTAL_OWNER_MISMATCH')
            columns={r[0] for r in self.db.execute('SELECT column_name FROM information_schema.columns WHERE table_schema=%s AND table_name=%s',('ingestion_meta',table))}
            if columns!=expected_columns[table]:raise PipelineError('INCREMENTAL_METADATA_SCHEMA_MISMATCH')
            for privilege in ('SELECT','INSERT','UPDATE','DELETE','TRUNCATE'):
                allowed=privilege in ('SELECT','INSERT') or (table=='incremental_versions' and privilege=='UPDATE')
                if self.db.execute('SELECT has_table_privilege(current_user,%s,%s)',('ingestion_meta.'+table,privilege)).fetchone()[0] != allowed:
                    raise PipelineError('INCREMENTAL_METADATA_PRIVILEGE_MISMATCH')
        for obj in objects():
            table='raw.delta_'+obj.target
            owner=self.db.execute('SELECT tableowner FROM pg_tables WHERE schemaname=%s AND tablename=%s',('raw','delta_'+obj.target)).fetchone()
            if owner!=('postgres',):raise PipelineError('INCREMENTAL_OWNER_MISMATCH')
            query='SELECT column_name,data_type,is_nullable,numeric_precision,numeric_scale,collation_name FROM information_schema.columns WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position'
            original=self.db.execute(query,('raw',obj.target)).fetchall()
            actual=self.db.execute(query,('raw','delta_'+obj.target)).fetchall()
            if actual!=original:raise PipelineError('INCREMENTAL_PAYLOAD_SCHEMA_MISMATCH')
            for privilege in ('SELECT','INSERT','UPDATE','DELETE','TRUNCATE'):
                if self.db.execute('SELECT has_table_privilege(current_user,%s,%s)',(table,privilege)).fetchone()[0] != (privilege in ('SELECT','INSERT')):
                    raise PipelineError('INCREMENTAL_PAYLOAD_PRIVILEGE_MISMATCH')
        for schema,name in [('raw','sales_state_'+o.target) for o in objects()]+[('ingestion_meta','assert_sales_version')]:
            fn=self.db.execute("SELECT p.prosecdef,pg_get_userbyid(p.proowner),has_function_privilege(current_user,p.oid,'EXECUTE') "
                "FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname=%s AND p.proname=%s AND p.proargtypes='2950'::oidvector",(schema,name)).fetchone()
            if fn!=(False,'postgres',True):raise PipelineError('INCREMENTAL_FUNCTION_CONTRACT_MISMATCH')
        # This is a candidate facility, not an ACK/publication mechanism.
        if self.db.execute('SELECT count(*) FROM ingestion_meta.incremental_versions WHERE acknowledged_publication_id IS NOT NULL').fetchone()[0]:
            raise PipelineError('INCREMENTAL_UNSUPPORTED_ACK_STATE')

    def rows(self, obj, version):
        from psycopg import sql
        with self.db.cursor(name='incr_'+uuid4().hex) as cursor:
            is_full=self.db.execute('SELECT 1 FROM ingestion_meta.runs WHERE run_id=%s AND status=%s',
                                    (version,'SUCCEEDED')).fetchone()
            query=(sql.SQL('SELECT {} FROM {} WHERE _run_id=%s ORDER BY {}').format(
                sql.SQL(',').join(sql.Identifier(c.name) for c in obj.columns),sql.Identifier('raw',obj.target),
                sql.Identifier(obj.primary_key)) if is_full else state_sql(obj))
            cursor.execute(query,(version,))
            while batch:=cursor.fetchmany(obj.page_size(self.target.config.batch_size)):
                yield from (tuple(row) for row in batch)

    def write_batch(self,obj,version,events,payload):
        from psycopg import sql
        if payload:
            columns=['_run_id','_row_ordinal']+[c.name for c in obj.columns]
            query=sql.SQL('COPY {} ({}) FROM STDIN').format(sql.Identifier('raw','delta_'+obj.target),
                      sql.SQL(',').join(sql.Identifier(c) for c in columns))
            with self.db.cursor().copy(query) as copy:
                for key,row in payload:copy.write_row((version,key+2147483649,*row))
        if events:
            with self.db.cursor().copy('COPY ingestion_meta.incremental_events '
                '(version_id,object_name,business_key,change_type,before_version,before_fingerprint,after_fingerprint) FROM STDIN') as copy:
                for change in events:
                    copy.write_row((version,obj.name,change.key,change.kind,change.before_version,
                                    change.before_hash,change.after_hash))


@dataclass(frozen=True)
class Event:
    key: int
    kind: str
    before_version: UUID
    before_hash: str | None
    after_hash: str | None


def reconcile(target: IncrementalTarget,version: UUID) -> dict:
    assert_version(target.db,version)
    row=target.db.execute('SELECT evidence FROM ingestion_meta.incremental_versions WHERE version_id=%s',(version,)).fetchone()
    if row is None:raise PipelineError('INCREMENTAL_VERSION_REQUIRED')
    result={}
    with target.db.transaction():
        for obj in objects():
            digest=RowDigest()
            for values in checked_rows(obj,target.rows(obj,version)):digest.add(values)
            expected=row[0]['objects'][obj.name]
            if (digest.count,digest.hexdigest)!=(expected['source_rows'],expected['digest']):
                raise PipelineError('INCREMENTAL_DURABLE_RECONCILIATION_FAILED')
            result[obj.name]={'rows':digest.count,'digest':digest.hexdigest,'status':'PASS'}
    return result


def run(source: SqlServerSource, target: IncrementalTarget, version: UUID, parent: UUID) -> dict:
    """One atomic six-object candidate. A fresh source extraction always gets a new ID."""
    from psycopg.types.json import Jsonb
    db=target.db
    if not db.execute('SELECT pg_try_advisory_lock(941061)').fetchone()[0]:
        raise PipelineError('INGESTION_ALREADY_ACTIVE')
    if db.execute('SELECT 1 FROM ingestion_meta.runs WHERE run_id=%s',(version,)).fetchone():
        raise PipelineError('INCREMENTAL_ID_COLLIDES_WITH_FULL_LOAD')
    prior=db.execute('SELECT status,parent_id,contract_hash,algorithm,evidence FROM ingestion_meta.incremental_versions '
                     'WHERE version_id=%s',(version,)).fetchone()
    if prior:
        if tuple(prior[1:4])!=(parent,contract_hash(),ALGORITHM):
            raise PipelineError('INCREMENTAL_RUN_ID_CONFLICT')
        if prior[0]=='VALIDATED':
            return {'status':'ALREADY_VALIDATED_NO_REEXTRACTION','version_id':str(version),
                    'reconciliation':reconcile(target,version)}
        # Failed input cannot be reconstructed from another live read. Preserve
        # failure evidence; same-ID retry deterministically refuses re-extraction.
        raise PipelineError('INCREMENTAL_FAILED_OR_UNKNOWN_ID_USE_NEW_VERSION')
    assert_version(db,parent)
    root=db.execute('SELECT base_run_id,depth FROM ingestion_meta.incremental_versions WHERE version_id=%s',(parent,)).fetchone()
    base,depth=(root[0],root[1]+1) if root else (parent,1)
    if depth>MAX_DEPTH:raise PipelineError('INCREMENTAL_CHAIN_LIMIT_REQUIRES_REVIEWED_COMPACTION')
    source.preflight(objects())
    # Current WWI has SNAPSHOT OFF. No isolation/config changes, writer locks,
    # business deletion inference or consistency upgrade are performed here.
    fixture_boundary=(getattr(source,'fixture_boundary',False) is True and
                      getattr(target,'fixture_boundary',False) is True)
    if fixture_boundary:
        namespace=getattr(db,'fixture_namespace','')
        if (not re.fullmatch(r'dbt_sales_test\.inc_[0-9a-f]{12}_',namespace)
            or getattr(source,'ns',None) is not db
            or db.execute('SELECT current_database(),current_user').fetchone()!=('retail_raw','retail_transform')):
            raise PipelineError('INCREMENTAL_INVALID_FIXTURE_BOUNDARY')
    consistency='VERIFIED_FIXTURE' if fixture_boundary else 'UNVERIFIED'
    db.execute('INSERT INTO ingestion_meta.incremental_versions '
               '(version_id,parent_id,base_run_id,depth,contract_hash,algorithm,source_context) '
               'VALUES(%s,%s,%s,%s,%s,%s,%s)',
               (version,parent,base,depth,contract_hash(),ALGORITHM,Jsonb(source.context)))
    began=time.perf_counter();stats={'objects':{},'consistency':consistency,'published':False,'acknowledged_checkpoint':None,
        'boundary_started_at':datetime.now(timezone.utc).isoformat()}
    commit_attempted=False
    try:
        with db.transaction():
            for obj in objects():
                started=time.perf_counter();digest=RowDigest();counts=Counter()
                count_started=time.perf_counter()
                expected=source.count(obj);events=[];payload=[];written=0
                extraction_seconds=time.perf_counter()-count_started
                load_seconds=0.0
                def stream():
                    nonlocal extraction_seconds
                    iterator=iter(source.batches(obj))
                    while True:
                        fetched=time.perf_counter()
                        try:batch=next(iterator)
                        except StopIteration:
                            extraction_seconds+=time.perf_counter()-fetched
                            break
                        extraction_seconds+=time.perf_counter()-fetched
                        yield from batch
                # Counts do not establish snapshot isolation, but detect common
                # partial/unstable scans. EOF/driver failures roll back all deltas.
                for change in compare(obj,target.rows(obj,parent),stream()):
                    counts[change.kind]+=1
                    if change.after is not None:digest.add(change.after)
                    if change.kind=='DELETE' and not fixture_boundary:
                        raise PipelineError('INCREMENTAL_DELETE_REQUIRES_CONSISTENT_COMPLETE_SNAPSHOT')
                    if change.kind!='UNCHANGED':
                        events.append(Event(change.key,change.kind,parent,
                            fingerprint(change.before) if change.before is not None else None,
                            fingerprint(change.after) if change.after is not None else None))
                        if change.after is not None:payload.append((change.key,change.after));written+=1
                    if len(events)>=obj.page_size(target.target.config.batch_size):
                        loading=time.perf_counter();target.write_batch(obj,version,events,payload)
                        load_seconds+=time.perf_counter()-loading;events=[];payload=[]
                loading=time.perf_counter()
                target.write_batch(obj,version,events,payload)
                load_seconds+=time.perf_counter()-loading
                count_started=time.perf_counter();after_count=source.count(obj)
                extraction_seconds+=time.perf_counter()-count_started
                if digest.count!=expected or after_count!=expected:
                    raise PipelineError('INCREMENTAL_INCOMPLETE_SOURCE_SCAN')
                elapsed=time.perf_counter()-started
                stats['objects'][obj.name]={'source_rows':digest.count,'digest':digest.hexdigest,
                    'changes':{k:counts[k] for k in ('INSERT','UPDATE','DELETE','UNCHANGED')},
                    'payload_rows_written':written,'scan_compare_load_seconds':round(elapsed,6),
                    'source_fetch_count_seconds':round(extraction_seconds,6),'payload_event_write_seconds':round(load_seconds,6),
                    'comparison_prior_state_read_seconds':round(elapsed-extraction_seconds-load_seconds,6)}
            # Validated state is visible only after COMMIT and target read-back.
            stats['boundary_completed_at']=datetime.now(timezone.utc).isoformat()
            stats['scan_apply_seconds']=round(time.perf_counter()-began,6)
            db.execute("UPDATE ingestion_meta.incremental_versions SET status='VALIDATED',evidence=%s,finished_at=clock_timestamp() WHERE version_id=%s",(Jsonb(stats),version))
            reconciliation_started=time.perf_counter();reconcile(target,version)
            reconciliation_seconds=round(time.perf_counter()-reconciliation_started,6)
            commit_attempted=True
        return {'status':'VALIDATED_UNPUBLISHED_CANDIDATE','version_id':str(version),**stats,
                'target_reconciliation_seconds':reconciliation_seconds,'total_seconds':round(time.perf_counter()-began,6)}
    except Exception as error:
        if commit_attempted:
            raise PipelineError('INCREMENTAL_COMMIT_OUTCOME_UNKNOWN_INSPECT_VERSION') from None
        code=error.code if isinstance(error,PipelineError) else 'INCREMENTAL_SOURCE_OR_TARGET_FAILURE'
        # Separate durable FAILED ledger; never overwrite a remotely committed
        # VALIDATED outcome after a lost COMMIT acknowledgement.
        try:
            db.execute("UPDATE ingestion_meta.incremental_versions SET status='FAILED',error_code=%s,evidence=%s,finished_at=clock_timestamp() WHERE version_id=%s AND status='RUNNING'",(code,Jsonb(stats),version))
        except Exception:
            raise PipelineError('INCREMENTAL_FAILURE_RECORD_UNKNOWN_INSPECT_VERSION') from None
        raise PipelineError(code) from None


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['plan','preflight','run','reconcile','inspect'])
    p.add_argument('--env-file',type=Path,default=Path('.env'))
    p.add_argument('--version-id',type=UUID)
    p.add_argument('--parent-id',type=UUID)
    p.add_argument('--batch-size',type=int,default=500)
    p.add_argument('--execute',action='store_true',help='Authorize non-admin candidate writes, never provisioning or publication')
    args=p.parse_args(argv);source=None;pg=None
    try:
        if args.command=='plan':
            print(json.dumps({'scope':SALES,'strategy':'FULL_SOURCE_SCAN_SNAPSHOT_DIFF',
                'algorithm':ALGORITHM,'source_incremental_filter':False,'delete_live':'BLOCK_UNVERIFIED',
                'ddl_executed':False,'publication':False}));return 0
        if args.command=='run' and (not args.execute or args.parent_id is None):
            raise PipelineError('EXPLICIT_EXECUTION_AND_PARENT_REQUIRED')
        if args.command in ('reconcile','inspect') and args.version_id is None:
            raise PipelineError('VERSION_ID_REQUIRED')
        config=settings(args.env_file,args.batch_size)
        pg=PostgresTarget(config);pg.connect();target=IncrementalTarget(pg)
        target.preflight()
        if args.command=='inspect':
            row=pg.connection.execute('SELECT version_id,parent_id,base_run_id,status,depth,evidence,error_code,acknowledged_publication_id FROM ingestion_meta.incremental_versions WHERE version_id=%s',(args.version_id,)).fetchone()
            if row is None:raise PipelineError('INCREMENTAL_VERSION_NOT_FOUND')
            output={'status':'INSPECT','version':list(row)}
        elif args.command=='reconcile':output={'status':'PASS','objects':reconcile(target,args.version_id)}
        else:
            source=SqlServerSource(config);source.connect();source.preflight(objects())
            if args.command=='preflight':
                if args.parent_id:assert_version(pg.connection,args.parent_id)
                output={'status':'PASS_PREFLIGHT','source':source.context,'scope':SALES}
            else:
                args.version_id=args.version_id or uuid4()
                output=run(source,target,args.version_id,args.parent_id)
        print(json.dumps(output,default=str));return 0
    except Exception as error:
        print(json.dumps({'status':'FAIL_STOP','error':error.code if isinstance(error,PipelineError) else 'CONFIGURATION_OR_DRIVER_FAILURE',
                          'version_id':str(args.version_id) if args.version_id else None}));return 1
    finally:
        close_failed=False
        for resource in (source,pg):
            if resource is not None:
                try:resource.close()
                except Exception:
                    close_failed=True
                    print(json.dumps({'status':'CLOSE_FAILED_INSPECT_VERSION','resource_type':type(resource).__name__,
                                      'version_id':str(args.version_id) if args.version_id else None}))
        if close_failed:return 1


if __name__=='__main__':raise SystemExit(main())
