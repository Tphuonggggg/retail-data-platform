# ADR-SCD-06 — Controlled Unresolved Publication & Certified Mart Gate (D06)

- **Status:** Accepted — Architecture Direction.
- **Decision Date / Authority:** 2026-11-14 / Project Owner.
- **Scope:** Phase 1.6 / WWI-04 / DW-02C/D. **Implementation:** Not Started.
- **Liên quan:** [ADR index](README.md), [Lookup/publication specification](../data-models/wwi-scd-historical-lookup-design.md).

## Quyết định và Approved Design Constraints

Core facts được giữ unresolved historical dimension references **có kiểm soát**, giữ source population và reconciliation. Certified analytical marts phải qua quality/coverage gates đã được xác định và phê duyệt. Integrity multi-match do history/identity/interval phải chặn publication ở scope bị ảnh hưởng.

Phân biệt missing reference, historical coverage gap, date-only ambiguity, precision error và integrity violation. Unknown/unresolved không là successful historical match. Không silent fallback current/earliest, không drop source fact chỉ vì unresolved dimension lookup. Marts không được claim historical grouping đầy đủ khi chưa qua coverage gate.

## Lý do và hệ quả

Tách khả năng bảo toàn detail/population khỏi mức chứng nhận analytical attribution. Core vẫn phải báo coverage và lỗi; không dùng unknown member để che invalid/multi-match hoặc làm certified gate tự pass. Buyer/Bill-to invoice roles giữ theo source header.

## Các phương án đã xem xét

Drop unresolved facts hoặc fallback current/earliest: không chọn. Chặn mọi core facts chỉ do thiếu lịch sử: không phải default direction được duyệt; quarantine/hold vẫn dành cho input invalid/incomplete hoặc integrity-invalid scopes theo policy.

## Logical policy approval và Pending Implementation Details

B4/B5 đã **Approved — Logical Policy** ngày 2026-11-15: Core giữ otherwise-valid U với source population/measures/NK/role/reason/lineage; I block affected scope. Chọn **Tiered Certification** theo KPI/view dependencies, đánh giá cả row và measure/value coverage; enterprise KPI có thể chứng nhận riêng, historical breakdown thiếu coverage là Uncertified. Lookup R/U/I khác certification Uncertified/Certified. Numeric thresholds được Owner cho phép chuyển DW-03 nhưng bắt buộc phê duyệt trước mọi Certified publication; không default 100%. Member/reserved SK/reason encoding, exact publication mechanism và runtime tests vẫn pending. [Final Specification](../data-models/wwi-final-scd2-design-specification.md), [backlog B4/B5](../data-models/wwi-dw-02e-work-plan.md) ghi chi tiết.
