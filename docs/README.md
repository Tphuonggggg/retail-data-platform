# docs
## 1. Overview
Module **Tài liệu yêu cầu và thiết kế**. Kiến trúc và ADR WWI đã được ghi ở mức tài liệu; source contract chi tiết và runtime chưa triển khai.

## 2. Purpose
Lưu requirements, architecture, data models, ADR và runbooks.

## 3. Scope
Lưu requirements, architecture, data models, ADR và runbooks.

## 4. Responsibilities
Ghi nguồn gốc yêu cầu, quyết định, mapping và hướng dẫn vận hành.

## 5. Inputs
Yêu cầu và quyết định của chủ dự án, cùng bằng chứng triển khai sau này.

## 6. Outputs
Tài liệu có version, liên kết tới quyết định và task.

## 7. Dependencies
PROJECT_SCOPE.md, ROADMAP.md, phản hồi chủ dự án.

## 8. Technology Stack
Markdown, Mermaid.

## 9. Directory Structure
- [`requirements/`](requirements/README.md) — xem trách nhiệm và trạng thái của thư mục.
- [`architecture/`](architecture/README.md) — xem trách nhiệm và trạng thái của thư mục.
- [`data-models/`](data-models/README.md) — xem trách nhiệm và trạng thái của thư mục.
- [`adr/`](adr/README.md) — xem trách nhiệm và trạng thái của thư mục.
- [`runbooks/`](runbooks/README.md) — xem trách nhiệm và trạng thái của thư mục.

## 10. Planned Workflow
Yêu cầu → quyết định → thiết kế → kiểm chứng → cập nhật runbook. Hướng dẫn thực thi: chưa có lệnh chạy; sẽ bổ sung sau khi triển khai.

## 11. Development Tasks
Chốt business rules Phase 1 và bổ sung tài liệu theo từng phase. Theo dõi ID và trạng thái tại [TASKS.md](../TASKS.md).

## 12. Testing Strategy
Rà liên kết, tính nhất quán và đối chiếu tài liệu với bằng chứng thực tế. Chưa có kiểm thử pipeline vì runtime chưa triển khai.

## 13. Acceptance Criteria
Không trình bày thành phần planned như implemented.

## 14. Current Status
Tài liệu kiến trúc và ADR WWI đã có; [Phase 1.1](data-models/wwi-phase-1-1-assessment.md), [Phase 1.2](data-models/wwi-phase-1-2-assessment.md), [Phase 1.3](data-models/wwi-phase-1-3-assessment.md), [Phase 1.4](data-models/wwi-phase-1-4-assessment.md) và [Phase 1.5](requirements/wwi-phase-1-5-assessment.md) đã được chấp thuận ở mức tài liệu. WWI-02/03 `DONE`; KPI business definitions được duyệt, physical warehouse và pipeline chưa triển khai. Kết quả kiểm thử chức năng: Not implemented yet.

## Owner closure và checkpoint được phép

Phase 0 **Completed**; Phase 1 **Completed — Requirements & Source Design**; WWI-02/03 **DONE**, WWI-04 **DONE — Design**. DW-01/02/03A/03B/03C **DONE — Design**; DW-04 **DONE — Design Acceptance**. Phase 2 **IN_PROGRESS — Authorized**, giới hạn WWI-05/M1A **IN_PROGRESS — Authorized**; WWI-05 chưa hoàn tất. M2 trở đi và Phase 3–9 **Not Started**. Production modules **Not implemented yet**; chỉ B9 isolated PoC có evidence lịch sử. [Approval record](architecture/wwi-phase-1-closure-approval.md). Runtime source/target readiness được kiểm ở M1A sau Checkpoint A commit, không suy từ design acceptance.
