# WWI DW-03A — Owner Decision Approval Register

**DW-03A DONE — Design, 2026-11-15.** A01/A03/A04/A06 Approved — Logical Policy; A02 Approved — Conditional Logical Policy; A05 Approved — PoC Direction Only (unchanged). **B9 APPROVED — Physical Raw Temporal Representation** theo current Owner instruction, không nâng A05 thành full implementation approval. B1–B8/accepted DW-02 không đổi; runtime gates ở [Work Plan](wwi-dw-03a-work-plan.md), final acceptance evidence ở [Assessment](wwi-dw-03a-assessment.md) section15.

| ID | Quyết định được Owner phê duyệt | Gate còn mở / giới hạn approval | Status |
| --- | --- | --- | --- |
| A01 | Full source-preserving extraction: 9 current + 2 physical archives, giữ origin/occurrences/NULL/types/temporal evidence | Verified full extraction fidelity/completeness; không dedupe history hoặc chồng temporal-query populations | APPROVED — Logical Policy |
| A02 | Static window có defensible no-write evidence; nếu không, separately approved verified consistent copy; hold publication khi thiếu proof | Concrete method/operational evidence chưa verified; không tự enable SNAPSHOT/RCSI, NOLOCK claim hoặc long SERIALIZABLE | APPROVED — Conditional Logical Policy |
| A03 | Immutable Raw captures + reconciled publication manifests + downstream pinned publication IDs; preserve incremental/SCD2 evidence | Physical schema, retention periods, access control và capacity pending; không implicit physical-view/mirror approval | APPROVED — Logical Policy |
| A04 | Separate run/attempt/capture/logical batch/publication; retry compatible sealed content; new context → new capture | Durable state và recovery execution evidence trước production; physical keys/commit/checkpoints pending | APPROVED — Logical Policy |
| A05 | F2 preferred precision PoC direction (original approval unchanged) | B9 scoped physical decision được ghi riêng bên dưới; entire Raw/index/retention/runtime không approved | APPROVED — PoC Direction Only |
| A06 | Dependency-complete atomic ledger/membership/pointer transitions; consumers pin compatible publications | Crash/retry/concurrency/rollback/atomic visibility trước runtime; RawPublished không Certified marts | APPROVED — Logical Policy |

**Authority / date:** Project Owner, 2026-11-15, qua instruction **“DW-03A — Record Project Owner Logical Design Approvals”**. Đây là formal Owner approval trong đúng sáu mức nêu trên, không suy từ reviewer recommendation hoặc SQL PASS. [Evidence](wwi-dw-03a-evidence-approval-readiness.md) section 10 giữ số liệu thực thi; section 11 ghi approval milestone. [Work Plan](wwi-dw-03a-work-plan.md) section 4–6 giữ backlog tám gate và narrow B9 handoff.

**Current B9:** [ADR-SCD-05](../adr/scd-05-exact-temporal-precision.md) ghi F2→Python str/None→parameterized psycopg→authoritative PostgreSQL TEXT/C comparator, exact27/seven digits/NULL/boundaries/sentinel/100ns; derived timestamp secondary. Current Owner cấp **APPROVED — Physical Raw Temporal Representation**, không entire Raw schema/index/retention/runtime approval.

Các alternatives/trade-offs và chi tiết implementation dưới đây được giữ để trace; chỉ **Recorded Owner decision** và approved scope ở overview là authoritative approval. Không phê duyệt toàn bộ proposed physical mechanisms, service identity, dependency installation, source-copy creation hoặc runtime tests bằng instruction này.

## A01

