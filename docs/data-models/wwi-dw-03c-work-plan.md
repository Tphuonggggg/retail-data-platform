# WWI DW-03C — Work Plan, Owner Review and Deferred Gates

**Stage 3, 2026-11-16. CP-01–CP-06 APPROVED — Logical Policy; D1/D2 Logical Approved, D3 Governance Approved, D4 confirmed.** Owner cho conditional DONE — Design + one focused docs commit sau mandatory criteria/QA PASS, không automatic closure. Current assessment ở Final Assessment section14+. Production downstream Not implemented yet, CP-T01–30 NOT RUN; DW-04 chưa bắt đầu.

**Final current outcome:** DW-03C **DONE — Design**,18/18 mandatory design criteria/actual QA đạt; no remaining mandatory architectural blocker. All CG/G/RG/B5/per-action/physical/runtime proof remains gated; no runtime tests/DB/Docker/B9 actions.

## 1. Stage 1 baseline history và Stage 2 current scope

Repository root D:\Code\project1_Retail_Data_platform; branch **main**, HEAD **17a00d38acaa233919cb57bf6c7004cf3fa2236d**, message **docs: finalize DW-03B incremental load design**. Git status trước sửa sạch, index rỗng, không remote. Đã đọc AGENTS.md trước repository analysis. Baseline 121 tracked/visible files được lấy SHA-256 trước sửa; preserve unrelated work nếu xuất hiện, không reset/revert.

Stage 1 Owner task “DW-03C Stage 1 — Change Propagation & Recovery Discovery and Design Proposal” chỉ cấp documentation/static inspection authorization; historical no-commit boundary vẫn được ghi ở đây. Kế hoạch đã trình trước edits: đọc accepted source/KPI/model/SCD/Raw/incremental contracts → source impact closure → dimension/fact/mart/recovery alternatives → six CP proposals → test plan/open decisions → static QA và current status. Không SQL/DB/Docker/B9 commands, dependency install, schema/code/model/DAG mới.

## 2. Evidence index và authority

Các observations nguồn là historical, không fresh database inspection. Stage 1 không tạo SQL evidence mới; đây là analysis từ approved specifications. Current B9 physical follow-up trong ADR-SCD-05 supersedes Pending notes cũ đúng scope, không thay entire Raw/runtime gates.

| Evidence | Existing source | Ý nghĩa cho task |
| --- | --- | --- |
| E01 | [AGENTS](../../AGENTS.md), [Scope](../../PROJECT_SCOPE.md), [Roadmap](../../ROADMAP.md), [Tasks](../../TASKS.md) | Rules/scope/status, Sales-first, read-only, no commit/phase/task closure |
| E02 | [Source Contracts](wwi-source-contracts.md), [Dictionary](wwi-metadata-dictionary.md), [Relationships](wwi-source-relationships.md), [Source ERD](wwi-source-erd.md) | Nine current+two physical H populations; PK/FK/nullable; no direct line1:1/payment allocation |
| E03 | [BRD Matrix](../requirements/wwi-business-rules-decision-matrix.md), [KPI Catalog](../requirements/kpi-definitions/wwi-kpi-candidate-catalog.md), [KPI SQL](../requirements/kpi-definitions/wwi-kpi-verification-sql.md) | Approved formulas/populations/dates/roles/exclusions, source reconciliation definitions |
| E04 | [Logical DW](wwi-logical-dw-design.md), [Fact-Dimension Dictionary](wwi-fact-dimension-dictionary.md), [Marts](wwi-logical-data-marts.md), [Source-to-Target](wwi-logical-source-to-target.md) | 2 intermediates, 4 dims, 4 facts, 6 mart grains; independent headers/current inventory/role semantics |
| E05 | [Final SCD2](wwi-final-scd2-design-specification.md), [Backlog B1–B9](wwi-dw-02e-work-plan.md), [Accepted ADR index](../adr/README.md) | Identity/registry/whole-day consensus/hybrid/unresolved/correction/tiered certification/exact B9; physical details still gated |
| E06 | [Raw Design](wwi-dw-03a-full-raw-design-proposal.md), [A01–A06](wwi-dw-03a-decision-register.md), [G01–G08](wwi-dw-03a-work-plan.md) | Immutable captures/manifests/distinct identities/coherent atomic publication/pins, no-writes or verified copy |
| E07 | [Incremental Design](wwi-dw-03b-incremental-design-proposal.md), [INC-01–INC-06](wwi-dw-03b-decision-register.md), [RG01–RG12](wwi-dw-03b-work-plan.md), [Acceptance](wwi-dw-03b-assessment.md) | Approved Current-State Convergence and ACK01–06; observed absence vs entity delete; no full CDC/intermediate-event guarantee |
| E08 | [Change Impact Matrix](wwi-change-impact-matrix.md) | Approved original propagation/old-new scope requirements, header-only changes, no role/source-measure rewrite |
| E09 | [Source Validation Matrix](../requirements/wwi-source-validation-matrix.md), [Raw Requirements](../requirements/wwi-raw-layer-requirements.md) | Same-grain counts/keys/amounts/qty, source anomaly vs incomplete/fidelity, I01–I12 and no partial publication |
| E10 | [ADR-SCD-05/B9](../adr/scd-05-exact-temporal-precision.md), [B9 evidence](wwi-dw-03a-evidence-approval-readiness.md), [PoC README](../../tests/integration/b9_precision/README.md) | Exact F2/str-None/psycopg/TEXT/C, bounded prior proof only; CP test outcomes không suy từ B9 |

