# WWI Implementation Readiness & Milestone Handoff — DW-04

**2026-11-16. Design handoff only.** Không authorize code/provisioning/phase transition, không runtime evidence mới. [DW-04 Assessment](wwi-dw-04-assessment.md) giữ architecture/source/model/KPI traceability và conditional acceptance; [Gate Register](wwi-implementation-gate-register.md) giữ31 original gates. Original [TASKS](../../TASKS.md)/[ROADMAP](../../ROADMAP.md) là phase/dependency authority.

## 1. Implementation readiness khác operational readiness

Classes theo task: **1 Ready to implement**, **2 Ready with explicit prerequisites**, **3 Blocked pending Owner/technical decision**, **4 Out of current MVP scope**. Class1/2 nghĩa accepted design đủ guide authorized implementation, không deployment permission hoặc tests đã PASS. Mọi actual task vẫn cần Owner authorization/dependencies; chưa start Phase2.

B9 là scoped physical representation approval + isolated executed bounded PoC; production connectors/full Raw/registry/Core/marts/Airflow/Power BI **Not implemented yet**. No SQL/Docker/environment check tại DW-04; historical engine/profile/results không current service readiness proof.

| ID | Main component | Readiness class | Actual implementation state | Explicit prerequisites / gates | Implementation owner / earliest milestone |
| --- | --- | --- | --- | --- | --- |
| R01 | Python source connector | 2 — Ready with explicit prerequisites | Production Not implemented yet; isolated B9 connector subset Tested | Approved source profile/TLS/projection/dependencies; G02/G03/G06/CG08 | IN+SO/DQ; M1→M3 |
| R02 | SQL Server source consistency strategy | 3 — Blocked pending Owner/technical decision | A02 policy accepted, concrete current method/proof Unverified | No-writes interval evidence hoặc separately approved verified copy; G01/RG01 | SO+PO/IN/DQ; M1 before M3/M4 |
| R03 | Least-privilege source access | 3 — Blocked pending Owner/technical decision | PoC interactive rights không production proof | DBA service identity/effective grants/trusted profile; G02/RG02 | SO+security/PO; M1 |
| R04 | PostgreSQL Raw storage | 2 — Ready with explicit prerequisites | Conceptual design accepted, actual Raw schema absent | Reviewed physical DDL/access/capacity/retention/codec mapping before execute; G04/G07 | ST+PO/DQ; M2 |
| R05 | Temporal field preservation | 1 — Ready to implement | B9 physical TEXT/C contract Approved; bounded PoC Verified | Implement exact approved F2/str-None/psycopg/TEXT path; actual full-field regressions mandatory G03–G05 | IN+ST/DQ; M2/M3 before M4 |
| R06 | Source datatype adapters | 2 — Ready with explicit prerequisites | Fidelity obligations complete; special adapters Unverified | Physical exact decimal/Unicode/bytes/geography/computed/NULL mapping approval and tests; G06/RG05 | IN+ST+PO/DQ; M2/M3 |
| R07 | Metadata, capture and publication manifests | 2 — Ready with explicit prerequisites | A03/A04/A06/INC/D2 logical identity/pinning accepted | Physical key/schema/atomicity/durable read-back/consumer enforcement G07/G08/RG08/CG05 | ST+IN+OP/DQ; M2/M4/M8 |
| R08 | Full Load | 2 — Ready with explicit prerequisites | Scope/projection/current+H design complete; no full ingestion runtime | Source method/profile/fidelity/physical target and I01–I12/full failure tests; G01–G08 | IN+ST/DQ; M3/M4 |
| R09 | Incremental Load | 2 — Ready with explicit prerequisites | INC-01–06 accepted; no implemented algorithm/schedule | Exact W/U/lookback/cadence/sandbox/recon/checkpoint proof and approvals; RG01–RG10 | IN+SO+PO/DQ; M7 |
| R10 | Checkpoint and recovery | 2 — Ready with explicit prerequisites | ACK/AP/CP-R logical contracts accepted; runtime NOT RUN | Durable predecessor/content/commit/visibility/idempotency/race/fencing proofs; G08/RG08/CG07 | ST+OP+IN/DQ; M4 then M7/M8/M6 |
| R11 | dbt Staging | 2 — Ready with explicit prerequisites | Model responsibility accepted; no dbt project | Approved dependencies/schema/field codecs, accepted Raw pins and occurrence-safe lineage; G06/CG05 | DW+ST+PO/DQ; M5 |
| R12 | SCD2 Dimensions | 2 — Ready with explicit prerequisites | B1–B9/D1 policy complete, registry not implemented | Physical registry/lookup/member design, exact basis/full-day/R-U-I/continuity/selected-set tests; CG02/09 | DW+custodian+PO/DQ; M5 baseline/M8 changes |
| R13 | Facts | 2 — Ready with explicit prerequisites | 4 approved source grains; no Core facts implemented | Compatible headers/dims/registry/date/reference pins, state replacement/sign/U/old-new tests; CG01–03/10 | DW+ST/DQ; M5/M8; Inventory later |
| R14 | Analytics Marts | 2 — Ready with explicit prerequisites | Six logical marts/full affected rebuild baseline accepted | Complete input scopes/KPI semantics/grain/role/distinct/ratio/full oracle; CG04/05 | AO+DW/DQ; M6, later Customer/Inventory |
| R15 | Airflow orchestration | 2 — Ready with explicit prerequisites | DAG responsibility defined; no orchestration implementation | WWI-07+WWI-08 runtime acceptance, approved environment/scheduling/retry/consumer identities | OP+IN+DW/DQ; M9/WWI-09 |
| R16 | Data Quality and reconciliation | 1 — Ready to implement | Logical rules/counts/keys/amount/qty/R-U-I contracts accepted | Implement basic exact checks from first code; numeric exception/severity values need PO before use; RG11/B5 | DQ+all implementers; M3 onward, not only M9 |
| R17 | Certified publication | 3 — Blocked pending Owner/technical decision | B5/D2/D3/CP policies accepted, no actual certificate | B5 numerical values/threshold policy+actual AP/runtime/Owner-action/consumer proofs; CG05–07 | DQ+AO+PO/ST+OP; before any Certified M6 |
| R18 | Power BI consumption | 2 — Ready with explicit prerequisites | Consumer contracts accepted; no report/semantic artifact | WWI-08/10 then WWI-11, accepted subject/joint pins, label/tier/role controls; distribution policy before public demo | AO+PO/DQ; M6 formal release |

