# analytics

## 1. Overview
Module **phục vụ phân tích WWI**. Status: Not Implemented. Not implemented yet.

## 2. Purpose
Định nghĩa KPI, data marts và Power BI cho MVP.

## 3. Scope
Sales/Invoicing trước; Customer Analytics và Inventory Movements sau. Purchasing/Finance chỉ là extensions.

## 4. Responsibilities
Sở hữu lớp tiêu thụ dữ liệu và định nghĩa metric được duyệt; không sửa warehouse facts.

## 5. Inputs
Warehouse PostgreSQL đã kiểm tra, source lineage và business definitions WWI-03.

## 6. Outputs
Sales, Customer, Inventory Movements marts và Power BI report.

## 7. Dependencies
storage, transformation, data-quality và decisions WWI-02/03/04.

## 8. Technology Stack
SQL, Power BI.

## 9. Directory Structure
- [data-marts/](README.md)
- [powerbi/](README.md)
- [kpi-definitions/](kpi-definitions/README.md)

## 10. Planned Workflow
Warehouse → mart → kiểm tra KPI → Power BI. Chưa có lệnh chạy.

## 11. Development Tasks
WWI-11 Sales; WWI-12 Customer; WWI-13 Inventory. Theo dõi [TASKS.md](../TASKS.md).

## 12. Testing Strategy
Đối chiếu KPI với công thức, date basis, grain và reconciliation được duyệt.

## 13. Acceptance Criteria
Báo cáo dùng metric có định nghĩa và dữ liệu đã kiểm tra; không JOIN fact khác grain gây double count.

## 14. Current Status
Phase 1.5 đã ghi [KPI definitions](kpi-definitions/wwi-kpi-candidate-catalog.md) và [SQL evidence](kpi-definitions/wwi-kpi-verification-sql.md); BRD-01–BRD-12 và định nghĩa nghiệp vụ được Project Owner duyệt. Chưa có mart, KPI runtime hoặc report. Not implemented yet.


## MVP-RESET-01 consolidation

Future-only submodule READMEs ?? h?p nh?t v? ??y; ch?a c? implementation trong c?c th? m?c k? ho?ch ??. Xem [roadmap](../ROADMAP.md). Kh?ng t?o placeholder code; t?o module con khi c? task tri?n khai th?c t?.
