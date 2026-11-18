# EX02-S1 — Chuẩn bị ACL protected staging

**DEFERRED — OPTIONAL SECURITY HARDENING**, theo Owner [MVP-SIMPLIFICATION-01](../../../docs/archive/pre-reset/wwi-m1b-owner-decisions.md#mvp-simplification-01--trusted-local-mvp). Protected staging không cần cho trusted local MVP; có thể revisit khi triển khai theo production-oriented security. Không execute ACL scripts/tạo staging/sửa permissions. Nội dung, guards, tests và hashes phía dưới là historical preparation tại commit f1d1fc4, **không MVP dependency hoặc runtime instruction hiện hành**. [EX02 local procedure](../../../docs/archive/pre-reset/security-history.md#10-local-mvp-setup--pending-runtime-authorization) thay mandatory staging workflow.

## Mục đích và phạm vi

Chuẩn bị remediation tối thiểu cho parent `D:\Code\Retail_Data_Platform` và protected staging sibling `Retail_EX02_Protected_Staging`. Repository sibling giữ nguyên vị trí; không đổi ACL Code/repo/venv. Đây là source package để review, **không phải protected staging thực tế**.

**PREPARED — BLOCKED FOR IMPLEMENTATION. Runtime: Not implemented yet.** Không chạy operator scripts trong task chuẩn bị. [Assessment](../../../docs/archive/pre-reset/wwi-ex02-s1-acl-assessment.md) là hồ sơ ACL/Owner decisions/hashes, không lặp lại SQL security manifest.

## Trách nhiệm

Owner review exact delta, giải quyết ancestor/inheritance blockers và authorize riêng. Elevated OS operator PC/SID-1001 thực thi tương lai từ independently trusted bootstrap; reviewer kiểm before/after và runtime access. Package không tự elevate, provision account, copy/activate SQL hoặc chạy EX02.

## Inputs và outputs

Input: [acl-plan.json](acl-plan.json) pin machine/operator/SID/NTFS/volume/paths/current Owner+Group+DACL/target SDDL; independent approved SHA256; future exact Owner authority và trusted existing backup directory.

Output dự kiến: readonly preflight, unique ACL backup và hash, exact parent/staging ACL metadata, readonly verification; rollback giữ staging. Chưa có backup/apply/runtime output thực tế. Không SACL backup, không secrets hoặc SQL payload.

## Dependencies và công nghệ

Windows PowerShell 5.1/.NET Framework và Windows NTFS ACL APIs có sẵn; không package mới hoặc venv dependency. Future scripts yêu cầu đúng máy `DESKTOP-OBDFK6B`, operator `DESKTOP-OBDFK6B\PC`, SID-1001, elevated token, volume serial `3EB49503`, exact paths, không reparse. Current non-elevated process chỉ làm offline/read-only preparation.

## Cấu trúc

| File | Trách nhiệm |
| --- | --- |
| [acl-common.ps1](acl-common.ps1) | Shared guards/hash/SDDL/policy/ancestor/trusted bootstrap helpers |
| [acl-plan.json](acl-plan.json) | Single exact ACL proposal và before-state, approvals false |
| [01-preflight-backup.ps1](01-preflight-backup.ps1) | Readonly default; guarded optional CreateNew backup |
| [02-create-protected-staging.ps1](02-create-protected-staging.ps1) | Guarded parent-only Set-Acl và atomic initial protected staging DACL |
| [03-verify-acl.ps1](03-verify-acl.ps1) | Readonly metadata/ancestor/unchanged-repo checks |
| [04-restore-parent-acl.ps1](04-restore-parent-acl.ps1) | Guarded exact parent-only rollback, giữ staging |

## Quy trình thực thi tương lai — CHƯA ĐƯỢC PHÉP

1. Resolve S1-D01–05 tại assessment. Code có untrusted DELETE nên ancestor guard hiện **sẽ từ chối**; không có switch bỏ qua. Parent giữ legacy inheritance streams nhưng repo/venv preservation chưa được chứng minh; flag false chặn apply.
2. Owner/operator chuẩn bị independently trusted bootstrap và existing trusted backup directory ngoài repo/venv bằng task riêng. Không chạy elevated helper từ development checkout. Independently verify hashes của cả helper, plan và entry scripts trước khi load bất kỳ code nào; adjacent writable checksum không đủ.
3. Sau exact ACL execution/backup authority riêng, future operator dùng 01 để preflight; `WriteBackup`/`OwnerAuthorized` mặc định false. Backup exact `C:\ProgramData\RetailDataPlatform\AclBackups\WWI05-EX02-S1-20261117.json` phải chưa tồn tại; script không tạo thư mục backup, không overwrite. Ghi hash vào approval record độc lập.
4. Chỉ khi revised plan/ancestor control/child-preservation proof được review, dùng 02 với independently supplied plan/backup SHA256 và explicit Owner authorization. Existing staging, ACL drift, reparse hoặc sai identity/volume → STOP. Chưa có revision nào vượt các gate này trong task hiện tại.
5. Dùng 03 và independently reviewed effective-token/file/ancestor checks trước Owner acceptance. Metadata match không phải SQL least-privilege verification hoặc protection proof chống mọi race.
6. Partial failure → giữ evidence, STOP.04 chỉ dùng khi được authorize rollback riêng, parent đúng target và Code/repo đúng before-state. Nếu child ACL bị propagation/drift, cần recovery review riêng; không tự sửa repo. Không xóa staging/artifacts, không recursive operations. Khôi phục parent có thể mở lại quyền rộng nên cấm tiếp tục SQL trong recovery.
7. Staging acceptance chưa cho SQL copy/activation: phải amend manifest cũ, review trusted client/log separation và Owner authorize exact SQL execution riêng.

## Testing

Chỉ chạy offline tests sau từ repository root (không gọi 01–04):

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'source_security_static.py' -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'staging_acl_static.py' -v
& .\tests\staging_acl_offline.ps1
```

[Python contract tests](../../../tests/staging_acl_static.py):13 tests PASS. [PowerShell offline tests](../../../tests/staging_acl_offline.ps1): parser 5 files PASS, 10 unsafe fixtures bị từ chối; descriptors chỉ trong bộ nhớ, read helper được thay bằng synthetic fixtures khi test access masks/ancestors. SQL static regression18 PASS. Không thực thi operator entry scripts, ACL apply, SQL hoặc filesystem destructive tests. Không formal security proof hoặc runtime PASS.

## Acceptance và status

Chuẩn bị đạt khi exact paths/SIDs/target ACEs/backup/recovery/stop boundaries và Owner requests review được; syntax/static/hash/link/secret/scope QA đạt. Runtime acceptance còn BLOCKED bởi ancestor namespace, child inheritance preservation, trusted bootstrap/backup và execution authority. EX01 DONE, EX02 Pending Execution Authorization, G02 BLOCKED, G01 Pending Consistency Proof; WWI-05 IN_PROGRESS; M1C/M2/M3 NOT STARTED.
