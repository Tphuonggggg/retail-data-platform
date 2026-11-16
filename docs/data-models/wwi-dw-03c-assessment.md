# WWI DW-03C — Final Design Acceptance Assessment

**Current Stage 3, 2026-11-16. DW-03C DONE — Design. CP-01–06/D1/D2 APPROVED — Logical Policy; D3 APPROVED — Governance Policy; D4 confirmed.** Sections14–18 ghi conditional acceptance sau mandatory criteria/actual QA. Sections1–13 giữ Stage1/2 historical evidence gồm15PASS+3PARTIAL/no-commit trước approvals, không current blocker/status. Production Not implemented yet; CP-T01–30 NOT RUN.

## 1. Repository baseline và execution boundary

Actual baseline: branch main, HEAD **17a00d38acaa233919cb57bf6c7004cf3fa2236d**, expected commit đúng; working tree sạch/index rỗng trước edits, không remote. 121 tracked/visible initial files được SHA-256 trước sửa. [AGENTS](../../AGENTS.md) đọc trước analysis; [Work plan](wwi-dw-03c-work-plan.md) giữ E01–E10/dependencies.

Chỉ read existing documents, design alternatives, Markdown updates và static validation. Không SQL Server/PostgreSQL reads/writes mới, không Docker commands, B9 sandbox/PoC modifications, dependency install, ingestion/dbt/Airflow/schema implementation. Historical B9/SQL results chỉ referenced, không lấy làm CP runtime proof.

## 2. Executive Summary

[Proposal](wwi-dw-03c-change-propagation-design-proposal.md) trace đủ 11 source populations tới 16 logical target models; tách header-only/dependent dimensions/facts/marts. Giữ approved grains/roles/KPI/SCD2/Raw/incremental contracts.

Khuyến nghị để review: old/new dependency envelope, controlled evidence/registry revision và re-resolution, state-based same-grain fact updates, full rebuild từng affected mart baseline, dependency-complete analytical manifests/per-view B5 certification và durable evidence recovery. Tất cả six CP directions chưa approved.

## 3. Source-to-target và propagation findings

| Finding | Existing evidence / impact | Proposed handling |
| --- | --- | --- |
| Invoice/Order header-only changes | DW-01 header contracts/Impact Matrix: lines không cần đổi timestamp | Union old/new child PKs/header dates/roles, update affected facts và old/new groups; all headers preserved |
| CustomerTransactions khác invoice lines | BRD-10: payment InvoiceID nullable, no allocation | Reconciliation support riêng, no new payment fact/additive amount |
| Occurrence/observation/episode/SK/reference khác nhau | DW-02 B1–B9/ADRs | 12 dimension transition cases, preserve registry/forward/supersession, no historical fallback |
| Same fact updated/rekeyed khác additive event | Four approved fact grains | One accepted state per source grain; measures conserved on rekey-only, source corrections exact before/after |
| Ratios/distincts/roles không additive across groups | Six marts/KPI Catalog | Recompute full group population, include unchanged rows, old/new/empty-group handling |
| Current inventory không historical daily balance | Holdings/current-state fact contract | Same published-state DP lookup; observed_at/published_at riêng; no SUM states/absent→zero |
| RawPublished không Certified | A06/B5/INC ACK | AP01–06/per-view dependency gates, old compatible publication retained, no partial certified output |
| Unknown commit/stale/concurrent requests | A04/INC-06/ACK01–06 | CP-R01–12 durable outcome/predecessor/content/pins before ACK/retry |

## 4. Alternatives và decisions

[Decision Register](wwi-dw-03c-decision-register.md) ghi đủ Problem, Existing approved constraints, Evidence, Alternatives, Recommended option, Trade-offs, Correctness limitations, Dependencies, Acceptance criteria, Required Project Owner approvals và Status cho CP-01–CP-06.

- CP-01: full subject rebuild vs retained-evidence dependency closure; recommend closure với full affected-scope fallback.
- CP-02: full affected-NK candidate revision vs interval/role-limited when proved; persistent registry/B7 selected scope giữ nguyên.
- CP-03: candidate full fact replacement vs affected-key state upsert/recompute; no additive correction/replay.
- CP-04: A full affected mart rebuild recommended baseline; B partition/C key-group optimization deferred proof.
- CP-05: dependency-complete subject/view publication recommended, all-platform coupling không default, model-by-model certification shortcut invalid.
- CP-06: serial builds vs isolated parallel candidates/guarded promotion recommended; physical locking/isolation/counts chưa chọn.

Không phát hiện yêu cầu buộc đổi approved architecture. CP choices còn mở là đúng Stage 1 scope; không tự cấp approvals hoặc đóng DW-03C.

