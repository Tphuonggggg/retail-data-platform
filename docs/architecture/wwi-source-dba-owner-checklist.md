# WWI-05 / M1B — DBA & Owner Action Checklist

**OD01/OD02 direction approved; exact execution package PREPARED — DBA REVIEW REQUIRED,2026-11-16.** M1B chỉ review/metadata SELECT/documentation, không Windows/SQL identity/grant/config changes. [Identity](wwi-source-identity-proposal.md), [Consistency](wwi-source-consistency-proposal.md), [M1B evidence](wwi-m1b-assessment.md), [existing Owner authority](wwi-phase-1-closure-approval.md). Recommendation không là APPROVED.

## 1. Pending decisions

| Decision ID | Vấn đề / options | Khuyến nghị và lý do | Required authority | Status |
| --- | --- | --- | --- | --- |
| M1B-D01 | Reuse approved non-admin principal hoặc chuẩn bị identity riêng; current developer sysadmin | Dedicated non-admin Windows Integrated identity; exact login/user/profile names TBD; giữ existing auth/TLS và tách developer/extractor | PO+DBA/OS owner duyệt identity/auth/logon scope,không tạo trong M1B | OD01 Direction APPROVED; actual names/package/execution pending |
| M1B-D02 | Object SELECT hay broad reader; metadata/TLS diagnostics rights | Exact SELECT allowlist,conditional metadata addenda nhỏ nhất; không broad reader/server-state role để tiện test | PO+DBA duyệt per-object package/exclusions/metadata proof | OD01 Direction APPROVED; actual names/package/execution pending |
| M1B-D03 | Concrete A static window hoặc B consistent copy | A ưu tiên khi đủ writer proof; nếu không đủ trình B,không tự failover/provision | PO+Source Owner/DBA chọn method trước capture | OD02 Preferred A APPROVED; exact window/proof/execution pending |
| M1B-D04 | Ai kiểm soát writers/interval hoặc xác nhận copy state | Named operator/writer inventory/drain/control evidence,T0/T1 và proof schema; không tự chọn fixed duration | SO/DBA+PO duyệt actions/evidence;IN/DQ kiểm prerequisites | PENDING OWNER/DBA APPROVAL |
| M1B-D05 | Nếu B cần tạo/restore copy | Proposal riêng supported method/provenance/license/capacity/endpoint/profile/generation protection; không B9/PG | PO+DBA/INF approve riêng trước creation/restore/config/identity action | PENDING — CONDITIONAL ON B |

Names/grant syntax/Windows execution setup/operator controls chưa chốt. M1B historical authorization chỉ cho review;current [OD01–03](wwi-m1b-owner-decisions.md) resolve direction/preferred approach vàcho artifact preparation,không administrative execution. D04/D05 vàactual names/package/window approvals vẫn pending.

## 2. DBA execution proposal — chưa chạy

| Step | Action sau approval riêng | Preconditions / review guard | Required artifact |
| --- | --- | --- | --- |
| DBA01 | Chốt actual source/identity/grant scope,review existing candidate và group/ownership/grant inheritance | Exact instance/database allowlist; không local/SQL administrator; không sửa developer identity mặc định | Baseline/token/Windows-group review,intended-principal identifier đã sanitize |
| DBA02 | Chuẩn bị exact change proposal cho reuse/create login/user/custom role và object SELECT; conditional VIEW DEFINITION | Chỉ sau D01/D02 và task authority;11-object/approved-slice inventory;không broad reader/writer/admin roles | Reviewed grant/membership/ownership diff và actual names,không password |
| DBA03 | Audit elevated paths qua public/guest/custom/fixed roles/Windows groups/schema ownership/column grants/grant options/application modules/IMPERSONATE/cross-DB | Own-context metadata cộng DBA closure;NULL/invisible không là denied proof; không DENY overlay admin | Forbidden paths absent hoặc explicit blocker chưa giải quyết |
| DBA04 | Owner authorize đúng change package,DBA thực hiện bằng identity riêng | M1B không cho apply;không actual DML/DDL/config changes ở task này | Authorized change record/operator outcome,secret ngoài Git |
| DBA05 | Fresh actual Windows extraction session,chạy LP01–12 chỉ đọc | Không EXECUTE AS/escalation/DML-negative;secure flags/allowlist fail closed | Expected/actual/status/SQLSTATE/version/proof refs từng test |
| DBA06 | Remediation/rollback nếu fail | Chỉ revert approved package changes có before/after và Owner scope;không tự xóa identities/grants dùng chung | Failed evidence giữ nguyên,reviewed corrective task;G02 chưa PASS |
| DBA07 | SO/DBA thực hiện selected window/copy actions sau method approval | SW/CPY plan và exact execution authority riêng;không bypass source-policy restrictions | Approved method/context C và actual proof/reconciliation trước G01 review |

Tại M1B Planning Review chỉ córeview logic,không privilege-changing SQL file. M1B-Approval nay đã prepare [setup](../../data-sources/security/wwi_extraction_identity_setup.sql) và[verify](../../data-sources/security/wwi_extraction_identity_verify.sql) theoOD03;DBA còn phải điền actual names/references,review diff/hash vàxin execution authority. Không SQL script được chạy. Backup/copy/admin rights của DBA không cấp cho extractor. Nếu cần tạo Windows account/service/logon setup thì xin scope riêng,không gộp ngầm vào SQL grants proposal.