## 3. Stage 1 work-item trace (lịch sử trước approvals)

| Item | Description / module | Dependencies | Stage 1 acceptance evidence | Status |
| --- | --- | --- | --- | --- |
| C1-01 | Discovery/traceability — docs/root | Owner task, DW-01/02/03A/03B DONE Design | Baseline/current rules + E01–E10, source/model scope | IN_PROGRESS |
| C1-02 | Source/dimension/fact impact — docs/data-models | C1-01, E02–E08 | 11-source matrix, 16-model inventory, SCD/four-fact contracts | IN_PROGRESS |
| C1-03 | Marts/publication/recovery — docs/data-models | C1-02, INC/ACK/B5/A06 | 6 marts, old/new groups, AP gates, 12 recovery cases | IN_PROGRESS |
| C1-04 | Six CP decision records + risks — docs/data-models | C1-02/03 | All required fields, no automatic approvals; dependencies/gates | IN_PROGRESS |
| C1-05 | Proposed tests/readiness/QA — docs/root | C1-01–04 | CP-T01–30 NOT RUN; links/secret/scope/hash/status/diff evidence | IN_PROGRESS |

Các C1 IDs chỉ work breakdown cho tài liệu, không implementation tasks mới hoặc phase transition. Không tự đánh dấu task/decision DONE vì static QA.

## 4. Deliverables và minimal file scope — tái sử dụng Stage 1 paths

Stage 1 đã tạo bốn documents; Stage 2 cập nhật đúng existing paths, không thêm duplicate source/model/KPI spec:

- [Change Propagation Proposal](wwi-dw-03c-change-propagation-design-proposal.md): source impact, SCD/fact/mart/certification/recovery/contracts/tests/risks.
- [Decision Register](wwi-dw-03c-decision-register.md): CP-01–CP-06 alternatives/recommendations/Owner approvals.
- [Assessment](wwi-dw-03c-assessment.md): coverage/QA/readiness và actual execution boundary.
- Work plan hiện tại: baseline/evidence/dependencies/gates.

Sửa 8 existing Markdown paths: AGENTS.md, PROJECT_SCOPE.md, ROADMAP.md, TASKS.md, README.md, CHANGELOG.md, docs/data-models/README.md, docs/data-models/wwi-change-impact-matrix.md. Impact Matrix chỉ thêm navigation follow-up, giữ nguyên approved table/rules. Accepted ADRs/DW-01/02/03A/03B/source/BRD/KPI/B9 code/tests/evidence ngoài scope giữ hashes. Không sửa source-to-target field mapping vì không thay fields/grains.

