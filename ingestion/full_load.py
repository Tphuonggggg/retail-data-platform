"""WWI-06A Full Load CLI. Config/plan/DDL are offline; no import-time execution."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any, Callable
from uuid import UUID, uuid4

from ingestion.common.codecs import RowDigest, admit_row
from ingestion.common.config import settings
from ingestion.common.contracts import SourceObject, catalog, select_objects, contract_hash
from ingestion.common.errors import PipelineError
from ingestion.common.evidence import SourceEvidence
from ingestion.extractors.sqlserver import SqlServerSource
from ingestion.loaders.postgres import PostgresTarget
from ingestion.loaders.schema import full_load_ddl


def utc_now() -> datetime: return datetime.now(timezone.utc)


def run_full_load(source: Any, target: Any, objects: tuple[SourceObject, ...], *,
                  run_id: UUID | None = None, retry_of: UUID | None = None,
                  evidence: SourceEvidence | None = None, publish: bool = False,
                  clock: Callable[[], datetime] = utc_now) -> dict[str, object]:
    if not objects or any(catalog().get(obj.name)!=obj for obj in objects):
        raise PipelineError("SOURCE_NOT_ALLOWLISTED")
    if publish and (tuple(objects)!=select_objects() or evidence is None):
        raise PipelineError("FULL_SCOPE_AND_CONSISTENCY_REQUIRED")
    run_id = run_id or uuid4()
    target.preflight(objects); target.acquire_lock()
    previous = target.existing(run_id,objects)
    if previous == "SUCCEEDED":
        return {"status":"ALREADY_VALIDATED_NO_RELOAD","run_id":str(run_id),
                "objects":target.reconcile(run_id,objects),"publication_changed":False}
    if previous is not None: raise PipelineError("RUN_ID_REUSE_REQUIRES_INSPECTION")
    source.connect(); source.preflight(objects)  # No metadata writes on TLS/identity/schema/permission failure.
    start=clock(); started=time.monotonic()
    try:
        target.begin_run(run_id,uuid4(),objects,retry_of,getattr(source,'context',{'kind':'OFFLINE_FIXTURE_ONLY'}))
    except PipelineError:
        raise
    except Exception:
        # The small registration transaction may have committed before its ACK
        # was lost. There is no capture rollback to acknowledge at this point.
        raise PipelineError("RUN_REGISTRATION_OUTCOME_UNKNOWN_INSPECT_RUN_ID") from None
    body_complete=False
    results=[]; publication_id=None; progress={}
    try:
        with target.transaction():
            for obj in objects:
                progress[obj.name]={"started_at":clock(),"source_count":None,"extracted_count":0}
                target.start_object(run_id,obj)
                expected=source.count(obj)
                if expected < 0: raise PipelineError("INVALID_SOURCE_COUNT")
                progress[obj.name]["source_count"]=expected
                digest=RowDigest(); last_key=None
                key_index=next((i for i,c in enumerate(obj.columns) if c.name==obj.primary_key),None)
                for batch in source.batches(obj):
                    if not batch: continue
                    progress[obj.name]["extracted_count"]+=len(batch)
                    admitted=[]
                    for row in batch:
                        values=admit_row(obj,row)
                        if key_index is not None:
                            key=values[key_index]
                            if last_key is not None and key<=last_key: raise PipelineError("SOURCE_KEY_DUPLICATE_OR_ORDER")
                            last_key=key
                        digest.add(values); admitted.append(values)
                    target.write(obj,run_id,digest.count-len(admitted)+1,admitted)
                after=source.count(obj)
                loaded=RowDigest()
                for row in target.rows(obj,run_id): loaded.add(admit_row(obj,row))
                if expected!=after or expected!=digest.count or (loaded.count,loaded.hexdigest)!=(digest.count,digest.hexdigest):
                    raise PipelineError("COUNT_OR_CONTENT_RECONCILIATION_FAILED")
                target.finish_object(run_id,obj,digest.count,digest.hexdigest)
                results.append({"object":obj.name,"source_rows":expected,"extracted_rows":digest.count,
                                "loaded_rows":loaded.count,"reconciliation":"PASS"})
            end=clock()
            if evidence is not None: evidence.validate(start,end,objects,publish=publish)
            target.finish_run(run_id,evidence.reference if evidence else None)
            if publish: publication_id=target.publish(run_id)
            body_complete=True
    except Exception as error:
        if body_complete: raise PipelineError("COMMIT_OUTCOME_UNKNOWN_INSPECT_RUN_ID") from None
        code=error.code if isinstance(error,PipelineError) else "EXTRACTION_OR_LOAD_FAILED"
        try: target.fail_run(run_id,code,progress)
        except Exception: raise PipelineError("ROLLBACK_OR_METADATA_OUTCOME_UNKNOWN_INSPECT_RUN_ID") from None
        raise PipelineError(code) from None
    return {"status":"RAW_PUBLISHED" if publish else "VALIDATED_UNPUBLISHED_CANDIDATE",
            "run_id":str(run_id),"publication_id":str(publication_id) if publication_id else None,
            "source_consistency":"VERIFIED_EXTERNAL_WINDOW" if evidence else "UNVERIFIED",
            "duration_seconds":round(time.monotonic()-started,3),"objects":results}


def parser() -> argparse.ArgumentParser:
    result=argparse.ArgumentParser(description=__doc__)
    result.add_argument("command",choices=("config","plan","ddl","connectivity","preflight","load","reconcile","abandon"))
    result.add_argument("--env-file",type=Path)
    scope=result.add_mutually_exclusive_group()
    scope.add_argument("--object",action="append",dest="objects")
    scope.add_argument("--all",action="store_true")
    result.add_argument("--batch-size",type=int)
    result.add_argument("--run-id",type=UUID)
    result.add_argument("--retry-of",type=UUID)
    result.add_argument("--consistency-evidence",type=Path)
    result.add_argument("--publish",action="store_true")
    result.add_argument("--execute",action="store_true",help="Explicit target-write authorization for load/abandon")
    return result


def main(argv: list[str] | None = None) -> int:
    args=parser().parse_args(argv)
    source=None; target=None
    try:
        objects=select_objects(args.objects)
        if args.command=="ddl":
            print(full_load_ddl()); return 0
        if args.command=="plan":
            print(json.dumps({"status":"OFFLINE_PLAN","scope":[o.name for o in objects],
                "contract_hash":contract_hash(),"source_selects":[o.query for o in objects],"executed":False}));return 0
        if args.command in {"load","abandon"} and not args.execute:
            raise PipelineError("EXPLICIT_EXECUTION_FLAG_REQUIRED")
        if args.command in {"reconcile","abandon"} and args.run_id is None:
            raise PipelineError("RUN_ID_REQUIRED")
        # Allocate the CLI id before any connection: an unknown COMMIT outcome must
        # still identify the run even when the caller omitted --run-id.
        if args.command=="load" and args.run_id is None:
            args.run_id=uuid4()
        config=settings(args.env_file,args.batch_size)
        if args.command=="config": print(json.dumps(config.summary())); return 0
        from importlib.util import find_spec
        if any(find_spec(name) is None for name in ("pyodbc", "psycopg")):
            raise PipelineError("MISSING_RUNTIME_DEPENDENCY_INSTALL_ROOT_REQUIREMENTS")
        target=PostgresTarget(config); target.connect()
        if args.command in {"reconcile","abandon"}:
            target.preflight(objects)
            if args.command=="abandon":
                target.acquire_lock();target.abandon(args.run_id,objects)
                output={"status":"ABANDONED_FAILED_RUN","run_id":str(args.run_id)}
            else: output={"run_id":str(args.run_id),"objects":target.reconcile(args.run_id,objects)}
        else:
            source=SqlServerSource(config)
            if args.command=="load":
                evidence=SourceEvidence.read(args.consistency_evidence) if args.consistency_evidence else None
                output=run_full_load(source,target,objects,run_id=args.run_id,retry_of=args.retry_of,
                                     evidence=evidence,publish=args.publish)
            else:
                source.connect(); source.preflight(objects)
                if args.command=="preflight": target.preflight(objects)
                output={"status":"PASS_READONLY_PREFLIGHT","source_and_target_connected":True,
                        "target_payload_checked":args.command=="preflight","full_load_executed":False}
        print(json.dumps(output));return 0
    except Exception as error:
        # Never print str(error), repr(connection) or traceback: drivers may include secrets/PII.
        output={"status":"FAIL_STOP","error_category":error.code if isinstance(error,PipelineError)
            else "CONFIGURATION_OR_DRIVER_FAILURE","error_type":type(error).__name__}
        if args.run_id is not None: output["run_id"]=str(args.run_id)
        print(json.dumps(output));return 1
    finally:
        close_failed=False
        for resource in (source,target):
            if resource is not None:
                try: resource.close()
                except Exception:
                    close_failed=True
                    print(json.dumps({"status":"CLOSE_FAILED_INSPECT_RUN_NO_RETRY","resource_type":type(resource).__name__,
                                      "run_id":str(args.run_id) if args.run_id else None}))
        if close_failed: return 1


if __name__=="__main__": raise SystemExit(main())