Class4/exclusions tách khỏi18 components: Purchasing/Finance/BigQuery chỉ controlled extensions; S07 AOV/S08 Recognized Revenue Deferred; S10 Refund Credit Note/I06 daily balance/I07 stockout risk unsupported current evidence, không lập implementation target/value0. Optional KPI S09/C04/C05/I03/I05 chỉ enabled khi own data/policy/tests ready. Kafka/streaming/new platforms ngoài MVP.

## 2. Reconcile candidate M1–M9 với existing phases/tasks

M labels là **handoff work packages**, không task IDs/phase replacement hoặc execution authorization mới. Sales-first source scope phải declared/approved trước capture; minimal Customer/Product current+H dependencies phục vụ Sales không nghĩa hoàn tất Customer Analytics. Inventory movement/holdings/type dimensions/facts/marts triển khai theo WWI-13 sau WWI-12/WWI-11, không dựng toàn platform trước first Sales result.

Actual existing dependencies: WWI-09 requires WWI-07+WWI-08; WWI-10 requires WWI-09; WWI-11 requires WWI-08+WWI-10. Vì vậy candidate M6 đứng trước M7/M9 **không thể là formal release** nếu giữ repository roadmap. Recommended execution order:
**M1 → M2 → M3 → M4 → M5 → M7 → M8 → M9 → M6**.
M5/M7 independent subwork có thể được giao song song nếu explicit dependencies/proofs satisfied; không tự change existing tasks.

M4 là first small verifiable source→Raw slice. M5 adds minimum Sales Core; M7/M8 adds safe changed-state acceptance; M9 operationalizes same Sales slice; M6 is first formal verifiable Sales mart/Power BI end-to-end result. Chưa cần toàn Customer/Inventory/optional/cloud platform. Earlier candidate/Uncertified experiments không được gọi WWI-11 DONE hoặc đổi phase sequencing; muốn formal Power BI earlier phải Owner approve roadmap/dependency change riêng, không làm trong DW-04.

Baseline SCD2/registry/lookup/R-U-I required for initial Sales **ở M5**; M8 mở rộng changed-state correction/recovery/certification-control readiness, không trì hoãn historical lookup integrity rồi dùng current fallback. Likewise Raw atomic/retry/reconciliation/precision tests ở M3/M4, không đợi M9 monitoring. Basic unit/CI/test strategy bắt đầu từ first code trong authorized tasks, không đợi Phase9.

~~~mermaid
flowchart LR
    M1[M1 Local readiness] --> M2[M2 Physical Raw review]
    M2 --> M3[M3 Full candidate capture]
    M3 --> M4[M4 Reconciled Raw publication]
    M4 --> M5[M5 Minimum Sales Core]
    M4 --> M7[M7 Incremental convergence]
    M5 --> M8[M8 Changed-state recovery readiness]
    M7 --> M8
    M8 --> M9[M9 Sales Airflow quality operations]
    M9 --> M6[M6 Formal Sales marts and Power BI]
~~~

M8 có thể prepare B5 measured proposal/control proofs; actual mart certification chỉ sau M6 build/member/KPI/consumer tests, không certify nonexistent marts. M9 không requires unreleased M6, nên dependency graph không cycle.

## 3. Milestone contracts — goals/inputs/deliverables/dependencies/tests/gates/DoD/demo

Tất cả milestones **PLANNED — NOT STARTED**. Các commands/config/schema/dependencies sẽ chỉ viết/chạy trong implementation task authorized sau này.

### M1 — Local infrastructure / connection contracts