## 5. Current deferred gates — approved directions vs pending details

CG01–CG10 là proposal tracking, không approvals, không replaces [G01–G08](wwi-dw-03a-work-plan.md)/[RG01–RG12](wwi-dw-03b-work-plan.md)/B5. Six CP logical policies đã Owner approve ở Stage2; D1/D2 Logical và D3 Governance nay Approved tại Stage3, không pending architectural choice. Physical/per-request/runtime decisions vẫn gates trước relevant use. Runtime details chọn/test trong authorized implementation task tương ứng.

| Gate / mapping | Open detail | Reason | Responsible owner / approval | Target | Required proof | Hold/usage condition |
| --- | --- | --- | --- | --- | --- | --- |
| CG01 / CP-01/RG09 | Impact envelope/old-new closure, exact subject/view scope | Chưa runtime lineage/child graph | DW/ingestion designer + DQ; CP-01/D2 scope policy Approved; DW/DQ verifies concrete closure trước use | D2 logical review resolved Stage3; before propagation builds WWI-08, before Customer/Inventory WWI-12/13 | Complete source/model pins, affected NK/role/interval/header-child/group sets; CP-T01/02/04 | Unknown closure widen/full affected rebuild or hold, no changed-row-only completeness claim |
| CG02 / CP-02/B1/B2/B3/B7 | Registry/Type1 scope/rekey/episode boundaries | D1 mode Approved; concrete selected-member/registry/lookup execution chưa verified | DW designer/custodian + DQ; Owner approve selected correction scope | D1 reference/mode Approved; B7 per-request scope và physical proof trước dimension/rekey correction use | Compatible registry+forward+supersession, exact predicates/whole-day proof, CP-T06–13/29 | I block affected, U controlled; no arbitrary SK/fallback/survivor/all-version default |
| CG03 / CP-03/B8/RG07 | Removal/retraction/incarnation actions | Absence không entity-deletion ground truth | Source/data owner+DW/DQ; Owner approve controlled action | Before retirement/retraction/reappearance action | Complete evidence, before/after eligible-population accounting/rollback, CP-T14/15 | Candidate only, no cascade/purge/reuse SK meaning |
| CG04 / CP-04 | Partition/key-group future optimization | A full affected-mart baseline đã Approved; B/C chưa measured/equivalence proof | Analytics/DW + DQ reviewer; Owner review future B/C optimizations | Before mart implementation WWI-08/11, then relevant expansion | Complete-group oracle, old/new/empty groups/distinct/ratio tests CP-T03/04/19 | No targeted promotion nếu scope/completeness chưa prove; no performance claim |
| CG05 / CP-05/A06/RG08/09 | Approved D2 subject/view/joint-consumer contract physical enforcement | D2 choice fixed Stage3; manifests/atomic visibility/consumer enforcement chưa implemented | Storage/DW/consumer owner+DQ; Owner physical/release review | Before normal subject publication/refresh; cross-subject needs verified joint proof | AP01–06 graph/membership/consumer pins, no partial visibility CP-T23/30 | No mixed dim-fact-mart/registry states, old valid publication retained |
| CG06 / CP-05/B5/RG11 | Threshold values/certification eligibility/revocation | B5 numerical approval chưa có; D3 governance Approved nhưng per-incident authorization/RBAC/lifecycle execution proof chưa có | DQ/analytics/data owner; Project Owner approval | D3 governance Approved; B5 numeric trước Certified claim; Owner action approval và runtime proof trước revoke/reinstate/rollback | Versioned KPI/view/filter/period/row+value thresholds and revocation/rollback tests | No default100%/tolerance; unproven breakdown Uncertified, known error scope review/hold |
| CG07 / CP-06/G08/RG08 | Concurrency/commit read-back/downstream ACK mechanism | Chưa physical locking/transaction/failure proof | Storage/orchestration/DW+DQ; CP-06 logical Approved; Owner review physical/release | Before publication/retry runtime; advanced monitoring later không defer basic correctness | CP-R01–12, CP-T20–29 durable outcome/duplicate/stale/race tests | Unknown outcome/conflict hold/no ACK; no task-success-only pointer advance |
| CG08 / G01–G06/RG01–06/10 | Approved source/target/test env, fidelity/access/consistency | Stage1–3 design-only, no source/target writes hoặc runtime proof | DBA/infrastructure/ingestion/test owner; Owner separate authorization | Before provisioning/testing/production use | Independent SQL/PG sandbox, least-privilege trusted profile, exact source fields/100ns, same source C | No original DML/config/B9 changes; incomplete/fidelity failures hold |
| CG09 / G07/B2/RG12 | Build/manifest/registry/forward retention and recovery | Chưa physical capacity/retention/backup plan | Storage/custodian/DW+DQ; Owner approve periods/actions | Before cleanup/restore/scale claim | Compatible dependency backup/restore, retained prior valid publication and lineage | No evidence purge or “equivalent SK recovery” without proof |
| CG10 / DW-01/RG09 | External reference/calendar/domain contracts | TransactionTypes/labels/date basis không trong11 approved populations đầy đủ | Source/reference owner+DW/DQ; Owner approve contract/mapping | Before dependent type/label/date attribution | Explicit mapping/projection/generation/time basis/reference completeness tests | No default type/classification or business-time inference, no new source by implication |

