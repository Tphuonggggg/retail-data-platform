# WWI DW-03C — Change Propagation Decision Register

**Stage 3, 2026-11-16. CP-01–CP-06 APPROVED — Logical Policy. D1/D2 APPROVED — Logical Policy; D3 APPROVED — Governance Policy; D4 CONFIRMED.** Current authority: Project Owner task **“DW-03C Stage 3 — Owner D1–D3 Approvals & Final Design Acceptance”**. Full DW-03C acceptance vẫn conditional theo mandatory design criteria/QA; physical/runtime approval không được suy từ decisions. DW-01/02/03A/03B/B1–B9/INC/ACK không đổi.

Runtime CP-T01–CP-T30 **NOT RUN**; production downstream modules Not implemented yet. Decision analysis/static QA không là execution evidence hoặc approval.

[Proposal](wwi-dw-03c-change-propagation-design-proposal.md) là detail contract/matrices; [Work plan](wwi-dw-03c-work-plan.md) giữ E01–E10/CG01–CG10; [Assessment](wwi-dw-03c-assessment.md) ghi actual static QA/readiness. Không tạo ADR Accepted hoặc duplicates của existing specs.

| ID | Logical policy được Owner phê duyệt | Remaining design/runtime boundary | Status |
| --- | --- | --- | --- |
| CP-01 | Accepted Raw pins, old/new envelope/dependency closure, header-child propagation và empty old-group recompute; full affected-scope fallback | Exact analytical unit D2 và runtime lineage/enforcement còn review | APPROVED — Logical Policy |
| CP-02 | Evidence-driven propagation giữ B1–B9/registry/continuity/replacement/supersession, U/measures và no fallback | D1 explicit set/four anchors đã Logical Approved; physical registry/lookup proof riêng | APPROVED — Logical Policy |
| CP-03 | One row/source grain, state replacement/upsert, signed movement, pinned restatement/old-new reconciliation; reject unconfirmed retraction | Removal/action proof và physical procedures vẫn gated; no unsupported facts/KPI | APPROVED — Logical Policy |
| CP-04 | Full rebuild từng affected mart từ complete compatible population, stale/new groups/distinct/ratios/grain đúng | Partition/group optimization cần future equivalence evidence; baseline không còn Pending | APPROVED — Logical Policy |
| CP-05 | Accepted Raw pins, compatible dependency-complete analytical manifests, B5 tiering/prior valid versions/atomic visibility, no partial Certified | D2 subject/view bundle Logical Approved; D3 Owner-governed lifecycle Approved; B5 numeric/physical proof pending | APPROVED — Logical Policy |
| CP-06 | Isolated candidates/guarded promotion, durable identities/pins, retry/predecessor/content/conflict/read-back, no last-writer-wins/checkpoint shortcut | Physical locks/fencing/transactions/compensation/recovery proof chưa approve | APPROVED — Logical Policy |

## CP-01 — Source-to-Target Change Impact

