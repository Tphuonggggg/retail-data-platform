-- PREPARED, NOT EXECUTED. Only the new isolated retail-raw Compose database.
-- psql input: credentials come from container environment, never SQL literals.
\set ON_ERROR_STOP on
\getenv ingest_password RAW_PG_INGEST_PASSWORD
SELECT current_database() = 'retail_raw' AND current_user = 'postgres' AS correct_target \gset
\if :correct_target
\else
    \echo 'STOP: bootstrap requires the isolated retail_raw database and postgres owner.'
    \quit 1
\endif
SELECT length(:'ingest_password') >= 16
   AND :'ingest_password' !~* '^(CHANGE_ME|YOUR_|example)' AS usable_password \gset
\if :usable_password
\else
    \echo 'STOP: provide a private ingestion password of at least 16 characters.'
    \quit 1
\endif

BEGIN;
SELECT format('CREATE ROLE retail_ingest LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD %L', :'ingest_password') \gexec
\unset ingest_password
REVOKE ALL ON DATABASE retail_raw FROM PUBLIC;
GRANT CONNECT ON DATABASE retail_raw TO retail_ingest;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

CREATE SCHEMA raw AUTHORIZATION postgres;
CREATE SCHEMA ingestion_meta AUTHORIZATION postgres;
GRANT USAGE ON SCHEMA raw, ingestion_meta TO retail_ingest;

-- Invocation tracking only: these are NOT capture/batch/publication manifests.
CREATE TABLE ingestion_meta.runs (
    run_id uuid PRIMARY KEY,
    capture_id uuid NOT NULL,
    retry_of_run_id uuid REFERENCES ingestion_meta.runs(run_id),
    source_system text NOT NULL DEFAULT 'WWI' CHECK (source_system = 'WWI'),
    extraction_mode text NOT NULL CHECK (extraction_mode IN ('FULL', 'INCREMENTAL', 'BACKFILL')),
    status text NOT NULL DEFAULT 'RUNNING' CHECK (status IN ('RUNNING', 'SUCCEEDED', 'FAILED')),
    consistency_state text NOT NULL DEFAULT 'UNVERIFIED'
        CHECK (consistency_state IN ('UNVERIFIED', 'VERIFIED_CONSISTENT')),
    consistency_evidence_ref text,
    started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    finished_at timestamptz,
    error_code text,
    CHECK (retry_of_run_id IS NULL OR retry_of_run_id <> run_id),
    CHECK (finished_at IS NULL OR finished_at >= started_at),
    CHECK ((status = 'RUNNING' AND finished_at IS NULL)
        OR (status IN ('SUCCEEDED', 'FAILED') AND finished_at IS NOT NULL)),
    CHECK (consistency_state <> 'VERIFIED_CONSISTENT'
        OR NULLIF(btrim(consistency_evidence_ref), '') IS NOT NULL)
);

CREATE TABLE ingestion_meta.object_runs (
    run_id uuid NOT NULL REFERENCES ingestion_meta.runs(run_id),
    source_schema text NOT NULL,
    source_table text NOT NULL,
    status text NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED')),
    source_row_count bigint CHECK (source_row_count >= 0),
    extracted_row_count bigint CHECK (extracted_row_count >= 0),
    loaded_row_count bigint CHECK (loaded_row_count >= 0),
    reconciliation_state text NOT NULL DEFAULT 'NOT_RUN'
        CHECK (reconciliation_state IN ('NOT_RUN', 'PASS', 'FAIL')),
    started_at timestamptz,
    finished_at timestamptz,
    error_code text,
    PRIMARY KEY (run_id, source_schema, source_table),
    CHECK ((source_schema, source_table) IN (
        ('Sales', 'Customers'), ('Sales', 'Orders'), ('Sales', 'OrderLines'),
        ('Sales', 'Invoices'), ('Sales', 'InvoiceLines'), ('Sales', 'CustomerTransactions'),
        ('Warehouse', 'StockItems'), ('Warehouse', 'StockItemHoldings'),
        ('Warehouse', 'StockItemTransactions'), ('Sales', 'Customers_Archive'),
        ('Warehouse', 'StockItems_Archive')
    )),
    CHECK ((status = 'PENDING' AND started_at IS NULL AND finished_at IS NULL)
        OR (status = 'RUNNING' AND started_at IS NOT NULL AND finished_at IS NULL)
        OR (status IN ('SUCCEEDED', 'FAILED') AND started_at IS NOT NULL
            AND finished_at IS NOT NULL AND finished_at >= started_at)),
    CHECK (reconciliation_state <> 'PASS' OR (
        source_row_count IS NOT NULL AND extracted_row_count IS NOT NULL
        AND loaded_row_count IS NOT NULL
        AND source_row_count = extracted_row_count AND extracted_row_count = loaded_row_count
    )),
    CHECK (status <> 'SUCCEEDED' OR reconciliation_state = 'PASS')
);

GRANT SELECT, INSERT, UPDATE ON ingestion_meta.runs, ingestion_meta.object_runs TO retail_ingest;
-- No Raw payload DDL, ingestion, publication, checkpoints or destructive reset.
-- No DELETE/TRUNCATE/schema-CREATE privilege for the normal ingestion role.
COMMIT;
