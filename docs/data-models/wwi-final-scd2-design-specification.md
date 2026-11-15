# WWI Final SCD2 Logical Design Specification — DW-02E

**DONE — nghiệm thu ở mức thiết kế theo Owner approval B1–B8 và quyền đóng có điều kiện sau document QA ngày 2026-11-15.** B1–B8 = **Approved — Logical Policy** theo task “Finalize DW-02E / DW-02 — Apply Approved SCD2 Logical Policies”; B9 = **Pending — Physical Implementation**. Baseline Git `2eee549e634a5ad5d57966ecec5cd337a4e6c0a6`; không thay BRD, grains, dimensions hoặc source evidence. Đây là logical specification, không là physical/runtime approval. Runtime: Not implemented yet.

**Current B9 follow-up, 2026-11-15:** Owner đã cấp **Approved — Physical Raw Temporal Representation** tại DW-03A: F2→Python str/None→parameterized psycopg→authoritative TEXT/C comparison,exact27/seven digits/NULL/boundaries/sentinel/100ns; derived timestamps secondary. [ADR-SCD-05](../adr/scd-05-exact-temporal-precision.md) và [B9 backlog row](wwi-dw-02e-work-plan.md) là current authority. B9 Pending/deferred statements trong E1–E5 bên dưới là snapshot DW-02 trước follow-up, không current B9 state. B1–B8 và toàn bộ analytical identity/validity/SCD2 decisions giữ nguyên; full Raw schema/index/retention/runtime/certification gates không tự approved. DW-03A final assessment tách scoped physical/design approval khỏi runtime.

## Nguồn và quy ước trạng thái

**Approved:** [BRD Matrix](../requirements/wwi-business-rules-decision-matrix.md), [KPI Catalog](../../analytics/kpi-definitions/wwi-kpi-candidate-catalog.md), [SCD-01–07 / Classification](wwi-scd-attribute-classification.md), [sáu ADR D01–06](../adr/README.md), [DW-01](wwi-logical-dw-design.md). **Verified source evidence:** [Temporal Assessment](wwi-scd-temporal-assessment.md), [SQL Evidence](wwi-scd-temporal-evidence.md). **Accepted C/D design, cập nhật logical policies B1–B8:** [Identity](wwi-scd-identity-key-design.md), [Lookup](wwi-scd-historical-lookup-design.md), [Forward/Cutover](wwi-scd-forward-cutover-design.md), [21 test specifications](wwi-dw-02cd-assessment.md). Các test IDs CD-Txx dưới đây chỉ cross-reference, tất cả NOT RUN.

Phê duyệt B1–B8 bổ sung logical policy, không thay sáu ADR architecture directions. [Backlog B1–B9](wwi-dw-02e-work-plan.md) ghi scope phê duyệt và từng deferral; [E Assessment](wwi-dw-02e-assessment.md) ghi acceptance. Numeric certification thresholds được Owner cho phép chuyển DW-03, phải duyệt trước Certified publication. Shared unknown vs per-NK inferred, reserved SK values, Type1 current/all-version mode, timezone/day-domain evidence và physical procedures chưa được chọn; đây là gated implementation/correction inputs, không là logical blocker mới.

Bảy khái niệm tách biệt: **natural key** nhận diện entity nguồn; **source occurrence identity** nhận diện evidence row/revision; **analytical episode identity** nhận diện trạng thái phân tích liên tục có evidence; **durable Warehouse SK** là opaque key được registry map tới episode; **system-time** là period nguồn; **observation-time** là cửa sổ pipeline quan sát; **analytical validity** là phạm vi dùng để phân tích theo basis được chứng minh. Published_at là thời điểm công bố đích riêng. Không đồng nhất các khái niệm hoặc tự tạo business-effective history.

## E1 — Decision Traceability Matrix