- **Problem:** source row/header/dimension change có thể ảnh hưởng nhiều target models/old groups dù downstream source timestamps không đổi; local-table-only processing bỏ sót.
- **Existing approved constraints:** DW-01 grains/independent headers/roles, L01–05; approved Change Impact Matrix; INC source-specific detection/current-state guarantee và Raw publication pinning.
- **Evidence:** E02–E04/E07/E08; Orders/Invoices own populations, no OrderLine↔InvoiceLine FK, CustomerTransactions payment InvoiceID optional; final 11-population/16-model matrix trong proposal section 2. Đây là existing-design evidence, không fresh writes.
- **Alternatives:** full rebuild entire declared subject scope từ pins; selective dependency closure using retained old/new keys; broader all-platform rebuild tốn work/chặn Sales-first. Single-table-only propagation không đáp ứng approved constraints, không viable shortcut.
- **Approved logical policy:** Old–new change impact envelope từ accepted pinned Raw states; header-only changes propagate toàn affected child facts/dependencies; previous/replacement keys và empty old groups phải recompute; full affected-scope rebuild là correctness fallback. Preserve lineage, không infer unobserved changes.
- **Trade-offs:** lineage/closure metadata tăng complexity; conservative full scope nhiều work hơn nhưng tránh stale groups. Không benchmark hoặc mặc định targeted faster.
- **Correctness limitations:** không có prior compatible evidence thì không biết đầy đủ old groups; source observations không reconstruct lost events. Missing reference/current-state proof không tự giải bằng impact traversal.
- **Dependencies:** CP-02–06, compatible Raw/registry, calendar/reference contracts, G01–G08/RG01–12 và CG01/10; full source consistency vẫn DW-03B.
- **Acceptance criteria:** đủ 9 current+2 H, all16 targets traced; header-only/date/role/reparent changes cover old/new children/groups; no payment allocation/role merge/extra facts; publication holds khi incomplete/conflict.
- **Remaining Owner approval / implementation proof:** Envelope representation/lineage/consumer enforcement proof trước runtime; D2 publication unit đã Approved, không còn pending policy choice. Concrete deployment scope phải declared compatible theo contract.
- **Status:** APPROVED — Logical Policy.

## CP-02 — Dimension / SCD2 Propagation

- **Problem:** source occurrence/observation/analytical episode/SK/fact reference khác nhau; correction/split/merge có thể làm historical facts sai attribution nếu blanket rewrite hoặc identity drift.
- **Existing approved constraints:** B1 stable continuity/split-merge replacement; B2 persistent registry recovery; B3 whole-day consensus; B4 controlled U; B5 tiered certification; B6 hybrid evidence; B7 correction scope; B8 incarnation ambiguity; scoped B9 exact text.
- **Evidence:** E05/E10; Final SCD2 transitions/invariants và ADR-SCD-01–06; proposal section 3 gồm 12 cases, no new historical meaning.
- **Alternatives:** rebuild candidate dimension coverage của affected NK từ full retained evidence; interval/role-limited revision khi exact scope proof đủ. Cả hai phải dùng persistent registry/accepted identity, không ROW_NUMBER/SK reset hoặc every-Raw-row episode.
- **Approved logical policy:** Evidence-driven SCD2 propagation giữ B1–B9: occurrence/episode/SK riêng, continuity mới giữ SK, controlled split/merge replacements/supersession, approved lookup/re-resolution, U/source measures preserved, no current/earliest fallback/business-effective inference, exact B9. D1 explicit set contract nay Approved; physical/per-request proof còn gated.
- **Trade-offs:** giữ multiple evidence/publication revisions và affected-request maps; selective lookup khó hơn full NK rebuild nhưng giới hạn restatement. Missing basis vẫn U, không ép thành historical match.
- **Correctness limitations:** temporal system-time không business-effective, zero-duration không positive validity; ambiguous occurrence/reappearance không được invent identity. Exact precision không chứng minh historical coverage.
- **Dependencies:** CP-01/03/05/06, B1–B9, full registry/forward/evidence backup, date-domain proof, CG02/09; member/allocator encoding chưa chọn.
- **Acceptance criteria:** 0..1 eligible match/role, proven I blocks; otherwise-valid U retained; boundary-only giữ SK khi continuity proof; split/merge replacement/supersession, U→R conserve measures; no fallback/Raw SCD episodes/lost forward history.
- **Remaining Owner approval / implementation proof:** D1 explicit selected-version set đã Approved; exact admitted attrs/selected member set/correction request vẫn theo B7 audit/review trước execution. Registry/lookup/storage/codecs/runtime tests còn gated; không current/latest/earliest fallback.
- **Status:** APPROVED — Logical Policy.

## CP-03 — Fact Reprocessing and Restatement

