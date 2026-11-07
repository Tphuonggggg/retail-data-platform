# .github

## 1. Overview
Module **Quy trình cộng tác và CI**. Status: Not Implemented. Not implemented yet.

## 2. Purpose
Chứa tài liệu về workflow và issue template cho GitHub khi đến phase phù hợp.

## 3. Scope
Chứa tài liệu về workflow và issue template cho GitHub khi đến phase phù hợp.

## 4. Responsibilities
Quy trình repository và tự động kiểm tra; không chứa logic pipeline.

## 5. Inputs
Tài liệu quy trình, task tracker và quyết định kiểm thử.

## 6. Outputs
Workflow/issue template trong các phase sau.

## 7. Dependencies
TASKS.md, test strategy từ các module.

## 8. Technology Stack
GitHub, GitHub Actions.

## 9. Directory Structure
- [`workflows/`](workflows/README.md) — xem trách nhiệm và trạng thái của thư mục.
- [`ISSUE_TEMPLATE/`](ISSUE_TEMPLATE/README.md) — xem trách nhiệm và trạng thái của thư mục.

## 10. Planned Workflow
Định nghĩa quy trình review, sau đó thêm CI khi có code cần kiểm tra. Hướng dẫn thực thi: chưa có lệnh chạy; sẽ bổ sung sau khi triển khai.

## 11. Development Tasks
Viết hướng dẫn cộng tác; xác định bộ test tối thiểu cho CI. Theo dõi ID và trạng thái tại [TASKS.md](../TASKS.md).

## 12. Testing Strategy
Kiểm tra cấu hình workflow bằng run thử và đối chiếu kết quả test khi được triển khai. Hướng dẫn kiểm thử: chưa có lệnh test vì module chưa triển khai.

## 13. Acceptance Criteria
Workflow không lộ secret và báo đúng trạng thái kiểm thử.

## 14. Current Status
Status: Not Implemented. Not implemented yet. Chưa có chức năng hoặc kết quả kiểm thử.
