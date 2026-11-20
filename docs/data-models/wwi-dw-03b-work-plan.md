# WWI DW-03B — Work Plan, Approval & Runtime Gates

**Stage 2, 2026-11-16. INC-01–INC-06 APPROVED — Logical Policy.** Owner task “DW-03B Stage 2 — Owner Logical Approval & Design Finalization” cho phép đóng DW-03B **DONE — Design** và một focused documentation commit **chỉ khi** mandatory design criteria/QA đạt. Không unconditional closure, không runtime approval. [Assessment](wwi-dw-03b-assessment.md) giữ kết quả; DW-03C/DW-04 không bắt đầu.

**Current outcome:** DW-03B **DONE — Design**, DA01–DA16/actual documentation QA đạt theo conditional authority; runtime gates dưới đây vẫn Pending/NOT RUN. WWI-04/Phase1 IN_PROGRESS, DW-03C/DW-04 TODO; commit chỉ sau staged checks và không push.

## 1. Baseline, authority và phạm vi được bảo toàn

Stage 1 bắt đầu từ working tree sạch trên main/HEAD **2e9dc2ab4117f9ba2c39d657c4739a617cfe52c9**. Stage 2 đã kiểm Git: vẫn main/cùng HEAD, **4 new DW-03B files + 7 modified management/navigation files** từ Stage 1, index rỗng, không remote. Bảo toàn nội dung Stage 1 làm nền, không reset/checkout/revert existing work. Baseline đầu Stage 2 có 121 visible files được lấy SHA-256.

Owner cấp trực tiếp sáu INC logical approvals; A01–A06/B1–B9, BRD/KPI, logical grains và scope không thay. Correctness objective: **Current-State Convergence** against verified consistent source state. Không complete CDC/intermediate-event guarantee; no-writes/source-copy policy A02 giữ nguyên.

Kế hoạch trước chỉnh sửa đã trình bày: read/trace accepted inputs → record exact logical approval/limits → hoàn thiện 11 per-source contracts/ACK/recon → review 21 runtime scenarios → tách design vs runtime gates → QA/status → một commit nếu đủ. Không SQL Server/PostgreSQL/Docker/PoC commands, provisioning, dependency hoặc source code mới.

## 2. Inputs và evidence index

Các links dưới đây là authority/evidence gốc, không sao chép hoặc coi các ghi chú Pending lịch sử là quyết định mới. Stage 1/2 không chạy SQL mới; evidence/metadata observations vẫn lịch sử, không current runtime proof.

