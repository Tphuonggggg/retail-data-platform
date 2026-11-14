# WWI Logical DW Design Specification — DW-01

**DW-01 DONE — thiết kế logic đã qua targeted review ngày 2026-11-14 theo quyền nghiệm thu có điều kiện của Project Owner.** Phase 1.5 đã nghiệm thu tại commit `411e3eed9cb0b422e0c19fdcd0566b2691a31fd2`; WWI-03 DONE. DW-01 chỉ thiết kế logic; Các logical contracts được nghiệm thu trong DW-01; SCD2 policy, physical implementation và các Open Decisions được ghi rõ vẫn Pending Approval. Runtime: Not implemented yet.

## Đầu vào và ranh giới quyết định

[Scope](../../PROJECT_SCOPE.md), [KPI Catalog](../../analytics/kpi-definitions/wwi-kpi-candidate-catalog.md), [BRD](../requirements/wwi-business-rules-decision-matrix.md), [Source Contracts](wwi-source-contracts.md), [Dictionary nguồn](wwi-metadata-dictionary.md), [Profiling](wwi-data-profiling.md), [Relationships](wwi-source-relationships.md) là nguồn tham chiếu. Không thay thế các tài liệu nguồn bằng bản sao. Warehouse tự thiết kế trên PostgreSQL, nguồn WWI SQL Server read-only; Sales end-to-end trước Customer rồi Inventory.

| Ràng buộc được duyệt | Hệ quả với DW-01 | Phần chưa chốt |
| --- | --- | --- |
| Kimball Star Schema, Conformed Dimensions | Bốn fact chi tiết, dimensions dùng chung; marts Power BI tách khỏi Core DW | Physical type, index, partition, keys allocation |
| Invoice Line, Order Line, Stock Movement, Inventory Current | Giữ source line/movement IDs; current inventory một row/item trong state công bố | Physical schema và publication transaction |
| SCD2 theo temporal có bằng chứng và forward tracking | Có version identity, evidence/lookup status; không tự backdate business validity | Attributes, validity, fallback ở DW-02 |
| L01 initial full + periodic incremental + periodic full reconciliation | Mỗi fact có yêu cầu full build, change impact và đối soát toàn bộ định kỳ | Lịch, window, consistency, thresholds |
| L02 transaction watermark candidate; temporal history/snapshot; holdings snapshot comparison | Tách change detection theo loại nguồn | Thuật toán, delete và tie-breaker ở DW-03B |
| L03 test INSERT/UPDATE/DELETE trên SQL Server độc lập | Test plan cần môi trường riêng, chưa tạo/chạy | Quyền, dữ liệu test và isolation |
| L04 idempotent upsert + SCD2 kiểm chứng + rebuild/restate | Replay giữ uniqueness theo business grain, restate partitions cũ và mới | Checkpoint, replay/recovery protocol |
| L05 Sales Full + Incremental end-to-end trước mở rộng | Customer/product tối thiểu phục vụ Sales trước; mart Customer/Inventory triển khai sau | Task triển khai và nghiệm thu riêng |

## Bus Matrix

`X` = dimension dùng chung; nhãn trong ô là role. `—` = không có requirement cho dimension đó trong fact. Chưa thêm dimension customer cho movement chỉ vì nguồn có nullable CustomerID.

| Business process / fact | dim_date | dim_customer | dim_product | dim_movement_type | Degenerate/source references |
| --- | --- | --- | --- | --- | --- |
| Invoice Line / fact_invoice_line | X: invoice date | X: buyer, bill-to | X | — | InvoiceLineID, InvoiceID, nullable OrderID |
| Order Line / fact_order_line | X: order date | X: buyer | X | — | OrderLineID, OrderID |
| Stock Movement / fact_stock_movement | X: movement date | — | X | X | StockItemTransactionID, nullable InvoiceID/PurchaseOrderID |
| Current Inventory / fact_inventory_current | — | — | X: current version | — | StockItemID, observation/run metadata |

dim_date là calendar dùng chung, không tự thêm fiscal calendar. Buyer và bill-to cùng dim_customer qua hai FK/alias. Khóa dimension surrogate xác định một version; natural key nguồn được giữ để distinct customer không đếm nhiều version. Date key, unknown member và chính sách lookup vẫn là candidate. Inventory Current dùng observation metadata, không có daily date FK để tránh gợi ý daily balance.

## Header population và distinct metrics

S01 lấy population từ **Sales.Orders**, S02 từ **Sales.Invoices**, C01/C02 từ **order header**, không yêu cầu invoice hoặc line tồn tại. Product-filtered count phải lấy distinct document IDs của các line phù hợp rồi semi-join header; không đếm dòng sau join, không cộng distinct counts từng product thành toàn doanh nghiệp. Product filter loại header không có matching line nên đây là population khác KPI toàn header. C02 theo product chưa có eligibility policy được duyệt, không công bố biến thể đó trong MVP hiện hành.

Đề xuất intermediate `int_order_header`: **1 OrderID**, từ mọi `Sales.Orders`, gồm order không invoice hoặc không line. Giữ OrderDate, CustomerID buyer, source lineage và dimension lookup metadata. S01 = count OrderID; C01 = distinct source CustomerID; C02 = buyer có ≥2 distinct OrderID/tháng / buyer có ≥1/tháng. Không đếm customer surrogate versions. Snapshot Phase 1.3 có 0 order không line, nhưng FK cho phép 0..N; không dùng snapshot thay schema guarantee.

