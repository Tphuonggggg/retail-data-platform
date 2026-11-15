# ADR-SCD-01 — Product Attribute Tracking (D01)

- **Status:** Accepted — Architecture Direction.
- **Decision Date / Authority:** 2026-11-14 / Project Owner.
- **Scope:** Phase 1.6 / WWI-04 / DW-02C/D. **Implementation:** Not Started.
- **Nguồn phê duyệt:** ADR và task Owner cung cấp; xem [ADR index](README.md).

## Quyết định và Approved Design Constraints

Tập Type 2 của dim_product chỉ gồm **UnitPackageID, OuterPackageID, QuantityPerOuter**. Các analytical attributes còn lại dùng Type 1 **nếu đã được duyệt đưa vào dimension**. Không tự đưa thuộc tính Excluded hoặc technical/audit metadata thành Type 1; CustomFields/Tags tiếp tục ngoài analytical scope. NK và metadata không là Type1 descriptive attributes.

Chỉ tracked Type2 attributes kích hoạt analytical historical version; Type1 changes không tự tạo SCD2 episode. Không thay transaction UnitPrice bằng master product price. Type1 correction lên các versions hiện có phải được đánh giá impact trước khi triển khai.

## Lý do và hệ quả

Tập tracking nhỏ phục vụ packaging, tránh tạo versions do source changes không có analytical requirement. Grouping fields như Brand/Size/ColorID/IsChillerStock không còn là Type2 candidates trong direction hiện hành; nếu được admitted vào dimension thì theo Type1 direction. Source history thay đổi Tags/CustomFields không tự tạo analytical episodes.

## Các phương án đã xem xét

Track toàn bộ source columns hoặc toàn bộ grouping candidates: không chọn. Giữ tất cả current-only: không đáp ứng packaging-history direction đã duyệt.

## Logical policy approval và Pending Implementation Details

B7 đã **Approved — Logical Policy** ngày 2026-11-15: Type1 correction phải có impact scope riêng, audit/reconciliation/rollback; AccountOpenedDate correction không tự tạo SCD2 episode. Không chọn mặc định current/all-version overwrite hoặc thêm admitted attributes. Mode và exact selected-version scope phải được review trong correction plan trước execution; reference label contracts, schema/algorithm/datatype vẫn pending. [Final SCD2 Specification](../data-models/wwi-final-scd2-design-specification.md) ghi contract hiện hành; metadata/observations không là runtime tests.