No numerical interval, retry count, retention period, performance objective hoặc coverage tolerance được tự chọn. Physical key/unknown-member encoding và transaction/locking/schema design vẫn gated.

## 6. Test strategy và execution boundary

Proposal section 9 định nghĩa **30 integration scenarios**, tất cả NOT RUN; section 7 có **12 recovery cases**. Cần independent approved writable SQL/PG/test transformation/orchestration-consumer environment khi triển khai; không create/reuse B9 trong Stage1–3. Basic scope/integrity/reconciliation/publication correctness phải kiểm trước use, không đợi Phase6 monitoring.

Static QA ở Assessment chỉ local docs/links/secret patterns/hash/source-model coverage/Git diff, không runtime tests. Stage3 đã resolve D1–D3 approval gaps; actual final18/18 criteria/QA đạt. Current statuses: DW-01/DW-02/DW-03A/DW-03B/DW-03C DONE Design; B9 scoped Physical Approved; DW-04 TODO; WWI-04/Phase1 IN_PROGRESS; Phase2–9 Not Started. Stage đúng12 Markdown paths/create one docs commit chỉ sau staged checks; không push hoặc tự bắt đầu DW-04.

## 7. Stage 2 focused work plan và actual baseline (lịch sử)

Actual main/HEAD **17a00d38acaa233919cb57bf6c7004cf3fa2236d** đúng expected; đầu Stage 2 có **4 new DW-03C +8 modified paths** từ Stage 1, index rỗng/no remote. Baseline **125 visible files** hashed trước edits; preserve all existing work, không reset/revert. Final allowlist12 Markdown paths vẫn như section4, không file mới.

Current Owner authority: “DW-03C Stage 2 — Owner Logical Approval & Final Design Review”,2026-11-16. Six CP approvals có explicit limitations. Kế hoạch trước edits: accepted-doc review/B7/type1+publication authority search → formal register → D1–D4 comparisons/AP evidence contract → recovery/test review → split design criteria/runtime gates → QA/current statuses; không tự chọn governance/physical values.

| Item | Dependencies / module | Evidence / current outcome |
| --- | --- | --- |
| C2-01 Formal six CP approvals | Owner instruction, existing A/B/INC decisions | Register six Approved — Logical Policy records; no approval inflation |
| C2-02 D1–D4 review | B7/ADRs, CP-04/05/06, consumers/Sales-first | Specification section10: D1/D2/D3 Pending, D4 Confirmed; no architectural conflict requiring accepted-policy change |
| C2-03 AP/recovery/coverage | 11-source/16-model scope, ACK01–06, B5 | AP01–06 eight fields, CP-R01–12 unchanged IDs/guards, source grain/recon preserved |
| C2-04 Test/gate review | All CP-T01–30, G/RG/B5 | All NOT RUN; owned CG rows and approval conditions; no runtime PASS |
| C2-05 Conditional acceptance/Git | C2-01–04 + actual docs QA | Partial acceptance do D1–D3; keep IN_PROGRESS/no finalization commit, no DW-04 |