| Decision ID | Requirement | Affected component | Approved constraint | Evidence | Remaining policy | Status |
| --- | --- | --- | --- | --- | --- | --- |
| BRD-01 | Tách Order/Invoice | Headers, hai Sales facts | Counts từ đúng header, sales từ invoice lines | BRD; DW-01; K01–03 | Publish completeness | Approved, consistent |
| BRD-02 | Dates riêng | dim_date và lookup | OrderDate/InvoiceDate không là source effective timestamp | BRD; Lookup | Day-domain/basis evidence và proof algorithm ở DW-03 | Approved; B3 Approved — Logical Policy |
| BRD-03 | Sales trước thuế | Invoice measures | S05=ExtendedPrice−TaxAmount; S03/S04 riêng | KPI K02 | Precision/tolerance implementation | Approved, consistent |
| BRD-04 | Revenue deferred | Marts | Không Recognized Revenue | BRD; KPI S08 | Không mở lại trong E | Approved exclusion |
| BRD-05 | Source profit optional | Invoice fact/S09 | Không gọi Gross Profit/COGS | K13; BRD | Optional report scope | Approved, consistent |
| BRD-06 | AIV trước thuế | S06/mart daily | S05/S02 cùng population; không AOV | K10; KPI | Thresholds/gate implementation ở DW-03 | Approved; B5 tiered logical approved |
| BRD-07 | Refund/Credit KPI ngoài MVP | Facts/marts | Không tự trừ refund | BRD; S10 | Không mở rộng scope | Approved exclusion |
| BRD-08 | Buyer/Bill-to riêng | Customer role keys | Invoice roles lấy header, không master current | K12; Lookup | Per-role numerical thresholds ở DW-03 | Approved; B4/B5 logical approved |
| BRD-09 | Repeat monthly | Order header/C02 | Distinct OrderID và buyer NK; quý tính lại | K11; DW-01 | Exact reporting eligibility/gates | Approved, consistent |
| BRD-10 | Không payment allocation | Reconciliation | Không join payment theo CustomerID | K03; BRD | Không thêm fact allocation | Approved exclusion |
| BRD-11 | Không daily balance | Inventory current/movement | Current không cumulative historical balance | K07; DW-01 | Same-state publication mechanism ở DW-03 | Approved; B6/B7 logical approved |
| BRD-12 | Không stockout risk | Inventory mart | Không forecast từ zero holding | BRD; I07 | Không mở I07 | Approved exclusion |
| SCD-01 | Customer tracking | dim_customer | Category/Group/Bill-to Type2; credit/hold optional chưa bật | Classification | CustomerName admission/mode và AccountOpenedDate correction scope trước execution | Principle + B1/B7 logical approved; admission unchanged |
| SCD-02 | Product analytical tracking | dim_product | Nguyên tắc hạn chế tracking; D01 chốt cụ thể packaging | Classification; D01 | Type1 correction request scope trước execution | Approved; B7 logical approved |
| SCD-03 | Hybrid history | Identity/cutover | Evidence-based source+forward, không system=business | Temporal; Forward | Exact cutover windows/procedure ở DW-03 | Approved; B6 logical approved |
| SCD-04 | Zero-duration | Raw/audit/lookup | Giữ evidence, không interval dương | SQL C02/C04 | Audit attachment implementation ở DW-03 | Approved; B1 logical approved |
| SCD-05 | Unresolved | Core/mart | Không current/earliest fallback | Lookup; D06 | Physical member/reason encoding ở DW-03 | Approved; B4 logical approved |
| SCD-06 | Exact precision | Registry/lookup | Source exact identity; không day proxy | SQL C03/P03; D05 | Encoding/driver/round-trip B9 | Approved direction |
| SCD-07 | Restatement control | Facts/marts | Không blanket restate | Change Impact; Forward | Correction request approval và execution ở DW-03 | Approved; B7 logical approved |
| D01 / ADR-SCD-01 | Product final set | dim_product | Type2 chỉ UnitPackageID/OuterPackageID/QuantityPerOuter; Type1 chỉ admitted fields | ADR; Classification | Type1 request scope và physical procedure | Accepted Architecture; B7 logical approved |
| D02 / ADR-SCD-02 | Persistent registry | Customer/Product SK | Opaque persistent mapping; không ROW_NUMBER durable SK | ADR; Identity; source duplicate-start | Allocator/backup/storage và execution | Accepted Architecture; B1/B2/B8 logical approved |
| D03 / ADR-SCD-03 | Whole-day consensus | Date-only role lookup | Full relevant day, duy nhất episode identity | ADR; Lookup | Day/basis evidence và coverage algorithm | Accepted Architecture; B3 logical approved |
| D04 / ADR-SCD-04 | Reconciled cutover | Source/current/forward | Không ép nối hoặc mất forward history | ADR; Forward | Exact windows/bridge implementation | Accepted Architecture; B6 logical approved |
| D05 / ADR-SCD-05 | Exact 100 ns | Identity/predicates | Microsecond không là nguồn identity duy nhất | ADR; Precision evidence | Physical mapping B9 | Accepted Architecture |
| D06 / ADR-SCD-06 | Controlled unresolved | Core/certified marts | Core giữ U, I block affected scope; mart gated | ADR; Lookup | Numerical thresholds/member/gate implementation | Accepted Architecture; B4/B5 tiered logical approved |
| L01 | Full+incremental+full reconciliation | Ingestion→warehouse | Không chỉ incremental mà bỏ periodic full checks | DW-01 architecture table | Schedule/chunk/consistency DW-03 | Approved direction |
| L02 | Detection theo nhóm nguồn | Transactions/temporal/holdings | Watermark candidate; history/snapshot; snapshot comparison | DW-01; Source Contracts | Algorithm/tie/delete DW-03 | Approved direction |
| L03 | Independent DML tests | Test environment | WWI gốc read-only | DW-01; CD-T01–21 | Approval/setup/runtime DW-03 | Approved constraint; NOT RUN |
| L04 | Idempotency/rebuild | Registry/facts/marts | No double apply; same accepted mapping | Identity; Forward | Recovery/checkpoint execution ở DW-03 | Approved direction; B2/B7 logical approved |
| L05 | Sales-first | Module dependencies | Sales end-to-end trước expansion | Scope; Roadmap | Subject-area execution tasks | Approved sequencing |
| DW-01 grains | Bốn fact grains | InvoiceLineID/OrderLineID/StockItemTransactionID/current StockItemID | Không thêm fact thứ năm; headers là intermediates | Dictionary/Mapping DW-01 | Physical schema DW-03 | Accepted logical design |
| DW-01 bus/dimensions | Bốn conformed dimensions | Date, Customer, Product, MovementType | Buyer/Bill-to role-playing, no fact-to-fact fan-out | DW-01 bus/diagrams | Reference contracts và SCD lookup | Accepted logical design |

