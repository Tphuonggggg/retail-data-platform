# requirements

## 1. Overview

Tài liệu yêu cầu thuộc [docs](../README.md). Phase 1.4 và 1.5 đã được nghiệm thu ở mức tài liệu.

## 2. Purpose

Ghi yêu cầu nghiệp vụ/kỹ thuật cần được phê duyệt trước thiết kế và triển khai.

## 3. Scope

Phase 1.4 mô tả raw layer và validation/reconciliation requirements; Phase 1.5 phân tích business requirements/questions, KPI candidates và Open Decisions cho ba subject areas MVP.

## 4. Responsibilities

Phân biệt yêu cầu nguồn đã kiểm chứng, yêu cầu sau ingestion chưa chạy và business rules còn mở; liên kết đến evidence ở `data-models`.

## 5. Inputs

[PROJECT_SCOPE.md](../../PROJECT_SCOPE.md), [Metadata Dictionary](../data-models/wwi-metadata-dictionary.md), [source contracts](../data-models/wwi-source-contracts.md), profiling/relationship evidence và quyết định của Project Owner.

## 6. Outputs

[Raw Layer Requirements](wwi-raw-layer-requirements.md), [Source Validation Matrix](wwi-source-validation-matrix.md), [Business Requirements](wwi-business-requirements.md), [Business Questions](wwi-business-questions-use-cases.md), [Business Rules Matrix](wwi-business-rules-decision-matrix.md) và [Phase 1.5 Assessment](wwi-phase-1-5-assessment.md). KPI business definitions đã duyệt; runtime: Not implemented yet.

## 7. Dependencies

WWI-02 source contracts là đầu vào; WWI-03/04 quyết định business rules, incremental và SCD2 trước các quality gates tương ứng.

## 8. Technology

Markdown; dẫn chiếu SQL Server metadata/SELECT evidence. Không có PostgreSQL object trong module.

## 9. Folder Structure

Thư mục lưu README và các tài liệu yêu cầu `wwi-*.md`; không chứa dữ liệu nguồn hoặc code.

## 10. Execution

Tài liệu để review, không có lệnh chạy ingestion hay validation runtime: Not implemented yet.

## 11. Tasks

Phase 1.4/WWI-02 và Phase 1.5/WWI-03 đã được nghiệm thu ở mức tài liệu; cả hai `DONE`. [TASKS.md](../../TASKS.md) là tracker.

## 12. Testing Strategy

Kiểm liên kết, nguồn evidence, phạm vi và trạng thái quyết định; kiểm thử raw/ingestion chỉ thực hiện ở phase triển khai: Not implemented yet.

## 13. Acceptance Criteria

Raw metadata và validation matrix tách rõ Verified/Proposed, grain và owner decisions; không mô tả kiểm tra chưa chạy như đã PASS.

## 14. Current Status

Phase 1.4/1.5 được nghiệm thu ở mức tài liệu. Pipeline và warehouse runtime: Not implemented yet.
