# WWI-05 / M1B — Owner Decisions & Execution Preparation

**Authority: Project Owner; decision date2026-11-16.** Nguồn là task trực tiếp “WWI-05 / M1B-Approval — Owner Decision Recording & DBA Execution Preparation” trong phiên này; không chữ ký điện tử hoặc approval từ hệ thống khác. Initial main/HEAD `fe0099e6d409252628af6ce48e0248ef2abbd7f3`,working tree sạch.

**M1B-Approval IN_PROGRESS — preparation ready for Owner/DBA review, chưa accepted.** WWI-04 DONE Design,Phase1 Completed,Phase2/WWI-05 IN_PROGRESS,M1A DONE Verification,M1B DONE Planning Review;M1C/M2/M3 NOT STARTED.

## 1. Formal Owner decisions

| ID | Approved status | Exact scope | Exclusions / further approval |
| --- | --- | --- | --- |
| M1B-OD01 | APPROVED — Logical/Security Direction | Dedicated non-admin Windows extraction identity,minimum object-level privileges trên9 current+2 physical H;archive permissions riêng | Actual Windows account/login/user,exact script package,execution environment và apply authority còn review;không admin/server-wide/write privileges không cần thiết |
| M1B-OD02 | APPROVED — Preferred Approach | Chọn Option A Verified Static No-Writes Window cho initial consistent extraction;proof bao phủ extraction và relevant source reconciliation với explicit state boundary | Không approve G01 runtime;A không chứng minh được thì STOP và trình Option B consistent copy riêng,không silent switch |
| M1B-OD03 | AUTHORIZED — Documentation, Scripts and Test Preparation Only | Tạo/sửa docs,prepare DBA-review SQL/read-only queries/proof procedures/test plans,local static QA/Git review,one local preparation commit sau validation PASS | Không execute CREATE LOGIN/USER/GRANT/REVOKE/DENY/ALTER ROLE;không source data/schema/settings/CDC/CT/SNAPSHOT/RCSI,backup/restore/copy,dependency/infra/ingestion changes hoặc push |

## 2. Approved object coverage

| Schema | Object | Population |
| --- | --- | --- |
| Sales | Customers | Current |
| Sales | Orders | Current |
| Sales | OrderLines | Current |
| Sales | Invoices | Current |
| Sales | InvoiceLines | Current |
| Sales | CustomerTransactions | Current |
| Warehouse | StockItems | Current |
| Warehouse | StockItemHoldings | Current |
| Warehouse | StockItemTransactions | Current |
| Sales | Customers_Archive | Physical history |
| Warehouse | StockItems_Archive | Physical history |

Allowlist không thêm TransactionTypes/Purchasing/labels hoặc source systems. Reference extensions vẫn CG10. History SELECT riêng;không thay physical H bằng FOR SYSTEM_TIME ALL.

## 3. Direction versus execution state

| Layer | State tại task này |
| --- | --- |
| Approved logical/security direction | OD01;không còn pending direction “dedicated non-admin Windows” |
| Approved preferred consistency | OD02 Option A;không còn pending preferred A selection |
| Prepared administrative artifacts | [Setup](../../data-sources/security/wwi_extraction_identity_setup.sql),[Read-only verify](../../data-sources/security/wwi_extraction_identity_verify.sql),[README](../../data-sources/security/README.md) |
| DBA approval of exact populated script/change | NOT OBTAINED;DBA REVIEW REQUIRED |
| Approved executable changes / concrete Windows names | NOT APPROVED / NOT SUPPLIED |
| Executed changes | NONE |
| Intended identity / no-writes-window runtime PASS | NOT RUN;G01/G02 Pending/BLOCKED |
| Local static tests |12 tests PASS;không SQL parser/compiler/runtime proof |

M1B-D01 identity direction được OD01 resolve,actual account/profile pending;D02 object-level direction được resolve nhưng exact metadata/grants/evidence exceptions chưa approve;D03 preferred A được OD02 resolve,actual window/proof chưa approve;D04 operator/interval/evidence vàD05 conditional copy vẫn pending. D01–05 và7/7 planning review ở [M1B assessment](wwi-m1b-assessment.md) là hồ sơ trước approval;không sửa lịch sử thành approval đã có trước đây.

## 4. Prepared package và permission scope

Setup là **new-identity-only proposal**,không quyết định rằng Owner đã chọn tạo account mới. Existing principal → stop,không tự reuse/alter/revoke. Nếu Owner chọn reuse thì DBA phải trình exact alternate package. Windows account phải được provision/verified riêng trước SQL login creation;SQL FROM WINDOWS không tạo OS account.

Proposed direct grants: CONNECT SQL cho login,CONNECT WideWorldImporters cho database user vàSELECT ON OBJECT cho11 objects. Không custom-role assignment,db_owner/db_datareader/db_datawriter,broad SELECT hoặc metadata/server-state grants. Object VIEW DEFINITION **không có trong setup**;nếu independently required cần exact per-object justification/approval riêng.