## 8. Stage 2 Owner decision blockers (lịch sử, Stage3 đã approve)

| Design gate | Reason cannot close automatically | Owner / target | Evidence required for resolution | Block condition |
| --- | --- | --- | --- | --- |
| D1 selected-version reference/mode | B7 approved request obligations nhưng không default mode/reference point; Stage2 không approve new rule | Project Owner, before final DW-03C acceptance và before Type1 correction | Accept/adjust explicit set B referenced to P_base/registry+compatible Raw source, field/scope/fact/mart/recon implications | Chưa approved → no selected-version default/correction action; design Partial |
| D2 analytical publication unit | CP-05 direction không chốt smallest unit/cross-subject/consumer enforcement contract | Project Owner, before final acceptance/promotion design freeze | Choose B subject/view transitive bundle or A/C, exact shared compatibility/joint consumer pins/supersession/Sales-first rules | Unresolved → no complete atomic-unit/consumer consistency claim, design Partial |
| D3 revocation/rollback governance | Prior valid retention không xác định authority/actions/consumer invalidation policy | Project Owner, before final acceptance và any revoke/reinstate/rollback use | Approved authority/evidence/valid-target/certification/visibility/rollback contract, non-destructive audit | Unresolved → no delegated lifecycle action/finalization commit; known-invalid scope hold/review |

Không cần approve lại CP-01–06 hoặc D4 baseline. Numeric B5 values, future B/C optimization, physical locks/schema/retention/runbooks/runtime proof tiếp tục CG/G/RG gates; chúng không được dùng như lý do bịa thêm architectural blocker. D1–D3 là explicit Stage2 Owner choices, được tách khỏi implementation deferrals.

## 9. Current CP-T01–CP-T30 / CP-R01–CP-R12 review

| Test IDs | Current design review | Pending dependencies | Actual execution |
| --- | --- | --- | --- |
| CP-T01–CP-T05 | Header-only/reparent/measure/new-entity closure đúng11 source/16 model grains | CG01/08/10; approved D2 closure needs runtime proof | NOT RUN |
| CP-T06–CP-T10 | Type1 selected scope/Type2/boundary/split/merge giữ B1–B9 | Approved D1 set/four anchors; B7 per-request scope/registry/basis/runtime proof | NOT RUN |
| CP-T11–CP-T15 | U→R/zero-duration/ambiguity/absence/reappearance accounting preserved | B4/B8, controlled action evidence và D3 when lifecycle | NOT RUN |
| CP-T16–CP-T19 | Signed FM/current FC/roles/no allocation/repeat/ratios đúng existing KPI | Reference/current-state pins, D2 compatibility | NOT RUN |
| CP-T20–CP-T24 | Partial downstream/recon failure mappings match CP-R01–05 | Physical evidence/recovery mechanism proof, no task-success-only publication | NOT RUN |
| CP-T25–CP-T30 | ACK loss/replay/concurrency/generation/restatement/tiering reviewed; T30 includes invalidation/rollback | D2/D3 contracts Approved; per-action authorization/B5 values/environment/runtime guards before tests/use | NOT RUN |

Tất cả12 recovery scenarios giữ durable evidence/idempotency/conflict/rollback-or-compensation/eligibility/manual trigger; D3 nay Approved governance cho invalid Certified state; role/action/rollback conditions reviewed, no physical rollback algorithm hoặc lifecycle action thực thi. AP logical evidence contract không runtime evidence.

**Stage2 historical stop:** IN_PROGRESS/Partial/no commit trước approvals; giữ trail, không current blocker. Stage3 current authority/result theo section10–12 và Final Assessment.

## 10. Stage 3 baseline, plan và conditional acceptance

Actual main/HEAD **17a00d38acaa233919cb57bf6c7004cf3fa2236d**,8 modified+4 untracked existing paths như Owner report;125 visible initial files hashed trước edits, index rỗng/no remote. Preserve Stage1/2 work/history, không reset/revert hoặc file/code/schema mới.