Kxx ở SQL KPI đã nghiệm thu; Cxx/Pxx ở temporal SQL. E1 không tìm thấy mâu thuẫn architecture/BRD trong baseline C/D. Bảng reason candidates của Lookup ghép precision uncertainty cùng invalid inputs; phần R/U/I phía sau đã phân biệt thiếu proof (U) với proven corruption/conflict (I). E4 chuẩn hóa lại taxonomy để tránh triển khai reason code sai; không phải thay constraint C/D hoặc sửa source findings. Reason encoding vẫn Pending Approval.

## E2 — Identity / Validity / Registry Invariants

| Invariant / definition | Required evidence | Failure condition | Expected handling | Test | Approval status |
| --- | --- | --- | --- | --- | --- |
| NK = source instance/entity + CustomerID hoặc StockItemID | Source PK/provenance, source continuity | Reuse mã sau delete/reset không rõ entity | Giữ Ambiguous khi thiếu evidence, không tự tạo incarnation hoặc nối history | T02/T15 | B8 Approved — Logical Policy; detection deferred |
| Occurrence ≠ episode; full source identity exact, không start-only | Raw origin/current/archive/batch, periods/payload lineage | Duplicate-start, indistinguishable conflicting occurrences | Audit occurrence; identity conflict block scope, không MAX/ordinal | T01/T07/T11 | D02/B1 approved; physical discriminator deferred |
| Episode identity độc lập mutable boundaries | Durable registry mapping và proof continuity | Boundary correction bị cấp ID mới tùy thời gian/row order | Preserve ID/SK khi unique same episode; revision lưu riêng | T08/T14/T18 | D02/B1 Approved — Logical Policy |
| Approved Type2 vector quyết định analytical state | Customer 3 IDs; Product 3 packaging; tracking-policy version | Editor/Tags/optional credit tự trigger Type2 | Audit only; không auto-version; không đổi transaction measures | T03–06 | SCD-01/D01 approved |
| Accepted episode→opaque SK mapping không đổi nghĩa | Registry assignments/supersession/backup evidence | Same episode nhiều SK hoặc SK tái dùng khác nghĩa | Chặn candidate, restore/reconcile; không ROW_NUMBER durable key | T08/T11/T19 | D02; allocator/schema deferred |
| Boundary-only preservation không che split/merge | Same NK/incarnation/vector/basis + unique occurrence-to-episode lineage | Revised interval thuộc nhiều episodes hoặc thay analytical identity | Replacement identities và explicit supersession, không arbitrary survivor | T14 | B1 Approved — Logical Policy |
| Historical fact RI gắn mapping generation | Fact source PK/role/NK, SK and registry revision | Dangling FK, mixed generations, superseded ID dùng sai revision | Block affected publication, giữ prior compatible state; audit remap | T13/T17/T18 | D02/D06/B7 approved; execution deferred |
| Times riêng: system/observation/analytical/publication | Source periods, observation window, history_basis, published state | observed_at gán thành business effective; history_basis mất | Unresolved validity, không invent business T | T09/T16/T20 | SCD-03/D04 approved |
| Positive interval half-open `[from,to)` | Exact endpoints và approved validity basis | Negative duration, overlap hoặc precision loss làm predicates sai | Zero-duration giữ audit, không positive match; invalid overlap block | T07/T10/T13 | SCD-04/D05 approved; encoding pending |
| Gap detection gồm internal và leading coverage | Per-NK ordered interval set, prior max end, event domain | Internal gaps hoặc event trước first version bị che bằng fallback | U coverage reason; không earliest/current | T12/T13 | D03/SCD-05 approved |
| Full-day lookup trả một episode identity cho toàn D | Accepted interval union phủ D, same episode ID, no conflicting interval | Endpoints match nhưng giữa ngày gap/sequential episodes | U nếu thiếu proof/date ambiguity; I nếu overlap/conflicting identities | T12/T13 | D03/B3 approved; concrete domain/basis evidence gate |
| Exact source periods 100 ns | Lossless source representation và predicate tests | Conversion/collision không bảo toàn identity | U khi chưa đủ proof; I khi đã chứng minh corruption/conflict; no reduced-time fallback | T10/T11 | D05; B9 deferred physical |
| Replay và controlled rebuild giữ registry/evidence | Registry+revisions+forward audit+publication maps tương thích | Forward history mất, registry restore thiếu, SK list không đủ | Hold candidate; không claim equivalence/stability; restore hoặc approved generation remap | T08/T18/T19 | D02/D04/B2 approved; restore tests NOT RUN |
| Full population/measure conservation | Header/line/movement grain, source scope/run and R/U/I counts | Duplicate/missing facts hoặc KPI numerator/denominator khác scope | Block incomplete/invalid scope; core giữ U; reconcile source/audit | T13/T17/T21 | BRD/D06/B4/B5 approved; numeric thresholds pending |

