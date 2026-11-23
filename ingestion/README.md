# Python Ingestion

## Nguồn, hợp đồng và môi trường

SQL Server WideWorldImporters chỉ SELECT, Windows Authentication qua current development account. Source allowlist11 objects nằm trong common/contracts.py: Sales.Customers/Orders/OrderLines/Invoices/InvoiceLines/CustomerTransactions, Warehouse.StockItems/StockItemHoldings/StockItemTransactions và hai physical archives Customers_Archive/StockItems_Archive. Chín current tables có PK; archives không được ép unique NK, giữ duplicates và zero-duration history.

Contract chứa ordered projection, SQL types, NULL policy và F2 source expression. Giữ datetime2(7) dưới dạng chuỗi27ký tự/None, không qua Python datetime làm representation chuẩn; giữ Decimal, Unicode, NULL/rỗng, binary/geography. Fixture tests/fixtures/source_dictionary.json giữ kỳ vọng độc lập156 current columns; tests/fixtures/f2_expression.json giữ F2 chuẩn. Không tạo schema tự động từ inferred data.

Các biến cấu hình từ .env.example: WWI_SQLSERVER_HOST/DATABASE/AUTH_MODE, ENCRYPT/TRUST_SERVER_CERTIFICATE, WWI_BATCH_SIZE/LOGIN_TIMEOUT/QUERY_TIMEOUT; RAW_PG_HOST/PORT/DATABASE/USER/PASSWORD/SSLMODE. APP_ENV=development mới cho opt-in trust/admin đã duyệt; không fallback credential, không đổi source grants/certificates. Password chỉ trong private config. Target mặc định retail_raw/127.0.0.1:55434/retail_ingest; admin password chỉ cho provisioning riêng.

## Full Load

```powershell
.venv\Scripts\python.exe -m ingestion.full_load plan --all
.venv\Scripts\python.exe -m ingestion.full_load preflight --all --env-file .env
.venv\Scripts\python.exe -m ingestion.full_load load --all --run-id <new-uuid> --execute --env-file .env
.venv\Scripts\python.exe -m ingestion.full_load reconcile --all --run-id <uuid> --env-file .env
```

Kiểm tra --help và exit code sau từng lệnh; load chỉ sau authorization phù hợp. Một immutable candidate chứa source-shaped payload và metadata/audits; counts, distinct keys, numeric/NULL controls và typed digest phải đối soát. Known zero khác unknown NULL. SUCCEEDED không tự là published/source-consistent. --run-id là invocation pin; không tráo với capture_id metadata hoặc fallback latest.

## Incremental snapshot-diff

Mỗi lần chạy vẫn **đọc toàn bộ sáu nguồn** Customers/Orders/OrderLines/Invoices/InvoiceLines/StockItems rồi so sánh parent state, chỉ ghi target delta cho INSERT/UPDATE; không phải timestamp-watermark hoặc CDC. UNCHANGED ghi counters. Live source chưa có coherent snapshot proof: absence phải STOP, không suy DELETE từ partial scan. DELETE chỉ được chứng minh bằng fixture adapter có boundary kiểm soát, không có CLI mở live DELETE.

```powershell
.venv\Scripts\python.exe -m ingestion.incremental plan
.venv\Scripts\python.exe -m ingestion.incremental preflight --parent-id <validated-parent-uuid>
.venv\Scripts\python.exe -m ingestion.incremental run --parent-id <validated-parent-uuid> --version-id <new-uuid> --execute
.venv\Scripts\python.exe -m ingestion.incremental inspect --version-id <uuid>
.venv\Scripts\python.exe -m ingestion.incremental reconcile --version-id <uuid>
```

## Identity, transaction và recovery

incremental_versions ghi parent/root/depth, frozen contract/algorithm, status và boundary; events ghi key/type/before-version và hashes. raw.delta_* giữ typed payload; sales_state_*(uuid) resolve đúng ancestor chain. Không copy full payload cho no-change. Chain tối đa32; compaction chưa triển khai. Projection ordinal là technical identity, không join trực tiếp vào base theo ordinal.

Sáu nguồn và delta/events/reconciliation/VALIDATED nằm trong một transaction. Lỗi rollback payload/events, lưu FAILED riêng; triggers bảo vệ terminal states. Unknown COMMIT phải inspect/read-back, không retry ghi mù. Same successful UUID chỉ reconcile/read-back; parent/contract khác bị từ chối. FAILED/RUNNING không bị overwrite; dùng UUID mới cho lần đọc nguồn mới. Retry Full Load là new-capture retry, không phải replay sealed chunks. Không TRUNCATE/overwrite để rerun.

acknowledged_publication_id vẫn NULL theo protocol; candidate progress khác publication ACK. Không tự advance source checkpoint hoặc raw_current. Source system-time không tự là business-effective time.

## Kiểm tra và lỗi thường gặp

scripts/run_checks.py chạy regression offline; tests/integration ở root giữ các verifier/failure fixtures cần --execute riêng, không phải lệnh vận hành mặc định. Source permission/TLS sai: dừng, không bypass hoặc cấp quyền tự động. PostgreSQL timeout: kiểm Docker Engine/đúng container/port; không xóa volume. Missing objects: kiểm provisioning và target, không tự DDL. Reconciliation/contract mismatch: giữ ID/evidence private, không sửa rules để vượt gate. Xem [infrastructure](../infrastructure/README.md), [dbt](../dbt/README.md).
