# Báo cáo đánh giá Phase 1.2 — WWI Data Profiling & Integrity

**Trạng thái: Phase 1.2 đã được Project Owner nghiệm thu về mặt khảo sát dữ liệu; WWI-02 vẫn `IN_PROGRESS`.** Project Owner đã chấp thuận nội dung Phase 1.1, cho phép Phase 1.2 và sau khi review đã chấp thuận nghiệm thu Phase 1.2 theo acceptance criteria. Khảo sát trực tiếp `WideWorldImporters` ngày 2026-11-07 bằng các lệnh `SELECT` và `COUNT_BIG(*)` qua Windows integrated authentication. Không thay đổi SQL Server/PostgreSQL hoặc triển khai pipeline. Dữ liệu được báo cáo ở mức tổng hợp; không lưu record cá nhân.

## 1. Executive summary và tables profiled

**Verified:** Năm bảng Sales/Invoicing (`Orders`, `OrderLines`, `Invoices`, `InvoiceLines`, `CustomerTransactions`), `Sales.Customers` và archive, ba bảng Inventory (`StockItems`, `StockItemHoldings`, `StockItemTransactions`) cùng `StockItems_Archive` đã được kiểm tra trực tiếp. Chín bảng hiện hành MVP có PK duy nhất; 11 quan hệ FK ưu tiên có **0 orphan khi FK khác NULL**. Hai bảng history có nhiều version cùng business ID như dự kiến.

**Verified:** 3,085 order chưa có invoice; 44,245 invoice có `CustomerID` khác `BillToCustomerID`; 26,637 customer payment transactions có `InvoiceID` NULL; 4,626 invoice lines có `LineProfit < 0`. Stock issues đối chiếu khớp invoice lines theo cặp `(InvoiceID, StockItemID)` trong snapshot. `StockItemHoldings.QuantityOnHand` không khớp tổng movement thô ở 227/227 item.

## 2. Bằng chứng chi tiết

- [WWI Data Profiling Report](wwi-data-profiling.md): exact counts, PK, timestamp duplicates và rủi ro chung.
- [Sales & Invoicing Profiling](wwi-sales-profiling.md): NULL, order–invoice, customer role, transaction types, tổng cột nguồn, phân phối năm/tháng.
- [Customer & Temporal Profiling](wwi-customer-temporal-profiling.md): history, changed attributes, zero-duration, as-of test và giới hạn system-time.
- [Inventory & Integrity Profiling](wwi-inventory-integrity-profiling.md): signed movement, holdings, stock temporal, trực tiếp FK anti-join và đối soát Sales/Purchasing.
- [SQL Profiling Queries](wwi-profiling-queries.md): truy vấn `SELECT` và mẫu chạy lại từng phép kiểm tra.

## 3. Data quality risks và giới hạn chứng cứ

| Mức xác minh | Quan sát / giới hạn | Ảnh hưởng |
| --- | --- | --- |
| Verified | `LastEditedWhen` trùng rất nhiều, dù NULL=0 ở bảy bảng khảo sát | Timestamp đơn lẻ không là khóa duy nhất cho checkpoint. |
| Verified | Một customer archive row có `ValidFrom = ValidTo`; `FOR SYSTEM_TIME ALL` ít hơn raw current + archive một dòng | Phải phân biệt version raw và version có khoảng hiệu lực khi phân tích temporal. |
| Verified | Chỉ `CreditLimit` thay đổi trong 28 thuộc tính Customer được so sánh; `LastEditedBy` cũng đổi | Chưa đủ căn cứ chọn SCD2 attributes hoặc as-of semantics. |
| Verified | StockItems history thay đổi ở `CustomFields` và computed `Tags`, không ở `UnitPrice` trong snapshot | Không coi history này là cost/price history. |
| Verified | 4 movement có quantity 0, 9 purchase-line pairs chưa có receipt, 4,626 negative `LineProfit` | Cần business rule/threshold trước khi gắn nhãn invalid. |
| Unverified | Mọi truy vấn không nằm trong một snapshot transaction chung | Không chứng minh nhất quán nguyên tử nếu tiến trình khác ghi nguồn trong khi khảo sát. |
| Unverified | Độ phủ business effective time, delete/change capture, revenue/COGS, opening balance | Không chốt SCD2, incremental, daily balance hoặc KPI. |

## 4. Acceptance checklist

| Acceptance Criterion | Evidence | PASS/PARTIAL/FAIL | Remarks |
| --- | --- | --- | --- |
| Exact row counts và PK uniqueness | `COUNT_BIG(*)`/`DISTINCT PK` cho 9 bảng hiện hành và hai archive | PASS | History duplicate ID là version hợp lệ. |
| Sales NULL, date, year/month, status và transaction distribution | 41 tháng, hai transaction types, cờ `IsFinalized`, invoice/order cardinality | PASS | Không suy order chưa invoiced là canceled. |
| Quantity, UnitPrice, tax, extended, profit và ngoại lệ | Tổng/min/max và 4,626 negative `LineProfit` | PASS | Chưa định nghĩa revenue/COGS. |
| Customer temporal changes và validity | 663 current + 51 archive, 28 thuộc tính so sánh, một zero-duration | PASS | System-time khác business effective time. |
| Inventory NULL, signed quantity và đối soát | 236,667 movement; type distribution, invoice/PO group-level reconciliation, 227 holdings mismatch thô | PASS | Không tính daily balance. |
| FK kiểm tra bằng dữ liệu, phân biệt NULL/orphan | 11 anti-join; 0 orphan non-NULL; NULL optional báo riêng | PASS | Chỉ các quan hệ ưu tiên trong phạm vi. |
| Timestamp feasibility observations | NULL/distinct/min/max ở 7 `LastEditedWhen` và period timestamps | PASS | Chưa chốt watermark. |
| SQL evidence tái kiểm chứng | [11 nhóm truy vấn SELECT](wwi-profiling-queries.md) | PASS | Không truy vấn raw record cá nhân. |
| Markdown links và không secret | Kiểm tra filesystem/link và scan tài liệu sau khi tạo | PASS | Kết quả kiểm tra cuối trong báo cáo Codex. |
| Không thay đổi nguồn, dependency hoặc phase ngoài task | Git diff chỉ tài liệu; lệnh SQL chỉ SELECT | PASS | Phase 1.2 đã được owner nghiệm thu; WWI-03/04 vẫn TODO. |

## 5. Open Decisions

- Revenue recognition, tax treatment, invoice date so với delivery date, credit note semantics và ý nghĩa `LineProfit`: WWI-03.
- Customer role `CustomerID`/`BillToCustomerID`, fact/dimension grain và source-to-target mapping: WWI-03; không lấy equality nguồn làm công thức KPI.
- SCD2 attributes, business-effective validity, giới hạn temporal history: WWI-04 sau khi owner review.
- Watermark/tie-breaker, late update/delete/replay và môi trường thử nghiệm độc lập: WWI-04.
- Inventory opening balance, stocktake adjustments, daily balance và ngưỡng data quality: trước inventory mart/quality gates.

## 6. Recommendations for Phase 1.3

**Proposed, chưa được triển khai:** dùng các profile Sales và FK đã kiểm để lập source relationship/cardinality contract, ghi rõ nullable và grain nguồn, sau đó đưa giả thuyết KPI/customer role cho WWI-03 review. Các quan sát về history và timestamp chỉ cung cấp đầu vào cho WWI-04. **Not Applicable ở Phase 1.2:** SQL DDL, warehouse schema, ETL, dbt, Airflow, Power BI, database clone hoặc test INSERT/UPDATE.