Setup guards mặc định0,confirmation DO_NOT_EXECUTE,identity/change-reference placeholders;NULL cũng từ chối. Whole-batch execution/no batch separator,source identity/history-link checks,QUOTENAME+length validation,new-principal collision rejection vàtransaction/exception cleanup là prepared safeguards;không self-authenticating authority hoặc runtime guarantee. Không chạy riêng selection để bỏ guard.

[Identity proposal](wwi-source-identity-proposal.md) giữ LP tests;[consistency proposal](wwi-source-consistency-proposal.md) giữ operator proof plan;[DBA checklist](wwi-source-dba-owner-checklist.md) giữ exact next authorization request.

Normalized UTF-8/LF SHA256 của **prepared,unpopulated** SQL artifacts:
- Setup: `35f2a652f6c65606e555bdad6b2ab2a80488a59e68187a903e95c729919346c2`.
- Verify: `97753db1945915cf569c63a6cc07f5eba4a93750d3dbf17d904b875e573d568a`.

Sau khi điền actual names/references/flags,hash thay đổi;DBA/Owner phải review populated artifacts+diff+hash mới trước execution. Hash chỉ pin nội dung,không chữ ký hoặc execution approval.

## 5. Required independent execution authorization

| Request | Exact actions cần Owner approve tiếp | Prerequisites / proof |
| --- | --- | --- |
| EX01 — Windows identity | Reuse/provision named non-admin Windows account,group/logon/execution environment vàcredential delivery ngoài Git | Actual principal/TBD values resolved;OS owner+DBA xác nhận không local-admin hoặc inherited SQL elevation;không tự tạo account trong task này |
| EX02 — SQL security changes | Duyệt actual source/database,new-or-reuse mode,populated scripts/confirmed names/SIDs/package hashes/operator/change scope;chỉ package quyền được review | DBA independently review existing principals/public/groups/ownership/modules/DDL triggers và rollback dependencies;metadata extras riêng;source application/data/schema/config không đổi |
| EX03 — Source window operations | Named SO/operator,writer inventory vàexact actions pause/quiesce/drain;window/proof artifacts/boundary/failure/release responsibilities | Không single-DMV/count/timestamp shortcut;không KILL/locks/settings changes từ package này;A infeasible → stop and separate B review |
| EX04 — Runtime verification | Fresh intended Windows session,secure profile,read-only verify vàDBA corroboration/negative-target review;source readiness proof collection | Không impersonation/destructive negatives;all outputs/errors/NULLs retained;G02/G01 reviewer acceptance dựa actual evidence,không direction approval |

EX03 có thể chuẩn bị/rehearse writer controls khi được giao,nhưng **không tự cho Full Load/ingestion/M2/M3**. G01 capture-level proof phải bao phủ actual authorized extraction/source reconciliation ở task tương ứng;rehearsal hoặc identity tests không thay được proof đó. PostgreSQL Raw target vẫn pending từ M1A,ngoài task này.

## 6. Gate preservation và validation record

[Original31 gates](../data-models/wwi-implementation-gate-register.md) giữ nguyên IDs/structure/status;G01/G02/RG01/RG02/CG08 vẫn Pending/BLOCKED đúng operational context.72 inherited runtime scenarios NOT RUN,B9/INC/CP/D1–D4 policies không đổi.12 local text-contract tests không là SQL gate/runtime suites.

Actual local/static QA PASS:142 visible files/133 Markdown,1.122 local links/anchors không lỗi;đúng16 paths (11 existing docs sửa+5 files mới:2 Markdown/2 SQL/1 Python),126 protected baseline hashes không đổi.31 gate entries/72 NOT RUN scenarios,3 OD records/11-object allowlist/script hashes vàstatuses được kiểm;0 secret pattern/known-value findings;Python compile/in-memory AST vàformat/diff checks đạt.12 offline unittest methods PASS;không DB driver hoặcSQL execution.

SQL engine syntax/compile,setup,read-only verify vàstatic-window operations **NOT RUN**. Existing ScriptDom parser lookup không tìm thấyDLL trongaccessible inspected paths;vàiengine folders bịACL deny,khôngelevate/retry protected paths hoặcinstall parser. Text checks/manual review không làT-SQL compiler hoặcsecurity formal proof. Không connection tớiSQL Server/PostgreSQL hoặcDocker command trongtask hiện tại.

