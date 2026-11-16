# WWI-05 / EX01 — Windows Identity Execution Evidence & Handoff

**2026-11-16 — EX01 BLOCKED trước provisioning.** Owner đã approve exact EX01 Windows scope; thiếu execution prerequisites, không phải thiếu approval cho account name. [Owner Record](wwi-m1b-owner-decisions.md#7-owner-ex01-authorization--2026-11-16), [Checklist](wwi-source-dba-owner-checklist.md#9-ex01-authorized-windows-task--blocked-before-provisioning), [Identity proposal](wwi-source-identity-proposal.md#6-ex01-owner-approval-và-execution-handoff), [TASKS](../../TASKS.md).

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
