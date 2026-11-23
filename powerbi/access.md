# POWERBI-ACCESS-01 — quyền đọc Sales

Ngày kiểm chứng: 2026-11-21. Kết quả: **POWERBI_ACCESS_ACCEPTED**.
Đây là nghiệm thu truy cập PostgreSQL qua psycopg bằng tài khoản BI; chưa kiểm thử giao diện Power BI hoặc tạo report.

## Target và thực thi được phê duyệt

- Container `retail-raw-postgres-1`, image `postgres:18`, PostgreSQL 18.7; database `retail_raw`, `127.0.0.1:55434`, volume `retail-raw_pg_data`. Target đã được xác minh trước thực thi; không đổi container/volume.
- Operator PostgreSQL: `postgres`. [SQL nguyên bản](../infrastructure/postgres/warehouse/provision_bi_reader.sql), SHA256 `c7b71b62991e3ae0a0f7e251b231bafbb2f7edfdb00fec723b63321818139b61`.
- Transaction guard yêu cầu đúng database/operator và role chưa tồn tại. Thực thi bằng `psql -X -q -U postgres -d retail_raw -v ON_ERROR_STOP=1 -f -`, exit code 0. Không chạy lại script này trên role đã tồn tại.
- Tạo NOLOGIN trước, cấp CONNECT, USAGE ba schemas và SELECT đúng 12 objects. Đặt mật khẩu riêng qua `psql \password` bằng stdin không echo, exit 0; sau đó bật LOGIN, exit 0. Mật khẩu không nằm trong SQL, argv, history, output hoặc Git.
- Role `retail_bi_reader`: NOINHERIT, NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOREPLICATION, NOBYPASSRLS; không membership hay sở hữu schema/object. Database default: `default_transaction_read_only=on`; `search_path=pg_catalog,dw_core,sales_marts,dw_intermediate`.

## Objects Power BI được đọc

| Schema | Object | Loại | Rows đã kiểm tra |
|---|---|---|---:|
| dw_core | dim_date | table | 1247 |
| dw_core | dim_customer | table | 663 |
| dw_core | dim_product | table | 227 |
| dw_core | fact_invoice_line | table | 228265 |
| dw_core | fact_order_line | table | 231412 |
| dw_intermediate | int_invoice_header | view | 70510 |
| dw_intermediate | int_order_header | view | 73595 |
| sales_marts | mart_sales_daily | table | 1247 |
| sales_marts | mart_sales_monthly | table | 41 |
| sales_marts | mart_sales_product_daily | table | 141561 |
| sales_marts | mart_customer_sales | table | 66463 |
| sales_marts | mart_sales_customer_summary | table | 663 |

## Runtime acceptance

[Evidence có thể kiểm tra](dashboard-guide.md), [verifier chỉ đọc](../infrastructure/tests/bi_reader_readonly.py).
Lệnh: `.\.venv\Scripts\python.exe -X utf8 infrastructure/tests/bi_reader_readonly.py --execute` từ repository root.
Verifier cần private profiles hiện có, không tự provisioning hoặc đặt lại mật khẩu. Baseline trước provisioning nằm trong ignored `.local/powerbi-access-execution.json`; evidence tracked chứa bản sao fingerprints trước/sau để đối chiếu.

| Kiểm tra | Kết quả |
|---|---|
| TCP password login, current_user/session_user đúng reader | PASS |
| Mật khẩu sai bị authentication từ chối | PASS |
| SELECT thực tế trên 12 objects; tất cả rows đúng version c825b18e-fc62-4cf1-8837-b37b4c9f9668 | PASS |
| Effective INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER false cho cả 12 objects | PASS |
| Schema CREATE, database CREATE/TEMP false; không membership/admin/ownership | PASS |
| Không USAGE/SELECT trên raw, dw_staging, dq, ingestion_meta, dbt_sales_test | PASS |
| SELECT thực tế vào Raw và DQ bị từ chối SQLSTATE 42501 | PASS |
| 17 Raw + 8 metadata + 19 warehouse tables có counts/content digests trước/sau giống nhau | PASS |
| Version records, capture metadata, publication pointer và publication history không đổi | PASS |

