# WWI DW-03B — Incremental Decision Register

**Stage 2, 2026-11-16. INC-01–INC-06: APPROVED — Logical Policy.** Authority: Project Owner instruction **“DW-03B Stage 2 — Owner Logical Approval & Design Finalization”**. Approval được cấp trực tiếp cho sáu logical policies cùng giới hạn dưới đây; không suy từ QA, không phê duyệt runtime/physical algorithm. Accepted DW-01/DW-02/A01–A06/B1–B9 giữ nguyên.

Decision trail: Stage 1 đề xuất cả sáu decisions → Owner cấp Logical Policy approval trong Stage 2 → final design assessment có điều kiện; original alternatives/evidence được giữ để trace. Correctness objective đã duyệt là **Current-State Convergence** so với verified consistent source state, không full CDC hoặc complete intermediate event history.

[Proposal](wwi-dw-03b-incremental-design-proposal.md) giữ chi tiết kỹ thuật; [Work plan](wwi-dw-03b-work-plan.md) giữ E01–E10; [Assessment](wwi-dw-03b-assessment.md) giữ readiness. Không tạo sáu ADR có chức năng trùng lặp.

| Decision | Logical policy đã phê duyệt | Gate kỹ thuật / giới hạn còn mở | Trạng thái |
| --- | --- | --- | --- |
| INC-01 | Source-specific detection, current/H occurrence preservation, full holdings snapshot và full-state reconciliation; mục tiêu Current-State Convergence | W có điều kiện; full-state comparison vẫn đọc full source; không complete CDC/event guarantee | APPROVED — Logical Policy |
| INC-02 | Inclusive candidate boundaries, stable pagination, watermark không là completeness proof; progress gắn durable publication | Exact algorithm/U selection/physical checkpoint format chưa duyệt | APPROVED — Logical Policy |
| INC-03 | Evidence-based lookback, compatible sealed replay khác re-extraction, periodic full reconciliation | Duration/cadence phải measured/tested và Owner approve trước scheduling | APPROVED — Logical Policy |
| INC-04 | Current/H riêng, exact periods/zero-duration/multiplicity/original evidence/generation-lineage; giữ B9 | Period filters chỉ conditional optimization; retention/late-commit proof, không business-effective inference | APPROVED — Logical Policy |
| INC-05 | Complete consistent compatible snapshots, key+canonical payload, H multiset; absence chỉ candidate; B8 giữ nguyên | Confirmation/retirement/retraction/reappearance evidence và controlled action policy | APPROVED — Logical Policy |
| INC-06 | Progress ACK bind durable reconciled accepted publication, distinct identities/sealed replay/atomic pins/predecessor/content/no regression | Physical storage/locking/concurrency/failure recovery phải review/test trước use | APPROVED — Logical Policy |

## INC-01 — Per-source Change Detection

- **Vấn đề:** không có complete CDC được phép; source types và change fields khác nhau. PK cao không bắt UPDATE/DELETE.
- **Evidence:** E02/E03; 9 current tables, 2 H; 6 ordinary transaction/header/line tables có LEW trùng; Holdings cũng có LEW nhưng chỉ 2 distinct/227 rows; masters không LEW. Q11 chưa chứng minh write behavior.
- **Alternatives:** LEW-only tất cả; PK-only append; full snapshots tất cả; phân nhóm W/T/S với recon. CDC/CT chỉ capability alternative ngoài authorization, không đề xuất bật.
- **Approved logical policy:** Source-specific W/T/S cùng full-state reconciliation là logical direction đã duyệt: ordinary transaction windows có điều kiện; temporal current/H giữ occurrence evidence; Holdings full current-state snapshot comparison. Current-State Convergence theo verified consistent boundary; không bảo đảm complete intermediate events. Full T/full comparison là reference correctness path ở WWI scale, không thuật toán tối ưu đã approve.
- **Trade-offs:** đọc nhiều hơn đổi lấy state coverage dễ kiểm; full recon có chi phí cần đo, không cam kết hiệu năng từ baseline size.
- **Correctness limitations:** state convergence không là complete logical event history. Mọi intermediate change ở ordinary tables có thể không còn observable.
- **Implementation dependencies:** G01/G02/G06/G07, source projections, standalone SQL sandbox approval, reference contracts, policy versions.
- **Remaining technical approval / proof:** Concrete W algorithm/write-path/scan cost và source method/scope proof trước runtime; assurance objective/detection directions không còn Pending. Runtime cadence/test-environment provisioning approvals riêng.
- **Acceptance criteria:** đủ 11 populations, PK/H-no-PK rõ; INSERT/UPDATE/DELETE candidates và full recon có evidence; writable sandbox tests chứng minh limits; không LEW/PK-only CDC claim.
- **Status:** APPROVED — Logical Policy.

