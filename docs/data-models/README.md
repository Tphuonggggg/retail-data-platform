# data-models

## 1. Overview

Tài liệu khảo sát và thiết kế dữ liệu nguồn WWI thuộc [docs](../README.md). Không chứa schema hoặc pipeline đã triển khai.

## 2. Purpose

Ghi metadata, profile, quan hệ nguồn và source contracts làm đầu vào cho các quyết định sau này.

## 3. Scope

Chín bảng MVP thuộc Sales/Invoicing, Customer và Inventory; Purchasing chỉ là dependency ở các phép đối soát đã nêu. KPI, fact/dimension và incremental policy chưa được phê duyệt.

## 4. Responsibilities

Phân biệt constraint nguồn với snapshot quan sát, ghi SQL evidence và giới hạn suy luận; dẫn chiếu cột/datatype về dictionary, không duy trì bản sao trùng chức năng.

## 5. Inputs

SQL Server WWI chỉ đọc, [PROJECT_SCOPE.md](../../PROJECT_SCOPE.md), [TASKS.md](../../TASKS.md) và quyết định của Project Owner.

## 6. Outputs

- Phase 1.1: [database inventory](wwi-database-inventory.md), [metadata dictionary](wwi-metadata-dictionary.md), [temporal/index assessment](wwi-temporal-index-assessment.md), [metadata queries](wwi-metadata-queries.md), [assessment](wwi-phase-1-1-assessment.md).
- Phase 1.2: [profiling tổng hợp](wwi-data-profiling.md), [Sales](wwi-sales-profiling.md), [Customer/temporal](wwi-customer-temporal-profiling.md), [Inventory/integrity](wwi-inventory-integrity-profiling.md), [profiling SQL](wwi-profiling-queries.md), [assessment](wwi-phase-1-2-assessment.md).
- Phase 1.3: [relationships](wwi-source-relationships.md), [source ERD](wwi-source-erd.md), [business data flow](wwi-business-data-flow.md), [relationship SQL](wwi-relationship-validation-sql.md), [assessment](wwi-phase-1-3-assessment.md).
- Phase 1.4: [source contracts](wwi-source-contracts.md), [extraction matrix](wwi-extraction-requirements-matrix.md), [assessment](wwi-phase-1-4-assessment.md); [raw requirements](../requirements/wwi-raw-layer-requirements.md) và [validation matrix](../requirements/wwi-source-validation-matrix.md) thuộc requirements.

## 7. Dependencies

Metadata Dictionary và profiling trước relationship contract; relationship contract trước source contracts. Các quyết định WWI-03/04 cần phê duyệt riêng trước schema/pipeline.

## 8. Technology

Markdown, Mermaid và SQL Server `SELECT`/catalog queries để khảo sát. PostgreSQL warehouse là mục tiêu dự án, chưa có object từ module này.

## 9. Folder Structure

Thư mục này lưu README và các tài liệu `wwi-*.md` theo phase; không chứa dữ liệu nguồn hoặc code.

## 10. Execution

Các truy vấn đọc/tái kiểm chứng nằm trong tài liệu SQL tương ứng. Không có lệnh chạy module hay extraction trong repository: Not implemented yet.

## 11. Tasks

WWI-02 `DONE` ở mức source design; Phase 1.4 được nghiệm thu ở mức tài liệu. Theo dõi [TASKS.md](../../TASKS.md).

## 12. Testing Strategy

Đối chiếu SQL evidence với metadata/profile, kiểm link Markdown, rà secret/diff và nêu rõ câu nào chỉ là Proposed. Kiểm thử ingestion/warehouse: Not implemented yet.

## 13. Acceptance Criteria

Mỗi kết luận quan trọng có evidence hoặc nhãn Unverified/Proposed; đủ chín bảng MVP ở Phase 1.4; không giả định KPI, SCD2, incremental hay daily balance chưa duyệt.

## 14. Current Status

Phase 1.1–1.4 được Project Owner chấp thuận trong phạm vi từng phần; WWI-02 `DONE` ở mức source design. Runtime: Not implemented yet.
