# storage

## 1. Overview
Module **Phân lớp dữ liệu**. [Raw foundation](raw/README.md) đã runtime verified/MVP-G02 DONE. Typed payload/control/view SQL đã Owner-approved execution/runtime verified, RAW_PAYLOAD_PROVISIONING_PASS; actual ingestion chưa chạy. Warehouse/staging runtime Not implemented yet.

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
- [`staging/`](README.md) — xem trách nhiệm và trạng thái của thư mục.
- [`warehouse/`](README.md) — xem trách nhiệm và trạng thái của thư mục.

## 10. Planned Workflow
Raw lưu dấu vết → staging chuẩn hóa → warehouse phục vụ phân tích. [Full Load code/runbook](../ingestion/README.md) đã có; Raw schema/grants đã Owner-approved provisioning/runtime verified, payload capture/publication chưa chạy. Actual ingestion cần Owner giao riêng; không suy schema PASS thành Full Load acceptance.

## 11. Development Tasks
Định nghĩa schema/storage contracts khi vào phase tương ứng. Theo dõi ID và trạng thái tại [TASKS.md](../TASKS.md).

## 12. Testing Strategy
Kiểm tra keys/constraints/lineage và đối soát nguồn. [Raw README](raw/README.md) có foundation runtime evidence và offline suites; source-to-Raw payload reconciliation runtime chưa chạy. WWI-06A có mock integration tests, không thay engine verification.

## 13. Acceptance Criteria
Mỗi layer có grain/ownership rõ, không có dữ liệu sai âm thầm.

## 14. Current Status
Raw foundation verified/MVP-G02 DONE. Payload/control/views đã provision/runtime verified; Python loader chỉ Implemented/Offline Tested, chưa chạy real load; persisted sealed-chunk/attempt replay, staging/Core **Not implemented yet**. Không coi hai metadata nền hoặc code-only PASS là complete operational Raw protocol.


## MVP-RESET-01 consolidation

Future-only submodule READMEs ?? h?p nh?t v? ??y; ch?a c? implementation trong c?c th? m?c k? ho?ch ??. Xem [roadmap](../ROADMAP.md). Kh?ng t?o placeholder code; t?o module con khi c? task tri?n khai th?c t?.