- **Goal / task mapping:** Phase2/WWI-05; cần Owner nghiệm thu tổng thể và cho phép phase/task, không provisioning trong DW-04.
- **Inputs:** Source/access constraints đã duyệt, inventory môi trường hiện có và G01/G02/RG02.
- **Exact deliverables:** Hồ sơ có version về môi trường/profile/bảo mật/tái lập; proposal/approval consistency method, bằng chứng least-privilege, kế hoạch test environment độc lập; chỉ cấu hình khi task cấp quyền.
- **Dependencies:** Chưa thực hiện; cần review WWI-04/Phase1 và Owner giao task, trước M2/M3.
- **Acceptance tests:** IT01 metadata/profile; bằng chứng TLS/quyền không ghi nguồn; negative tests cho allowlist.
- **Gate IDs:** G01/G02/RG01/RG02/CG08.
- **Definition of Done:** PO/DBA review phạm vi setup; source/target profiles an toàn, runbook không secret; method/profile chưa rõ phải giữ Blocked.
- **Portfolio demonstration evidence:** Version/grants/kết quả kết nối và consistency evidence đã loại thông tin nhạy cảm, không credential/raw dump.

### M2 — Physical Raw and metadata

- **Goal / task mapping:** WWI-05 physical review → WWI-06 schema operation khi được cho phép.
- **Inputs:** M1 profiles/source contracts/B9/Gate Register.
- **Exact deliverables:** Proposal có review về field/control/manifest schema, projection/codec/identity/retention/capacity; sau approval mới tạo target objects đúng phạm vi và tài liệu restore/rollback; không thêm công nghệ mặc định.
- **Dependencies:** M1; duyệt G06/G07 trước DDL/loader code/full payload.
- **Acceptance tests:** Kiểm thử actual full-field serialization/NULL/exact temporal fixtures, schema/access/constraints; B9 regression trên actual path.
- **Gate IDs:** G03–G07/RG05/RG12/CG09.
- **Definition of Done:** Physical mapping/schema/dependencies được duyệt, target độc lập sẵn sàng cho source-preserving Raw tests; không secret/backup trong Git.
- **Portfolio demonstration evidence:** Mapping review/DDL version khi được cho phép, expected/actual codec và schema tests; không tự nhận đã production load.

### M3 — Python full extraction / candidate Raw

- **Goal / task mapping:** Phase3/WWI-06 implementation khi được giao.
- **Inputs:** M1 consistency/least privilege, M2 target/mappings đã review; capture scope Sales tường minh.
- **Exact deliverables:** Connector/extractor/loader tests và module README; candidate capture đủ current/H thuộc scope, immutable manifests, identities riêng, chunk coverage và toàn bộ source columns.
- **Dependencies:** M1+M2; no-writes/copy evidence phải bao phủ bounds/reads/reconciliation, khai báo scope trước run.
- **Acceptance tests:** Source/context/keys/NULL/full-field/H multiset/100ns/count/amount/quantity; interrupted extraction/partial load/unsupported conversion.
- **Gate IDs:** G01–G07/RG01/RG05/RG06/CG08.
- **Definition of Done:** Candidate capture đầy đủ, sealed, faithful và có context/coverage tái kiểm chứng; chưa normal published/Certified.
- **Portfolio demonstration evidence:** Run/attempt/capture IDs thực, manifests/count/type comparison/error logs đã bảo vệ; duration chỉ số đo thực.

### M4 — Raw reconciliation / publication / replay

- **Goal / task mapping:** Hoàn tất nghiệm thu WWI-06.
- **Inputs:** M3 sealed captures, cùng source context C cho count/key/value/H evidence; target control contract đã duyệt.
- **Exact deliverables:** Basic DQ/reconciliation reports; atomic ledger/member/pointer/ACK và immutable replay/read-back thực tế; tài liệu failure/recovery.
- **Dependencies:** M3; mọi gate B trước normal Raw publication đầu tiên.
- **Acceptance tests:** I01–I12 subset Sales bắt buộc; key/value/netting negatives, cùng-context H multiset, missing stream, retry/unknown commit/partial visibility/concurrent stale request; IT15–18 full-baseline subset.
- **Gate IDs:** G08/RG08/RG09/RG10/RG11/CG07.
- **Definition of Done:** RawPublished faithful và dependency-complete, exact outcome/pins; failed candidate không visible, replay không nhân bản hoặc làm lùi pointer.
- **Portfolio demonstration evidence:** Source-vs-Raw reconciliation/durable publication và injected failure/replay traces đã loại thông tin nhạy cảm; chưa Certified.

### M5 — dbt Staging + minimum Sales dimensions/facts

