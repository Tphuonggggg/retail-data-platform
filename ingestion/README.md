# ingestion — WWI-06A Full Load

## Trạng thái và phạm vi

2026-11-18: **Implemented / Offline Tested / REVIEW**. Full Load cho đúng11 populations đã có code/test; **runtime Full Load NOT RUN**, MVP-G03 chưa nghiệm thu. MVP-G02 foundation verified; source TLS certificate và hai archive effective INSERT vẫn là blocker MVP-G01. Task hiện tại chỉ cho code/offline tests, không cho chạy các lệnh load/provision dưới đây.

Module đọc SQL Server WWI → PostgreSQL Raw, quản lý run/capture, fidelity/count/digest và publication. Không tính KPI, không dbt/DW/SCD2/Airflow hoặc incremental; các phần đó **Not implemented yet**. Sales → Customer → Inventory giữ thứ tự nghiệp vụ; nạp11 source populations chỉ chuẩn bị Raw.

## Trách nhiệm, cấu trúc và dependencies

| Thành phần | Trách nhiệm / input → output |
| --- | --- |
| [full_load.py](full_load.py) | CLI và orchestration trong một process; contracts/config → candidate hoặc publication |
| [common/](common/README.md) | Frozen source schema, F2, codecs/digest, config, external evidence coverage |
| [extractors/](extractors/README.md) | Dedicated Windows identity; SELECT-only metadata/count/batched reads |
| [loaders/](loaders/README.md) | COPY/read-back/metadata/atomic pointer/recovery; không auto DDL/GRANT |
| [checkpoints/](checkpoints/README.md) | Incremental checkpoint Not implemented yet |
| [requirements.txt](requirements.txt) | pyodbc5.5.0, psycopg[binary]3.3.9 đã có trong project-local .venv; task này không cài package |

Python3.12, ODBC18, PostgreSQL18, unittest stdlib. Inputs: [source contracts](../docs/data-models/wwi-source-contracts.md), [metadata dictionary](../docs/data-models/wwi-metadata-dictionary.md), [accepted Full/Raw design](../docs/data-models/wwi-dw-03a-full-raw-design-proposal.md), [Raw foundation](../storage/raw/README.md), private ignored .env. Outputs: typed Raw candidates/published membership và metadata. Không sửa accepted mappings/KPI/temporal policies. Config tái sử dụng pure functions của [Raw checker](../scripts/check_raw_connection.py).

## Hợp đồng dữ liệu và kiểu

[source_contract.json](common/source_contract.json) đóng băng9 current tables/156 columns từ metadata dictionary: Sales.Customers, Orders, OrderLines, Invoices, InvoiceLines, CustomerTransactions; Warehouse.StockItems, StockItemHoldings, StockItemTransactions. Hai populations riêng Sales.Customers_Archive và Warehouse.StockItems_Archive giữ đủ columns/duplicate multiplicity; không unique natural key archive. Runtime so tên/thứ tự/type/nullability với sys.columns; khác biệt → STOP. Archive schema chưa kiểm tra lại trực tiếp trong task này.

| SQL Server | Python / Raw | Kiểm soát |
| --- | --- | --- |
| int, bit, date | int/bool/date → integer/boolean/date | Type/range/NULL theo source contract |
| decimal(p,s) | Decimal → numeric(p,s) | Không float hoặc âm thầm rounding; reject scale/range loss |
| nvarchar | str → text | Giữ Unicode/whitespace/case; reject NUL/unpaired surrogate không thể lưu lossless |
| varbinary(max) | bytes → bytea | Giữ nguyên bytes kể cả byte0 |
| geography | SQL native varbinary → bytes/bytea | Không gọi WKB; lưu engine/version/encoding context; actual round-trip proof pending |
| datetime2(7) | source F2 → str/None → text COLLATE "C" | Canonical27 ký tự YYYY-MM-DDTHH:MM:SS.fffffff; exact100ns/min/max/sentinel; không Python datetime |

