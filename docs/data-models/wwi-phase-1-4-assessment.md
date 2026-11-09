# Phase 1.4 Assessment — Source Contracts & Extraction Requirements

**Trạng thái: Project Owner đã review và chấp thuận Phase 1.4 ở mức tài liệu; WWI-02 đủ điều kiện `DONE` theo acceptance criteria trong `TASKS.md`.** Tài liệu thiết kế ngày 2026-11-09 dựa trên metadata/SELECT đã ghi ở Phase 1.1–1.3 (khảo sát nguồn ngày 2026-11-07). Không chạy extraction, không đổi SQL Server/PostgreSQL, không tạo pipeline/DDL, không thêm dependency, không chốt KPI/SCD2/incremental policy.

## Executive summary

**Verified input:** chín bảng current MVP có PK duy nhất tại snapshot, FK/nullable/temporal được ghi trong [Metadata Dictionary](wwi-metadata-dictionary.md); quan hệ và ngoại lệ có [SQL evidence](wwi-relationship-validation-sql.md) và [profiling SQL](wwi-profiling-queries.md). **Proposed output:** source contracts, extraction matrix, raw requirements và validation matrix. **Unverified:** service account permissions, consistent multi-table read, hành vi timestamp khi update, delete detection, type mapping, performance và runtime reconciliation. **Not Applicable:** KPI, warehouse schema, ETL/dbt/Airflow implementation.

## Deliverables

1. [WWI Source Contracts](wwi-source-contracts.md): grain, PK/FK, NULL, temporal, full/incremental feasibility, dependencies và checks cho chín bảng.
2. [WWI Extraction Requirements Matrix](wwi-extraction-requirements-matrix.md): priority đề xuất, full eligibility, candidate timestamp/period/PK, update/delete limits, consistency risks.
3. [Raw Layer Requirements](../requirements/wwi-raw-layer-requirements.md): payload nguồn, tám metadata kỹ thuật tối thiểu, traceability/rerun và giới hạn physical design.
4. [Source Validation Matrix](../requirements/wwi-source-validation-matrix.md): kiểm tra nguồn, sau ingestion và nghiệp vụ chờ quyết định riêng.

## Acceptance checklist

| Tiêu chí | Evidence | Đánh giá |
| --- | --- | --- |
| Contract đủ chín bảng MVP | Chín mục trong [Source Contracts](wwi-source-contracts.md) | PASS — tài liệu |
| Grain, PK, nullable, dependencies | Metadata Dictionary và Relationship Contract được dẫn chiếu từng bảng | PASS — source evidence |
| Incremental candidate khác policy | Extraction matrix ghi LEW/period chỉ candidate, delete/update limits; WWI-04 open | PASS — tài liệu |
| Raw metadata, batch/retry và đối soát | [Raw Requirements](../requirements/wwi-raw-layer-requirements.md) có tám field và manifest đề xuất | PASS — thiết kế, chưa runtime |
| Snapshot/temporal limits | Contract/matrix ghi one zero-duration, system-time khác business time, count không cùng snapshot | PASS — tài liệu |
| Order–Invoice, Payment–Invoice không suy đoán | 3.085 order chưa invoice, FK OrderID nullable, 26.637 payment InvoiceID NULL; không đặt 1:1 constraint | PASS — source evidence |
| Validation/reconciliation có grain và evidence | [Validation Matrix](../requirements/wwi-source-validation-matrix.md) S/I/B và Q/R queries | PASS — thiết kế, ingestion tests chưa chạy |
| Không chốt KPI, SCD2, incremental policy | Open Decisions trong các tài liệu, không có physical schema/checkpoint | PASS — tài liệu |
| Không code/database object/dependency | Git diff Phase 1.4 chỉ Markdown thuộc phạm vi; không có truy vấn ghi nguồn hoặc database objects | PASS — Verified diff |
| Liên kết Markdown/secret | 259 liên kết nội bộ, 0 gãy; quét mẫu secret không phát hiện | PASS — Verified tại lần kiểm tra trước commit |

**Giới hạn nghiệm thu:** `PASS — tài liệu` không xác nhận full load, incremental, raw storage hoặc validation chạy được. Project Owner đã nghiệm thu Phase 1.4 và cho phép hoàn thiện WWI-02 nếu acceptance criteria đạt. [Dictionary](wwi-metadata-dictionary.md), [profiling](wwi-data-profiling.md), [relationships/ERD](wwi-source-relationships.md), [source contracts](wwi-source-contracts.md) và assessment Phase 1.1–1.4 cung cấp bằng chứng PK/FK, source grain, dates, temporal, NULL và ngoại lệ cho Sales, Customer/Inventory; owner review đã có. Vì vậy WWI-02 đạt `DONE` ở phạm vi khảo sát và source design. Các business decisions WWI-03/04 vẫn mở.

## Open Decisions

- **WWI-03:** revenue/tax/LineProfit, invoice date vs delivery date, buyer/bill-to role, payment allocation, fact/dimension grain và KPI eligibility.
- **WWI-04:** `LastEditedWhen` update behavior, watermark/tie-breaker, replay/backfill/delete, temporal/SCD2 validity, independent test environment.
- **Trước Inventory mart:** opening balance, stocktake/adjustment rules và daily balance nếu được yêu cầu.
- **Trước implementation:** quyền service account, snapshot/isolation có thể dùng mà không đổi cấu hình nguồn, projection/type mapping, batch/window, retry semantics, raw retention/security và quality thresholds.

## Recommendations for WWI-03 / Phase 1.5

**Proposed:** dùng source contracts làm đầu vào để Project Owner review các business decisions WWI-03; kiểm chứng điều kiện extraction còn mở trước physical ingestion design. Project Owner đã cho phép Phase 1.5/WWI-03 bằng task riêng. Không tự triển khai Phase 1.6 hoặc pipeline.