- **Goal / task mapping:** Phase4/WWI-08 baseline.
- **Inputs:** M4 accepted Raw; physical staging/Core/registry/config/field admission và lookup/member contracts đã duyệt.
- **Exact deliverables:** Staging có lineage và giữ occurrences; OH/IH, DD/minimum DC+DP/registry, FI/FO initial accepted state; basic field/DQ/dbt tests/docs/mapping.
- **Dependencies:** M4; gates D trước baseline lookup/facts use; DM/FM/FC và full Customer subject không chặn initial Sales.
- **Acceptance tests:** Baseline CD tests, whole-day/exact lookup/R-U-I/registry replay; all-header/no-line/uninvoiced/role tests; source-grain amount/quantity/PK reconciliation.
- **Gate IDs:** G05/CG01/CG02/CG05/CG09/CG10.
- **Definition of Done:** Minimum approved SCD2/registry/historical lookup hoặc valid U có lý do; giữ population/measures, I chặn publication; không fallback current/earliest hoặc dời semantics bắt buộc.
- **Portfolio demonstration evidence:** Accepted Core build/registry/input refs; dbt results/per-key totals/header counts/U-I coverage và giới hạn.

### M6 — Sales marts / initial Power BI release

- **Goal / task mapping:** Phase7/WWI-11 formal release sau WWI-08+WWI-10.
- **Inputs:** M5/M8 Core, M7 incremental, M9 Airflow/quality readiness; B5/consumer/subject contracts đã duyệt.
- **Exact deliverables:** Full rebuild Sales mart đã chọn, semantic/report artifact, KPI source/date/role/population measures, subject/certification/consumer pins và demo evidence an toàn.
- **Dependencies:** M9+M5/M8; giữ dependencies WWI-11. Có thể phát triển candidate/Uncertified trước gates E khi được giao, không tự release.
- **Acceptance tests:** CP-T03/04/18/19/23/24/25–30 theo mart/tier/consumer/rollback; Kxx source→Core→mart reconciliation; single-role/non-additive ratio tests.
- **Gate IDs:** CG04–CG07/B5/RG11.
- **Definition of Done:** Ít nhất Sales view/report đã chọn được kiểm chứng từ compatible accepted bundle; Certified chỉ khi B5/AP proof đủ; historical breakdown chưa đủ phải Uncertified; Owner nghiệm thu trước WWI-12/13.
- **Portfolio demonstration evidence:** Report/manifest/refresh/pin IDs thực; approved KPI comparisons/DQ/coverage, demo/screenshots đã loại thông tin nhạy cảm và có quyền công bố; không unsupported revenue/COGS/AOV.

### M7 — Incremental / checkpoint convergence

- **Goal / task mapping:** Phase3/WWI-07; sau full Raw/Core baseline theo dependencies.
- **Inputs:** M4 normal full/replay, independent writable sandbox/profile được duyệt, concrete method/window/reconciliation/schedule approvals.
- **Exact deliverables:** Conditional W/T/S incremental theo từng source, current-state reconstruction; checkpoint/bounds/late/delete-candidate/replay/backfill lineage và test evidence.
- **Dependencies:** M4; phase/task authorization và RG02 sandbox riêng; có thể sau M5 hoặc song song khi được giao, không đổi dependencies.
- **Acceptance tests:** IT01–IT21 subset Sales bắt buộc end-to-end; same-time/old-key/backdated/late-commit/NULL/out-of-window/full-state reconciliation/delete-vs-absence/retry-ACK-loss; không ghi WWI gốc.
- **Gate IDs:** RG01–RG10/G08/CG03.
- **Definition of Done:** Observed/expected state hội tụ tới verified consistent C, không cam kết complete events; checkpoint neo durable publication, sandbox tests bắt buộc PASS trước incremental publish.
- **Portfolio demonstration evidence:** Before/after fixture states có kiểm soát, exact key/value diffs, window/checkpoint/full comparison/failure/replay evidence; WWI gốc giữ nguyên.

### M8 — Sales SCD2/restatement/recovery and certification-control readiness

- **Goal / task mapping:** Hoàn tất changed-state WWI-07/08, chuẩn bị WWI-10 release controls.
- **Inputs:** M5 baseline dims/facts+M7 accepted changes; approved action/correction scopes và registry/forward set đầy đủ.
- **Exact deliverables:** Thực thi D1 frozen selected-set; source-history/forward bridge, split/merge/re-resolution/rekey/old-new restatement, D2/D3 tests/runbook; không Certified mart khi thiếu M6 dependencies.
- **Dependencies:** M5+M7; D1/D2/D3 policies đã duyệt, per-action/basis/physical proof vẫn bắt buộc; không dời baseline rules M5.
- **Acceptance tests:** CD-T01–21 changed-state/recovery phù hợp; CP-T01–22/26–29 Core controls; accepted-registry restore/no-registry negative/candidate isolation; B5 proposal/test readiness.
- **Gate IDs:** CG01–CG03/CG05–CG09/B5.
- **Definition of Done:** Changed-state Sales Core/recovery controls được test đúng trước use; giữ opaque SK/forward history/source measures; duyệt B5 values trước Certified M6, không cấp chứng nhận cho mart chưa tồn tại.
- **Portfolio demonstration evidence:** Audited old/new mapping/groups/measure comparisons; supersession/registry restore; incident/Owner approval/operator outcome chỉ trong sandbox được duyệt.

### M9 — Airflow / CI / operational hardening

