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
