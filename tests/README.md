# tests

## Current Local MVP Checks

[raw_provisioning_readonly.py](raw_provisioning_readonly.py) kiểm initial empty Raw provisioning:15 new tables/11 views,248 columns, PK/UNIQUE/FK/CHECK/indexes, owners/exact ACL và pointer; expected definitions lấy từ approved SQL, CHECK deparse được so AST để giữ Boolean precedence. Bốn offline unit tests chạy bằng `unittest discover -s tests -p raw_provisioning_readonly.py -v`; mặc định CLI không network. `python tests/raw_provisioning_readonly.py --verify --env-file .env` chỉ SELECT qua retail_ingest/default_transaction_read_only=on, cần runtime read-only authorization. Không provisioning/load/source connection; row-count0 contract chỉ dùng trước ingestion, không là monitor cho captures đã có. [Actual approved runtime evidence](../storage/raw/README.md#wwi-06b--approved-raw-payload-provisioning-2026-11-18).

[full_load_offline.py](full_load_offline.py) là WWI-06A executable unit/offline integration suite với synthetic fixtures/mock drivers: exact types/F2, batches, NULL, failure rollback, unknown ACK, count/digest, retry/idempotency, source permission/TLS/schema/identity guards, COPY/named cursor và no-secret CLI. Chạy `unittest discover -s tests -p full_load_offline.py -v` bằng project venv. Không DB/source connection hoặc real Full Load; actual SQL/adapter/runtime proof dành WWI-06B. [Runbook](../ingestion/README.md).

[raw_foundation_static.py](raw_foundation_static.py) kiểm config/secret omission/target isolation/metadata SQL và actual Compose parser; [source_security_static.py](source_security_static.py) giữ11-object SQL guards regression. Chạy explicit `unittest discover -s tests -p 'raw_foundation_static.py' -v` hoặc `source_security_static.py` trong existing venv, không DB runtime. [Raw README](../infrastructure/docker/README.md) có commands. EX02-S1 ACL tests phía dưới là **DEFERRED — OPTIONAL SECURITY HARDENING** theo MVP-SIMPLIFICATION-01; không pipeline gate hoặc prerequisite. Không claim SQL compilation/service/runtime từ static PASS.

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
- [e2e/](README.md)

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

## EX02-S1 ACL offline checks

[staging_acl_static.py](staging_acl_static.py) có13 standard-library contract/mutation tests; [staging_acl_offline.ps1](staging_acl_offline.ps1) parse5 prepared operator/helper files và kiểm10 unsafe fixtures trong memory. Commands và giới hạn tại [staging README](../data-sources/security/staging/README.md). Không chạy operator entry scripts, không ACL/SQL writes, không là effective-access hoặc ancestor race proof. EX02/G02 runtime vẫn BLOCKED.


## MVP-RESET-01 consolidation

Future-only submodule READMEs ?? h?p nh?t v? ??y; ch?a c? implementation trong c?c th? m?c k? ho?ch ??. Xem [roadmap](../ROADMAP.md). Kh?ng t?o placeholder code; t?o module con khi c? task tri?n khai th?c t?.