- **Goal / task mapping:** Phases5–6: WWI-09 rồi WWI-10; WWI-16 tổng hợp portfolio sau.
- **Inputs:** WWI-07(M7)+WWI-08(M5/M8) đã nghiệm thu; environment/schedule/control IDs được duyệt.
- **Exact deliverables:** Sales DAG/logs/metrics/alerts/central quality gates/runbook; scheduler/retry/replay/CI evidence thực và số đo hiệu năng, operational hardening.
- **Dependencies:** M5+M7+M8; không phụ thuộc Power BI chưa release; M6 formal sau WWI-10; basic tests/CI bắt đầu cùng code trước M9.
- **Acceptance tests:** Orchestration no-start/partial/retry/concurrent/crash, enforcement/alerts/recovery và scheduled full/incremental reconciliation; chỉ rerun earlier tests khi path thay đổi cần thiết.
- **Gate IDs:** G08/RG04/RG10/CG05–CG09; WWI-09/10 AC.
- **Definition of Done:** Sales orchestration/monitoring/CI/runbook được nghiệm thu; không bypass gate hoặc ACK từ task-success; đủ recovery/notification evidence; mở WWI-11, chưa toàn subject expansion.
- **Portfolio demonstration evidence:** DAG run IDs/task retries/CI logs/alerts/recovery demo và số đo so sánh thực; không bịa benchmark.


M6 formal Sales accept là gate mở WWI-12 Customer Analytics rồi WWI-13 Inventory Movements; tables/model contracts đã thiết kế không đồng nghĩa chúng phải production implementation ở M3–M6. WWI-14/15 extensions và WWI-16 overall portfolio giữ existing dependencies. Không tự tạo tasks/mark milestones DONE.

## 4. Earliest test allocation — complete72-scenario ledger

Original tests giữ IDs/assertions: [DW-02 CD-T01–21](wwi-dw-02cd-assessment.md), [DW-03B IT01–21](wwi-dw-03b-incremental-design-proposal.md), [DW-03C CP-T01–30](wwi-dw-03c-change-propagation-design-proposal.md). Table là earliest implementation planning + must-pass use boundary, **không test results**. Multi-layer case có earlier subset và later full scenario; chưa run đủ thì full original scenario vẫn NOT RUN, không auto PASS từ subset.

