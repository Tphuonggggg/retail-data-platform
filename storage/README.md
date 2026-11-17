# storage

## 1. Overview
Module **Phân lớp dữ liệu**. Raw namespace/run tracking [bootstrap](raw/README.md) đã PREPARED/OFFLINE TESTED; storage runtime/payload/warehouse Not implemented yet.

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
Raw lưu dấu vết → staging chuẩn hóa → warehouse phục vụ phân tích. Foundation bootstrap/startup instructions tại [raw](raw/README.md), execution cần Owner runtime authority; chưa có ingestion hoặc serving publication.

## 11. Development Tasks
Định nghĩa schema/storage contracts khi vào phase tương ứng. Theo dõi ID và trạng thái tại [TASKS.md](../TASKS.md).

## 12. Testing Strategy
Kiểm tra keys/constraints/lineage và đối soát nguồn. Foundation có offline SQL-contract/Compose/config tests tại [Raw README](raw/README.md); chưa có PostgreSQL execution hoặc source-to-Raw reconciliation runtime.

## 13. Acceptance Criteria
Mỗi layer có grain/ownership rõ, không có dữ liệu sai âm thầm.

## 14. Current Status
Raw foundation prepared/offline tested. Payload tables, capture/batch/chunk/publication ledger, staging/Core và actual SQL execution **Not implemented yet**; không coi metadata invocation tables là complete Raw protocol.
