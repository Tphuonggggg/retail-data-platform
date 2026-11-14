# ADR-SCD-05 — Exact Temporal Precision (D05)

- **Status:** Accepted — Architecture Direction.
- **Decision Date / Authority:** 2026-11-14 / Project Owner.
- **Scope:** Phase 1.6 / WWI-04 / DW-02C/D. **Implementation:** Not Started.
- **Liên quan:** [ADR index](README.md), [Precision options](../data-models/wwi-scd-identity-key-design.md).

## Quyết định và Approved Design Constraints

Bảo toàn exact **100 ns** representation của SQL Server temporal values liên quan tới source identity và validity assessment. Chưa phê duyệt PostgreSQL physical datatype.

Không phụ thuộc duy nhất vào microsecond timestamps cho identity hoặc interval predicates khi precision loss có thể làm sai lookup. Phân biệt source exact values với timestamps dùng display/ordinary analytics. Phải kiểm chứng round-trip, boundary predicates, collisions, sentinels và open-ended intervals.

## Lý do và hệ quả

Các finite periods hiện tại có thể không có submicrosecond differences nhưng không chứng minh future inputs hoặc sentinel convert lossless. Exact identity giữ riêng không đủ nếu lookup vẫn chạy predicate trên rounded boundaries.

## Các phương án đã xem xét

Canonical representation, integer ticks và timestamp kèm exact identity/residual vẫn là technical options. Chỉ dùng timestamp giảm precision: không đáp ứng direction. Không có physical option nào được chọn trong ADR này.

## Proposed Technical Policies / Pending Implementation Details

Encoding, epoch, datatype, normalization, timezone interpretation, sentinel representation và driver/PostgreSQL round-trip cần đặc tả/kiểm thử tại bước phù hợp. C/D chỉ có test specification; chưa có runtime result.
