# tests

## 1. Overview
Module **kiểm thử xuyên module**. Isolated [B9 precision PoC](integration/b9_precision/README.md) đã Implemented/Tested cho source→Python→PG candidate transport/persistence. Production/pipeline integration và end-to-end suites: Not implemented yet.

## 2. Purpose
Tổ chức unit, integration và end-to-end tests cho pipeline WWI → PostgreSQL.

## 3. Scope
Sales trước; Customer và Inventory Movements sau khi Sales end-to-end được review.

## 4. Responsibilities
Kiểm chứng contracts, full/incremental, idempotency, grain, SCD2, quality gates và recovery.

## 5. Inputs
Source contract, ingestion, warehouse, orchestration và KPI definitions đã duyệt.

## 6. Outputs
Kết quả test/reports có bằng chứng, không phải benchmark giả.

## 7. Dependencies
data-sources, ingestion, transformation, orchestration, analytics.

## 8. Technology Stack
pytest, dbt tests và SQL validation; công cụ cụ thể chỉ được dùng khi task triển khai phê duyệt.

## 9. Directory Structure
- [source_security_static.py](source_security_static.py): explicit offline text-contract tests,no DB connection hoặcSQL execution.
- [integration/](integration/README.md)
- [e2e/](e2e/README.md)

## 10. Planned Workflow
Workflow pipeline dự kiến: môi trường tách biệt → chạy pipeline → so nguồn/đích → báo lỗi. Chưa triển khai pipeline tests. B9 dùng project-local ignored venv và unittest/SELECT-only; commands ở README PoC. Không thực hiện INSERT/UPDATE trên WWI gốc.

## 11. Development Tasks
WWI-07, WWI-08, WWI-09/10 và WWI-16. Theo dõi [TASKS.md](../TASKS.md).

## 12. Testing Strategy
Full/rerun, incremental trong môi trường độc lập đã duyệt, SCD2 temporal có giới hạn, SQL connectivity/permission/query failure, partial batch failure và reconciliation.

## 13. Acceptance Criteria
Tests quan trọng chạy được và có kết quả thực tế; giới hạn bằng chứng incremental được ghi rõ.

## 14. Current Status
Isolated B9 SQL→Python→PostgreSQL candidate proof:12 offline methods,source14/169/18,PG parameters14/persisted15/new-session ordering169/equality14/range5 PASS. B9 Approved — Physical Raw Temporal Representation;DW-03A DONE — Design, runtime gates pending; full ingestion/SCD2/Raw/production suites Not implemented yet.


## Prepared source-security static checks

M1B-OD03 cho phépstandard-library offline tests đối với[prepared SQL package](../data-sources/security/README.md).12 tests PASS cho disabled/NULL-safe authority guards,allowlist/archives,quoting,batch isolation,read-only verification vàunsafe-mutation rejection. Tests chỉđọc files/mutate strings trongmemory,khôngimportDBdriver/subprocess/executeSQL;khôngregisteradminSQL vàoCI,migration hoặctest discovery. Không compiler/formal verification.

Chạy riêng:
```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
./.venv/Scripts/python.exe -m unittest discover -s tests -p 'source_security_static.py' -v
```
SQL setup/verify/window tests và72 inherited runtime scenarios vẫnNOT RUN;B9 evidence không đổi.
