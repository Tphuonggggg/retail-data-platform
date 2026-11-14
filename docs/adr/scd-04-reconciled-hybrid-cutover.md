# ADR-SCD-04 — Reconciled Hybrid Cutover (D04)

- **Status:** Accepted — Architecture Direction.
- **Decision Date / Authority:** 2026-11-14 / Project Owner.
- **Scope:** Phase 1.6 / WWI-04 / DW-02C/D. **Implementation:** Not Started.
- **Liên quan:** [ADR index](README.md), [Cutover/recovery design](../data-models/wwi-scd-forward-cutover-design.md).

## Quyết định và Approved Design Constraints

Reconcile verified WWI temporal history với forward-observed changes. Bảo toàn source-backed/observation-backed lineage; source system-time, observation-time và analytical validity là các ngữ nghĩa riêng.

Không invent business-effective timestamps/intermediate changes, không double-create analytical versions khi cùng thay đổi xuất hiện ở history và observation. Full reload không được làm mất forward evidence. Không hòa giải được thì giữ trạng thái chưa xác minh, không ép nối timeline.

## Lý do và hệ quả

Dùng source evidence có sẵn và theo dõi từ khi pipeline hoạt động mà không claim quá mức historical coverage. Raw zero-duration và current→archive revisions phải trace được; source version count không là analytical version count.

## Các phương án đã xem xét

Ép một global cutover/business-effective timestamp hoặc bỏ forward history khi reload: không chọn. Evidence tracks có thể được giữ riêng khi chưa reconcile, nhưng không phải alternative cho phép hai timelines conflict cùng được publish như một lịch sử đã xác minh.

## Proposed Technical Policies / Pending Implementation Details

Generation boundaries, bridge criteria, source consistency, registry backup/replay và recovery procedures còn cần nghiệm thu. C/D mô tả reconciliation invariants, không phê duyệt isolation, chunking, checkpoints hoặc runtime state tables.
