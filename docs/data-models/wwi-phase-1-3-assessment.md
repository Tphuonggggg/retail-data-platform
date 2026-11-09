# Phase 1.3 Assessment — WWI Business Relationships & Source ERD

**Trạng thái:** Project Owner đã review và chấp thuận Phase 1.3 ở mức tài liệu và khảo sát ngày 2026-11-09; WWI-02 vẫn `IN_PROGRESS`. Khảo sát nguồn `WideWorldImporters` local ngày 2026-11-07 chỉ bằng SELECT/metadata. Không thay đổi SQL Server/PostgreSQL, không viết pipeline/schema/KPI. Phase 1.4 được cho phép riêng; WWI-03 chưa bắt đầu.

## Executive summary

**Verified:** các FK trong contract enabled/trusted; anti-join bổ sung có 0 orphan khác NULL. Có 3.085 orders chưa invoice; snapshot có tối đa một invoice/order và một invoice transaction/invoice, nhưng **schema không có unique constraint tương ứng**. 44.245 invoice có buyer khác bill-to. Payment transactions hiện có `InvoiceID` NULL, không có allocation tới invoice từ các FK khảo sát. Issue/receipt đối soát được ở grain document + stock item, không phải line-level FK.

**Unverified:** business semantics của customer roles, payment allocation, revenue, tồn kho ngày, lịch sử as-of và các quy tắc KPI. **Proposed:** owner review source relationship contract và bốn ERD; chưa chốt downstream model.

## Deliverables

1. [WWI Source Relationships](wwi-source-relationships.md): relationship contract, nullable, RI, cardinality schema/snapshot, join risks.
2. [WWI Source ERD](wwi-source-erd.md): Sales, Customer/Financial, Inventory/Purchasing và MVP rút gọn bằng Mermaid.
3. [Business Data Flow](wwi-business-data-flow.md): luồng tham chiếu nghiệp vụ nguồn và ranh giới suy luận.
4. [Relationship Validation SQL](wwi-relationship-validation-sql.md): truy vấn metadata và SELECT tái kiểm chứng.

## Acceptance checklist

| Tiêu chí | Bằng chứng | Đánh giá |
| --- | --- | --- |
| PK/FK, nullable và trust | Metadata dictionary; SQL R01 | PASS — Verified |
| Cardinality schema khác snapshot | Contract R02, ERD dùng `0..N` theo FK | PASS — Verified |
| Optional relationship | `Invoices.OrderID`, `CustomerTransactions.InvoiceID`, movement links ghi NULL riêng | PASS — Verified |
| Order không invoice; không giả định line 1:1 | 3.085 order; R06 chỉ đối chiếu composite key | PASS — Verified |
| Buyer vs bill-to; payment vs invoice | SQL R04, 44.245 role khác, 26.637 payment InvoiceID NULL | PASS — Verified |
| Inventory issue/receipt, không suy daily balance | SQL R05; Phase 1.2 Q10; contract ghi opening balance mở | PASS — Verified |
| ERD chỉ vẽ FK có bằng chứng | SQL R01, các quan hệ quan sát ghi chú riêng | PASS — Verified |
| Không đưa KPI/warehouse vào source model | Scope và nội dung tài liệu | PASS |
| Markdown links, Git diff, secret, file scope | 196 liên kết nội bộ, 0 gãy; quét mẫu secret không phát hiện; diff chỉ Markdown Phase 1.3 | PASS — Verified |

**Not Applicable:** DDL, warehouse facts/dimensions, ingestion, dbt, Airflow, daily inventory snapshot và quyết định KPI trong Phase 1.3.

## Data modeling risks

- Header→line và cùng một customer→nhiều invoice/transaction có thể nhân measures khi join; phải đối soát ở cùng grain.
- Cardinality tối đa 1 ở snapshot không bảo đảm schema 1:1; Invoices.OrderID và CustomerTransactions.InvoiceID nullable.
- `Customers.BillToCustomerID`, `Invoices.CustomerID`, `Invoices.BillToCustomerID` và `CustomerTransactions.CustomerID` là các role khác nhau.
- Không có FK từ InvoiceLine tới OrderLine, từ movement tới invoice/PO line, hoặc payment allocation tới invoice.
- Current holdings không là lịch sử tồn kho; temporal system-time không mặc định là business effective time.

## Open Decisions và đề xuất tiếp theo

**Pending Approval:** customer role theo KPI, payment allocation, revenue/tax/profit, fact grain, SCD2 validity, incremental extraction, opening balance/stocktake và data quality thresholds. Kết quả relationship contract/ERD đã được chấp thuận ở mức khảo sát nguồn, không phê duyệt các business decisions này. Phase 1.4 xử lý source contracts và extraction requirements theo giao việc riêng. WWI-02 chưa DONE.
