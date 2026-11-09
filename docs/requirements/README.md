# requirements

## 1. Overview

Tài liệu yêu cầu thuộc [docs](../README.md); các tài liệu Phase 1.4 hiện ở mức đề xuất.

## 2. Purpose

Ghi yêu cầu nghiệp vụ/kỹ thuật cần được phê duyệt trước thiết kế và triển khai.

## 3. Scope

BRD/KPI definitions theo task sau; Phase 1.4 chỉ mô tả raw layer và validation/reconciliation requirements cho chín bảng WWI MVP.

## 4. Responsibilities

Phân biệt yêu cầu nguồn đã kiểm chứng, yêu cầu sau ingestion chưa chạy và business rules còn mở; liên kết đến evidence ở `data-models`.

## 5. Inputs

[PROJECT_SCOPE.md](../../PROJECT_SCOPE.md), [Metadata Dictionary](../data-models/wwi-metadata-dictionary.md), [source contracts](../data-models/wwi-source-contracts.md), profiling/relationship evidence và quyết định của Project Owner.

## 6. Outputs

[Raw Layer Requirements](wwi-raw-layer-requirements.md) và [Source Validation Matrix](wwi-source-validation-matrix.md). KPI definitions và BRD chi tiết: Not implemented yet.

## 7. Dependencies

WWI-02 source contracts là đầu vào; WWI-03/04 quyết định business rules, incremental và SCD2 trước các quality gates tương ứng.

## 8. Technology

Markdown; dẫn chiếu SQL Server metadata/SELECT evidence. Không có PostgreSQL object trong module.

## 9. Folder Structure

Thư mục lưu README và các tài liệu yêu cầu `wwi-*.md`; không chứa dữ liệu nguồn hoặc code.

## 10. Execution

Tài liệu để review, không có lệnh chạy ingestion hay validation runtime: Not implemented yet.

## 11. Tasks

Phase 1.4 thuộc WWI-02 đã được Project Owner nghiệm thu ở mức tài liệu; WWI-02 `DONE`. [TASKS.md](../../TASKS.md) là tracker.

## 12. Testing Strategy

Kiểm liên kết, nguồn evidence, phạm vi và trạng thái quyết định; kiểm thử raw/ingestion chỉ thực hiện ở phase triển khai: Not implemented yet.

## 13. Acceptance Criteria

Raw metadata và validation matrix tách rõ Verified/Proposed, grain và owner decisions; không mô tả kiểm tra chưa chạy như đã PASS.

## 14. Current Status

Phase 1.4 được nghiệm thu ở mức tài liệu; chức năng nghiệp vụ và pipeline: Not implemented yet.
