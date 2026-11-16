# WWI-05 / M1B — SQL Server Extraction Identity Proposal

**M1B-OD01 APPROVED — Logical/Security Direction,2026-11-16. Current EX01 final OS identity handoff ở §7; EX02 SQL package/execution còn pending.** Task M1B trước đây chỉ cho review/SELECT metadata và documentation commit; §6 giữ history trước EX01-R01, không cho tạo/sửa SQL login/user/role/grants. [M1A Secure Contract](wwi-secure-connection-contract.md) giữ general connection/security boundaries; tài liệu này chuyên biệt object-level privilege package và acceptance tests, không tạo connector hoặc duplicate source contracts.

Liên kết: [Consistency proposal](wwi-source-consistency-proposal.md), [DBA/Owner checklist](wwi-source-dba-owner-checklist.md), [M1B actual evidence/acceptance](wwi-m1b-assessment.md), [31 original gates](../data-models/wwi-implementation-gate-register.md). G02/RG02/CG08 vẫn BLOCKED/Pending cho intended extraction profile.

## 1. Phát hiện hiện tại và quyền tối thiểu đề xuất

M1B actual self-context inspection tại UTC `2026-11-16T07:29:27.1556321`: source đúng SQLEXPRESS/WideWorldImporters, TLS TRUE/TCP/NTLM. Current principal fingerprint `5eecf0d76c45635cd7b2026ff0ebb098811ebd393fc08164a804c28e9a92f27d` khớp M1A; sysadmin/CONTROL SERVER/CONNECT ANY DATABASE=1, role predicates securityadmin/db_owner/db_datawriter=1,51 server và109 database effective permission names. Đây là effective security-context results, **không suy ra mọi quyền đều được GRANT trực tiếp hoặc membership path đã audit đầy đủ**.

11 objects có SELECT/VIEW DEFINITION/INSERT/UPDATE/DELETE/ALTER/CONTROL/TAKE OWNERSHIP predicates=1. Current identity **FAIL suitability**; không sửa quyền developer hoặc coi client read-only hint là server enforcement. Engine restrictions đối với direct H mutation khác permission metadata; không thử ghi archive để chứng minh quyền.

| Package | Minimum requested scope | Điều kiện và giới hạn |
| --- | --- | --- |
| P01 Authentication/connect | Windows Integrated bằng dedicated non-admin execution identity; CONNECT SQL và CONNECT WideWorldImporters qua mapping được DBA duyệt | Tên Windows principal/login/user/role TBD; không hardcode credentials hoặc reuse developer sysadmin. Không đề nghị SQL auth fallback/mixed-mode change trong task này. |
| P02 Source SELECT | SELECT từng object thuộc declared capture scope trong bảng11 dưới đây | Tránh db_datareader, schema-wide hoặc database-wide SELECT vì rộng hơn approved scope; không tự thêm reference tables. |
| P03 Metadata | Catalog metadata cần cho11 objects: columns/types/nullability/PK/FK/index/computed/default/period/history binding | SELECT thường cho visibility object; chỉ xin object-scoped VIEW DEFINITION ở objects cần definitions mà visibility hiện có chưa đủ. Không mặc định cần database/server VIEW DEFINITION. |
| P04 Own permission inspection | Own fn_my_permissions/HAS_PERMS_BY_NAME/role predicates và token inspection | Không IMPERSONATE/EXECUTE AS; không nâng quyền để đọc principal khác. DBA audit role/group/grant/ownership closure bằng identity riêng. |
| P05 TLS diagnostics | Driver18,Encrypt=yes,TrustServerCertificate=no; approved endpoint/name/CA; fail closed | Không xin VIEW SERVER PERFORMANCE STATE/VIEW SERVER STATE chỉ vì diagnostic DMV; dùng validated client handshake và DBA corroboration nếu cần session detail. |
| P06 Không cấp quyền thay đổi | Không sysadmin/db_owner/db_datawriter hoặc privileged server/db roles; không DML/DDL/config/CONTROL/TAKE OWNERSHIP/IMPERSONATE/role-management/grant option hoặc executable mutation paths | Kiểm cả Windows groups/local-admin capability, public/custom-role inheritance, schema/object ownership, column grants và modules. Không dùng DENY overlay để “sửa” sysadmin. |
| P07 Cross-database boundary | Không CONNECT ANY DATABASE/SELECT ALL USER SECURABLES hoặc user-DB access ngoài scope | DBA chỉ định negative database/object allowlist không nhạy cảm; system metadata/master/tempdb cần cho kết nối phải phân biệt với unrelated business DB access. Không đổi server/database configuration trong M1B. |

