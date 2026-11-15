# ADR-SCD-03 — Whole-Day Analytical Consensus (D03)

- **Status:** Accepted — Architecture Direction.
- **Decision Date / Authority:** 2026-11-14 / Project Owner.
- **Scope:** Phase 1.6 / WWI-04 / DW-02C/D. **Implementation:** Not Started.
- **Liên quan:** [ADR index](README.md), [Lookup design](../data-models/wwi-scd-historical-lookup-design.md).

## Quyết định và Approved Design Constraints

Date-only facts chỉ resolve khi chứng minh **full relevant-day coverage** và duy nhất **một analytical version identity** cho toàn khoảng thời gian sự kiện có thể phát sinh. Thiếu analytical validity/coverage hoặc có nhiều analytical episodes phù hợp thì unresolved. Không dùng beginning/end-of-day proxy.

Nhiều source occurrences không nhất thiết là nhiều analytical versions nếu được hợp nhất hợp lệ theo tracked attributes và validity. Không gộp noncontiguous episodes chỉ vì cùng values. Integrity multi-match phải chặn publication trong scope bị ảnh hưởng.

## Lý do và hệ quả

Tránh chọn arbitrary timestamp khi nguồn chỉ có ngày. Hai endpoint đều match chưa chứng minh full-day coverage hoặc cùng analytical episode; source-day sensitivity từ A/B là evidence khảo sát, không là lookup policy.

## Các phương án đã xem xét

Operational midnight/end-day proxy: không được chọn. Unresolved vẫn là kết quả bắt buộc khi không chứng minh consensus, không phải fallback về current/earliest.

## Logical policy approval và Pending Implementation Details

B3 đã **Approved — Logical Policy** ngày 2026-11-15: relevant day phải có valid evidence phủ toàn bộ và đúng một eligible episode identity; thiếu proof/ambiguity U, integrity overlap/incompatible multi-match I block affected publication. Không chọn day proxy. Concrete day/timezone domain và analytical-validity evidence phải được chứng minh trước lookup; thiếu proof vẫn U. Exact coverage algorithm/representation/registry revision procedures chuyển DW-03. [Final Specification](../data-models/wwi-final-scd2-design-specification.md) giữ proof obligations; không biến system-time thành business-effective time.
