# Raw foundation

## Purpose, scope và responsibilities

Namespace Raw và invocation/object-run tracking cho target Compose riêng. **Server retail_raw đã chạy, nhưng bootstrap FAILED và schemas/tables/ingestion role chưa tồn tại theo readonly inspection2026-11-17.** [Bootstrap](bootstrap.sql) đã sửa failure exit và chuẩn bị recovery, chưa apply. Không tạo WWI payload tables, batch/chunk/publication ledger, checkpoint, warehouse hoặc SCD2; ingestion/publication runtime Not implemented yet.

## Inputs, outputs và dependencies

Input: dedicated database `retail_raw` mới, bootstrap user `postgres`, ingestion password qua container environment; [Compose](../../infrastructure/docker/README.md) sở hữu first-start execution. Output dự kiến:

| Object | Grain / trách nhiệm |
| --- | --- |
| `raw` | Namespace cho source-shaped payload, hiện chưa có payload tables |
| `ingestion_meta.runs` | Một invocation `run_id`; `capture_id` riêng, optional retry link, mode/status/timestamps/consistency reference |
| `ingestion_meta.object_runs` | Một `(run_id, source_schema, source_table)` trong đúng11 approved objects; observed counts/status/reconciliation/error code |

Owner schemas/tables là bootstrap `postgres`; app `retail_ingest` NOSUPERUSER/NOCREATEDB/NOCREATEROLE/NOREPLICATION/NOBYPASSRLS. App được CONNECT database, USAGE schemas và SELECT/INSERT/UPDATE metadata; không DELETE/TRUNCATE hoặc CREATE schema/payload tables. Chưa grant quyền payload khi chưa có bảng. Bootstrap password không dùng cho normal ingestion. SQL Server identity/grants là phần riêng, không được bootstrap PostgreSQL thay đổi.

## Data và time semantics

Counts chưa đo để NULL, không dùng0 thay unknown. `reconciliation_state=PASS` yêu cầu ba count có giá trị và bằng nhau, nhưng count equality không chứng minh fidelity/source consistency. `SUCCEEDED` chỉ là execution status, không Raw publication. Consistency mặc định UNVERIFIED; evidence reference bắt buộc nếu sau này ghi VERIFIED_CONSISTENT, application vẫn phải kiểm actual proof.

`timestamptz` chỉ lưu technical run times; **không** lưu authoritative datetime2(7) nguồn vào các cột này. Payload temporal sẽ dùng approved F2→Python str/None→PostgreSQL TEXT/C, giữ27 ký tự/100ns/sentinel/NULL theo B9. Current/H là populations riêng; archive duplicate multiplicity không được collapse.

Giữ [approved Full/Raw design](../../docs/data-models/wwi-dw-03a-full-raw-design-proposal.md): append-only captures, riêng capture/batch/attempt/chunk/publication, atomic published membership và replay retained content. Hai bảng foundation chưa đủ thay các manifests đó. WWI-06 phải bổ sung physical metadata/payload trước production Full Load; không TRUNCATE/overwrite Raw để làm rerun. Không phát minh CDC, opening inventory hoặc KPI.

## Technology, structure và execution

PostgreSQL18 SQL/psql; [bootstrap.sql](bootstrap.sql), không extension/dependency mới. Script dùng first start hoặc authorized recovery A trên target new-only; role/schema collision → STOP, không `IF NOT EXISTS` che drift. Guard invalid target/password/collision dùng constant SQL exception với ON_ERROR_STOP → exit3, không `\quit 1`. CREATE/GRANT nằm trong transaction; không sửa schema/permission scope đã định nghĩa. [Recovery A/B và exact commands](../../infrastructure/docker/README.md#bootstrap-failure-và-recovery-a); không chạy trên native PG hoặc B9.

## Testing, acceptance và status

[Offline suite](../../tests/raw_foundation_static.py) kiểm SQL allowlist, counts/status constraints, no destructive reset và config/Compose. Chưa engine compilation, SQL execution hoặc real connection; không dùng text checks để claim constraint runtime PASS. Sau Owner cho phép startup, chạy [readonly probe](../../scripts/check_raw_connection.py), kiểm role/schema và persistence rồi mới xét MVP-G02. Dữ liệu payload/idempotency/recovery thuộc MVP-G03/04, chưa triển khai.

[Parent storage module](../README.md). Current status: fix offline tested và guard-only read-only probes verified; **full bootstrap/recovery not applied**, app permissions chưa runtime verified; ingestion/publication **Not implemented yet**.
