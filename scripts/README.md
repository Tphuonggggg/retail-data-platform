# scripts

## 1. Overview
Module **Lệnh hỗ trợ dự án**. Raw checker và foundation đã verified/MVP-G02 DONE. WWI-06B có source SELECT-only diagnostics; không ingestion hoặc privileged remediation runtime.

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
- [inspect_wwi_source.py](inspect_wwi_source.py): default offline help; `--execute` cho strict TLS/Integrated SELECT-only metadata/PK/temporal/own permissions; `--samples` thêm TOP(1) codec sample/object, `--holdings-profile` thêm small-table count/NULL/numeric/F2 aggregates. `--history-permissions` riêng WWI-06C yêu cầu actual Windows wwi_extract trước connect và SQL login/SID/user/target khớp sau connect; không kết hợp samples/holdings-profile. Đọc all11 rights và metadata/own-token grants của đúng hai history/parent pairs; output SQL/parameters/results hoặc sanitized NOT_VERIFIED. Exit0/2 chỉ collection complete/partial, không gate approval. Không password/Raw config cần thiết, không full source dump, row values hoặc writes. PC chỉ DBA metadata ở mode cũ, không được thay extractor ở history mode. [WWI-06C evidence/commands](../ingestion/README.md#wwi-06c--history-permission-investigation-2026-11-18).
- [recover_raw_bootstrap.py](recover_raw_bootstrap.py): recovery A cho đúng Raw container/volume; default preflight-only, `--apply` là database mutation cần Owner authorize riêng. Không reset/recreate resources hoặc log credentials. [Exact commands/limits](../infrastructure/docker/README.md#bootstrap-failure-và-recovery-a).

## 10. Planned Workflow
Raw checker: từ root chạy `.\.venv\Scripts\python.exe scripts/check_raw_connection.py --env-file .env --check-config` để chỉ kiểm config. Bỏ `--check-config` là database connection, chỉ chạy khi Owner authorize runtime. [Raw instructions](../infrastructure/docker/README.md) có target/roles/TLS boundaries.

## 11. Development Tasks
WWI-05 Raw foundation verified; WWI-06A code/offline đã có, WWI-06B readiness được giao; Full Load runtime chưa được phép. Theo dõi [TASKS.md](../TASKS.md).

## 12. Testing Strategy
Kiểm config thiếu/placeholder/secrets/target sai, offline mode không gọi probe và sanitized exception output tại [Raw suite](../tests/raw_foundation_static.py). [Full Load/readiness suite](../tests/full_load_offline.py) kiểm source diagnostics default-offline/11-object schema drift/read-only projections/current-context permission reporting và recovery runId; history mode có regression cho PC rejection trước connect, wrong SQL identity, exact permission matrix và denied metadata/no-secret output. Không runtime writes.

## 13. Acceptance Criteria
Mỗi script có mục đích và cách dùng rõ, không thao tác phá hủy mặc định.

## 14. Current Status
Checker/foundation runtime verified theo evidence Phase A; source helper đã read-only metadata/11 TOP(1)/small holdings profile dưới PC trong WWI-06B, không dedicated least-privilege approval. WWI-06C Python collector Implemented/Offline Tested; actual Python launch chưa truy cập được base interpreter trong PC profile. Independent actual wwi_extract PowerShell/ODBC subset verified27/30 queries, fresh TLS reconnect fail; không production preflight PASS hoặc permission exception. [Evidence/limitations](../ingestion/README.md#wwi-06c--history-permission-investigation-2026-11-18). Không ingestion/source DDL/grant/certificate mutation ở WWI-06C. Existing local Python3.12/pyodbc5.5.0/psycopg3.3.9 dùng lại; không install dependency.
