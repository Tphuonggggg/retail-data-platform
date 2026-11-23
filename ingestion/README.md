# Python Ingestion

This module owns SELECT-only extraction from WideWorldImporters, typed PostgreSQL Raw loading, immutable version metadata and reconciliation. It does not provision schemas, transform analytical models or publish candidates. See the [project overview](../README.md) and [infrastructure setup](../infrastructure/README.md).

## Source and Configuration

[Contracts](common/contracts.py) freeze ordered projections, SQL types, NULL policy and the exact F2 temporal formatting expression. Full Load covers:

- `Sales.Customers`, `Orders`, `OrderLines`, `Invoices`, `InvoiceLines`, `CustomerTransactions`.
- `Warehouse.StockItems`, `StockItemHoldings`, `StockItemTransactions`.
- `Sales.Customers_Archive`, `Warehouse.StockItems_Archive`.

Nine current tables have source primary keys. Archives preserve repeated natural keys and zero-duration occurrences. Independent fixtures in [tests/fixtures](tests/fixtures) retain the 156-column current-source dictionary and verified F2 expression.

Use Windows Python and ODBC Driver 18 with current-principal Windows Authentication. [.env.example](../.env.example) documents `WWI_SQLSERVER_*`, batch/timeouts and `RAW_PG_*` settings. The implementation validates the reviewed local machine/instance/database; changing the hostname alone does not port those guards. `Encrypt=yes` and `TrustServerCertificate=no` are defaults. Approved development-only trust/admin opt-ins require `APP_ENV=development`; they are not production defaults or credential fallbacks. Keep real `.env` and passwords outside Git.

The normal target is `127.0.0.1:55434/retail_raw` as `retail_ingest`. Administrative credentials are for separately reviewed provisioning, not extraction.

## Full Load

Run from the repository root. Commands containing `<...>` require actual reviewed values; they are templates, not copy-and-run defaults.

```powershell
.venv\Scripts\python.exe -m ingestion.full_load --help
.venv\Scripts\python.exe -m ingestion.full_load plan --all
.venv\Scripts\python.exe -m ingestion.full_load preflight --all --env-file .env
# Writes a new unpublished candidate; run only after target/scope authorization.
.venv\Scripts\python.exe -m ingestion.full_load load --all --run-id <new-uuid> --execute --env-file .env
.venv\Scripts\python.exe -m ingestion.full_load reconcile --all --run-id <full-run-uuid> --env-file .env
```

Check each exit code. Full Load records invocation, object status, frozen contract and audits. Reconciliation compares source/extracted/loaded counts, current-table distinct keys, numeric totals, NULL controls and typed content digests. Known zero and unknown NULL remain different. `_run_id` and `_row_ordinal` identify stored occurrences; ordinal is not a business key. Select the Full Load **run UUID** for downstream dbt, not an unrelated metadata capture UUID or an implicit latest run.

## Incremental Snapshot Diff

The six inputs are Customers, Orders, OrderLines, Invoices, InvoiceLines and StockItems. Every run scans their complete snapshots and compares the result with an explicit eligible parent. It is not CDC, Change Tracking or timestamp-watermark extraction.

| Change | Target behavior | Runtime boundary |
|---|---|---|
| INSERT | Typed delta payload and event | Live supported |
| UPDATE | New typed payload, before-version/hash lineage and event | Live supported |
| UNCHANGED | Counters; no duplicate payload/event | Live supported |
| DELETE | Tombstone/state propagation in consistent fixture adapter | Live absence stops; source snapshot consistency is unproven |

```powershell
.venv\Scripts\python.exe -m ingestion.incremental --help
.venv\Scripts\python.exe -m ingestion.incremental plan
.venv\Scripts\python.exe -m ingestion.incremental preflight --parent-id <validated-parent-uuid>
# Writes; use a separately reviewed new version UUID.
.venv\Scripts\python.exe -m ingestion.incremental run --parent-id <validated-parent-uuid> --version-id <new-uuid> --execute
.venv\Scripts\python.exe -m ingestion.incremental inspect --version-id <version-uuid>
.venv\Scripts\python.exe -m ingestion.incremental reconcile --version-id <version-uuid>
```

`ingestion_meta.incremental_versions` records parent/root/depth, contract, algorithm, boundary and status; events record key/change/hash lineage. `raw.delta_*` stores payloads and `raw.sales_state_*(uuid)` resolves the ancestor chain. Maximum chain depth is 32; compaction is not implemented. A no-change run still creates a new validated read version.

## Data Contracts

- Preserve Decimal without float coercion, Unicode, binary/geography bytes, NULL and empty strings. Native geography bytes are not advertised as WKB.
- Preserve source `datetime2(7)` as the verified F2 27-character string or `None`, stored as `TEXT COLLATE "C"`. Do not use Python datetime or PostgreSQL microsecond timestamps as authoritative source identity.
- Source system-time is distinct from business-effective time. Exact representation does not prove complete historical SCD2 coverage.
- Freeze schema/projection rather than inferring target DDL from sampled values.

## Transactions, Idempotency and Recovery

Incremental payloads, events, reconciliation and VALIDATED state commit together across all six objects. On failure, payload/events roll back and a FAILED ledger entry is recorded separately. Guards protect terminal states.

A matching successful UUID returns `ALREADY_VALIDATED_NO_REEXTRACTION` and reconciles stored state. Parent/contract/algorithm changes are rejected. FAILED/RUNNING UUIDs cannot be overwritten; a fresh extraction requires a new UUID. Full Load retries also use a fresh run identity with the supported retry linkage, rather than truncating or replaying sealed chunks. Inspect subcommand help before retrying.

For unknown COMMIT or timeout: inspect the durable ledger, read back data and check active Windows processes/locks before retry. Do not infer rollback from a failed client acknowledgment. Cooperating ingestion uses advisory lock 941061; dbt uses 941062. These locks do not establish a coherent SQL Server source snapshot.

`VALIDATED`/`SUCCEEDED` is candidate progress. It does not advance `raw_current`, a source checkpoint or publication ACK. `acknowledged_publication_id` remains NULL for the current workflow. See [dbt version selection](../dbt/README.md) and [Airflow recovery](../airflow/README.md).

## Checks and Troubleshooting

Run `.venv\Scripts\python.exe scripts/run_checks.py` for offline regression, syntax, links and repository checks. Integration fixtures under [tests/integration](../tests/integration) require their own reviewed `--execute` scope and are not routine operational commands.

| Symptom | Safe next step |
|---|---|
| Source authentication/TLS/permission error | Verify approved identity, instance and configuration; stop rather than changing source grants/certificates |
| PostgreSQL timeout | Check Docker Engine, existing container, loopback binding and health; retain the volume |
| Missing target objects | Review provisioning inventory/target; ingestion must not create schemas automatically |
| Contract/digest mismatch | Keep private evidence and stop; do not relax rules to pass |
| FAILED/RUNNING/uncertain version | Inspect durable state and active child processes before selecting recovery identity |