[Microsoft metadata visibility](https://learn.microsoft.com/en-us/sql/relational-databases/security/metadata-visibility-configuration?view=sql-server-ver17) cho biết quyền trên object và VIEW DEFINITION ảnh hưởng metadata được thấy; NULL/empty catalog không chứng minh object/definition không tồn tại. Do đó P03 là conditional minimum dựa trên required metadata tests; thiếu visibility phải báo BLOCKED hoặc dùng DBA evidence, không tự mở quyền rộng.

## 2. Approved population allowlist

Full design scope là9 current+2 physical H, không11 nguồn độc lập. Default privilege proposal bao phủ11 objects để chuẩn bị MVP; execution capture vẫn cần scope Sales-first được Owner duyệt. Nếu chọn staged permission rollout thì chỉ cấp subset được duyệt, ghi rõ excluded populations và không claim đủ11 trước khi verified. Không thay approved source scope.

| Population | Role / dependency | Metadata columns observed | Requested data privilege |
| --- | --- | --- | --- |
| Sales.Customers | Current temporal master | 31 | Object SELECT; no write/ALTER/CONTROL |
| Sales.Orders | Current source | 16 | Object SELECT; no write/ALTER/CONTROL |
| Sales.OrderLines | Current source | 12 | Object SELECT; no write/ALTER/CONTROL |
| Sales.Invoices | Current source | 25 | Object SELECT; no write/ALTER/CONTROL |
| Sales.InvoiceLines | Current source | 13 | Object SELECT; no write/ALTER/CONTROL |
| Sales.CustomerTransactions | Current source | 14 | Object SELECT; no write/ALTER/CONTROL |
| Warehouse.StockItems | Current temporal master | 25 | Object SELECT; no write/ALTER/CONTROL |
| Warehouse.StockItemHoldings | Current source | 9 | Object SELECT; no write/ALTER/CONTROL |
| Warehouse.StockItemTransactions | Current source | 11 | Object SELECT; no write/ALTER/CONTROL |
| Sales.Customers_Archive | Physical H stream | 31 | Object SELECT; no write/ALTER/CONTROL |
| Warehouse.StockItems_Archive | Physical H stream | 25 | Object SELECT; no write/ALTER/CONTROL |

Customers → Sales.Customers_Archive; StockItems → Warehouse.StockItems_Archive đã xác nhận bằng history_table_id metadata. Archive cần được cấp SELECT riêng; SELECT current không tự cấp SELECT history, theo [Microsoft Temporal Table Security](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal/security?view=sql-server-ver17). Physical archive access phải giữ zero-duration/duplicates theo A01/B9; không thay bằng FOR SYSTEM_TIME ALL.

Application.TransactionTypes, Purchasing và label/reference tables ngoài11 không được đọc thêm bằng broad SELECT để tiện triển khai. Nếu cần metadata/reference extension phải review CG10/source contract riêng; không cấp quyền mới trong M1B.

## 3. Authentication/TLS và loại trừ elevation

Preferred identity là dedicated Windows execution principal không thuộc local Administrators hoặc nhóm có SQL elevation; DBA kiểm Windows group membership ngoài SQL cùng effective SQL token. Service/logon/scheduler setup chưa được phép; tên identity và cách chạy Python dưới identity đó cần Owner/DBA chốt. Không suy từ interactive connection hiện tại.

Không member db_owner/db_datawriter/db_ddladmin/db_securityadmin, privileged server roles hoặc custom role tương đương; không CONTROL SERVER/database/schema/object, ownership hoặc permission-management/grant-option paths. Quyền public/guest/custom groups/modules phải được audit; catalog explicit grants một mình không bao phủ fixed-role/Windows inheritance. [Microsoft effective permissions](https://learn.microsoft.com/en-us/sql/relational-databases/security/authentication-access/determining-effective-database-engine-permissions?view=sql-server-ver17) giải thích các nguồn quyền và sysadmin không bị chặn bởi DENY thông thường; không đề xuất giữ sysadmin rồi thêm DENY DML.

Endpoint giữ tcp:DESKTOP-OBDFK6B,1433/database WideWorldImporters cho original. B9 driver/time precision policy không đổi. Strict client settings và successful certificate-validated handshake là evidence TLS, theo [Microsoft ODBC attributes](https://learn.microsoft.com/en-us/sql/connect/odbc/dsn-connection-string-attribute?view=sql-server-ver17); không fallback TrustServerCertificate=yes/Encrypt=no, không auto import certificate hoặc đổi engine config.

Query TLS của M1A/M1B dùng sys.dm_exec_connections dưới current admin. WHERE session_id=@@SPID **không tự miễn quyền DMV**: [Microsoft DMV permissions](https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-objects/sys-dm-exec-connections-transact-sql?view=sql-server-ver17) yêu cầu VIEW SERVER PERFORMANCE STATE từ SQL Server2022 trở đi. Future extractor không được tự cấp quyền này chỉ để làm test xanh. Nếu diagnostic bị từ chối, giữ actual outcome; client secure flags/handshake vẫn kiểm được, DBA riêng có thể cung cấp correlated session evidence theo quyền sẵn có. Không tạo elevated helper/procedure trong task này.

## 4. Read-only acceptance test specification — chưa chạy intended identity

[fn_my_permissions](https://learn.microsoft.com/en-us/sql/relational-databases/system-functions/sys-fn-my-permissions-transact-sql?view=sql-server-ver17) trả effective permissions của current context và dùng được qua public; kiểm user khác cần impersonation, không làm trong M1B. Chạy các tests sau bằng **real approved extraction logon context**, không EXECUTE AS developer. Các expected-zero assertions có NULL/error → NOT VERIFIED/BLOCKED, không đổi NULL thành0.

| Test ID | Method / expected assertion | Execution status |
| --- | --- | --- |
| LP01 | Match actual host/instance/database và expected principal fingerprint/SSPI context; không dbo/admin mapping hoặc identity fallback | NOT RUN — intended profile chưa supplied/approved |
| LP02 | sysadmin/securityadmin/privileged role predicates=0; db_owner/db_datawriter/db_ddladmin/db_securityadmin=0; DBA kiểm custom/Windows/local-admin paths | NOT RUN — current developer FAIL, không substitute |
| LP03 | Own server/database fn_my_permissions: chỉ allowlisted required permissions; không CONTROL/ALTER/IMPERSONATE/CREATE/config/role-management/broad cross-DB powers; DBA audit grant options/ownership | NOT RUN |
| LP04 | Từng11 object SELECT=1 và bounded TOP(1) constant; SELECT approved-column metadata/projection contract không permission exception | NOT RUN — M1A/current admin access không intended-profile proof |
| LP05 | Object DML/ALTER/CONTROL/TAKE OWNERSHIP=0; check effective column-level SELECT/UPDATE grants bằng fn_my_permissions object subentity rows; catalog/module review bảo đảm không executable mutation path | NOT RUN — không chạy DML/DDL negatives |
| LP06 | Driver18/Encrypt=yes/TrustServerCertificate=no,validated connection và expected source identity; own diagnostics nếu được phép hoặc approved DBA corroboration; không tự cấp broad DMV rights | NOT RUN — admin TLS observed riêng |
| LP07 | Metadata columns/types/null/PK/FK/default/computed/temporal links đủ contract; missing metadata visibility giữ BLOCKED, object VIEW DEFINITION chỉ sau review nếu cần | NOT RUN |
| LP08 | Direct SELECT physical H và đúng current→history mapping; không collapse occurrences hoặc dùng current grant suy H grant | NOT RUN |
| LP09 | HAS_DBACCESS/permission checks cho DBA-approved unrelated user DB/object có expected denied scope; chỉ zero-row SELECT/connect attempt nếu Owner cho phép và không business payload | NOT RUN — no cross-DB test target supplied |
| LP10 | Source write-absence bảo đảm bằng scope/code review SELECT-only và effective permissions/DBA controls; không INSERT/UPDATE/DELETE/DDL để thử deny, kể cả rollback transaction | NOT RUN — evidence collection under intended identity |
| LP11 | Logs chỉ sanitized codes/identity fingerprint; secret ngoài Git, cursor/connection đóng; no automatic retry/security fallback | NOT RUN — future connector verification |
| LP12 | Fresh Windows session/token sau DBA-approved changes, re-evaluate all paths; unknown/missing proof chặn G02 release | NOT RUN |

Safe negative checks là metadata rights/allowlist rejection và bounded zero-row SELECT ở objects không nhạy cảm đã được DBA chỉ định. Không tạo database/table giả, không đổi grants, impersonate hoặc thực thi executable module để thử khả năng ghi. Rights-zero không tự chứng minh toàn bộ source không có writers; G01 tách riêng.


## 5. Owner approval / prepared scripts — current follow-up

[M1B-OD01–03](wwi-m1b-owner-decisions.md) approve dedicated non-admin Windows vàminimum object-level11-population direction,không approve actual account/login/user/metadata extras hoặc apply. [Setup](../../data-sources/security/wwi_extraction_identity_setup.sql),[read-only verify](../../data-sources/security/wwi_extraction_identity_verify.sql),[script README](../../data-sources/security/README.md) đã prepared cho review,NOT RUN. New-identity-only package là proposal;reuse existing cần alternate reviewed package,không tự alter.

Setup chỉCONNECT SQL/CONNECT DB/object SELECT,không role assignment/broad reader/write/admin/VIEW DEFINITION grant. Metadata gaps phải independently justify scope sau LP07. Windows account provisioning là separate OS-owner prerequisite;Windows/SQL names giữ placeholders. Guards0/NULL rejection/source checks/QUOTENAME/new-principal collision rejection vàtransaction cleanup đã static-reviewed,không SQL engine validation.

LP01–12 mapping: verify guard+identity/role-token/effective-permission reports;11 object rights+constant read probes bao gồm2 H;metadata columns/hidden definitions/current-H binding;column subentity permissions;negativeDB metadata;client TLS/group/code/log evidence external. VisibleColumns/hidden-definition counts0 không chứng minh metadata complete,phải so contract. Standard public metadata permissions ngoàiCONNECT được báo DBA_REVIEW_REQUIRED,không tự globally revoke hoặc silently allow;actual exception package còn review. Application-module/Windows-group/ownership closure vẫn DBA evidence,không dựa duy nhất role predicates hay single negative DB.

SQL scripts nằm ngoài migration/CI vàkhông được auto-execute. Offline [static tests](../../tests/source_security_static.py) chỉ đọc/mutate strings,không import DB driver hoặc execute SQL. G02 vẫn Pending/BLOCKED tới actual approved extraction logon verification.

## 6. EX01 Owner Approval và Execution Handoff

Các account-name-pending/preparation notes §1–5 là hồ sơ trước [Owner EX01 authorization](wwi-m1b-owner-decisions.md#7-owner-ex01-authorization--2026-11-16). Ngày2026-11-16 Owner approve local Windows principal `DESKTOP-OBDFK6B\wwi_extract` và intended future database-user name `wwi_extract`; Owner là OS Operator và local DBA. SQL mapping/grants chưa được approve hoặc thực hiện; script placeholders giữ nguyên.

[EX01-E01–E12](wwi-ex01-windows-identity-evidence.md) xác minh expected Git baseline, đúng machine, LocalAccounts commands có sẵn và target chưa tồn tại. Current process không có elevated admin token hoặc verified delegated provisioning authority; redirected input/output không là secure OS Operator secret channel. Vì vậy EX01 **BLOCKED before provisioning**, không create attempt/password collection; actual SID/groups/enabled/local restrictions/non-admin token/logon/profile/Python-under-target đều NOT RUN. Không kết luận current PC account là standard user chỉ từ filtered token.

Manual handoff trong evidence chỉ dùng private elevated Windows console của Owner và SecureString prompt, không password qua Codex, không automatic group/right/ACL changes. Interactive Python cần actual target token/profile và protected runtime access; scheduled task/service logon cần scope riêng. Developer Python không tự dùng approved Windows principal. LP01–12 vẫn NOT RUN, EX02 BLOCKED, G01/G02 pending; M1C/M2/M3 chưa được phép. Next EX02 cần EX01 proof, designated actual DBA principal/SID/authority và protected populated package/hash approval, không chỉ Owner role assignment.

## 7. EX01 Final OS Identity Handoff

[Owner EX01-R01 record](wwi-m1b-owner-decisions.md#8-ex01-r01-owner-remediation-record-và-final-review-authority) và [final evidence/acceptance](wwi-ex01-windows-identity-evidence.md#9-final-ex01-acceptance--os-identity-verification) resolve account requirement/target privilege gaps: same principal/SID-1007, Enabled/Local, PasswordRequired=True independent read-back, non-admin interactive/profile và supplied target privilege evidence đầy đủ. Final QA PASS → **EX01 DONE — OS Identity Verification** theo Owner task, không G02 PASS; prior absent/BLOCKED notes §1–6 là lịch sử.

Current **EX02 BLOCKED / Pending Authorization; G02 Pending Runtime Verification; G01 Pending Source Consistency Proof**. SQL login/user/11 object SELECT/current/H metadata/effective permissions/TLS còn chưa provision/verify trong workflow này; LP01–12 NOT RUN. Cần exact DBA execution identity/rights, protected staging/client và populated diff/hash/change/rollback + separate actual-context read-only verification approval. Không populate SQL placeholders hoặc cấp quyền ở EX01; M1C/M2/M3 chưa bắt đầu.