Txx = CD-Txx trong bộ test đã có. Không có runtime evidence cho các invariants đích; evidence nguồn hiện tại không chứng minh algorithm đã đúng.

### Episode / registry — B1/B2/B8 Approved — Logical Policy

Registry giữ episode identity được cấp một lần trong persistent registry, map nhiều source revisions về cùng episode chỉ khi exact evidence chứng minh contiguous compatible coverage. Boundary-only correction giữ identity/SK nếu không đổi NK/incarnation/vector và không split/merge; audit validity revision và re-resolve affected requests trước publication. Không dùng payload hash, ValidFrom hoặc row ordinal làm durable identity.

**Split:** giữ old episode/SK cho các publication cũ, tạo replacement episode IDs/SKs cho các positive segments của candidate revision và explicit old→new interval map. Không mặc định “segment đầu giữ old SK”. **Merge:** chỉ contiguous compatible episodes được xem xét; tạo replacement identity với lineage của old episodes, không merge noncontiguous A→B→A dù values bằng nhau. Không đổi nghĩa keys đang referenced; Supersession/remap đi qua controlled correction request có audit, reconciliation và rollback trước publication. Không áp survivor alternative; split/merge bắt buộc replacement theo B1.

Thiếu continuity proof giữ Ambiguous ở identity layer và U cho otherwise-valid fact context; không cấp identity mới để tự sửa uncertainty. Proven conflicting accepted identities/intervals → I, block affected publication. Thiếu history/basis không có corruption → U, không tự tạo timeline. Recovery có backup đầy đủ: restore registry, revision/supersession, source+forward evidence và publication policies như một compatible set rồi reconcile. Không có backup/evidence đủ: không claim stable SK; giữ recovery candidate blocked, Owner quyết định restore thêm evidence hoặc phê duyệt riêng generation/remap plan không được mặc định equivalent. Không cascade/delete historical facts.

