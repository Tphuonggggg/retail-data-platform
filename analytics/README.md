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
- [data-marts/](data-marts/README.md)
- [powerbi/](powerbi/README.md)
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
Chưa có mart, KPI definition được duyệt hoặc report. Not implemented yet.