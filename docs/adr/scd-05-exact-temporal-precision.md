# ADR-SCD-05 — Exact Temporal Precision (D05)

- **Status:** Accepted — Architecture Direction; **B9 APPROVED — Physical Raw Temporal Representation** (scoped, 2026-11-15).
- **Decision Date / Authority:** 2026-11-14 / Project Owner.
- **Scope:** Original direction Phase1.6/WWI-04/DW-02C/D; scoped B9 physical follow-up tại DW-03A. **Production implementation:** Not Started; isolated B9 PoC Implemented/Tested.
- **Liên quan:** [ADR index](README.md), [Precision options](../data-models/wwi-scd-identity-key-design.md).

## Quyết định D05 ban đầu — 2026-11-14 (lịch sử, logical invariant giữ nguyên)

Bảo toàn exact **100 ns** representation của SQL Server temporal values liên quan tới source identity và validity assessment. Chưa phê duyệt PostgreSQL physical datatype.

Không phụ thuộc duy nhất vào microsecond timestamps cho identity hoặc interval predicates khi precision loss có thể làm sai lookup. Phân biệt source exact values với timestamps dùng display/ordinary analytics. Phải kiểm chứng round-trip, boundary predicates, collisions, sentinels và open-ended intervals.

## Lý do và hệ quả

Các finite periods hiện tại có thể không có submicrosecond differences nhưng không chứng minh future inputs hoặc sentinel convert lossless. Exact identity giữ riêng không đủ nếu lookup vẫn chạy predicate trên rounded boundaries.

## Các phương án đã xem xét

Canonical representation, integer ticks và timestamp kèm exact identity/residual vẫn là technical options. Chỉ dùng timestamp giảm precision: không đáp ứng direction. Không có physical option nào được chọn trong ADR này.

## B9 trước PoC/physical approval — hồ sơ lịch sử

B9 = **Pending — Physical Implementation** theo Owner task ngày 2026-11-15; không hoãn hoặc bác bỏ logical exact 100 ns invariant đã duyệt. Datatype/encoding/epoch/normalization/timezone/sentinel/driver conversion và round-trip implementation là DW-03/physical design inputs, phải duyệt trước conversion và có tests trước runtime publication. Chưa chọn P-A/B/C hoặc có runtime result. [Backlog B9](../data-models/wwi-dw-02e-work-plan.md) ghi stage/gate.

## B9 — APPROVED: Physical Raw Temporal Representation, 2026-11-15

**Authority:** Project Owner instruction “DW-03A — B9 Physical Approval & Final Design Acceptance Review”. Approval được cấp trực tiếp trong instruction, không suy từ reviewer hoặc PoC PASS.

1. Dùng verified **F2 explicit seven-digit source-side formatter**, giữ nguyên biểu thức đã kiểm chứng.
2. Canonical datetime2(7) qua Python dưới dạng **str hoặc None**.
3. Transport bằng **parameterized psycopg**, không concatenate giá trị vào SQL.
4. **PostgreSQL TEXT là authoritative Raw temporal storage type** cho relevant datetime2(7) source temporal fields trong approved project scope.
5. Dùng **COLLATE "C"** khi cần canonical textual ordering/comparison.
6. Non-NULL phải giữ đúng format **YYYY-MM-DDTHH:mm:ss.fffffff**, fixed27 characters/seven fractional digits.
7. Giữ NULL, min/max boundaries, temporal sentinel và distinct values cách100ns; không collapse/round/trim hoặc biến sentinel thành NULL.
8. Source system-time **không được diễn giải thành business-effective time**.
9. Không silently chuyển authoritative value sang Python datetime hoặc PostgreSQL timestamp giảm precision.
10. Derived timestamp/search-optimized representation chỉ là **secondary**, không thay authoritative source value.

### Evidence và giới hạn phê duyệt

[DW-03A evidence](../data-models/wwi-dw-03a-evidence-approval-readiness.md) sections10/12/14/15 giữ SQL F2 fixtures14/14, SQL/Python/PG order169/169, actual source samples18/18, PG parameters14/14/persisted15/15, equality/ranges/NULL/zero/trailing/min/max/sentinel/100ns PASS; command/runtime/image/config/raw-result locations có thể tái kiểm chứng. [B9 PoC](../../tests/integration/b9_precision/README.md) giữ code/test commands; metadata failure trước values và successful retries không bị xóa.

Approval **không bao gồm** entire Raw schema/index strategy/retention periods/publication runtime/crash-restart-recreation reliability hoặc production-scale performance. Physical DDL/access/capacity/retention/secondary representations phải qua implementation review/gates; driver/config/version thay đổi cần appropriate fidelity regression trước runtime. B1–B8/A01–A06 và historical logical D05 không đổi; [DW-02 backlog](../data-models/wwi-dw-02e-work-plan.md) ghi current B9 status, [DW-03A assessment](../data-models/wwi-dw-03a-assessment.md) tách design acceptance khỏi runtime.

Decision trail: D05 exact100ns logical direction Accepted → B9 physical Pending ở DW-02 → source/Python/PG bounded PoC PASS → **current scoped physical approval**. Các Pending statements trong hồ sơ trước mốc này là lịch sử, không là current B9 state.
