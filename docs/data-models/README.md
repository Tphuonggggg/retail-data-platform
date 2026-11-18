# data-models

## 1. Overview

Tài liệu khảo sát và thiết kế dữ liệu nguồn WWI thuộc [docs](../README.md). Không chứa schema hoặc pipeline đã triển khai.

## 2. Purpose

Ghi metadata, profile, quan hệ nguồn và source contracts làm đầu vào cho các quyết định sau này.

## 3. Scope

Chín bảng MVP thuộc Sales/Invoicing, Customer và Inventory; Purchasing chỉ là dependency ở các phép đối soát đã nêu. KPI Phase1.5, DW-01 logical models và DW-02/03 logical policies đã nghiệm thu; scoped B9 physical temporal representation đã duyệt. Concrete physical schema/algorithms/values/runtime proof còn gates.

## 4. Responsibilities

Phân biệt constraint nguồn với snapshot quan sát, ghi SQL evidence và giới hạn suy luận; dẫn chiếu cột/datatype về dictionary, không duy trì bản sao trùng chức năng.

## 5. Inputs

SQL Server WWI chỉ đọc, [PROJECT_SCOPE.md](../../PROJECT_SCOPE.md), [TASKS.md](../../TASKS.md) và quyết định của Project Owner.

## 6. Outputs

- DW-04 hiện hành (2026-11-16): [Overall Assessment](wwi-dw-04-assessment.md), [Implementation Gate Register](wwi-implementation-gate-register.md), [Readiness & Milestone Handoff](wwi-implementation-readiness-handoff.md). DONE — Design Acceptance sau20/20 criteria/static/staged QA;31 original gates pending implementation,72 runtime scenarios NOT RUN; không production readiness/phase transition.

- Phase 1.1: [database inventory](wwi-database-inventory.md), [metadata dictionary](wwi-metadata-dictionary.md), [temporal/index assessment](wwi-temporal-index-assessment.md), [metadata queries](wwi-metadata-queries.md), [assessment](wwi-phase-1-1-assessment.md).
- Phase 1.2: [profiling tổng hợp](wwi-data-profiling.md), [Sales](wwi-sales-profiling.md), [Customer/temporal](wwi-customer-temporal-profiling.md), [Inventory/integrity](wwi-inventory-integrity-profiling.md), [profiling SQL](wwi-profiling-queries.md), [assessment](wwi-phase-1-2-assessment.md).
- Phase 1.3: [relationships](wwi-source-relationships.md), [source ERD](wwi-source-erd.md), [business data flow](wwi-business-data-flow.md), [relationship SQL](wwi-relationship-validation-sql.md), [assessment](wwi-phase-1-3-assessment.md).
- Phase 1.4: [source contracts](wwi-source-contracts.md), [extraction matrix](wwi-extraction-requirements-matrix.md), [assessment](wwi-phase-1-4-assessment.md); [raw requirements](../requirements/wwi-raw-layer-requirements.md) và [validation matrix](../requirements/wwi-source-validation-matrix.md) thuộc requirements.
- DW-03B Stage 2 (2026-11-16): [work plan/runtime gates](wwi-dw-03b-work-plan.md), [logical incremental specification](wwi-dw-03b-incremental-design-proposal.md), [INC-01–INC-06 register](wwi-dw-03b-decision-register.md), [final assessment](wwi-dw-03b-assessment.md). DW-03B DONE — Design theo conditional acceptance/QA; six INC Approved — Logical Policy; physical/numeric/runtime gates pending, IT01–21 NOT RUN.

- DW-03C Stage3 (2026-11-16): [work plan/gates](wwi-dw-03c-work-plan.md), [final specification](wwi-dw-03c-change-propagation-design-proposal.md), [approval register](wwi-dw-03c-decision-register.md), [final assessment](wwi-dw-03c-assessment.md). DW-03C DONE — Design sau18/18 criteria/QA; CP/D1/D2 Logical+D3 Governance Approved, D4 confirmed. Physical/runtime gates pending, CP-T01–30 NOT RUN.

## 7. Dependencies

DW-03A **DONE — Design**, scoped **B9 Approved — Physical Raw Temporal Representation** theo Owner2026-11-15. [Work Plan/G01–G08](wwi-dw-03a-work-plan.md),[Full/Raw Design](wwi-dw-03a-full-raw-design-proposal.md),[Decision Register](wwi-dw-03a-decision-register.md),[Final Assessment](wwi-dw-03a-assessment.md)§15,[Evidence](wwi-dw-03a-evidence-approval-readiness.md)§15 và [ADR-SCD-05](../adr/scd-05-exact-temporal-precision.md) giữ current authority. F2/str-None/parameterized psycopg/TEXT/C exact comparator approved;actual source14/169/18/PG14/15/order169/equality14/ranges5,12 unit methods PASS. A01–A06/B1–B8 unchanged;physical full schema/index/retention/security/adapters/runtime/publication còn gates. Historical Pending/BLOCKED notes giữ theo milestones; không production pipeline.