- **Problem:** full load cần đúng source grain/population và history evidence, không chỉ current master values hoặc filtered analytical fields.
- **Constraints:** source read-only, chín current contracts; B1/B2/B6; current/archive khác grain, Customer start-key không unique; geography/blob/computed/Unicode không được silently drop.
- **Options considered:** current-only; full current + physical H streams; temporal AS OF/ALL; source-shaped full projection hoặc subset có approved exception.
- **Recommended option:** explicit full contract projections và physical H cho hai masters, candidate type adapters; PK keyset/streaming trong same approved context, H uninterrupted stream khi không unique key. Gắn source origin, retain multiplicity và zero-duration.
- **Rationale:** giữ evidence dùng lại được cho hybrid/SCD2, reconciliation và replay, không invent source/episode IDs. Design đủ chín nguồn nhưng Sales phục vụ trước, không mở Customer/Inventory analytics sớm.
- **Trade-offs:** nhiều payload/PII/photo bytes và archive reads hơn; cần service-account/archive permission và exact special-type adapters. Projection optimization chưa duyệt có thể làm mất evidence.
- **Risks:** source-schema drift, archive/current inconsistency, truncated values hoặc dedupe nhầm physical versions.
- **Evidence:** [dictionary](wwi-metadata-dictionary.md), [contracts](wwi-source-contracts.md), [profiles](wwi-data-profiling.md), [temporal evidence](wwi-scd-temporal-evidence.md); proposal A1. Trusted TCP, current/H mappings và interactive SELECT permissions đã tái xác minh tại evidence section 10; service-account/full capture/type-adapter proof chưa có.
- **Remaining approval / verification:** Full preservation scope đã Approved; least-privilege current/H access, concrete projection/adapters và fidelity/completeness evidence phải verified trước implementation/publication. Projection exceptions cần approval riêng; không tự drop fields.
- **Downstream impact:** Raw→staging giữ source rows, analytical version mapping sau Raw; reference ingestion ngoài chín current + hai associated H không tự được mở.

### A01 — Approval đã ghi nhận và implementation gates

- **Approved logical policy:** complete source-preserving current/H extraction đã được Owner duyệt; hai H không là independent sources. Sales-first declared scope không mở Customer/Inventory analytics sớm; stream/projection implementation và verification còn gate.
- **Evidence available:** A01 checklist/contracts/dictionary/profiling C01/C02/C04; latest SELECT metadata đủ 9 current + 2 H, 156 current columns và 56 H columns, temporal mappings/permissions/scale verified; bounded temporal samples giữ zero-duration. Không fresh full extraction hoặc refresh toàn bộ profiling.
- **Evidence missing:** least-privilege service-account access, full field adapter fidelity và same-context count/multiset/aggregate tests. Interactive metadata/permissions verified không thay full-extraction proof.
- **Residual risks / alternatives / trade-offs:** current-only/temporal-query-only thiếu physical evidence; full payload tăng bytes/PII/UDT adapter work. Stage 1 options giữ để trace, không approved subset/drop.
- **Implementation implications:** explicit projections và separate current/H manifests, source type/scale/NULL/origin giữ nguyên; no archive dedupe/source-default regeneration. References ngoài scope không được tự coi loaded.
- **Exact pre-implementation conditions:** Full preservation scope đã Approved; least-privilege current/H access, concrete projection/adapters và fidelity/completeness evidence phải verified trước implementation/publication. Projection exceptions cần approval riêng; không tự drop fields. Runtime verification chưa hoàn tất; không cấp quyền source writes/schema hoặc install từ logical approval.
- **Recorded Owner decision — APPROVED — Logical Policy, 2026-11-15:** Chấp thuận complete source-preserving full extraction cho chín approved current tables và hai physical temporal archives. Bảo toàn source origin, physical occurrences, NULL, source types và temporal evidence; không silently dedupe history hoặc ingest chồng physical archives với temporal-query populations. Extraction fidelity/completeness vẫn là implementation gates.

## A02

