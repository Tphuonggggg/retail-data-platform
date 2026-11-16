# source-security — Prepared DBA Scripts

## 1. Overview

**DBA REVIEW REQUIRED — DO NOT AUTO-EXECUTE.** Chỉ artifacts chuẩn bị theo [M1B-OD01–03](../../docs/architecture/wwi-m1b-owner-decisions.md). SQL setup/verify **NOT RUN**;production extraction Not implemented yet.

## 2. Purpose

Chuẩn bị dedicated non-admin Windows identity/mapping/object SELECT vàsafe read-only verification,tách khỏi ingestion vàB9.

## 3. Scope

Original SQLEXPRESS/WideWorldImporters,9 current+2 physical H;không Raw schema,copy,source config hoặc data changes.

## 4. Responsibilities

DBA review/populate/approve execution riêng;OS owner xác nhận account vàgroups;Source Owner kiểm soát writers;DQ review proof. Codex task này chỉ file preparation/static tests.

## 5. Inputs

Actual Windows principal/database-user/change/verification references **chưa supplied**;11-object allowlist,reviewed client TLS/profile,external non-admin/group/negative-database evidence vàfuture execution authority.

## 6. Outputs

- [Setup](wwi_extraction_identity_setup.sql): proposed new Windows SQL login/user,CONNECT vàobject SELECT;disabled by default.
- [Verify](wwi_extraction_identity_verify.sql): own-context rights/roles/columns/H links/constant read/cross-DB/TLS evidence queries;disabled by default.

Không output nào là executed/G01/G02 PASS.

## 7. Dependencies

Existing SQL Server/approved Windows identity,source contracts,Owner authorization và[execution checklist](../../docs/architecture/wwi-source-dba-owner-checklist.md). Windows provisioning là external prerequisite;không thêm package/module dependency.

## 8. Technology

T-SQL preparation;offline standard-library Python unittest. Không SQL parser/engine connection trong static QA;SQL compatibility/compilation cần DBA review vàauthorized validation.

## 9. Structure

README,2 standalone .sql files. Không migration registration,CI hooks,SQLCMD include files hoặc bootstrap runner. Static checker ở [tests/source_security_static.py](../../tests/source_security_static.py) chỉ đọc/mutate strings trong memory,không execute SQL.

## 10. Execution — FUTURE SEPARATE APPROVAL REQUIRED

1. Review actual names/SIDs/new-vs-reuse mode vàpopulated artifact diff/hash;Owner approve exact change package. Các defaults hiện tại phải stop.
2. OS owner provision/verify account riêng;không local-admin/group elevation;không giả account đã có.
3. DBA session dùng approved secure source/database context;review DDL policies/triggers vàprivilege closure trước apply. Chạy toàn bộ reviewed setup batch,không selected fragments hoặc thêm batch separators.
4. Setup chỉ hỗ trợ **new identity**;nếu login/user tồn tại thì stop. Reuse/metadata VIEW DEFINITION cần proposal riêng,không bật broad grants.
5. Verification bằng fresh real Windows extraction session,không developer/admin/EXECUTE AS. Điền approved negative user-DB target vàexternal TLS/group evidence;placeholders/default0 hoặcNULL đều không là authority.
6. Capture mọi resultset/error/NULL vàper-test outcomes;không coi ending EVIDENCE_ONLY marker hoặc process exit0 là G02 PASS. Permission/cross-DB/module/Windows closure còn cần DBA review.
7. Failure trong setup transaction có rollback/rethrow;post-commit revoke/disable/drop chỉ theo separate reviewed rollback request,không tự xóa principal/grants đang được dùng.

Không SQL execution command được nối vào normal project automation. Không chạy setup/verify ở task hiện tại. Client TLS giữ Driver18/Encrypt=yes/TrustServerCertificate=no;SQL không tự chứng minh client certificate validation. Optional DMV không biện minh cấp server-state rights.

## 11. Testing

Chỉ explicit offline command:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'source_security_static.py' -v
```

12 static tests PASS,bao gồm disabled guards,11-object allowlist/H,QUOTENAME,one batch,read-only verify vàunsafe-mutation rejection. Không import DB driver,run SQL,subprocess hoặc thay dependencies;không compiler/formal proof.

## 12. Acceptance Criteria

Prepared artifacts đúng11 allowlist,no secrets/no actual Windows names,fail-closed guards;setup/verify tách biệt;external prerequisites rõ;no automation executes admin SQL;static QA PASS. Actual setup/verify/window tests giữ NOT RUN.

## 13. Status

Prepared,technically reviewed statically;**DBA review vàexecution approval outstanding**. M1B-Approval IN_PROGRESS,WWI-05/Phase2 IN_PROGRESS,M1C/M2/M3 Not Started.

## 14. Reference semantics

[Microsoft CREATE LOGIN](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-login-transact-sql?view=sql-server-ver17) mô tả transactional login creation;không đảm bảo rollback external DDL-trigger/audit side effects. [QUOTENAME](https://learn.microsoft.com/en-us/sql/t-sql/functions/quotename-transact-sql?view=sql-server-ver17) giới hạn128 characters vàdelimits identifiers;script kiểm length/NULL trước dynamic identifiers. [Object GRANT](https://learn.microsoft.com/en-us/sql/t-sql/statements/grant-object-permissions-transact-sql?view=sql-server-ver17) là reference cho per-object SELECT,không cấp actual execution approval.
