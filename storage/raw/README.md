# Raw storage

**Latest WWI-06B:** [live provisioning verification](#wwi-06b--live-provisioning-verification-2026-11-18) xác nhận NOT APPLIED cho payload/control/view objects, không chỉ dựa Owner-reported COMMIT. Foundation vẫn PASS; actual load chưa được phép.

## Trạng thái

**2026-11-18: MVP-G02 DONE — foundation verified.** PostgreSQL18.7/retail_raw, schemas raw/ingestion_meta, runs/object_runs và retail_ingest permissions/TCP giữ nguyên qua một bounded Raw-only restart; [evidence](../../infrastructure/docker/README.md#phase-a--mvp-g02-verified-2026-11-18).

**WWI-06A: SQL prepared / offline tested; payload runtime NOT RUN.** [Full Load code/runbook](../../ingestion/README.md) đã có. [full_load.sql](full_load.sql) chưa apply; không payload/control tables mới, COPY hoặc publication đã chạy. Historical bootstrap failure/recovery ở Docker runbook không phải current failure.

## Purpose, scope và responsibilities

Sở hữu storage contract source-shaped Raw và ingestion metadata, không KPI/DW/SCD2 hoặc orchestration. Inputs: approved11 source populations + types, existing foundation/config; outputs: typed immutable capture rows, technical metadata và published membership. Dependencies: infrastructure Compose, ingestion/accepted source design.

## Foundation và proposed extensions

| Object | Grain / status |
| --- | --- |
| raw / ingestion_meta schemas | Foundation đã verified, owner postgres |
| ingestion_meta.runs | Một invocation/run_id, capture_id riêng, retry link, times/status/consistency |
| ingestion_meta.object_runs | Một run/source object, counts/status/reconciliation/error; đúng11-object allowlist |
| load_contracts / load_audits | Proposed: scope/fingerprint/source context và count/typed digest |
| raw_publications / raw_current | Proposed: publication ledger và atomic singleton pointer |
| raw.sales_* / raw.warehouse_* | Proposed:11 typed payload tables, PK(run_id,row_ordinal); unique current key trong run, không archive NK uniqueness |
| raw.current_* | Proposed:11 views chỉ đọc current published all11 membership |

Baseline [bootstrap.sql](bootstrap.sql) đã apply ngoài task hiện tại; chỉ role/schema/run tracking, không payload. Runtime retail_ingest NOSUPERUSER/NOCREATEDB/NOCREATEROLE/NOREPLICATION/NOBYPASSRLS; CONNECT/USAGE và metadata SELECT/INSERT/UPDATE; không Raw CREATE/DELETE/TRUNCATE. Các grants cho objects mới ở proposed SQL **chưa cấp**, pipeline không tự cấp.

## Data, time và recovery semantics

Counts chưa biết NULL; known zero mới0. Count equality không đủ chứng minh fidelity/consistent source. SUCCEEDED execution không tự Raw publication. Unverified source context không được đưa vào published views. Payload datetime2(7) dùng F2→str/None→TEXT COLLATE C; technical timestamps timestamptz. Geography native SQL varbinary/engine context cần actual fidelity proof; NULL/Decimal/Unicode/binary không được âm thầm normalize. Current và physical archive riêng, giữ duplicates/zero-duration.

[Accepted Full/Raw design](../../docs/data-models/wwi-dw-03a-full-raw-design-proposal.md) vẫn giữ. WWI-06A triển khai atomic capture/new-capture retry; persisted sealed chunks/attempt registry/retained failed-content replay chưa có, không gọi source reread là replay. WWI-06/MVP-G03 không DONE. Không TRUNCATE/overwrite để rerun; không suy CDC/business-time/history completeness.

## Technology, structure và execution

PostgreSQL18/psql. [full_load.sql](full_load.sql) sinh từ [schema.py](../../ingestion/loaders/schema.py), không runtime execution; có guard retail_raw/postgres và transaction new-only, không DROP/role creation. Owner cần review/cho phép riêng target initialization/grants ở WWI-06B. [Runbook](../../ingestion/README.md) có exact proposed command, CLI/preflight/load/reconcile/recovery; **không chạy initialization/load trong task WWI-06A**. Không đụng native PostgreSQL/B9.

## Testing và acceptance

[Foundation tests](../../tests/raw_foundation_static.py) kiểm config/metadata guards/Compose/checker; foundation actual runtime evidence ở trên. [Full Load offline tests](../../tests/full_load_offline.py) kiểm generated SQL bằng generator, contracts/types/transaction model/digest/rerun. Không dùng mock/static PASS claim SQL engine compilation/new grants/COPY/publication runtime. WWI-06B phải provision đúng scope và kiểm engine/fidelity/recovery/atomic views dưới runtime authorization trước operational acceptance.

[Parent storage](../README.md).

## WWI-06B — Live provisioning verification, 2026-11-18

**Provisioning = NOT APPLIED. First load NOT READY.** Git đầu task main/4435b2a7ac97261e88175a27e19a88695620d68a, clean. Owner báo output có COMMIT; kiểm live đúng approved target chưa thấy bất kỳ object mới nào từ full_load.sql. COMMIT riêng lẻ không xác nhận đúng SQL/context đã được apply. Chưa xác định lần chạy đó ở đâu; không dò native PostgreSQL/B9/database khác, không tự rerun/reset.

### Docker và target đã verified

Operator DESKTOP-OBDFK6B\PC; CLI tại C:\Users\PC\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe; context desktop-linux, Docker client/server29.8.2/Linux. Container retail-raw-postgres-1 ID9fd7b79bf3a28ba8a531fef868fa5d8aaf6b0af786d9e042b3407fdb65ca8ddd, healthy, image postgres:18; runtime SQL18.7. Image digest sha256:2ea8630df176ad090ec92136dee850397c5af8781e4bcf2e4162593691c61bbc, RepoTag/RepoDigest verified; không dùng Compose image label một mình làm current-image proof.

Compose labels project retail-raw/service postgres/config_files trỏ đúng infrastructure/docker/compose.raw.yaml trong repo này. Binding chỉ127.0.0.1:55434→5432; volume retail-raw_pg_data→/var/lib/postgresql, labels project retail-raw/volume pg_data. Bootstrap bind read-only. Không inspect container Env hoặc password, không sửa system PATH. Read-only Docker commands phải chạy PC; không dùng wwi_extract để quản lý Docker.

### Exact live inventory và differences

| Live table | Owner | Columns | Rows | Kết quả |
| --- | --- | --- | --- | --- |
| ingestion_meta.runs | postgres | 11 | 0 | Foundation column names/types/nullability/defaults/PK/FK và validated CHECK definitions khớp bootstrap.sql |
| ingestion_meta.object_runs | postgres | 11 | 0 | Foundation column names/types/nullability/defaults/PK/FK và validated CHECK definitions khớp bootstrap.sql |

Schemas raw/ingestion_meta đều owner postgres. Hai indexes duy nhất trong scope là runs_pkey trên(run_id), object_runs_pkey trên(run_id,source_schema,source_table): btree/primary/unique/valid/ready. Không constraint invalid/deferrable; không table RLS trong hai bảng. Không suy toàn volume hoặc database khác không có dữ liệu giá trị từ inventory này.

Tên expected dưới đây lấy từ CREATE TABLE/CREATE VIEW trong chính [full_load.sql](full_load.sql), không tự đặt theo suy đoán. Artifact cũng được so khớp với generator hiện có.

| Expected payload table — absent | Expected serving view — absent |
| --- | --- |
| raw.sales_customertransactions | raw.current_sales_customertransactions |
| raw.sales_customers | raw.current_sales_customers |
| raw.sales_customers_archive | raw.current_sales_customers_archive |
| raw.sales_invoicelines | raw.current_sales_invoicelines |
| raw.sales_invoices | raw.current_sales_invoices |
| raw.sales_orderlines | raw.current_sales_orderlines |
| raw.sales_orders | raw.current_sales_orders |
| raw.warehouse_stockitemholdings | raw.current_warehouse_stockitemholdings |
| raw.warehouse_stockitemtransactions | raw.current_warehouse_stockitemtransactions |
| raw.warehouse_stockitems | raw.current_warehouse_stockitems |
| raw.warehouse_stockitems_archive | raw.current_warehouse_stockitems_archive |

Bốn expected control tables cũng absent: ingestion_meta.load_contracts, ingestion_meta.load_audits, ingestion_meta.raw_publications, ingestion_meta.raw_current. Tổng0/15 new tables và0/11 views. Column/type/nullability/PK/check/index/ownership/privilege comparison cho **objects mới = NOT VERIFIABLE — ABSENT**, không đánh PASS từ static SQL hay gọi đây chỉ là missing GRANT. Publication pointer chưa tồn tại, không ghi nhận như existing NULL pointer.

### Runtime identity và preflight

retail_raw/retail_ingest/session_user retail_ingest/UTF8/C verified qua TCP55434. Role LOGIN=true; SUPERUSER/CREATEDB/CREATEROLE/REPLICATION/BYPASSRLS=false; không direct role memberships. Database CONNECT=true, CREATE/TEMP=false. Hai schemas USAGE=true/CREATE=false. Hai metadata tables SELECT/INSERT/UPDATE=true; DELETE/TRUNCATE/REFERENCES/TRIGGER/MAINTAIN=false. Foundation permissions **PASS**; quyền trên objects mới chưa kiểm được vì objects không tồn tại, không tự GRANT.

| Check | Outcome / evidence boundary |
| --- | --- |
| Raw checker | PASS_READONLY_CONNECTIVITY |
| config --batch-size64 / selected offline plan | PASS; target đúng, source strict TLS flags giữ nguyên, không extraction |
| PostgresTarget.preflight(all11) | BLOCKED — TARGET_DDL_REQUIRED |
| Actual CLI preflight selected holdings trong PC session | FAIL_STOP — DEDICATED_SOURCE_IDENTITY_REQUIRED; dừng trước source connection, chưa reach archive-permission check |
| Source strict TLS dưới actual wwi_extract | PASS — Owner-provided trong task mới; không independently rerun bởi Codex/PC |
| Archive effective INSERT exception | Unresolved; guard strict-zero all11 không đổi, không skip archives/impersonate/DBA fallback |
| reconcile / real load / publication | NOT RUN; chưa có validated runId/payload; --execute load không được authorize |

### Exact next steps và smoke command

Owner cần review execution context/output lần COMMIT trước, rồi giao riêng bounded provisioning/remediation đúng retail_raw nếu tiếp tục; **không có quyền apply/rerun trong task này**. Script new-only: không chạy lại chỉ để xem có qua không. [Docker operator/PATH và exact reviewed provisioning command](../../ingestion/README.md#schematype-và-raw-provisioning-review) dành cho future authorization; cần verify lại objects sau apply, không chỉ exit0/COMMIT.

Sau target verification PASS và Owner giải quyết archive security decision, fresh wwi_extract session phải chạy selected CLI preflight; PC chỉ Docker operator. Smoke vẫn cần Owner authorize riêng, source Windows identity wwi_extract, target retail_ingest, strict TLS, không publication:

~~~powershell
Set-Location -LiteralPath 'D:\Code\Retail_Data_Platform\project1_Retail_Data_platform'
whoami /user
.venv\Scripts\python.exe -m ingestion.full_load preflight --object Warehouse.StockItemHoldings --env-file .env
if ($LASTEXITCODE -ne 0) { throw 'STOP: source/target preflight not accepted' }
# Chỉ sau explicit selected-load authorization:
$candidateRun = [guid]::NewGuid().ToString()
$candidateRun
.venv\Scripts\python.exe -m ingestion.full_load load --object Warehouse.StockItemHoldings --batch-size 64 --run-id $candidateRun --execute --env-file .env
if ($LASTEXITCODE -ne 0) { throw ('STOP: inspect '+$candidateRun+'; no automatic retry') }
~~~

Commands trên **PREPARED / NOT RUN**. [Existing smoke plan](../../ingestion/README.md#selected-object-smoke-procedure--prepared-not-run) có source before/after profile, numeric/NULL/time controls, digest/fresh-session reconciliation/metadata lifecycle/failure/unchanged publication checks. Baseline227/227/30343296/5107.92 chỉ historical; không remeasure source dưới PC trong task này. Không --publish, không declare source snapshot consistency.

Validation thực chạy:44 Full Load/readiness +22 Raw foundation +18 source security +12 B9 offline tests PASS; syntax/secret/link/Git scope checks trước commit. Không code/schema/security policy changes hoặc source queries; chỉ read-only Docker/Raw metadata và CLI guard checks, minimal docs. Không restart/recreate/delete resource, mutate DB/permissions/certificates, hoặc Full Load. WWI-06B/WWI-06 vẫn IN_PROGRESS, MVP-G03 chưa acceptance.