- **Problem:** sequential reads, source counts và current/H có thể thuộc các database states khác nhau.
- **Constraints:** WWI chỉ đọc trong project; database thực tế READ_WRITE, SNAPSHOT OFF, RCSI OFF theo trusted SELECT. Không tự bật isolation/config hoặc kết luận active writes từ flags.
- **Options considered:** C2/A evidence-backed static window; C5/B verified consistent copy hoặc separately approved snapshot environment; C3/C single read-only SERIALIZABLE transaction. C1 không khả dụng ở cấu hình hiện hành; C4/windowed/NOLOCK không thay common consistency proof.
- **Approved conditional direction / execution pending:** ưu tiên C2 khi kiểm soát và chứng minh được mọi writers trong toàn extraction interval; nếu không thì review C5 được chuẩn bị/verify độc lập. C3 chỉ với separate operational approval; không chạy long extraction transaction ở task này.
- **Rationale:** C2 đơn giản nhất cho local portfolio khi có operational evidence thật; C5 tách rủi ro khỏi nguồn khi không bảo đảm được static window. Serializable logical read không được gọi snapshot tại transaction start.
- **Trade-offs:** static window cần phối hợp vận hành; copy cần storage/provenance/quyền tạo ở task riêng; SERIALIZABLE shared/range locks có blocking/deadlock/resource risks.
- **Risks:** successful read-only client/sysadmin permission không bảo vệ khỏi writer khác; reconnect/new observation mất context; matching counts/FK không chứng minh consistency.
- **Evidence:** [Evidence & Approval Readiness](wwi-dw-03a-evidence-approval-readiness.md) section 10: trusted TCP/encrypt TRUE; OFF/OFF/READ_WRITE; 9 current + 2 H metadata/interactive SELECT rights. Chưa có extraction interval hoặc writer-control/copy/long-transaction proof.
- **Remaining approval / verification:** Conditional policy đã Approved; chosen window/copy method, scope/operational limits và evidence phải verify. Copy creation hoặc long transaction cần separate authorization; không có static-source assumption từ read-only client hay READ_WRITE flag.
- **Downstream impact:** expected counts/keysets/multisets/aggregate reconciliation phải cùng approved context; context loss → capture mới, không ghép current/H/headers/lines của các state khác nhau.

### A02 — Approval đã ghi nhận và implementation gates

- **Approved conditional logical policy:** C2 khi có defensible no-write evidence toàn extraction interval; nếu thiếu thì separately approved verified C5 copy. C3 không được tự chạy; concrete method chưa verified. Bảng tám tiêu chí tại evidence section 10 là technical analysis, không tự cấp operational approval.
- **Evidence available:** Owner-supplied trusted command/flags/V1 đã được direct SELECT tái kiểm chứng; source capability không còn TLS-blocked trên endpoint đã xác minh.
- **Evidence missing:** inventory/control của toàn writer, interval evidence; hoặc copy provenance/consistency/writer exclusion; hoặc approved SERIALIZABLE lock/capacity/failure envelope và execution proof. Target atomicity không thay source consistency.
- **Implementation implications:** context/projection/scope/expected-count measurement provenance phải auditable. Không đủ evidence → WINDOWED_UNVERIFIED và hold normal publication; diagnostic qualified use cần approval riêng.
- **Exact pre-implementation conditions:** Conditional policy đã Approved; chosen window/copy method, scope/operational limits và evidence phải verify. Copy creation hoặc long transaction cần separate authorization; không có static-source assumption từ read-only client hay READ_WRITE flag. Runtime verification chưa hoàn tất; không cấp quyền source writes/schema hoặc install từ logical approval.
- **Recorded Owner decision — APPROVED — Conditional Logical Policy, 2026-11-15:** Chấp thuận conditional consistency policy khi WWI gốc SNAPSHOT OFF và RCSI OFF: controlled static window chỉ khi có defensible no-write evidence trong toàn extraction interval; nếu không thì dùng separately approved verified consistent copy. Không dùng NOLOCK để claim consistency; không tự bật SNAPSHOT/RCSI hoặc chạy long SERIALIZABLE transaction. Không chứng minh consistency thì hold normal publication; concrete method/operational evidence vẫn phải verify.

## A03