| Preparation criterion | Result | Evidence / limit |
| --- | --- | --- |
| OD01–03 exact scope/authority | PASS | §1,date/source direct Owner task,no signatures invented |
|11 allowlisted current/H objects | PASS | §2,setup/verify/static checks độc lập |
| Defaults/placeholders/NULL-safe guards vàquoting | PASS — static | Setup/verify vàmutation tests;khôngengine validation |
| Admin/verify separation vàautomation isolation | PASS — static | Standalonefiles,explicit offline test filename,no CI/migration binding/no DB API calls |
| Preferred A vàcomplete proof procedure | PASS — document | Procedure10 steps/writer inventory/evidence/failures;NOT EXECUTED |
| EX01–04 execution request | PASS — prepared | Checklist;actual names/operators/package/window/runtime authority chưa có |
| Approved policies/31 gates/72 scenarios | PASS — preservation | Protected hash/row checks,G01/G02 vẫnPending/BLOCKED |
| Links/secrets/scope/working diff | PASS | Actual counts ởtrên;staged check bắt buộc trướccommit |

Preparation checks PASS không phảiOwner acceptance:M1B-Approval vẫnIN_PROGRESS. Staged-content/security/diff validation phảiPASS trướcone local commit.

Actual staged validation PASS:16 blobs khớp working content sau Git line-ending normalization,0 staged secret findings,diff --cached --check đạt,no active hooks/no remote. Script normalization hashes ở§4 đã đối chiếu đúng.12 static tests không load/execute SQL;setup/verify/window/SQL compilation vẫnNOT RUN. Final staged check được lặp sau record này trướccommit.

Authorized commit sau QA: `docs: approve M1B directions and prepare source access execution`. Commit không close M1B-Approval hoặc approve executable changes;không push. Dừng sau preparation/report,không M1C/M2/M3.

## 7. Owner EX01 Authorization — 2026-11-16

Task trực tiếp “WWI-05 / EX01 — Windows Extraction Identity Provisioning & Verification” approve **EX01 Windows provisioning/verification only** cho `DESKTOP-OBDFK6B\wwi_extract`; future database user name `wwi_extract`. Project Owner là OS Operator và DBA local development. Không chữ ký từ hệ thống khác; không coi role assignment là proof current process elevated. OD01–03 giữ nguyên và các sections trước là lịch sử trước EX01 task, không còn diễn giải rằng exact Windows name chưa được duyệt.

Cho phép inspect/create exact local account nếu chưa tồn tại, secure credential collection chỉ trong OS Operator console, SID/groups/non-admin/logon/profile checks khi an toàn, sanitized docs/evidence và một local documentation commit sau QA PASS. Existing account → inspect only, không reset/recreate/change properties. Không SQL login/user/grants, group-policy changes, OS changes ngoài exact identity hoặc ACL ngoài account-creation necessity; không install/PG/Docker/ingestion/push. Thiếu privilege hoặc secure prompt → stop trước provisioning, manual handoff; blocked-documentation commit được phép nếu valid/useful.

[EX01 evidence](wwi-ex01-windows-identity-evidence.md) ghi actual baseline `main/a2f0ae2ac00303a32e1baeef37c60ef27f3070a7` clean, đúng máy, target absent; current token không elevated và input/output redirected. **EX01 BLOCKED before provisioning**, không create attempt, target SID chưa có. EX02 BLOCKED và không execution approval; G01/G02 pending, WWI-05 IN_PROGRESS. M1B-Approval không tự DONE và không mở M1C/M2/M3. Principal name được approve không tự bật hoặc populate SQL guards.

## 8. EX01-R01 Owner Remediation Record và Final Review Authority

Nguồn là task trực tiếp “WWI-05 / EX01 Final Acceptance & Evidence Update” ngày2026-11-16: Owner xác nhận **Owner-authorized EX01-R01** đã enforce PasswordRequired=True cho existing `DESKTOP-OBDFK6B\wwi_extract`, same SID `S-1-5-21-2164258108-3044412014-540060861-1007`; cung cấp successful runas/profile và exact target whoami /user + năm whoami /priv entries. R01 approval/result là Owner statement được ghi nhận tại đây, không original command/execution timestamp/external signature hoặc quyền cho Codex chạy lại remediation. OD01–03 và EX01 authority §7 giữ nguyên; BLOCKED notes của milestones trước là lịch sử.

[Final evidence/matrix](wwi-ex01-windows-identity-evidence.md#9-final-ex01-acceptance--os-identity-verification) corroborate flag/SID/account/groups/profile bằng local read-only checks và phân biệt supplied target token evidence. Captured before/after delta đúng account requirement; không claim forensic absence proof toàn OS. Owner conditional authority cho EX01 **DONE — OS Identity Verification khi mandatory criteria + final QA PASS**, một local commit `docs: accept EX01 windows extraction identity`; không SQL security execution, credential collection hoặc push.

EX02 BLOCKED/Pending Authorization; G02 Pending Runtime Verification, G01 Pending Source Consistency Proof; WWI-05/Phase2 IN_PROGRESS, M1B-Approval không tự DONE, M1C/M2/M3 NOT STARTED. Approval này chỉ OS identity acceptance, không whole source least privilege/SQL grants/staging/runtime/window/ingestion approval.