Delete/reinsert theo B8: vắng trong incremental batch không chứng minh delete. Vắng trong consistent full snapshot chỉ là delete candidate, phải có completeness/consistency và entity evidence trước retirement. Confirmed delete giữ history/audit và historical facts. Reappearance phải phân biệt reactivation cùng entity với incarnation mới; chỉ tạo incarnation mới khi có evidence. Thiếu evidence giữ **Ambiguous** ở identity layer, lookup U cho context chưa chứng minh được; không tự cấp episode/incarnation giả, nối history hoặc reuse SK. Nếu có proven identity conflict thì I và block scope. Detection algorithm/evidence format chuyển DW-03 trước runtime.

## E3 — 14 State Transition Review Cases

Không tạo test IDs mới; đây là projection review của CD-T01–21 theo B1–B8 Approved — Logical Policy. Preconditions/physical mechanisms/correction requests vẫn phải đáp ứng gate trước execution; tất cả tests NOT RUN.

| Scenario / test | Precondition | Input | Expected episode state | SK behavior | Fact impact | Mart impact | Recovery | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Initial baseline / T01 | Permitted history/current | Full input | Source-backed candidates từ approved vector, U khi validity thiếu | Registry once per accepted episode | Resolve 7 roles, no fabricated old history | Build from complete core only | Restore prior/empty publication | Counts/period/lineage gates |
| New NK / T02 | Complete input, new incarnation proven | INSERT | New candidate episode | New opaque mapping, không row ordinal | New/missing-ref requests | New groups after gates | Replay same mapping | NK/reference identity |
| No change / T05/T08 | Existing registry, same vector | No-op/editor-only | Same episode, audit observation | Reuse SK | No artificial rekey | No double apply | Idempotent retry | Equality/lineage |
| Type1 / T03 | Admitted field; correction scope approved trước execution | Name/classification correction | No Type2 episode | Same meaning/SK | Usually keys unchanged | Label/current grouping refresh theo chosen mode | Audit Type1 revision | B7 correction-scope approval |
| Type2 / T04/T06 | Approved vector/basis | Customer IDs hoặc Product packaging change | New candidate episode theo evidence | Registry new episode key khi evidence đủ | Only affected interval/roles, no master invoice reattribution | Scoped old/new groups | Candidate rollback/replay | Single-match + rekey approval |
| Between-batch changes / T09 | Two observations | A→C, unknown B | Only evidenced history, uncertainty retained | No invented intermediate key | U cho uncovered contexts | Disclose/hold affected breakdown | Preserve forward audit | No fake business T |
| Late history / T14 | Existing published mapping | New old evidence | Candidate revised timeline | Preserve identity or supersession plan | Affected requests remap only | Restate affected groups after approval | Keep previous revision | Source/evidence precedence |
| Source correction / T21/T14 | Header/line or dimension evidence sửa | Date/role/value corrected | Episode chỉ đổi nếu dimension evidence thật sự yêu cầu | Mapping revision independent source-fact update | Header-only propagation; source roles giữ đúng | Recompute old/new group, no fan-out | Replay same correction request | Source lineage + B7 |
| Delete / T15 | Complete evidence, not partial scan | Confirmed delete | Full consistent absence chỉ delete candidate; confirmed delete mới retire, retain history | No historical key reuse | No cascade historical facts | Current scope review | Restore audit/registry | Delete proof |
| Delete/reinsert / T15 | Deleted NK returns | Same code | Reactivation hoặc new incarnation chỉ khi evidence đủ; thiếu proof → Ambiguous/U | Never assign old SK to different meaning | New requests evaluated, old facts retained | Separate uncertainty from historic group | Incarnation decision audit | B8 logical approved; incarnation evidence gate |
| Retry/replay / T08/T11 | Known attempts/registry state | Repeated input | Same accepted episode | Stable mapped SK | No duplicated fact rows/measures | No delta applied twice | Reconcile accepted vs candidate | Registry integrity |
| Failed batch / T17 | Compatible published state | Fail mid-dimension/fact/mart | Failed candidate, old revision intact | Reservations cannot change meaning | No mixed-generation FKs | No partial certified result | Restore/resume coherent state | Atomic visibility requirement |
| Rebuild / T18/T19 | Retained evidence/maps or explicit loss | Full reload | Reconstruct only evidenced history | Stable with mappings; otherwise no stability claim | Remap only approved generation | Reconcile totals and coverage | Backup compatibility audit | B2; lost evidence stop rule |
| Split/merge / T14 | Identity change identified | Corrected intervals | Supersession candidate, no arbitrary survivor | Replacement keys bắt buộc, old keys retained for old publication | Old→new scoped role mapping | Scoped restatement request | Roll back candidate to prior revision | B1/B7 approved; correction execution gate |