- **Problem:** Raw cần durable evidence/replay nhưng MVP không nên có nhiều copies/control paths chưa cần.
- **Constraints:** không SCD2/episode/SK allocation tại Raw; full reload không mất forward evidence hoặc historical publication lineage; raw sensitive data không Git/logs.
- **Options considered:** R1 append-only batch snapshots + manifest; R2 current mirror only; R3 immutable generic envelopes + mirror; R4 event log/snapshot/mirror hybrid.
- **Approved logical design:** immutable source-preserving captures, reconciled publication manifests và compatible consumer pins; R1 là hướng kiến trúc capture, physical tables/views/mirror và retention chưa được duyệt.
- **Rationale:** giữ source fidelity và audit với ít copies hơn; future extraction modes có thể dùng cùng capture interface, incremental policy riêng ở DW-03B.
- **Trade-offs:** repeated full capture tăng storage; view/manifest pinning và retention cần rõ. Physical tables/index/partition/codec/loader vẫn cần review sau approval.
- **Risks:** premature purge phá registry recovery, duplicate H bị collapse, source data lộ trong logs; storage growth do blobs/snapshots.
- **Evidence:** Raw requirements, B1/B2/B6, Identity design; proposal A3 conceptual keys/candidates. Chưa có runtime size/throughput measures.
- **Remaining approval / verification:** Capture/manifest/pin và evidence-preservation principles đã Approved; retention periods, physical schema, access control/capacity và backup/restore details pending implementation-level approval. Không purge referenced evidence.
- **Downstream impact:** staging pin publication, Core registry recovery có evidence, future deltas có base membership explicit; không rewrite layer vì current-only mirror đã overwrite history.

### A03 — Approval đã ghi nhận và implementation gates

- **Approved logical policy:** immutable Raw captures/reconciled manifests/pinned publication IDs, bảo toàn incremental/SCD2 evidence. Physical mirror/view/layout, retention/access/capacity không được chọn từ principle approval.
- **Evidence available:** Stage 2 conceptual identity/lifecycle và retention alternatives; B1/B2/B6 logical constraints và source evidence nhu cầu history/forward preservation.
- **Evidence missing:** storage measurement/capacity, data access/retention classes/periods, recoverable backup/codec plan và reference-protection/pinning enforcement tests.
- **Residual risks / alternatives / trade-offs:** keep-all tăng cost/PII; short retention có thể phá replay/registry/history; reference-aware tiers giảm bytes nhưng cần dependency/restore proof. Mirror-only không đủ audit.
- **Implementation implications:** sealed content immutable; failed/superseded captures retained according to reviewed policy; forward observations không bị full reload ghi đè; không đổi raw locators thành analytical keys.
- **Exact pre-implementation conditions:** Capture/manifest/pin và evidence-preservation principles đã Approved; retention periods, physical schema, access control/capacity và backup/restore details pending implementation-level approval. Không purge referenced evidence. Runtime verification chưa hoàn tất; không cấp quyền source writes/schema hoặc install từ logical approval.
- **Recorded Owner decision — APPROVED — Logical Policy, 2026-11-15:** Chấp thuận immutable Raw captures, reconciled publication manifests và downstream pinned publication identities; bảo toàn evidence cho incremental ingestion và SCD2. Retention periods, physical schema, access control và capacity tiếp tục Pending Implementation-Level Approval.

## A04

- **Problem:** run retry, re-extraction và source snapshot thường bị đồng nhất dẫn tới duplicate/mixed-state data.
- **Constraints:** batch/capture/source snapshot IDs khác execution run/attempt; count identity và occurrence multiplicity phải rõ; source reconnect không giữ old snapshot một cách tự động.
- **Options considered:** một run ID làm toàn bộ batch key; PK upsert/current overwrite; logical capture + batch + execution attempt/chunk + publication identifiers.
- **Recommended option:** tách identities theo A4; exact sealed chunk reuse sau unknown commit; new source observation/context là capture mới. Không dedupe archive bằng payload hash; ordinal chỉ technical sealed-content locator.
- **Rationale:** retries có thể idempotent mà vẫn giữ source evidence thật; trạng thái execution/validation/publication độc lập và auditable.
- **Trade-offs:** thêm metadata/control validation, index/transaction details phải thiết kế; retained chunks/batches cần quản lý.
- **Risks:** mark complete khi seal missing, same chunk ID different content, replay đưa pointer về prior publication, count attempted rows thành source population.
- **Evidence:** Raw metadata requirements; B2/B6, CD-T08/17–19 NOT RUN; proposal A4 failure scenarios và synthetic lineage example.
- **Remaining approval / verification:** Identity/retry/new-context principles đã Approved; durable state/commit-outcome detection, checkpoint/transaction/key formats và recovery proof còn pending. UTC observation metadata/physical encoding không tự được chốt thêm.
- **Downstream impact:** orchestration sau này trigger run không tự certify/publish; source-to-Raw lineage, recovery và downstream generation pinning dùng cùng immutable evidence.