| ID | Tài liệu đã đối chiếu | Evidence / cách sử dụng |
| --- | --- | --- |
| E01 | [AGENTS](../../AGENTS.md), [Scope](../../PROJECT_SCOPE.md), [Roadmap](../../ROADMAP.md), [Tasks](../../TASKS.md), [README](../../README.md), [Changelog](../../CHANGELOG.md) | Rules, Sales-first, read-only, task/phase và approval boundary |
| E02 | [Source Contracts](wwi-source-contracts.md), [Metadata Dictionary](wwi-metadata-dictionary.md), [Extraction Requirements](wwi-extraction-requirements-matrix.md) | 9 current PKs/columns/types, 2 associated H, candidate LEW/periods, reference dependencies |
| E03 | [Profiling tổng hợp](wwi-data-profiling.md), [Sales](wwi-sales-profiling.md), [Customer temporal](wwi-customer-temporal-profiling.md), [Inventory](wwi-inventory-integrity-profiling.md), [Profiling SQL](wwi-profiling-queries.md) Q01/Q05–Q11 | Historical exact counts, 7 LEW duplicate distributions, 1 zero-duration, current holdings, signed values; không freshness/write-behavior proof |
| E04 | [Raw Requirements](../requirements/wwi-raw-layer-requirements.md), [Validation Matrix](../requirements/wwi-source-validation-matrix.md) S01–S08/I01–I12 | Payload/lineage, required reconciliation/partial-batch boundaries; current DW-03A follow-up supersedes older proposals đúng scope |
| E05 | [BRD Matrix](../requirements/wwi-business-rules-decision-matrix.md), [KPI Catalog](../requirements/kpi-definitions/wwi-kpi-candidate-catalog.md), [KPI SQL](../requirements/kpi-definitions/wwi-kpi-verification-sql.md) | Approved source measures/date roles/exclusions; không đổi revenue/COGS/payments/daily-balance scope |
| E06 | [DW-01 logical design](wwi-logical-dw-design.md), [Change Impact](wwi-change-impact-matrix.md) | 4 facts/conformed dims/headers, L01–05, independent headers/old-new group propagation |
| E07 | [Final SCD2 Specification](wwi-final-scd2-design-specification.md), [SCD SQL](wwi-scd-temporal-evidence.md) C01/C02/C04/P01/P02, [SCD ADRs](../adr/README.md) | B1–B8 identity/registry/validity/hybrid/correction, current B9 follow-up; physical occurrence ≠ analytical episode |
| E08 | [DW-03A final design](wwi-dw-03a-full-raw-design-proposal.md), [approval register](wwi-dw-03a-decision-register.md), [assessment](wwi-dw-03a-assessment.md) section 15, [G01–G08](wwi-dw-03a-work-plan.md) section 5 | Accepted captures/context/multiplicity/replay/atomic pins; deferred gate ownership/implementation boundaries |
| E09 | [B9 evidence](wwi-dw-03a-evidence-approval-readiness.md) sections 5.1/15, [PoC README](../../tests/integration/b9_precision/README.md), [ADR-SCD-05](../adr/scd-05-exact-temporal-precision.md) | Actual F2/TEXT/C proof đã ghi, không rerun/sửa sandbox. Unit12/source14-169-18/PG14-15-order169-equality14-ranges5 là **historical B9**, không incremental tests |
| E10 | Primary Microsoft references trong [proposal](wwi-dw-03b-incremental-design-proposal.md) section 5 | Engine transaction-begin time, zero-duration, H constraints/retention; kiểm online 2026-11-16, không actual local feature-state evidence |

## 3. Stage 2 work items và dependencies

| Work item | Module / dependencies | Mandatory design deliverable | Acceptance evidence |
| --- | --- | --- | --- |
| S2-01 | docs/data-models; Owner instruction + Stage 1 | Six formal logical approvals/limits, no physical approval inflation | Decision Register, six recorded statuses |
| S2-02 | docs/data-models; S2-01 + DW-03A A02/A06 | C/S_C/R_C state boundary, 11 source contracts, full-read cost disclosure | Specification sections 1–2 |
| S2-03 | docs/data-models; S2-02 + INC-02/03/06 | Conditional window/replay, guarded state machine, ACK01–06, recon coverage | Specification sections 3–8 |
| S2-04 | docs/data-models; accepted SCD2/ADRs + S2-03 | Compatibility, 21 scenarios all NOT RUN, every deferral with owner/proof/gate | Specification sections 9–11, RG01–RG12 below |
| S2-05 | docs/root; S2-01–04 | Structured design criteria/QA, conditional DONE, exact scope/status | Assessment DA01–DA16, QA evidence |
| S2-06 | docs/root Git; S2-05 PASS | Review staged blobs/secrets/size/diff, one focused documentation commit | Git result reported after commit; no push |

Không tạo task implementation mới. DW-03B DONE — Design không cấp quyền thực hiện DW-03C; Owner phải giao task riêng. Không bắt buộc complete production pipeline để nghiệm thu design, nhưng runtime deferrals không được đánh dấu PASS.

## 4. Deliverables và file ownership

[Logical Incremental Specification](wwi-dw-03b-incremental-design-proposal.md): source matrix + extended contracts, assurance/boundaries, ACK/recon/test/risk. [Decision Register](wwi-dw-03b-decision-register.md): formal authority/limits/remaining decisions. [Assessment](wwi-dw-03b-assessment.md): design criteria/actual QA/runtime boundary. Work plan hiện tại: baseline/trace/gate ownership.