## 5. Stage 1 document acceptance checklist

PASS dưới đây chỉ coverage/consistency analysis, không Owner approval hoặc execution PASS.

| Criterion | Evidence | Document result / remaining |
| --- | --- | --- |
| C-AC01 Baseline/rules/dependencies | Work plan E01–E10, baseline Git | PASS — actual read-only inspection |
| C-AC02 All11 source populations and impact fields | Proposal section 2 source matrix 9 columns | PASS — existing source/model contracts, no fresh source-data profiling |
| C-AC03 All16 named models traced | Model inventory: 2 headers+4 dims+4 facts+6 marts | PASS — no new logical fact/mart |
| C-AC04 Header-only/role/financial limits | Source matrix/impact envelope/BRD links | PASS — no payment allocation/Buyer-Bill-to merge |
| C-AC05 Dimension/SCD identity/lookup/correction cases | Proposal section 3, 12 transitions and existing B1–B9 | PASS — concrete procedures/member/modes gated |
| C-AC06 Four-fact update/restate/retract contract | Proposal section 4 | PASS — source grain/measure/idempotency and controlled removal distinctions |
| C-AC07 Six marts/old-new groups/A-B-C alternatives | Proposal section 5 | PASS — A baseline recommendation Pending Approval |
| C-AC08 Publication/certification/dependency guards | Proposal section 6 AP01–AP06 | PASS — B5 numeric thresholds unchanged, runtime no Certified output |
| C-AC09 Minimum12 failure scenarios đủ required fields | Proposal section 7 CP-R01–CP-R12 | PASS — matrices only, failure injection NOT RUN |
| C-AC10 Source assurance/consistency/lineage preserved | Proposal sections 1/8, A02/INC/ACK references | PASS — no upgraded complete-event guarantee |
| C-AC11 Six CP records Pending, owned runtime details | Register; Work plan CG01–CG10 | PASS — Owner review required, no new physical/numeric approval |
| C-AC12 Integration plan/environment scope | Proposal section 9 CP-T01–CP-T30 | PASS — all30 NOT RUN, no provisioning |
| C-AC13 Links/secrets/scope/hash/diff/status | Actual static QA section 6 | PASS — actual documentation checks, không runtime proof |
| C-AC14 Task/phase/commit boundary | TASKS DW-03C IN_PROGRESS; DW-04 TODO | PASS — no stage/commit/push hoặc task closure |

**Full DW-03C acceptance: chưa đủ điều kiện.** Six CP decisions/rebuild/publication/recovery procedures chưa Owner approve; exact physical/runtime choices và integration proof pending. Stage 1 không authorize task closure dù document coverage PASS.

## 6. Actual static validation

Đã chạy static QA ngày2026-11-16 bằng existing project-local Python standard library qua UTF-8 PowerShell stdin, không cài dependency hoặc thêm validator source module. Kết quả dưới là local documentation/Git checks; không report CP-T runtime PASS.

| Actual check | Observed result | Boundary |
| --- | --- | --- |
| Git baseline/HEAD/branch | main/17a00d38acaa233919cb57bf6c7004cf3fa2236d, đúng expected | HEAD giữ nguyên, không commit |
| File allowlist | 8 tracked modified + 4 new Markdown, không path ngoài scope | Tất cả unstaged; không code/schema/config mới |
| Protected content | 113/113 initial files ngoài allowlist giữ SHA-256 | Bao gồm accepted DW-01/02/03A/03B/ADRs/source/BRD/KPI/B9 code/tests/evidence |
| Existing Change Impact content | Original approved table và phần rules/scenario phía sau byte-equivalent sau normalized text read | Chỉ thêm navigation proposal note |
| Links/anchors | 836 local links và2 fragments trên119 visible Markdown files, 0 broken | Target/heading checks, không Mermaid/browser rendering |
| Source/model coverage | 11 source populations,16 models,4 fact contracts,6 mart contracts | Matrix/contract presence+manual grain/dependency review; no pipeline test |
| Decisions/recovery/gates | 6 CP records×11 required fields/status,12 recovery rows×8 fields, AP01–06 và10 owned CG rows | All CP Pending; physical/runtime gates không close |
| Integration test plan | CP-T01–CP-T30 đủ30 IDs, tất cả NOT RUN | Không test fixtures/source changes/builds/failure injection |
| Security/ignore/size/format | 0 secret pattern/actual sandbox-credential value hits; credential files/.venv ignored; no visible file >5 MiB/UTF-8/fence/table-width/trailing-space/extra-new-doc-EOF errors | Pattern/value scan không comprehensive security certification, không in credentials |
| Git diff/status | git diff --check exit0; index0 files; no remote; all task statuses đúng scope | Dirty tree có đúng12 paths, no stage/commit/push |