### A04 — Approval đã ghi nhận và implementation gates

- **Approved logical policy:** distinct run/attempt/capture/logical batch/publication identities, compatible sealed replay và new-context/new-capture. Execution state schemas/physical key formats và recovery implementation chưa duyệt.
- **Evidence available:** Stage 2 run/attempt/capture/batch/manifest/publication key table; synthetic crash sequence và seven-scenario publication matrix. Chưa chạy recovery implementation.
- **Evidence missing:** actual durable state/commit-outcome detection, uniqueness/metadata state machine, concurrency/restart/persistence and backup/restore test outcomes.
- **Residual risks / alternatives / trade-offs:** run-only identity hoặc PK overwrite làm mất legitimate occurrences; rich IDs/control audit tăng complexity nhưng không phải lý do cấp source identity giả.
- **Implementation implications:** exact chunk/content bindings, immutable seal and accepted attempt; same request/different content conflict; failed/superseded lineage retained, no blind reload/double publication.
- **Exact pre-implementation conditions:** Identity/retry/new-context principles đã Approved; durable state/commit-outcome detection, checkpoint/transaction/key formats và recovery proof còn pending. UTC observation metadata/physical encoding không tự được chốt thêm. Runtime verification chưa hoàn tất; không cấp quyền source writes/schema hoặc install từ logical approval.
- **Recorded Owner decision — APPROVED — Logical Policy, 2026-11-15:** Chấp thuận tách run, attempt, capture, logical batch và publication identities; retry compatible sealed content không tạo duplicate logical records; extraction từ new source context tạo capture mới. Durable state và recovery evidence bắt buộc trước production use.

## A05 — original PoC-direction approval và pre-physical discussion (lịch sử; current B9 bên dưới)

- **Problem:** datetime2(7) có digit 100 ns có thể mất ở driver/Python/target trước khi Raw lưu.
- **Constraints:** D05 exact preservation approved; B9 physical implementation pending; system/observation/analytical times riêng, không tự timezone conversion hoặc source-key dedupe.
- **Options considered:** P1 fixed-precision text; P2 integer ticks; P3 numeric packed calendar; P4 timestamp+exact residual; P5 native timestamp-only không đáp ứng.
- **Approved PoC candidate:** F2 source-side fixed-seven-digit text trước Python datetime coercion. P1 authoritative Raw physical representation vẫn là proposal để review sau transport/target evidence; không final PostgreSQL type/adapter/encoding/collation approval.
- **Rationale:** audit trực tiếp source digits, giảm dependence vào microsecond datetime path và không tự chốt ticks epoch/tuple semantics.
- **Trade-offs:** text/index rộng hơn scalar ticks; cần parse/format/order tests. Ticks thuận exact comparisons nhưng codec/epoch khác; residual dễ bị timestamp-only queries dùng sai.
- **Risks:** source formatter không đủ scale/length, parse/reformat sau khi mất precision, sentinel carry, collation sorting, timezone/basis conflation. Chưa có driver compatibility proof.
- **Evidence:** primary SQL Server/PostgreSQL/Python docs, existing temporal source evidence và local mathematical V1/V2/ticks checks; proposal A5. Mathematical equality không là database round-trip.
- **Remaining approval / verification:** F2 preferred PoC candidate đã Approved; riêng dependency installation/versions, identities/profiles và physical/runtime scope cần authorization/evidence phù hợp. PostgreSQL datatype/adapter/encoding/collation và B9 chưa approved.
- **Downstream impact:** Raw adapters, dbt staging exact columns, SCD2 interval predicates, registry occurrence evidence, conversion gates và backup codec compatibility.

### A05 — Approval đã ghi nhận và implementation gates

