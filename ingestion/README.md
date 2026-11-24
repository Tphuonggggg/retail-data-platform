# Python Ingestion

## Overview

The ingestion component reads WideWorldImporters through SELECT-only SQL Server access and loads typed records into the PostgreSQL Raw Layer. It owns extraction, codecs, version metadata and reconciliation. [Infrastructure](../infrastructure/README.md) provisions schemas; [dbt](../dbt/README.md) transforms analytical data.

## Data Sources

Full Load covers 11 objects:

- `Sales.Customers`, `Orders`, `OrderLines`, `Invoices`, `InvoiceLines` and `CustomerTransactions`.
- `Warehouse.StockItems`, `StockItemHoldings` and `StockItemTransactions`.
- `Sales.Customers_Archive` and `Warehouse.StockItems_Archive`.

The nine current tables have source primary keys. Archives retain repeated natural keys and zero-duration occurrences. [Source contracts](common/contracts.py) fix ordered projections, SQL types and NULL policy. [Independent fixtures](tests/fixtures) retain the 156-column current-source dictionary and exact F2 temporal expression.

Incremental Loading operates on six inputs: Customers, Orders, OrderLines, Invoices, InvoiceLines and StockItems.

## Ingestion Architecture

Full Load initializes a candidate from source populations. Incremental Loading merges complete, ordered source and parent streams using Snapshot-Diff, writes changed payload and records lineage events. Neither path provisions schemas or advances publication pointers.

`ingestion_meta.incremental_versions` stores parent, root, depth, contract, algorithm, extraction boundary and status. Events store key/change/hash lineage. `raw.delta_*` holds payloads; `raw.sales_state_*(uuid)` resolves a version's ancestor chain. No-change extraction still creates a new Read Version.

## Full Load

Run commands from the repository root. UUID placeholders below are templates: replace them with canonical identifiers for the intended target. `load --execute` writes a new unpublished candidate and requires target/scope authorization.

```powershell
.venv\Scripts\python.exe -m ingestion.full_load --help
.venv\Scripts\python.exe -m ingestion.full_load plan --all
.venv\Scripts\python.exe -m ingestion.full_load preflight --all --env-file .env
# Writes a new unpublished candidate; run only after target/scope authorization.
.venv\Scripts\python.exe -m ingestion.full_load load --all --run-id <new-uuid> --execute --env-file .env
.venv\Scripts\python.exe -m ingestion.full_load reconcile --all --run-id <full-run-uuid> --env-file .env
```

Full Load records invocation, object status, frozen contract and reconciliation controls. `_run_id` and `_row_ordinal` identify stored occurrences; the ordinal is not a business key. Downstream dbt selects the successful Full Load run UUID, not a metadata capture UUID or an implicit latest run.

## Incremental Loading

Snapshot-Diff compares all six source snapshots with one explicit eligible parent. It is not CDC, Change Tracking or timestamp-watermark extraction.

| Classification | Storage behavior | Support boundary |
|---|---|---|
| INSERT | Typed payload and lineage event | Live source |
| UPDATE | New payload with before-version/hash lineage | Live source |
| UNCHANGED | Counters without duplicate payload/events | Live source |
| DELETE | Tombstone/state propagation | Consistent isolated fixture adapter only; live absence detection stops |

Live DELETE inference requires a coherent, complete source snapshot, which the source extraction path does not establish. Counts detect some incomplete scans but do not establish snapshot isolation.

```powershell
.venv\Scripts\python.exe -m ingestion.incremental --help
.venv\Scripts\python.exe -m ingestion.incremental plan
.venv\Scripts\python.exe -m ingestion.incremental preflight --parent-id <validated-parent-uuid>
# Writes; use a separately reviewed new version UUID.
.venv\Scripts\python.exe -m ingestion.incremental run --parent-id <validated-parent-uuid> --version-id <new-uuid> --execute
.venv\Scripts\python.exe -m ingestion.incremental inspect --version-id <version-uuid>
.venv\Scripts\python.exe -m ingestion.incremental reconcile --version-id <version-uuid>
```

Incremental payloads, events, reconciliation and the `VALIDATED` state commit together across all six objects. On failure, payload/events roll back and a separate `FAILED` ledger entry records the failure.

## Data Contracts

| Source value | Raw Layer representation |
|---|---|
| Decimal | Exact Decimal/numeric, without float coercion |
| NULL / empty text | Distinct values |
| Unicode | Preserved text |
| Binary / geography | Native bytes; geography bytes are not represented as WKB |
| `datetime2(7)` | Exact F2 27-character text or NULL, stored as `TEXT COLLATE "C"` |