Current authority: Owner “DW-03C Stage 3 — Owner D1–D3 Approvals & Final Design Acceptance”,2026-11-16. D1 explicit four-anchor selected set và D2 dependency-complete subject/view/joint consumer manifests **Approved — Logical Policy**, D3 role/incident/authorized rollback lifecycle **Approved — Governance Policy**, D4 CP-04 confirmed. Không current architectural blockers do D1–D3; runtime/action gates vẫn Pending.

Plan đã trình trước edits: read accepted ADRs/B7 and current docs → exact approval trail → integrate D1–D3 in SCD/publication/AP/recovery → validate11-source/16-model/30 tests và all18 mandatory criteria → root status update only after QA → exact12-file staging/secret/diff/size review → one focused docs commit nếu complete. Không database/Docker/PoC/runtime test.

## 11. Stage 3 compatibility and deferred gate disposition

| Disposition | Design finding / Owner approval | Remaining mandatory proof/gate |
| --- | --- | --- |
| D1 vs DW-02 | Four anchors: analytical base, compatible accepted Raw, persistent registry revision, recorded analytical build identity; explicit reproducible/frozen set | Actual selection/lookup/member encoding/storage/generation tests, B7 field/action scope; before correction execution |
| D2 subject/view/joint consumer | Safe complete transitive unit preserves Sales-first; no independent latest→cross-subject consistency | CG05/AP02/AP06 physical manifests/shared dependencies/consumer pin enforcement; missing joint proof holds cross-subject publication |
| D3 role/lifecycle | DQ detects/collects/recommends; Owner authorizes; Operator executes/audits. Existing compatible validated appropriately certified rollback target only; none→hold | CG06/07 Owner per-incident approval, B5 numeric values, physical RBAC/state transitions/fencing/recovery/notification-block proof before use |
| D4 affected mart baseline | CP-04 full affected-mart rebuild/old-new/empty/header/re-resolve/distinct/ratio guards confirmed | CG04 future B/C optimization needs correctness-equivalence evidence, no MVP shortcut |
| Inherited architecture | DW-01/02/03A/03B/B1–B9/INC/ACK/grains/KPI/assurance unchanged | G01–G08/RG01–RG12/CG01–CG10/B5 owners/targets/proof/blockers at section5 + inherited tables unchanged |

No numerical threshold/retention/cadence/retry count/physical schema/lock/fencing/allocator/ID codec chọn mới. B5 Pending vẫn chặn Certified use khi không approved values/proof; no degraded uncertified fallback. Critical gates cần actual PASS trước relevant normal publication, không để đến monitoring phase mới kiểm correctness.

Review all30 CP tests và12 recovery cases vẫn logical-only/NOT RUN; D1 four-anchor immutability, D2 missing joint proof hold, D3 Owner authorization/validated-certified target/no replacement hold/durable outcome/consumer visibility là assertions bắt buộc future execution. No automatic revocation/reinstatement/rollback trong documentation task.

## 12. Stage 3 file/Git handoff

Final allowlist đúng **12 Markdown paths** (4 existing DW-03C docs +8 management/navigation/Impact paths ở section4). Current source/model matrices/SCD/fact/six-mart/AP/recovery/30 scenarios reviewed; accepted docs ngoài scope giữ hashes và original approved Impact table/rules body preserved.

Nếu18/18 mandatory criteria+QA PASS thì record DW-03C **DONE — Design**, stage đúng allowlist, validate staged blobs/secrets/size/diff/identity và create one commit **docs: finalize DW-03C propagation and recovery design**. No push/remote/history changes. Nếu blocker thật thì giữ IN_PROGRESS/no finalization commit; approval instructions alone không closure.

DW-04 ready-for-Owner-task handoff chỉ sau design acceptance; **không start DW-04**. WWI-04/Phase1 IN_PROGRESS,Phase2–9 Not Started. Actual final result tại Assessment, Git hash/status báo sau verify commit, không self-referential hash trong docs.
