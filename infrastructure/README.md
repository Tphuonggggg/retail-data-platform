# Infrastructure và PostgreSQL

## Setup và persistence

Docker Desktop dùng Linux Engine, context desktop-linux. Compose: [compose.raw.yaml](docker/compose.raw.yaml), project retail-raw, service postgres, container retail-raw-postgres-1, database retail_raw, host binding127.0.0.1:55434→5432, volume retail-raw_pg_data. PostgreSQL18 là target riêng, không thay native PostgreSQL hoặc B9 sandbox. Volume lưu dữ liệu độc lập container; không prune/remove/recreate để sửa kết nối.

```powershell
docker compose --env-file .env -f infrastructure/docker/compose.raw.yaml config --quiet
docker context show
docker inspect retail-raw-postgres-1 --format '{{.State.Status}}'
.venv\Scripts\python.exe infrastructure/scripts/check_raw_connection.py --help
```

Máy mới: tạo private .env từ template; ingestion/admin passwords phải khác nhau, tối thiểu16ký tự. Giữ .env và credentials ngoài Git. Xác minh port/container/volume không xung đột, target/database/identity đúng trước khi provision. Compose dùng bootstrap bind read-only; không khởi tạo lại database đang có chỉ vì sửa đường dẫn.

## Provisioning và migration

| File | Chức năng |
|---|---|
| [bootstrap.sql](postgres/bootstrap.sql) | raw/ingestion_meta foundation, runs/object_runs, ingestion role |
| [full_load.sql](postgres/full_load.sql) |11typed payload tables,4control tables,11published views và pointer singleton |
| [incremental.sql](postgres/incremental.sql) |6delta tables, version/events metadata, state functions và immutable triggers |
| [warehouse/provision.sql](postgres/warehouse/provision.sql) | retail_transform và dw_staging/intermediate/core, sales_marts/dq/test schemas |
| [warehouse/provision_bi_reader.sql](postgres/warehouse/provision_bi_reader.sql) | retail_bi_reader read-only trên đúng12Sales objects |

Thứ tự máy mới: foundation → Full Load objects → incremental extension; warehouse trước dbt build, BI reader sau khi approved objects tồn tại. DDL/GRANT chỉ bằng administrative identity và authorization riêng, psql -X -v ON_ERROR_STOP=1, giữ exit code. Scripts new-only có collision/target guards và transactions; không rerun tự động trên target đã provision. Không cấp admin/broad grants cho ingestion/BI.

## Quyền và dữ liệu

Trên máy mới, scripts/provision_warehouse.py --help hướng dẫn wrapper có --execute/--approved-sha256. Khi được duyệt, wrapper tạo mật khẩu transform riêng vào .local/dbt/connection.json rồi bật LOGIN; dbt runner đọc private profile này. Không tự điền mật khẩu vào repository, không rerun provisioning để đổi password. BI role đặt password riêng qua psql prompt theo SQL đã review. Các thao tác này chưa được thực thi trong task tài liệu.

retail_ingest không superuser/createdb/createrole/replication/bypassrls; chỉ quyền payload/meta cần thiết, không tự CREATE/DELETE/TRUNCATE. retail_transform đọc Raw/meta, sở hữu warehouse schemas và không được ghi Raw/publication. retail_bi_reader CONNECT, USAGE vàSELECT đúng allowlist, default_transaction_read_only=on; không được Raw/staging/DQ/meta/test access.

Payload datetime2(7) lưu TEXT COLLATE C từ F2 source strings; technical execution timestamps là timestamptz. Raw PK theo run/ordinal, current source keys unique trong capture; không ép archives unique NK. raw_current/raw_publications chỉ phục vụ publication có kiểm soát, không suy SUCCEEDED = certified/published.

## Recovery

Timeout: kiểm Engine/context/container/localhost port trước, không đoán mất dữ liệu từ table list trống. Bootstrap chỉ chạy khi volume/database mới; container init thành công không bảo đảm mọi init script thành công. Có thể dùng scripts/recover_raw_bootstrap.py và scripts/ensure_raw_bind.ps1 theo --help; default preflight, apply cần authorization, backup và kiểm tra collision. Sau lỗi migration phải inspect partial state, không tự chạy lại hoặc mở rộng grants. Không đổi ACL/certificates, source SQL Server hoặc volume ngoài scope.

[Ingestion](../ingestion/README.md), [dbt](../dbt/README.md), [Power BI](../powerbi/README.md). Không chạy load/build để thử hạ tầng.