Python datetime and PostgreSQL microsecond timestamps are not authoritative representations of the source's 100-nanosecond identity. Source system-time is distinct from business-effective time; exact storage does not provide complete historical SCD Type 2 coverage. Target DDL follows the frozen contract rather than inferred sample types.

## Versioning and Idempotency

A matching successful UUID returns `ALREADY_VALIDATED_NO_REEXTRACTION` and reconciles durable state. Reusing the identity with a different parent, contract or algorithm is rejected. `FAILED`/`RUNNING` identities cannot be overwritten; fresh extraction uses a new UUID. Full Load retries also use a fresh run identity with the supported retry linkage instead of truncating sealed chunks.

The maximum incremental chain depth is 32; compaction is not implemented. `VALIDATED` and `SUCCEEDED` describe candidate state. They do not advance `raw_current`, source checkpoints or publication ACK; `acknowledged_publication_id` remains NULL in this workflow.

## Data Reconciliation

Source-to-Raw checks compare extracted/loaded counts, current-table distinct keys, numeric totals, NULL controls and ordered typed content digests. Zero and unknown NULL remain different. Successful version reuse includes durable read-back rather than relying only on a prior status value.

## Running the Pipeline

Use `plan` to inspect scope, then `preflight` to validate the selected objects and target identity/schema/privileges. History INSERT permission is not a global source prerequisite. Follow with the explicitly authorized load/run and reconciliation commands above, checking every exit code.

For offline regression, syntax and repository links:

```powershell
.venv\Scripts\python.exe scripts/run_checks.py --portable
```

[Integration fixtures](../tests/integration) have separate `--execute` scopes and are not routine read-only checks.

## Sample Demo

[demo.py](demo.py) uses authored synthetic rows, the production comparator/codecs and an isolated upsert adapter. It uses neither live parent/version identifiers nor production metadata. The independent [dbt demo project](../dbt/demo/dbt_project.yml) contains two models and seven data tests.

```powershell
.venv\Scripts\python.exe -m ingestion.demo config
.venv\Scripts\python.exe -m ingestion.demo run
.venv\Scripts\python.exe -m ingestion.demo run
.venv\Scripts\python.exe -m ingestion.demo down
```

The sequence loads two rows, repeats an unchanged snapshot, injects a pre-COMMIT failure, verifies rollback, then applies one UPDATE and one INSERT. Count/digest read-back includes Unicode, NULL versus empty text and seven-digit temporal text. Expected final output:

| Sales date | Sales | Units |
|---|---:|---:|
| 2024-01-01 | 45.00 | 6 |
| 2024-01-02 | 10.00 | 1 |

