# infrastructure

Sở hữu Docker Compose, PostgreSQL initialization/schema provisioning và local infrastructure utilities. Không chứa ingestion hoặc dbt transformation logic.

- [docker](docker/README.md): Compose project retail-raw, localhost55434, volume retail-raw_pg_data.
- [postgres](postgres/README.md): bootstrap.sql, full_load.sql và bằng chứng Raw provisioning/load lịch sử. SQL không đổi trong refactor, không chạy initialization lại.
- scripts/check_raw_connection.py: offline config hoặc SELECT-only connectivity.
- scripts/recover_raw_bootstrap.py: historical recovery, mặc định chỉ preflight; không apply trong refactor.
- scripts/provision_warehouse.py và postgres/warehouse/provision.sql: draft DW-IMPLEMENT-01 chưa runtime verified, không chạy tự động.
- tests: Raw foundation offline/static và initial-empty provisioning read-only verifier.

Runtime accepted ngày 2026-11-19 nằm tại [ingestion](../ingestion/README.md#ingest-010203--runtime-acceptance-2026-11-19). Ngày 2026-11-20 Docker Linux Engine unavailable/TCP55434 timeout; kiểm lại capture BLOCKED, không sửa/xóa/recreate infrastructure.

Compose bootstrap bind chuyển sang ../postgres/bootstrap.sql; container/image/project/volume/port không đổi. Existing container không bị recreate trong refactor. [Project checks](../scripts/run_checks.py) chỉ offline; Compose config validation không khởi động service.

## DBT-SALES-01 — khôi phục runtime ngày 2026-11-20

Docker Desktop đã được khởi động bằng CLI; container Raw cũ ban đầu không start vì bind mount vẫn dùng đường dẫn bootstrap trước refactor. [ensure_raw_bind.ps1](scripts/ensure_raw_bind.ps1) khôi phục `storage/raw` dưới dạng runtime-only junction tới `infrastructure/postgres` (ignored); chỉ có một bản canonical SQL. Mặc định helper chỉ inspect; `-Apply` chỉ tạo khi chưa có, không xóa/ghi đè đường dẫn khác. Chạy helper trước `docker start retail-raw-postgres-1` nếu clone/path cũ thiếu junction. Không recreate container, reset volume hoặc chạy lại bootstrap.

Container ID `9fd7b79bf3a28ba8a531fef868fa5d8aaf6b0af786d9e042b3407fdb65ca8ddd`, image postgres:18, volume retail-raw_pg_data, database retail_raw18.7, loopback55434 giữ nguyên. Read-only typed digest của accepted capture PASS cả 11 objects/939208 dòng; publication ledger0/pointerNULL.

Owner đã phê duyệt [warehouse provisioning package](postgres/warehouse/provision.sql), SHA256 `409e65e330e2cc7292c23c87c8cbc914c46121c5d0acd38a08476b9546335477`. [Provisioning entrypoint](scripts/provision_warehouse.py) đã thực thi transaction qua đúng container socket/postgres, exit0: role retail_transform không admin; CONNECT database, USAGE Raw/meta, SELECT đúng 6 payload dependencies và 6 metadata/control tables; sở hữu 6 schemas dw_staging/dw_intermediate/dw_core/sales_marts/dq/dbt_sales_test. LOGIN dùng secret random lưu private, không log/commit. Không có quyền ghi Raw/meta, không thay SQL Server. Ordinary transformations dùng retail_transform; không dùng postgres.

Đây là new-only provisioning đã chạy, không phải lệnh recovery để chạy lại. Helper dừng nếu role/schema/private profile đã tồn tại. Các snapshot “unavailable/draft” phía trên giữ làm lịch sử, được supersede bởi runtime results này và [dbt runbook](../dbt/README.md).