Commands thực tế: Get-Content/rg, Get-Location, Git status/log/remote/ls-files/diff/check-ignore; standard-library pathlib/hashlib/re/json/urllib.parse/subprocess cho validation. Validator đã điều chỉnh explicit new-document boundary check và baseline hash reuse để tránh đổi protected-key names khi thay prefix paths; rerun cuối PASS, không thay accepted files để vượt QA. Final checks phải lặp sau evidence edits.

No SQL Server/PostgreSQL/Docker/PoC runner commands trong task; static QA không chứng minh database runtime hoặc source changes. Historical precision/source results vẫn chỉ cited evidence. Không staging/commit/remote/push.

## 7. Files changed và preservation

Tạo bốn files:

- wwi-dw-03c-work-plan.md
- wwi-dw-03c-change-propagation-design-proposal.md
- wwi-dw-03c-decision-register.md
- wwi-dw-03c-assessment.md

Sửa 8 files: AGENTS.md, PROJECT_SCOPE.md, ROADMAP.md, TASKS.md, README.md, CHANGELOG.md, docs/data-models/README.md, docs/data-models/wwi-change-impact-matrix.md. Impact Matrix chỉ additional navigation note, toàn approved table/rules giữ nguyên. Mọi DW-01/02/03A/03B/ADRs/source/KPI/B9 files khác scope phải giữ SHA-256. Không stage/commit/push; HEAD giữ baseline.

## 8. Owner review/readiness và điểm dừng

Ready for **Stage 1 review**, chưa final design acceptance/implementation readiness. Owner cần quyết định CP-01–06 và các Open Decisions trong proposal section 10/CG gates: closure unit, Type1 scope, retraction/incarnation evidence, rebuild method, analytical publication/consumer/revocation policy, concurrency/recovery direction. G01–08/RG01–12/B5 và physical/numeric/runtime gates vẫn pending.

DW-01/DW-02/DW-03A/DW-03B DONE Design; B9 Approved — Physical Raw Temporal Representation; DW-03C IN_PROGRESS; DW-04 TODO; WWI-04/Phase1 IN_PROGRESS; Phase2–9 Not Started. Không tự bắt đầu DW-04 hoặc phase implementation. Dừng sau proposal.

## 9. Stage 2 — Formal logical approvals và D1–D4 review

Authority: Project Owner task **“DW-03C Stage 2 — Owner Logical Approval & Final Design Review”**,2026-11-16. Six CP policies được approve trực tiếp, không suy từ static QA. Instruction **không** automatic resolve D1–D3; task/commit closure chỉ conditional khi không remaining mandatory Owner decisions. Register ghi exact approval scope/limits, proposal section10 giữ focused comparisons/implications.

Actual Stage2 main/HEAD **17a00d38acaa233919cb57bf6c7004cf3fa2236d**, expected đúng; 4 new+8 modified pre-existing paths từ Stage1, index rỗng/no remote;125 visible files hashed trước edits. Preserve all existing work, không reset/revert. Allowed scope vẫn12 Markdown paths; no new docs/source/schema/dependencies hoặc DB/Docker/B9 tests.

| Review | Verified existing contract | Stage2 recommendation / outcome | Remaining approval |
| --- | --- | --- | --- |
| D1 Type1 selected-version mode | B7/ADR-SCD-01 fixed explicit request scope/audit/recon, **no global current/all-version default**; mode/reference point chưa selected | Explicit enumerated version set tại pinned target analytical/registry base, correction values từ compatible accepted Raw pin; source measures/episode/SK conserved on Type1-only | **PENDING OWNER APPROVAL** cho reference/mode; không reopen B7 hoặc admit attrs |
| D2 Analytical publication unit | CP-05/A06 dependency completeness/atomic visibility/pins approved; smallest analytical unit/shared consumer composition chưa fixed | Subject/view+transitive dependency bundle, joint consumer manifest khi cross-subject consistency requested; preserve Sales-first | **PENDING OWNER APPROVAL** cho unit/shared compatibility/enforcement contract |
| D3 Invalid Certified data/revocation/rollback | CP-05 giữ prior valid versions, B5 tiering; formal authority/delegation/consumer lifecycle chưa established | Owner authorizes revoke/reinstate/rollback, DQ/operator evidence/hold/execution separation; compatible validated target only, non-destructive audit | **PENDING OWNER APPROVAL** cho governance/visibility/rollback policy |
| D4 Rebuild/restatement closure | CP-04 đã chọn full affected-mart rebuild, CP-01 old/new envelope, CP-03 state-based grain | Confirmed baseline; old/new/empty groups, fact IDs, dim re-resolution, historical corrections, broader repeat populations, generation guard | **CONFIRMED — existing approved policies**, no new blocker |