- **Approved PoC direction only:** chọn F2 làm preferred candidate để tiếp tục SQL→pyodbc string→psycopg text parameter verification. F1 V1 vẫn PASS, four zero-fraction fixed-width cases FAIL; full B9/physical representation không được duyệt.
- **Evidence available:** D05 và 9 local groups PASS; latest SQL F1 V1 đúng text/27/ns123456700; F2 14 fixtures PASS, 169 ordered pairs không mismatch, 18 sampled temporal cells round-trip exact; source datetime2(7) và formatter varchar(27) nullable metadata verified. Chi tiết/query tại evidence section 10.
- **Latest evidence / missing:** Resume PoC source14/169/18,PG parameters14/persisted15 qua new backend,ordering169/equality14/ranges5 và12 unit methods PASS; evidence section14. Bounded TEXT/C candidate proof không final physical/adapter selection,least-privilege/full-projection/special-type hoặc production recovery proof. Recorded A05 vẫn PoC Direction Only; B9 Pending Physical Approval.
- **Residual risks / alternatives / trade-offs:** F1 omitted-zero fixed-width failure đã observed; F2 engine subset PASS chưa chứng minh mọi source value/driver/storage path. Text/index/codec và ticks/residual alternatives giữ để review; microsecond projection không authoritative.
- **Implementation implications:** preserve exact value trước driver datetime coercion; metadata datatype/scale/basis separate; candidate COLLATE C chỉ PoC expression, không tự default/index schema.
- **Exact pre-implementation conditions:** F2 preferred PoC candidate đã Approved; riêng dependency installation/versions, identities/profiles và physical/runtime scope cần authorization/evidence phù hợp. PostgreSQL datatype/adapter/encoding/collation và B9 chưa approved. Runtime verification chưa hoàn tất; không cấp quyền source writes/schema hoặc install từ logical approval.
- **Recorded Owner decision — APPROVED — PoC Direction Only, 2026-11-15:** Chấp thuận F2 explicit seven-digit source-side formatting là preferred candidate cho temporal precision PoC. F1 fixed-width zero-fraction FAIL, F2 14/14 SQL fixtures PASS, 169 ordering comparisons và 18/18 actual temporal sample checks chỉ là SQL Server-side evidence. B9 PENDING PHYSICAL APPROVAL; chưa chọn final PostgreSQL datatype, adapter, encoding hoặc collation.

## A06

- **Problem:** extraction/load success hoặc matching aggregate totals không bảo đảm full population, fidelity hoặc published consistency.
- **Constraints:** source context/expected scope khai báo trước; valid Core U không phải raw transport rejection; RawPublished khác Certified KPI/view; không arbitrary quality tolerance/threshold.
- **Options considered:** publish từng table khi loaded; publish toàn source mọi subject areas; dependency-complete immutable publication scopes với atomic target membership.
- **Recommended option:** declared Sales-first dependency scope, sealed capture + completeness/key-set/multiset/type/precision checks + source anomaly disposition; target publication ledger/membership/pointer atomic và consumer pinning. Default hold normal publication nếu consistency/fidelity proof thiếu; qualified diagnostic use cần approval riêng.
- **Rationale:** không mixed header/line/current/H states hoặc false Certified labels; rollback/retry có published boundary rõ mà không phải chờ Inventory analytics.
- **Trade-offs:** candidate bytes được giữ lâu hơn; manifest/concurrency controls và future downstream propagation phải thiết kế. Raw pointer rollback không tự rollback Core/mart đã consume.
- **Risks:** source count ở time khác bị coi exact, hashes/netting che missing keys, quarantine tạo thiếu rows nhưng báo complete, ACK mất gây double application.
- **Evidence:** Source Validation I01–I12, B4/B5/B7; proposal A6 gate/failure matrices; runtime outcomes chưa có.
- **Remaining approval / verification:** Atomic dependency-complete publication/pinning principles đã Approved; exact scopes/severity/qualified-use exceptions/thresholds và physical implementation còn review gates; crash/retry/concurrency/rollback/atomic visibility phải verify trước runtime.
- **Downstream impact:** downstream snapshots/reconciliation và mart certification biết source population/context; raw publication event không tự certify models; DW-03C nhận constraints chứ chưa được triển khai.

### A06 — Approval đã ghi nhận và implementation gates

