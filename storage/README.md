# storage

## 1. Overview
Module **Phân lớp dữ liệu**. [Raw foundation](raw/README.md) đã runtime verified/MVP-G02 DONE. WWI-06A typed payload/control/view SQL đã prepared/offline tested, chưa apply. Warehouse/staging runtime Not implemented yet.

## 2. Purpose
Định nghĩa ranh giới raw, staging và warehouse.

## 3. Scope
Định nghĩa ranh giới raw, staging và warehouse.

## 4. Responsibilities
Sở hữu hợp đồng lưu trữ, metadata và mô hình dữ liệu đích; không điều phối job.

## 5. Inputs
Dữ liệu từ ingestion, models từ transformation.

## 6. Outputs
Raw/staging/warehouse và metadata theo thiết kế được duyệt.

## 7. Dependencies
ingestion, transformation, docs/data-models.

## 8. Technology Stack
PostgreSQL local; BigQuery ở Phase 8; Parquet khi cần.

## 9. Directory Structure
- [`raw/`](raw/README.md) — xem trách nhiệm và trạng thái của thư mục.
- [`staging/`](staging/README.md) — xem trách nhiệm và trạng thái của thư mục.
- [`warehouse/`](warehouse/README.md) — xem trách nhiệm và trạng thái của thư mục.

## 10. Planned Workflow
Raw lưu dấu vết → staging chuẩn hóa → warehouse phục vụ phân tích. [Full Load code/runbook](../ingestion/README.md) đã có; payload/publication runtime chưa chạy và provisioning cần Owner giao riêng. Không suy code offline PASS thành operational acceptance.

## 11. Development Tasks
Định nghĩa schema/storage contracts khi vào phase tương ứng. Theo dõi ID và trạng thái tại [TASKS.md](../TASKS.md).

## 12. Testing Strategy
Kiểm tra keys/constraints/lineage và đối soát nguồn. [Raw README](raw/README.md) có foundation runtime evidence và offline suites; source-to-Raw payload reconciliation runtime chưa chạy. WWI-06A có mock integration tests, không thay engine verification.

## 13. Acceptance Criteria
Mỗi layer có grain/ownership rõ, không có dữ liệu sai âm thầm.

## 14. Current Status
Raw foundation verified/MVP-G02 DONE. Payload/control/view SQL và Python loader Implemented/Offline Tested nhưng chưa provision/chạy; persisted sealed-chunk/attempt replay, staging/Core **Not implemented yet**. Không coi hai metadata nền hoặc code-only PASS là complete operational Raw protocol.