Final commit allowlist **12 Markdown files**, gồm 11 existing Stage 1 paths và **wwi-change-impact-matrix.md** thêm reference handoff; không thay approved DW-01 impact table hoặc business/model rules. Bảy root/navigation paths: AGENTS.md, PROJECT_SCOPE.md, ROADMAP.md, TASKS.md, README.md, CHANGELOG.md, docs/data-models/README.md. Bốn DW-03B files giữ nguyên tên, không thêm duplicate spec/ADR. Source-to-target mapping không cần sửa vì source fields/grains không thay.

Mọi accepted ADR, source contracts/profiling SQL, DW-02/DW-03A/B9 code/tests/evidence và module runtime ngoài allowlist phải giữ SHA-256. Không tạo script/dependency/schema/config hoặc output chứa source data trong Git.

## 5. Design acceptance vs runtime acceptance

Mandatory **design**: approved assurance/policies, coherent source boundary, complete per-source contracts, exactness/multiplicity/delete distinctions, checkpoint guards/failure/recon/compatibility, 21 test specs, traceable deferrals, statuses/QA. Kết quả duy nhất tại Assessment DA01–DA16; chưa QA đạt thì chưa đóng/commit.

Mandatory **runtime**: source consistency/permission/fidelity/full-state equality, test infrastructure approval, timestamps/window behavior, delete action evidence khi áp dụng, durable publication/checkpoints/recovery, consumer pinning, measured scheduling/capacity/thresholds. B9 bounded historical PASS không thay full-field incremental proof. Tất cả IT01–IT21 vẫn **NOT RUN**; no new test outcomes.

## 6. Deferred physical/runtime gates — authoritative DW-03B disposition

RG01–RG12 là tracking IDs, **không** approvals hoặc tasks được phép tự bắt đầu. Giữ nguyên toàn bộ [DW-03A G01–G08](wwi-dw-03a-work-plan.md) section 5 và B5 certification thresholds. Mỗi gate có lý do, trách nhiệm, target, required proof và blocker; “Pending” là chưa technical approval/proof, không còn “chưa approved six logical policies”.

