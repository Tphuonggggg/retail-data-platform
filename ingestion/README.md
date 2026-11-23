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

## Portfolio Demo

```powershell
.venv\Scripts\python.exe -m ingestion.demo config
.venv\Scripts\python.exe -m ingestion.demo run
.venv\Scripts\python.exe -m ingestion.demo run
.venv\Scripts\python.exe -m ingestion.demo down
```

Entrypoint [demo.py](demo.py) dùng fixture tự tạo (không lấy WWI), production `compare`, typed codecs và count/digest. Adapter upsert riêng chỉ cho database demo; không đổi source adapter hoặc metadata production. Không dùng parent/version UUID live. Một transaction chứa delta và read-back; failure chủ động trước COMMIT phải rollback, sau đó retry fixture an toàn.

Lượt chạy cô lập ngày 23/11/2026: initial INSERT=2; no-change UNCHANGED=2; thử lỗi rollback giữ digest cũ; recovery UPDATE=1/INSERT=1/UNCHANGED=1. dbt build hai models và bảy data tests PASS. Kết quả cuối: 2024-01-01 Sales=45.00, units=6; 2024-01-02 Sales=10.00, units=1. Unicode `Cà phê`, NULL so với chuỗi rỗng và F2 7 chữ số đi qua read-back digest. Chạy lại toàn entrypoint trên demo đã xong kiểm tra digest và trả ba UNCHANGED. State bất ngờ hoặc DELETE bị từ chối; không reset ngầm.

Kết quả/logs/profile/credentials nằm trong `.local/portfolio-demo`, được ignore. Demo cần Docker Engine Linux và các package từ requirements.txt; không cần ODBC server hay private `.env`. `down` chỉ tác động project demo và mất dữ liệu tmpfs; không xóa named volumes. Xem [isolation và teardown](../infrastructure/README.md#isolated-portfolio-demo). Đây là isolated local runtime PASS, chưa phải clean-machine full-stack validation.

## Snapshot-Diff Fixture Benchmark

```powershell
.venv\Scripts\python.exe -m ingestion.benchmark --rows 10000 --repeats 3 --seed 20261123
```

Harness [benchmark.py](benchmark.py) gọi nguyên `ingestion.incremental.compare` với contract fixture bảy cột. Baseline 10,000 rows; delta tính theo baseline, chia đều INSERT/UPDATE (odd count nghiêng UPDATE). Không DELETE. Vì INSERT thêm dòng nên source sau thay đổi có 10,000/10,050/10,500 rows. UPDATE tăng chính xác Decimal 0.01; seed ổn định. Mỗi scenario warm-up một lần rồi đo ba lần với cùng instrumentation; kiểm tra count/change mix/digest sau mỗi lần.

**Đo thật ngày 23/11/2026, in-memory fixture, không phải database benchmark:** Windows 11 build 26300, Python 3.12.10, Intel64 Family 6 Model 154. Tracemalloc bật trong mọi phase. Extract=copy tuples trong RAM; compare=typed admission và merge; load=apply delta vào dict; không có network/COPY/transaction/fsync. Setup parent/fixture và digest verification nằm ngoài thời gian; total là elapsed ba phase, throughput=source rows/total. Các medians theo phase không nhất thiết cộng đúng median total.

| Delta / baseline | Examined | INSERT / UPDATE / UNCHANGED | Extract / compare / load median (s) | Total median [min–max] (s) | Rows/s median | Peak traced MiB |
|---|---:|---|---|---|---:|---:|
| 0% | 10,000 | 0 / 0 / 10000 | 0.0255 / 3.4653 / 0.0008 | 3.4972 [3.0286–3.5595] | 2859 | 5.63 |
| 1% | 10,050 | 50 / 50 / 9950 | 0.0262 / 3.8134 / 0.0007 | 3.8403 [3.8087–4.2032] | 2617 | 5.65 |
| 10% | 10,500 | 500 / 500 / 9500 | 0.0271 / 3.9800 / 0.0011 | 4.0194 [3.9967–4.1353] | 2612 | 5.82 |

Raw repetitions, min/max/stdev từng metric và môi trường được ghi tại `.local/portfolio-benchmark/result.json`, không commit. Các lần đo được chạy khi máy còn thực hiện validation/demo khác; không phải máy benchmark chuyên dụng. Peak là allocated Python bytes kể từ khi bật tracemalloc, không phải RSS hay tổng bộ nhớ fixture/parent đã tạo trước đó.

0% vẫn kiểm tra toàn bộ 10,000 rows để biết chắc không có delta; chi phí scan/typed comparison vẫn còn. Ghi delta giảm payload nhưng không loại bỏ source scan hoặc parent read. Comparator merge có streaming semantics; harness cố ý materialize extracted rows/change list để tách phase, nên peak memory không biểu diễn memory streaming production. Không suy ra lợi ích indexes/threads/materialization hay tốc độ production từ số đo này. Timings database/extraction thật: NOT_RUN.
