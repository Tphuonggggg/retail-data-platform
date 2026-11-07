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
Tài liệu kiến trúc và ADR WWI đã có; [Phase 1.1](data-models/wwi-phase-1-1-assessment.md) được chấp thuận về nội dung, [Phase 1.2 profiling](data-models/wwi-phase-1-2-assessment.md) được nghiệm thu về mặt khảo sát. Phase 1.3 được phép thực hiện. WWI source contract/KPI chi tiết chưa được duyệt. Pipeline và kết quả kiểm thử chức năng: Not implemented yet.
