# source-security — Prepared DBA Scripts

**Owner-provided runtime evidence2026-11-18:** dedicated wwi_extract đã SELECT đủ11 source objects; hai physical archives báo effective INSERT dù chưa thấy direct grant, còn unresolved; TLS certificate validation fail nếu không diagnostic trust bypass. Không independently rerun dưới dedicated identity trong Phase A. MVP-G01 **BLOCKED**, không dùng TrustServerCertificate=yes hoặc DBA fallback trong production ingestion. Historical “chưa provision” notes bên dưới không thay current exceptions; task WWI-06A chỉ code/offline tests cho source, không security changes hoặc source Full Load.

**Current MVP policy: MVP-SIMPLIFICATION-01.** EX02-S1 **DEFERRED — OPTIONAL SECURITY HARDENING**; protected staging/ACL remediation/mandatory SHA256 manifest không MVP blocker. [Local setup §10](#10-local-mvp-setup--pending-runtime-authorization) là workflow hiện hành. Existing populated SQL/guards/allowlist giữ nguyên; manifest/checklist/hardening status notes dưới đây là historical references khi nói về mandatory staging/hashes. **EX01 DONE, EX02 pending explicit SQL execution, MVP-G01/G02 chưa runtime PASS.**

## 1. Overview

**DBA REVIEW REQUIRED — DO NOT AUTO-EXECUTE.** EX02 **Pending SQL Execution Authorization**. [Historical manifest](wwi_extraction_execution_manifest.json) giữ populated identities/SIDs/11-object scope/activation recipe và old staging/hashes để truy vết. [Populated-package history](../../docs/architecture/wwi-source-dba-owner-checklist.md#12-ex02-populated-package--final-authorization-review) ghi actual metadata/empty-negative-DB exception của task trước. Current local workflow ở §10 không cần mandatory execution manifest. Setup/verify **NOT RUN**; EX01 DONE không source-access/runtime PASS.

**EX02-S1 historical follow-up:** [ACL assessment](../../docs/architecture/wwi-ex02-s1-acl-assessment.md) và [package](staging/README.md) giữ sibling layout/ancestor findings tại f1d1fc4; nay DEFERRED theo Owner simplification. Không ACL/staging/copy nào đã được thực hiện. Old C:\ProgramData manifest paths chỉ revisit nếu có future hardening task, không cần amendment để chạy local MVP procedure.

## 2. Purpose

Chuẩn bị dedicated non-admin Windows identity/mapping/object SELECT vàsafe read-only verification,tách khỏi ingestion vàB9.

## 3. Scope

Original SQLEXPRESS/WideWorldImporters,9 current+2 physical H;không Raw schema,copy,source config hoặc data changes.

## 4. Responsibilities

Owner/local DBA review exact setup và authorize execution một lần cho task cụ thể; OS owner giữ credential, extractor dùng dedicated identity; data correctness checks dựa actual evidence. Current task chỉ preparation/offline tests, không SQL connection/security execution. Empty negative DB CREATE là evidence task trước, không quyền create/query/cleanup mới trong task này.

## 5. Inputs

Windows principal `DESKTOP-OBDFK6B\wwi_extract`, SID-1007, DB user `wwi_extract`, reference `WWI05-EX02-20261117-01` và negative target `Retail_EX02_DeniedAccess_20261117` đã populated. DBA/operator PC/SID-1001 cần targeted SQL execution authority. Client/group/TLS và actual least-privilege evidence vẫn cần; protected staging/execution hashes là optional hardening. Repo confirmations vẫn0/DO_NOT_EXECUTE.

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

<a id="10-execution--future-separate-approval-required"></a>

## 10. Local MVP Setup — Pending Runtime Authorization

Theo [MVP-SIMPLIFICATION-01](../../docs/architecture/wwi-m1b-owner-decisions.md#mvp-simplification-01--trusted-local-mvp), không cần protected staging/custom ACL/SHA256 execution manifest cho local MVP. Dùng existing guarded SQL, một Owner/DBA local authorization cụ thể và ghi actual result. **Task chuẩn bị này không execute SQL hoặc tạo activated copies.**

1. Owner/DBA xác nhận target `tcp:DESKTOP-OBDFK6B,1433`, instance SQLEXPRESS, database WideWorldImporters; DBA/operator `DESKTOP-OBDFK6B\PC`, SID-1001. Recheck source và login/user collision trước setup; existing identity hoặc ambiguous result → STOP, không tự alter/reuse/retry.
2. Kiểm Windows account `DESKTOP-OBDFK6B\wwi_extract`, Enabled/PasswordRequired=True, SID `S-1-5-21-2164258108-3044412014-540060861-1007`, no-admin theo EX01. Không reset password hoặc đổi account; Owner giữ password và nhập riêng trong runas prompt.
3. Review [setup](wwi_extraction_identity_setup.sql): new FROM WINDOWS login và database user `wwi_extract`, **CONNECT SQL trong master + CONNECT trong WWI + SELECT trên đúng11 objects**. Không sysadmin/db_owner/db_datareader/db_datawriter/GRANT OPTION hoặc source DML/schema changes.9 current: Sales.Customers/Orders/OrderLines/Invoices/InvoiceLines/CustomerTransactions, Warehouse.StockItems/StockItemHoldings/StockItemTransactions;2 physical archives: Sales.Customers_Archive và Warehouse.StockItems_Archive.
4. Sau Owner approve actual setup action: dùng SSMS query buffer hoặc ordinary ignored `.local/ex02/setup.sql` copy. Chỉ đổi bốn setup bits `DbaReviewed`, `OwnerExecutionAuthorized`, `WindowsAccountProvisioned`, `WindowsNonAdminAttested` từ0→1 sau actual checks, cùng confirmation sang `EXECUTE_APPROVED_WWI_IDENTITY_SETUP`. Không sửa principal/SID/scope/guards; không commit activated copy. Không cần custom staging ACL hoặc privileged runner.
5. Nếu dùng SQLCMD, command chuẩn bị dưới đây chỉ dành **sau execution authorization và manual activation**; chạy toàn batch bằng real PC DBA session:

```powershell
& 'C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\180\Tools\Binn\SQLCMD.EXE' -S tcp:DESKTOP-OBDFK6B,1433 -d WideWorldImporters -E -Nm -X1 -x -b -r1 -f 65001 -l 5 -t 20 -i 'D:\Code\Retail_Data_Platform\project1_Retail_Data_platform\.local\ex02\setup.sql'
```

6. Mở fresh extractor session bằng `runas /user:DESKTOP-OBDFK6B\wwi_extract powershell.exe`; Owner nhập password tương tác. Không EXECUTE AS/developer/sysadmin extraction. Source Python tiếp tục ODBC18/Windows Integrated/Encrypt=yes/TrustServerCertificate=no; không `-C` hoặc TLS fallback.
7. Trong task verification được authorize, dùng [verify](wwi_extraction_identity_verify.sql). Giữ guard defaults ở Git. Manual copy `.local/ex02/verify.sql`: chỉ bật `VerificationAuthorized`, `DbaWindowsGroupReviewComplete`, `ClientTlsProofReviewed`, `NegativeDatabaseExistsAttested` sau đúng actual checks, và confirmation `EXECUTE_APPROVED_READ_ONLY_VERIFICATION`. Dùng command bước5 với input `verify.sql` trong **extractor session**. Existing negative DB Retail_EX02_DeniedAccess_20261117 phải được DBA recheck identity/state trước attestation; không tạo/drop trong task này. Không bật flag để giả proof.
8. Ghi LP01–12 results/errors/NULL: exact identity/SID,11 SELECT/current+H probes, no write/admin/broad permissions, Windows/public/group/module paths và client TLS. Optional DMV thiếu quyền là NOT RUN, không cấp broad rights để test xanh. `PREPARED_SETUP_APPLIED_NOT_GATE_PASS`/exit0 không tự PASS. Owner local có thể review kết quả cùng một task, không cần approval chain mới. Source consistency là proof riêng trước Full Load, không được suy từ access PASS.

Failure/rollback: transaction setup rollback/rethrow khi chưa commit; ambiguous outcome inspect trước retry. Postcommit removal phải được authorize theo exact newly created SID/grants/dependencies, không drop shared identity hoặc KILL. Existing negative DB cleanup chỉ sau actual tests và exact pinned resource checks như historical checklist, không tự cleanup sớm. Không source writes hoặc password trong logs.

Historical [manifest](wwi_extraction_execution_manifest.json) và [checklist §12](../../docs/architecture/wwi-source-dba-owner-checklist.md#12-ex02-populated-package--final-authorization-review) giữ traceability; staging paths/hashes/activation recipe ở đó là optional hardening reference, không prerequisite của local steps này. Guarded SQL bytes không đổi; chưa có execution authorization hoặc runtime PASS.

## 11. Testing

Chỉ explicit offline command:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'source_security_static.py' -v
```

18 tests PASS ngày2026-11-17: disabled guards,populated values/SIDs/operator/refs,11-object/H coverage,CONNECT contexts/QUOTENAME/SID collisions/read-only verify,extra SELECT/role/wrong SID mutations và manifest exact hashes/activation recipe. Tests không DB drivers/subprocess/SQL execution/dependency changes; không compiler/formal proof. Activated bytes chỉ derive trong memory.

## 12. Acceptance Criteria

Populated names/SIDs/refs đúng, không secrets; exact11 allowlist/no broad/admin grants, disabled guards và new-only transaction behavior; actual Owner-authorized setup/fresh extractor TLS/access/permission evidence trước source-access PASS. Mandatory protected staging/execution hashes đã deferred. Static QA không thay SQL runtime; setup/verify/window NOT RUN.

## 13. Status

**EX01 DONE; EX02 Pending SQL Execution Authorization; G02 detailed chưa PASS; G01 Pending Consistency Proof; WWI-05/Phase2 IN_PROGRESS.** EX02-S1 DEFERRED, không cần protected staging/hash-manifest approval để theo local §10. Source setup/verify chưa chạy; Full Load/runtime milestones chưa bắt đầu. Historical hashes/negative-DB creation/evidence giữ traceable trong Owner Record/checklist/manifest; task hiện tại không query hoặc sửa database đó. M1B-Approval không tự DONE, không tự runtime gate PASS.

## 14. Reference semantics

[Microsoft CREATE LOGIN](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-login-transact-sql?view=sql-server-ver17) mô tả transactional login creation;không đảm bảo rollback external DDL-trigger/audit side effects. [QUOTENAME](https://learn.microsoft.com/en-us/sql/t-sql/functions/quotename-transact-sql?view=sql-server-ver17) giới hạn128 characters vàdelimits identifiers;script kiểm length/NULL trước dynamic identifiers. [Object GRANT](https://learn.microsoft.com/en-us/sql/t-sql/statements/grant-object-permissions-transact-sql?view=sql-server-ver17) là reference cho per-object SELECT,không cấp actual execution approval.

[Server GRANT](https://learn.microsoft.com/en-us/sql/t-sql/statements/grant-server-permissions-transact-sql?view=sql-server-ver17) yêu cầu context master. Setup giữ outer context/source guard WideWorldImporters; chỉ dynamic CONNECT batch chuyển sang master cho CONNECT SQL rồi về WideWorldImporters cho CONNECT database, trong transaction hiện có. Không thêm quyền hoặc batch separator; engine compilation/execution vẫn NOT RUN.