### Hybrid and propagation review — B6/B7 Approved — Logical Policy

Source-backed, source current và observation-backed evidence giữ origin/basis riêng; một change xuất hiện ở hai streams chỉ map một analytical episode sau proof, không dedupe chỉ bằng rounded timestamp/hash. Bridge phải reconcile approved vector, occurrence identity, temporal coverage và compatible registry generation cho từng NK; equal endpoint values không chứng minh không có intermediate changes. Không bridge được thì unverified interval/U; conflicting accepted intervals là I. Full reload phải giữ forward audit; source restore snapshot một mình không phục hồi forward history đã mất.

Late correction/backfill ghi exact affected NK/incarnation/role/interval, old/new episode/SK, reporting periods, policy/publication revisions và source lineage. Version creation không tự reassign mọi historical FK; rekey không tự sửa source fact; mart restatement chỉ sau approved affected-scope plan. Buyer/Bill-to lấy Invoices roles riêng, Customer master BillTo change không rewrite source roles. Current Product refresh theo cùng holdings published_state_id; observed_at nguồn và published_at đích khác nhau; không daily inventory history.

**B7 correction contract — Approved — Logical Policy:** mỗi request phải khai báo NK/incarnation, admitted attributes, roles, affected intervals, selected versions (current-only hoặc explicitly enumerated retained versions), old/new groups và reporting periods. Audit before/after, reconciliation và rollback plan là bắt buộc trước apply; không silently đổi historical fact SKs. Không mặc định current-only hoặc all-version overwrite: mode/field admission phải được Owner review trong correction design/request trước execution, thuộc DW-03C handoff. CustomerName vẫn là candidate theo classification; không mở rộng admitted fields. AccountOpenedDate correction phải auditable và không tự tạo SCD2 episode hoặc KPI mới. Type1 label refresh khác Type2 creation, fact rekey và source correction; source measures/roles không bị thay bởi master correction.

## E4 — Publication & Quality Gates: B4/B5 Approved — Logical Policy

**R:** một accepted episode/version theo role: exact-time hoặc whole-day proof cho historical requests; same-published-state proof cho current inventory Product. **U:** thiếu evidence nhưng chưa có integrity violation. **I:** invalid data/identity/interval conflict hoặc multi-match integrity đã chứng minh. Unresolved reason families: missing source reference; insufficient history; date-only ambiguity; missing/incomplete observation evidence cho validity; precision/identity uncertainty. Đây chưa là reserved codes hoặc SK values chính thức.