A completed rerun verifies the three-row state and reports three UNCHANGED rows. Unexpected state and DELETE are rejected rather than silently reset. Results, logs and generated credentials stay in ignored `.local/portfolio-demo`. `down` removes only demo resources and discards tmpfs data. See [environment isolation](../infrastructure/README.md#demo-environment).

### PostgreSQL integration in CI

The independent `demo-integration` GitHub Actions job runs the demo twice against the same isolated PostgreSQL state. [Integration verification](tests/demo_integration.py) requires the exact initial/no-change/recovery counts, an observed rollback, three UNCHANGED rows on rerun, exact SQL read-back and the daily output above. Each run must complete both demo models and all seven data tests under a fresh dbt invocation. Missing, failed or skipped results stop the job.

To reproduce the integration checks from the repository root:

```powershell
.venv\Scripts\python.exe -m ingestion.demo config
.venv\Scripts\python.exe -m ingestion.demo run
.venv\Scripts\python.exe -m ingestion.tests.demo_integration initial
.venv\Scripts\python.exe -m ingestion.demo run
.venv\Scripts\python.exe -m ingestion.tests.demo_integration rerun
# Run cleanup even if an earlier command fails.
.venv\Scripts\python.exe -m ingestion.demo down
.venv\Scripts\python.exe -m ingestion.tests.demo_integration cleanup
```

Start with no existing demo container or occupied demo port; initial verification rejects a completed-state rerun in place of initialization. Inspect existing demo resources before stopping them. CI uses an `always()` cleanup step and fails visibly if teardown fails or project-labeled containers/networks remain. No repository secrets, production profiles or data dumps are required or uploaded. The integration scope is the synthetic demo, not the WideWorldImporters pipeline.

## Performance Characteristics

Snapshot-Diff saves payload writes when few rows change, but still reads source and parent populations. The comparator merges ordered streams; unchanged data is still examined.

```powershell
.venv\Scripts\python.exe -m ingestion.benchmark --rows 10000 --repeats 3 --seed 20261123
```

[benchmark.py](benchmark.py) measures in-memory fixtures, not database throughput. The baseline contains 10,000 seven-column rows, with seed 20261123 and 0%, 1% or 10% changes relative to baseline. Changed rows split between INSERT and UPDATE, with an odd remainder assigned to UPDATE. INSERTs increase source size to 10,050 or 10,500 rows; UPDATEs add exactly Decimal 0.01. Each scenario uses one warm-up and three measured repetitions, checking counts, classifications and reconstructed digests.

A reference experiment on 23 November 2026 used Windows 11 build 26300, Python 3.12.10 and Intel64 Family 6 Model 154. Tracemalloc was enabled throughout the timed phases:

| Delta / baseline | Examined | INSERT / UPDATE / UNCHANGED | Extract / compare / load median (s) | Total median [min–max] (s) | Rows/s median | Peak traced MiB |
|---|---:|---|---|---|---:|---:|
| 0% | 10,000 | 0 / 0 / 10000 | 0.0255 / 3.4653 / 0.0008 | 3.4972 [3.0286–3.5595] | 2859 | 5.63 |
| 1% | 10,050 | 50 / 50 / 9950 | 0.0262 / 3.8134 / 0.0007 | 3.8403 [3.8087–4.2032] | 2617 | 5.65 |
| 10% | 10,500 | 500 / 500 / 9500 | 0.0271 / 3.9800 / 0.0011 | 4.0194 [3.9967–4.1353] | 2612 | 5.82 |

Extraction copies tuples in RAM; comparison performs typed admission and merge; loading applies deltas to a dictionary. Fixture/parent preparation and digest verification are outside the timing. Total measures the three phases; throughput is examined source rows divided by total. Phase medians need not sum to the total median.

The harness materializes rows and changes to separate phases, so peak traced allocations do not represent streaming production memory. Peak excludes earlier fixture/parent allocations and is not RSS. Other validation/demo work ran on the same machine during the experiment. Raw repetitions, min/max, standard deviation and environment details are written to ignored `.local/portfolio-benchmark/result.json`. Network, COPY, transactions and fsync are not measured; these results cannot establish production speed or justify index/thread changes.

## Error Handling and Recovery

| Symptom | Next step |
|---|---|
| Authentication, TLS or source permission failure | Check the intended identity/configuration; retain source grants and certificate settings |
| PostgreSQL timeout | Inspect Engine, existing container, loopback port and health; retain the volume |
| Missing target objects | Review provisioning inventory rather than creating schemas through ingestion |
| Contract/digest mismatch | Preserve private diagnostics and investigate the discrepancy |
| Failed, running or uncertain version | Inspect durable ledger/state and active Windows children before choosing a recovery identity |

For unknown COMMIT or timeout, reconcile durable state before retrying: a failed client acknowledgment does not imply rollback. Cooperating ingestion uses advisory lock 941061; dbt uses 941062. These locks do not create source snapshot consistency. See [Airflow recovery](../airflow/README.md#retry-and-recovery).

## Configuration

Install the pinned [requirements](../requirements.txt) in Windows Python 3.12 with ODBC Driver 18. [.env.example](../.env.example) defines `WWI_SQLSERVER_*`, `RAW_PG_*`, batch size and timeout settings. The target is `127.0.0.1:55434/retail_raw` as `retail_ingest`; administrative credentials belong to provisioning only.

Windows Authentication uses the current development account. Source configuration validates machine, principal, instance and database; porting requires reviewing these guards, not just changing a hostname. TLS defaults to `Encrypt=yes`, `TrustServerCertificate=no`. Explicit trust/admin development opt-ins require `APP_ENV=development` and separate authorization; there is no fallback credential. Keep `.env`, credentials, extracts and private diagnostics outside Git.

## Known Limitations

Source consistency across tables is unproven, live DELETE detection is blocked and Snapshot-Diff scans complete populations. Chain compaction, complete historical SCD Type 2 lookup and Certified publication remain future scope. The demo exercises comparator/codecs and an isolated adapter rather than the complete SQL Server/production metadata path.