Không phát hiện conflict buộc sửa accepted architecture/grains/KPI. Minimum unresolved **Owner decision set = D1,D2,D3**; không gọi chúng “six CP chưa approved”, không coi mọi physical/numeric runtime gate là architectural blocker mới. Các choices ảnh hưởng selected-version/publication/governance semantics nên không thể silently chọn để đạt DONE.

## 10. Structured mandatory design acceptance

PASS là documentation/design review, **không** runtime test hoặc final DW-03C acceptance.

| Criterion | Evidence / disposition | Result |
| --- | --- | --- |
| DA01 Formal CP-01–06 approval/authority/limits | Six register records Approved — Logical Policy, D1–D3 explicitly excluded | PASS |
| DA02 Baseline/current work/rules/dependencies | Current Git state/125-file baseline và work plan, no reset | PASS |
| DA03 Final11-source/16-model impact coverage | Existing source matrix/model inventory/full facts/six marts reviewed, no extra source/grain | PASS |
| DA04 SCD2/fact restatement compatible | Registry/continuity/replacement/lookup/U/source measures/B9/no allocations/signs preserved | PASS |
| DA05 D4 mart baseline/closure | Full affected mart A approved; old/new/empty groups and broader repeat recompute, no B/C default | PASS |
| DA06 D1 Type1 selection contract chosen | Comparison/ref-point/source pin/generation/fact-mart/recon recommendation complete, Owner choice missing | PARTIAL |
| DA07 D2 safe analytical publication unit chosen | Alternatives/smallest-safe closure/shared versions/consumer pins/supersession/Sales-first proposed, Owner choice missing | PARTIAL |
| DA08 D3 governance/invalid Certified/rollback chosen | Authority/hold/revoke/reinstate/compatible target/audit/consumer proposal complete, Owner choice missing | PARTIAL |
| DA09 AP01–AP06 finalized logical evidence interpretation | Each AP row8 fields: inputs/evidence/state/failure/blocker/owner/runtime proof; D1–D3 usage guards | PASS |
| DA10 Recovery/concurrency correctness review | CP-R01–12 eight fields; partial/ACK/replay/race/supersession/rekey/generation and D3 invalidation/rollback proposal traced | PASS |
| DA11 CP-T01–CP-T30 reviewed, execution honest | All30 NOT RUN; T06/T30 explicitly depend on future D1–D3 approvals, no DB/Docker test | PASS |
| DA12 Every deferred gate reason/owner/stage/proof/blocker | CG01–10 and D1–D3 owner table, preserve G01–08/RG01–12/B5 | PASS |
| DA13 No strengthened assurance/business scope | Raw C/state convergence≠event history/SCD validity/Certified; consistent compatible pins required | PASS |
| DA14 No numeric/physical algorithms silently approved | B5 thresholds/locks/fencing/compensation/storage/retention still gated | PASS |
| DA15 Actual local links/secret/diff/format QA | Section11 actual static checks PASS, không runtime proof | PASS |
| DA16 Status/Git/phase boundary | IN_PROGRESS; DW-04 TODO, WWI-04/Phase1 IN_PROGRESS; no finalization commit/stage | PASS |
| DA17 Protected content/approved impact rules | Section11:113 protected hashes/approved impact body unchanged | PASS |
| DA18 Conditional acceptance authority correctly applied | D1–D3 are precise minimum blockers, no automatic DONE from six approvals | PASS |

**Overall design acceptance: PARTIAL — NOT COMPLETE. DW-03C IN_PROGRESS.** Không commit “finalize” khi DA06–DA08 chưa có approval. Stage2 authorized docs work đã thực hiện; còn cần Owner decision, không tiếp tục sang DW-04/implementation. Numeric/runtime deferrals vẫn có gates, không report PASS hoặc invent thresholds để che blockers.

Final design matrix: **15 PASS +3 PARTIAL**, không được gọi18/18 PASS. Ba partial criteria tương ứng duy nhất D1/D2/D3. Documentation QA PASS không giải quyết Owner decision blockers.

## 11. Actual Stage 2 validation

Đã chạy Stage2 static validation ngày2026-11-16 bằng existing project-local Python standard library qua UTF-8 PowerShell stdin; không new dependency/validator module trong Git. Stage1 numbers ở section6 giữ history, không thay actual Stage2 evidence.

