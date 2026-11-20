# Ingestion

## INGEST-01/02/03 — Runtime acceptance, 2026-11-19

**FULL_LOAD_RUNTIME_ACCEPTED — unpublished candidates.** Phần preparation/NOT RUN phía dưới là trạng thái trước Owner development-config approval và execution trong task này.

- Source: tcp:DESKTOP-OBDFK6B,1433 / SQLEXPRESS / WideWorldImporters; Windows current PC account. Owner approve đúng ba local keys APP_ENV=development, trust=yes, admin-source=yes; password/SQL grants/certificate stores không đổi, .env ignored.
- Target: existing retail-raw-postgres-1 (ID9fd7b79b), retail_raw18.7 / retail_ingest / localhost55434 / retail-raw_pg_data. Restored same container/volume, healthy; source/target all11 preflight PASS.
- Environment: Python3.12.10, pyodbc5.5.0, psycopg3.3.9, ODBC18; không install packages.

| Object | Source rows | Candidate rows | Count / digest / controls |
|---|---:|---:|---|
| Sales.Customers | 663 | 663 | PASS |
| Sales.Orders | 73595 | 73595 | PASS |
| Sales.OrderLines | 231412 | 231412 | PASS |
| Sales.Invoices | 70510 | 70510 | PASS |
| Sales.InvoiceLines | 228265 | 228265 | PASS |
| Sales.CustomerTransactions | 97147 | 97147 | PASS |
| Sales.Customers_Archive | 51 | 51 | PASS |
| Warehouse.StockItems | 227 | 227 | PASS |
| Warehouse.StockItemHoldings | 227 | 227 | PASS |
| Warehouse.StockItemTransactions | 236667 | 236667 | PASS |
| Warehouse.StockItems_Archive | 444 | 444 | PASS |
| Total | 939208 | 939208 | PASS |

### Runs và source capture window

| Run | ID | Result |
|---|---|---|
| Holdings smoke, batch64 | 47b6c909-b930-411a-912b-9a3ca4270907 | 227 rows, SUCCEEDED, engine duration0.109s |
| All11, batch default500 with existing LOB caps | 5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8 | 939208 rows, SUCCEEDED, engine duration154.625s |
| Injected first-COPY failure | eb8da54c-f80f-42f5-adc3-c7753ea357c6 | FAILED, INJECTED_RUNTIME_COPY_FAILURE; extracted64, loaded0, payload0, audits0 |
| New-ID retry of failed run | b3520673-0ce1-48d5-bd2a-1093bec5130a | 227 rows, SUCCEEDED, engine duration0.062s |

All11 CLI window observed UTC2026-11-19T04:36:49.913340 →04:39:25.649191; baseline aggregates trước load và fresh source checks sau load khớp. Source current tables fresh ordered digests khớp capture audits9/9; hai physical histories dùng order-independent duplicate-multiplicity fingerprints khớp Raw, không giả stable ordinal xuyên capture. Không quan sát unexpected source-content changes. Không khóa toàn bộ writers hoặc tạo SQL snapshot: **consistency_state vẫn UNVERIFIED**, không Certified point-in-time dataset và chưa publish.

### Reconciliation và fidelity

- All11 source/extracted/Raw counts và ordered typed-row digests PASS; fresh-connection durable reconciliation PASS. Nine current PK distinct counts bằng row counts; archives không có source PK, giữ duplicates/occurrences.
- NULL distribution và sums trên mọi int/decimal columns khớp source/Raw; required NULL violations0. Holdings QuantityOnHand=30343296, LastCostPrice=5107.92; all9 holdings NULL counts0.
- InvoiceLines controls: Quantity8950628, UnitPrice10406986.80, TaxAmount25782098.25, ExtendedPrice198043439.45, source LineProfit85729180.90. Đây là source controls, không định nghĩa thêm revenue/COGS/profit.
- datetime2(7) source F2 → str → Raw TEXT/C giữ7 digits, NULL, min/max và sentinel9999-12-31T23:59:59.9999999. Four temporal populations không reversed intervals; zero-duration không bị loại.
- Unicode/Decimal/NULL/native bytes đi qua codec/COPY/read-back/digest. Native geography bytes đã persist/read-back exact cho663 customers và51 history rows; không chuyển WKB hoặc suy business-effective time.
- 16 source/Raw reference checks trong selected scope đều0 orphan; nullable FK NULL không tính orphan. Application/Purchasing reference populations ngoài11 không được nạp, không claim kiểm toàn bộ external relationships.
- Raw không tạo business FKs lên tables chưa nạp; all11 cùng capture transaction, kiểm relationships sau complete scope. Không dùng thứ tự nạp làm bằng chứng integrity.

### Rerun, failure và publication

Supported CLI load --all cùng all11 run ID trả ALREADY_VALIDATED_NO_RELOAD, durable reconcile11/11 PASS; payload/metadata counts trước/sau giữ nguyên. Controlled probe inject lỗi sau một COPY thật trong transaction, rollback toàn payload và giữ FAILED metadata. Retry --retry-of với UUID mới thành công; đây là new-source capture, không retained-content replay.

Final:4 runs (3 SUCCEEDED,1 intentional FAILED),14 object_runs,13 audits,0 RUNNING,0 publications, raw_current=NULL; all11 serving views vẫn0 rows. Raw holdings base table có681 rows ở3 distinct captures; không cộng xuyên run để đối soát snapshot227 rows. Không delete/reset failed attempts.

Hai verifier failures được giữ trong ignored local evidence: normalization int vs PostgreSQL numeric cho SUM(bigint), và driver error ở comprehensive verifier. Đã normalize count types, close ODBC cursors explicitly và thêm regression tests; corrected verifier PASS, không reload hoặc sửa payload để che lỗi. Engine load không thất bại ở các lượt verifier này.

