# Task Tracker

Trạng thái hợp lệ: `TODO`, `IN_PROGRESS`, `BLOCKED`, `REVIEW`, `DONE`, `DEFERRED`. DONE cần acceptance evidence; Owner quyết định nghiệm thu/chuyển phase. Phase 0 **Completed**; Phase 1 **Completed — Requirements & Source Design**; WWI-02/03 **DONE**, WWI-04 **DONE — Design**. DW-01/02/03A/03B/03C **DONE — Design**; DW-04 **DONE — Design Acceptance**. Phase 2 **IN_PROGRESS — Authorized**, WWI-05 **IN_PROGRESS**, M1A **DONE — Verification Checkpoint**. Raw foundation PREPARED/OFFLINE TESTED; runtime/Full Load và Phase3–9 **Not Started**. [Owner closure/authorization](docs/architecture/wwi-phase-1-closure-approval.md) và [current MVP policy](docs/architecture/wwi-m1b-owner-decisions.md#mvp-simplification-01--trusted-local-mvp).

## MVP Operational Milestones

MVP-SIMPLIFICATION-01 tạo operational view dưới đây; không thay ID/status31 detailed gates hoặc tuyên bố72 runtime scenarios đã PASS. EX02-S1 protected staging/ACL/hashes **DEFERRED — OPTIONAL SECURITY HARDENING**, không dependency của MVP-G01/02. Readiness/handoff cũ phía dưới giữ lịch sử; source least privilege, consistency, temporal fidelity, reconciliation, SCD2 và recovery vẫn bắt buộc tại đúng milestone.

| Milestone | Dependencies / outcome bắt buộc | Status / evidence hiện tại |
| --- | --- | --- |
| MVP-G01 — Source Access | EX01; authorize EX02 rồi actual extractor connect, đúng11 SELECT, không write/admin, source TLS | BLOCKED — EX01 DONE, SQL setup/verify NOT RUN; [local procedure](data-sources/security/README.md#10-local-mvp-setup--pending-runtime-authorization) |
| MVP-G02 — PostgreSQL Raw | Authorize riêng isolated Compose startup/bootstrap; reliable restart/persistence/config, schema+metadata và connectivity | REVIEW — [foundation prepared](infrastructure/docker/README.md), offline tests PASS; Docker Engine unavailable, runtime NOT RUN. Có thể chuẩn bị song song G01 |
| MVP-G03 — Full Load | G01+G02; WWI-06 physical payload/batch/chunk/publication, supported source context,11 required objects/counts/fidelity/100ns/safe rerun | TODO — không extractor hoặc ingestion runtime |
| MVP-G04 — Incremental | G03; approved current-state convergence, checkpoint/rerun/delete-history limitations và recovery | TODO — không bịa CDC; mutation tests chỉ môi trường độc lập được duyệt |
| MVP-G05 — Data Warehouse | Accepted mappings/BRD/KPI; dbt staging/core/facts/dims/SCD2/critical tests trên accepted Raw | TODO — WWI-08; có thể phát triển Sales slice từ G03 trong khi G04 hoàn thiện |
| MVP-G06 — Analytics & Orchestration | G04+G05; defined KPI marts/Power BI, Airflow/recovery và reproducible Sales e2e demo | TODO — WWI-09/10/11 rồi Customer/Inventory như roadmap |

Next engineering task: **WWI-06 Python Full Load implementation** sau EX02/Raw runtime readiness hoặc trong task code-only riêng được giao. Dùng đúng11 allowlist, batch reads, source-shaped lossless types, approved F2 strings, immutable capture/batch/attempt/chunk IDs, append-only target/reconciliation/publication boundary; no partial publication. Test failed chunk/unknown commit ACK, retry sealed content, archive duplicate multiplicity và explicit UNVERIFIED source-context limitation; chỉ publish khi applicable correctness checks có evidence. Không chạy Full Load trong task simplification.

Các task dưới đây là backlog hiện hành cho nguồn SQL Server WWI chỉ đọc và warehouse PostgreSQL. Task của kiến trúc nguồn cũ đã được loại khỏi backlog, không được tính là `DONE`. Mỗi task chỉ được bắt đầu khi phase và dependencies tương ứng được chủ dự án cho phép.

| Task ID | Phase | Module | Description | Priority | Dependencies | Acceptance Criteria | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0-01 | 0 | Root | Kiểm tra hiện trạng và bảo toàn file dùng chung | High | Yêu cầu khởi tạo | Xác định root, file hiện có và phạm vi thay đổi | DONE |
| P0-02 | 0 | All modules | Tạo cấu trúc và README điều hướng | High | P0-01 | Module dùng chung có README phù hợp | DONE |
| P0-03 | 0 | Root/docs | Viết quy tắc AI, scope, roadmap và architecture | High | P0-01 | Tài liệu hiện hành nhất quán; Open Decisions rõ | DONE |
| P0-04 | 0 | Root | Kiểm tra checklist Phase 0 | High | P0-02, P0-03, WWI-01 | Không có code sớm, secret, link gãy hoặc kết quả giả | DONE |
| P0-05 | 0 | Root | Kiểm tra file nhạy cảm/lớn, `.gitignore` và đề xuất baseline commit | High | P0-01 | Có kết luận về file được theo dõi, dữ liệu nguồn, secret và các bước Git trước `git init` | DONE |
| P0-06 | 0 | Root | Khởi tạo Git repository và baseline commit theo yêu cầu riêng | Medium | P0-05, owner approval | `.git` có trạng thái kiểm tra được; staged files an toàn; baseline commit đúng message; không tạo remote/push | DONE |
| WWI-01 | 0 | Root/docs/data-sources | Chuyển tài liệu hiện hành sang WWI, rà yêu cầu chung và loại file nguồn/đề cương cũ | High | Quyết định chuyển nguồn của owner | Scope, roadmap, tasks, architecture, README, ADR đồng bộ; không còn link gãy/file nguồn cũ/PDF đề cương; không xóa thành phần dùng chung | DONE |
| WWI-02 | 1 | docs/data-models, data-sources | WWI source contract/data dictionary/ERD cho Sales; khảo sát Customer/Inventory | High | Phase 0 được nghiệm thu, WWI-01 | PK/FK/grain/dates/temporal/null và ngoại lệ có bằng chứng; owner review | DONE |
| WWI-03 | 1 | docs/requirements, analytics | Chốt business requirements, KPI MVP, tax/customer role và hoãn revenue/COGS/AOV không đủ policy | High | WWI-02 | Công thức, source measure, date basis, exclusions, reconciliation và tests được owner duyệt trước fact/mart | DONE |
| WWI-04 | 1 | docs/data-models, docs/architecture, docs/adr | Thiết kế logical DW, SCD2, full/incremental, propagation/recovery và môi trường thử nghiệm độc lập | High | WWI-02, WWI-03 | DW-01–DW-04 được owner nghiệm thu; watermark/tie-breaker/delete/history/as-of và test INSERT/UPDATE/DELETE chỉ trên môi trường độc lập được duyệt | DONE |
| WWI-05 | 2 | infrastructure, data-sources, storage | Chuẩn bị WWI read-only và PostgreSQL đích | High | WWI-02, WWI-04, phase implementation approval | Quyền/cấu hình kết nối, điều kiện nguồn ngoài repo và môi trường local tái lập được xác minh; không lộ secret/không sửa WWI | IN_PROGRESS |
| WWI-06 | 3 | ingestion, storage, data-quality | Sales full load, raw/staging, validation và rerun | High | WWI-03, WWI-05 | Batch metadata (count/duration/error), count/keys đối soát, quarantine và idempotent rerun có unit/integration test thực | TODO |
| WWI-07 | 3 | ingestion, tests | Sales incremental/checkpoint và failure recovery | High | WWI-04, WWI-06, approval cho test environment | Test INSERT/UPDATE end-to-end trong môi trường độc lập; checkpoint/retry/backfill có bằng chứng; WWI gốc không đổi | TODO |
| WWI-08 | 4 | storage, transformation, data-quality | Sales warehouse/dbt và kiểm tra cơ bản | High | WWI-03, WWI-06 | Fact/dim đúng grain, tránh double count; unique/not null/relationships/accepted values và business tests, reconciliation chạy thực | TODO |
| WWI-09 | 5 | orchestration, tests | Điều phối Sales bằng Airflow | High | WWI-07, WWI-08 | DAG đúng dependency, retry/rerun an toàn qua thử nghiệm | TODO |
| WWI-10 | 6 | data-quality, monitoring, tests | Sales quality gates, monitoring, failure và hiệu năng | High | WWI-09 | Ngưỡng được duyệt; sai lệch/lỗi được phát hiện, truy vết và phục hồi; thời gian/query plan có số đo thực | TODO |
| WWI-11 | 7 | analytics | Sales mart/Power BI và nghiệm thu lát cắt Sales | High | WWI-08, WWI-10 | KPI khớp định nghĩa, mart/report có lineage và đối soát; Sales end-to-end được review | TODO |
| WWI-12 | 7 | ingestion, transformation, analytics | Customer Analytics và SCD2 theo bằng chứng | High | WWI-11, WWI-02, WWI-04, quyết định customer/SCD2 | Customer pipeline/mart có as-of tests, DQ, orchestration và reconciliation | TODO |
| WWI-13 | 7 | ingestion, transformation, analytics | Inventory Movements và mart | High | WWI-12, inventory contract/decisions | Movement grain/quantity đúng; DQ, orchestration, reconciliation; không suy daily balance chưa duyệt | TODO |
| WWI-14 | 8 | docs/analytics | Purchasing hoặc Finance extension khi được duyệt | Low | WWI-13, owner scope approval | Task/KPI/contract và tests riêng; không chặn MVP | TODO |
| WWI-15 | 8 | infrastructure, storage | BigQuery extension khi được duyệt | Low | WWI-13, owner approval | Tương đương dữ liệu, bảo mật/chi phí và số đo thực nếu triển khai | TODO |
| WWI-16 | 9 | tests, docs, .github | Unit/integration/e2e, CI, runbooks, tối ưu truy vấn và portfolio MVP local | High | WWI-11, WWI-12, WWI-13; WWI-14, WWI-15 chỉ nếu được giao | Người khác tái lập local với nguồn WWI được chuẩn bị hợp lệ; CI/test/failure report và số đo tối ưu trước/sau nếu có đều có bằng chứng | TODO |

## Kế hoạch Phase 1.6 / WWI-04

WWI-04 là parent task; các ID DW dưới đây phân rã task theo yêu cầu Owner, không đổi ID WWI hiện hữu. DW-01 đã hoàn tất; các task sau chỉ bắt đầu khi Owner giao; dependencies đạt không tự cấp quyền bắt đầu task sau. Không tạo database/code/test environment trong DW-01.

| ID | Description / module | Dependencies | Acceptance criteria | Status |
| --- | --- | --- | --- | --- |
| DW-01 | Logical Dimensional Modeling — docs/data-models, architecture | WWI-02, WWI-03, Owner cho phép Phase 1.6 | Bốn fact grains, conformed dims, mapping nguồn, BRD/KPI trace, năm Mermaid, change impact/header updates, sáu marts và checklist được Owner review | DONE |
| DW-02 | SCD2 & Temporal History Design — docs/data-models | DW-01 nghiệm thu, Owner giao task | Attributes, system/business/observation time, validity, gap/zero-duration/unknown và forward tracking được duyệt | DONE |
| DW-03A | Full Load & Raw Layer Design (DONE — Design) — docs/requirements, architecture | DW-01 nghiệm thu, source contracts, Owner giao task | Full extraction consistency, projection/type/precision, batch/raw/manifest và reconciliation được duyệt | DONE |
| DW-03B | Incremental Load Design (DONE — Design) — docs/data-models, ingestion docs | DW-02, DW-03A, Owner giao task | Watermark/tie-breaker, late update/delete/snapshot và test INSERT/UPDATE/DELETE độc lập được duyệt, không đổi WWI gốc | DONE |
| DW-03C | Change Propagation & Recovery Design (DONE — Design) — docs/architecture | DW-03B, DW-02, Owner giao task | Header/dim propagation, affected old/new groups, checkpoint/replay/restate/publication và recovery tests có specification được duyệt | DONE |
| DW-04 | Final Design Verification & Acceptance — docs (DONE — Design Acceptance) | DW-01, DW-02, DW-03A/B/C, Owner giao task | Cross-document/model/KPI/lineage/phase gates nhất quán, không open blocker bắt buộc; Owner nghiệm thu WWI-04 | DONE |

[DW-01 specification](docs/data-models/wwi-logical-dw-design.md) và [assessment](docs/data-models/wwi-dw-01-assessment.md) là bộ thiết kế đã nghiệm thu, không phải evidence runtime. WWI-03 giữ DONE; DW-01 đã nghiệm thu qua targeted review; WWI-04 vẫn IN_PROGRESS. L01–L05 và Kimball/bốn facts/conformed dims do Owner phê duyệt ở task Phase 1.6; B1–B8 SCD2 logical policies sau đó được duyệt; incremental/physical implementation còn mở.

## DW-02A/B nghiệm thu và nghiệm thu thiết kế DW-02C/D

Owner cho phép bắt đầu DW-02 trong đúng A/B sau nghiệm thu DW-01. [Attribute Classification](docs/data-models/wwi-scd-attribute-classification.md), [Temporal/Precision/Lookup Assessment](docs/data-models/wwi-scd-temporal-assessment.md), [SQL evidence](docs/data-models/wwi-scd-temporal-evidence.md) và [Assessment A/B](docs/data-models/wwi-dw-02ab-assessment.md) là deliverables để review. A/B đã được Owner nghiệm thu sau ghi nhận SCD-01–07; approved Customer direction tách khỏi Product/technical options Pending Approval. C/D chưa được đưa vào commit nghiệm thu A/B.

| ID | Description / module | Dependencies | Acceptance criteria | Status |
| --- | --- | --- | --- | --- |
| DW-02A | SCD Attribute Classification — docs/data-models | DW-01 DONE; Owner giao A/B | Customer/Product đủ columns, meaning/observations/SCD recommendation/reason/KPI/evidence/approval; không auto SCD2 metadata | DONE |
| DW-02B | Temporal History Coverage — docs/data-models | DW-01 DONE; source evidence; Owner giao A/B | NK/version coverage, physical/ALL, zero/gap/overlap/precision/lookup và forward readiness có SELECT evidence; không tự chọn fallback/type/algorithm | DONE |
| DW-02C | Source Identity, SK & Historical Lookup — docs/data-models | DW-02A/B DONE, Owner giao C/D | Tách NK/source/business version/SK/lookup, ít nhất hai identity/SK options, precision và bảy role lookups/unresolved; technical choices chờ Owner review | DONE |
| DW-02D | Forward Tracking, Hybrid Cutover & Recovery — docs/data-models | DW-02A/B DONE, interface C, Owner giao C/D | State transitions, hybrid/recovery options, scoped restatement và independent test matrix được trình review; không runtime | DONE |
| DW-02E | Final SCD2 Design Assessment & Handoff — docs/data-models | DW-02C/D DONE; Owner giao E riêng | E1–E5 audit/invariants/transitions/gates/handoff được Owner nghiệm thu; technical backlog có quyết định hoặc deferral hợp lệ; chưa tự triển khai | DONE |


## Bằng chứng nghiệm thu WWI-01 (hồ sơ lịch sử)

Chủ dự án đã review và phê duyệt WWI-01 ngày 2026-11-07. [Scope](PROJECT_SCOPE.md), [Roadmap](ROADMAP.md), [README](README.md), [architecture](docs/architecture/README.md) và [ADR](docs/adr/wwi-source-migration.md) cùng mô tả một nguồn WWI SQL Server chỉ đọc và warehouse PostgreSQL. File dữ liệu/đề cương và tài liệu chỉ phục vụ nguồn cũ đã được loại; module Data Engineering dùng chung được giữ. Kiểm tra 102 liên kết Markdown cục bộ cho kết quả 0 liên kết gãy; quét nội dung hiện hành không thấy tham chiếu tới file nguồn cũ. Đây là nghiệm thu **tài liệu/cấu trúc**; không có pipeline, database đích hoặc test chức năng được xác nhận.

## Bằng chứng nghiệm thu Phase 0

Ngày 2026-11-07, chủ dự án phê duyệt P0-01, P0-02, P0-05 và P0-06 theo báo cáo nghiệm thu, đồng thời cho phép hoàn tất Phase 0 nếu P0-03 và P0-04 đạt sau khi khắc phục. Root Git được xác minh tại thư mục dự án; 13 module cấp cao đều có README với các mục bắt buộc. [ADR chuyển nguồn](docs/adr/wwi-source-migration.md) đã được diễn giải bằng tiếng Việt, giữ quyết định WWI SQL Server chỉ đọc → PostgreSQL warehouse và các Open Decisions. [Scope](PROJECT_SCOPE.md), [Roadmap](ROADMAP.md), [README](README.md) và ADR nhất quán về MVP, thứ tự Sales → Customer → Inventory và giới hạn chưa triển khai.

Kiểm tra lại P0-04 trên 57 file tracked: 111 liên kết Markdown nội bộ, không có link gãy; không phát hiện yêu cầu nguồn cũ còn hiệu lực, file dữ liệu nguồn, file nhị phân hoặc mẫu secret; không có code pipeline hay kết quả test chức năng được tuyên bố. File lớn nhất 8.985 byte. Baseline commit `9f514f81fb8f2a0efac65b566a4b1cd7f3818677` có đúng message `chore: initialize WWI retail data platform`; Git không có remote hoặc push. Nghiệm thu này chỉ áp dụng cho Phase 0 tài liệu và repository; Phase 1 vẫn `Not Started`.

## Tiến độ WWI-02 — Phase 1.1 và Phase 1.2

Chủ dự án đã review và chấp thuận nội dung Phase 1.1; sau khi review, chủ dự án chấp thuận nghiệm thu khảo sát Phase 1.2 và cho phép Phase 1.3. [Inventory](docs/data-models/wwi-database-inventory.md), [metadata dictionary](docs/data-models/wwi-metadata-dictionary.md), [temporal/index assessment](docs/data-models/wwi-temporal-index-assessment.md), [SQL metadata queries](docs/data-models/wwi-metadata-queries.md) và [báo cáo Phase 1.1](docs/data-models/wwi-phase-1-1-assessment.md) ghi bằng chứng metadata chỉ đọc. [Báo cáo profiling Phase 1.2](docs/data-models/wwi-phase-1-2-assessment.md) và [SQL evidence](docs/data-models/wwi-profiling-queries.md) ghi kết quả kiểm tra dữ liệu trực tiếp. Các acceptance criteria Phase 1.2 trong assessment đều PASS, được Project Owner nghiệm thu về mặt khảo sát dữ liệu. WWI-02 vẫn `IN_PROGRESS` vì source contract và các phần còn lại chưa hoàn tất; WWI-03/04 vẫn TODO.

Phase 1.3 đã tạo [source relationships](docs/data-models/wwi-source-relationships.md), [source ERD](docs/data-models/wwi-source-erd.md), [business data flow](docs/data-models/wwi-business-data-flow.md), [relationship validation SQL](docs/data-models/wwi-relationship-validation-sql.md) và [assessment](docs/data-models/wwi-phase-1-3-assessment.md). Các quan hệ nguồn có bằng chứng FK và số liệu snapshot riêng. Chủ dự án đã review và chấp thuận Phase 1.3 ở mức tài liệu/khảo sát; Phase 1.4 được phép thực hiện. WWI-02 vẫn `IN_PROGRESS`; WWI-03/04 vẫn TODO.

Phase 1.4 đã chuẩn bị [source contracts](docs/data-models/wwi-source-contracts.md), [extraction matrix](docs/data-models/wwi-extraction-requirements-matrix.md), [raw requirements](docs/requirements/wwi-raw-layer-requirements.md), [validation matrix](docs/requirements/wwi-source-validation-matrix.md) và [assessment](docs/data-models/wwi-phase-1-4-assessment.md). Chín bảng MVP được bao phủ; mọi extraction candidate và kiểm tra sau ingestion chỉ ở mức đề xuất. Project Owner đã review và nghiệm thu Phase 1.4 ở mức tài liệu. PK/FK/grain/dates/temporal/null và ngoại lệ nguồn có bằng chứng trong các deliverable Phase 1.1–1.4; tiêu chí owner review đạt. WWI-02 `DONE` ở phạm vi source design, không chứng minh ingestion/warehouse đã triển khai. Project Owner đã cho phép Phase 1.5; WWI-03/04 chưa được nghiệm thu.

Phase 1.5/WWI-03: Project Owner đã phê duyệt BRD-01–BRD-12 theo [Business Rules Matrix](docs/requirements/wwi-business-rules-decision-matrix.md). [Business Requirements](docs/requirements/wwi-business-requirements.md), [Business Questions](docs/requirements/wwi-business-questions-use-cases.md) và [KPI Catalog](analytics/kpi-definitions/wwi-kpi-candidate-catalog.md) ghi công thức, source measure, grain nguồn, date basis, population, exclusions và vai trò buyer/bill-to. [KPI Verification SQL](analytics/kpi-definitions/wwi-kpi-verification-sql.md) K01–K13 cho phép đối soát; K10–K13 đã chạy SELECT trên WWI local ngày 2026-11-14 và [assessment](docs/requirements/wwi-phase-1-5-assessment.md) ghi acceptance checklist. Owner duyệt định nghĩa nghiệp vụ và quyết định hoãn KPI ngoài MVP; runtime tests, fact/dimension grain và physical schema chưa triển khai/duyệt. WWI-03 `DONE` ở mức tài liệu, Phase 1.5 hoàn tất; Phase 1 vẫn `In Progress`, Phase 1.6/WWI-04 chưa bắt đầu.

## Nghiệm thu DW-02C/D và chuẩn bị DW-02E

A/B acceptance commit: `b293fdbfed99cfb64d65c7bc3641c1068627e060`. Bản [Identity/SK/Precision](docs/data-models/wwi-scd-identity-key-design.md), [Historical Lookup](docs/data-models/wwi-scd-historical-lookup-design.md), [Forward/Cutover/Recovery](docs/data-models/wwi-scd-forward-cutover-design.md), [Assessment/Test Matrix](docs/data-models/wwi-dw-02cd-assessment.md) đã được targeted review, C/D DONE ở mức tài liệu theo D01–D06. Architecture direction Accepted; technical procedures/physical details vẫn Pending Approval. Hồ sơ C/D tại thời điểm nghiệm thu giữ parent IN_PROGRESS; nay DW-02/DW-02E design DONE theo approval B1–B8 và final QA, WWI-04 vẫn IN_PROGRESS; DW-03 chưa bắt đầu.

Sáu [ADR SCD](docs/adr/README.md) đã được Owner phê duyệt ngày 2026-11-14. [DW-02E Work Plan](docs/data-models/wwi-dw-02e-work-plan.md) ghi E1–E5 và backlog B1–B9; E1–E5 đã có kết quả review tài liệu trong [Final Specification](docs/data-models/wwi-final-scd2-design-specification.md) và [E Assessment](docs/data-models/wwi-dw-02e-assessment.md). E/DW-02 DONE ở mức thiết kế theo B1–B8 logical approval và conditional acceptance authority của Owner sau QA đạt; không thực hiện DW-03. Parent DW-02 DONE ở mức thiết kế, WWI-04 vẫn IN_PROGRESS, Phase 1 In Progress. Source evidence và BRD/KPI không thay đổi; 21 runtime tests NOT RUN.

Bằng chứng nghiệm thu DW-02 ngày 2026-11-15: B1–B8 Approved — Logical Policy; B9 Pending — Physical Implementation và numerical thresholds chuyển DW-03 với gate trước conversion/Certified publication. E Assessment ghi 19 required design criteria PASS, runtime execution NOT APPLICABLE/21 tests NOT RUN; 502 local links/0 broken, 82 protected files và 56 attribute rows/bốn fact rows/Bus giữ nguyên, secret/diff/scope checks đạt. Chỉ E/DW-02 đóng theo quyền Owner; WWI-04/Phase 1 In Progress, DW-03A/B/C và DW-04 TODO.

## DW-03A Stage 1 — Discovery & Design Proposal (lịch sử trước logical approval)

Owner giao Stage 1 ngày 2026-11-15 sau DW-02 design acceptance. DW-03A IN_PROGRESS; [work plan](docs/data-models/wwi-dw-03a-work-plan.md), [Full/Raw proposal](docs/data-models/wwi-dw-03a-full-raw-design-proposal.md), [Decision Register](docs/data-models/wwi-dw-03a-decision-register.md), [Assessment](docs/data-models/wwi-dw-03a-assessment.md) là hồ sơ review. A01–A06 đều PROPOSED — PENDING PROJECT OWNER APPROVAL; B9 physical pending, numerical gates chưa tự chọn. Final design acceptance NOT PERFORMED, runtime tests NOT RUN. Chỉ thiết kế, không stage/commit/push hoặc triển khai. DW-03B/C và DW-04 TODO; WWI-04/Phase 1 In Progress; DW-01/DW-02 và các phần đã nghiệm thu giữ DONE.

## DW-03A — Owner Logical Approval Milestone, 2026-11-15

Project Owner instruction **“DW-03A — Record Project Owner Logical Design Approvals”** formal approve: **A01/A03/A04/A06 Approved — Logical Policy; A02 Approved — Conditional Logical Policy; A05 Approved — PoC Direction Only (F2)**. [Decision Register](docs/data-models/wwi-dw-03a-decision-register.md) giữ approved scope/authority/date/limits; không còn pending six logical directions. B1–B8/accepted DW-02 giữ nguyên; **B9 Pending Physical Approval**.

[Evidence](docs/data-models/wwi-dw-03a-evidence-approval-readiness.md) section 10 giữ trusted source metadata và SQL-only results: F1 V1 PASS nhưng 4 zero-fraction fixed-width FAIL; F2 14/14 fixtures, 169 comparisons và 18/18 sampled period cells PASS. Section 11 ghi approval hiện hành, không nâng thành DBAPI/PG/runtime PASS. [Work Plan](docs/data-models/wwi-dw-03a-work-plan.md) sections 5–6 giữ tám technical gates G01–G08 và narrow B9-P01–06 plan; gate IDs không là tasks được tự động mở.

**DW-03A IN_PROGRESS**, chưa final acceptance; **DW-03B/C/DW-04 TODO**, **WWI-04/Phase 1 In Progress**. Acceptance criteria/tracker rows không đổi; physical schema/retention/access/capacity, concrete extraction method/proof, driver/PG fidelity và runtime atomicity/recovery còn gates. Installation/dependency versions/profiles cần separate authorization; không database changes/tables/pipeline hoặc bắt đầu B/C. Current instruction cho phép một documentation-only commit sau QA/staged secret/diff checks, không push; historical “không commit” của Stage 1 không là current milestone restriction. [Assessment](docs/data-models/wwi-dw-03a-assessment.md) section 11 tách design approval checklist khỏi runtime criteria và ghi QA thực tế.


## DW-03A final design acceptance / scoped B9 physical approval — 2026-11-15 (lịch sử)

Owner instruction “DW-03A — B9 Physical Approval & Final Design Acceptance Review” cấp B9 physical representation approval và quyền đóng có điều kiện sau mandatory design review/tests/QA. [Assessment](docs/data-models/wwi-dw-03a-assessment.md)§15 ghi14/14 design criteria PASS,không remaining mandatory architectural blocker. **DW-03A DONE — Design**, không runtime/production DONE.

B9 **Approved — Physical Raw Temporal Representation**: verified F2→str/None→bound psycopg→authoritative TEXT/C comparator,exact27/seven digits/NULL/boundaries/sentinel/100ns,secondary derived fields không thay source. [ADR-SCD-05](docs/adr/scd-05-exact-temporal-precision.md)/[backlog](docs/data-models/wwi-dw-02e-work-plan.md) giữ trail logical→pending→PoC→physical approval. A01–A06/B1–B8 unchanged.

Actual rerun12 unit methods/source14/169/18/PG parameters14/persisted15/order169/equality14/ranges5 PASS,raw/versions/image/backend/location ở [Evidence](docs/data-models/wwi-dw-03a-evidence-approval-readiness.md)§15. [G01–G08](docs/data-models/wwi-dw-03a-work-plan.md) có reason/owner/stage/evidence/gate cho mọi deferral; G01full consistency và G02/G06/G08runtime chưa PASS; G07 conceptual sufficient/full DDL-index-retention chưa approve.

**WWI-04/Phase1 IN_PROGRESS,DW-03B/C/DW-04 TODO,Phase2–9 Not Started.** DW-03B ready-for-Owner-task handoff,không tự bắt đầu. Current task authorize one focused commit sau successful acceptance/QA/staged checks,no push; prior “IN_PROGRESS/Pending/no commit” notes là dated history. Source/Raw production không implementation.

## DW-03B Stage 1 — Discovery & Design Proposal, 2026-11-16 (lịch sử)

Owner đã giao task; **DW-03B IN_PROGRESS**, không nghiệm thu/đóng task. [Work plan](docs/data-models/wwi-dw-03b-work-plan.md), [Incremental proposal](docs/data-models/wwi-dw-03b-incremental-design-proposal.md), [INC-01–INC-06 register](docs/data-models/wwi-dw-03b-decision-register.md) và [Stage 1 assessment](docs/data-models/wwi-dw-03b-assessment.md) là hồ sơ review. Sáu decisions đều **PROPOSED — PENDING PROJECT OWNER APPROVAL**; chưa chọn numeric lookback/cadence, confirmation/delete action hoặc physical checkpoint algorithm. Ma trận bao phủ 9 current + 2 physical H, test plan chỉ Planned/NOT RUN.

DW-03A DONE — Design; B9 Approved — Physical Raw Temporal Representation; A01–A06/B1–B8 giữ nguyên; WWI-04/Phase 1 IN_PROGRESS; DW-03C/DW-04 TODO; Phase 2–9 Not Started. Chỉ tài liệu, không source/target/Docker/B9 sandbox changes hoặc implementation; không stage/commit/push. Acceptance criteria của DW-03B giữ nguyên: proposal chưa là approved design.


## DW-03B Stage 2 — Logical Approval & Design Acceptance, 2026-11-16 (mốc trước DW-03C)

Owner task “DW-03B Stage 2 — Owner Logical Approval & Design Finalization” cấp **INC-01–INC-06 Approved — Logical Policy**. [Specification](docs/data-models/wwi-dw-03b-incremental-design-proposal.md) và [Register](docs/data-models/wwi-dw-03b-decision-register.md) chốt mục tiêu **Current-State Convergence** so với verified consistent source state; candidate windows/temporal history không là complete CDC. Full comparison có full source-read cost dù chỉ ghi changed rows. Exact algorithms/U selection, numeric duration/cadence/quality thresholds và physical/runtime mechanisms chưa tự chốt.

[Assessment](docs/data-models/wwi-dw-03b-assessment.md) sections 9–13 ghi mandatory design criteria/QA và conditional acceptance: **DW-03B DONE — Design**. [RG01–RG12](docs/data-models/wwi-dw-03b-work-plan.md) có reason/owner/target/proof/publication blocker, giữ G01–G08/B5. IT01–IT21 **NOT RUN**, production incremental Not implemented yet. DW-03A/B9/A01–A06/B1–B8 không đổi; **DW-03C/DW-04 TODO, WWI-04/Phase 1 IN_PROGRESS, Phase 2–9 Not Started**. Không bắt đầu task tiếp. Current authorization cho một focused documentation commit sau staged QA; không push hoặc DB/Docker/B9 sandbox changes.

Acceptance evidence DW-03B: [DA01–DA16](docs/data-models/wwi-dw-03b-assessment.md) tách design khỏi runtime; 11 complete source contracts, 6 formal INC records, ACK01–06/8 failure cases, full-state/multiset reconciliation và 12 owned runtime deferrals. Tiêu chí test INSERT/UPDATE/DELETE được đáp ứng ở **specification/design đã duyệt**, không test execution PASS. Không tự đóng WWI-04/Phase 1.


## DW-03C Stage 1 — Discovery & Design Proposal, 2026-11-16 (lịch sử trước Stage 2)

Owner đã giao DW-03C **IN_PROGRESS**. [Work plan](docs/data-models/wwi-dw-03c-work-plan.md), [Change Propagation Proposal](docs/data-models/wwi-dw-03c-change-propagation-design-proposal.md), [CP-01–CP-06](docs/data-models/wwi-dw-03c-decision-register.md) và [Assessment](docs/data-models/wwi-dw-03c-assessment.md) là hồ sơ Stage 1. Tất cả CP decisions **PROPOSED — PENDING PROJECT OWNER APPROVAL**; không thay approved DW-01/02/03A/03B/B9 hoặc business scope. Source/model impact, old/new groups, SCD2/fact/mart/publication/recovery và test scenarios chỉ là design proposals.

DW-01/DW-02/DW-03A/DW-03B DONE Design; DW-04 TODO; WWI-04/Phase 1 IN_PROGRESS; Phase 2–9 Not Started. Inherited G01–G08/RG01–RG12/B5 vẫn pending; CP runtime tests NOT RUN, production modules Not implemented yet. Không SQL/DB/Docker/B9 sandbox/code/dependency changes; **không stage/commit/push, không đóng DW-03C hoặc bắt đầu DW-04**.

Stage 1 evidence/coverage không thay final acceptance criteria: header/dim propagation, old/new groups, checkpoint/replay/restate/publication/recovery specifications vẫn cần Owner phê duyệt. DW-03C chưa DONE; không tự chuyển WWI-04/Phase1.


## DW-03C Stage 2 — Owner Logical Approval & Final Design Review, 2026-11-16 (lịch sử trước Stage 3)

Owner đã approve **CP-01–CP-06 — Logical Policy** tại [Register](docs/data-models/wwi-dw-03c-decision-register.md). [Specification](docs/data-models/wwi-dw-03c-change-propagation-design-proposal.md) section10 ghi D1–D4: **D1 Type1 selection reference/mode, D2 analytical publication unit/shared consumer compatibility, D3 revocation/rollback authority còn PENDING OWNER APPROVAL**; D4 full affected-mart rebuild baseline CONFIRMED theo CP-04, không cần approve lại. Six logical approvals không tự resolve D1–D3.

[Assessment](docs/data-models/wwi-dw-03c-assessment.md) sections9–13: design acceptance **PARTIAL**, DW-03C **IN_PROGRESS**; no finalization commit/staging/push. AP01–AP06 logical evidence contracts reviewed, CP-R01–12 và CP-T01–30 được rà; runtime tests **NOT RUN**. G01–G08/RG01–RG12/CG01–10/B5 vẫn gated, không numeric/physical defaults. DW-04 TODO/chưa bắt đầu; WWI-04/Phase1 IN_PROGRESS, Phase2–9 Not Started. Approved DW-01/02/03A/03B/B9/business scope không đổi; không DB/Docker/B9 sandbox/code changes.

Không chuyển DW-03C DONE: acceptance yêu cầu remaining mandatory Owner decisions resolved, hiện D1–D3 chưa approved. Không dùng six CP approvals hoặc static QA để chốt new rules. Giữ nguyên DW-03C row IN_PROGRESS/DW-04 TODO và các accepted task statuses.


## DW-03C Stage 3 — Final Design Acceptance, 2026-11-16 (lịch sử trước DW-04)

Owner task “DW-03C Stage 3 — Owner D1–D3 Approvals & Final Design Acceptance” cấp **D1/D2 Approved — Logical Policy, D3 Approved — Governance Policy; D4 Confirmed**. [Register](docs/data-models/wwi-dw-03c-decision-register.md) ghi exact scope/authority; [Specification](docs/data-models/wwi-dw-03c-change-propagation-design-proposal.md) tích hợp explicit frozen four-anchor selected set, dependency-complete subject/view+joint consumer manifest và DQ/Owner/Operator lifecycle governance. Không phát hiện conflict với accepted DW-02; no Type2/source-measure/history-meaning changes.

[Final Assessment](docs/data-models/wwi-dw-03c-assessment.md) sections14–18 ghi **18/18 mandatory design criteria PASS → DW-03C DONE — Design** theo conditional authority sau actual QA, không runtime approval. Stage1/2/Pending/15PASS+3PARTIAL evidence giữ history. CP-01–06 vẫn Approved — Logical Policy; CP-T01–30 NOT RUN; G01–08/RG01–12/CG01–10/B5 và per-action evidence còn gates trước relevant normal publication/use. Không tự revoke/reinstate/rollback hoặc implement. DW-04 TODO/ready-for-Owner-task, WWI-04/Phase1 IN_PROGRESS,Phase2–9 Not Started. Current authority cho one focused docs commit sau staged checks, no push/remote/DB/Docker/B9 changes; không bắt đầu DW-04.

DW-03C acceptance evidence: six CP Logical approvals, D1/D2 Logical+D3 Governance approvals, D4 confirmed,11 source/16 model/4 fact/6 mart/AP6/recovery12/test30 coverage và final18 criteria/QA PASS. Source state/registry/SCD/reconciliation/generation/consumer/runtime gates vẫn required, không đánh dấu tests hoặc parent task DONE. DW-04 chỉ được start khi Owner giao riêng.

## DW-04 — Design Acceptance & Implementation Handoff, 2026-11-16 (lịch sử trước Owner closure)

**DW-04 DONE — Design Acceptance**,20/20 criteria và static/staged QA PASS. [Assessment](docs/data-models/wwi-dw-04-assessment.md), [Implementation Gate Register](docs/data-models/wwi-implementation-gate-register.md) và [Readiness/Handoff](docs/data-models/wwi-implementation-readiness-handoff.md) đối chiếu11 source populations/16 models/22 KPI/12 BRD,31 original gates,18 readiness components và72 planned tests NOT RUN. Approved DW-01/02/03A/03B/03C/B9/INC/CP/D1–D3 giữ nguyên; không thêm business/physical defaults.

Design acceptance khác implementation/operational readiness. WWI-04/Phase1 **IN_PROGRESS**, Phase2–9 **Not Started**; production modules **Not implemented yet**. Không tự bắt đầu task/phase sau; chỉ task tài liệu và một focused commit sau QA theo Owner DW-04 authority, không push/remote/DB/Docker/B9 changes.

DW-04 acceptance evidence:20/20 mandatory design criteria PASS;11 source/16 model/22 KPI/12 BRD coverage,31 original gates/18 components/M1–M9/72 NOT RUN scenarios;128 visible files/122 Markdown/946 local links/0 broken,115 protected hashes unchanged,secret/size/scope/staged/diff checks PASS. Conditional Owner authority chỉ nghiệm thu DW-04 — Design Acceptance; original acceptance criteria/dependencies giữ nguyên. “Owner nghiệm thu WWI-04” là parent overall review checkpoint, không tự đóng parent bằng subtask acceptance. Candidate M1–M9 trong Handoff không thay task IDs hoặc dependencies WWI-05–16.

## Owner Closure & Phase 2 Authorization — 2026-11-16 (Checkpoint A, trước verification)

Phase 0 **Completed**; Phase 1 **Completed — Requirements & Source Design**; WWI-02/03 **DONE**, WWI-04 **DONE — Design**. DW-01/02/03A/03B/03C **DONE — Design**; DW-04 **DONE — Design Acceptance**. Phase 2 **IN_PROGRESS — Authorized**, giới hạn WWI-05/M1A **IN_PROGRESS — Authorized**; WWI-05 chưa hoàn tất. M2 trở đi và Phase 3–9 **Not Started**. Production modules **Not implemented yet**; chỉ B9 isolated PoC có evidence lịch sử.

[Owner closure/authorization](docs/architecture/wwi-phase-1-closure-approval.md) là authority mới cho APPROVAL-01–05; nguồn là task trực tiếp của Project Owner, không chữ ký điện tử/hệ thống approval bên ngoài. Checkpoint A ghi nhận và commit sau QA, rồi Checkpoint B mới thực hiện M1A chỉ đọc. G01–08/RG01–12/CG01–10/B5 giữ nguyên31 entries;72 runtime scenarios NOT RUN. Approval không cho DML/DDL, infrastructure/identity/config changes, install dependencies, pipeline, M2/M3 hoặc push. Các status/no-start notes của DW-04 phía trên là lịch sử trước approval này.

### WWI-05 verification checkpoint

| ID | Description / module | Dependencies | Acceptance criteria | Status |
| --- | --- | --- | --- | --- |
| M1A | Local Readiness & Secure Connection-Contract Verification (DONE — Verification Checkpoint) — infrastructure/data-sources/storage/docs | WWI-04/Phase1 closure APPROVAL-01/02; Phase2/task APPROVAL-03/04; Checkpoint A QA+commit | Inventory, secure connectivity/identity, target classification, contracts/evidence/handoff và QA đầy đủ; missing prerequisites ghi BLOCKED/NOT RUN; checkpoint completion khác operational readiness | DONE |

M1A là child checkpoint của WWI-05, không thay official WWI-05 Definition of Done. Authorization không làm WWI-05 DONE; M2 và các milestone sau NOT STARTED.

## WWI-05 / M1A — Verification Report, 2026-11-16 (hiện hành)

M1A **DONE — Verification Checkpoint**, không operational acceptance: secure developer SQL/TLS và11 bounded source reads PASS; tested identity có sysadmin/write permissions nên FAIL suitability, approved extraction profile/consistency/Raw target/reproducibility còn BLOCKED. WWI-05/Phase2 **IN_PROGRESS**; WWI-04 DONE — Design, Phase1 Completed theo Owner approval; M2/M3+ NOT STARTED.

[Environment Report](docs/architecture/wwi-m1a-environment-readiness.md), [Secure Contract](docs/architecture/wwi-secure-connection-contract.md), [26-check Evidence Matrix](docs/architecture/wwi-m1a-gate-evidence.md), [M1A Handoff](docs/architecture/wwi-m1a-handoff.md). Metadata/connectivity là subset, không nghiệm thu IT01 hoặc72 scenarios;31 original gates giữ nguyên. Không source/target writes/infrastructure/identity/dependency changes, B9 sandbox giữ nguyên. Mọi next remediation/provision cần Owner giao task riêng; không tự M2/M3/push.

## WWI-05 / M1B — Source Identity & Consistency Planning, 2026-11-16 (trước OD01–03)

Task Owner M1B chỉ cho review/metadata SELECT và documentation commit sau QA. M1B **DONE — Planning Review** sau acceptance/QA; không identity/grant/config/source/infrastructure changes. [Assessment](docs/architecture/wwi-m1b-assessment.md), [Identity proposal](docs/architecture/wwi-source-identity-proposal.md), [Consistency proposal](docs/architecture/wwi-source-consistency-proposal.md), [DBA/Owner checklist](docs/architecture/wwi-source-dba-owner-checklist.md).

G01/G02/RG01/RG02/CG08 vẫn Pending/BLOCKED; current developer identity FAIL suitability. Recommended static no-writes window A và identity package **PROPOSED — Pending Owner/DBA Approval**, B consistent copy fallback cần separate approval, không tạo copy. M1B planning không operational PASS, không đóng WWI-05/Phase2; M1A DONE Verification/Phase1 Completed/WWI-04 DONE Design giữ nguyên. Original31 gates/72 NOT RUN scenarios/B9 không đổi; M1C/M2/M3 chưa được giao.

| ID | Description / module | Dependencies | Acceptance criteria | Status |
| --- | --- | --- | --- | --- |
| M1B | Secure Source Identity & Consistency Readiness — docs/source-security review (DONE — Planning Review) | M1A verification evidence,Owner task M1B,DW-03A/B accepted policies | Required privileges và LP tests;evaluate A/B consistency,preferred option PROPOSED,Owner/DBA checklist,accurate gates và documentation QA;không source operational PASS | DONE |

M1B child checkpoint chỉ planning; G01/G02 runtime closure cần approved identity/method và actual proof. WWI-05 IN_PROGRESS,không tự M1C/M2/M3.

## M1B-Approval — Owner Direction & Execution Preparation,2026-11-16

[M1B-OD01–03](docs/architecture/wwi-m1b-owner-decisions.md): dedicated non-admin Windows/minimum object SELECT direction APPROVED;preferred Option A static no-writes APPROVED;Codex chỉ documentation/scripts/test preparation vàlocal static QA/commit. Actual names/grants/window/operator/execution approval chưa có. [DBA scripts](data-sources/security/README.md) PREPARED,NOT RUN;không auto-execute hoặcsource connection ởtask này.

WWI-04 DONE Design,Phase1 Completed,Phase2/WWI-05 IN_PROGRESS,M1A DONE Verification,M1B DONE Planning Review;**M1B-Approval IN_PROGRESS tớiOwner acceptance**,M1C/M2/M3 NOT STARTED. G01/G02 Pending/BLOCKED,31 original gates/72 NOT RUN scenarios vàB9/INC/CP/D1–D4 unchanged. Không administrative/source/settings/infra/dependency/ingestion changes hoặcpush.

| ID | Description / module | Dependencies | Acceptance criteria | Status |
| --- | --- | --- | --- | --- |
| M1B-Approval | Owner Decision Recording & DBA Execution Preparation — docs/source-security | M1B DONE Planning Review,Owner OD01–03 task | Exact approval record,11-object prepared gated setup/read-only verify,OptionA proof procedure,EX01–04 handoff,static QA/commit;DBA/Owner package acceptance còn pending,no G01/G02 runtime PASS | IN_PROGRESS |

## WWI-05 / EX01 — Windows Identity Provisioning & Verification

Owner task ngày2026-11-16 approve Windows principal `DESKTOP-OBDFK6B\wwi_extract`, future DB-user name `wwi_extract`; Project Owner là OS Operator và local DBA. [Authority](docs/architecture/wwi-m1b-owner-decisions.md#7-owner-ex01-authorization--2026-11-16), [EX01 evidence/handoff](docs/architecture/wwi-ex01-windows-identity-evidence.md). Approval không cho EX02 SQL security changes hoặc phase transition; các pending-name notes ở milestones trước là lịch sử.

| ID | Description / module | Dependencies | Acceptance criteria | Status |
| --- | --- | --- | --- | --- |
| EX01 | Windows Extraction Identity Provisioning & Verification — OS identity/docs | M1A/M1B evidence, prepared package commit a2f0ae2, exact Owner EX01 authority, approved machine, secure OS Operator input và provisioning privileges | Exact local account/SID/enabled/password-required được verify; groups/non-admin/effective logon/profile phù hợp; sanitized evidence và QA; không unrelated OS/SQL changes hoặc credential exposure | DONE |

**EX01 DONE — OS Identity Verification** theo conditional Owner final-acceptance task sau mandatory criteria/final QA PASS. [E22–E29/acceptance](docs/architecture/wwi-ex01-windows-identity-evidence.md#9-final-ex01-acceptance--os-identity-verification), [EX01-R01 authority/result](docs/architecture/wwi-m1b-owner-decisions.md#8-ex01-r01-owner-remediation-record-và-final-review-authority): PasswordRequired=True được independent read-back Get-LocalUser/CIM, same SID `S-1-5-21-2164258108-3044412014-540060861-1007`, Enabled/Local/profile/groups không đổi; Owner supplied target whoami /user + đủ năm non-elevated privilege entries và successful runas. E01–E21/BLOCKED/PasswordRequired=False giữ historical evidence, không current findings. **EX02 BLOCKED / Pending Authorization; G02 Pending Runtime Verification; G01 Pending Source Consistency Proof; WWI-05/Phase2 IN_PROGRESS; M1B-Approval không tự DONE; M1C/M2/M3 NOT STARTED.** Không SQL security/pipeline acceptance; current task chỉ read-only inspection/docs/one local commit sau QA, không password hoặc OS/SQL changes/push.

## WWI-05 / EX02 — Populated Execution Package Review

| ID | Description / module | Dependencies | Acceptance criteria | Status |
| --- | --- | --- | --- | --- |
| EX02 | Local SQL read-only identity setup — data-sources/security/docs | EX01 DONE; explicit Owner SQL execution authority, source/operator/account checks | Guarded new-only setup: exact principal/SID, CONNECT SQL + database CONNECT +11 object SELECT, no broad/admin grants; fresh extractor/TLS/permission evidence. Protected staging/execution-hash manifest không mandatory cho MVP | REVIEW |

**EX02 = Pending Execution Authorization** (tracker REVIEW,không DONE). [Manifest](data-sources/security/wwi_extraction_execution_manifest.json) và [review evidence](docs/architecture/wwi-source-dba-owner-checklist.md#12-ex02-populated-package--final-authorization-review) pin proposal WWI05-EX02-20261117-01,PC/SID-1001 operator proposed,target SID-1007 và9 current+2 H. Scripts vẫn flags0/DO_NOT_EXECUTE;guarded/activated hashes khác nhau vàđúng5 activation edits được pin,không enabled file/SQL setup/verify đã chạy. Owner đã cho phép riêng empty negative-test database CREATE và DROP sau actual tests;Retail_EX02_DeniedAccess_20261117 tồn tại chờ test,cleanup đúng GUID/empty/dependencies sau evidence,không xóa trước test. EX01 DONE,G02 BLOCKED,G01 Pending Consistency Proof,WWI-05/Phase2 IN_PROGRESS,M1B-Approval không tự DONE,M1C/M2/M3 NOT STARTED. No source business/security writes,protected staging/ACL changes/ingestion/push.

## WWI-05 / EX02-S1 — Protected Staging ACL Preparation

| ID | Description / module | Dependencies | Acceptance criteria | Status |
| --- | --- | --- | --- | --- |
| EX02-S1 | DEFERRED — OPTIONAL SECURITY HARDENING; historical ACL preparation package giữ nguyên để tham khảo | MVP-SIMPLIFICATION-01; chỉ revisit khi Owner giao production-oriented hardening | Không MVP blocker; không execute ACL scripts/tạo staging/sửa Code hoặc repo permissions. Historical preparation evidence tại assessment/commit f1d1fc4 giữ traceable | DEFERRED |

[Assessment](docs/architecture/wwi-ex02-s1-acl-assessment.md) và [package](data-sources/security/staging/README.md) giữ historical preparation tests/ancestor findings/hashes tại f1d1fc4. Theo MVP-SIMPLIFICATION-01, không cần resolve ancestor/inheritance/staging manifest để làm local MVP; revisit hardening cần task riêng. Không apply ACL/tạo staging. EX01 DONE,EX02 pending SQL execution,G02 detailed chưa PASS,G01 consistency pending,WWI-05 IN_PROGRESS; Full Load/runtime milestones chưa bắt đầu.