| Actual check | Observed Stage2 result | Limits |
| --- | --- | --- |
| Git baseline/branch/HEAD | main/17a00d38acaa233919cb57bf6c7004cf3fa2236d, expected đúng | No commit, không rewrite/reset |
| Current scope | 8 tracked modified+4 untracked existing Stage1 documents, đúng12 paths | Không thêm document trùng hoặc source/schema/config/code |
| Protected content | 113/113 initial visible files ngoài allowlist giữ SHA-256 | Includes accepted source/BRD/KPI/DW-01/02/03A/03B/ADRs/B9 code/tests/evidence; initial baseline125 visible (121 tracked+4 untracked) |
| Approved Change Impact | Exact normalized original table/rules/scenario body hash unchanged | Chỉ current approval/review navigation notes changed |
| Links/anchors | 855 local links+2 fragments trên119 visible Markdown files,0 broken | Local target/heading checks, no Mermaid/browser rendering |
| Source/model/contract coverage | 11 source rows,16 exact models,4 fact contracts,6 mart contracts | Manual grain/pin/role/sign/occurrence review + structural checks; no runtime data |
| Formal decisions/gates/recovery/tests | Six Approved CP records×11 fields, D1–D3 pending/D4 confirmed, AP6×8 fields, CG10×7 fields, recovery12×8 fields, tests30 NOT RUN | AP logical not runtime PASS; correct partial design classification |
| Mandatory acceptance structure | 18 criteria,15 PASS+3 PARTIAL (DA06/07/08) | No automatic closure; no false all-PASS |
| Security/format/size |0 high-confidence secret-pattern hits và0 actual local sandbox credential-value leaks in visible text; no UTF-8/fence/table-width/trailing-space/new-doc EOF/large-file errors | Credentials/.venv ignored, no visible file >5 MiB; not comprehensive security certification, no secret output |
| Git status/diff/index | git diff --check exit0, index0, no remote; DW-03C IN_PROGRESS/DW-04 TODO/WWI-04+Phase1 IN_PROGRESS | No staging/commit/push vì remaining mandatory Owner decisions |

Commands thực tế: read docs/Get-Content/rg và Git status/log/remote/ls-files/diff/check-ignore; standard-library pathlib/hashlib/re/json/urllib.parse/subprocess cho local validation. Command-length limit ban đầu chặn tạo validation process; đã rút payload bằng reference hash thay nhúng full old Impact text và rerun PASS. Không có DB test hoặc approved-content modification để vượt QA. Final checks được rerun sau actual-evidence edits.

**Runtime evidence:** CP-T01–CP-T30 vẫn **NOT RUN**, không source/target DB queries/writes, Docker/PoC commands, crash/recovery/concurrency/performance test mới. AP/G/RG/CG gates không được nâng runtime PASS. Không prepared commit nên staged-content check NOT APPLICABLE; index được verify rỗng. Git finalization hash **không có**, HEAD giữ baseline.

## 12. Files changed và Git outcome

12-path allowlist giữ nguyên, không tạo duplicate files. Four existing untracked DW-03C documents được hoàn thiện; 8 existing tracked management/navigation/Impact paths cập nhật current approvals/status.

- AGENTS.md
- PROJECT_SCOPE.md
- ROADMAP.md
- TASKS.md
- README.md
- CHANGELOG.md
- docs/data-models/README.md
- docs/data-models/wwi-change-impact-matrix.md
- docs/data-models/wwi-dw-03c-work-plan.md
- docs/data-models/wwi-dw-03c-change-propagation-design-proposal.md
- docs/data-models/wwi-dw-03c-decision-register.md
- docs/data-models/wwi-dw-03c-assessment.md

Approved source/BRD/KPI/DW-01/02/03A/03B/ADRs/B9 code/tests/evidence ngoài scope phải unchanged; Impact Matrix approved table/rules giữ nguyên, chỉ navigation notes/current authority updated. Không stage/commit/push; HEAD giữ baseline. Suggested finalization message của Owner **chưa được sử dụng** vì acceptance còn mandatory decisions.

## 13. Owner action và DW-04 handoff

Owner cần accept/adjust đúng ba recommendations D1 explicit selected-set/base reference, D2 dependency-complete subject/view unit/consumer compatibility, D3 authority/lifecycle/validated rollback. CP-01–06 và D4 không cần phê duyệt lại. Sau quyết định, authorized follow-up mới update affected contracts/tests/criteria, kiểm conditional acceptance và Git; không mặc định automatic closure.

