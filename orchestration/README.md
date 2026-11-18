# orchestration

## 1. Overview
Module **Điều phối workflow**. Status: Not Implemented. Not implemented yet.

## 2. Purpose
Tổ chức DAG, schedule, dependency, retry và recovery.

## 3. Scope
Tổ chức DAG, schedule, dependency, retry và recovery.

## 4. Responsibilities
Sở hữu lịch chạy và thứ tự task; không chứa logic ETL chi tiết.

## 5. Inputs
Lệnh/tác vụ ingestion, transformation, data quality.

## 6. Outputs
DAG runs, task states và tín hiệu lỗi.

## 7. Dependencies
ingestion, transformation, data-quality, monitoring.

## 8. Technology Stack
Apache Airflow.

## 9. Directory Structure
- [`dags/`](README.md) — xem trách nhiệm và trạng thái của thư mục.
- [`plugins/`](README.md) — xem trách nhiệm và trạng thái của thư mục.

## 10. Planned Workflow
Chạy ingestion → transformation → kiểm tra chất lượng → ghi trạng thái. Hướng dẫn thực thi: chưa có lệnh chạy; sẽ bổ sung sau khi triển khai.

## 11. Development Tasks
Xây DAG và runbook ở Phase 5 sau khi các tác vụ độc lập chạy được. Theo dõi ID và trạng thái tại [TASKS.md](../TASKS.md).

## 12. Testing Strategy
Thử retry, dependency, backfill và partial failure. Hướng dẫn kiểm thử: chưa có lệnh test vì module chưa triển khai.

## 13. Acceptance Criteria
DAG chạy đúng thứ tự, có thể phục hồi an toàn.

## 14. Current Status
Status: Not Implemented. Not implemented yet. Chưa có chức năng hoặc kết quả kiểm thử.


## MVP-RESET-01 consolidation

Future-only submodule READMEs ?? h?p nh?t v? ??y; ch?a c? implementation trong c?c th? m?c k? ho?ch ??. Xem [roadmap](../ROADMAP.md). Kh?ng t?o placeholder code; t?o module con khi c? task tri?n khai th?c t?.
