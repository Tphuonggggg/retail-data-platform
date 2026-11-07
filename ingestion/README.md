# ingestion

## 1. Overview
Module **nạp dữ liệu batch từ WWI SQL Server**. Status: Not Implemented. Not implemented yet.

## 2. Purpose
Extract theo quyền chỉ đọc, nạp PostgreSQL raw/staging và quản lý checkpoint/idempotency.

## 3. Scope
Sales/Invoicing trước; Customer Analytics và Inventory Movements sau Sales end-to-end.

## 4. Responsibilities
Sở hữu extractors, loaders, checkpoints, retry và batch metadata; không định nghĩa KPI hoặc sửa nguồn WWI.

## 5. Inputs
WWI source contract, quyền đọc, cấu hình môi trường và quyết định incremental WWI-04.

## 6. Outputs
Raw/staging records, batch metadata, checkpoint, quarantine/error records có thể truy vết.

## 7. Dependencies
data-sources, storage, infrastructure, docs/requirements và quyết định WWI-02/03/04.

## 8. Technology Stack
Python 3.12, SQL Server nguồn và PostgreSQL đích. Driver/connector cụ thể chưa được duyệt.

## 9. Directory Structure
- [extractors/](extractors/README.md)
- [loaders/](loaders/README.md)
- [checkpoints/](checkpoints/README.md)
- [common/](common/README.md)

## 10. Planned Workflow
Full extract Sales → kiểm tra kỹ thuật → ghi raw/staging → đối soát → commit checkpoint. Incremental và thử INSERT/UPDATE end-to-end chỉ theo chiến lược/môi trường độc lập được duyệt. Chưa có lệnh chạy.

## 11. Development Tasks
WWI-06/07; theo dõi [TASKS.md](../TASKS.md).

## 12. Testing Strategy
Unit/integration cho full, rerun, watermark tie-breaker, partial failure và recovery; kiểm tra dữ liệu nguồn chỉ đọc.

## 13. Acceptance Criteria
Rerun an toàn, checkpoint đúng, record lỗi có lý do, count/keys đối soát được và WWI gốc không đổi.

## 14. Current Status
Chưa có extractor, loader hoặc kết quả kiểm thử. Not implemented yet.