| Original test ID | Existing scenario / scope | Earliest implementation milestone | Must-pass boundary | Gate / authority mapping | Current execution |
| --- | --- | --- | --- | --- | --- |
| CD-T01 | initial baseline | M5 | D baseline trước Core | CG02/G05 | NOT RUN |
| CD-T02 | new NK INSERT | M5 | D new-NK trước use; SQL fixture authorized | CG02/RG02 | NOT RUN |
| CD-T03 | Type1 UPDATE | M5/M8 | D Type1 action trước use | CG02/D1 | NOT RUN |
| CD-T04 | Customer Type2 UPDATE | M5/M8 | D baseline/Type2 changes trước use | CG02/B3 | NOT RUN |
| CD-T05 | optional/technical/excluded changes | M5 | D nontracked-change negative trước use | CG02/B7 | NOT RUN |
| CD-T06 | Product Type2 UPDATE | M5/M8 | D packaging version action trước use | CG02/B1 | NOT RUN |
| CD-T07 | same-transaction multiple updates | M3 Raw assertion; M7 full same-transaction fixture | B zero-duration retention trước M4; D lookup trước M5; C engine-write scenario M7 | G03/RG06 | NOT RUN |
| CD-T08 | no-change replay / failed retry | M4 Raw subset; M5/M8 registry | B Raw replay; D mapping retry trước normal use | G08/CG02/CG07 | NOT RUN |
| CD-T09 | several changes between observations | M7/M8 | C/D between-observation limits trước changed-state claim | RG03/RG06 | NOT RUN |
| CD-T10 | precision 100 ns / sentinel | M2/M3 | B authoritative field fidelity trước M4; D exact predicates trước M5 | G03–G05 | NOT RUN |
| CD-T11 | hash collision/canonicalization | M2/M5 | B/D canonical equality/registry identity before use | G06/CG02 | NOT RUN |
| CD-T12 | date-only disagreement | M5 | D whole-day proof/R-U-I before lookup acceptance | G05/CG02 | NOT RUN |
| CD-T13 | missing/multi match | M5 | D missing/multi-match before Core | CG02/B4 | NOT RUN |
| CD-T14 | late history/backfill correction | M8 | D/E late correction/split-merge before use | CG02/CG01 | NOT RUN |
| CD-T15 | DELETE/missing/reinsert | M7/M8 | C/D removal/reappearance action before use | RG07/CG03 | NOT RUN |
| CD-T16 | cutover bridge mismatch | M5 baseline; M8 bridge changes | D no forced timeline/lost forward evidence | RG06/CG02/CG09 | NOT RUN |
| CD-T17 | mid-publication failure | M4 Raw subset; M5/M8 Core; M6 marts | B/D/E atomic scope before corresponding publish | G08/CG05/CG07 | NOT RUN |
| CD-T18 | rebuild preserve mapping | M5 registry backup; M8 restore | D compatible mapping restore before equivalence/use | CG09/B2 | NOT RUN |
| CD-T19 | rebuild without registry | M5/M8 | D hold/non-equivalence when registry lost | CG09/CG02 | NOT RUN |
| CD-T20 | current Product refresh | M5 contract tests; WWI-13 live Inventory | D/E before FC/IC current-state publication | CG02/CG05 | NOT RUN |
| CD-T21 | header-only fact update | M5 initial; M8 correction | D/E header propagation before affected use | CG01/CG04 | NOT RUN |
| IT01 | Read-only metadata/Q11/current+H recheck | M1; M7 recheck | A source metadata/profile; C timestamp refresh | G01/G02/RG02 | NOT RUN |
| IT02 | INSERT + replay, writable SQL sandbox | M7 | C concrete W/late/old-key/replay before publish | RG03/RG04/RG10 | NOT RUN |
| IT03 | UPDATE key cũ, LEW tăng | M7 | C concrete W/late/old-key/replay before publish | RG03/RG04/RG10 | NOT RUN |
| IT04 | UPDATE key cũ LEW không đổi / backdated | M7 | C concrete W/late/old-key/replay before publish | RG03/RG04/RG10 | NOT RUN |
| IT05 | Nhiều keys cùng LEW, chia nhiều pages | M7 | C concrete W/late/old-key/replay before publish | RG03/RG04/RG10 | NOT RUN |
| IT06 | Long transaction commit sau upper-bound selection | M7 | C concrete W/late/old-key/replay before publish | RG03/RG04/RG10 | NOT RUN |
| IT07 | Correction nằm ngoài proposed lookback | M7 | C concrete W/late/old-key/replay before publish | RG03/RG04/RG10 | NOT RUN |
| IT08 | Temporal nhiều UPDATE trong một transaction | M3 known H assertions; M7 writable scenario | B H preservation trước M4; C full event scenario before temporal incremental | RG06/G03 | NOT RUN |
| IT09 | Current→H, duplicate starts/identical H payload | M3/M4; M7 new observations | B/C occurrence/multiset before claim | RG06/G08 | NOT RUN |
| IT10 | H correction/cleanup/restore, approved maintenance sandbox riêng | M7/M8 authorized maintenance fixture | C/D generation/retention before enabled path | RG06/CG09 | NOT RUN |
| IT11 | Holdings update quantity/cost với LEW cũ | M7 contract tests; WWI-13 live holdings | C/E full current snapshot before holdings publish | INC-05/CG05 | NOT RUN |
| IT12 | DELETE ordinary/current temporal, full vs partial snapshot | M7 | C candidate absence before delete-related claim | RG07 | NOT RUN |
| IT13 | Delete→reappearance cùng NK | M7/M8 | C/D reappearance before identity/action use | RG07/CG03 | NOT RUN |
| IT14 | INSERT→DELETE hoặc A→B→A giữa polls | M7 | C disclose transient-event limitation before convergence claim | RG03 | NOT RUN |
| IT15 | Interrupted extract/partial load/reconcile fail | M3/M4 full subset; M7 incremental | B/C partial failure before respective publish | G08/RG08 | NOT RUN |
| IT16 | Reconcile PASS/publication fail/unknown commit | M4 full subset; M7 incremental | B/C unknown commit before ACK | G08/RG08 | NOT RUN |
| IT17 | Commit success/crash/retry/concurrent stale base | M4 full subset; M7 incremental | B/C race/retry/read-back before use | G08/RG08 | NOT RUN |
| IT18 | Replay sealed/backfill/new context/full reload | M4 replay; M7/M8 backfill/registry | B/C/D preserve lineage/mappings before use | RG08/CG09 | NOT RUN |
| IT19 | Header-only date/buyer/bill-to change | M5 source-header baseline; M7/M8 changes | C/D/E propagation closure before affected publish | RG09/CG01 | NOT RUN |
| IT20 | NULL/Unicode/decimal/bytes/geography/time fixtures | M2/M3; M5 lookup | B/D full-field/null/100ns before use | G03–G06/CG02 | NOT RUN |
| IT21 | Source drift, reference/generation changes và recon totals netting | M4 full; M7 incremental | B/C source drift/generation/netting before state claim | RG01/RG03/RG09 | NOT RUN |
| CP-T01 | Accepted invoice/header+lines pins; chỉ đổi InvoiceDate/buyer/bill-to | M5/M8 | D/E header closure before affected output | CG01 | NOT RUN |
| CP-T02 | Accepted OH; chỉ đổi OrderDate/buyer, gồm uninvoiced/no-line headers | M5/M8 | D/E order/repeat old-new before use | CG01 | NOT RUN |
| CP-T03 | Same InvoiceLineID sửa ExtendedPrice/TaxAmount/qty | M5; M6 mart oracle | D/E state measures before release | CG04/CG01 | NOT RUN |
| CP-T04 | Line đổi parent/product/date group, old group trở nên rỗng | M5/M8; M6 groups | D/E old empty-group removal before output | CG01/CG04 | NOT RUN |
| CP-T05 | New entity/new order line/replayed source capture | M5; M7 replay | D/C one grain/registry identity before use | CG02 | NOT RUN |
| CP-T06 | Approved D1 four-anchor contract, future authorized environment/action scope; admitted Type1 correction, explicit frozen selected-version plan | M5/M8 | D selected Type1 action only explicit four-anchor set | CG02/D1 | NOT RUN |
| CP-T07 | Approved Type2 vector và late historical evidence | M5/M8 | D late approved vector/validity before lookup | CG02/RG06 | NOT RUN |
| CP-T08 | Boundary-only correction with proven unique continuity | M8 | D/E boundary continuity before restatement | CG02/B1 | NOT RUN |
| CP-T09 | Approved episode split proposal input | M8 | D/E split before changed publication | CG02/B1 | NOT RUN |
| CP-T10 | Contiguous merge và negative noncontiguous A→B→A | M8 | D/E merge/noncontiguous negative before use | CG02/B1 | NOT RUN |
| CP-T11 | Previously U fact, new eligible unique dimension evidence | M5/M8 | D/E U→R before re-resolution output | CG02/B4 | NOT RUN |
| CP-T12 | Direct H zero-duration/duplicate-start/duplicate occurrence corpus | M3 Raw; M5 lookup | B/D zero-duration/multiplicity fidelity before use | G03/RG06/CG02 | NOT RUN |
| CP-T13 | Missing basis/coverage vs proven overlapping/multi-match periods | M5 | D missing basis vs integrity before Core | CG02/B4 | NOT RUN |
| CP-T14 | Partial snapshot absence, complete candidate absence, separately authorized confirmed retraction | M7/M8 | C/D/E controlled retraction before action | CG03/RG07 | NOT RUN |
| CP-T15 | Entity disappears/reappears same NK, continuity evidence missing/present | M7/M8 | C/D identity/incarnation before action | CG03/B8 | NOT RUN |
| CP-T16 | Movement decimal quantity/sign/date/type/product correction | M5 contract tests; WWI-13 live movements | D/E sign/grain/type before FM/MD use | CG10/CG01 | NOT RUN |
| CP-T17 | Complete holdings/Product state and incompatible state negative | M5 contract tests; WWI-13 live state | D/E FC/IC pins before Inventory publication | CG05/CG02 | NOT RUN |
| CP-T18 | Multiple payments InvoiceID NULL; Buyer≠Bill-to | M5; M6 semantic proof | D/E financial/roles no allocation before reporting | CG05/BRD-08/10 | NOT RUN |
| CP-T19 | Header populations/products/time filters và buyer một order mỗi tháng | M5 header checks; M6; WWI-12 repeat | D/E correct distinct/ratios/populations before enabled reporting | CG04 | NOT RUN |
| CP-T20 | Raw accepted, downstream request never starts | M4 Raw consumption proof; M5 downstream | B/D durable unconsumed state before use | G08/CG07 | NOT RUN |
| CP-T21 | Staging sealed, dimension build failure mid-registry | M5 | D partial dimension/registry before Core publication | CG02/CG07 | NOT RUN |
| CP-T22 | Dim/registry complete, fact partial failure | M5 | D partial facts before Core acceptance | CG05/CG07 | NOT RUN |
| CP-T23 | Facts complete, one required mart fails | M6 | E mart failure cannot expose mixed certificate | CG05 | NOT RUN |
| CP-T24 | All builds done, key/group recon mismatch though net totals equal | M5 Core; M6 mart | D/E per-key/group netting before promotion | CG04/CG05 | NOT RUN |
| CP-T25 | Certification commit outcome/ACK lost | M4 Raw analog; M6 full analytical | B/E durable ACK-loss before respective use | G08/CG07 | NOT RUN |
| CP-T26 | Same request replay và two equivalent concurrent attempts | M4 Raw analog; M5/M8/M6 actual scopes | B/D/E duplicate/equivalent concurrency before respective use | CG07 | NOT RUN |
| CP-T27 | Concurrent differing content/stale predecessor | M4 Raw analog; M5/M8/M6 actual scopes | B/D/E conflicting concurrency before respective use | CG07 | NOT RUN |
| CP-T28 | Raw supersession/restore changed generation during recovery | M4 source pins; M7/M8 changes; M6 consumer | B/C/D/E generation compatibility before use | CG05/CG09 | NOT RUN |
| CP-T29 | Approved historical restatement + failure/rollback/new retry | M8 Core restatement; M6 mart/lifecycle | D/E historical restore/rollback full dependency before use | CG01/CG06/CG09 | NOT RUN |
| CP-T30 | D2 Logical/D3 Governance Approved, B5 values/per-action authority và runtime setup required trước test; tiered refresh, historical U và invalid certificate/rollback cases | M6; later subject joint refresh | E B5/D2/D3 role/consumer/valid certified target/hold before certification or action | B5/CG05/CG06 | NOT RUN |

