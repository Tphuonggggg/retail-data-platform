# kpi-definitions

## 1. Overview

Tài liệu định nghĩa KPI thuộc [analytics](../README.md). Phase 1.5 đã được Project Owner phê duyệt ở mức business rules; KPI runtime chưa triển khai.

## 2. Purpose

Ghi công thức, grain, date basis, filters, giới hạn và bằng chứng nguồn để ra quyết định KPI.

## 3. Scope

Sales/Invoicing, Customer Analytics và Inventory Movements trong MVP; Purchasing/Finance chuyên sâu ngoài phạm vi hiện tại.

## 4. Responsibilities

Phân biệt Approved Business Rule với Verified source arithmetic và test warehouse chưa thực hiện; tránh fan-out/double counting.

## 5. Inputs

[Source Contracts](../../docs/data-models/wwi-source-contracts.md), [Business Requirements](../../docs/requirements/wwi-business-requirements.md), profile/relationship evidence và quyết định Project Owner.

## 6. Outputs

[KPI Catalog](wwi-kpi-candidate-catalog.md) và [KPI Verification SQL](wwi-kpi-verification-sql.md). Business definitions được duyệt ở mức tài liệu; semantic model: Not implemented yet.

## 7. Dependencies

WWI-02 source design và WWI-03 business rules đã nghiệm thu ở mức tài liệu; WWI-04 SCD2/incremental chưa bắt đầu.

## 8. Technology

Markdown và SQL Server `SELECT` read-only để kiểm arithmetic nguồn. PostgreSQL/Power BI là công nghệ kế hoạch, chưa hoạt động ở module này.

## 9. Folder Structure

Thư mục chứa README và hai tài liệu `wwi-*.md`; không chứa code, extract hoặc dashboard.

## 10. Execution

Các câu SQL kiểm chứng nằm trong tài liệu SQL; không có lệnh chạy KPI pipeline: Not implemented yet.

## 11. Tasks

WWI-03/Phase 1.5 `DONE` ở mức tài liệu. Xem [TASKS.md](../../TASKS.md).

## 12. Testing Strategy

Kiểm công thức nguồn bằng SELECT ở grain nguồn, đối soát count/amount/quantity, phân biệt các KPI chưa đủ dữ liệu. Test warehouse/dashboard: Not implemented yet.

## 13. Acceptance Criteria

Mỗi KPI Core/Optional có formula, source/grain/date/filter/unit, double-count/DQ risk, scope class, approval và verification status; source SQL không chứng minh accounting semantics hoặc warehouse test.

## 14. Current Status

22 KPI IDs đã phân lớp: 12 Core, 5 Optional, 2 Deferred, 3 Unsupported. Business definitions được duyệt; mart, Power BI: Not implemented yet.
