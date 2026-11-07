# data-sources

## 1. Overview

Module **WWI OLTP source contract**. Database `WideWorldImporters` trên SQL Server local là nguồn chính, truy cập **chỉ đọc**. Status của module trong repository: Not Implemented. Not implemented yet.

## 2. Purpose

Xác định ranh giới nguồn, quyền truy cập, bảng/cột/khóa và metadata cần cho ingestion. Không sở hữu business transformation hoặc warehouse.

## 3. Scope

MVP theo thứ tự Sales/Invoicing, Customer Analytics, Inventory Movements. Purchasing và Finance là extensions chỉ khi được phê duyệt.

## 4. Responsibilities

WWI-02 tạo source contract và data dictionary có bằng chứng metadata. Các bảng dự kiến khảo sát gồm `Sales.Orders`, `Sales.OrderLines`, `Sales.Invoices`, `Sales.InvoiceLines`, `Sales.Customers`, `Sales.CustomerTransactions`, `Warehouse.StockItems` và `Warehouse.StockItemTransactions`. Đây là danh sách khảo sát, chưa phải hợp đồng triển khai đã chốt.

## 5. Inputs

Database WWI local và quyền đọc được cấp riêng; không lưu credentials trong repository.

## 6. Outputs

Source contracts cho ingestion: grain, PK/FK, timestamps, nullable fields, temporal coverage, exception rules và phạm vi full/incremental được duyệt.

## 7. Dependencies

[Scope](../PROJECT_SCOPE.md), WWI-02/03/04, infrastructure cho kết nối an toàn. Không có source generator dependency.

## 8. Technology Stack

SQL Server là nguồn OLTP; Python/SQL sẽ đọc theo contract khi triển khai. PostgreSQL là đích của ingestion/warehouse, không phải nguồn WWI.

## 9. Directory Structure

Thư mục này chỉ giữ README điều hướng; dữ liệu WWI nằm trong SQL Server local, không được sao chép vào repository trong WWI-01.

## 10. Planned Workflow

Xác minh metadata bằng truy vấn chỉ đọc → đề xuất contract → owner review → ingestion ở phase được cho phép. Không có lệnh chạy module trong repository.

## 11. Development Tasks

WWI-02 source contract, WWI-05 kết nối, WWI-06/07 ingestion. Theo dõi [TASKS.md](../TASKS.md).

## 12. Testing Strategy

Kiểm tra schema/keys/quan hệ và quyền đọc; về sau kiểm tra extraction count, watermark và reconciliation. Không sửa dữ liệu WWI gốc.

## 13. Acceptance Criteria

Contract đúng bảng/cột/grain đã kiểm chứng; quyền đọc tối thiểu và không đưa dữ liệu/secret nguồn vào repository.

## 14. Current Status

Database WWI local đã được khảo sát read-only trong assessment. Chưa có source adapter, contract WWI hoàn chỉnh hoặc pipeline được kiểm thử trong repository. Not implemented yet.