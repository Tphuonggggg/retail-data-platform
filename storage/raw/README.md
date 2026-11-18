# Raw storage

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
