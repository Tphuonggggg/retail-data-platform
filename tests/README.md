# tests

## 1. Overview
Module **kiểm thử xuyên module**. Status: Not Implemented. Not implemented yet.

## 2. Purpose
Tổ chức unit, integration và end-to-end tests cho pipeline WWI → PostgreSQL.

## 3. Scope
Sales trước; Customer và Inventory Movements sau khi Sales end-to-end được review.

## 4. Responsibilities
Kiểm chứng contracts, full/incremental, idempotency, grain, SCD2, quality gates và recovery.

## 5. Inputs
Source contract, ingestion, warehouse, orchestration và KPI definitions đã duyệt.

## 6. Outputs
Kết quả test/reports có bằng chứng, không phải benchmark giả.

## 7. Dependencies
data-sources, ingestion, transformation, orchestration, analytics.

## 8. Technology Stack
pytest, dbt tests và SQL validation; công cụ cụ thể chỉ được dùng khi task triển khai phê duyệt.

## 9. Directory Structure
- [integration/](integration/README.md)
- [e2e/](e2e/README.md)

## 10. Planned Workflow
Chuẩn bị môi trường thử nghiệm tách biệt → chạy pipeline → so nguồn/đích → báo lỗi. Không thực hiện INSERT/UPDATE trên WWI gốc. Chưa có lệnh test.

## 11. Development Tasks
WWI-07, WWI-08, WWI-09/10 và WWI-16. Theo dõi [TASKS.md](../TASKS.md).

## 12. Testing Strategy
Full/rerun, incremental trong môi trường độc lập đã duyệt, SCD2 temporal có giới hạn, SQL connectivity/permission/query failure, partial batch failure và reconciliation.

## 13. Acceptance Criteria
Tests quan trọng chạy được và có kết quả thực tế; giới hạn bằng chứng incremental được ghi rõ.

## 14. Current Status
Chưa có test code hoặc kết quả kiểm thử. Not implemented yet.