Đề xuất `int_invoice_header`: **1 InvoiceID**, từ mọi `Sales.Invoices`, gồm header không line nếu xuất hiện; giữ InvoiceDate, buyer, bill-to, nullable OrderID và IsCreditNote. S02 đếm header; S06 lấy tổng S05 chia S02 cùng header population. Line totals được aggregate theo InvoiceID rồi **left join từ header**; header không line được cảnh báo coverage, không tự loại khỏi mẫu. Số amount từ tập line rỗng là 0 cho phép tổng hợp; missing batch/line chưa nạp xong phải chặn công bố, không coi là 0 hợp lệ.

Hai intermediate là hợp đồng logic hỗ trợ population, **không phải Core Fact thứ năm/sáu**. Không sao chép header amount/count=1 vào từng line rồi SUM. Product-filtered distinct invoice/order chỉ phản ánh chứng từ có product đó; không thay KPI count toàn header. Đề xuất semantic layer phân biệt rõ phạm vi này.

## Business Rule → KPI → model → source → validation

| BRD | KPI chính xác | Fact / intermediate | Dimension / role | Source table.columns | Validation/evidence |
| --- | --- | --- | --- | --- | --- |
| 01 | S01, S02, S03, S04, S05 | order header; invoice header + fact_invoice_line | order/invoice date, buyer, product | Orders.OrderID; Invoices.InvoiceID; InvoiceLines.InvoiceLineID/ExtendedPrice/TaxAmount | K01–K03; R02 header/line coverage; unique source grain |
| 02 | S01–S06, C01–C04 | headers, invoice/order lines | dim_date hai role riêng | Orders.OrderDate; Invoices.InvoiceDate | Tổng theo ngày khớp header/source; không dùng delivery date |
| 03 | S05 mặc định; S03,S04 | fact_invoice_line | invoice date, buyer/bill-to, product | InvoiceLines.ExtendedPrice, TaxAmount | K02: S03 = S04 + S05 cùng population |
| 04 | S08 Deferred | Không tạo recognized measure | Không chọn recognition date | Invoices.ConfirmedDeliveryTime chỉ evidence | K09; không công bố recognized revenue |
| 05 | S09 Optional | fact_invoice_line | invoice date, product | InvoiceLines.LineProfit | K13; âm không tự là lỗi; không suy COGS |
| 06 | S06 Core; S07 Deferred | fact_invoice_line + invoice header | invoice date, buyer | ExtendedPrice−TaxAmount / distinct InvoiceID | K10; cùng filter/as-of; mẫu 0 → NULL |
| 07 | S10 Unsupported | Không có refund fact/measure | Không áp dụng | Invoices.IsCreditNote dùng cảnh báo nguồn | K01; 0 credit note không chứng minh refund amount = 0 |
| 08 | C03 Core, C04 Optional | fact_invoice_line | dim_customer buyer và bill-to | Invoices.CustomerID, BillToCustomerID | K12; mỗi phân bố bằng S05, không cộng hai role |
| 09 | C02, C01, S01 | int_order_header; fact_order_line chỉ chi tiết | order date; buyer natural key | Orders.OrderID/CustomerID/OrderDate | K11 distinct OrderID/tháng, tử ≤ mẫu; quý tính lại |
| 10 | Không có allocation KPI | CustomerTransactions chỉ đối soát | Không join payment theo customer | CustomerTransactions.InvoiceID/TransactionTypeID | K03, R04; không fact-to-fact payment join |
| 11 | I01–I05; I06 Unsupported | fact_stock_movement, fact_inventory_current | product, movement date/type | StockItemTransactions.Quantity; Holdings.QuantityOnHand | K07/K08; không cộng movements để dựng balance |
| 12 | I07 Unsupported | Không có risk model | Không áp dụng | Current holdings không là forecast | Không công bố Stockout Risk |

K01–K13 ở [SQL KPI](../../analytics/kpi-definitions/wwi-kpi-verification-sql.md); R02/R04 ở [SQL Relationships](wwi-relationship-validation-sql.md). C05 Optional lấy current dim_customer một row/NK theo category, không join fact, đối soát K06. I05 month trend có thể roll-up từ mart movement daily theo type/product, giữ precision Quantity.

## Điều hướng deliverables

- [Fact & Dimension Dictionary](wwi-fact-dimension-dictionary.md): grain, measures, keys, full/incremental, SCD candidates và dependencies.
- [Logical Mapping](wwi-logical-source-to-target.md): fields, source columns, NULL/type/lookup và validation.
- [Star Schemas](wwi-logical-star-schemas.md): bốn stars và consolidated bus.
- [Change Impact](wwi-change-impact-matrix.md): detection → propagation → SCD2 → restatement.
- [Logical Marts](wwi-logical-data-marts.md): sáu marts, population và aggregation contracts.
- [DW-01 Assessment](wwi-dw-01-assessment.md): checklist, rủi ro và chuyển giao. DW-02 chưa bắt đầu.