DW-04 **chưa ready để bắt đầu** vì dependency DW-03C chưa DONE. Handoff material đã có11 sources/16 models, AP guards/12 recoveries/30 NOT RUN tests, G/RG/CG/B5 gates và exact blockers; không tự thực hiện final cross-phase verification. Current DW-01/02/03A/03B DONE Design, B9 scoped Approved, DW-03C IN_PROGRESS, DW-04 TODO, WWI-04/Phase1 IN_PROGRESS, Phase2–9 Not Started. Dừng DW-03C Stage2.

## 14. Stage 3 — Formal approvals, compatibility và mandatory re-evaluation

Authority: Project Owner instruction **“DW-03C Stage 3 — Owner D1–D3 Approvals & Final Design Acceptance”**,2026-11-16. D1/D2 Logical và D3 Governance được approve trực tiếp; D4 CP-04 confirmed. Task chỉ cho conditional DONE — Design/one focused commit nếu all mandatory criteria/QA đạt; no automatic closure. No execution/dependency/schema/SQL/PG/Docker/B9 commands.

Actual baseline main/HEAD **17a00d38acaa233919cb57bf6c7004cf3fa2236d**,8 modified+4 untracked existing paths, index0/no remote,125 visible files hashed. Preserve complete Stage1/2 work; không reset/revert hoặc remove evidence.

| Decision | Formal Stage3 disposition | Compatibility / evidence |
| --- | --- | --- |
| D1 | **APPROVED — Logical Policy** | Explicit reproducible frozen selected-version set anchors analytical base/publication, compatible accepted Raw, persistent registry revision, recorded analytical build identity; B7 field/action scope and B1–B9 rules unchanged |
| D2 | **APPROVED — Logical Policy** | Initial dependency-complete subject/view bundle, complete compatible transitive pins/models/recon/certification/predecessor/promotion; joint manifest required for cross-subject, missing proof holds cross-subject publication; Sales-first preserved |
| D3 | **APPROVED — Governance Policy** | DQ detects/collects/recommends, Owner authorizes revoke/reinstate/rollback, Operator executes/audits; invalid incident/dependency closure/hold/evidence/consumer notice-block/outcome sequence; only existing compatible validated appropriately certified rollback target, none→hold |
| D4 | **CONFIRMED — CP-04** | Full affected-mart rebuild, old/new/empty groups/full population/header re-resolution/distinct-ratios/source-generation guards; future partition optimization only equivalence evidence |

D1 không conflict với approved DW-02: explicit set/audit/per-request fields là refinement tương thích B7, four anchors không thay episodes/registry identity/Type2 vector/source measures/lookup/Unresolved semantics hoặc system-time meaning. No automatic current/latest/earliest fallback. No physical registry/lookup choice approved.

D2/D3 không cấp quyền thực thi hiện tại: manifests/locks/fencing/transaction/RBAC/consumer/recovery proof still gated; no automatic revoke/rollback/notification action. B5 numeric certification thresholds remain Pending before Certified use, không default. Six CP policy scopes giữ nguyên.

### 14.1 Final mandatory design criteria — re-evaluation of Stage2 DA01–DA18

FA01–FA18 map1:1 previous DA01–DA18, không tạo criteria để né ba blockers. PASS chỉ là approved design/evidence completeness, không test runtime.

| Criterion | Final evidence / disposition | Result |
| --- | --- | --- |
| FA01 / DA01 Formal CP approvals | Six CP logical records unchanged, current D1–D3 authority/limits explicit | PASS |
| FA02 / DA02 Baseline/rules/work preservation | main/expected HEAD125-file baseline,12 paths preserved, no reset | PASS |
| FA03 / DA03 Eleven-source/sixteen-model coverage | Source matrix/model inventory,4 fact/6 mart contracts reviewed, no grain/role/model expansion | PASS |
| FA04 / DA04 SCD2/fact compatibility | B1–B9/INC/ACK preserved, D1 four anchors/basis/registry/continuity/U/source measures intact | PASS |
| FA05 / DA05 D4 rebuild baseline | CP-04 full affected mart, old/new/empty/header/re-repeat/generation, B/C future only | PASS |
| FA06 / DA06 D1 selected-version choice | Owner Logical Approval fixes explicit frozen four-anchor set; no previous pending mode gap | PASS |
| FA07 / DA07 D2 publication unit | Owner Logical Approval fixes subject/view bundle/shared pins/joint manifest/hold cross-subject without proof | PASS |
| FA08 / DA08 D3 governance/lifecycle choice | Owner Governance Approval fixes roles/incident/action authority/valid-certified target-or-hold/audit/history protection | PASS |
| FA09 / DA09 AP01–AP06 contracts | Six8-field logical gates integrate D1/D2/D3, runtime state Unverified/NOT RUN | PASS |
| FA10 / DA10 Recovery/concurrency | Twelve cases durable evidence/idempotency/conflict/compensation/eligibility/manual triggers, D3 authorization/target/consumer guards | PASS |
| FA11 / DA11 Tests reviewed honestly | All30 CP scenarios NOT RUN, no runtime or production claim | PASS |
| FA12 / DA12 Deferred gate ownership | G01–08/RG01–12/CG01–10/B5 preserved with owner/target/proof/block; no indefinite correctness deferral | PASS |
| FA13 / DA13 Assurance/scope unchanged | Accepted consistent compatible Raw state required; no complete CDC/unobserved-event/business-validity strengthening | PASS |
| FA14 / DA14 Numeric/physical boundaries | No thresholds/storage/schema/ID codec/lock/fencing/compensation algorithms silently approved | PASS |
| FA15 / DA15 Actual docs QA | Section16 actual links/secrets/format/diff checks PASS; no runtime proof | PASS |
| FA16 / DA16 Conditional statuses/Git/phase | DONE Design after actual checks; exact scoped commit only after staged QA; DW-04 TODO/WWI-04+Phase1 IN_PROGRESS | PASS |
| FA17 / DA17 Unrelated integrity/Impact | 113 protected initial files/original approved Impact body unchanged, verified section16 | PASS |
| FA18 / DA18 Owner authority applied | No unresolved mandatory logical/governance choices; conditional closure only on actual checks, runtime gates pending | PASS |