Precision/identity uncertainty chỉ vì thiếu proof → U; đã chứng minh lossy conversion/conflicting identity → I. Extract batch incomplete làm **source population chưa đầy đủ** phải hold complete-publication claim, không chỉ gắn U rồi coi input complete. Thiếu observation evidence để xác định dimension history với fact population đã complete có thể là U. Unknown member không là successful historical match.

### Core và publication boundary — logical constraints approved, physical unit deferred

Đề xuất consistency unit là declared source scope + required parent/header inputs + affected downstream mart/role/period dependencies cùng publication revision. Invalid scope được xác định bằng dependency closure; không bỏ I khỏi mẫu để publish số “đẹp”, cũng không block các independent validated scopes vô cớ. Nếu chưa xác định impact closure, hold tối thiểu toàn parent batch/subject slice có thể bị ảnh hưởng cho tới làm rõ; đây là conservative design refinement; exact dependency closure/physical batch/transaction phải review ở DW-03 trước publication, không là mechanism đã duyệt hoặc triển khai.

Core giữ facts R+U với source NK/PK/role/reason/provenance và exact source measures; B4 bắt buộc giữ source NK/role/reason cho re-resolution; shared unknown hoặc per-NK inferred là physical options chưa chọn, không phải hai publication policies cạnh tranh. I giữ raw/audit và chặn affected publication. Partition fact rows không trùng: bất kỳ required role I thì fact I; còn lại bất kỳ required role U thì fact U; đủ required roles R thì fact R. `Expected source rows = R + U + I` theo grain/scope đã validate; nếu chưa đủ extract không được claim equality/completeness. No silent fallback, no line/header count fan-out. Re-resolution mở request có source PK/role/evidence/policy revision, tạo candidate old→new mapping diff; chỉ publish cùng dimension/fact/mart-compatible revision. Rollback giữ prior compatible publication; failure/retry không nhân measures hoặc đổi nghĩa SK. Atomic **visibility** là yêu cầu, không khẳng định một cross-system database transaction đã tồn tại.

### Quality metrics — kiểm cả row và value coverage, chưa có numeric thresholds

| Metric | Definition / population | Guard / reason |
| --- | --- | --- |
| Overall source population completeness | Source PK key-set missing/extra/duplicate và counts source→raw→core cùng declared scope/run; ratio matched expected PK / expected source PK nếu denominator đã xác minh | Count bằng nhau chưa chứng minh key-set bằng nhau; expected unknown/incomplete → not evaluable, không 100% |
| Resolved dimension coverage | R-role rows / toàn applicable source population cho role, U vẫn trong mẫu, I báo riêng và block scope | Không distinct SK thay source entity; mẫu 0 → N/A; không loại U để tăng ratio |
| Unresolved amount/quantity | Theo reason/role: signed sum, positive/negative sums, absolute sum, row count và NULL/zero counts của U | Chống cancellation; role overlap không cộng đôi enterprise U. Fact-level U là union fact IDs, không SUM reason populations |
| Affected KPI population | Distinct eligible source PK/NK và denominator của KPI có U/I trong dependencies thực sự | C01 distinct BuyerID khác SCD SK; S02 counts headers không lines |
| Affected KPI value coverage | Với additive m: resolved applicable absolute magnitude / total applicable absolute magnitude là diagnostic, kèm signed source totals; non-additive KPI báo covered numerator/denominator riêng | Không đổi KPI formula bằng absolute sum; denominator 0 → N/A, không auto Certified; không tính coverage bằng cách cộng/average ratios |
| Invalid matching count | Distinct source fact/role requests có multi-match, invalid key/period/identity, kèm affected scope | Must block integrity-invalid theo D06; không transform thành unknown để pass |
| Reconciliation differences | Key-set/count, per-key/group amount/tax/qty và aggregate diffs cùng grain/population/time; S03=S04+S05, S06 dùng same header population | Không dùng totals netting làm bằng chứng duy nhất; tolerance/precision formatting cần approval |

### KPI dependencies và Tiered Certification được duyệt