Không dùng DML/DDL write probes để kiểm tra quyền; dùng effective ACL từ chính reader. Read-only default là lớp phòng vệ bổ sung, quyền mới là giới hạn truy cập. `public` giữ USAGE có sẵn từ PUBLIC nhưng không có bảng ứng dụng, không CREATE/SELECT; không phát sinh grant ngoài package.
Hai header views dùng quyền owner đối với underlying relations (không phải security_invoker); reader không có quyền trực tiếp trên staging/DQ. Có thể thấy tên/metadata hệ thống PostgreSQL; điều này không cấp SELECT dữ liệu ứng dụng ngoài allowlist.

Kiểm tra ban đầu của verifier đòi chính xác ba schemas USAGE đã bỏ sót USAGE mặc định trên `public`; đã sửa oracle theo privilege thực tế, không thay ACL để làm test pass.

## Nguyên nhân và kết nối Power BI

`retail_ingest` SELECT 0/21 models dbt, không USAGE các schemas dbt; quyền phục vụ ingestion chỉ cho thấy Raw/metadata. `retail_transform` SELECT 21/21 và sở hữu model/schema, có quyền ghi nên không dùng làm BI reader. Đây là phân tách quyền, không phải mất bảng DDS.

- PostgreSQL server: `127.0.0.1:55434`; database: `retail_raw`; Database authentication; username: `retail_bi_reader`.
- Mật khẩu riêng ở `.local/powerbi/connection.json`, được Git ignore; thư mục mới giới hạn ACL cho Windows user hiện tại và SYSTEM. Owner mở file tại máy để nhập vào hộp credential; không đưa nội dung vào chat, console logs hoặc Git. Không dùng mật khẩu của ingest/transform.
- Đổi hoặc xóa credential `retail_ingest` đã lưu cho đúng nguồn này trong Power BI, kết nối lại bằng reader và refresh Navigator. Chọn objects ở bảng trên. Không dùng tài khoản `postgres`/`retail_transform` cho report.
- Chưa kiểm chứng Power BI UI/TLS/refresh qua Gateway; `127.0.0.1` chỉ áp dụng máy local, không phải endpoint Power BI Service. Không tắt TLS hoặc sửa chứng chỉ trong task này.
- Dữ liệu vẫn là development, chưa publish/UNVERIFIED source consistency. Giữ Buyer/Bill-to, grain, date basis theo [KPI Catalog](../docs/requirements/kpi-definitions/wwi-kpi-candidate-catalog.md). Không join các facts/marts khác grain để cộng doanh số.

## Đề xuất dbt grants — snapshot ACCESS-01, đã triển khai qua ACCESS-02

Tại thời điểm ACCESS-01 chưa có model grants trong `dbt/dbt_project.yml`. Đề xuất dưới đây đã được Owner phê duyệt qua POWERBI-ACCESS-02 và kiểm chứng runtime sau controlled rebuild; xem [kết quả hiện hành](persistent-grants.md). Table/view materialization của dbt có thể thay object; manual grants không bảo đảm tồn tại sau rebuild. Cấu hình giữ nguyên schema/materialization hiện hữu:

```yaml
models:
  retail_sales:
    core:
      dim_date:
        +grants: {select: [retail_bi_reader]}
      dim_customer:
        +grants: {select: [retail_bi_reader]}
      dim_product:
        +grants: {select: [retail_bi_reader]}
      fact_invoice_line:
        +grants: {select: [retail_bi_reader]}
      fact_order_line:
        +grants: {select: [retail_bi_reader]}
    intermediate:
      int_invoice_header:
        +grants: {select: [retail_bi_reader]}
      int_order_header:
        +grants: {select: [retail_bi_reader]}
    marts:
      mart_sales_daily:
        +grants: {select: [retail_bi_reader]}
      mart_sales_monthly:
        +grants: {select: [retail_bi_reader]}
      mart_sales_product_daily:
        +grants: {select: [retail_bi_reader]}
      mart_customer_sales:
        +grants: {select: [retail_bi_reader]}
      mart_sales_customer_summary:
        +grants: {select: [retail_bi_reader]}
```

Không dùng schema-wide/default grants cho tất cả bảng hoặc grants cho staging/DQ/test/future models. ACCESS-01 không sửa dbt hoặc chạy rebuild; ACCESS-02 đã áp dụng riêng đúng 12 model grants và xác minh reader/pin sau rebuild theo authorization mới. Không chạy ingestion/publish. SALES-04 và các parent phases không tự động hoàn thành.
