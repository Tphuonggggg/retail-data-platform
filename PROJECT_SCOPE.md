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

Buyer CustomerID kh?c BillToCustomerID; order/header v? invoice/line kh?c grain. Invoiced Sales Before Tax=SUM(ExtendedPrice?TaxAmount), theo InvoiceDate, kh?ng recognized revenue. Order metrics theo OrderDate. Kh?ng suy payment allocation, refunds, daily inventory balance ho?c official COGS. Xem [KPI](analytics/kpi-definitions/wwi-kpi-candidate-catalog.md), [source contracts](docs/data-models/wwi-source-contracts.md), [DW design](docs/data-models/wwi-logical-dw-design.md).

## ?i?u ch?nh acceptance k? thu?t

Current Windows account ???c ph?p; selected-object checks thay global all11 security audit. Development trust bypass c?n explicit config; admin account c?n explicit opt-in. Dedicated account/ACL/staging/manifests/security audit kh?ng MVP gates. SELECT-only, parameterization, target validation v? rollback v?n b?t bu?c.

Historical SCD2/incremental/full publication/recovery designs ???c gi? cho milestones sau, kh?ng gi? ?? implement ho?c silently ??i existing publication semantics. Ch?a cho ph?p ingestion runtime trong reset. [L?ch s?](docs/archive/pre-reset/README.md).
