# transformation

## 1. Overview
Module **biến đổi dữ liệu WWI thành warehouse PostgreSQL**. Status: Not Implemented. Not implemented yet.

## 2. Purpose
Dùng dbt/SQL để xây dimensions, facts và business logic đã được duyệt.

## 3. Scope
Sales/Invoicing trước; Customer Analytics và Inventory Movements theo thứ tự MVP.

## 4. Responsibilities
Sở hữu models, grain, mapping nguồn–đích và SCD Type 2 trong phạm vi history hợp lệ; không sửa dữ liệu WWI.

## 5. Inputs
PostgreSQL staging, source contracts và định nghĩa KPI/business rules đã duyệt.

## 6. Outputs
Warehouse facts/dimensions và dbt docs/tests.

## 7. Dependencies
storage, docs/requirements, data-quality; quyết định WWI-02/03/04.

## 8. Technology Stack
dbt Core, SQL, PostgreSQL.

## 9. Directory Structure
- [dbt/](dbt/README.md)
- [sql/](sql/README.md)

## 10. Planned Workflow
Staging → dimensions/facts → kiểm tra grain/relationships → reconciliation. Chưa có lệnh chạy.

## 11. Development Tasks
WWI-08 Sales, WWI-12 Customer, WWI-13 Inventory. Theo dõi [TASKS.md](../TASKS.md).

## 12. Testing Strategy
dbt/SQL tests cho unique, not null, relationships, no fan-out, KPI và SCD2 as-of theo source history được duyệt.

## 13. Acceptance Criteria
Fact/dim đúng grain, KPI không double count, lịch sử dimension chỉ khẳng định trong phạm vi có bằng chứng.

## 14. Current Status
Chưa có dbt project, SQL model hoặc kết quả kiểm thử. Not implemented yet.