- **Problem:** replay/update/reclassification/confirmed retraction có thể bị xem như additive new fact; source correction khác dimension-only rekey.
- **Existing approved constraints:** bốn DW-01 grains/source keys; independent headers/source roles/units, no fan-out; B4 U conservation/B7 controlled correction; INC-05 absence candidate/B8 ambiguity.
- **Evidence:** E03/E04/E08/E09; proposal section 4 four-fact table, fact/current published-state dictionary, source amount/quantity reconciliation.
- **Alternatives:** full candidate fact replacement từ complete pinned evidence; affected-key state upsert/recompute; additive delta-only không đủ với corrections/retry và chưa có event completeness.
- **Approved logical policy:** State-based replacement/upsert theo one row per approved source grain; no changed measures treated additive transactions; signed movements/header/dim/source corrections under pinned revisions; old/new lineage/reconciliation và reject unconfirmed removal as retraction evidence. No payment/refund/daily-balance expansion.
- **Trade-offs:** repeated compute/storage khi giữ candidate/prior versions; full rebuild đơn giản hơn targeted physical upsert nhưng cần retained source/mapping coverage. Không chọn target SQL/merge algorithm.
- **Correctness limitations:** unverified delete candidate không confirmed removal; missing source/state/history khác valid U. Fact rekey không sửa source role/price; updates không tự tạo revenue/COGS hoặc daily balance.
- **Dependencies:** CP-01/02/04/05/06, full child/header/reference pins, CG03/08/09; source action/retirement evidence và approved population before retraction.
- **Acceptance criteria:** one accepted row per grain/state; header-only propagation; signed movement/NULL price preserved; no snapshot sum/count-per-line; reparent/correction/retry/rekey/controlled removal reconciled và auditable.
- **Remaining Owner approval / implementation proof:** Controlled retraction/incarnation evidence và per-action scope theo B7/B8/INC-05; physical state-upsert/replacement/correction execution proof. D3 governance approval không xác nhận mọi source absence là business deletion.
- **Status:** APPROVED — Logical Policy.

## CP-04 — Mart Invalidation and Rebuild

- **Problem:** chỉ cập nhật new group để lại stale old totals; changed-row aggregation làm sai ratios/distincts/role attribution.
- **Existing approved constraints:** sáu mart grains/KPI formulas, all-header counts/repeat, buyer vs bill-to single-role totals, movement signs/current-state inventory; B5 certification unchanged.
- **Evidence:** E03/E04/E08; proposal section 5 six-mart table và A/B/C alternatives, existing mart population/reconciliation contracts.
- **Alternatives:** A full affected mart rebuild; B affected partition replacement; C targeted key-group recomputation. Không method nào miễn complete-group inputs/old-new scope.
- **Approved logical policy:** Full rebuild **mỗi affected mart** là initial correctness baseline, không rebuild unrelated marts. Complete compatible dependency population, stale/empty old groups cleaned, distincts/ratios/grain/approved KPI reconciliation đúng. Partition/key-group recomputation chỉ future optimization cần equivalence proof.
- **Trade-offs:** A có full read/compute, B/C tiết kiệm tiềm năng nhưng closure/empty groups/non-additive KPI khó; không claim performance đã đo.
- **Correctness limitations:** product-filtered distinct invoice counts không cộng ra enterprise count; quarterly repeat không average monthly; Type1/reporting attribute mode vẫn cần B7. Historical unknown không được certify nhờ rebuild.
- **Dependencies:** CP-01–03/05/06, complete source/model pins, CG04/06; semantic consumer contracts và approved optional KPI scope.
- **Acceptance criteria:** six exact grains preserved, union old/new groups và empty-group removal; unchanged rows trong group included; independent counts/ratios recomputed; no seventh mart/daily balance/role double sum.
- **Remaining Owner approval / implementation proof:** B/C chỉ future optimization/equivalence/performance proposal; A baseline/D4 confirmed. Complete compatible scope và selected-version references theo approved D1/D2, no unrelated-mart rebuild default.
- **Status:** APPROVED — Logical Policy.

## CP-05 — Analytics Publication and Certification