## 3. Evidence package để review G02

- Approved endpoint/database/auth/expected principal/profile,secret delivery,TLS/driver/query bounds;không credential/DSN raw.
- Fresh effective identity/roles/tokens và DBA-reviewed Windows/local-admin/ownership/column/module/grant-option/cross-DB closure;exact SELECT allowlist và metadata sufficiency.
- LP01–12 expected/actual/status;negative checks bằng permission metadata hoặc approved zero-row SELECT,không thử DML/DDL rồi rollback.
- Missing rights → exact reviewed request,không self grant CONTROL/IMPERSONATE/server-state. Any elevation/unknown proof chặn G02 dù connection11 reads PASS.

## 4. Evidence package để review G01/RG01

A: approved writer inventory/controls,drained in-flight writes,T0/T1/capture scope/contracts/generation và no-writes proof xuyên bounds/current/H/source reconciliation;control-break handling. Matching count/hash/old timestamps/read-only login không thay primary proof.

B: approved copy provenance/recovery/committed boundary/compatible generation,least-privilege allowlist/no-writer protection và same-copy reconciliation. Creation/capability/license được duyệt trước;không tự dùng Express database-snapshot feature,cross-time logical export hoặc bật isolation. Thiếu proof giữ hold.

## 5. Next task boundary

Đề nghị Owner review,approve source-identity package và consistency/evidence plan,rồi giao tiếp trong **WWI-05 — Chuẩn bị WWI read-only và PostgreSQL đích**: DBA execution scope riêng và bounded re-verification. Chưa có administrative action được phép bởi recommendation này.

M1B planning completion không đóng WWI-05/M1 operational readiness. PostgreSQL Raw target vẫn pending từ M1A,ngoài M1B;không bắt đầu M1C/M2/M3,copy creation/target setup/ingestion hoặc install dependencies. B9 untouched;original31 gates/72 scenarios giữ nguyên.


## 6. Compact execution authorization request — READY FOR REVIEW, NOT AUTHORIZED

[Owner Record](wwi-m1b-owner-decisions.md) giữ OD01–03 và11-object allowlist. [Security README](../../data-sources/security/README.md) giữ inputs/guards/manual future procedure;[static checker](../../tests/source_security_static.py) không execute SQL.

| Authorization | Exact proposed request / artifacts | Missing approval/evidence before action |
| --- | --- | --- |
| EX01 Windows | Supply actual principal,OS provisioning/reuse/non-admin group/logon environment vàowner;không assume account tồn tại | OS owner/DBA review actual SID/group/local-admin paths;no credential inGit;actual names TBD |
| EX02 SQL | Review populated source-specific setup hash/change diff:FROM WINDOWS login,new DB user sameSID,CONNECT SQL/CONNECT DB và11 objectSELECT riêng H;new-identity-only proposal | Confirm new/reuse mode,exact names/operator/source context;existing principal collision stop;VIEW DEFINITION vàother metadata exceptions cần own justification,không chọn silently |
| EX03 Window | Approve named SO/DBA/application/scheduler operators vàconcrete writer inventory/quiesce/drain/T0→reconciliation→T1/release/failure plan | Existing stop/control procedures+all-writer proof;Agentstopped/singleDMV/count/timestamp không đủ;no settings/KILL/locking từ current package |
| EX04 Runtime | Approve fresh real extraction-context read-only verify,expected tests,negative userDB target/external group+TLS proof vàevidence retention/reviewer | Actual login/grants/profiles/window proof phải supplied;không impersonate/no destructive negatives;source control rehearsal không full capture proof |

### Script preparation and unresolved choices

Setup chỉ chuẩn bịnew identities,không tựreuse hoặcalter existing accounts. Windows principal/database-user names vàexternal authorization refs làplaceholders. Verify cũng yêu cầuactual negative userDB đượcDBA chỉ định vàexternal TLS/group proof. Default flags0/NULL rejection vàconfirmation tokens stop;human flags không thay signed/recorded approval artifacts.

Metadata extras chưa approved nênkhông có trongsetup. Verify báometadata sufficiency vàunexpected effective/public permissions đểreview,không tựgrant hoặcrevoke global public rights. Engine syntax/compile/behavior/permission enforcement cònNOT RUN;static tests không substitute independent DBA review.

### Rollback/revocation considerations — proposal only

Setup TRY/transaction rollback/rethrow xử lýSQL metadata failure trướccommit;DBA phải review DDL triggers/policies/external side effects,không claim toàn bộ audit/notification effects rollback. Saucommit,khôngautoDROP/revoke/disable:Owner/DBA phải review exact created SIDs/resources/dependencies,stop authorized extraction use vàchuẩn bịrollback package riêng;không ảnh hưởngusers/grants khác.

Revocation/access changes phải đượcverify trongfresh sessions theoapproved operator plan;khôngKILL sessions hoặcresetexistingidentity trongtask hiện tại. Failed setup/verify/window evidence giữ nguyên,no silent retry hoặcsecurity fallback. Nếu A infeasible,stop vàrequest B separately,khôngbackup/restore/copy creation.

