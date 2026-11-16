# WWI-05 / EX01 — Windows Identity Execution Evidence & Handoff

**2026-11-16 — EX01 DONE — OS Identity Verification.** Current evidence tại **§9** resolve hai findings sau Owner EX01-R01: PasswordRequired=True và target privilege listing đã supplied; mandatory criteria/final documentation QA **PASS** tại §10 theo conditional Owner authority. §1–8/E01–E21 giữ nguyên lịch sử trước remediation. [Owner Record](wwi-m1b-owner-decisions.md#8-ex01-r01-owner-remediation-record-và-final-review-authority), [Checklist](wwi-source-dba-owner-checklist.md#11-ex01-final-acceptance--os-identity-verification), [Identity proposal](wwi-source-identity-proposal.md#7-ex01-final-os-identity-handoff), [TASKS](../../TASKS.md). Không G02 PASS hoặc EX02 execution authority.

## 1. Authority và preflight

Authority là task trực tiếp của Project Owner “WWI-05 / EX01 — Windows Extraction Identity Provisioning & Verification”, đính kèm ngày 2026-11-16. Không có chữ ký/approval từ hệ thống khác. Project Owner được chỉ định **OS Operator** và **DBA local development**. Chỉ Windows account `DESKTOP-OBDFK6B\wwi_extract` được approve provisioning/verification; future DB user name `wwi_extract` chưa là SQL execution approval.

Preflight Git **PASS**: branch `main`, HEAD `a2f0ae2ac00303a32e1baeef37c60ef27f3070a7`, working tree sạch và index trống. Đã đọc AGENTS, PROJECT_SCOPE, ROADMAP, TASKS, CHANGELOG, Phase1 closure, Owner Record, DBA checklist, identity proposal, security README và hai prepared SQL scripts. OD01–03/approved ADRs giữ nguyên. Task này không populate SQL templates, chạy EX02/EX03/EX04, sửa OS policies/ACL, cài software hoặc bắt đầu M1C/M2/M3.

## 2. Actual read-only observations

Evidence capture tại UTC `2026-11-16T14:18:07.0840709Z`, tương ứng `2026-11-16 21:18:07.0840709+07:00` (Asia/Bangkok). Mọi kết quả bên dưới là discovery thực tế; không phải authentication dưới account đích.

| Evidence ID | Check / actual result | Status / giới hạn |
| --- | --- | --- |
| EX01-E01 | Git `main` / expected HEAD / clean tree | PASS — preflight |
| EX01-E02 | Environment hostname và Win32_ComputerSystem cùng `DESKTOP-OBDFK6B`; PartOfDomain=false | PASS — đúng approved machine, local/workgroup model |
| EX01-E03 | Windows 11 Home Single Language, version `10.0.26200`, build26200, 64-bit | PASS — inventory |
| EX01-E04 | Windows PowerShell Desktop `5.1.26100.9818`, 64-bit process; LocalAccounts `1.0.0.0`; Get/New-LocalUser, Get-LocalGroup/Member available; New-LocalUser Password parameter là System.Security.SecureString | PASS — command availability; không thử create/WhatIf |
| EX01-E05 | Current process `DESKTOP-OBDFK6B\PC`, NTLM, IsSystem=false, current token IsInRole(Administrator)=false | BLOCKED — không elevated administrator token hoặc verified delegated provisioning authority; không kết luận PC không thuộc Administrators ở account level |
| EX01-E06 | UserInteractive=true **nhưng** Console InputRedirected=true và OutputRedirected=true; không có OS-Operator-controlled secure credential channel đã xác lập | BLOCKED — không gọi Read-Host/Get-Credential để lấy secret qua tool/chat; UserInteractive không đủ chứng minh secure entry |
| EX01-E07 | Get-LocalUser enumeration thành công, exact-name `wwi_extract` match count=0 | PASS — absence check, account chưa tồn tại tại observation; **không phải PASS provisioning** |
| EX01-E08 | Actual target SID, Enabled/PasswordRequired/restrictions, local memberships, effective non-admin token | NOT RUN — không có target account; không lấy current operator SID làm target SID |
| EX01-E09 | Secondary Logon service Running | PASS — service observation; actual logon rights/policy và authentication/profile vẫn NOT RUN/NOT VERIFIED |
| EX01-E10 | `whoami /priv` của current process: SeChangeNotifyPrivilege Enabled; SeShutdownPrivilege, SeUndockPrivilege, SeIncreaseWorkingSetPrivilege, SeTimeZonePrivilege Disabled | PASS — current-token inventory, không target-token proof hoặc delegated SAM privilege proof |
| EX01-E11 | Provisioning command, password collection, group/right/ACL changes | BLOCKED / NOT RUN — dừng theo task §5–6; chưa có creation attempt hoặc Windows creation error |
| EX01-E12 | Fresh target authentication, profile initialization, Python process under target identity | NOT RUN — prerequisites thiếu; không chạy developer Python để thay target identity proof |

Commands đã chạy chỉ đọc: Git status/branch/HEAD; Get-CimInstance Win32_ComputerSystem/Win32_OperatingSystem; WindowsIdentity.GetCurrent và WindowsPrincipal.IsInRole; PowerShell/process/console flags; Get-Command và parameter metadata; Get-LocalUser exact-name filter; Get-Service seclogon; whoami /priv. Nhánh group membership không chạy vì không có target. Không export/import local security policy hoặc tạo policy/evidence dump chứa toàn bộ machine accounts. Account-specific logon rights, restrictions và non-admin status còn **NOT VERIFIED**; không sửa quyền để làm test pass.

**Stop decision:** task §5–6 yêu cầu dừng nếu thiếu provisioning privileges hoặc không có genuine secure interactive password entry. Không thử elevation/UAC/helper/alternate principal/temporary password. Discovery command success không thay EX01 acceptance.

## 3. Manual OS Operator procedure — NOT EXECUTED

Owner đã có EX01 authority; không cần approve lại account name. Owner tự mở **Windows PowerShell 64-bit bằng Run as administrator** qua Windows UI trên đúng máy, trong console riêng do Owner kiểm soát. Không chạy đoạn này qua Codex/PTY/stdin redirection, pipeline hoặc remote chat; không gửi password cho Codex. Không tắt audit/security policy. Đảm bảo secure input và bảo vệ console/logs theo OS policy; nếu không bảo đảm thì dừng.

Đoạn dưới chỉ tạo exact approved account khi không có collision; không đổi group/right/policy/ACL. Không dùng NoPassword, PasswordNeverExpires hoặc thay expiration policy. Không lưu password vào environment, clipboard-based script source, file, history hay log. Microsoft hỗ trợ [New-LocalUser với SecureString](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.localaccounts/new-localuser?view=powershell-5.1) và [Read-Host -AsSecureString](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/read-host?view=powershell-5.1); masked prompt vẫn cần console boundary an toàn.

```powershell
# MANUAL OS OPERATOR ONLY — NOT RUN BY CODEX
$ErrorActionPreference = 'Stop'
if (-not [Environment]::Is64BitProcess) { throw 'STOP: use 64-bit Windows PowerShell.' }
$ex01Machine = Get-CimInstance Win32_ComputerSystem
if ($env:COMPUTERNAME -ne 'DESKTOP-OBDFK6B' -or $ex01Machine.Name -ne 'DESKTOP-OBDFK6B') {
    throw 'STOP: approved machine mismatch.'
}
$ex01Operator = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $ex01Operator.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'STOP: operator session is not elevated.'
}
if (-not [Environment]::UserInteractive -or [Console]::IsInputRedirected -or [Console]::IsOutputRedirected) {
    throw 'STOP: use a private interactive OS Operator console.'
}
$ex01Existing = @(Get-LocalUser -ErrorAction Stop | Where-Object { $_.Name -eq 'wwi_extract' })
if ($ex01Existing.Count -ne 0) { throw 'STOP: account exists; inspect only, no reset/recreate.' }
$ex01Secret = Read-Host -Prompt 'Enter password privately for wwi_extract' -AsSecureString
try {
    if ($ex01Secret.Length -eq 0) { throw 'STOP: an empty password is not allowed.' }
    $ex01Created = New-LocalUser -Name 'wwi_extract' -Password $ex01Secret -Description 'Retail WWI extraction identity' -ErrorAction Stop
    $ex01Created | Select-Object Name, SID, Enabled, PrincipalSource, PasswordRequired
}
finally {
    if ($null -ne $ex01Secret) { $ex01Secret.Dispose() }
    $ex01Secret = $null
}
```

Nếu tạo lỗi, giữ sanitized Windows error code/message và dừng; không retry/elevate tiếp/reset/delete hoặc đổi account khác. Nếu command outcome không rõ, kiểm exact existing account trước mọi action tiếp. Nếu tạo thành công nhưng verification fail, giữ account và trình remediation riêng, không xóa/tạo lại. Default memberships phải được quan sát; không tự Add/Remove-LocalGroupMember kể cả Users để giải quyết logon failure.

Manual read-only post-check trong console Owner, chỉ sau account tồn tại:

```powershell
# READ-ONLY MANUAL VERIFICATION — NOT RUN BY CODEX
$ErrorActionPreference = 'Stop'
if ((Get-CimInstance Win32_ComputerSystem).Name -ne 'DESKTOP-OBDFK6B') { throw 'STOP: wrong machine.' }
$ex01User = Get-LocalUser -Name 'wwi_extract' -ErrorAction Stop
$ex01User | Select-Object Name, SID, Enabled, PrincipalSource, PasswordRequired, AccountExpires, PasswordExpires, UserMayChangePassword, LastLogon
Get-CimInstance Win32_UserAccount -Filter "LocalAccount=True AND Name='wwi_extract'" |
    Select-Object Name, Domain, SID, LocalAccount, Disabled, Lockout, PasswordRequired
$ex01Groups = @(Get-LocalGroup -ErrorAction Stop | ForEach-Object {
    $ex01Group = $_
    $ex01Members = @(Get-LocalGroupMember -Group $ex01Group -ErrorAction Stop)
    if (@($ex01Members | Where-Object { $_.SID.Value -eq $ex01User.SID.Value }).Count -gt 0) {
        [pscustomobject]@{ Group = $ex01Group.Name; GroupSID = $ex01Group.SID.Value }
    }
})
$ex01Groups | Format-Table -AutoSize
if ($ex01Groups.GroupSID -contains 'S-1-5-32-544') { throw 'STOP: target is in Administrators.' }
if ((Get-LocalUser -Name 'wwi_extract' -ErrorAction Stop).SID.Value -ne $ex01User.SID.Value) {
    throw 'STOP: target SID changed during verification.'
}
```

All-group read error → incomplete membership proof, dừng và giữ error; không suy groups rỗng là verified non-admin. DBA/OS owner review mọi privileged/custom/nested group paths và effective rights; direct Administrators absence chưa đủ. Ghi exact SID đối chiếu hai reads/CIM, local domain, Enabled=true, PasswordRequired=true, account restrictions và memberships; bất kỳ mismatch nào chặn acceptance. Không đổi property/password/groups trong post-check.

Authentication/profile checks chỉ dùng fresh real local Windows session của `DESKTOP-OBDFK6B\wwi_extract` do Owner nhập secret trực tiếp; kiểm whoami /user, /groups, /priv và USERPROFILE trong đúng context. Nếu `runas /profile` được dùng thì không /netonly, /savecred hoặc impersonation; account profile/policy vẫn cần kiểm chứng. Không thử SQL login hoặc chạy module ingestion. Chỉ chia sẻ sanitized results/SID/groups/status, không credential/token/recovery data hoặc unrelated account inventory. Windows user-right effective policy do OS Owner kiểm đọc bằng công cụ được phép; không tự cấp Allow/Deny rights hoặc chỉnh machine policy.

## 4. Python runtime feasibility và implementation gates

| Model | Ý nghĩa / prerequisite | Current status |
| --- | --- | --- |
| Separate interactive Windows identity | Local account + actual logon eligibility/profile, ODBC18 và certificate trust trong correct context; Python process Windows token phải là approved account | PROPOSED model theo approved EX01 purpose; actual authentication/Python NOT RUN |
| Scheduled task/service | Cần riêng task/service definition, credential handling và effective batch/service logon rights; không suy từ interactive logon | NOT AUTHORIZED / NOT RUN trong EX01 |
| Developer session | Python chạy trực tiếp dưới PC dùng PC token; không tự thành wwi_extract. Nếu real alternate logon thì phải prove actual token/profile | Developer-token execution không được dùng làm target proof |

Current repository/venv inherited Modify gap ở Checklist §7 chưa được remediate. Trước future extraction phải có protected runtime code/interpreter/read-execute access và writable output riêng được duyệt; không cấp ACL hoặc copy deployment ở đây. Profile và client certificate trust không kế thừa bằng chứng developer một cách tự động. Không cần service/batch/RDP/admin privileges cho planned manual model; nếu thiếu Users membership/logon eligibility thì ghi prerequisite và trình narrowly scoped remediation, không tự thêm.

SQL Server login/user provisioning **NOT RUN / NOT PROVISIONED BY THIS WORKFLOW**. Không query SQL Server trong EX01 nên global existing SQL security state **NOT VERIFIED**, không khẳng định đã audit absence bằng SQL. DB user name chỉ là future mapping. G01/G02 Pending/BLOCKED; EX02 BLOCKED, chưa approve grants hoặc chạy scripts. WWI-05/Phase2 IN_PROGRESS; M1C/M2/M3 chưa bắt đầu.

## 5. Acceptance và handoff

| Acceptance requirement | Kết quả | Remaining work |
| --- | --- | --- |
| Exact authority/machine/Git baseline | PASS | Giữ fences khi Owner thao tác manual |
| Secure provisioning context | BLOCKED | Owner-controlled elevated console và secure password entry, không qua Codex |
| Account exists/enabled/local/SID | NOT RUN — absence verified | Manual create hoặc inspect nếu account xuất hiện; capture actual target SID |
| Expected groups/non-admin/effective privileges | NOT RUN | All-group + fresh-token + effective policy verification, không tự remediate |
| Logon/profile/Python suitability | NOT RUN | Actual-context checks/protected runtime prerequisites; không scheduler/ingestion |
| No unauthorized changes/secret handling | PASS — performed-action scope | Không OS/SQL/ACL/policy changes được thực hiện; không thu thập password |
| Documentation/static QA/Git | Ghi kết quả thực tế sau validation | Documentation commit không là EX01 runtime acceptance |

**EX01 overall BLOCKED**, không DONE/PASS. Approval name/role đã được giải quyết; execution prerequisites và mandatory verification chưa đạt. No Windows creation error có thể báo vì creation chưa được thử. Một lỗi encode stdout UTF-8 trong local Python documentation snapshot đã được sửa bằng process-only PYTHONIOENCODING, không account error hoặc machine configuration change.

Owner next action là manual EX01 procedure, sau đó gửi sanitized evidence để review/verify, không password. EX02 chỉ được đề nghị execution khi EX01 mandatory proof đã đủ, DBA operator identity/SID và privileges được chốt, protected staging/client và exact populated script hashes/change/rollback authority được Owner duyệt; negative DB/TLS/group proof và separate read-only verification scope còn prerequisites. Project Owner đã nhận role DBA nhưng actual approved DBA execution principal/SID chưa supplied; không mặc định PC/developer sysadmin là operator đó. Không đề nghị EX03 no-writes actions khi chưa concrete operators/window.

## 6. Documentation validation record

QA trước Git staging **PASS**: 13/13 existing offline security tests; cả hai manual PowerShell examples parse bằng built-in Parser với 0 syntax errors và **không execute**; 143 visible files/134 Markdown/1.145 local links và anchors không lỗi; đúng 7 documentation paths, 136 protected baseline hashes không đổi; 0 secret-pattern findings và `git diff --check` đạt. SQL setup/verify/checker và 31 gates/72 NOT RUN scenarios giữ nguyên. QA này xác minh documentation/package preservation, không account provisioning, authentication hoặc target non-admin proof.

Task cho phép một documentation/evidence commit khi provisioning BLOCKED nếu hồ sơ valid/useful. Trước commit phải kiểm lại staged scope/content/secret/size/diff và active hooks; commit message `docs: record EX01 windows extraction identity provisioning`. Commit SHA/final tree được báo sau khi tạo, không fabricated trong file này; không push. EX01 BLOCKED, EX02 BLOCKED, G01/G02 pending; không tự chuyển task/phase tiếp.

## 7. Post-Provisioning Evidence Review & Acceptance

### Authority, baseline và evidence sources

Owner task “WWI-05 / EX01 — Post-Provisioning Evidence Review & Acceptance” cho phép inspect **chỉ đọc**, reconcile Owner evidence, documentation QA và một local commit `docs: verify EX01 windows extraction identity`. Không cho sửa account/property/password/groups/user rights/ACL hoặc thực hiện EX02. Git preflight PASS: `main`, HEAD `f5755519647a221f659d96aa6d522a363c2d4177`, working tree sạch/index trống. Đã đọc AGENTS và các EX01 governance/evidence records. Không thay các approval/ADR trước đây.

**Owner-provided evidence** trong task trực tiếp: đã tạo `DESKTOP-OBDFK6B\wwi_extract`, Enabled=True, PrincipalSource=Local, SID `S-1-5-21-2164258108-3044412014-540060861-1007`; direct Administrators check không match; account mở được Windows PowerShell, session groups có BUILTIN\Users/standard identities, không Administrators, Integrity Level=Medium, USERPROFILE=`C:\Users\wwi_extract`. Password do Owner nhập tương tác và không cung cấp cho Codex. Đây là supplied narrative runtime evidence; không có raw token/privilege listing hoặc timestamp của session do Owner cung cấp. Không mô tả nó là test do Codex chạy.

**Independent local read-only inspection** tại UTC `2026-11-16T14:53:17.4153486Z`, tương ứng `2026-11-16 21:53:17.4153486+07:00` (Asia/Bangkok), dưới inspector `DESKTOP-OBDFK6B\PC`. Không target authentication, password access, SQL connection hoặc security mutations.

| Evidence ID | Observation / nguồn | Result và giới hạn |
| --- | --- | --- |
| EX01-E13 | Git/host preflight đúng f575551/main/clean; host DESKTOP-OBDFK6B, PartOfDomain=false | PASS — local inspection |
| EX01-E14 | Owner cung cấp successful target PowerShell session, standard groups, no Administrators token, Medium integrity, profile và interactive password-entry attestation | PASS — Owner-provided, không independent reauthentication hoặc full whoami /priv proof |
| EX01-E15 | Get-LocalUser Name=wwi_extract, Enabled=True, PrincipalSource.ToString()=Local; CIM Domain=DESKTOP-OBDFK6B, LocalAccount=True, Disabled=False, Lockout=False, Status=OK | PASS — local/CIM khớp supplied account; no account expiry, password expiry enabled, UserMayChangePassword=True |
| EX01-E16 | SID bằng `S-1-5-21-2164258108-3044412014-540060861-1007` ở Get-LocalUser trước/sau và CIM, khớp Owner | PASS — stable across these reads, không claim lifetime immutability |
| EX01-E17 | **PasswordRequired=False** ở cả Get-LocalUser và Win32_UserAccount | **BLOCKED** — trái explicit password-required acceptance; không suy ra actual password rỗng |
| EX01-E18 | Đọc members của toàn bộ17 local groups không lỗi, target có0 direct memberships; direct Administrators SID S-1-5-32-544 không match | PASS — direct membership audit; không giả lập actual target token |
| EX01-E19 | BUILTIN\Users (S-1-5-32-545) chứa NT AUTHORITY\Authenticated Users (S-1-5-11) và INTERACTIVE (S-1-5-4) | PASS — giải thích token Users có thể có dù target không direct member; không mâu thuẫn Owner evidence, không tự thêm Users |
| EX01-E20 | Win32_UserProfile cùng target SID, LocalPath=C:\Users\wwi_extract, Loaded=True, Special=False, Status=0 | PASS — profile local corroboration; successful logon/Medium integrity dựa Owner evidence |
| EX01-E21 | Actual target whoami /priv, exhaustive effective user-right assignments, target Python/ODBC/TLS/SQL verification | NOT RUN — không có password/token delegation hoặc authority mở các runtime tests đó; không dùng inspector privileges thay target proof |

Read-only commands: Get-LocalUser exact name trước/sau; Get-CimInstance Win32_ComputerSystem, Win32_UserAccount với exact local name filter, Win32_UserProfile với exact SID filter; Get-LocalGroup và Get-LocalGroupMember cho membership checks. Chỉ target/group-standard metadata được ghi, không unrelated members/password/token blobs. Account không bị mutate; không thử blank-password logon hoặc reset để kiểm mật khẩu.

### Reconciliation và independent acceptance matrix

PasswordRequired là account requirement flag, không phải disclosure/test của giá trị password hiện tại. [Microsoft Win32_UserAccount](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-useraccount) mô tả property này; [account flags](https://learn.microsoft.com/en-us/windows/win32/api/lmaccess/ns-lmaccess-user_info_1008) tách trạng thái password-not-required. Vì vậy Owner đã nhập password và local flag=False có thể cùng đúng; supplied evidence không resolve requirement flag. Không kiểm password value hoặc thử credentials.

| Acceptance criterion hiện có | Evidence | Result | Remaining work |
| --- | --- | --- | --- |
| Authority, exact machine và Git baseline | Owner approval, E13 | PASS | Giữ read-only/task boundaries |
| Exact local account, enabled và SID | E15–E16 | PASS | Giữ cùng SID khi remediation, không recreate |
| Password required | E17 | **BLOCKED** | Separate Owner-authorized account-specific remediation để PasswordRequired=True, sau đó read-back Get-LocalUser/CIM; không reset password từ review task |
| Known groups và non-admin session | E14/E18/E19 | PASS — direct audit + supplied non-admin session | Không nâng thành independent target-token test; không group changes cần thiết từ findings hiện tại |
| Không unnecessary elevated/account-management privileges | E21; Owner chưa cung cấp target privilege list | **NOT RUN — mandatory evidence còn thiếu** | Sanitized whoami /user và /priv từ cùng target session, review privilege paths bất thường nếu có; không cấp thêm privileges để kiểm tra |
| Interactive logon và profile | Owner session + E20 | PASS — supplied/corroborated | Detailed allow/deny policy export NOT RUN; successful concrete interactive session đủ chứng minh mode đó đã hoạt động, không xin blanket logon rights |
| Future Python model feasibility được phân biệt | §4, Owner có target PowerShell process | PASS — assessment | Actual Python/protected runtime/ODBC/TLS NOT RUN, prerequisites triển khai tương lai; không tự biến thành EX01 ingestion test |
| No unrelated OS/SQL/infrastructure change hoặc password exposure trong review | Executed-action scope | PASS | Không credentials được thu thập; chỉ metadata/doc/Git operations |
| Docs, links, static/security/scope validation | Kết quả QA bổ sung sau kiểm tra | Chưa suy PASS trước chạy | Commit chỉ sau QA PASS, không thay acceptance runtime |

**EX01 overall BLOCKED; không DONE — OS Identity Verification.** Hai remaining items cụ thể là password-required flag chưa đạt và target privilege inventory chưa đủ. Initial tool-elevation/secure-prompt blockers của E05–E06 đã được Owner manual provisioning vượt qua về mặt workflow, không tiếp tục dùng chúng làm lý do đóng chặn post-provisioning review. Không coi successful logon là proof password-required flag hoặc toàn bộ least-privilege SQL readiness.

### Narrow handoff và EX02 boundary

Owner cần cấp task remediation riêng chỉ cho exact existing principal/SID để enforce password-required mà giữ nguyên identity, groups, rights và current credentials; review này không được tự làm. Sau remediation kiểm lại flag/SID/enabled bằng read-only metadata. Không đề nghị reset password, delete/recreate hoặc chỉnh machine policy. Owner cung cấp sanitized `whoami /user` và `whoami /priv` từ fresh target session để gắn privilege evidence với đúng SID; không password hoặc raw access-token data. Nếu có unexpected privilege, trình scope remediation riêng.

Manual interactive mode đã chạy theo Owner evidence, nên không có bằng chứng cần cấp thêm Windows logon rights/group membership. Scheduled task/service/batch rights ngoài scope; detailed effective-policy inventory NOT RUN, không claim hỗ trợ các mode đó. Protected runtime deployment/code/venv access và TLS trust dưới actual target vẫn là prerequisites **future Python extraction/G02**, không lý do tạo thêm account hoặc thử developer-token Python thay thế.

EX02 và G02 **BLOCKED**, G01 pending;31 runtime gates/72 NOT RUN scenarios và WWI-05/Phase2 IN_PROGRESS giữ nguyên. EX02 cần EX01 acceptance đầy đủ, actual DBA Windows principal/SID/authority, protected staging/trusted SQL client, exact populated setup diff/hash và execution/rollback approval; separate read-only verify authority cùng negative DB/client TLS/group/ownership proof. Không SQL scripts/login/user/grants được chạy ở review này và không query SQL để khẳng định global security state. Không đề nghị EX03 operations hoặc tự bắt đầu M1C/M2/M3.

## 8. Post-Review Documentation QA

QA trước Git staging **PASS**: 13/13 existing offline security tests, 143 visible files/134 Markdown/1.148 local Markdown links và anchors không lỗi; đúng 4 existing documentation paths,139 protected baseline hashes không đổi,0 secret-pattern findings, `git diff --check` đạt. Owner Record/AGENTS/ADRs/identity proposal/security README và SQL setup/verify/checker không đổi; original EX01 acceptance row/status,31 gates và72 NOT RUN scenarios giữ nguyên. §5–6 là QA/acceptance lịch sử trước review này, không dùng các số liệu đó để thay kết quả hiện hành.

Documentation QA PASS không làm password-required hoặc target privilege criteria PASS. Staged content/scope/secrets/size/diff và hooks được kiểm trước commit `docs: verify EX01 windows extraction identity`; commit SHA/final tree báo sau actual commit, không tự ghi runtime acceptance. Không OS/SQL security changes, target authentication hoặc push.

## 9. Final EX01 Acceptance — OS Identity Verification

### Authority và provenance của bằng chứng

Owner task “WWI-05 / EX01 Final Acceptance & Evidence Update” ngày2026-11-16 cung cấp completion evidence của **Owner-authorized EX01-R01**, cho phép read-only verification và conditional EX01 acceptance nếu mọi mandatory criterion đạt, rồi một local documentation commit sau QA. Baseline **PASS**: main/`c6b097e0ed6b80f6c22534dabb88e2b01c5a83fb`, clean working tree/index. Đây không phải permission cho Codex thực hiện remediation hoặc EX02.

R01 authority/completion được ghi từ **Owner-provided statement trong task này**, không có external signature, original R01 command, execution timestamp hoặc OS-wide audit log được cung cấp. Remediation scope được ghi nhận là password-required requirement của exact existing principal/SID; không rewrite prior approvals hoặc mô tả Codex đã execute R01. Owner cung cấp successful interactive runas/profile, whoami /user đúng SID và target whoami /priv đầy đủ năm entries dưới đây; không tiết lộ password. Supplied group/no-Administrators/Medium integrity evidence E14 của cùng approved identity được giữ cùng latest SID/privilege evidence, không chỉ suy non-admin từ privilege names.

Independent read-only observation dưới inspector `DESKTOP-OBDFK6B\PC` tại UTC **2026-11-16T15:13:31.3174828Z**, tương ứng **2026-11-16 22:13:31.3174828+07:00** (Asia/Bangkok). Không authenticate target hoặc truy cập password để kiểm chứng.

| Evidence ID | Actual result / source | Classification |
| --- | --- | --- |
| EX01-E22 | Git/host đúng baseline, DESKTOP-OBDFK6B, PartOfDomain=false | PASS — independent preflight |
| EX01-E23 | Get-LocalUser và CIM cùng PasswordRequired=True; trước R01 E17=False | PASS — independent result corroborates Owner-reported remediation |
| EX01-E24 | Name=wwi_extract, Enabled=True, PrincipalSource=Local; SID trước/sau/CIM đều S-1-5-21-2164258108-3044412014-540060861-1007; CIM LocalAccount=True, Disabled=False, Lockout=False, Status=OK | PASS — independent; same identity, không recreate |
| EX01-E25 |17 local groups đọc không lỗi,0 direct target memberships/no direct Administrators match; Owner target-token group evidence E14 không privileged groups/Administrators, Medium | PASS — independent direct check + supplied target session; không claim Codex đọc fresh target token |
| EX01-E26 | Owner whoami /user xác nhận approved SID; whoami /priv chỉ có năm entries ở bảng dưới, không elevated administrative privileges xuất hiện | PASS — Owner-provided target runtime evidence, không inspector-token substitution |
| EX01-E27 | Profile same SID tại C:\Users\wwi_extract, Loaded=True, Special=False, Status=0; Owner interactive runas logon succeeded | PASS — independent profile metadata + supplied logon evidence |
| EX01-E28 | SID/name/enabled/local/groups/profile/lockout/password-changeability/expiry flags khớp E15–E20; observed captured-property delta là PasswordRequired False→True | PASS — bounded comparison + Owner R01 scope attestation; không OS-wide forensic change audit |
| EX01-E29 | Codex chỉ metadata inspection/docs/Git; target Python/ODBC/TLS/SQL verification, scheduled/service execution không chạy | PASS scope preservation; downstream runtime tests NOT RUN, không EX01 implementation claim |

Commands tái kiểm chỉ đọc: Get-LocalUser exact approved name trước/sau; CIM Win32_ComputerSystem/Win32_UserAccount exact local name/Win32_UserProfile exact SID; Get-LocalGroup/Get-LocalGroupMember. Không properties setter, password reset, group/right/ACL change, SQL connection, source/infra changes hoặc dependency installation.

### Target privileges — Owner-supplied, bound to approved SID

| Privilege | Supplied state | Assessment trong EX01 interactive model |
| --- | --- | --- |
| SeShutdownPrivilege | Disabled | Không unexpected administrative privilege được evidenced |
| SeChangeNotifyPrivilege | Enabled | Accepted standard Windows privilege trong supplied listing |
| SeUndockPrivilege | Disabled | Không unexpected administrative privilege được evidenced |
| SeIncreaseWorkingSetPrivilege | Disabled | Không unexpected administrative privilege được evidenced |
| SeTimeZonePrivilege | Disabled | Không unexpected administrative privilege được evidenced |

Không quyền admin/elevation khác xuất hiện trong supplied complete listing; không coi chỉ Disabled là đủ chứng minh mọi privilege an toàn. Assessment dùng cả exact SID, group/no-Administrators/Medium evidence, direct membership inspection và privilege inventory. Codex không lấy target password/token hoặc thực hiện independent runas; no expiry/lockout/policy guarantee cho mọi thời điểm tương lai.

### Independent EX01 acceptance matrix

| Mandatory criterion | Evidence | Result | Limit / downstream boundary |
| --- | --- | --- | --- |
| Approved scope, exact host và Git baseline | Owner authority/E22 | PASS | Giữ previous approvals và read-only review |
| Exact principal/local/enabled/SID stable | E24 | PASS | Identity verified ở observation này |
| PasswordRequired=True sau R01 | E23 | PASS | Không đọc hoặc assert giá trị password |
| Direct/inherited privileged group membership không evidenced | E25 và supplied target group/token evidence | PASS — independent/supplied | Không claim exhaustive all-machine security audit hoặc SQL effective permissions |
| No unexpected target privileges | E26 và bảng năm privileges | PASS — Owner-supplied | Hai mandatory evidence gaps của §7 đã resolve |
| Profile và intended interactive logon hoạt động | E27 | PASS — independent/supplied | Không cần grant thêm logon rights; scheduled/service model ngoài EX01 |
| R01 limited account requirement | Owner statement + E28 comparison | PASS — attested/corroborated | Original command/full machine audit NOT RUN; chỉ claim captured delta đúng scope, không fabricate absence proof cho mọi tài nguyên |
| Future Python process identity model được phân biệt | §4/E29 | PASS — assessment | Developer Python không tự thành target; protected runtime/ODBC/TLS tests còn implementation gates |
| No unauthorized changes hoặc credential exposure trong review | E29/action scope | PASS | Không password collected, không OS/SQL mutations |
| Docs/static/security/scope QA | Final QA record §10 | PASS chỉ sau actual QA | Không thay runtime findings bằng documentation-only PASS |

Conditional Owner authority đủ để ghi **EX01 = DONE — OS Identity Verification** sau final QA PASS; không còn mandatory EX01 finding chưa xử lý từ hai vòng review. Đây không là SQL least-privilege account/connection validation hoặc ingestion acceptance. Không cần thêm Windows group/logon/privilege grants cho đã-verified interactive model. Không thực hiện thêm R01 action trong review này.

### Remaining execution boundaries

**EX02 = BLOCKED / Pending Authorization; G02 = Pending Runtime Verification; G01 = Pending Source Consistency Proof; WWI-05 = IN_PROGRESS; M1C/M2/M3 = NOT STARTED.**31 original gates/72 runtime scenarios không tự PASS hoặc đổi policy. G02 source SQL login/user mapping/effective rights/TLS chưa được test; EX01 không là G02 PASS. Không query SQL Server trong task này.

Next EX02 cần named actual DBA Windows principal/SID/confirmed grant authority; protected staging PS01–08/trusted client; populated exact source-specific setup diff/hash/expected security delta và Owner execution/rollback authorization. Source allowlist9 current+2 physical archives không đổi. Sau setup được authorize riêng mới có separate actual-identity read-only verify authority/negative DB/TLS/group/module/ownership evidence. Không tự populate scripts, cấp SELECT/metadata privileges, khởi tạo SQL login/user hoặc authorize no-writes window. Runtime Python protected code/venv/access và client trust còn prerequisites triển khai tương lai, không mở lại EX01 OS acceptance.

## 10. Final Acceptance QA & Status Record

Actual final QA trước Git staging **PASS**: 13/13 existing offline static tests;143 visible files/134 Markdown/1.153 local links và anchors không lỗi; đúng7 existing Markdown paths,136 protected baseline hashes giữ nguyên;0 secret-pattern findings, `git diff --check` đạt. Original EX01 dependencies/acceptance criteria giữ nguyên, chỉ status BLOCKED→DONE; mọi prior task rows/status khác và31 gates/72 NOT RUN scenarios giữ nguyên. Original Owner OD01–03/EX01 approval text được bảo toàn, R01 record được append; SQL setup/verify/checker, AGENTS và ADRs không đổi.

Mandatory EX01 criteria và QA đều PASS → **EX01 DONE — OS Identity Verification** theo conditional Owner authority; không còn current EX01 blocker. Staged file/content/secret/size/diff/hook checks bắt buộc trước một local commit `docs: accept EX01 windows extraction identity`. Commit SHA/final tree báo sau actual commit, không push. EX02 BLOCKED/Pending Authorization, G02 Pending Runtime Verification, G01 Pending Source Consistency Proof; WWI-05 IN_PROGRESS, M1C/M2/M3 NOT STARTED. Không account/SQL/infra mutation, credential collection hoặc target reauthentication trong review.