## INC-02 — Watermark / Tie-breaker

- **Vấn đề:** equal timestamp, old-key update, late commit và mutable reads có thể làm tuple cursor bỏ sót.
- **Evidence:** E03 Q11 có timestamp duplicates ở 7 LEW tables; E07 temporal periods trùng; E08 A02 source consistency chưa runtime verified. Synthetic counterexample proposal section 3 không là actual WWI event.
- **Alternatives:** timestamp-only >H; timestamp+PK làm global checkpoint; inclusive replay window + page cursor; snapshot/full comparison. Exact algorithm vẫn chưa được phê duyệt.
- **Approved logical policy:** Inclusive candidate boundaries và stable pagination khi áp dụng; tuple (LEW,PK) chỉ tie-break/page cursor, không bằng chứng bắt đủ source changes. Không silently bỏ equal-time hoặc old-key updates; watermark là progress candidate, acknowledged checkpoint chỉ sau durable accepted publication. Exact [L,U]/U selection và physical format vẫn technical validation.
- **Trade-offs:** equality replay đọc trùng có chủ đích, cần idempotency/content evidence; fixed bound không bảo đảm consistency.
- **Correctness limitations:** tuple chỉ phân trang current PK-unique population; không phát hiện later update PK cũ/LEW không tiến, backdate hoặc delete. Không global temporal cursor trên H.
- **Implementation dependencies:** source timestamp write-path tests, U selection evidence, G01 coherent context, checkpoint/publication binding INC-06, exact types/adapters.
- **Remaining technical approval / proof:** Exact boundary implementation/upper-bound selection/NULL cases/cursor format phải technical validation; inclusivity/progress policy đã Approved. Chưa chọn physical SQL/index hoặc maximum timestamp làm safe frontier.
- **Acceptance criteria:** same-time keys qua pages đầy đủ; old-key/same-time và late-commit negative tests không false PASS; no checkpoint advance trước publication; NULL/U<H/context-loss cases explicit.
- **Status:** APPROVED — Logical Policy.

## INC-03 — Lookback / Replay

- **Vấn đề:** late/backdated updates và outage có thể nằm sau hoặc ngoài window; requery không là replay cùng capture.
- **Evidence:** E03 chỉ historical timestamp distribution, chưa measured lag/commit/write paths; E08 A04 đã tách sealed replay và new source context.
- **Alternatives:** không replay; arbitrary fixed lookback; measured bounded replay + full recon; full comparison mỗi observation.
- **Approved logical policy:** Evidence-based lookback + compatible sealed replay + periodic full reconciliation. Finite lookback không bảo đảm arbitrary backdating; source re-extraction là capture mới, khác replay retained content. Duration/cadence/scheduling cần measurement/test evidence và explicit Owner approval.
- **Trade-offs:** tăng IO/storage, replay overlap; windows nhỏ bỏ late changes, lớn chưa chắc bắt backdated changes.
- **Correctness limitations:** hữu hạn lookback không bảo đảm completeness với timestamps không đáng tin; polling không chứng minh true commit delay. Full recon bắt final state, không events đã mất.
- **Implementation dependencies:** INC-01/02/06; sandbox ground truth begin/commit/source timestamps, outages, cost measurements, G07 retained content.
- **Remaining technical approval / proof:** Measurement/test plan execution, numeric duration/cadence/trigger/severity và runtime scheduling phải Owner approve; không tự đặt defaults. Assurance giới hạn và sealed replay direction đã Approved.
- **Acceptance criteria:** replay/repeated windows không duplicate logical application; correction ngoài window được full recon tìm; stale replay không regress pointer; new context có new capture; all forward evidence retained khi reload.
- **Status:** APPROVED — Logical Policy.

