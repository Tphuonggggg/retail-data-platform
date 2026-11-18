"""Generate explicit owner-reviewed target DDL; never execute it in ingestion."""
from __future__ import annotations

from ingestion.common.contracts import select_objects, pg_quote


def full_load_ddl() -> str:
    parts = ["-- WWI-06A owner-reviewed initialization proposal. NOT EXECUTED by the loader.",
             "-- Only retail_raw; normal runtime stays retail_ingest. No role creation or source DDL.",
             "\\set ON_ERROR_STOP on", "BEGIN;",
             "DO $$ BEGIN IF current_database() <> 'retail_raw' OR current_user <> 'postgres' "
             "THEN RAISE EXCEPTION 'Wrong initialization context'; END IF; END $$;",
             "CREATE TABLE ingestion_meta.load_contracts (run_id uuid PRIMARY KEY REFERENCES ingestion_meta.runs(run_id), "
             "scope text[] NOT NULL, contract_hash text NOT NULL CHECK (contract_hash ~ '^[0-9a-f]{64}$'), "
             "source_context jsonb NOT NULL);",
             "CREATE TABLE ingestion_meta.load_audits (run_id uuid NOT NULL REFERENCES ingestion_meta.load_contracts(run_id), "
             "object_name text NOT NULL, row_count bigint NOT NULL CHECK(row_count>=0), row_digest text NOT NULL "
             "CHECK(row_digest ~ '^[0-9a-f]{64}$'), PRIMARY KEY(run_id,object_name));",
             "CREATE TABLE ingestion_meta.raw_publications (publication_id uuid PRIMARY KEY, "
             "run_id uuid NOT NULL UNIQUE REFERENCES ingestion_meta.load_contracts(run_id), "
             "previous_id uuid REFERENCES ingestion_meta.raw_publications(publication_id), "
             "published_at timestamptz NOT NULL DEFAULT clock_timestamp());",
             "CREATE TABLE ingestion_meta.raw_current (singleton boolean PRIMARY KEY CHECK(singleton), "
             "publication_id uuid REFERENCES ingestion_meta.raw_publications(publication_id));",
             "INSERT INTO ingestion_meta.raw_current(singleton,publication_id) VALUES (true,NULL);",
             "GRANT SELECT,INSERT ON ingestion_meta.load_contracts,ingestion_meta.load_audits,"
             "ingestion_meta.raw_publications TO retail_ingest;",
             "GRANT SELECT,UPDATE ON ingestion_meta.raw_current TO retail_ingest;"]
    for obj in select_objects():
        columns = ["_run_id uuid NOT NULL REFERENCES ingestion_meta.runs(run_id)", "_row_ordinal bigint NOT NULL CHECK(_row_ordinal>0)"]
        for col in obj.columns:
            definition = pg_quote(col.name) + " " + col.pg_type + ("" if col.nullable else " NOT NULL")
            if col.source_type == "datetime2(7)":
                definition += " CHECK(" + pg_quote(col.name) + " IS NULL OR " + pg_quote(col.name) + " ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\\.[0-9]{7}$')"
            columns.append(definition)
        columns.append("PRIMARY KEY(_run_id,_row_ordinal)")
        if obj.primary_key: columns.append("UNIQUE(_run_id," + pg_quote(obj.primary_key) + ")")
        parts.append("CREATE TABLE " + obj.pg_table + " (\n  " + ",\n  ".join(columns) + "\n);")
        parts.append("GRANT SELECT,INSERT ON " + obj.pg_table + " TO retail_ingest;")
        fields = ",".join("p." + pg_quote(c.name) for c in obj.columns)
        parts.append("CREATE VIEW raw." + pg_quote("current_" + obj.target) + " AS SELECT p._run_id,p._row_ordinal," + fields
            + " FROM " + obj.pg_table + " p JOIN ingestion_meta.raw_publications u ON u.run_id=p._run_id "
              "JOIN ingestion_meta.raw_current c ON c.publication_id=u.publication_id WHERE c.singleton;")
        parts.append("GRANT SELECT ON raw." + pg_quote("current_" + obj.target) + " TO retail_ingest;")
    parts.append("COMMIT;")
    return "\n\n".join(parts) + "\n"