[ADR index](../adr/README.md) là nguồn quyết định D01–D06. [DW-02E Work Plan](wwi-dw-02e-work-plan.md) giữ backlog B1–B9; [Final SCD2 Specification](wwi-final-scd2-design-specification.md) và [DW-02E Assessment](wwi-dw-02e-assessment.md) ghi kết quả review E1–E5, B1–B8 logical approved, E/DW-02 design DONE sau QA; B9 ở mốc DW-02E còn pending; sau đó DW-03A phê duyệt scoped physical temporal representation như trên, không production runtime.


DW-02C/D: [Source Identity/SK/Precision](wwi-scd-identity-key-design.md), [Historical Lookup & Unresolved](wwi-scd-historical-lookup-design.md), [Forward Tracking/Cutover/Recovery](wwi-scd-forward-cutover-design.md), [Assessment/Test Matrix](wwi-dw-02cd-assessment.md). C/D đã nghiệm thu theo sáu ADR Accepted Architecture Direction; B1–B8 được duyệt ở mức logic ngày 2026-11-15; physical procedures và numerical thresholds pending, runtime NOT RUN.


DW-02A/B: [SCD Attribute Classification](wwi-scd-attribute-classification.md), [Temporal/Precision/Lookup Assessment](wwi-scd-temporal-assessment.md), [SELECT Evidence](wwi-scd-temporal-evidence.md), [Assessment](wwi-dw-02ab-assessment.md). Đây là phần khảo sát/proposal bổ sung, không thay dictionary nguồn, profiling cũ hoặc DW-01 đã nghiệm thu.

Phase 1.6/DW-01: [Logical DW Design và Bus Matrix](wwi-logical-dw-design.md), [Fact/Dimension Dictionary](wwi-fact-dimension-dictionary.md), [Logical Mapping](wwi-logical-source-to-target.md), [Star Schemas](wwi-logical-star-schemas.md), [Change Impact Matrix](wwi-change-impact-matrix.md), [Logical Marts](wwi-logical-data-marts.md), [Assessment](wwi-dw-01-assessment.md). Các tài liệu đích này không thay source ERD/dictionary hiện có.

Metadata Dictionary và profiling trước relationship contract; relationship contract trước source contracts. Các quyết định WWI-03/04 cần phê duyệt riêng trước schema/pipeline.

## 8. Technology

Markdown, Mermaid và SQL Server `SELECT`/catalog queries để khảo sát. PostgreSQL warehouse là mục tiêu dự án, chưa có object từ module này.

## 9. Folder Structure

Thư mục này lưu README và các tài liệu `wwi-*.md` theo phase; không chứa dữ liệu nguồn hoặc code.

## 10. Execution

Các truy vấn đọc/tái kiểm chứng nằm trong tài liệu SQL tương ứng. Không có lệnh chạy module hay extraction trong repository: Not implemented yet.

## 11. Tasks

WWI-02/03 `DONE` ở mức tài liệu. Phase 1.6/WWI-04 `DONE — Design`, DW-02 `DONE` ở mức thiết kế, DW-01 và DW-02A/B `DONE`; hồ sơ A/B ghi SCD-01–07 Approved Principles; sáu ADR sau đó chốt D01–D06, B1–B8 logical policies đã duyệt; physical procedures/thresholds pending. C/D DONE ở mức thiết kế sau targeted review; E DONE ở mức thiết kế sau QA theo quyền nghiệm thu có điều kiện ngày 2026-11-15; DW-03A DONE — Design, scoped B9 physical representation approved; DW-03B DONE — Design theo Owner Stage 2 conditional acceptance ngày 2026-11-16, DW-03C DONE — Design sau Stage3 approvals/QA, DW-04 DONE — Design Acceptance sau20/20 criteria/static/staged QA. Theo dõi [TASKS.md](../../TASKS.md).

## 12. Testing Strategy

Đối chiếu SQL evidence với metadata/profile, kiểm link Markdown, rà secret/diff và nêu rõ câu nào chỉ là Proposed. Kiểm thử ingestion/warehouse: Not implemented yet.

## 13. Acceptance Criteria

Mỗi kết luận quan trọng có evidence hoặc nhãn Unverified/Proposed; đủ chín bảng MVP ở Phase 1.4; không giả định KPI, SCD2, incremental hay daily balance chưa duyệt.

## 14. Current Status

Phase 0 **Completed**; Phase 1 **Completed — Requirements & Source Design**; WWI-02/03 **DONE**, WWI-04 **DONE — Design**. DW-01/02/03A/03B/03C **DONE — Design**; DW-04 **DONE — Design Acceptance**. Phase 2 **IN_PROGRESS — Authorized**, giới hạn WWI-05 **IN_PROGRESS**, M1A **DONE — Verification Checkpoint**; WWI-05 chưa hoàn tất. M2 trở đi và Phase 3–9 **Not Started**. Production modules **Not implemented yet**; chỉ B9 isolated PoC có evidence lịch sử. [Owner approval](../architecture/wwi-phase-1-closure-approval.md).

[M1A Handoff](../archive/pre-reset/wwi-m1a-handoff.md) ghi verification hoàn tất nhưng operational prerequisites còn blocked; không thay accepted data models/31 gates/72 scenarios.