### Expected evidence artifacts — templates, chưa tạo runtime evidence

Approved change request +populatedscript revision/hash;Windows provisioning/group review;DBA before/after security diff;actual source/profile/client TLS configuration proof;all verify resultsets/errors/NULLs/per-test statuses;writer inventory/operator actions/drain/start/end/boundaryC/capture+recon manifest references vàrelease decision. Credentials/PII/sourcepayload/backup ngoàiGit. Khôngfabricate operator signatures hoặc actual window.

Đoạn EX01–04 ở trên là danh mục bàn giao của package trước final review. Kết luận hiện hành tại §7 chỉ trình EX01/EX02; chưa đề nghị authorize EX03 operational execution khi chưa có suitable operators và concrete extraction window. Chưa actual execution approval,không M1C/M2/M3/ingestion/PG infrastructure. M1B-Approval vẫn IN_PROGRESS tớiOwner acceptance.

## 7. Final Security Execution Review — 2026-11-16

### Kết luận và authority

Preflight **VERIFIED**: branch `main`, HEAD `87b67f55d87d947e661aa491c035e3908fdd29f5`, working tree sạch trước review. Đã đọc AGENTS/TASKS, ADR liên quan, M1A/M1B, Owner Record và toàn bộ ba file security. Task hiện tại chỉ final pre-execution review và bounded correctness fix, không cấp quyền thực thi.

| Hạng mục | Kết quả | Điều kiện còn thiếu để trình exact execution approval |
| --- | --- | --- |
| EX01 Windows | **BLOCKED** | Owner chỉ định reuse/create và actual principal/SID; OS owner xác minh groups/logon/profile/TLS và protected runtime files. Chưa xác lập được dedicated identity phù hợp |
| EX02 SQL | **BLOCKED** | Bản setup sửa context đã qua static QA; actual names, negative database, named DBA, protected populated artifacts/diff/hash, independent DBA review và execution authority vẫn thiếu |

OD01–03 giữ nguyên **Approved logical direction / preparation only**. Concrete execution bên dưới là **PROPOSED**. Owner-authorized EX01/EX02 execution: **NOT OBTAINED**. Runtime-verified identity/grants: **NOT RUN**. G02 giữ Pending/BLOCKED; WWI-05/Phase2 IN_PROGRESS, M1C/M2/M3 Not Started. Không review lại architecture hoặc thay 31 gates/72 runtime scenarios.

### EX01 — Windows identity và operational model

Read-only inventory trong review này: host `DESKTOP-OBDFK6B`, Windows 11 Home Single Language 64-bit, `PartOfDomain=false`, `WORKGROUP`; 7 local users, 3 enabled. Không có local name khớp `wwi|retail|extract`; `wwi_extract` chưa tồn tại. Không có principal do Owner chỉ định để xác minh SID/effective groups. Name search không chứng minh mọi account khác đều không phù hợp; developer identity đã FAIL suitability ở M1A không được dùng thay extractor.

| Identifier / lựa chọn | Đề xuất cụ thể | Trạng thái |
| --- | --- | --- |
| Local Windows user | `wwi_extract` trên host hiện tại | PROPOSED nếu Owner không chỉ định được account dedicated phù hợp; chưa cho phép create |
| Windows principal / SQL login | `DESKTOP-OBDFK6B\wwi_extract` | PROPOSED; actual approved SID chưa có |
| Database user | `wwi_extract` trong `WideWorldImporters` | PROPOSED; phải map cùng SID với login |
| Actual script inputs | `<APPROVED_WINDOWS_PRINCIPAL>`, `<APPROVED_DATABASE_USER>` | Giữ nguyên placeholders trong repository; không coi tên đề xuất là approval |
| Change/verify inputs | `<APPROVED_CHANGE_REFERENCE>`, `<APPROVED_VERIFICATION_REFERENCE>`, `<APPROVED_NEGATIVE_DATABASE>` | Owner/DBA cung cấp sau; negative target phải là existing non-sensitive user DB, không tự tạo |
| OS owner / DBA / runtime operator | Chưa chỉ định | BLOCKED; không tự lấy developer làm operator được duyệt |

Mô hình đề xuất nhỏ nhất: manual Python process trên chính Windows host, dùng fresh real non-admin Windows logon và project-local Python đã được kiểm tra quyền file. Windows Authentication dùng token của process; local account cùng host là phương án khả thi để kiểm chứng, chưa là tested connection. Chưa có bằng chứng domain/trust cho domain principal; không đề xuất domain join, OS upgrade, SQL authentication hoặc Linux/Airflow Integrated Authentication trong task này. Nếu Owner chọn reuse, setup hiện tại không hỗ trợ: phải có alternate package được review riêng.

Logon requirements: local interactive session cần **Allow log on locally** và không bị Deny log on locally; kiểm effective policy, không mặc định từ group membership. Secondary Logon đang Running, nhưng quyền chạy `runas`/profile của proposed account chưa kiểm chứng. Nếu dùng `runas`, yêu cầu real alternate logon/profile; không `/netonly`, `/savecred` hoặc impersonation để thay bằng chứng token thực. **Log on as a batch job** chỉ cần cho scheduled-task model được duyệt riêng; **Log on as a service** chỉ cho service model riêng. Manual model không cần các quyền này, RDP, administrator, debug, backup/restore, take ownership hoặc impersonation privileges. Không thêm Administrators/Backup Operators/privileged custom groups; normal Users membership chỉ được chấp nhận sau effective-rights review. Policy truy cập SQL qua TCP dưới actual account vẫn NOT VERIFIED.

