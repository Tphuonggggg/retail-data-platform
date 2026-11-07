# Project Scope

## Trạng thái

Chủ dự án đã quyết định **WideWorldImporters (WWI) trên SQL Server là nguồn OLTP chính** và **PostgreSQL là Data Warehouse do dự án tự xây dựng**. Đây là phạm vi mục tiêu đã duyệt, không phải bằng chứng pipeline đã triển khai. Phase 0 đã `Completed`; Phase 1–9 chưa được bắt đầu. Các quyết định nghiệp vụ và schema ở mục Open Decisions chưa được chốt.

## Mục tiêu và kiến trúc

Pipeline dự kiến: SQL Server WWI (**chỉ đọc**) → Python ingestion → PostgreSQL raw/staging → dbt/SQL transformations → PostgreSQL Data Warehouse → analytical data marts → Power BI. Apache Airflow điều phối; data quality, reconciliation và monitoring hoạt động xuyên suốt. Docker Compose phục vụ môi trường local khi được triển khai; BigQuery chỉ là phần mở rộng.

MVP gồm **Sales/Invoicing, Customer Analytics và Inventory Movements**. Hoàn thiện **Sales end-to-end** từ ingestion đến warehouse, Airflow, data quality, monitoring và mart/report trước khi mở rộng Customer rồi Inventory. Purchasing, Finance và BigQuery cần scope/task riêng. Giữ cấu trúc repository và các module Data Engineering dùng chung.

## Functional Requirements dự kiến

| ID | Yêu cầu | Acceptance criteria dự kiến |
| --- | --- | --- |
| FR01 | Đọc WWI bằng quyền chỉ đọc theo source contract | Bảng/cột/khóa và quyền được ghi; không DDL/DML trên WWI gốc. |
| FR02 | Full load vào PostgreSQL raw/staging | Batch ID, source table, extracted_at, row count và đối soát khóa/số dòng. |
| FR03 | Incremental load với watermark/checkpoint | Quy tắc theo bảng và tie-breaker được duyệt; INSERT/UPDATE end-to-end chỉ thử trong môi trường độc lập được phê duyệt; không tuyên bố nguồn gốc đã thay đổi nếu chưa quan sát. |
| FR04 | Idempotent upsert, retry/backfill và recovery | Rerun không tạo duplicate trái quy tắc; checkpoint không tiến khi batch lỗi; backfill khoảng thời gian chọn và test khôi phục có bằng chứng. |
| FR05 | Validation, quarantine và cleaning | Record không hợp lệ có lý do; raw giữ dấu vết; không âm thầm sửa nguồn. |
| FR06 | Warehouse/star schema đúng grain | Fact/dimension và measures theo schema đã duyệt; không double count khi kết hợp order, invoice, transaction và stock movement. |
| FR07 | SCD Type 2 có giới hạn bằng chứng | Chỉ áp dụng cho thuộc tính/history được duyệt; khoảng hiệu lực và lookup as-of được kiểm thử. |
| FR08 | Data quality và reconciliation | Kiểm tra cơ bản từ ingestion/warehouse gồm unique, not null, relationships, accepted values và business rules được duyệt; count/amount/quantity đối soát cùng grain, kỳ và population. |
| FR09 | Airflow orchestration, logging/monitoring | Sales DAG theo dependency, retry và recovery; batch/task được truy vết. |
| FR10 | Data marts và Power BI | Sales rồi Customer rồi Inventory Movements; KPI có định nghĩa, nguồn, test đối soát và cách dùng nhất quán trong semantic/reporting layer. |

## Business và data boundaries

- `Sales.Orders`, `Sales.OrderLines`, `Sales.Invoices`, `Sales.InvoiceLines` và `Sales.CustomerTransactions` có grain/ý nghĩa khác nhau. Chưa chốt fact chính hoặc quy tắc revenue/tax.
- Customer analytics phải phân biệt `CustomerID` và `BillToCustomerID` theo KPI được duyệt.
- Inventory Movements dùng `Warehouse.StockItemTransactions` theo loại nghiệp vụ; current holdings không tự chứng minh lịch sử tồn cuối ngày.
- Temporal history chỉ hỗ trợ SCD2 ở bảng và khoảng lịch sử đã kiểm chứng, không mặc định bao phủ mọi giao dịch.
- Kiểm tra chất lượng cơ bản bắt đầu ở Phase 3–4. Phase 6 tập trung quality gates, monitoring tập trung và failure scenarios nâng cao.
- WWI gốc luôn chỉ đọc. Không dùng CDC trong phương án hiện hành; chưa bật Change Tracking. Phương án môi trường thử nghiệm độc lập cho incremental chỉ được thiết kế ở WWI-04, chưa tạo clone hoặc DML.

