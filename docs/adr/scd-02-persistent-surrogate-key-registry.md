# ADR-SCD-02 — Persistent Surrogate Key Registry (D02)

- **Status:** Accepted — Architecture Direction.
- **Decision Date / Authority:** 2026-11-14 / Project Owner.
- **Scope:** Phase 1.6 / WWI-04 / DW-02C/D. **Implementation:** Not Started.
- **Liên quan:** [ADR index](README.md), [Identity/SK design](../data-models/wwi-scd-identity-key-design.md).

## Quyết định và Approved Design Constraints

Persistent Registry cấp và quản lý **Opaque SK** cho analytical versions của Customer/Product. Natural key, source occurrence identity, analytical version identity và warehouse SK là các khái niệm riêng. Không dùng ROW_NUMBER theo thời gian làm durable SK; không mặc định CustomerID + ValidFrom unique.

Registry phải có stable mapping, backup/recovery, version supersession và integrity validation. SK stability chỉ được claim khi registry/identity evidence đầy đủ. Boundary corrections, split/merge và late corrections phải có rekey/restatement policy; không đổi nghĩa SK đang referenced.

## Lý do và hệ quả

Persistent mapping giúp replay và rebuild có kiểm soát bảo toàn references. Source period/end có thể thay đổi hoặc có duplicate start; không thể thay registry bằng timestamp sorting. Source versions có thể nhiều hơn analytical episodes.

## Các phương án đã xem xét

Deterministic hash/ordinal-derived SK không được chọn làm kiến trúc cấp key hiện hành. Hash có thể hỗ trợ lookup/equality với collision checks, không là chứng cứ uniqueness hoặc durable SK thay registry.

## Logical policy approval và Pending Implementation Details

B1/B2/B8 đã **Approved — Logical Policy** ngày 2026-11-15: boundary-only giữ identity/SK khi unique continuity; split/merge tạo replacement episode identities và explicit supersession. Recovery phải giữ registry/version evidence/lineage/supersession/publication state tương thích, prove continuity trước equivalent rebuild; thiếu evidence là recovery limitation, không cấp keys rồi assume equivalent. Reinsert chỉ có new incarnation khi evidence đủ, thiếu giữ Ambiguous. Registry schema/allocator/encoding, backup tooling/schedule và execution procedures chuyển DW-03 trước runtime. [Final Specification](../data-models/wwi-final-scd2-design-specification.md), [backlog](../data-models/wwi-dw-02e-work-plan.md) ghi approval boundary.
