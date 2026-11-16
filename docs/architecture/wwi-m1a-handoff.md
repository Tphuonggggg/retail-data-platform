# WWI-05 / M1A — Verification Acceptance & Implementation Handoff

**2026-11-16.** [Owner approvals](wwi-phase-1-closure-approval.md), [Readiness Report](wwi-m1a-environment-readiness.md), [Secure Connection Contract](wwi-secure-connection-contract.md), [Gate/Evidence Matrix](wwi-m1a-gate-evidence.md). Governance A đã commit `554c5ea3c5eab5f9d3f5ad98f543b3739d0e0d95` trước B.

## 1. Verification completion khác operational readiness

**M1A DONE — Verification Checkpoint**, có hiệu lực sau documentation/static/staged QA PASS. Các authorized checks đã thực hiện hoặc ghi FAIL/BLOCKED/NOT RUN với evidence và owner next action. Đây không là Owner đã nghiệm thu toàn bộ WWI-05 hoặc operational prerequisites.

**Operational readiness BLOCKED**: current developer sysadmin không suitable cho extraction; chưa approved extraction profile, A02 concrete consistency evidence hoặc Raw target contract/profile. WWI-05 IN_PROGRESS; Phase2 In Progress; M2/M3+ NOT STARTED. Parent WWI-04 DONE Design/Phase1 Completed theo approval, không mở lại.

## 2. Acceptance checklist

| Criterion | Verification result | Giới hạn / evidence |
| --- | --- | --- |
| Baseline/governance/ordered checkpoints | PASS | A commit xác minh trước B, owner5 approvals có record. |
| Local inventory/versions | PASS | Environment §2, Evidence C01–04. |
| Secure SQL connectivity / identity classification | PASS — checkpoint | Secure developer connection11 tables, identity suitability FAIL và approved extraction profile BLOCKED được ghi rõ; không claim G02 đạt. |
| Raw PostgreSQL readiness classification | PASS — checkpoint | Native service discovered nhưng target approval PENDING, connection NOT RUN; B9 excluded/unchanged. |
| Security và connector contract | PASS — documentation/review | No secret finding; TLS/no bypass/cleanup/params/identity boundaries; future config/PG TLS vẫn proposal. |
| Evidence cho mọi PASS | PASS | Per-check matrix00–25; SQL code/observations và command ledger; bounded access không full runtime suites. |
| Prerequisites có owner/next action | PASS | §4 dưới đây; không tự remediation/admin. |
| Không prohibited writes/infra/dependency changes | PASS | Chỉ SELECT/metadata/inspection và Markdown; original gate/ADR/B9 tracked và local evidence hashes giữ nguyên. |
| Documentation QA / scope / staged checks | PASS sau actual checks | Environment §6 ghi counts/link/hash/secret/diff evidence; staged check bắt buộc trước commit. Operational prerequisite FAIL/BLOCKED được bảo toàn. |

## 3. Required gates còn mở

[Original31 gates](../data-models/wwi-implementation-gate-register.md) giữ nguyên identity/structure/status. M1A evidence là supplemental observations, không đóng gate nguyên nhóm; G02 current-identity fail khác approved-profile missing, G01 chưa consistency proof, CG08 chưa approved deployment scope.

G03–05 bounded B9 lịch sử không actual Raw adapter/regression proof; G06/G07 physical mapping/schema/retention/capacity chưa approved; G08/RG08/CG07 transactions/checkpoint/recovery chưa runtime. B5/CG06 numerical/Certified/per-action values chưa duyệt. CD-T01–21/IT01–21/CP-T01–30=72 NOT RUN, không chuyển IT01 PASS chỉ vì M1A một phần giống scenario.

## 4. Smallest next actions — chưa thực hiện

| Priority | Responsible owner | Task / required decision | Proof before next use |
| --- | --- | --- | --- |
| 1 | PO + Source Owner/DBA | Cung cấp/duyệt riêng least-privilege extraction identity/profile; DBA thực hiện identity/grants chỉ trong task được phép | Exact approved endpoint/database/auth/TLS, effective SELECT/current+H/meta và không write/admin; rerun bounded M1A permissions dưới đúng identity |
| 2 | PO + INF/ST/DBA | Duyệt Raw target connection/environment contract riêng: native PG hiện có hoặc sandbox/service mới; dedicated DB/roles/TLS/credentials/capacity, không B9 | Approved profile+allowlist, rồi SELECT identity/version/encoding/collation/TLS; nếu cần provision phải có scope riêng trước thao tác |
| 3 | PO + Source Owner/DBA + IN/DQ | Chốt concrete A02 no-writes interval hoặc verified consistent copy và evidence plan | Writer control/context/generation/coverage proof trước M3 capture/M4 publish; không đổi original isolation hoặc tự clone |
| 4 | PO + IN/INF/ST | Production dependency/config/bootstrap và physical target proposal review theo WWI-05 DoD | Approved versions/security/reproducibility; không mặc định B9 requirements là full pipeline dependencies |

**Official next task vẫn WWI-05 — “Chuẩn bị WWI read-only và PostgreSQL đích”**, follow-up giải quyết M1A prerequisites và re-verification. Không invent một task ID mới hoặc tự bắt đầu M2. Owner task hiện tại kết thúc sau report/commit B; hành động admin/provision cần task/approval riêng.

## 5. Prerequisites M2 và M3

- M2 physical Raw/metadata proposal cần approved target/source/config/dependency scope và G06/G07 review; target chưa verified thì không claim environment ready. Không schema/DDL trong M1A.
- M3 Full Load cần M1 source consistency+least privilege, M2 reviewed physical target/mappings, scope/dependency closure và fidelity proof trước publication. Full/incremental generators/pipelines không được task này cấp quyền.
- M1 operational DoD chưa đủ; hoàn tất M1A documentation không mark WWI-05 DONE. Certified metrics/scheduling/action approvals tiếp tục đúng deadline, không tự đặt thresholds/retention/window/retry budgets.

## 6. Git và điểm dừng

Commit B chỉ sau QA PASS: `docs: record M1A environment readiness and connection verification`. Không amend/reset commit A, không push/remote. Chỉ4 M1A docs và related trackers/index/module READMEs; không source/config/dependency/runtime code changes. Dừng sau Checkpoint B reporting, không M2/M3.


## M1B follow-up — 2026-11-16

Owner đã giao riêng M1B source identity/consistency review. [Identity proposal](wwi-source-identity-proposal.md), [Consistency proposal](wwi-source-consistency-proposal.md), [DBA/Owner checklist](wwi-source-dba-owner-checklist.md), [M1B assessment](wwi-m1b-assessment.md) giải quyết phần planning,không runtime prerequisites. M1B DONE — Planning Review sau QA; D01–D05 Pending Owner/DBA Approval,G01/G02 không PASS;WWI-05/Phase2 IN_PROGRESS. Các next-action “chưa thực hiện” ở §4 nay có proposal chi tiết,administrative actions vẫn chưa chạy. Không bắt đầu M1C/M2/M3.
