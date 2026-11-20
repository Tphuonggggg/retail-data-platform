# Ph?m vi MVP

Owner MVP-RESET-01,2026-11-19: ?u ti?n Sales/Invoicing end-to-end tr?n SQL Server WWI ? Python ? PostgreSQL Raw ? dbt staging/core/marts ? Power BI. Airflow l? milestone sau; BigQuery optional.

## Acceptance MVP

1. Extract SELECT-only v? n?p Raw theo batch/COPY.
2. ??i so?t count/digest v? business measures c?ng grain; repeatable execution/transaction rollback/basic logs.
3. dbt staging, dimensional DW v? ?t nh?t m?t Sales Mart, Power BI dashboard, basic DQ.
4. Kh?ng thay ngu?n, kh?ng commit secrets; runtime results c? evidence.

## Hi?n tr?ng

Phase0/1 ho?n th?nh thi?t k?. Raw foundation v?11 payload/4 controls/11 views ?? provision/verified. Python Full Load Implemented/Offline Tested; ingestion th?t NOT RUN. dbt/DW/marts/Airflow/Power BI ch?a tri?n khai.

## Business contracts gi? nguy?n

Buyer CustomerID kh?c BillToCustomerID; order/header v? invoice/line kh?c grain. Invoiced Sales Before Tax=SUM(ExtendedPrice?TaxAmount), theo InvoiceDate, kh?ng recognized revenue. Order metrics theo OrderDate. Kh?ng suy payment allocation, refunds, daily inventory balance ho?c official COGS. Xem [KPI](docs/requirements/kpi-definitions/wwi-kpi-candidate-catalog.md), [source contracts](docs/data-models/wwi-source-contracts.md), [DW design](docs/data-models/wwi-logical-dw-design.md).

## ?i?u ch?nh acceptance k? thu?t

Current Windows account ???c ph?p; selected-object checks thay global all11 security audit. Development trust bypass c?n explicit config; admin account c?n explicit opt-in. Dedicated account/ACL/staging/manifests/security audit kh?ng MVP gates. SELECT-only, parameterization, target validation v? rollback v?n b?t bu?c.

Historical SCD2/incremental/full publication/recovery designs ???c gi? cho milestones sau, kh?ng gi? ?? implement ho?c silently ??i existing publication semantics. Ch?a cho ph?p ingestion runtime trong reset. [L?ch s?](docs/archive/pre-reset/README.md).
# Cập nhật triển khai và ownership — 2026-11-20

Business scope/BRD/KPI/grains giữ nguyên. Full Load đã được nghiệm thu ngày 2026-11-19 cho unpublished capture 5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8; những dòng “ingestion NOT RUN” bên dưới là snapshot trước runtime, được thay bằng [bằng chứng hiện hành](ingestion/README.md#ingest-010203--runtime-acceptance-2026-11-19). dbt/DW/marts chưa được nghiệm thu; chỉ có draft được bảo toàn. [Ownership và paths mới](README.md#cấu-trúc-theo-pipeline-stage) không thay kiến trúc hoặc cho phép runtime mới. REPO-STRUCTURE-02 chỉ structural refactor; kiểm lại Raw hiện BLOCKED do Docker Engine unavailable.

## DBT-SALES-01 — cập nhật runtime ngày 2026-11-20

Sales staging, DQ/quarantine, 3 dimensions, 2 headers, 2 facts và 5 Sales marts/derived summaries đã triển khai và runtime verified theo [runbook](dbt/README.md). Không thay BRD/KPI/grain logical đã duyệt: customer mart giữ date/customer/role; summary một customer/role là derived summary dưới dạng table riêng. Historical SCD2/registry chưa runtime implement; facts giữ U/NK/reason và separate observed-current references. Không recognized revenue/COGS/refunds/payment allocation. Capture vẫn unpublished/UNVERIFIED; không tự chuyển phase hoặc triển khai Power BI/Airflow/domain khác. Ghi chú draft/NOT RUN trước đây là snapshot lịch sử được supersede về trạng thái runtime này.
