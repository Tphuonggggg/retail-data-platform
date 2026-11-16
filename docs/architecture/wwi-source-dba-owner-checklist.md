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

Next requested work làOwner review EX01–04 vàDBA independent review/parameterization. Chưa actual execution approval,không M1C/M2/M3/ingestion/PG infrastructure. M1B-Approval vẫn IN_PROGRESS tớiOwner acceptance.
