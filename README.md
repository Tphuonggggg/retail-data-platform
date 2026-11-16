# Retail Data Platform & Analytics Warehouse

## Project Overview

Dự án portfolio Data Engineering dùng **WideWorldImporters (WWI) trên SQL Server** làm nguồn OLTP **chỉ đọc**, xây Data Warehouse riêng trên PostgreSQL và phục vụ Power BI. Phase 0 **Completed** ở mức tài liệu/cấu trúc; Phase 1.1–1.5 đã được chấp thuận ở mức tài liệu, WWI-02/03 `DONE`, Phase 1.6/WWI-04 IN_PROGRESS; DW-01 DONE ở mức thiết kế logic, DW-02 DONE; DW-02A/B DONE; DW-02C/D DONE ở mức thiết kế; DW-02E DONE — B1–B8 Approved — Logical Policy và design acceptance/QA đạt ngày 2026-11-15. Chưa có pipeline của dự án chạy được. [Scope](PROJECT_SCOPE.md), [Roadmap](ROADMAP.md), [Tasks](TASKS.md).

## Business Problems and MVP

Dữ liệu order, invoice, customer transaction và stock movement có grain/ý nghĩa khác nhau. Báo cáo cần phân biệt đặt hàng, xuất hóa đơn, thu tiền và biến động hàng để tránh đếm trùng và đối soát được. MVP gồm **Sales/Invoicing, Customer Analytics, Inventory Movements**; hoàn thiện Sales end-to-end trước. Purchasing, Finance và BigQuery chỉ là extensions có kiểm soát. BRD-01–BRD-12 đã được duyệt ở mức nghiệp vụ; [KPI Catalog](analytics/kpi-definitions/wwi-kpi-candidate-catalog.md) phân loại KPI MVP và loại trừ. DW-01 fact/dimension grains và DW-02 B1–B8 logical policies đã duyệt; physical design, incremental algorithms và numerical quality thresholds còn pending.

## Planned Architecture

`SQL Server WWI (read-only) → Python ingestion → PostgreSQL raw/staging → dbt/SQL → PostgreSQL warehouse → data marts → Power BI`. Airflow điều phối; quality/reconciliation, logging/monitoring và failure recovery xuyên suốt. Kiểm tra cơ bản bắt đầu từ ingestion/warehouse; Phase 6 bổ sung quality gates và failure nâng cao. Xem [system overview](docs/architecture/system-overview.md) và [data flow](docs/architecture/data-flow.md).

## Technology Stack

Python 3.12, SQL Server nguồn, PostgreSQL đích, SQL, dbt Core, Apache Airflow, Docker Compose, pytest, Power BI và GitHub Actions là stack dự kiến theo phase. BigQuery là extension. Chưa cài hoặc cấu hình runtime của dự án trong repository; dịch vụ local tồn tại không chứng minh pipeline đã chạy. Không tự thêm package/framework.

## Module Overview

| Module | Vai trò dự kiến |
| --- | --- |
| `.github` | Cộng tác và CI khi có Git/code |
| `docs` | Requirements, architecture, data models, ADR, runbooks |
| `infrastructure` | Cấu hình local/cloud theo phase |
| `data-sources` | WWI source contract và quyền đọc |
| `ingestion` | Full/incremental extract, load, checkpoint, retry |
| `storage` | Raw, staging, warehouse PostgreSQL |
| `transformation` | dbt/SQL facts, dimensions và SCD2 theo quyết định |
| `orchestration` | Airflow DAGs |
| `data-quality` | Validation, quarantine, reconciliation |
| `analytics` | Marts, KPI, Power BI |
| `monitoring` | Logs, metrics, alerts |
| `tests` | Unit, integration và end-to-end |
| `scripts` | Lệnh hỗ trợ theo task cụ thể |

## Folder Structure and Status

Mỗi module hiện có README điều hướng; cấu trúc giữ lại để tái sử dụng. Chưa có Python ingestion, PostgreSQL schema của dự án, dbt project, Airflow DAG, Docker Compose, Power BI report, BigQuery deployment hoặc test result. Git repository local đã được khởi tạo trong P0-06; không có remote hoặc push. Đối chiếu trạng thái ở [TASKS.md](TASKS.md).

## Getting Started (planned)

Hiện chưa có lệnh chạy dự án. Sau khi source contract, kết nối, schema và quyền được duyệt, các phase triển khai sẽ bổ sung hướng dẫn cấu hình từ `.env.example`, nạp dữ liệu, kiểm thử và khôi phục. WWI gốc luôn chỉ đọc; môi trường thử nghiệm INSERT/UPDATE cho incremental phải độc lập và được duyệt trước khi tạo.

## Documentation Navigation

[Quy tắc AI](AGENTS.md) · [Scope](PROJECT_SCOPE.md) · [Roadmap](ROADMAP.md) · [Tasks](TASKS.md) · [Architecture](docs/architecture/README.md) · [Migration ADR](docs/adr/wwi-source-migration.md) · [Changelog](CHANGELOG.md).

## DW-03B Stage 2 — 2026-11-16

**DW-03B DONE — Design**, INC-01–INC-06 **Approved — Logical Policy** theo conditional design acceptance/QA của Owner. [Specification](docs/data-models/wwi-dw-03b-incremental-design-proposal.md), [Register](docs/data-models/wwi-dw-03b-decision-register.md), [Assessment](docs/data-models/wwi-dw-03b-assessment.md) và [Runtime gates](docs/data-models/wwi-dw-03b-work-plan.md). Mục tiêu Current-State Convergence trên verified consistent source state; không full CDC/intermediate-event guarantee. Full comparison vẫn đọc full source. Numeric/physical/runtime details pending, IT01–IT21 NOT RUN, production pipeline Not implemented yet. DW-03A/B9 approvals giữ nguyên; DW-03C/DW-04 TODO, WWI-04/Phase 1 IN_PROGRESS. Không tự triển khai task tiếp.
