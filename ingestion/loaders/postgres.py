"""Runtime never creates tables/grants. A capture's rows and publication commit atomically."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterator
from uuid import UUID, uuid4

from ingestion.common.codecs import RowDigest, admit_row
from ingestion.common.config import Settings
from ingestion.common.contracts import SourceObject, select_objects, contract_hash
from ingestion.common.errors import PipelineError


class PostgresTarget:
    def __init__(self, config: Settings):
        self.config = config
        self.connection: Any = None

    def connect(self) -> None:
        import psycopg
        c = self.config.target
        self.connection = psycopg.connect(host=c.host,port=c.port,dbname=c.database,user=c.user,password=c.password,
            sslmode=c.sslmode,connect_timeout=self.config.login_timeout,autocommit=True,
            application_name="retail_wwi_full_load", options=f"-c statement_timeout={self.config.query_timeout*1000}")
        row = self.connection.execute("SELECT current_database(),current_user,session_user").fetchone()
        if tuple(row) != ("retail_raw", "retail_ingest", "retail_ingest"):
            raise PipelineError("TARGET_IDENTITY_MISMATCH")
        flags = self.connection.execute("SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls "
                                        "FROM pg_roles WHERE rolname=current_user").fetchone()
        if flags is None or any(flags): raise PipelineError("TARGET_ADMIN_IDENTITY")

    def preflight(self, objects: tuple[SourceObject, ...]) -> None:
        privileges=self.connection.execute("SELECT has_schema_privilege(current_user,'raw','USAGE'), "
                                           "has_schema_privilege(current_user,'raw','CREATE')").fetchone()
        if tuple(privileges)!=(True,False): raise PipelineError("TARGET_SCHEMA_PRIVILEGE_MISMATCH")
        required = {"runs": ("SELECT","INSERT","UPDATE"), "object_runs": ("SELECT","INSERT","UPDATE"),
                    "load_contracts": ("SELECT","INSERT"), "load_audits": ("SELECT","INSERT"),
                    "raw_publications": ("SELECT","INSERT"), "raw_current": ("SELECT","UPDATE")}
        for table, permissions in required.items():
            for permission in permissions:
                if self.connection.execute("SELECT to_regclass(%s)", ("ingestion_meta."+table,)).fetchone()[0] is None:
                    raise PipelineError("TARGET_DDL_REQUIRED")
                if self.connection.execute("SELECT has_table_privilege(current_user,%s,%s)",
                                           ("ingestion_meta."+table,permission)).fetchone()[0] is not True:
                    raise PipelineError("TARGET_OBJECT_GRANT_REQUIRED")
        expected_meta = {
            "runs": {"run_id","capture_id","retry_of_run_id","source_system","extraction_mode","status",
                     "consistency_state","consistency_evidence_ref","started_at","finished_at","error_code"},
            "object_runs": {"run_id","source_schema","source_table","status","source_row_count","extracted_row_count",
                            "loaded_row_count","reconciliation_state","started_at","finished_at","error_code"},
            "load_contracts": {"run_id","scope","contract_hash","source_context"},
            "load_audits": {"run_id","object_name","row_count","row_digest"},
            "raw_publications": {"publication_id","run_id","previous_id","published_at"},
            "raw_current": {"singleton","publication_id"}}
        for table, names in expected_meta.items():
            owner=self.connection.execute("SELECT tableowner FROM pg_tables WHERE schemaname='ingestion_meta' AND tablename=%s",(table,)).fetchone()
            if owner is None or owner[0]!="postgres": raise PipelineError("TARGET_OWNER_MISMATCH")
            found = {r[0] for r in self.connection.execute("SELECT column_name FROM information_schema.columns "
                     "WHERE table_schema='ingestion_meta' AND table_name=%s", (table,))}
            if found != names: raise PipelineError("TARGET_METADATA_SCHEMA_MISMATCH")
            types=dict(self.connection.execute("SELECT column_name,data_type FROM information_schema.columns "
                       "WHERE table_schema='ingestion_meta' AND table_name=%s",(table,)))
            for name,kind in types.items():
                expected=("uuid" if name.endswith('_id') and name not in {'singleton'} else
                          "boolean" if name=='singleton' else "ARRAY" if name=='scope' else
                          "jsonb" if name=='source_context' else
                          "timestamp with time zone" if name.endswith('_at') else
                          "bigint" if name.endswith('_count') else "text")
                if kind!=expected: raise PipelineError("TARGET_METADATA_TYPE_MISMATCH")
        for obj in objects:
            owner=self.connection.execute("SELECT tableowner FROM pg_tables WHERE schemaname='raw' AND tablename=%s",(obj.target,)).fetchone()
            if owner is not None and owner[0]!="postgres": raise PipelineError("TARGET_OWNER_MISMATCH")
            if self.connection.execute("SELECT to_regclass(%s)",("raw."+obj.target,)).fetchone()[0] is None:
                raise PipelineError("TARGET_DDL_REQUIRED")
            actual = list(self.connection.execute("SELECT column_name,data_type,is_nullable,numeric_precision,numeric_scale,collation_name "
                "FROM information_schema.columns WHERE table_schema='raw' AND table_name=%s ORDER BY ordinal_position",(obj.target,)))
            if [r[0] for r in actual] != ["_run_id","_row_ordinal"]+[c.name for c in obj.columns]:
                raise PipelineError("TARGET_PAYLOAD_SCHEMA_MISMATCH")
            if [(r[1],r[2]) for r in actual[:2]]!=[("uuid","NO"),("bigint","NO")]:
                raise PipelineError("TARGET_PAYLOAD_IDENTITY_TYPE")
            for col, row in zip(obj.columns, actual[2:],strict=True):
                expected_type = ("numeric" if col.source_type.startswith("decimal") else
                    "text" if col.source_type.startswith(("nvarchar","datetime2")) else col.pg_type)
                if row[1] != expected_type or row[2] != ("YES" if col.nullable else "NO"):
                    raise PipelineError("TARGET_TYPE_MISMATCH")
                if col.source_type.startswith("decimal"):
                    p,s=map(int,col.source_type[8:-1].split(","))
                    if (row[3],row[4])!=(p,s): raise PipelineError("TARGET_DECIMAL_PRECISION")
                if col.source_type=="datetime2(7)" and row[5]!="C":
                    raise PipelineError("TARGET_TEMPORAL_COLLATION")
            for privilege in ("SELECT","INSERT","UPDATE","DELETE","TRUNCATE"):
                granted=self.connection.execute("SELECT has_table_privilege(current_user,%s,%s)",
                                                ("raw."+obj.target,privilege)).fetchone()[0]
                if granted != (privilege in {"SELECT","INSERT"}):
                    raise PipelineError("TARGET_PAYLOAD_PRIVILEGE_MISMATCH")

    def acquire_lock(self) -> None:
        if self.connection.execute("SELECT pg_try_advisory_lock(941061)").fetchone()[0] is not True:
            raise PipelineError("INGESTION_ALREADY_ACTIVE")

    def transaction(self) -> Any: return self.connection.transaction()

    def existing(self, run_id: UUID, objects: tuple[SourceObject, ...]) -> str | None:
        row=self.connection.execute("SELECT r.status,c.scope,c.contract_hash FROM ingestion_meta.runs r "
            "JOIN ingestion_meta.load_contracts c USING(run_id) WHERE r.run_id=%s",(run_id,)).fetchone()
        if row is None:
            if self.connection.execute("SELECT 1 FROM ingestion_meta.runs WHERE run_id=%s",(run_id,)).fetchone():
                raise PipelineError("RUN_WITHOUT_CONTRACT")
            return None
        if row[1]!=[o.name for o in objects] or row[2]!=contract_hash():
            raise PipelineError("RUN_SCOPE_OR_CONTRACT_CONFLICT")
        return row[0]

    def begin_run(self, run_id: UUID, capture_id: UUID, objects: tuple[SourceObject, ...], retry_of: UUID | None,
                  source_context: dict[str, Any]) -> None:
        from psycopg.types.json import Jsonb
        if retry_of is not None and self.existing(retry_of,objects)!="FAILED":
            raise PipelineError("RETRY_REQUIRES_FAILED_PREDECESSOR")
        with self.transaction():
            self.connection.execute("INSERT INTO ingestion_meta.runs(run_id,capture_id,retry_of_run_id,extraction_mode) "
                                    "VALUES(%s,%s,%s,'FULL')",(run_id,capture_id,retry_of))
            self.connection.execute("INSERT INTO ingestion_meta.load_contracts VALUES(%s,%s,%s,%s)",
                                    (run_id,[o.name for o in objects],contract_hash(),Jsonb(source_context)))
            for obj in objects:
                self.connection.execute("INSERT INTO ingestion_meta.object_runs(run_id,source_schema,source_table) VALUES(%s,%s,%s)",
                                        (run_id,obj.schema,obj.table))

    def start_object(self, run_id: UUID, obj: SourceObject) -> None:
        self.connection.execute("UPDATE ingestion_meta.object_runs SET status='RUNNING',started_at=clock_timestamp() "
                                "WHERE run_id=%s AND source_schema=%s AND source_table=%s",(run_id,obj.schema,obj.table))

    def write(self, obj: SourceObject, run_id: UUID, start_ordinal: int, rows: list[tuple[Any, ...]]) -> None:
        from psycopg import sql
        from psycopg.pq import TransactionStatus
        if self.connection.info.transaction_status!=TransactionStatus.INTRANS:
            raise PipelineError("PAYLOAD_TRANSACTION_REQUIRED")
        fields=["_run_id","_row_ordinal"]+[c.name for c in obj.columns]
        statement=sql.SQL("COPY {} ({}) FROM STDIN").format(sql.Identifier("raw",obj.target),
            sql.SQL(",").join(sql.Identifier(c) for c in fields))
        with self.connection.cursor() as cursor:
            with cursor.copy(statement) as copy:
                for offset,row in enumerate(rows,start_ordinal): copy.write_row((run_id,offset,*row))

    def rows(self, obj: SourceObject, run_id: UUID) -> Iterator[tuple[Any, ...]]:
        from psycopg import sql
        fields=sql.SQL(",").join(sql.Identifier(c.name) for c in obj.columns)
        # Server-side cursor: fetchmany on a normal libpq cursor would buffer the whole result.
        with self.connection.cursor(name="wwi_verify_"+uuid4().hex) as cursor:
            cursor.execute(sql.SQL("SELECT {} FROM {} WHERE _run_id=%s ORDER BY _row_ordinal").format(
                fields,sql.Identifier("raw",obj.target)),(run_id,))
            while batch:=cursor.fetchmany(obj.page_size(self.config.batch_size)):
                for row in batch: yield tuple(row)

    def finish_object(self, run_id: UUID, obj: SourceObject, count: int, digest: str) -> None:
        self.connection.execute("UPDATE ingestion_meta.object_runs SET status='SUCCEEDED',finished_at=clock_timestamp(),"
            "source_row_count=%s,extracted_row_count=%s,loaded_row_count=%s,reconciliation_state='PASS' "
            "WHERE run_id=%s AND source_schema=%s AND source_table=%s",(count,count,count,run_id,obj.schema,obj.table))
        self.connection.execute("INSERT INTO ingestion_meta.load_audits VALUES(%s,%s,%s,%s)",(run_id,obj.name,count,digest))

    def finish_run(self, run_id: UUID, evidence_ref: str | None) -> None:
        self.connection.execute("UPDATE ingestion_meta.runs SET status='SUCCEEDED',finished_at=clock_timestamp(),"
            "consistency_state=%s,consistency_evidence_ref=%s WHERE run_id=%s",
            ("VERIFIED_CONSISTENT" if evidence_ref else "UNVERIFIED",evidence_ref,run_id))

    def publish(self, run_id: UUID) -> UUID:
        from psycopg.pq import TransactionStatus
        if self.connection.info.transaction_status!=TransactionStatus.INTRANS:
            raise PipelineError("PUBLICATION_TRANSACTION_REQUIRED")
        row=self.connection.execute("SELECT consistency_state,consistency_evidence_ref FROM ingestion_meta.runs "
                                    "WHERE run_id=%s AND status='SUCCEEDED'",(run_id,)).fetchone()
        if row is None or row[0]!="VERIFIED_CONSISTENT" or not row[1]:
            raise PipelineError("SOURCE_CONSISTENCY_UNVERIFIED")
        scope=self.connection.execute("SELECT scope FROM ingestion_meta.load_contracts WHERE run_id=%s",(run_id,)).fetchone()
        if scope is None or scope[0]!=[o.name for o in select_objects()]: raise PipelineError("PARTIAL_SCOPE_CANNOT_PUBLISH")
        prior=self.connection.execute("SELECT publication_id FROM ingestion_meta.raw_current WHERE singleton FOR UPDATE").fetchone()
        if prior is None: raise PipelineError("PUBLICATION_POINTER_MISSING")
        published=self.connection.execute("SELECT publication_id FROM ingestion_meta.raw_publications WHERE run_id=%s",(run_id,)).fetchone()
        if published: return published[0]  # Never move a newer current pointer backwards on replay.
        publication_id=uuid4()
        self.connection.execute("INSERT INTO ingestion_meta.raw_publications(publication_id,run_id,previous_id) VALUES(%s,%s,%s)",
                                (publication_id,run_id,prior[0]))
        self.connection.execute("UPDATE ingestion_meta.raw_current SET publication_id=%s WHERE singleton",(publication_id,))
        return publication_id

    def fail_run(self, run_id: UUID, code: str, progress: dict[str, dict[str, Any]] | None = None) -> None:
        # Only called after an acknowledged transaction rollback, never after ambiguous commit.
        from psycopg.pq import TransactionStatus
        if self.connection.closed or self.connection.info.transaction_status!=TransactionStatus.IDLE:
            raise PipelineError("ROLLBACK_OUTCOME_UNKNOWN")
        with self.transaction():
            self.connection.execute("UPDATE ingestion_meta.object_runs SET status='FAILED',started_at=COALESCE(started_at,statement_timestamp()),"
                "finished_at=statement_timestamp(),loaded_row_count=0,error_code=%s WHERE run_id=%s",(code,run_id))
            for name,stats in (progress or {}).items():
                obj_schema,obj_table=name.split('.')
                self.connection.execute("UPDATE ingestion_meta.object_runs SET started_at=%s,source_row_count=%s,"
                    "extracted_row_count=%s WHERE run_id=%s AND source_schema=%s AND source_table=%s",
                    (stats['started_at'],stats['source_count'],stats['extracted_count'],run_id,obj_schema,obj_table))
            if code=="COUNT_OR_CONTENT_RECONCILIATION_FAILED" and progress:
                obj_schema,obj_table=next(reversed(progress)).split('.')
                self.connection.execute("UPDATE ingestion_meta.object_runs SET reconciliation_state='FAIL' "
                    "WHERE run_id=%s AND source_schema=%s AND source_table=%s",(run_id,obj_schema,obj_table))
            self.connection.execute("UPDATE ingestion_meta.runs SET status='FAILED',finished_at=clock_timestamp(),error_code=%s "
                                    "WHERE run_id=%s AND status='RUNNING'",(code,run_id))

    def reconcile(self, run_id: UUID, objects: tuple[SourceObject, ...]) -> list[dict[str, object]]:
        if self.existing(run_id,objects)!="SUCCEEDED": raise PipelineError("RUN_NOT_VALIDATED")
        result=[]
        with self.transaction():
            for obj in objects:
                expected=self.connection.execute("SELECT row_count,row_digest FROM ingestion_meta.load_audits "
                                                 "WHERE run_id=%s AND object_name=%s",(run_id,obj.name)).fetchone()
                digest=RowDigest()
                for row in self.rows(obj,run_id): digest.add(admit_row(obj,row))
                if expected is None or (digest.count,digest.hexdigest)!=tuple(expected):
                    raise PipelineError("DURABLE_RECONCILIATION_FAILED")
                result.append({"object":obj.name,"rows":digest.count,"reconciliation":"PASS"})
        return result

    def abandon(self, run_id: UUID, objects: tuple[SourceObject, ...]) -> None:
        if self.existing(run_id,objects)!="RUNNING": raise PipelineError("ONLY_RUNNING_CAN_BE_ABANDONED")
        from psycopg import sql
        for obj in objects:
            if self.connection.execute(sql.SQL("SELECT 1 FROM {} WHERE _run_id=%s LIMIT 1").format(
                    sql.Identifier("raw",obj.target)),(run_id,)).fetchone(): raise PipelineError("COMMIT_OUTCOME_UNKNOWN")
        if self.connection.execute("SELECT 1 FROM ingestion_meta.load_audits WHERE run_id=%s",(run_id,)).fetchone():
            raise PipelineError("COMMIT_OUTCOME_UNKNOWN")
        if self.connection.execute("SELECT 1 FROM ingestion_meta.raw_publications WHERE run_id=%s",(run_id,)).fetchone():
            raise PipelineError("COMMIT_OUTCOME_UNKNOWN")
        self.fail_run(run_id,"ABANDONED_AFTER_LOCK_AND_EMPTY_PAYLOAD_CHECK")

    def close(self) -> None:
        if self.connection is not None: self.connection.close()  # Releases session advisory lock.