**Current design review finding:** three Stage2 partial criteria are resolved by explicit approvals; no remaining mandatory architectural/governance blocker identified. Không dùng missing runtime/numeric/per-action execution evidence làm approval blocker giả. Nếu final QA fail thì giữ IN_PROGRESS/no commit cho tới khắc phục; chưa gọi final acceptance PASS từ instruction alone.

**Final disposition:** all18 mandatory design criteria PASS sau actual approval/compatibility/coverage/QA checks → **DW-03C DONE — Design** theo conditional Owner authority. Không runtime/physical DONE; staged validation bắt buộc trước one focused commit. Stage2 fifteen PASS/three PARTIAL giữ history, không sửa thành outcome chưa từng có ở thời điểm đó.

## 15. Final contract/test/runtime handoff

All **11 source populations/16 models** reviewed: header-only changes, separate Buyer/Bill-to, CustomerTransactions recon-only, H multiplicity/exact text, source grain/state-based four facts, full six affected marts, current inventory state và generation guards unchanged.

D1 now requires frozen selected set/four-anchor/build evidence in AP03; D2 subject closure/shared compatibility/joint consumer manifest in AP02/AP06; D3 per-incident Owner authorization, Operator audit/durable outcome and valid appropriately certified rollback target-or-hold in AP05/AP06. Invalidity handling không destructive deletion hoặc arbitrary prior target.

CG01–CG10 table trong Work Plan là current DW-03C runtime/action gate registry; inherited G/RG/B5 authoritative. Owners/target stages/proofs/blockers vẫn maintained, before relevant normal publication/use. B5 numerical values, per-correction/action approvals, full-field codecs, Raw/analytical physical manifests/storage/RBAC/locking/fencing/consumer/runtime recovery/tests/backup/retention remain deferred, **không runtime PASS**.

CP-T01–CP-T30 **NOT RUN**; CP-R01–CP-R12 là logical review only. Tests future phải cover selected-set immutability/build anchor, joint proof missing→hold, D3 role authorization/consumer notice-block/existing validated certified target/no replacement→hold/unknown-commit read-back. Không DB/Docker/PoC tests hoặc existing publication lifecycle action trong task này.

## 16. Actual Stage 3 QA and staged checks

Đã chạy Stage3 static documentation validation ngày2026-11-16 bằng existing project-local Python standard library qua UTF-8 PowerShell stdin; no dependency install hoặc validator source module mới. Stage1/2 QA tables giữ historical, không sửa old15PASS/3PARTIAL thành outcome chưa từng có.