Actual account cần read/execute Python, libraries, code và approved non-secret configuration; writable outputs tách riêng. Credentials không đưa vào code/Git/command line. ODBC18 với Encrypt=yes/TrustServerCertificate=no giữ nguyên. Certificate trust trong profile mới phải kiểm chứng; không suy từ developer CurrentUser trust store hoặc bypass TLS.

**Protected handoff gap — VERIFIED observation, effective-account impact chưa kiểm chứng:** `Get-Acl` tại `D:\Code`, repository root và `.venv\Scripts\python.exe` có inherited **Allow Modify** cho Authenticated Users (`S-1-5-11`); Users có ReadAndExecute. Đây không là full effective ACL proof cho account chưa tồn tại, nhưng chưa đủ bảo vệ script/interpreter khỏi sửa trước lần chạy có đặc quyền. DBA phải dùng bản script populated được pin hash trong nơi không writable bởi extractor/untrusted users, kiểm ACL/hash ngay trước execute. Runtime code/venv cũng cần approved read/execute-only deployment cho extractor, outputs riêng; targeted staging/ACL action phải được duyệt riêng. Chưa sửa ACL, tạo deployment hoặc copy privileged artifacts trong review này.

Evidence commands đã dùng chỉ đọc: `git status --short`, `git branch --show-current`, `git rev-parse HEAD`; `Get-CimInstance Win32_ComputerSystem`/`Win32_OperatingSystem`; `Get-LocalUser` và đối chiếu candidates/membership; `Get-Service seclogon`; `Get-Acl` ba paths trên. Không ghi tên unrelated users, password hoặc full account inventory vào Git. Các command này không xác minh SQL login/token hoặc effective logon policy của future account.

### EX02 — SQL package review

Exact allowlist: `Sales.Customers`, `Sales.Orders`, `Sales.OrderLines`, `Sales.Invoices`, `Sales.InvoiceLines`, `Sales.CustomerTransactions`, `Warehouse.StockItems`, `Warehouse.StockItemHoldings`, `Warehouse.StockItemTransactions`; physical H riêng `Sales.Customers_Archive`, `Warehouse.StockItems_Archive`. Không thêm reference tables hoặc FOR SYSTEM_TIME ALL thay H.

| Tiêu chí | Kết quả review và giới hạn |
| --- | --- |
| 1. Allowlist | VERIFIED static: cả setup/verify đúng 9 current + 2 H, không schema/database-wide SELECT |
| 2. SQL Server 2025/17.x | Một correctness defect đã sửa: CONNECT SQL phải GRANT ở master; CONNECT database ở WideWorldImporters. Cấu trúc còn lại phù hợp documented SQL Server syntax; engine compile/runtime NOT RUN |
| 3. Mapping | FROM WINDOWS, user FOR LOGIN, type U và same-SID checks; không tạo OS account, không chấp nhận group/SQL-login như Windows user |
| 4. Permissions | Chỉ CONNECT SQL, CONNECT database và 11 object SELECT; không GRANT OPTION, roles, write, VIEW DEFINITION/server-state hoặc elevation grants |
| 5. Existing principals | New-identity-only, existing login/user thì STOP trước change; SID/name collision phải DBA review, không ALTER/reuse/drop tự động |
| 6. Identifiers/injection | Bounded identifiers, placeholders/whitespace/control checks và QUOTENAME trước dynamic use; source objects/db literals cố định; không concatenate credential hoặc executable input khác |
| 7. Rerun/failure | Không convergent/idempotent provisioning: rerun sau success bị từ chối an toàn. XACT_ABORT + TRY/transaction/rollback/rethrow; race/partial metadata failure không tự sửa existing objects. Commit outcome không rõ → inspect state/SIDs trước retry |
| 8. Guards | Flags 0, NULL-safe confirmation, explicit tokens, source fences/history bindings/no ambient transaction; chạy whole reviewed batch. Flags không tự chứng minh approval; DBA/operator có thể sửa/bypass text nên artifact integrity là prerequisite |
| 9. Escalation | Không có grant elevation trực tiếp. Public/groups/roles/ownership/modules/column rights/grant options/cross-DB paths vẫn cần independent DBA closure dưới actual identity; script không chứng minh toàn bộ effective security |
| 10. Verification | SELECT/metadata và constant TOP(1) probes; không DML/DDL negative tests, không source payload capture. NULL/invisible/error không là denied/PASS; optional DMV không có quyền thì NOT RUN |
| 11. Temporal coverage | Hai H được grant/probe riêng và kiểm current-history mapping; runtime metadata/hidden-definition sufficiency chưa verify, không tự thêm metadata permission |
| 12. Revocation | Precommit rollback có sẵn; postcommit cần exact reviewed rollback package và fresh-session verify, không destructive rollback tự động |