## INC-04 — Temporal Incremental Capture

- **Vấn đề:** current/H movement, zero-duration, duplicate starts, long transactions/retention làm period-only extraction thiếu/nhầm evidence.
- **Evidence:** E03/E07 Customers 663+51=714 so ALL713, same-start identity không unique; StockItems 227+444=671; E09 B9 approved scoped exact path. Engine references E10, local cleanup state Unverified.
- **Alternatives:** FOR SYSTEM_TIME ALL; current-only; period-filtered H/current; full direct current/H comparison trước tối ưu.
- **Approved logical policy:** Tách current và physical H populations; giữ exact temporal boundaries, zero-duration, multiplicity, original evidence, generation và lineage. Period filter chỉ conditional optimization, xét late commit/retention. B9 F2→str/None→parameterized psycopg→TEXT/C giữ nguyên; không business-effective inference/analytical episodes trong Raw.
- **Trade-offs:** đọc history lặp/cost của special payload; không có enforced H occurrence key nên lineage ambiguity có thể tồn tại.
- **Correctness limitations:** periods là transaction-begin system-time, không commit sequence/business-time; source retention loss không phục hồi bằng recon; identical H tuples chỉ đối soát multiplicity, không invent row identity.
- **Implementation dependencies:** A01/A02, B1/B2/B6/B9, G01–G07; metadata generation/retention/versioning, serialization full fields, separately approved maintenance-test scope.
- **Remaining technical approval / proof:** Optimization/projection/canonicalization/retention-generation evidence và cleanup-gap recovery proof trước runtime; không reopen B9/analytical validity hoặc authorize source maintenance.
- **Acceptance criteria:** direct zero-duration coverage/multiplicity, current→H no double episode, late-visible period test, history gap/generation hold, no forward evidence loss, exact100ns/canonical equality, compatible hybrid bridge.
- **Status:** APPROVED — Logical Policy.

## INC-05 — Snapshot / Delete Detection

- **Vấn đề:** Holdings LEW yếu, missing key từ partial extraction dễ dẫn mass false delete; source absence không đủ retirement/incarnation proof.
- **Evidence:** E03 227 holdings/2 LEW; E07 B8 và E06 Change Impact yêu cầu delete candidate/confirmed distinction; E08 G01 consistency.
- **Alternatives:** LEW-only; key-only snapshot; full row direct comparison; canonical hash-assisted row compare; absence→hard delete (không khuyến nghị).
- **Approved logical policy:** So complete, consistent, compatible snapshots bằng key-set và exact canonical payload; physical H dùng multiset. Partial/failed/inconsistent snapshot không tạo valid delete evidence. Absence chỉ delete candidate; confirmation/retirement/retraction/reappearance cần explicit evidence/controlled policy, giữ B8 ambiguity.
- **Trade-offs:** full scans và payload comparison thay vì chỉ keys; conditional confirmation workflow chậm hơn speculative deletion.
- **Correctness limitations:** two snapshots bỏ transient changes; hash equality không uniqueness/event identity; repeat absence không tự là business deletion. Permission/filter/source-generation drift có thể giả absence.
- **Implementation dependencies:** INC-01/04/06, G01/G06/G07, compatible Product current state, Owner-approved confirmation/action policy, B8 identity evidence.
- **Remaining technical approval / proof:** Concrete confirmation standard, controlled retirement/retraction action, reappearance/incarnation proof và physical tombstone/digest encoding; snapshot/candidate-only policy đã Approved, không auto business delete.
- **Acceptance criteria:** partial snapshot không tạo candidate; full valid snapshot chỉ candidate; changed field cùng LEW vẫn được tìm; NULL/rỗng/Unicode/precision distinctions giữ; reappearance Ambiguous nếu thiếu proof; no cascade/history loss.
- **Status:** APPROVED — Logical Policy.

## INC-06 — Checkpoint / Recovery

