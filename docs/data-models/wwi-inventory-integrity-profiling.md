# Inventory & Integrity Profiling — Phase 1.2

**Trạng thái: Verified từ truy vấn `SELECT` trực tiếp trên WWI ngày 2026-11-07.** Số liệu phản ánh snapshot khảo sát; không định nghĩa daily inventory balance hoặc COGS. SQL tái kiểm chứng: [WWI Profiling Queries](wwi-profiling-queries.md).

## StockItems, holdings và movement

| Bảng | COUNT_BIG(*) | DISTINCT PK | Duplicate PK |
| --- | ---: | ---: | ---: |
| `Warehouse.StockItems` | 227 | 227 | 0 |
| `Warehouse.StockItems_Archive` | 444 | 227 | 217 theo `StockItemID`, hợp lệ với history |
| `Warehouse.StockItemHoldings` | 227 | 227 | 0 |
| `Warehouse.StockItemTransactions` | 236,667 | 236,667 | 0 |

`Warehouse.StockItems`: `ColorID` NULL 99, `Brand` NULL 209, `Size` NULL 64, `Barcode` NULL 219, `RecommendedRetailPrice` NULL 0. `UnitPrice` min 0.66, max 1,899.00 và không có giá ≤ 0. Đây là phân phối cột nguồn, chưa phải pricing rule.

`Warehouse.StockItemHoldings`: tổng `QuantityOnHand` **30,343,296**, tổng `LastStocktakeQuantity` **29,459,593**; `QuantityOnHand` min 3, max 1,034,169, không âm hoặc bằng 0. `LastCostPrice` min 0.36, max 1,140.00; không âm. Đây là **tồn hiện tại**, không phải số dư cuối từng ngày.

## Signed movement và liên kết optional

| `TransactionTypeID` / tên nguồn | Dòng | Tổng `Quantity` | Min | Max | Invoice link | PurchaseOrder link |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 / `Stock Issue` | 228,265 | -8,950,628 | -360 | -1 | 228,265 | 0 |
| 11 / `Stock Receipt` | 8,358 | 139,418,326 | 6 | 67,368 | 0 | 8,358 |
| 12 / `Stock Adjustment at Stocktake` | 44 | -18 | -5 | 4 | 0 | 0 |
| **Tổng** | **236,667** | **130,467,680** | **-360** | **67,368** | **228,265** | **8,358** |

Có 228,286 movement âm, 4 bằng 0 và 8,377 dương. `CustomerID` và `InvoiceID` NULL ở 8,402 dòng; `SupplierID` và `PurchaseOrderID` NULL ở 228,309 dòng. Theo cặp link: 228,265 chỉ có `InvoiceID`, 8,358 chỉ có `PurchaseOrderID`, 44 không có cả hai, 0 có cả hai. Các FK NULL này là optional; orphan được kiểm tra riêng.

`TransactionOccurredWhen` từ 2013-01-01 12:00 đến 2016-05-31 12:00. `LastEditedWhen` cũng có min 2013-01-01 12:00 và max 2016-05-31 12:00; 0 NULL nhưng có nhiều timestamp trùng (xem [Data Profiling Report](wwi-data-profiling.md)).

### Phân phối movement theo năm

| Năm | Dòng |
| --- | ---: |
| 2013 | 63,306 |
| 2014 | 68,386 |
| 2015 | 74,451 |
| 2016 (đến tháng 5) | 30,524 |

### Phân phối movement theo tháng

| Tháng | Dòng |
| --- | ---: |
| 2013-01 | 5,564 |
| 2013-02 | 3,851 |
| 2013-03 | 5,498 |
| 2013-04 | 5,449 |
| 2013-05 | 5,812 |
| 2013-06 | 5,465 |
| 2013-07 | 6,040 |
| 2013-08 | 4,957 |
| 2013-09 | 5,200 |
| 2013-10 | 5,303 |
| 2013-11 | 5,077 |
| 2013-12 | 5,090 |
| 2014-01 | 5,809 |
| 2014-02 | 4,943 |
| 2014-03 | 5,250 |
| 2014-04 | 5,637 |
| 2014-05 | 6,124 |
| 2014-06 | 6,001 |
| 2014-07 | 6,457 |
| 2014-08 | 5,260 |
| 2014-09 | 5,269 |
| 2014-10 | 6,214 |
| 2014-11 | 5,272 |
| 2014-12 | 6,150 |
| 2015-01 | 5,863 |
| 2015-02 | 5,602 |
| 2015-03 | 6,097 |
| 2015-04 | 6,766 |
| 2015-05 | 6,207 |
| 2015-06 | 6,297 |
| 2015-07 | 7,178 |
| 2015-08 | 5,528 |
| 2015-09 | 6,512 |
| 2015-10 | 6,367 |
| 2015-11 | 5,828 |
| 2015-12 | 6,206 |
| 2016-01 | 6,133 |
| 2016-02 | 5,404 |
| 2016-03 | 6,291 |
| 2016-04 | 6,134 |
| 2016-05 | 6,562 |

