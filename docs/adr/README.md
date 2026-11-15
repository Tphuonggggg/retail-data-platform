# adr

- **Purpose:** Ghi quyết định kiến trúc và phạm vi có owner, lý do, ảnh hưởng và Open Decisions.
- **Owned files / responsibilities:** [WWI source migration ADR](wwi-source-migration.md) ghi quyết định chuyển nguồn tại thời điểm ban hành; bảng dưới ghi các SCD decisions hiện hành. KPI/BRD và logical grains đã được duyệt theo các hồ sơ tương ứng; physical schema và incremental policies chưa hoàn tất.
- **Parent module:** [docs](../README.md).
- **Status:** ADR chuyển nguồn đã ghi; schema/pipeline: Not Implemented. Not implemented yet.

## SCD ADR index — Accepted Architecture Direction

Project Owner phê duyệt ngày **2026-11-14**, phạm vi Phase 1.6 / WWI-04 / DW-02C/D; implementation **Not Started**. Các file tuân theo cấu trúc quyết định/lý do/hệ quả/phương án/Open Decisions của ADR hiện có. `D01–D06` là mã trong task, map tới `ADR-SCD-01–06` dưới đây. Không nhầm với bộ nguyên tắc `SCD-01–07` trước đó: ví dụ SCD-01 nói về Customer, ADR-SCD-01 nói về Product; các nguyên tắc trước không bị thay đổi.

| Task decision | ADR | Trạng thái | Technical gate |
| --- | --- | --- | --- |
| D01 | [ADR-SCD-01 Product tracking](scd-01-product-attribute-tracking.md) | Accepted — Architecture Direction | Type1 correction scope; reference contracts |
| D02 | [ADR-SCD-02 Persistent registry](scd-02-persistent-surrogate-key-registry.md) | Accepted — Architecture Direction; B1/B2/B8 logical approved | Allocator/backup/execution mechanisms |
| D03 | [ADR-SCD-03 Whole-day consensus](scd-03-whole-day-analytical-consensus.md) | Accepted — Architecture Direction | Day domain, exact coverage proof, validity evidence |
| D04 | [ADR-SCD-04 Reconciled cutover](scd-04-reconciled-hybrid-cutover.md) | Accepted — Architecture Direction | Generation boundary/bridge/recovery procedures |
| D05 | [ADR-SCD-05 Exact precision](scd-05-exact-temporal-precision.md) | Accepted — Architecture Direction | Physical encoding, round-trip/interval tests |
| D06 | [ADR-SCD-06 Unresolved & mart gates](scd-06-controlled-unresolved-publication.md) | Accepted — Architecture Direction; B4/B5 logical approved | Physical members/reason encoding; numerical gates before Certified publish |

**Accepted Architecture Decision** ghi lựa chọn Owner đã duyệt. **Approved Design Constraint** là invariant bắt buộc từ quyết định đó. **Proposed Technical Policy** là phương án vận hành chưa được duyệt. **Pending Implementation Detail** là thuật toán/schema/configuration/runtime test chưa thực hiện. Nghiệm thu C/D ở mức tài liệu không biến hai loại cuối thành Approved. [DW-02E plan/backlog](../data-models/wwi-dw-02e-work-plan.md) và [E assessment](../data-models/wwi-dw-02e-assessment.md) ghi review E1–E5; B1–B8 Approved — Logical Policy ngày 2026-11-15, B9 Pending — Physical Implementation; E/DW-02 design DONE sau QA theo quyền đóng có điều kiện ngày 2026-11-15, runtime chưa bắt đầu. Tiered Certification đã chọn; numerical thresholds được Owner defer tới DW-03 trước mọi Certified publication. Các gate trong bảng là implementation/evidence requirements, không phủ nhận logical approval.