| Gate / mapping | Decision deferred | Reason | Owner / approval authority | Target stage | Required proof | Publication blocker / usage gate |
| --- | --- | --- | --- | --- | --- | --- |
| RG01 / G01 | Concrete consistency method/state C | Chưa có verified no-writes window hoặc approved consistent copy | Source Owner/DBA + ingestion implementer; Project Owner duyệt method/copy | WWI-05 prepare, trước WWI-06/07 capture và normal publication | Writer controls/attestation xuyên reads/recon hoặc verified copy+generation provenance; same-C full count/key/value/H multisets | Không proof C/S_C hoặc mixed states → hold normal publication; không enable SNAPSHOT/RCSI/NOLOCK shortcut |
| RG02 / G02 | Least-privilege profiles + independent writable environments | Interactive PoC không production principal; chưa authorize provision/DML test | DBA/infrastructure + security reviewer; Project Owner approve separate task | WWI-05/readiness; trước WWI-07 test DML | Effective SELECT/meta grants original, trusted TLS; exact sandbox allowlist/provenance/permissions/capacity; approved separate target | Không deploy bằng sysadmin PoC hoặc chạy writes khi chưa allowlisted/approved; B9 sandbox không sửa |
| RG03 / INC-01/02 | Exact W/U/cursor/NULL/generation algorithm | Logical inclusion không chứng minh source update behavior/complete horizon | Ingestion designer + DQ; Project Owner review technical proposal | Trước WWI-07 window use; baseline full method trước WWI-06 publication | IT02–07/21 expected/actual old-key/equal/backdated/late-commit/page/NULL/U<H/source-reset cases; full state comparison equivalence | W-only/window-count PASS không đủ convergence; thiếu proof dùng complete full comparison hoặc hold; không silent omissions |
| RG04 / INC-03 | Lookback duration/recon cadence/lag/outage limits | Chưa đo lateness/write paths/cost, không chọn số giả định | Ingestion/DQ/operations đo; Project Owner approve values/schedule | Trước periodic runtime scheduling WWI-07; normal full checks vẫn trước publish | Measured begin/commit/observation/timestamp envelope, missed-outside-window cases, scan cost/storage/outage tests, versioned approved schedule | Không schedule numeric defaults hoặc skip required recon; missing state proof hold converged publication |
| RG05 / G03–G06 | Actual full-field codecs/NULL/canonicalization/hash/physical B9 path | B9 PoC bounded, chưa full extractor/loader/projection verification | Ingestion/storage + DQ; Project Owner approve mapping/dependencies | WWI-05 mapping, WWI-06 trước normal Raw publish; WWI-07 incremental regression | Explicit projection; exact decimal/Unicode/bytes/geography/computed/NULL; F2→str/None→psycopg→TEXT/C, actual equality/100ns/multiplicity tests | Lossy/unverified required field hoặc hash-only “proof” → hold fidelity/completeness; no silent normalization |
| RG06 / INC-04/B6 | Period optimization, retention/generation/cutover proof | History not global log; cleanup/restore/late visibility còn Unverified | Source DBA + ingestion/DW designer + DQ; Project Owner review | Trước temporal optimization/publish WWI-06/07, trước SCD lookup WWI-08/12 | Versioning/H linkage/retention metadata, generation/source-forward bridge, IT06/08–10/18, retained source-H multiset | Missing required current/H/context or unresolved generation splice → hold affected complete claim; no purge/forward loss; no business-effective inference |
| RG07 / INC-05/B8 | Delete confirmation/action/reappearance procedure | Absence chỉ observation candidate, không có entity-lifetime ground truth | Source/data owner + DW designer/DQ; Project Owner approve controlled action | DW-03C handoff planning; trước bất kỳ retirement/retraction/incarnation action trong implementation | Complete compatible snapshots/absence lineage, source/DBA removal evidence, B8 entity continuity, approved impact/rollback policy; IT12/13 | Partial/inconsistent snapshot không valid delete evidence; chưa confirmed policy thì không retire/cascade/retract; faithful candidate audit có thể giữ riêng |
| RG08 / G08/INC-06 | Physical checkpoint binding/storage/locking/concurrency/recovery | Logical ACK01–06 có, runtime transactions/durable read-back chưa triển khai | Storage/ingestion/orchestration + DQ; Project Owner release authority | DW-03C thiết kế khi được giao; WWI-06 trước first normal Raw publish, WWI-07 incremental use | Ledger/membership/pointer/checkpoint-binding atomic visibility, predecessor/content validation, IT15–18 crash/ACK loss/retry/race tests | Unknown commit, failed guards/stale conflict/partial visibility → hold/no ACK; no silent pointer regression |
| RG09 / A06/DW-01 | Concrete publication/reference scope + propagation execution | Sales-first direction approved, exact execution closure/reference contracts chưa implement | Ingestion/DW + reference owner/DQ; Project Owner approve scope/contracts | Trước affected scope publish WWI-06/07; DW-03C impact design; WWI-08 downstream | Compatible required parents/headers/master current-H pins, TransactionTypes/PackageTypes controlled references, IT19 old/new header envelope và downstream tests | Missing required dependency/type contract hoặc mixed pins → hold affected scope; không chờ toàn Inventory analytics để publish Sales |
| RG10 / IT01–21 | Runtime suite execution/performance/failure evidence | Stage 1/2 design-only, không writable SQL/PG setup authorization | Test/ingestion/storage implementers + DQ; Project Owner acceptance | WWI-06 baseline subset trước normal publish; WWI-07 incremental E2E; advanced monitoring WWI-10 | Scenario-specific fixtures/expected/actual/source-target versions/negative controls, original unchanged evidence; full rebuild/reconciliation comparison | Required cases cho enabled path phải thực chạy PASS trước use; future monitoring không trì hoãn publication correctness |
| RG11 / B5/A06 | Numeric Raw quality thresholds/severity và Certified row/value thresholds/tolerances | Chưa có measured evidence/Owner values; không tự default 100% hoặc tolerance | DQ/DW designer đề xuất; Project Owner approve | Raw gates trước use/publication; B5 trước bất kỳ Certified KPI/view | Versioned metrics/scope/denominator/value coverage/signed-absolute diagnostics, approved limits, boundary tests | No bypass completeness/integrity/precision; numerical criteria chưa approve thì không dùng để pass hoặc claim Certified |
| RG12 / G07/B2 | Raw DDL/index/layout/retention/capacity/backup/performance settings | A03/B9 không approve whole Raw physical design, chưa đo full-read/storage cost | Storage/data custodian + implementer/DQ; Project Owner approve | WWI-05 review trước schema/load WWI-06; retention trước purge; incremental scale trước claim | Physical proposal/constraints, measured scans/bytes/growth, dependency-safe retention/restore compatible registry+forward/publications | No unauthorized schema/purge/index; không xóa referenced evidence; không performance/full-scan-avoidance claim khi chưa đo |

