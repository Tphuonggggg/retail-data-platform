# source-security — Prepared DBA Scripts

## 1. Overview

**DBA REVIEW REQUIRED — DO NOT AUTO-EXECUTE.** Ngày2026-11-17, EX02 populated candidate **Pending Execution Authorization**. [Execution manifest](wwi_extraction_execution_manifest.json) pin actual identities/SIDs,paths/11-object scope,guarded/activated hashes/operator/staging/rollback/stop conditions. [Current review](../../docs/architecture/wwi-source-dba-owner-checklist.md#12-ex02-populated-package--final-authorization-review) ghi actual metadata và ngoại lệ Owner cho empty negative database. Setup/verify **NOT RUN**, production extraction Not implemented yet; EX01 DONE không G02 PASS.

**EX02-S1 follow-up:** Owner yêu cầu repo và protected staging làm siblings dưới `D:\Code\Retail_Data_Platform`. [ACL assessment](../../docs/architecture/wwi-ex02-s1-acl-assessment.md) và [prepared staging package](staging/README.md) ghi exact proposal và ancestor/inheritance blockers; **chưa áp dụng ACL hoặc tạo staging**. Paths C:\ProgramData trong SQL manifest là proposal lịch sử, cần amendment riêng trước execution; không dùng chúng để vượt Owner location requirement mới. EX02/G02 vẫn BLOCKED, package chỉ chuẩn bị để review.

## 2. Purpose

Chuẩn bị dedicated non-admin Windows identity/mapping/object SELECT vàsafe read-only verification,tách khỏi ingestion vàB9.

## 3. Scope

Original SQLEXPRESS/WideWorldImporters,9 current+2 physical H;không Raw schema,copy,source config hoặc data changes.

## 4. Responsibilities

DBA review/populate/approve execution riêng;OS owner xác nhận account vàgroups;Source Owner kiểm soát writers;DQ review proof. Current task gồm preparation/static tests và metadata SELECT; Owner follow-up cho riêng empty negative database CREATE, không EX02 security execution.

## 5. Inputs

Windows principal `DESKTOP-OBDFK6B\wwi_extract`, SID-1007, DB user `wwi_extract`, reference `WWI05-EX02-20261117-01` và negative target `Retail_EX02_DeniedAccess_20261117` đã populated; không unresolved placeholders. Proposed DBA là PC/SID-1001, phải được Owner duyệt cho EX02. Staging/client/group/TLS/approval evidence là external prerequisites. Repo confirmations vẫn0/DO_NOT_EXECUTE.

## 6. Outputs

- [Setup](wwi_extraction_identity_setup.sql): proposed new Windows SQL login/user,CONNECT vàobject SELECT;disabled by default.
- [Verify](wwi_extraction_identity_verify.sql): own-context rights/roles/columns/H links/constant read/cross-DB/TLS evidence queries;disabled by default.
- [Execution manifest](wwi_extraction_execution_manifest.json): guarded/activated SHA256,exact activation edits và bounded sandbox/cleanup record; không execution authority.

Không output nào là executed/G01/G02 PASS.

## 7. Dependencies

Existing SQL Server/approved Windows identity,source contracts,Owner authorization và[execution checklist](../../docs/architecture/wwi-source-dba-owner-checklist.md). Windows provisioning là external prerequisite;không thêm package/module dependency.

## 8. Technology

T-SQL preparation;offline standard-library Python unittest. Không SQL parser/engine connection trong static QA;SQL compatibility/compilation cần DBA review vàauthorized validation.

## 9. Structure

README,2 standalone .sql files và1 JSON manifest. Không migration registration,CI hooks,SQLCMD include files hoặc bootstrap runner. Static checker ở [tests/source_security_static.py](../../tests/source_security_static.py) chỉ đọc/mutate strings trong memory,không execute SQL hoặc viết activated files.

Thư mục [staging/](staging/README.md) bổ sung prepared native PowerShell ACL procedures/plan; không production hoặc SQL execution runner, không tự register hooks.

## 10. Execution — FUTURE SEPARATE APPROVAL REQUIRED

1. Owner review manifest ID WWI05-EX02-20261117-01, exact proposed PC/SID-1001 operator, staging/access/client/rollback và cả guarded/activated hashes. Chưa setup/verify execution approval.
2. Reverify exact existing EX01 principal/SID-1007 và source/negative DB identity; không provision/reset account. DBA recheck collision/metadata/public/group/module/ownership/trigger baseline; missing/unknown proof thì STOP.
3. Owner review [EX02-S1](../../docs/architecture/wwi-ex02-s1-acl-assessment.md): target hiện hành là `D:\Code\Retail_Data_Platform\Retail_EX02_Protected_Staging`, sibling với repo. Ancestor namespace/parent inheritance preservation chưa resolve; không tạo/copy hoặc execute. SQL manifest C:\ProgramData/verification/log proposal cũ cần amendment riêng sau exact ACL/location/client review. Restricted named-principal ACL/effective parent/file/owner/reparse checks vẫn bắt buộc; không elevated helper từ repo/venv hoặc writable PATH. Hiện chưa staging/ACL/copy nào được tạo.
4. **Exact-byte activation:** repo chỉ lưu flags0/DO_NOT_EXECUTE. Manifest pin actual guarded hash và derived activated hash, đúng5 edits/script. Owner approve activated hash và external prerequisites; flags không tự chứng minh authority. Custodian copy guarded bytes, kiểm hash với independent protected approval record, trusted editor sửa đúng5 lines rồi activated hash phải khớp trước execute. Không dùng privileged Python/venv runner. Edit khác, BOM hoặc LF↔CRLF change → STOP/new review; không authorize arbitrary post-hash edits.
5. Named DBA dùng absolute signed/pinned SQLCMD17.0.1000.7 trong manifest, fresh real Windows context và protected working directory ngoài checkout/venv; proposed args: -S tcp:DESKTOP-OBDFK6B,1433 -d WideWorldImporters -E -Nm -X1 -x -b -r1 -f 65001 -l 5 -t 20. Input là whole reviewed activated protected copy, logs riêng/unique/no overwrite. Không -C/-P/-U/-A/startup/env/substitution/selected fragments. Chỉ offline -? đã chạy, không -i/-Q/setup/verify execution.
6. Setup new-only: existing name/SID → STOP, không alter/reuse. CONNECT SQL trong master, database CONNECT và11 object SELECT trong WWI; type U/expected SID pin. XACT_ABORT/transaction rollback/rethrow; ambiguous outcome inspect state trước mọi retry. Postcommit revoke/drop/rollback cần exact authority/dependency/active-use checks; không global public/Windows changes hoặc KILL.
7. Separate verification authority: fresh actual extractor context, external group/client TLS/negative DB proof trước activation; chạy read-only verify,giữ mọi result/error/NULL và LP01–12 reviewer outcomes. No DML negative tests,diagnostic elevation hoặc process-exit/marker G02 PASS. Metadata gaps trình exact request riêng.
8. **Owner-authorized sandbox exception:** đã CREATE empty Retail_EX02_DeniedAccess_20261117, ID11/GUID E5CDE2F8-8281-4138-9441-59793F62F8B9,0 user tables/guest CONNECT grants. Không source payload/user/grant. Owner yêu cầu tạo test DB và xóa khi hoàn tất. Actual target tests còn NOT RUN nên giữ DB để test; sau tests/evidence, recheck name/ID/GUID/create_date/owner/empty/dependencies/no active sessions rồi chỉ DROP đúng database đó. Không SINGLE_USER/ROLLBACK IMMEDIATE/KILL hoặc filesystem delete. Creation không là denied-access PASS.

Source TLS giữ ODBC18/Encrypt=yes/TrustServerCertificate=no; client/server-state diagnostics không tự chứng minh certificate validation. Optional DMV NOT RUN khi thiếu quyền; không cấp broad rights để làm test xanh. Không auto-execution hook/CI/ingestion/source-window operation. Xem [platform sqlcmd](https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-utility?view=sql-server-ver17); actual command support được đối chiếu offline với client cài sẵn.

## 11. Testing

Chỉ explicit offline command:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'source_security_static.py' -v
```

18 tests PASS ngày2026-11-17: disabled guards,populated values/SIDs/operator/refs,11-object/H coverage,CONNECT contexts/QUOTENAME/SID collisions/read-only verify,extra SELECT/role/wrong SID mutations và manifest exact hashes/activation recipe. Tests không DB drivers/subprocess/SQL execution/dependency changes; không compiler/formal proof. Activated bytes chỉ derive trong memory.

## 12. Acceptance Criteria

Populated names/SIDs/refs đúng,không unresolved placeholders hoặc secrets; exact11 allowlist,no broad/admin grants,disabled guards và new-only transaction behavior; manifest pin guarded/activated bytes,external execution prerequisites rõ;static QA PASS. Actual SQL setup/verify/window NOT RUN, không auto gate PASS.

## 13. Status

**EX01 DONE; EX02 Pending Execution Authorization; G02 BLOCKED; G01 Pending Consistency Proof; WWI-05/Phase2 IN_PROGRESS; M1C/M2/M3 NOT STARTED.** Ready for Owner review của exact candidate manifest, không executable authorization. M1B-Approval không tự DONE. Original unpopulated hashes/decisions trong Owner Record là history, current hashes lấy manifest; SQL setup/verify chưa chạy. Chỉ empty negative database đã tạo theo Owner exception, giữ cho pending tests rồi cleanup theo exact manifest conditions.

## 14. Reference semantics

[Microsoft CREATE LOGIN](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-login-transact-sql?view=sql-server-ver17) mô tả transactional login creation;không đảm bảo rollback external DDL-trigger/audit side effects. [QUOTENAME](https://learn.microsoft.com/en-us/sql/t-sql/functions/quotename-transact-sql?view=sql-server-ver17) giới hạn128 characters vàdelimits identifiers;script kiểm length/NULL trước dynamic identifiers. [Object GRANT](https://learn.microsoft.com/en-us/sql/t-sql/statements/grant-object-permissions-transact-sql?view=sql-server-ver17) là reference cho per-object SELECT,không cấp actual execution approval.

[Server GRANT](https://learn.microsoft.com/en-us/sql/t-sql/statements/grant-server-permissions-transact-sql?view=sql-server-ver17) yêu cầu context master. Setup giữ outer context/source guard WideWorldImporters; chỉ dynamic CONNECT batch chuyển sang master cho CONNECT SQL rồi về WideWorldImporters cho CONNECT database, trong transaction hiện có. Không thêm quyền hoặc batch separator; engine compilation/execution vẫn NOT RUN.