| Actual check | Observed Stage3 result | Boundary |
| --- | --- | --- |
| Final design criteria | **18/18 FA01–FA18 PASS**, no Pending/Partial current criteria | Previous Stage2 DA06/07/08 remain PARTIAL trong historical table |
| Approval trace | Six CP Logical records, D1/D2 Logical+D3 Governance current formal records, D4 confirmed | Exact Owner authority/limits, no physical/runtime approval inflation |
| Source/model coverage | 11 source populations,16 exact models,4 fact/6 mart contracts | Original grains/roles/KPI/signed/current-state rules preserved; no new runtime data |
| Publication/recovery/gates/tests | AP6×8 fields, recovery12×8 fields, CG10×7 fields, CP-T01–30 NOT RUN | Logical obligations/owners/targets/proofs/blockers; no AP/runtime test PASS |
| Links/anchors | 874 local links+2 fragments trên119 visible Markdown files,0 broken | Local existence/heading checks, no Mermaid/browser rendering |
| Protection/scope | 113/113 initial visible files ngoài12-path allowlist giữ SHA-256; approved Impact table/rules body hash unchanged | Includes source/BRD/KPI/DW-01/02/03A/03B/ADRs/B9 code/tests/evidence |
| History | Stage2 18 criteria/15PASS+3PARTIAL preserved; original Pending alternatives explicitly historical | Current D1–D3 approvals không overwrite prior evidence dates/results |
| Secrets/ignore/size/format | 0 secret-pattern hits,0 actual sandbox-credential value leaks in visible text; credentials/.venv ignored; no visible file >5 MiB/UTF-8/fence/table-width/trailing-space/new-doc EOF errors | No credential output, not comprehensive security certification |
| Git pre-stage | main/HEAD17a00d38acaa233919cb57bf6c7004cf3fa2236d,8 modified+4 untracked, index0/no remote; git diff --check exit0 | Preserve all current work, no reset/revert, commit only after exact staged review |
| Task/phase | DW-03C DONE — Design, DW-04 TODO, WWI-04/Phase1 IN_PROGRESS, Phase2–9 Not Started | No phase/next-task transition, production Not implemented yet |

Commands thực tế: Get-Content/rg, Git status/log/remote/ls-files/diff/check-ignore; pathlib/hashlib/re/json/urllib.parse/subprocess for local checks. After evidence edits rerun actual validator; before commit exact12 staged Markdown blobs must match working normalized content, no binary/large/secret payload, git diff --cached --check exit0, configured identity và hooks reviewed. Staged outcome/actual commit reported after execution; no self-referential commit hash inserted.

**Actual staged validation:** exact12 Markdown staged paths/blobs match working normalized bytes; staged secret/size/binary checks0 errors; git diff --cached --check exit0; existing Git author/committer identity available, no custom hooks. Full validation again18/18 criteria,874 links/2 anchors,113 protected hashes PASS. Evidence-line update này được restage và rerun trước commit; không in credential hoặc personal Git identity.

**Runtime:** no SQL Server/PostgreSQL queries/writes, no Docker/B9 runner/tests, no lifecycle revoke/reinstate/rollback action, no ingestion/dbt/Airflow/physical recovery implementation. CP-T01–CP-T30 NOT RUN; G/RG/CG/B5/per-action/runtime gates remain pending before relevant publication/use.

## 17. Final files / conditional commit manifest

Exactly12 Markdown paths, unchanged allowlist from Stage2:

- AGENTS.md
- PROJECT_SCOPE.md
- ROADMAP.md
- TASKS.md
- README.md
- CHANGELOG.md
- docs/data-models/README.md
- docs/data-models/wwi-change-impact-matrix.md
- docs/data-models/wwi-dw-03c-work-plan.md
- docs/data-models/wwi-dw-03c-change-propagation-design-proposal.md
- docs/data-models/wwi-dw-03c-decision-register.md
- docs/data-models/wwi-dw-03c-assessment.md

Bao gồm all existing Stage1/2 uncommitted paths, không new duplicate file hoặc source/config/dependency. Accepted ADR/source/BRD/KPI/DW-01/02/03A/03B/B9 code/tests/evidence ngoài scope phải unchanged; original approved Change Impact table/rules preserved. Four DW-03C paths vẫn tên cũ; Stage1/2 approval/pending/assessment history giữ explicit boundaries.

Nếu final18/18/QA PASS: stage đúng12 paths, check staged blobs/secret/size/diff/identity rồi one commit **docs: finalize DW-03C propagation and recovery design**. No push/remote/history rewrite, no DB changes hoặc DW-04. Actual hash/status được verify sau commit và báo final, không ghi self-referential hash vào committed docs.

## 18. DW-04 readiness and stop

After final design acceptance, DW-04 **ready-for-Owner-task handoff**, không được tự start. Handoff: accepted CP/D1–D4 contracts,11-source/16-model matrix, old-new scope/registry/rekey/fact/full-mart/AP guards,12 recovery scenarios/30 NOT RUN tests, G/RG/CG/B5 runtime gates và historical evidence.

DW-01/02/03A/03B giữ DONE Design; B9 scoped Physical Approved; DW-03C chỉ DONE Design sau final checks, DW-04 TODO, WWI-04/Phase1 IN_PROGRESS, Phase2–9 Not Started. Không implement ingestion/dbt/Airflow/physical publication/recovery. Dừng Stage3 sau actual final acceptance/Git verification.