### Commands tái kiểm chứng

```powershell
.venv\Scripts\python.exe -m ingestion.full_load reconcile --all --run-id 5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8 --env-file .env
.venv\Scripts\python.exe tests/integration/ingest_runtime.py --execute --run-id 5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8 --env-file .env
```

Second command rereads source aggregates; nếu nguồn thay đổi sau evidence window phải điều tra, không tự sửa capture cũ. [Failure probe](../tests/integration/ingest_failure_runtime.py) mặc định help-only, --execute tạo một failed test run mới trên Raw; không chạy lại để chỉ xem evidence. Local sanitized aggregates/digests/CLI outputs giữ ở ignored `.local/ingest-20261119`; durable capture/audits/metadata ở Raw, không commit source payload hoặc credentials.

**Next:** dbt Staging → Core DW → Sales Mart theo task Owner. Candidate đã sẵn cho scoped development bằng explicit run pin; published current views chưa có dữ liệu. Publication cần approval riêng và consistency requirements hiện hành; advanced sealed-chunk replay vẫn deferred. Task này không triển khai downstream.

**INGEST-01/02/03 — 2026-11-19:** existing Raw container restored, healthy; schema/grants/all11 target preflight PASS, all payload/runs empty, pointer NULL. Python3.12.10/pyodbc5.5.0/psycopg3.3.9/ODBC18 verified. Source/load NOT RUN: local config remains production/trust=no/admin opt-in=no; current PC account requires explicit local development/admin opt-in, Owner response pending. No secrets/config changes or ingestion performed. Do not infer runtime acceptance from offline tests.

Prepared read-only acceptance tool: `python tests/integration/ingest_runtime.py --execute --object Warehouse.StockItemHoldings --env-file .env` captures source aggregates; add `--run-id <uuid>` after authorized load for candidate count/distinct/numeric/NULL/F2 min-max and durable digest comparison. Outputs aggregates only; no publication or writes. Runtime of this tool awaits source configuration. Continue to smoke, all11 load, RI checks and safe rerun/failure verification after opt-in; first smoke alone does not close the task.

Python3.12 + pyodbc5.5.0 + psycopg3.3.9. Full Load Implemented/Offline Tested; runtime NOT RUN. [Setup/commands](../README.md).

- full_load.py: CLI config/plan/ddl/connectivity/preflight/load/reconcile/abandon.
- common: frozen11-source contracts, config, codecs, exact F2 datetime2(7), digest/evidence.
- extractors: current-account Windows Auth, SELECT-only, selected SELECT/projection/schema checks.
- loaders: non-admin retail_ingest, target schema/grants checks, COPY/read-back, metadata/atomic publication.
- checkpoints: incremental ch?a tri?n khai.

## Contract runtime

SELECT explicit columns/parameterized metadata; no source writes. Encrypt=yes m?c ??nh; development trust=yes v? admin-source opt-in ph?i explicit. Kh?ng permission audit/history INSERT global gate. Selected load check ??ng selected objects; all load check all11. Missing SELECT/schema drift ? STOP.

Source-shaped Raw gi? Decimal/NULL/Unicode/binary/native geography bytes/datetime2(7) text27/C. Batch limits v? ordered typed digest gi? nguy?n; archive duplicates gi? occurrence, kh?ng fake PK. Geography full persistent coverage v?n c?n runtime proof.

Raw provisioning ?? PASS11 payload/4 controls/11 views, foundation2 tables intact. Runtime kh?ng auto DDL/GRANT. M?t capture transaction, known failure rollback; same successful run ID reconcile/no reload; failed run retry d?ng UUID m?i; unknown commit ph?i inspect. Sealed-chunk replay/resume ch?a implement, l? advanced milestone.

Selected candidate kh?ng publish; existing all11 publication c?n consistent source proof v? geography/reconciliation evidence. Read-only extraction/count equality kh?ng t? ch?ng minh source snapshot consistent. Ch?a thay publication semantics ho?c accepted SCD2/business rules.

## First smoke acceptance

Warehouse.StockItemHoldings/batch64/unpublished: fresh source vs Raw count/distinct keys/numeric totals/NULLs, exact F2, typed digest, durable reconnect/reconcile/rerun, run/object metadata, unchanged publication pointer. Ch?a ch?y trong reset.

## Tests v? history

[Offline tests](tests/full_load_offline.py), [Raw tests](../infrastructure/tests/raw_foundation_static.py), [Raw SQL](../infrastructure/postgres/README.md). [Evidence tr??c reset](../docs/archive/pre-reset/ingestion-history.md) l? historical, kh?ng active security requirements.
# Paths hiện hành — REPO-STRUCTURE-02

CLI `python -m ingestion.full_load` giữ nguyên. Raw config helper chuyển sang infrastructure.scripts.check_raw_connection; source diagnostics dùng `python ingestion/scripts/inspect_wwi_source.py`. Unit/offline tests: `python -m unittest discover -s ingestion/tests -p full_load_offline.py -v`. Cross-module acceptance/recovery probes vẫn ở tests/integration, không chạy load tự động.

Raw DDL/runbook ở [infrastructure/postgres](../infrastructure/postgres/README.md); capture, datatype/F2 fidelity và business/data contracts không đổi. Runtime evidence ngày 2026-11-19 bên dưới giữ nguyên; re-verification sau refactor ngày 2026-11-20 BLOCKED do Docker Engine unavailable/TCP55434 timeout. Không chạy lại Full Load hoặc publish để kiểm tra refactor.