Before first full Raw publication M4, ngoài original scenarios cần execute existing Source Validation I01–I12 applicable Sales population: exact same-context count/key/value/NULL/type/amount/qty/H occurrence/fidelity+partial/replay/accepted-manifest controls. No empty/missing input interpreted0. Purchasing receipt check I10 NOT APPLICABLE nếu chưa separately approved dependency; reference/inventory checks apply trước enabled publication, không enforce nonexistent subject as Sales prerequisite.

CD-T07/IT08 same-transaction writable temporal generation có full scenario ở M7 sandbox; **known/current H zero-duration preservation vẫn phải tested M3/M4** và lookup no-positive-duration guard M5. CD/CP Inventory contracts có thể fixture-test sớm; actual FM/FC/MD/IC live proof required trước WWI-13 publication. Advanced optional paths không required cho earlier independent Sales scope, nhưng basic shared full-field/identity/registry safety không được waive.

### Existing B9 executed evidence — tách biệt

[DW-03A evidence section15](wwi-dw-03a-evidence-approval-readiness.md)/[B9 README](../../tests/integration/b9_precision/README.md) record executed bounded proof:12 unit methods,14 SQL→Python fixtures,169 order pairs,18 sampled period cells; PG14 parameters/15 persisted-readback/169 ordering/14 equality/5 ranges PASS, commit-close-reconnect evidence. Driver/server/digest/raw-result hash/commands đã có trong original report. Không chạy lại, không sửa PoC hoặc verify service availability tại DW-04.

