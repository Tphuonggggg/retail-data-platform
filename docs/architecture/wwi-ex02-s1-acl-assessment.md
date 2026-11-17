# EX02-S1 — Đánh giá ACL và chuẩn bị protected staging

**Current status: DEFERRED — OPTIONAL SECURITY HARDENING.** Owner [MVP-SIMPLIFICATION-01](wwi-m1b-owner-decisions.md#mvp-simplification-01--trusted-local-mvp) supersede protected-staging/ACL/mandatory execution-manifest blockers cho trusted local MVP. Không cần resolve ancestor/inheritance findings để tiếp tục MVP; không apply ACL/tạo staging. Sections1–8 và SHA256 bên dưới là **historical preparation evidence tại commit f1d1fc4**, không current execution approval hoặc hashes của deferred status metadata mới. Giữ nguyên findings để revisit hardening khi có scope riêng; [local EX02](../../data-sources/security/README.md#10-local-mvp-setup--pending-runtime-authorization) là current handoff.

Ngày: 2026-11-17. **PREPARED — BLOCKED FOR IMPLEMENTATION.** Đây là hồ sơ chuẩn bị theo task Owner “Protected Staging ACL Remediation & Execution Preparation”, không phải chấp thuận chạy ACL hoặc EX02. Các quyết định M1B-OD01–03, EX01/R01 và kiến trúc đã duyệt giữ nguyên.

## 1. Preflight và ranh giới bằng chứng

| Hạng mục | Kết quả quan sát |
| --- | --- |
| Repository thực tế | `D:\Code\Retail_Data_Platform\project1_Retail_Data_platform`; Owner đã di chuyển trước task, task này không move |
| Git ban đầu | `main`, HEAD `f3c96169f81a19cfadfc9a79921fa129d6bf950d`, working tree sạch, 144 tracked files |
| Máy / operator | `DESKTOP-OBDFK6B`; `DESKTOP-OBDFK6B\PC`, SID `S-1-5-21-2164258108-3044412014-540060861-1001` |
| Token hiện tại | Không elevated; được phép inspection/offline preparation. Future operator scripts yêu cầu elevated PC token; không tự nâng quyền |
| D: | NTFS, volume serial `3EB49503` |
| Protected staging | `D:\Code\Retail_Data_Platform\Retail_EX02_Protected_Staging` chưa tồn tại |
| Reparse | Không thấy reparse point tại `D:\`, `D:\Code`, parent và repo; staging chưa có để inspect |
| Mốc capture ACL | UTC `2026-11-17T04:35:09.1838378Z`; toàn bộ Owner/Group/DACL trước thay đổi nằm trong `before` của [ACL plan](../../data-sources/security/staging/acl-plan.json) |
| Môi trường offline | Windows PowerShell `5.1.26100.9818`, CLR `4.0.30319.42000`; reflection xác nhận có overload `Directory.CreateDirectory(String, DirectorySecurity)`, chưa gọi tạo thư mục |

Inspection dùng `Get-Acl`, `Get-Item`, WindowsIdentity/WindowsPrincipal, `Get-CimInstance Win32_LogicalDisk` và Git. Không thử delete/rename, không đổi ACL/account/SQL, không dùng extractor password. SID và đường dẫn là sanitized identity evidence, không credentials.

## 2. ACL hiện tại và effective access

Quy ước: SY = SYSTEM (`S-1-5-18`), BA = Administrators (`S-1-5-32-544`), AU = Authenticated Users (`S-1-5-11`), BU = Users (`S-1-5-32-545`), PC = SID-1001. Không thấy Deny ACE trong bốn DACL. Cả bốn còn inheritance; staging chưa có ACL.

| Path | Owner | ACE áp dụng trực tiếp lên folder | ACE inherit-only cho con |
| --- | --- | --- | --- |
| `D:\` | SY | SY/BA FullControl; AU Modify+Synchronize `0x1301bf`; BU ReadAndExecute+Synchronize `0x1200a9` | BA/SY GenericAll; AU `SDGXGWGR`; BU `GXGR` |
| `D:\Code` | PC | Như trên, inherited | Bốn stream trên, inherited |
| `D:\Code\Retail_Data_Platform` | BA | Như trên, inherited | Bốn stream trên, inherited |
| Repository root | PC | Như trên, inherited | Bốn stream trên, inherited |

Mask AU `0x1301bf` có CreateFiles/WriteData, CreateDirectories/AppendData và **DELETE `0x10000`**, nhưng **không FILE_DELETE_CHILD `0x40`**, WRITE_DAC `0x40000` hoặc WRITE_OWNER `0x80000`. Không diễn giải Modify thành DeleteChild. Inherit-only ACE không áp dụng cho chính folder; generic rights phải xét mapping khi inherited. Xem [Microsoft access rights](https://learn.microsoft.com/windows/win32/wmisdk/file-and-directory-access-rights-constants) và [ACE inheritance](https://learn.microsoft.com/en-us/windows/win32/secauthz/ace-inheritance-rules).

Đây là đánh giá theo DACL/group class và owner rights, không phải Windows Authz AccessCheck cho mọi token. PC là trusted operator được Owner chỉ định cho task chuẩn bị, có owner rights ở Code/repo và quyền AU; token không elevated không biến PC thành một identity không được tin cậy. SYSTEM/Administrators có FullControl. Git đọc hoạt động; VS Code/write/execute workflow sau ACL apply **NOT RUN**.

## 3. Parent cần thiết nhưng chưa đủ

1. **Hiện tại chưa an toàn:** AU có DELETE trên parent `Retail_Data_Platform` và CreateDirectories tại Code. Suy luận từ quyền cho thấy identity ngoài trusted set có đường rename/replace namespace của parent; staging protected riêng không giải quyết rủi ro này. Không thực hiện destructive proof.
2. **Cần xử lý parent:** loại broad self Modify/Delete ở parent và bảo vệ DACL của staging sẽ tạo immediate boundary. Chỉ tắt staging inheritance không đủ.
3. **Vẫn còn tổ tiên:** `D:\Code` cũng có AU DELETE; `D:\` có AU CreateDirectories. Bảo vệ parent/staging không chứng minh tính ổn định của absolute path nếu Code có thể bị rename/replaced. Task yêu cầu Code không đổi, nên không được tự mở rộng ACL remediation tới Code hoặc D:.
4. **Không có acknowledgement bypass:** các script apply/verify/rollback từ chối khi ancestor có untrusted Delete/DeleteChild/WriteDacl/WriteOwner tương ứng. Owner cần control riêng được review, giữ Code unchanged, hoặc task mới điều chỉnh scope. Cơ chế giữ handle/namespace là hướng cần nghiên cứu riêng, **chưa thiết kế hoặc chứng minh** trong package này.
5. **Không chạy elevated code từ repo:** repo vẫn writable theo thiết kế phát triển. Việc dot-source helper trước guard cũng cần trusted bootstrap đã được operator kiểm độc lập; hash nằm cạnh file writable không phải trust anchor. Chuỗi thư mục chứa bootstrap/backup cần kiểm tra tương tự.

Quyền xóa object và quyền delete-child của parent là hai đường cấp quyền khác nhau; xem [Microsoft DeleteFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-deletefilea). Đánh giá directory namespace ở đây là suy luận bảo mật từ ACL, không báo rename runtime PASS/FAIL.

## 4. Exact target ACL delta — PROPOSED

| Path | Delta đề xuất | Phạm vi kế thừa / owner |
| --- | --- | --- |
| `D:\`, `D:\Code` | **Không thay đổi** | Giữ nguyên Owner/Group/SDDL; ancestor blocker chưa được giải quyết |
| `Retail_Data_Platform` parent | Protect DACL. Bỏ các ACE inherited áp dụng lên chính folder; thay bằng đúng **SY, BA, PC: FullControl, This folder only**. Không giữ AU/BU self access, không thêm Deny | Giữ owner BA, primary group cũ. Giữ nguyên bốn stream inherit-only về mask/SID/thứ tự/OI+CI+IO, chuyển thành explicit vì protect DACL; không thêm propagating PC FullControl |
| Repository và `.venv` | **Không Set-Acl, không sửa trực tiếp** | Điều kiện trước apply: phải chứng minh parent update không làm thay đổi ACL/control bits của repo/venv và những child hiện hữu; hiện chưa có runtime proof |
| Staging mới | Protected DACL ngay khi tạo: **SY, BA, PC: FullControl OI/CI**; đúng ba Allow ACE | Owner/group BA. Không AU/BU/extractor, không Deny. Nếu folder đã tồn tại thì STOP, không reuse/overwrite |
| Bootstrap / ACL backup | Đề xuất existing trusted bootstrap do Owner cung cấp và existing trusted backup directory `C:\ProgramData\RetailDataPlatform\AclBackups` | Chưa tạo, chưa approve ACL. Backup file exact name trong plan, CreateNew/no overwrite; không tự provision thư mục hoặc cấp quyền |

Hai target SDDL exact nằm tại `target_parent_sddl` / `target_staging_sddl` của ACL plan, là nguồn duy nhất cho prepared scripts. FullControl của PC là quyền trusted custodian có thể thay ACL/artifact; đây không phải tuyên bố chống chính PC hoặc elevated administrators.

**Rủi ro propagation:** thay parent inheritable ACEs có thể lan tới các child hiện hữu, kể cả metadata/control flags dù giữ effective inherited stream. [Microsoft automatic propagation](https://learn.microsoft.com/en-us/windows/win32/secauthz/automatic-propagation-of-inheritable-aces) mô tả việc thêm/bỏ inherited ACE trên child. Giữ bốn stream là đề xuất giảm tác động, **không chứng minh repo ACL unchanged**. `repository_inheritance_preservation_verified=false` chặn apply; không tự protect repo hoặc thực hiện recursive repair để vượt guard.

## 5. Scripts và quy trình tương lai

Package tại [staging README](../../data-sources/security/staging/README.md). Chỉ chuẩn bị, **không chạy bốn operator entry scripts** trong task này.

| Artifact | Chức năng / hành vi khi thiếu điều kiện |
| --- | --- |
| `acl-common.ps1` | Guard machine/operator/SID/elevation/NTFS/serial/path/reparse; kiểm target policy, ancestor, trusted bootstrap/backup, before-state và SHA256 độc lập |
| `01-preflight-backup.ps1` | Mặc định readonly; future `WriteBackup` cần OwnerAuthorized và existing trusted directory; CreateNew, không overwrite; backup Owner/Group/DACL, không SACL |
| `02-create-protected-staging.ps1` | Chỉ được Set-Acl parent và tạo exact staging với initial protected descriptor khi mọi gate đạt. Recheck parent, repo/Code ACL, concurrent existence, staging final descriptor. Plan hiện tại khiến script STOP trước mutation |
| `03-verify-acl.ps1` | Readonly: kiểm ancestors, không reparse, exact trusted target descriptors, Code/repo unchanged. Không suy runtime SQL PASS |
| `04-restore-parent-acl.ps1` | Separate Owner rollback authority, pinned backup và exact expected after-state. Chỉ khôi phục parent; không delete staging/artifacts hoặc sửa repo |

Trình tự tương lai: Owner giải quyết blockers §3–4 → review revision/hash/authority riêng → independently verify trusted bootstrap/client/backup directory → preflight và backup hash vào approval record độc lập → apply exact parent/staging → readonly ACL/effective-token verification → Owner accept staging. SQL artifact copy/activation/security execution là task riêng sau manifest amendment, không phần của trình tự ACL này. Không cung cấp lệnh bật approval flag như một shortcut để vượt blockers.

Partial failure sau parent Set-Acl phải STOP, giữ trạng thái/logs, không tự rollback hoặc delete/recreate. Nếu Code/repo đúng baseline và parent đúng target, Owner có thể authorize reviewed parent-only rollback. Nếu propagation/drift xảy ra, script rollback cũng từ chối: Owner/OS operator phải review captured before/after, recovery scope riêng. Khôi phục parent có thể tái mở broad rights và ảnh hưởng inheritance; không tiếp tục SQL hoặc tin artifacts trong quá trình recovery. Staging giữ nguyên; cleanup cần task riêng. Backup/hash phải truy cập được từ elevated trusted recovery context; không dựa repo/venv.

Logs chỉ chứa path/SID/SDDL/hash/status/timestamp; lưu ở evidence location có ACL được duyệt riêng, no overwrite. Không password, connection secrets hoặc SQL source data. Script không tự copy artifact hoặc ghi logs ngoài exact backup file được duyệt.

## 6. SHA256 cho Owner review

Hash là exact working bytes UTF-8/LF; không chữ ký, không execution authorization. Owner đối chiếu độc lập từ commit đã review và trusted copy; bất kỳ edit/BOM/newline conversion nào đều cần tính lại và review.

| File trong `data-sources/security/staging/` | SHA256 |
| --- | --- |
| `acl-plan.json` | `2eb1ed70ab02dd4bf056f65f784258ebf1cd88cbd5cd4a2720e83cad020c47ab` |
| `acl-common.ps1` | `ae7667321b799180c5fb3329a1c1e460a563bc49d0606d641a1c9444d70a94b3` |
| `01-preflight-backup.ps1` | `c8f4922a555b47cf2cdcc80cf9b4068160d929b1613d40b49ee4f91170e1c5e8` |
| `02-create-protected-staging.ps1` | `579bb9155b85fdfb6ded5deda06bcaa3ddcdb02eef6fababbd89e7ffe9acd2f9` |
| `03-verify-acl.ps1` | `d2d77970c3ae36783a7cc236c0d07f8bdba0afadc0c9d8577701394475a037d9` |
| `04-restore-parent-acl.ps1` | `ad96429ca689de073722966551e97867fddf4b8eb257a40bafaab32af55bd4c0` |

## 7. Owner decisions và EX02 blockers

| ID | Nội dung cần quyết định / bằng chứng | Trạng thái |
| --- | --- | --- |
| S1-D01 | Review exact parent/staging delta và giữ sibling paths; chỉ cho phép apply ở task riêng sau mọi prerequisite | Pending Approval |
| S1-D02 | Cách bảo vệ ancestor namespace với Code unchanged; nếu không khả thi, Owner giao scope amendment riêng. Không chỉ acknowledge rủi ro để bypass | BLOCKED — chưa có control được chứng minh |
| S1-D03 | Bằng chứng parent inheritance update giữ repo/venv ACL nguyên vẹn. Nếu không thể, quyết định riêng trước khi thay ACL child | BLOCKED — NOT VERIFIED |
| S1-D04 | Named elevated PC operator, independently trusted bootstrap/backup/evidence locations, exact revision/hash, execution và rollback authority | Pending Approval / Provisioning |
| S1-D05 | Amend EX02 manifest cho sibling staging mới, file/log/verification separation, client/operator và hashes/authority trước SQL copy/execution | Pending Review |

[SQL execution manifest](../../data-sources/security/wwi_extraction_execution_manifest.json) được giữ nguyên SHA256 `c86ee8af57d387d5284d4fa2f186dfde46ddb23d089c2c248873bf8c066f8f6e`. Các path `C:\ProgramData\RetailDataPlatform\SecurityReview...` trong manifest/§12 checklist là **proposal lịch sử**, chưa được chạy; task Owner mới yêu cầu sibling D: cho protected staging. ACL plan này không tự amend/activate SQL manifest và không cho phép fallback về vị trí cũ.

Hai SQL files và offline SQL checker không sửa. Exact 9 current + 2 archive grants vẫn là proposed EX02 package, không SQL runtime proof. Empty negative database ghi nhận trong §12 checklist là evidence task trước; task này không kết nối SQL, tạo/drop database hoặc xác minh lại trạng thái database đó. EX01 **DONE**; EX02 **Pending Execution Authorization**; G02 **BLOCKED**; G01 **Pending Consistency Proof**; WWI-05/Phase2 **IN_PROGRESS**; M1C/M2/M3 **NOT STARTED**.31 original gates và72 runtime scenarios NOT RUN không thay đổi.

## 8. Validation và acceptance chuẩn bị

| Tiêu chí | Kết quả | Bằng chứng / giới hạn |
| --- | --- | --- |
| Preflight Git/machine/operator/NTFS/location | PASS — observed | §1 và ACL plan before |
| Ownership/inheritance/masks/reparse/ancestor risk | PASS — assessment | §2–3; không destructive probe/full Authz token proof |
| Exact proposed ACL delta và không mở rộng scope | PASS — design | §4; Code/repo unchanged, parent necessity khác sufficiency |
| Bốn operator procedures và guard | PASS — prepared/offline | Năm `.ps1` AST không lỗi; 10 unsafe in-memory fixtures bị từ chối |
| SQL security regression | PASS — offline |18/18 tests, SQL artifacts/manifest không sửa |
| ACL package static regression | PASS — offline |13/13 tests, gồm mutation/allowlist/authority/target coverage |
| Parent/staging ACL apply và effective access | NOT RUN | Không tạo staging hoặc áp dụng ACL; chưa runtime-ready |
| Child inheritance preservation | NOT VERIFIED | S1-D03 chặn apply |
| Ancestor namespace protection | BLOCKED | S1-D02; giữ Code unchanged |

Lệnh offline tái lập ở staging README; PowerShell test chỉ parse operator files, load helper definitions và dùng descriptors/fixtures trong bộ nhớ. Không chạy entry scripts 01–04. Markdown links/anchors, secret scan, scope/hashes, Git diff và staged QA được ghi kết quả sau khi thực hiện, trước commit chuẩn bị. Không thể dùng static PASS để đánh dấu EX02/G02 hoặc ACL runtime PASS.

QA working content thực tế:154 visible files/136 Markdown,1.181 local links và anchors không lỗi;0 secret-pattern/forbidden-artifact findings. Đúng15 paths trong scope (5 existing docs +10 new files),139/144 original tracked hashes giữ nguyên; hai SQL scripts, SQL manifest/checker, approved records, gate register và runtime test plan không sửa. Sáu documented artifact SHA256 khớp exact bytes. `git diff --check` đạt; staged QA được kiểm riêng trước commit. UTC `2026-11-17T04:59:12.4895144Z` đọc lại xác nhận cả bốn before-SDDL D:/Code/parent/repo không đổi, không reparse, staging vẫn absent; `.venv` ACL hiện tại còn inherited giống repo, không có baseline venv riêng để tuyên bố so sánh byte-for-byte từ đầu task. Không chạy Set-Acl hoặc operator scripts.

Staged QA thực tế PASS:15 blobs khớp exact reviewed working bytes, UTF-8/LF,0 secret-pattern findings, không binary/large artifact hoặc file ngoài scope; `git diff --cached --check` đạt, không active/custom hooks. Kiểm lại sau khi ghi record này trước local preparation commit `docs: prepare EX02 protected staging ACL remediation`; không push. Commit chuẩn bị không cấp ACL/SQL execution authority.

**Khuyến nghị:** nhận gói chuẩn bị để Owner review, giữ execution BLOCKED. Task an toàn tiếp theo là giải quyết S1-D02/D03 và trusted bootstrap/manifest review trong phạm vi riêng; chưa apply ACL hoặc chạy EX02.