| KPI/view | Tiered enterprise khả năng công bố nếu other gates đạt | Dimension-dependent hạn chế |
| --- | --- | --- |
| S01/S02; C01/C02 | Counts/repeat từ complete headers và valid source NK/date có thể evaluated không cần historical dimension SK | Không gắn nhãn historical category/group/product breakdown đầy đủ khi thiếu history; Product filter không đổi header KPI tự ý |
| S03/S04/S05/S06, optional S09 | Line source amounts/profit + complete invoice headers, same population; historical dimension U không tự làm amount sai | Product/category/packaging historical segments cần role coverage. S09 vẫn source profit, không Gross Profit |
| C03/C04 by source Buyer/Bill-to ID | NK grouping từ invoice header có thể evaluated riêng từng role, nếu source identities hợp lệ | NK-only grouping không là historical customer-category grouping; không cộng hai roles |
| I01/I02/I03/I05 | Source signed movement/type/date/item-ID totals khi type contract/classification và inputs hợp lệ | Historical packaging descriptors cần Product lookup; không quy đổi quantity bằng master current; không daily balance |
| I04 | Current source holdings total cùng validated state có thể evaluated | Product descriptor attribution cần same-state mapping; không publish partial/mixed states |
| C05 | Chỉ khi current dim_customer population/NK/category đúng và complete | Không lấy published historical version rows hoặc joined fact population để đếm current customer |
| S07/S08/S10/I06/I07 | Ngoài MVP/deferred/unsupported giữ nguyên | Không chứng nhận KPI chưa được scope/source hỗ trợ |

**Phương án A — Strict certification:** giữ để trace phương án đã xem xét, không được chọn làm policy MVP. Proposed 100% required role coverage không phải threshold chính thức, không được dùng làm default.

**Phương án B — Tiered Certification: Approved — Logical Policy, B5.** Chứng nhận từng KPI/view theo dependency, scope/filter và period; enterprise/NK-source metrics có thể Certified riêng khi population, integrity, reconciliation và quality evidence đầy đủ. Historical breakdown thiếu coverage requirements là **Uncertified**, không gắn nhãn Certified toàn mart/dashboard rồi ngầm bao phủ breakdown đó. Đánh giá cả **row coverage và measure/value coverage**, kể cả signed/absolute/zero/NULL diagnostics; không dùng amount netting hoặc bỏ U để tăng tỷ lệ.

Lookup **Resolved/Unresolved/Invalid** và certification **Uncertified/Certified** là hai axes khác nhau. Identity **Ambiguous** theo B8 không là entity mới; có thể dẫn U. R không tự Certified; KPI/view chưa có thresholds/gate evidence vẫn Uncertified. I chặn publication affected scope, không được relabel U để vượt gate; unaffected independently validated scopes được đánh giá riêng. Chưa có runtime KPI/mart Certified.

**Deferral B5 do Owner cho phép ngày 2026-11-15:** numerical row/value thresholds và reconciliation tolerances tiếp tục Pending Approval tại DW-03, bắt buộc Owner duyệt trước bất kỳ Certified publication nào. Owner là approval authority; DW-03 designer đề xuất thresholds theo measured evidence, ghi metric/dependency/denominator/scope/period/policy version và tests. Không tự đặt 100%, tolerance hoặc coverage exemption để pass. B9 physical precision tiếp tục Pending — Physical Implementation; 100 ns logical invariant đã duyệt không bị hoãn.

## E5 — Acceptance và handoff boundary

B1–B8 đã Approved — Logical Policy; không còn blocker logical-policy approval trong phạm vi DW-02. Những đề xuất cũ về shared unknown, Type1 all-version default hoặc survivor split không được tự nâng thành Approved: member encoding/mode chuyển gated DW-03; survivor không áp dụng theo B1. B9 giữ Pending — Physical Implementation. Chi tiết day domain/basis phải có proof; thiếu proof vẫn U, không buộc invent timeline để nghiệm thu thiết kế.

[Assessment](wwi-dw-02e-assessment.md) ghi design acceptance theo quyền đóng có điều kiện trong task Owner; [work plan/backlog](wwi-dw-02e-work-plan.md) ghi approval provenance, deferral owner/stage/gates. Runtime CD-T01–21 NOT RUN, physical/database/pipeline Not Started. WWI-04 IN_PROGRESS, Phase 1 In Progress; DW-03/DW-04 TODO. Handoff chỉ planning, không bắt đầu task tiếp theo.