- **Approved logical policy:** dependency-complete atomic ledger/membership/pointer và compatible downstream pinning; Raw không là Certified Data Mart. Physical transaction/locking/access/gate enforcement và recovery/concurrency phải review/verify trước runtime.
- **Evidence available:** immutable candidate/validated/published manifest definitions, scope/version membership, durable ledger + active pointer, consumer dependency pinning; seven failure outcomes và synthetic ACK-loss example reviewed.
- **Evidence missing:** approved full-capture consistency/fidelity proof; physical target transaction/concurrency/access model, no-partial-visibility/ACK-loss tests, compatible dependency retention/rollback tests và approved gate severity. Trusted source connectivity/interactive metadata subset đã verified, không thay những gates này.
- **Residual risks / alternatives / trade-offs:** table-by-table latest có mixed states; toàn platform scope trì hoãn Sales; fixed dependency scopes cần versioning/retention và consumers thực sự obey pins. Pointer rollback không tự rollback consumed Core/marts.
- **Implementation implications:** same target commit cho publication ledger/membership/pointer, compare expected scope revision, same request/content idempotent; missing full/forward bridge hoặc unpinnable analytical dependency → hold, không bắt đầu incremental strategy ở đây.
- **Exact pre-implementation conditions:** Atomic dependency-complete publication/pinning principles đã Approved; exact scopes/severity/qualified-use exceptions/thresholds và physical implementation còn review gates; crash/retry/concurrency/rollback/atomic visibility phải verify trước runtime. Runtime verification chưa hoàn tất; không cấp quyền source writes/schema hoặc install từ logical approval.
- **Recorded Owner decision — APPROVED — Logical Policy, 2026-11-15:** Chấp thuận dependency-complete atomic publication với coherent ledger/membership/active publication pointer transitions; downstream pin compatible publication identities. Crash/retry, concurrency, rollback và atomic visibility phải verify trước runtime use. Raw publication không đồng nghĩa Certified Data Mart publication.

## Logical-approval boundary trước B9 physical approval (lịch sử)

Owner đã formal approve A01–A06 theo mức trong overview và từng Recorded Owner decision; không còn gate “chờ Owner duyệt sáu logical directions”. B9 vẫn **PENDING PHYSICAL APPROVAL**, các gate thực thi/physical design và numerical certification thresholds vẫn giữ. Backlog tám technical gates và narrow B9 verification handoff tại [Work Plan](wwi-dw-03a-work-plan.md); không tạo sub-decisions được coi approved.

DW-03A **IN_PROGRESS**, DW-03B/C/DW-04 **TODO**, WWI-04/Phase 1 **In Progress**; không final DW-03A acceptance. Instruction milestone chỉ cho cập nhật tài liệu và một documentation-only commit sau QA/staged review; không push, install, tạo tables, database changes hoặc bắt đầu PoC/DW-03B/C.

## B9 — Current Physical Raw Temporal Representation approval

Authority/date: Project Owner task “DW-03A — B9 Physical Approval & Final Design Acceptance Review”,2026-11-15. **Status: APPROVED — Physical Raw Temporal Representation**. Ten approved constraints/exclusions authoritative tại [ADR-SCD-05](../adr/scd-05-exact-temporal-precision.md); approved source scope là relevant datetime2(7) fields của project, không arbitrary new sources hoặc business-effective history.

Evidence: SQL F2 fixtures14/14, source/Python/PG ordering169/169, source period samples18/18, PG parameters14/14/readback15/15,equality14/ranges5/NULL/boundaries/sentinel/adjacency PASS. Current actual test rerun/raw SHA/versions ở evidence section15, earlier failed metadata và successful PoCs giữ nguyên.

Original A05 **Recorded Owner decision** vẫn PoC Direction Only, original Pending B9 statements trong phần lịch sử không current authority. New scoped physical choice là TEXT/C, không ticks hoặc native timestamp làm sole authority. Full DDL/index/retention/access/capacity/publication/crash/performance vẫn separate gates.

Final DW-03A design review đủ mandatory conditions; **DONE — Design** theo conditional acceptance authority sau tests/QA. G07 conceptual evidence/replay/retention protection đủ, implementation-specific approvals explicitly deferred bởi A03/current B9; G01 conditional policy không là verified full extraction. [Work Plan](wwi-dw-03a-work-plan.md) tableG01–G08 là reason/owner/stage/proof/gate disposition; runtime không được tự PASS. WWI-04/Phase1 IN_PROGRESS,B/C/DW-04 TODO; không bắt đầu task tiếp.
