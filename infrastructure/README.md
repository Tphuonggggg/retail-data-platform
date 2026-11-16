# infrastructure

## 1. Overview
Module **môi trường thực thi cho nguồn WWI chỉ đọc và warehouse PostgreSQL**. Status: Not Implemented. Not implemented yet.

## 2. Purpose
Quản lý cấu hình local/cloud theo phase mà không đưa credentials vào repository.

## 3. Scope
SQL Server WWI là nguồn OLTP local; PostgreSQL là raw/staging/warehouse đích. Docker Compose dự kiến quản lý các thành phần dự án local; BigQuery là extension.

## 4. Responsibilities
Tách cấu hình môi trường khỏi logic dữ liệu; kiểm soát biến môi trường, quyền truy cập và bảo mật kết nối.

## 5. Inputs
Yêu cầu runtime, source contract, quyền đọc WWI và cấu hình môi trường qua biến môi trường.

## 6. Outputs
Hướng dẫn và cấu hình local/cloud theo phase được duyệt.

## 7. Dependencies
data-sources, storage, orchestration và yêu cầu bảo mật.

## 8. Technology Stack
SQL Server nguồn; PostgreSQL đích; Docker/Docker Compose và BigQuery ở phase tương ứng.

## 9. Directory Structure
- [docker/](docker/README.md)
- [local/](local/README.md)
- [cloud/](cloud/README.md)

## 10. Planned Workflow
Xác minh nguồn read-only → thiết kế local → kiểm tra tái lập → chỉ xét cloud theo task riêng. Chưa có lệnh chạy.

## 11. Development Tasks
WWI-05 cho môi trường local; WWI-15 cho BigQuery nếu được duyệt. Theo dõi [TASKS.md](../TASKS.md).

## 12. Testing Strategy
Kiểm tra quyền đọc, kết nối, khởi động và tái lập môi trường khi có service; không sửa WWI gốc.

## 13. Acceptance Criteria
Môi trường tái lập được, không commit secret, nguồn giữ quyền chỉ đọc.

## 14. Current Status
M1A đã kiểm environment/driver/Docker/Compose và phân loại target; xem [Environment Report](../docs/architecture/wwi-m1a-environment-readiness.md), [Secure Contract](../docs/architecture/wwi-secure-connection-contract.md), [Evidence](../docs/architecture/wwi-m1a-gate-evidence.md), [Handoff](../docs/architecture/wwi-m1a-handoff.md). Native PG service có nhưng Raw target chưa approved/verified, B9 không dùng lại. Chưa có project Compose/bootstrap/physical Raw; operational BLOCKED, WWI-05 IN_PROGRESS. Runtime module Not implemented yet.