B9 scope không entire Raw schema/full projection/type codecs/source no-writer/least-privilege/production performance/restart/crash reliability; G03–G08 still require actual-path regression/evidence. CD-T/IT/CP NOT RUN không đổi vì bounded B9 PASS.

## 5. Evidence required before portfolio claims / operational release

Mỗi DoD phải có actual command/version/input/expected/actual/status/artifact revision/source+build+publication pins và reviewer result. No “worked” from design text. Test failures retained với root cause/next step, không overwrite failed evidence để chỉ còn PASS.

Sanitize logs/manifests/screenshots; no credentials/PII/contact payload/database backups/source extracts in Git. Public portfolio/dataset distribution requires Owner license/privacy approval trước publish/push. Benchmark chỉ actual measured runs/conditions/plans, không invent performance/scale hoặc claim avoids full scans khi full comparison đọc toàn source.

No Operational Readiness hiện tại: physical environment/schema/access/consistency/profiles/schedules/thresholds/DB tests/pipeline/DAG/report not implemented/verified for project. Design acceptance chỉ đủ guide tasks, all normal publication gates enforce trước use.

## 6. Recommended first implementation task — recommendation, not started

**WWI-05 / M1A — Local readiness & secure connection-contract verification**, sau Owner review closure WWI-04/Phase1 và explicit Phase2/task authorization.

Bounded first scope: inventory existing local source/target/tools **read-only**, actual source endpoint/TLS/driver/version capabilities, least-privilege grant review with DBA, source consistency method/evidence plan, target/test sandbox allowlist/capacity/credentials-outside-Git/config version proposal. Do not interpret existing B9 sink hoặc interactive sysadmin as production target/identity.

Inputs: accepted DW-04/handoff/gates, externally available approved source, Owner/DBA authority. Deliver: secret-free readiness record/connection contract/explicit unresolved prerequisites/reproducibility steps/module README status; no Raw schema/ingestion/dbt/DAG creation in first bounded verification subtask unless separately authorized. Provisioning/dependency installation/source clone/target writes needs exact approved scope trước action, không tự dùng documentation approval làm permission.

DoD: G01/G02/RG02/CG08 prerequisites either proven with artifacts+approvals, hoặc accurately BLOCKED/Pending with responsible owner; không claim M1 complete nếu required source method/profile absent. Original WWI unchanged, no secret/source data staged. Next M2 chỉ sau prerequisites và Owner-assigned scope.

## 7. Parent/phase acceptance boundary

DW-04 conditional DONE không tự start Phase2. TASKS WWI-04 parent criterion gồm Owner nghiệm thu DW-01–DW-04 và approved source/incremental/history/as-of/independent-test design; DW-04 supplies consolidated evidence để Owner review tổng. Phase1 criteria còn broad Sales decisions/limits; physical choices được trace gates, không pretend implemented.

Current task không yêu cầu đóng parent/phase hoặc cấp implementation authority. Giữ **WWI-04/Phase1 IN_PROGRESS**, đề xuất Owner review overall closure/Phase2 assignment separately; không dùng runtime tests NOT RUN riêng lẻ như architectural blocker để phủ nhận design acceptance. Đây là completion/authorization tracking, không thiết kế mới. Phase2–9 Not Started.

## Owner follow-up — 2026-11-16, sau design review

[APPROVAL-01–05](../architecture/wwi-phase-1-closure-approval.md) giải quyết parent/phase sign-off còn thiếu ở hồ sơ trên: WWI-04 DONE — Design; Phase1 Completed — Requirements & Source Design; Phase2/WWI-05/M1A IN_PROGRESS — Authorized, ban đầu chỉ bounded verification sau Checkpoint A QA+commit. Historical parent-IN_PROGRESS/no-start statements giữ mốc trước approval. M2+ chưa được giao;31 gates/72 NOT RUN tests/architecture/B9 không đổi, không operational readiness approval.