- **Problem:** models/tasks success riêng lẻ không bảo đảm graph compatible hoặc complete Certified outputs; consumer latest-per-table có mixed generations.
- **Existing approved constraints:** A03/A06 immutable manifests/atomic visibility/pins; INC/ACK durable source acceptance; B4 Core R+U/I blocks và B5 tiered per KPI/view certification/numeric thresholds pending.
- **Evidence:** E05–E09; proposal section 6 AP01–AP06/model graph/certification axes/old-valid-publication policy; no runtime analytical publication exists.
- **Alternatives:** dependency-complete subject/view publication; all-platform atomic scope gây coupling Sales/Inventory; model-by-model “Certified on success” không đáp ứng approved constraints và bị loại.
- **Approved logical policy:** Dependency-complete analytical publication: accepted Raw pins, compatible staging/dim/fact/marts, manifests, validation, B5 tiering, prior valid versions, atomic consumer visibility, no partial Certified. AP01–AP06 logical only; D2 Logical/D3 Governance Approved tại Stage3; B5 numeric Pending.
- **Trade-offs:** thêm publication/certification metadata, compatible retention và consumer refresh contract; không phải distributed transaction guarantee xuyên services.
- **Correctness limitations:** unresolved historical attribution vẫn limited; numeric thresholds thiếu thì no Certified. Old publication không tự còn “current” sau correction; known proven invalid certification cần scoped review/hold, concrete revocation authority còn mở.
- **Dependencies:** CP-01–04/06, all AP gates, B5/G/RG, CG05/06/09/10; consumer/report semantics và physical atomicity runtime proof.
- **Acceptance criteria:** RawPublished≠Certified; no mixed dim/fact/mart/registry state; candidate failures invisible as Certified; row/value coverage và approved policy pins; independent eligible tiers không bị imply toàn dashboard certified.
- **Remaining Owner approval / implementation proof:** D2/D3 unit/governance đã Approved. B5 numerical thresholds, physical manifests/consumer enforcement/transaction/RBAC/lifecycle execution evidence trước use; per-incident Owner authorization bắt buộc.
- **Status:** APPROVED — Logical Policy.

## CP-06 — Recovery, Retry and Concurrency

- **Problem:** partial downstream failures, ACK loss, duplicate/stale/concurrent processing có thể double apply, regress pointers hoặc đổi SK meaning.
- **Existing approved constraints:** A04 distinct identities/sealed replay/new-context-new-capture; A06 atomic accepted outcome; INC-06/ACK01–06; B1/B2/B7 compatible registry/recovery/correction.
- **Evidence:** E05–E08; proposal section 7 CP-R01–CP-R12 đủ durable evidence/safe retry/idempotency/conflict/compensation/eligibility/manual triggers.
- **Alternatives:** serialize all builds; parallel isolated candidates with guarded promotion; broad parallel publication without predecessor checks bị loại. Physical lock/CAS/isolation/fencing algorithm chưa chọn.
- **Approved logical policy:** Isolated build candidates và guarded promotion với durable identities/input-generation pins/idempotent retries, predecessor/content/conflict validation, durable read-back/unknown-commit investigation; no last-writer-wins, implicit checkpoints hoặc mixed generations. Physical compensation/locking/runtime mechanisms còn evidence gate.
- **Trade-offs:** recovery/control state và retained losing candidates tăng complexity/storage; fully serial simpler nhưng không chọn concurrency count/runtime policy mặc định.
- **Correctness limitations:** static scenario review không crash/transaction/concurrency proof. Missing registry/forward evidence không equivalent rebuild; source supersession không cho query latest để resume old request.
- **Dependencies:** CP-01–05, G08/RG08/12, CG07–09; approved isolated test environments, physical durable state and source/registry/policy identity guards.
- **Acceptance criteria:** all12 recovery cases specified; no task-success-only checkpoints; unknown commit hold/read-back; duplicate same accepted result/no measures twice; old/new generation conflicts detected; rollback compatible set, historical correction/split/merge retained/auditable.
- **Remaining Owner approval / implementation proof:** Physical locking/fencing/transactions/compensation/restore/runbook/runtime proof còn pending; D3 role contract đã Approved nhưng actual revoke/reinstate/rollback vẫn cần Owner authorize đúng incident/target.
- **Status:** APPROVED — Logical Policy.