F2 expression nguyên văn [B9 PoC](../tests/integration/b9_precision/poc.py), chỉ thay vetted operand. Technical run times dùng timestamptz, không biến system-time thành business-effective time. Geography dùng CONVERT(varbinary(max), geography) theo [SQL Server serialization](https://learn.microsoft.com/en-us/sql/t-sql/spatial-geography/spatial-types-geography-transact-sql?view=sql-server-ver17); cần actual adapter round-trip proof trước publication.

Current ORDER BY PK/strictly increasing key. Archive ORDER BY natural ID/ValidFrom/ValidTo; tied ordinal chỉ là occurrence trong capture, không stable cross-capture identity. Không collapse duplicates/zero-duration rows.

Source fetchmany, target COPY từng batch, read-back bằng **server-side named cursor**. Batch1–10000 mặc định500; binary/geography cap1; max-text cap64. Memory tỷ lệ batch × largest row; một LOB/driver buffer vẫn lớn. Chưa đo RSS/throughput hoặc hard memory ceiling. COPY dùng typed write_row, không CSV interpolation; transaction behavior theo [psycopg COPY](https://www.psycopg.org/psycopg3/docs/basic/copy.html).

## Target initialization và quyền

[full_load.sql](../storage/raw/full_load.sql) là **artifact chưa thực thi**, sinh từ [schema.py](loaders/schema.py):11 typed payload tables,11 views, bốn control tables. DDL new-only transaction trên retail_raw; Owner dùng postgres chỉ khi cấp quyền provisioning riêng. Collision → rollback; không DROP/TRUNCATE/IF-NOT-EXISTS che drift. Runtime luôn retail_ingest, không auto CREATE/GRANT/escalation.

Actual role chỉ có raw USAGE, không CREATE; payload/control mới chưa provision. Preflight sẽ TARGET_DDL_REQUIRED. Grant proposal chỉ SELECT/INSERT payload; controls SELECT/INSERT hoặc pointer SELECT/UPDATE; views SELECT. Metadata nền runs/object_runs giữ SELECT/INSERT/UPDATE; app không DELETE/TRUNCATE. Không nới quyền để đạt PASS.

Sau Owner review và **riêng target DDL/grants authorization**, lệnh PowerShell tương lai:

~~~powershell
Get-Content -LiteralPath storage/raw/full_load.sql -Raw | docker exec -i retail-raw-postgres-1 psql -X -U postgres -d retail_raw -v ON_ERROR_STOP=1
~~~

Lệnh **NOT RUN**, không áp dụng native PostgreSQL/B9 hoặc đổi bootstrap. CLI load không tự provisioning.

## Transaction, metadata và publication

runs lưu run_id/capture_id riêng, retry link, start/end/status/error/consistency. object_runs lưu scope/status/timestamps/source/extracted/loaded counts/reconciliation. Duration tính finished_at−started_at và tổng trên CLI; unknown count NULL, known rollback mới loaded=0. Columns dựa [bootstrap thực tế](../storage/raw/bootstrap.sql).

Bốn bảng mới: load_contracts(scope/contract fingerprint/source engine context), load_audits(count/SHA256 typed-row digest), raw_publications(immutable run/previous publication), raw_current(singleton pointer). Fingerprint là data replay contract, không approval manifest; source snapshot ID NULL khi không proof.

Sau preflight/session advisory lock: transaction nhỏ ghi RUNNING/PENDING, rồi **một transaction cho toàn selected scope** gồm COPY/read-back/count/digest/final status. Lỗi rollback toàn payload capture; không per-batch commit/partial publication. Long transaction/WAL cost cần đo. Source count trước/sau bằng nhau không chứng minh snapshot consistency.

Selected/all không proof → VALIDATED_UNPUBLISHED_CANDIDATE, consistency UNVERIFIED. Publication chỉ all11, external verified no-writes window + geography proof/count/content PASS; pointer/payload commit cùng transaction. Current views chỉ committed publication; downstream nhiều statements phải pin publication/run hoặc dùng consistent transaction. Base tables có candidate rows; consumers không tự MAX(run time) mỗi bảng. Raw publication không phải Certified DW/mart approval.

**Persisted chunk ledger/sealed-chunk resume, retained failed-content replay và toàn bộ attempt registry chưa triển khai**. WWI-06A có atomic capture và safe new-capture retry; không gọi source reread là retained replay. Accepted design giữ nguyên, remaining recovery requirements phải đối chiếu/bổ sung WWI-06B trước operational acceptance; không WWI-06/MVP-G03 DONE.

## CLI offline và cấu hình

Chạy tại root bằng .venv có sẵn. Private .env/environment, không password argv/in file tracked. Summary chỉ allowlisted fields. Fixed source tcp:DESKTOP-OBDFK6B,1433 / SQLEXPRESS / WideWorldImporters, kiểm Windows principal/SQL SID/user. Encrypt=yes/TrustServerCertificate=no không fallback. [.env.example](../.env.example): batch500/login5s/query60s có configurable bounds.

~~~powershell
.venv\Scripts\python.exe -m ingestion.full_load config --env-file .env
.venv\Scripts\python.exe -m ingestion.full_load plan --all
.venv\Scripts\python.exe -m ingestion.full_load ddl
~~~

plan là dry-run offline chỉ SELECT projections; ddl chỉ in SQL; config không kết nối. Các lệnh offline này đã chạy. load/abandon thiếu --execute dừng trước connect.

## Runbook runtime tương lai — NOT RUN

Prerequisites: Owner giao WWI-06B; source TLS hợp lệ/least privilege all11; target DDL/grants + actual schema/type adapter proof. Chạy Python trong Windows DESKTOP-OBDFK6B\wwi_extract session, nhập password tương tác ngoài repository, không PC/DBA fallback. Private config/env phải đọc được bởi extractor; task này không thay ACL/logon rights.

~~~powershell
# SELECT-only; connectivity kiểm source rights/schema, preflight thêm target payload.
.venv\Scripts\python.exe -m ingestion.full_load connectivity --all --env-file .env
.venv\Scripts\python.exe -m ingestion.full_load preflight --all --env-file .env

# Chỉ sau runtime authorization: selected candidate trước.
$candidateRun = [guid]::NewGuid().ToString()
.venv\Scripts\python.exe -m ingestion.full_load load --object Sales.Orders --run-id $candidateRun --execute --env-file .env
.venv\Scripts\python.exe -m ingestion.full_load reconcile --object Sales.Orders --run-id $candidateRun --env-file .env

# All11 candidate, vẫn UNVERIFIED nếu không proof.
$fullRun = [guid]::NewGuid().ToString()
.venv\Scripts\python.exe -m ingestion.full_load load --all --run-id $fullRun --execute --env-file .env
~~~

Source preflight luôn effective-rights all11, cả selected-object; archive INSERT phải resolve. Readonly ODBC hint không thay quyền thực tế. Không command nào bypass TLS/auto grant.

Publication cần **capture mới** trong actual verified window phủ toàn thời gian/scope. External JSON ở ignored .local; template sau **chưa valid**, không runtime proof:

~~~json
{
  "kind": "OWNER_VERIFIED_NO_WRITES_WINDOW",
  "reviewed": false,
  "endpoint": "tcp:DESKTOP-OBDFK6B,1433",
  "database": "WideWorldImporters",
  "reference": "REPLACE_WITH_REVIEWED_ACTUAL_SOURCE_WINDOW_EVIDENCE",
  "window_start": "REPLACE_WITH_ACTUAL_AWARE_ISO8601_START",
  "window_end": "REPLACE_WITH_ACTUAL_AWARE_ISO8601_END",
  "scope": ["Sales.Customers", "Sales.Customers_Archive", "Sales.CustomerTransactions", "Sales.InvoiceLines", "Sales.Invoices", "Sales.OrderLines", "Sales.Orders", "Warehouse.StockItemHoldings", "Warehouse.StockItemTransactions", "Warehouse.StockItems", "Warehouse.StockItems_Archive"],
  "geography_roundtrip_reference": "REPLACE_WITH_ACTUAL_ENGINE_ADAPTER_ROUNDTRIP_EVIDENCE"
}
~~~

Operator chịu proof writer inventory/control/window; parser chỉ kiểm review flag/shape/endpoint/coverage, không chứng minh authenticity/writer control. Không source timestamp nào tự thành business-effective time. Lệnh tương lai: load --all --run-id <new-uuid> --consistency-evidence .local/source-window.json --publish --execute --env-file .env. Không promote UNVERIFIED capture cũ bằng sửa metadata.

## Rerun và recovery

- Cùng run_id SUCCEEDED: durable count/digest read-back, không source reread/duplicate load/reset current pointer. Scope/contract phải khớp. reconcile không sửa metadata.
- Known batch failure: rollback toàn scope, metadata FAILED/category/progress, previous publication giữ nguyên. New UUID + --retry-of <failed-uuid> cùng scope/contract: source reread/new capture.
- Mất COMMIT ACK: COMMIT_OUTCOME_UNKNOWN_INSPECT_RUN_ID; không rewrite FAILED/auto retry. Fresh connection inspect runs/contracts/audits/payload/publication. SUCCEEDED → reconcile sameID; ambiguity → STOP.
- Crash để RUNNING: operator xác nhận process dừng; abandon đúng --all/--object + --run-id + --execute phải lấy lock và không payload/audit/publication rồi mới mark FAILED. Không delete. Broken connection không giả vờ rollback/loaded=0.
- Logs chỉ IDs/status/category/count/duration, không driver text/row values/password. Close failure trả non-zero và inspect-before-retry. Không auto database retry/backoff để che lỗi.

## Testing, acceptance và WWI-06B

~~~powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p full_load_offline.py -v
.venv\Scripts\python.exe -m unittest discover -s tests -p raw_foundation_static.py -v
.venv\Scripts\python.exe -m unittest discover -s tests -p source_security_static.py -v
~~~

[Offline suite](../tests/full_load_offline.py): synthetic fixtures/mock drivers; F2/NULL/Decimal/Unicode/binary, frozen contracts156 current columns, batching/empty/history duplicates, rollback/count/content mismatch/retry/idempotency/unknown ACK, atomic full-scope publication, identity/schema/TLS/permission blockers, named cursor/no-secret CLI. Offline PASS không chứng minh SQL compilation/geography fidelity/performance hoặc runtime ingestion.

Kết quả thực tế2026-11-18: Python3.12.10, pyodbc5.5.0, psycopg/psycopg-binary3.3.9 và ODBC Driver18 có sẵn; không install. **38 Full Load +22 Raw foundation +18 source security +12 B9 offline tests PASS**. CLI plan/config/ddl PASS offline; load thiếu execute trả exit1 trước connection. Final readonly Raw inspection: PostgreSQL18.7,0 payload tables, chỉ runs/object_runs, counts[0,0], app Raw CREATE=false. Task chỉ restart Raw một lần ở Phase A và chạy metadata/TCP reads; không source query/extraction, payload DDL/grants/COPY/publication, source permission change, native PostgreSQL/B9 resource change hoặc real Full Load.

WWI-06A acceptance: runnable CLI/code/type contracts + reproducible offline tests + safe failure/recovery/privilege boundaries; Owner review pending. WWI-06B: resolve source TLS/archive INSERT; actual full projection/archive metadata/geography proof; review/provision target artifact; dedicated runtime preflight; selected smoke/full candidate trong verified window; actual COPY/rollback/reconnect/idempotency/count+value/atomic views và remaining chunk/attempt recovery requirements. Chưa bắt đầu WWI-06B hoặc milestone sau.