- **Vấn đề:** load success, recon success hoặc orchestration ACK không là publication durability; retries/stale bases có thể skip/double apply.
- **Evidence:** E08 A04/A06 logical identities/atomic ledger+membership+pointer/pins đã duyệt; G08 runtime chưa test. Không có implemented checkpoint table.
- **Alternatives:** advance khi extraction complete; advance khi load complete; separate metadata write không bind publication; effective checkpoint bind coherent accepted publication và durable outcome read-back.
- **Approved logical policy:** Bind acknowledged progress với durable reconciled accepted publication. Giữ run/attempt/capture/batch/publication identities, sealed replay, atomic membership, predecessor/content validation, downstream pins/no pointer regression; examine durable evidence trước retry. Không advance chỉ vì extract/load success; physical locking/storage/concurrency/recovery vẫn gate.
- **Trade-offs:** thêm control lineage/state reads và concurrency checks, cần durable proof thay vì simple job success.
- **Correctness limitations:** chưa chứng minh crash durability/recreation/race; checkpoint đúng không sửa detection blind spots; Raw checkpoint khác Core/mart consumed checkpoint.
- **Implementation dependencies:** INC-01–05, A03/A04/A06, G07/G08, source-context consistency, target sandbox/schema approval, DW-03C task riêng cho full propagation/recovery.
- **Remaining technical approval / proof:** Physical checkpoint storage/locking/concurrency/durable binding mechanism và runtime failure proof. Logical ACK/publication/identity policy đã Approved; không cấp physical schema/index/access approval.
- **Acceptance criteria:** 8 failure cases có deterministic safe action/evidence; checkpoint không tiến vì load/recon alone; commit-ACK-loss trả same result; changed-content identity conflict/stale base hold; no mixed pins/pointer regression; actual runtime tests trước use.
- **Status:** APPROVED — Logical Policy.

## Remaining technical decisions — không mở lại logical approvals

INC-01–INC-06 đã Approved — Logical Policy; không còn blocker “chưa Owner duyệt sáu directions”. [Work plan](wwi-dw-03b-work-plan.md) section 6 ghi **RG01–RG12** với reason/owner/target/proof/publication blocker cho mọi deferral. Các details chưa được phê duyệt không được chuyển thành approved vì design acceptance.

| Technical decision còn mở | Approved boundary | Target / approval gate |
| --- | --- | --- |
| Exact W algorithm, U selection/page continuation/NULL behavior | Inclusive, no equal-time omission; state reconciliation là correctness proof | RG03, trước WWI-07 candidate-window use |
| Lookback duration, recon cadence, lag/outage envelope | Evidence-based replay + periodic recon, finite window không CDC | RG04, trước runtime scheduling |
| Canonicalization/hash/projection/physical mappings | Exact payload + B9; hash chỉ accelerator, H giữ multiplicity | RG05 và G03–G07, trước Raw publish |
| Temporal optimization/history-retention-generation response | Direct current/H evidence, no loss/fabrication | RG06 trước temporal optimization/publication claim |
| Confirmation/retirement/retraction/incarnation procedure | Absence chỉ candidate; observation membership khác business deletion | RG07 trước entity action, không chặn riêng faithful candidate audit |
| Physical checkpoint binding/locking/concurrency | Durable reconciled publication ACK, no regression | RG08 trước normal Raw publication |
| Dependency scope/reference contracts/impact execution | Sales-first, complete pins, independent headers | RG09 trước affected scope publish; DW-03C design cần task riêng |
| Writable SQL/PG test setup | Original read-only; B9 sandbox không sửa | RG02 trước test DML, RG10 trước E2E claim |
| Numeric Raw quality gates và Certified thresholds | Không tự đặt tolerance/coverage exemption | RG11 trước áp dụng gate/Certified publication |
| Retention/backup/capacity/performance settings | Evidence giữ nguyên khi chưa approved purge | RG12/G07 trước use/purge/scale claim |

Không chọn physical algorithm, numeric values hoặc approve sandbox provisioning trong register này. [Final assessment](wwi-dw-03b-assessment.md) ghi16 mandatory design criteria/QA PASS: **DW-03B DONE — Design** theo conditional Owner authority, không runtime/physical acceptance. DW-03C/DW-04 chưa bắt đầu.