## Stage 2 D1–D4 review — historical pre-approval evidence

**Historical boundary:** phần dưới giữ Stage2 recommendations/Pending/blocker/không-commit evidence trước current Owner Stage3 approvals; không current status hoặc yêu cầu approve lại D1–D3. Current formal dispositions ở section tiếp theo.

Authority/evidence: [Final SCD2 B7](wwi-final-scd2-design-specification.md), [ADR-SCD-01](../adr/scd-01-product-attribute-tracking.md), [ADR-SCD-06](../adr/scd-06-controlled-unresolved-publication.md), A06/INC/ACK và current Owner task. [Specification section 10](wwi-dw-03c-change-propagation-design-proposal.md) chứa comparison/recommendation/impact/evidence details, không lặp thành ADR mới.

| Review ID | Already fixed | Recommended option for remaining decision | Schema/pipeline/reporting implication | Status / authority |
| --- | --- | --- | --- | --- |
| D1 | B7 bắt buộc declared attrs/NK/incarnation/roles/intervals/selected versions và audit; không current/all-version default | Explicit enumerated selected-version set theo target analytical base+registry revision, source correction value từ accepted compatible Raw pin; current-only là explicit singleton request, không dynamic latest | Unselected versions/measures/SKs invariant cho Type1-only; dependent descriptors/marts rebuild và recert; không admit CustomerName/attrs ngoài approved set | **PENDING OWNER APPROVAL** cho mode/reference point; B7 không reopen |
| D2 | CP-05 dependency-complete manifests/atomic visibility/B5, Sales-first đã Approved | Dependency-complete subject/view bundle: smallest safe KPI/view scope **plus transitive required inputs**, joint consumer bundle khi cross-view/subect needs consistency | Reuse shared exact compatible builds/registry pins; không independent latest queries hoặc cross-publication consistency claim khi thiếu joint manifest | **PENDING OWNER APPROVAL** cho concrete unit/shared compatibility/consumer contract |
| D3 | CP-05 giữ prior valid versions, no partial Certified; CP-06 durable guarded transitions | Owner authorizes revoke/reinstate/rollback; DQ detects/holds candidate, operator executes approved audited transition; only validated compatible prior target can rollback | Non-destructive status/lineage/evidence trail, consumers see invalidation/supersession/as-of; no silent deletion/pointer regression | **PENDING OWNER APPROVAL** cho governance/visibility/rollback authority |
| D4 | CP-01/03/04 đã chốt old/new closure/state updates/full affected-mart rebuild | Confirm baseline A; closure includes fact PK/roles/intervals, dimension re-resolution, whole repeat populations và empty groups | No new architecture choice; generation incompatibility hold, B/C remain future optimization | **CONFIRMED — existing CP approvals**, không new approval |

**Minimum blocking set: D1, D2, D3.** Chúng không phải thiếu sáu CP approvals hoặc chưa chạy tests; cần Owner review đúng ba lựa chọn còn ảnh hưởng selected-version/publication/governance semantics. D4 không blocker. Numerical B5/physical runtime gates tiếp tục riêng theo [work plan](wwi-dw-03c-work-plan.md), không tự dùng chúng để falsely close hoặc tạo blocker kiến trúc khác.

DW-03C **IN_PROGRESS**, full design acceptance **PARTIAL / Owner decisions pending**. Không finalization commit/staging/push khi D1–D3 chưa được phê duyệt. DW-04 TODO, WWI-04/Phase1 IN_PROGRESS; production modules Not implemented yet, CP-T01–30 NOT RUN.