## StockItems temporal history

Current có 227 dòng/227 ID; archive có 444 dòng/227 ID. Hợp trực tiếp current + archive có 671 version rows. Số version theo item: 55 ID có 2, 129 có 3, 41 có 4 và 2 có 5. `ValidFrom` archive từ 2013-01-01 00:00 đến 2016-05-31 23:09; current từ 2016-05-31 23:00 đến 23:12. Có 0 version zero/negative-duration, 0 overlap, 0 gap và 444 cặp version liền kề.

So sánh null-safe cả 22 thuộc tính ngoài PK/period qua `LAG` cho thấy chỉ `CustomFields` và cột computed `Tags` thay đổi: mỗi cột 444 transition trên 227 ID. Các cột khác, gồm `UnitPrice`, `TaxRate`, `SupplierID` và `LastEditedBy`, có 0 transition trong snapshot này. Không suy ra rằng giá vốn/giá bán đã có historical change.

Tất cả 236,667 movement có ít nhất một version StockItems thỏa `ValidFrom <= TransactionOccurredWhen < ValidTo`. Đây là system-time overlap quan sát, **không** xác nhận business effective time hoặc SCD2 policy.

## Referential integrity kiểm tra trực tiếp

Mỗi orphan count dưới đây chỉ tính child có FK **khác NULL** nhưng không có parent. NULL ở FK tùy chọn được báo riêng.

| Child FK → Parent PK | Child rows | NULL FK | Orphan non-NULL |
| --- | ---: | ---: | ---: |
| `Orders.CustomerID → Customers.CustomerID` | 73,595 | 0 | 0 |
| `OrderLines.OrderID → Orders.OrderID` | 231,412 | 0 | 0 |
| `Invoices.OrderID → Orders.OrderID` | 70,510 | 0 | 0 |
| `InvoiceLines.InvoiceID → Invoices.InvoiceID` | 228,265 | 0 | 0 |
| `InvoiceLines.StockItemID → StockItems.StockItemID` | 228,265 | 0 | 0 |
| `CustomerTransactions.CustomerID → Customers.CustomerID` | 97,147 | 0 | 0 |
| `CustomerTransactions.InvoiceID → Invoices.InvoiceID` | 97,147 | 26,637 | 0 |
| `StockItemTransactions.StockItemID → StockItems.StockItemID` | 236,667 | 0 | 0 |
| `StockItemTransactions.InvoiceID → Invoices.InvoiceID` | 236,667 | 8,402 | 0 |
| `StockItemTransactions.PurchaseOrderID → PurchaseOrders.PurchaseOrderID` | 236,667 | 228,309 | 0 |
| `StockItemHoldings.StockItemID → StockItems.StockItemID` | 227 | 0 | 0 |

## Khả năng đối soát với bảng nguồn liên quan

- **Invoice stock issues:** gom `Sales.InvoiceLines` và movement type `Stock Issue` theo `(InvoiceID, StockItemID)`: 228,265 cặp, 0 cặp chỉ ở một bên, 228,265 cặp có `InvoiceLines.Quantity = -SUM(movement.Quantity)`, 0 mismatch số dòng. Không có FK trực tiếp từ movement tới `InvoiceLineID`; đây là phép đối soát quan sát ở grain cặp khóa.
- **Purchase stock receipts:** gom `Purchasing.PurchaseOrderLines` theo `(PurchaseOrderID, StockItemID)`, đổi `ReceivedOuters × StockItems.QuantityPerOuter` ra unit; so với `Stock Receipt` movement: 8,358 cặp khớp quantity, 9 purchase-line pairs chưa có receipt movement, 0 movement-only pairs. Công thức chuyển đơn vị ở đây chỉ là phép kiểm tra dữ liệu, chưa phê duyệt quy tắc nghiệp vụ Purchasing.
- **Current holdings:** với cả 227 stock item, `QuantityOnHand` **khác** tổng movement `Quantity` cộng từ mọi lịch sử hiện có. Tổng holdings 30,343,296 so với tổng movement 130,467,680. Không suy daily balance hoặc xem chênh lệch là lỗi khi opening balance/stocktake rules chưa được xác định.

## Rủi ro và điểm cần mở

**Verified:** bốn movement có `Quantity=0`; 44 stocktake adjustments không có invoice/PO link; chín purchase line pairs chưa có receipt. Chúng cần được giải thích bằng nghiệp vụ trước khi viết data quality rule. **Unverified:** opening balance, diễn giải signed quantity theo từng transaction type qua thời gian, và lịch sử product cost. **Not Applicable:** tính daily balance hoặc COGS trong Phase 1.2.
