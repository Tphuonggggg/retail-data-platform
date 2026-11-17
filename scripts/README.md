# scripts

## 1. Overview
Module **Lệnh hỗ trợ dự án**. [Raw checker](check_raw_connection.py) PREPARED/OFFLINE TESTED; actual connection NOT RUN.

## 2. Purpose
Chứa script vận hành chỉ khi có nhu cầu và được giao.

## 3. Scope
Chứa script vận hành chỉ khi có nhu cầu và được giao.

## 4. Responsibilities
Lệnh bootstrap/demo/maintenance nhỏ, không gom business logic module khác.

## 5. Inputs
Cấu hình môi trường và tác vụ được duyệt.

## 6. Outputs
Lệnh có hướng dẫn và đầu ra kiểm tra được.

## 7. Dependencies
Các module liên quan theo từng script.

## 8. Technology Stack
Python 3.12 hoặc shell phù hợp khi được duyệt.

## 9. Directory Structure
- [check_raw_connection.py](check_raw_connection.py): đọc environment/optional dotenv, offline config validation hoặc explicit readonly Raw probe; không ingestion/schema writes.
- [recover_raw_bootstrap.py](recover_raw_bootstrap.py): recovery A cho đúng Raw container/volume; default preflight-only, `--apply` là database mutation cần Owner authorize riêng. Không reset/recreate resources hoặc log credentials. [Exact commands/limits](../infrastructure/docker/README.md#bootstrap-failure-và-recovery-a).

## 10. Planned Workflow
Raw checker: từ root chạy `.\.venv\Scripts\python.exe scripts/check_raw_connection.py --env-file .env --check-config` để chỉ kiểm config. Bỏ `--check-config` là database connection, chỉ chạy khi Owner authorize runtime. [Raw instructions](../infrastructure/docker/README.md) có target/roles/TLS boundaries.

## 11. Development Tasks
WWI-05 Raw foundation; WWI-06 ingestion là task kế tiếp, chưa triển khai. Theo dõi [TASKS.md](../TASKS.md).

## 12. Testing Strategy
Kiểm config thiếu/placeholder/secrets/target sai, offline mode không gọi probe và sanitized exception output tại [offline suite](../tests/raw_foundation_static.py). Không runtime writes.

## 13. Acceptance Criteria
Mỗi script có mục đích và cách dùng rõ, không thao tác phá hủy mặc định.

## 14. Current Status
Checker/config implemented và offline tested; actual Raw connection, startup/persistence và ingestion NOT RUN. Existing local Python3.12/psycopg3.3.9 dùng lại; không install dependency.