Không gate nào ở bảng trên được gắn runtime PASS tại vòng này. Đối với RG07, candidate observation không yêu cầu tự xác nhận entity deletion để tồn tại; action gates chỉ chặn việc sử dụng candidate như confirmed business deletion. Đối với RG03/04, full comparison có thể là correctness baseline nhưng không miễn method/permission/fidelity/runtime proof.

## 7. Review đủ 21 runtime scenarios

IT01–IT21 giữ nguyên IDs/scenario assertions trong Specification section 10; không lập suite mới trùng chức năng. Stage 2 review coverage:

| IDs | Coverage và owner gate | Design review | Actual execution |
| --- | --- | --- | --- |
| IT01 | Metadata/context/versioning/retention — RG01/02/06 | Covered; read-only scope phải authorized | NOT RUN |
| IT02–IT07 | INSERT/UPDATE/equal-time/page/late/backdated/long transaction — RG03/04/10 | Covered; same-capture vs new context rõ | NOT RUN |
| IT08–IT10 | Direct H/zero-duration/multiplicity/maintenance/generation — RG05/06 | Covered; no original writes/direct H DML assumption | NOT RUN |
| IT11–IT14 | Holdings exact diff/absence/reappearance/transient-event limit — RG05/07 | Covered; candidate khác entity action, no event completeness claim | NOT RUN |
| IT15–IT18 | Failures/unknown commit/retry/stale base/replay/reload — RG08/10/12 | Covered; ACK guards/pins/forward history | NOT RUN |
| IT19 | Independent header detection và old/new impact envelope — RG09 | Covered; downstream mechanics để DW-03C | NOT RUN |
| IT20 | Exact full-field/B9 canonicalization negative controls — RG05 | Covered; không sửa/rerun B9 sandbox | NOT RUN |
| IT21 | Source/reference/generation/netting risks — RG01/03/06/09/11 | Covered; full key/value proof không totals-only | NOT RUN |

## 8. Handoff và điểm dừng

DW-03C nhận approved INC policies, C/S_C/R_C/P0/ACK01–06, 11 source contracts, header old/new envelope requirements, immutable identities/replay/absence candidates, recon/test definitions và RG gates. Downstream propagation/rekey/restatement execution không được thực hiện trong DW-03B; chưa có DAG/dbt/schema/pipeline.

Chỉ khi DA01–DA16/QA đạt mới cập nhật DW-03B DONE — Design, tạo đúng một commit **docs: finalize DW-03B incremental load design**. WWI-04/Phase 1 IN_PROGRESS, DW-03C/DW-04 TODO, Phase 2–9 Not Started. Không push/remote hoặc tự bắt đầu task tiếp.