## Out of Scope và extensions

MVP không gồm returns/refunds chi tiết, campaign attribution, streaming, Kafka/Flink/Hadoop cluster/Kubernetes, machine learning, payment gateway thật hay frontend web application hoàn chỉnh. Purchasing, Finance và BigQuery là phần mở rộng có kiểm soát; chúng không chặn nghiệm thu MVP local. Không tự thêm dependency hoặc thay đổi technology stack.

## Non-functional Requirements và Definition of Done dự kiến

- **Tái lập local:** tài liệu phải nêu cách chuẩn bị WWI làm nguồn read-only và các điều kiện truy cập/restore hợp lệ bên ngoài repository; cấu hình dự án qua `.env.example`, Docker Compose cho các service phù hợp, phiên bản dependency được phê duyệt và runbook. Không commit backup WWI để chứng minh tái lập.
- **Bảo mật:** quyền đọc tối thiểu trên WWI; secret qua environment variables hoặc cơ chế được duyệt; không commit credentials, backup, bản trích xuất chứa dữ liệu nguồn hoặc dữ liệu nhạy cảm. Quyền phân phối/demo dữ liệu được xem xét trước khi công khai repository.
- **Quan sát:** batch ID, row counts, duration, error type và trạng thái task phải truy vết được; cảnh báo và hướng dẫn khôi phục được kiểm thử khi triển khai.
- **Kiểm thử:** unit, integration và end-to-end phù hợp từng phase; kiểm thử rerun, checkpoint, lỗi giữa batch, SCD2 trong phạm vi history có bằng chứng, reconciliation và failure recovery. Không dùng dữ liệu WWI gốc làm nơi tiêm lỗi.
- **Hiệu năng và tối ưu truy vấn:** đo full/incremental load và các truy vấn warehouse; xem execution plan phù hợp từng engine. Chỉ đề xuất/chỉnh index hoặc partition trên PostgreSQL đích sau khi schema được duyệt; không tối ưu bằng cách sửa WWI gốc. Chỉ ghi cải thiện khi có số đo trước/sau cùng điều kiện.
- **CI và portfolio:** sau khi có Git và code, chạy kiểm tra phù hợp bằng GitHub Actions; báo cáo số liệu, dashboard, DAG run và benchmark chỉ khi có bằng chứng. MVP local có thể tái lập và nghiệm thu độc lập với BigQuery.
- **Cloud extension:** nếu BigQuery được duyệt sau này, xác định quota/budget, quyền truy cập và đối soát với local trước khi tuyên bố triển khai.

Definition of Done cho **MVP triển khai** là một người khác có thể chuẩn bị nguồn WWI theo hướng dẫn, cấu hình môi trường hợp lệ, chạy pipeline local, xem kết quả kiểm thử/đối soát và giải thích grain/KPI/SCD2. Điều này không phải tiêu chí hoàn thành Phase 0 tài liệu.

## Open Decisions

| Nhóm | Quyết định chưa chốt | Gate |
| --- | --- | --- |
| KPI | Revenue recognition, tax treatment, invoice date hay delivery date, invoice chưa xác nhận giao | WWI-03 |
| Customer | `CustomerID` so với `BillToCustomerID` trong facts/KPI | WWI-02/03 |
| Warehouse | Grain, tên fact/dimension, source-to-target mapping, profit/COGS và ý nghĩa `LineProfit` | WWI-03 trước schema |
| SCD2 | Thuộc tính, hiệu lực `ValidFrom`/`ValidTo`, as-of và độ phủ history | WWI-02/04 |
| Incremental | Watermark/tie-breaker, delete, replay, môi trường thử nghiệm độc lập | WWI-04 |
| Inventory | Có cần daily balance không; opening balance và đối soát movements | Trước inventory mart |
| Data quality | Eligibility, ngưỡng, mức cảnh báo/chặn batch và ngoại lệ nguồn | WWI-03/04 |
| Git publication | Quyền phân phối dữ liệu, license và chính sách công khai repository trước khi tạo remote/push | Chủ dự án quyết định trước publish |

## Change control

Chỉ chủ dự án phê duyệt business rules, schema, công nghệ, phase và nghiệm thu. Các tài liệu cũ không còn là yêu cầu hiện hành. Không coi tài liệu là bằng chứng database, ingestion, dbt, DAG hoặc dashboard đã hoạt động. Xem [ADR chuyển nguồn](docs/adr/wwi-source-migration.md), [ROADMAP.md](ROADMAP.md) và [TASKS.md](TASKS.md).