**Bounded defect fix:** source guard yêu cầu outer DB WideWorldImporters nhưng `@ConnectSql` trước review GRANT server CONNECT SQL ngay tại đó. Theo [Microsoft Server GRANT](https://learn.microsoft.com/en-us/sql/t-sql/statements/grant-server-permissions-transact-sql?view=sql-server-ver17), server-scope GRANT phải ở master. Bản sửa chỉ thêm `USE [master]` trước server GRANT rồi `USE [WideWorldImporters]` trước database GRANT trong cùng dynamic batch/transaction; không đổi outer source guard/quyền/batch separation. Static checker mới từ chối cả missing/wrong master và missing/wrong return context. 12 baseline tests PASS trước fix; 13 tests PASS sau fix. Kết quả này chưa phải engine execution proof.

### Artifact hashes và required operator privileges

SHA256 dưới đây của file hiện hành, UTF-8/LF chưa populated; hash setup/checker cũ trong historical record không còn pin bản mới. Hash verify giữ nguyên. **Chưa artifact nào được authorize execution.** Populating names/references/guards sẽ đổi hash; phải review exact diff và SHA256 mới, không approve dựa hash template.

| File | SHA256 |
| --- | --- |
| [setup](../../data-sources/security/wwi_extraction_identity_setup.sql) | `f655c3fdeb4a6ac3440ca89db7bb2bff426076ee605557f6b49fc95244ccc0c9` |
| [verify](../../data-sources/security/wwi_extraction_identity_verify.sql) | `97753db1945915cf569c63a6cc07f5eba4a93750d3dbf17d904b875e573d568a` |
| [offline checker](../../tests/source_security_static.py) | `4e6d59519c75d614a40ce3576f1f5f7ec6b4e2b5063de378898912b166ad4651` |

Proposed extractor permissions chính xác: server CONNECT SQL; database WideWorldImporters CONNECT; SELECT ON OBJECT cho đúng 11 objects trên. Không cấp quyền vào master objects bởi việc đổi context của DBA, không role assignments hoặc explicit metadata exceptions. Effective public grants vẫn phải review và không revoke public globally.

OS provisioning operator cần quyền quản lý local accounts và approved targeted file access trên host, dùng identity riêng; không chuyển quyền đó sang extractor. DBA cần quyền tạo login (SQL17: CREATE LOGIN hoặc quyền cao hơn phù hợp), tạo user trong WWI (CREATE USER hoặc quyền cao hơn), grant CONNECT SQL tại master, grant CONNECT/11 SELECT tại WWI với grant authority tương ứng, visibility đủ cho preflight/security/history review và xử lý transaction. Có CREATE LOGIN/USER riêng chưa đủ quyền GRANT. Named existing authorized DBA có thể dùng approved administrative session; không yêu cầu cấp sysadmin/securityadmin mới cho extractor hoặc operator chỉ để chạy test. Privileges của concrete DBA chưa được verify.

### Safe execution order — đề xuất, chưa được phép chạy

1. Owner quyết định exact EX01 principal/new-vs-reuse/manual Windows model và chỉ định OS owner/DBA/runtime operator; actual SID/group/logon/access/TLS profile phải được ghi nhận. Nếu chọn reuse hoặc có collision: STOP, review alternate package.
2. DBA hoàn tất independent rights/DDL-trigger/public/group/module review; chỉ định approved existing non-sensitive negative DB; ghi security baseline, expected delta và rollback dependencies. Thiếu visibility là blocker, không self-grant diagnostic rights.
3. Resolve protected staging/runtime access gap; populate scripts ở nơi được bảo vệ, giữ source fences/allowlist/guards. Review diff/hash/correct execution context và separate Owner change authorization; repository template vẫn không tự bật guards.
4. Chỉ sau exact authority: OS operator thực hiện approved EX01 scope, DBA kiểm lại identity/SID và chạy toàn bộ approved setup từ clean secure DBA session. Ghi commit/rollback outcome và before/after rights; không coi outcome marker là gate PASS. Ambiguous commit → kiểm state trước mọi retry.
5. Chỉ sau EX04 read-only verification authority riêng: fresh actual Windows extraction session, secure TCP/ODBC18/TLS; chạy populated verify, lưu mọi resultset/error/NULL và đối chiếu LP01–12. Expected SELECT=1, forbidden powers=0, negative DB access=0; empty table không là failed permission. Corroborate group/column/module/public/cross-DB closure với DBA; TLS certificate validation cần client proof. Không chạy dưới developer/admin hoặc EXECUTE AS.
6. Reviewer đánh giá đầy đủ evidence trước bất kỳ G02 decision riêng. Identity verification không chứng minh static no-writes window/G01 và không authorize Full Load. EX03 **chưa được đề nghị operational authorization**: named consistency operators và concrete extraction window vẫn thiếu; giữ procedure đã duyệt, không thực hiện writer controls.

### Rollback/revocation và Owner actions còn thiếu

Trước commit, setup rollback/rethrow xử lý transactional SQL security metadata; external trigger/audit/notification effects cần DBA đánh giá riêng. Sau commit chỉ dùng separately approved rollback: xác minh đúng newly created SID/login/user và exact direct grants từ before/after diff, dependencies/ownership/shared usage; dừng authorized extractor usage theo operator plan, thu hồi quyền/mapping/login trong đúng approved delta khi an toàn. Không drop/revoke existing/shared principals, không global DENY/public changes, không KILL hoặc tự disable account. Sau revocation kiểm fresh actual sessions không còn quyền đã thu hồi và existing users không bị ảnh hưởng; existing-session handling phải được duyệt trước. Giữ failure evidence; không blind rerun hoặc fallback admin.

Owner cần review **(a)** exact EX01 naming/reuse-create/manual model/operators, **(b)** protected artifact/runtime-access remediation scope, **(c)** populated EX02 package/hash/DBA grant authority/negative target/rollback, **(d)** separate EX04 verification scope sau prerequisites. Đây là danh sách quyết định còn thiếu, không approval hoặc request EX03 execution. Không tự thay existing business/architecture policies hoặc task statuses.

Offline QA command: đặt `$env:PYTHONDONTWRITEBYTECODE='1'` trong PowerShell process rồi chạy existing `.venv` Python với `-m unittest discover -s tests -p 'source_security_static.py' -v`; **13/13 PASS**. New checker tái hiện đúng context finding trên baseline setup và không còn finding trên bản sửa. Whole-repository static QA **PASS**: 142 visible files, 133 Markdown, 1.126 local links/anchors không lỗi; đúng 4 modified paths, 138 protected hashes giữ nguyên, 31 gates/72 NOT RUN scenarios giữ nguyên; 0 secret-pattern findings và không sensitive tracked paths theo kiểm tra, `git diff --check` đạt, index trống. Không import DB drivers, connect SQL/PostgreSQL, inspect/change B9/Docker, install software hoặc chạy pipeline; không commit/stage/push. Secret-pattern scan không thay exhaustive security proof; engine compile/runtime vẫn NOT RUN.

References cho reviewer: [CREATE LOGIN / SQL17 operator rights](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-login-transact-sql?view=sql-server-ver17), [CREATE USER](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-user-transact-sql?view=sql-server-ver17), [Object GRANT](https://learn.microsoft.com/en-us/sql/t-sql/statements/grant-object-permissions-transact-sql?view=sql-server-ver17), [STRING_AGG](https://learn.microsoft.com/en-us/sql/t-sql/functions/string-agg-transact-sql?view=sql-server-ver17), [Windows interactive logon right](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/security-policy-settings/allow-log-on-locally), [RunAs profile caveat](https://learn.microsoft.com/en-us/troubleshoot/windows-client/group-policy/group-policy-not-applied-user-account-runas). Platform documentation không thay actual identity/runtime proof.

## 8. Security Preparation Finalization — Owner authorization package

**2026-11-16 — PREPARED FOR OWNER REVIEW; EXECUTION NOT AUTHORIZED.** Task tiếp nối cho phép hoàn thiện preparation và **một local commit sau QA PASS**, không cho administrative execution. §7 là hồ sơ final review trước task này; ghi nhận index trống/no commit tại đó là lịch sử. Preflight task này: `main`, HEAD `87b67f55d87d947e661aa491c035e3908fdd29f5`, đúng bốn modified paths đã khai báo; index trống, không unexpected/untracked paths. Bảo toàn toàn bộ thay đổi trước, không sửa tiếp SQL/checker hoặc cập nhật task/gate status.

### Protected staging procedure — PROPOSED, chưa thực hiện

Thủ tục này chỉ áp dụng sau Owner duyệt scope và chỉ định operators. Không tạo staging directory, copy executable package, thay ACL hoặc mở SQL session trong task preparation.

| Bước | Yêu cầu và bằng chứng trước khi đi tiếp |
| --- | --- |
| PS01 — Chọn nơi bàn giao | Đề xuất một root do DBA quản lý dưới `C:\ProgramData\RetailDataPlatform\SecurityReview\<APPROVED_CHANGE_REFERENCE>`, **không phải path đã tồn tại/được duyệt**. Owner/OS owner chốt resolved absolute path; phải tách khỏi repository, `.venv`, developer Downloads/Temp và runtime writable output. Kiểm parent ACL, owner, reparse/junction/symlink; không dùng redirect về writable checkout |
| PS02 — Restrict access | OS owner chỉ cấu hình targeted ACL sau approval riêng: SYSTEM và trusted local Administrators FullControl; `<APPROVED_STAGING_CUSTODIAN>` Modify để chuẩn bị; `<APPROVED_DBA_WINDOWS_PRINCIPAL>` ReadAndExecute để đọc/chạy bằng SQL client. Đây là proposed access list, actual SIDs phải được duyệt; custodian/DBA có thể là cùng named operator nếu Owner chấp thuận. Loại inherited broad write grants; không Everyone/Users/Authenticated Users write/modify, không extractor write/ownership/permission-management. Kiểm effective rights cả parent và file, không chỉ nhìn inheritance flag; thiếu proof thì STOP |
| PS03 — Controlled copy | Custodian lấy đúng reviewed Git revision và kiểm template SHA256 §7 từ nguồn approval độc lập; copy **chỉ** hai SQL files và non-secret manifest vào staging chưa chạy. Không chạy Python/checker từ `.venv` bằng admin để bàn giao, không copy venv/repository tree/credentials hoặc dùng clone/sync/CI tự động. So SHA256 nguồn và đích trên **exact bytes** ngay sau copy; không overwrite existing change package khi chưa review |
| PS04 — Populate và freeze | Custodian điền approved names/references/confirmations chỉ trong protected working copy; review diff giữ source fences/11 objects/default template safeguards. Manifest ghi revision, path, encoding/line endings, SHA256 từng populated file, principal/SID, source context, expected delta, reviewers và change authority reference. Mọi edit kể cả LF↔CRLF tạo hash mới, phải review/approve lại. Template hashes không authorize populated artifacts; hash lưu cùng writable files một mình không bảo đảm integrity. Owner/DBA lưu approved hashes qua record được bảo vệ độc lập và đóng quyền sửa của custodians không còn nhiệm vụ trước execution |
| PS05 — Trusted SQL client | Named DBA dùng client có sẵn đã được DBA/OS owner xác minh origin/version, vendor signature hoặc approved binary hash và protected install/config path; ghi executable absolute path. Chưa chọn client cụ thể hoặc cho phép cài client mới. Không dùng tool từ checkout/venv, PATH lookup không kiểm soát, developer extension/startup task hoặc unreviewed helper. Client dùng fresh real DBA Windows context, approved TCP endpoint/source WWI, validated TLS và clean transaction context; không saved credentials trong repo |
| PS06 — Manual execution gate | Ngay trước execute, đối chiếu lại exact populated hash với approved record độc lập, file/parent ACL/owner và actual source/operator/SID; đọc file bằng trusted client từ protected copy. DBA chạy whole reviewed batch, không selected fragments/GO/include/SQLCMD directives hoặc auto-retry. Không Git hook, job, CI, IDE task hay normal ingestion automation nào được gọi setup từ development folders. Drift hoặc unknown commit outcome → STOP và review state, không blind rerun |
| PS07 — Verify và logs | Read-only verify chỉ chạy sau separate EX04 authority, trong fresh actual extractor Windows session. Nếu extractor cần đọc verify artifact, dùng protected **verification-only** copy/hash đã duyệt với Read cho extractor, không cấp nó quyền vào administrative setup area. Writable logs đặt riêng ngoài repo/venv/staging executable inputs; extractor chỉ được ghi authorized run output của mình, không script/config/hash approvals. DBA/approved evidence reviewer đọc/thu thập logs; OS owner kiểm ACL và ngăn writer sửa approved evidence sau collection. Giữ errors/NULL/SQLSTATE/per-test results, source/operator fingerprints, timestamps và before/after grant delta; không password/token/connection string/source payload. Log hash/manifest lưu độc lập sau collection; không coi writer-controlled logs là security proof duy nhất |
| PS08 — Release/retention | DBA/DQ review kết quả theo LP01–12; execution success không tự G02 PASS. Owner/custodian quy định access/retention/location cho logs và change artifacts, sanitized evidence mới được xem xét đưa Git. Không tự purge/overwrite artifacts hoặc rollback sau commit; dùng rollback authority/dependency checks ở §7. Không no-writes operations/EX03/Full Load/M1C/M2/M3 |

Staging SQL package và runtime Python deployment là hai phạm vi khác nhau. PS01–08 không tự giải quyết inherited Modify của project code/venv đã quan sát ở §7: trước future Python extraction, OS owner phải đưa phương án protected read/execute-only runtime code/interpreter và separate writable outputs, có approval/verification riêng. Không mở rộng quyền để dùng nguyên shared writable checkout bằng tài khoản privileged.

### Compact Owner decision request — mọi mục dưới đây PENDING

| Quyết định | Nội dung chính xác trình Owner | Trường phải điền / điều kiện |
| --- | --- | --- |
| EX01 — Account và mapping names | Đề xuất **tạo mới** local standard user `wwi_extract`, Windows/SQL login `DESKTOP-OBDFK6B\wwi_extract`, database user `wwi_extract` trong WWI; dedicated manual Windows Python process. Đây vẫn PROPOSED, không là account đã được duyệt/tạo | Owner chấp thuận create/naming/model hoặc chỉ định alternate reuse; `<APPROVED_OS_OPERATOR>` và `<APPROVED_EXTRACTION_OPERATOR>` chưa supplied. Collision sau approval → STOP, không overwrite/reuse |
| EX01 — OS scope | OS operator được duyệt thiết lập account/password theo OS policy, secret delivery ngoài Git; normal Users membership sau effective-rights review, Allow log on locally và không Deny; không Administrators/Backup Operators hoặc elevated group/privileges. Không batch/service/RDP rights cho manual model | Sau provisioning, ghi exact account SID, enabled state, effective groups/logon policy và fresh token; DBA đối chiếu Windows SID với SQL login/database-user SID. Profile, ODBC18, certificate trust và read/execute-only runtime access phải verify, không TLS bypass |
| EX02 — Exact SQL delta | New FROM WINDOWS login và same-SID user; CONNECT SQL cấp trong master, CONNECT trong WideWorldImporters, 11 object-level SELECT đúng §7 bao gồm hai physical H. Không role/broad reader/write/admin/VIEW DEFINITION/GRANT OPTION/server-state grants | Owner approve exact populated setup diff/hash + expected before/after delta và rollback scope, giữ machine/instance/database fences. Existing login/user hoặc insufficient metadata → STOP, không tự đổi package |
| EX02 — DBA/operator | Proposed role là một existing authorized DBA Windows identity tách khỏi extraction identity; identifier **`<APPROVED_DBA_WINDOWS_PRINCIPAL>`**, SID chưa supplied. Không coi developer/sysadmin hiện tại là designated operator | Owner chỉ định actual principal/SID và `<APPROVED_STAGING_CUSTODIAN>`, reviewer; DBA xác nhận CREATE LOGIN/CREATE USER và grant authority/visibility theo §7, OS owner chốt PS01 path/access list. Không tự cấp operator privileges |
| EX02 — Protected artifacts và authority | Approve PS01–08 với actual paths/principals/client; dùng template hashes ở §7 để review, sau đó chốt populated exact-byte hashes trong protected approval record. Execution order: approved EX01 provisioning/SID proof → independent DBA review/protected copy → exact EX02 authorization → manual setup | Phải có change reference, reviewer/operator, script revision/hash, run scope, source, collision/partial-failure handling và rollback decision. Commit preparation không thay authorization. Không chạy khi còn placeholders hoặc chưa review exact artifact |
| Runtime least-privilege verification | Đề xuất follow-up EX04 chỉ đọc sau EX01/EX02, bằng fresh actual extractor context; LP01–12 và DBA corroboration, external TLS/group/module/ownership closure, approved existing negative user DB. Giữ mọi failures/NULL; không DML/DDL negative tests | `<APPROVED_VERIFICATION_REFERENCE>` và `<APPROVED_NEGATIVE_DATABASE>` chưa supplied; cần separate bounded runtime authority. Runtime chưa chạy, không G02 PASS; không request EX03 khi chưa named consistency operators/concrete extraction window |

**Readiness:** preparation package sẵn sàng Owner review sau QA; **EX01 BLOCKED / EX02 BLOCKED for execution** tới khi các actual identifiers, staging/operator proof và exact authorities được cung cấp. OD01–03 unchanged; G01/G02 Pending/BLOCKED, WWI-05/Phase2 IN_PROGRESS; chưa M1C/M2/M3.

Scope local commit được Owner cho phép: đúng [checklist này](wwi-source-dba-owner-checklist.md), [security README](../../data-sources/security/README.md), [setup correctness fix](../../data-sources/security/wwi_extraction_identity_setup.sql), [offline regression checker](../../tests/source_security_static.py). Không tạo file mới; verify SQL giữ nguyên. Static/staged validation phải PASS trước commit `docs: finalize EX01 EX02 security execution review`; không push hoặc execution hook. Kết quả QA/commit thực tế được báo lại sau khi chạy, không suy từ permission cho commit.

QA finalization trước Git staging **PASS**: 13/13 offline security tests; 142 visible files/133 Markdown/1.132 local links và anchors không lỗi; đúng 4 modified paths, 138 protected baseline hashes không đổi; 0 secret-pattern findings, `git diff --check` đạt. Setup/verify/checker hashes khớp §7; bản SQL/checker của final review được giữ nguyên trong task finalization này. 31 gates/72 NOT RUN scenarios và task statuses giữ nguyên. Không active Git hooks được tìm thấy trong configured/default hook location lúc kiểm tra; staged scope/blob/secret/hash/diff checks phải được lặp ngay trước commit. Không SQL/runtime/ACL/account/staging operations được thực hiện.

## 9. EX01 Authorized Windows Task — BLOCKED Before Provisioning

Current follow-up ngày2026-11-16 supersede pending-name/operator-role notes ở §7–8: [Owner EX01 authorization](wwi-m1b-owner-decisions.md#7-owner-ex01-authorization--2026-11-16) approve `DESKTOP-OBDFK6B\wwi_extract`, future DB user `wwi_extract`; Project Owner là OS Operator/DBA. Đây không approve EX02 grants, actual DBA execution principal, protected staging hoặc runtime G02.

[EX01-E01–E12 evidence và manual handoff](wwi-ex01-windows-identity-evidence.md) ghi đúng expected Git baseline/host, target account chưa tồn tại, process PC không elevated administrator token, stdin/stdout redirected và secure OS Operator password channel chưa có. Theo task §5–6 dừng trước account creation. **EX01 BLOCKED**, target SID/groups/non-admin/logon/profile NOT RUN; không dùng operator token làm target evidence. Không SQL/OS account/policy/ACL changes hoặc password collection trong task này.

Next action: Owner dùng private elevated Windows console theo manual procedure trong evidence; account collision → inspect only, error/missing verification → stop, không reset/recreate hoặc tự grant logon/group rights. Không cần duyệt lại exact EX01 name; cần actual execution evidence trước acceptance. EX02 vẫn BLOCKED đến khi EX01 proof/actual DBA identity+grant authority/protected staging+trusted client/populated diff/hash/rollback+separate execution approval đầy đủ. G01/G02 pending; không đề nghị EX03 operations hoặc bắt đầu M1C/M2/M3. Một local documentation/evidence commit được task EX01 cho phép sau QA PASS kể cả provisioning BLOCKED; các commit/no-commit notes trước đây là lịch sử.