## Stage 3 — Formal Owner D1–D3 approvals and current D4 disposition

**Authority/date:** Project Owner instruction “DW-03C Stage 3 — Owner D1–D3 Approvals & Final Design Acceptance”,2026-11-16. Approvals được cấp trực tiếp, không inferred từ documentation QA, runtime hoặc agent recommendation.

| Decision | Formal disposition | Approved contract / exact limitation |
| --- | --- | --- |
| D1 | **APPROVED — Logical Policy** | Explicit Type1 selected-version set anchored to pinned analytical base/publication, compatible accepted Raw publication, persistent registry revision và recorded analytical build identity; reproducible/frozen selection, source evidence/correction rules/B1–B9 preserved; no physical storage/lookup approval |
| D2 | **APPROVED — Logical Policy** | Initial analytical unit là dependency-complete subject/view bundle, complete compatible transitive closure/version pins/build-publication/recon-certification/predecessor/durable promotion; joint consumer manifest required for cross-subject consistency, missing joint proof holds cross-subject certification/publication; Sales-first preserved; no physical table/lock/pointer approval |
| D3 | **APPROVED — Governance Policy** | DQ/Validation detects/collects/recommends hold/revoke; Project Owner authorizes revoke/reinstate/rollback; Operator executes authorized transitions and durable audit. Invalid Certified incident/affected dependency/hold-invalidation/evidence-preservation/consumer notification-or-block/transition outcome recorded. Rollback only existing compatible validated appropriately certified target; no valid replacement → hold. No silent destructive history change; no automatic lifecycle action trong task docs |
| D4 | **CONFIRMED — CP-04 baseline** | Full rebuild mỗi affected mart, no unrelated platform rebuild, old/new/empty groups/headers/re-resolution/distinct-ratios/generation guards; B/C optimization only future equivalence evidence |

### D1 compatibility finding

D1 phù hợp B7/ADR-SCD-01 explicit scope/audit, B1/B2 persistent identities/continuity/supersession, B3 lookup, B4 U conservation, B6 source/forward lineage và B9 exact text. Four anchors bổ sung recorded build identity và reproducible set; không admit attrs, không thay Type2 vector/source measures/business-time hoặc chọn physical allocator/member/lookup algorithm. Không phát hiện accepted-DW02 conflict cần escalation.

### D2 and D3 interpretation limits

Subject independence chỉ khi shared dependencies/downstream compatibility được prove; joint consumer cannot select independent latest and claim coherent platform state. Manifest/RBAC/locking/pointer enforcement/runtime tests vẫn deferred, không AP runtime PASS.

D3 là governance authority, không blanket authorization thực hiện lifecycle transitions: từng revoke/reinstate/rollback cần Owner decision/target/evidence. DQ role không tự được delegate execute. Gate failures không publish invalid Certified state; no replacement hợp lệ → hold, không expose uncertified fallback. B5 numeric values vẫn Pending; no automatic current publication action trong documentation task.

**Current decision blocker set: none trong mandatory logical/governance design sau D1–D3 approvals.** Per-request correction/action approvals, B5 values và CG/G/RG/runtime proof vẫn cần đúng stage trước use, không là unresolved D1–D3 architecture choices. [Final assessment](wwi-dw-03c-assessment.md) ghi conditional acceptance thực tế; không từ approvals alone tự đóng task.

Decision trail: Stage1 CP proposals → Stage2 six CP logical approvals +15PASS/3PARTIAL → Stage3 D1/D2 Logical+D3 Governance approvals, D4 confirmed → final design/QA review. Stage1/2 pending/no-commit notes giữ history. DW-04 chưa bắt đầu.

**Final current outcome:** DW-03C **DONE — Design** sau18/18 mandatory design criteria/actual QA theo conditional Owner authority. CP/D1/D2 Logical và D3 Governance approvals không là runtime approval; G/RG/CG/B5/action-proof gates remain pending. Không DW-04 hoặc implementation trong task này.
