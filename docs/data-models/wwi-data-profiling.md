# WWI Data Profiling Report — Phase 1.2

**Trạng thái: Verified observations; chờ Project Owner review.** Khảo sát bằng `SELECT` trực tiếp trên `WideWorldImporters` ngày 2026-11-07. Các số dòng dùng `COUNT_BIG(*)` chính xác tại thời điểm truy vấn; truy vấn không nằm trong một snapshot transaction chung nên không khẳng định các bảng là ảnh chụp nguyên tử nếu nguồn được tiến trình khác thay đổi. Không lưu record cá nhân hoặc credential. Xem [SQL Profiling Queries](wwi-profiling-queries.md).

## Phạm vi và điều hướng

| Nhóm | Bảng / tài liệu chi tiết | Kết quả chính |
| --- | --- | --- |
| Sales & Invoicing | [Sales Profiling](wwi-sales-profiling.md): Orders, OrderLines, Invoices, InvoiceLines, CustomerTransactions | 3,085 order chưa invoiced; 44,245 invoice có `CustomerID` khác `BillToCustomerID`; 4,626 invoice lines có `LineProfit < 0`. |
| Customer & Temporal | [Customer Temporal Profiling](wwi-customer-temporal-profiling.md): Customers + archive | 663 current/51 history; một history row zero-duration; chỉ `CreditLimit` là thuộc tính nghiệp vụ quan sát thay đổi. |
| Inventory & Integrity | [Inventory/Integrity Profiling](wwi-inventory-integrity-profiling.md): StockItems + archive, StockItemHoldings, StockItemTransactions và FK ưu tiên | 236,667 movement; 0 orphan non-NULL ở 11 quan hệ đã kiểm; holdings không bằng tổng movement thô. |

Purchasing chỉ được đọc ở mức `PurchaseOrderLines`/parent để đối chiếu receipt. Không mở rộng Purchasing thành subject area MVP.

## Đối chiếu số dòng và tính duy nhất

| Bảng | COUNT_BIG(*) | DISTINCT PK | Dòng trùng PK |
| --- | ---: | ---: | ---: |
| `Sales.Orders` | 73,595 | 73,595 | 0 |
| `Sales.OrderLines` | 231,412 | 231,412 | 0 |
| `Sales.Invoices` | 70,510 | 70,510 | 0 |
| `Sales.InvoiceLines` | 228,265 | 228,265 | 0 |
| `Sales.CustomerTransactions` | 97,147 | 97,147 | 0 |
| `Sales.Customers` | 663 | 663 | 0 |
| `Sales.Customers_Archive` | 51 | 46 | 5 theo `CustomerID`, đúng tính chất version history |
| `Warehouse.StockItems` | 227 | 227 | 0 |
| `Warehouse.StockItems_Archive` | 444 | 227 | 217 theo `StockItemID`, đúng tính chất version history |
| `Warehouse.StockItemHoldings` | 227 | 227 | 0 |
| `Warehouse.StockItemTransactions` | 236,667 | 236,667 | 0 |

## Timestamp và incremental observations

`Dòng vượt DISTINCT` = `COUNT_BIG(*) - COUNT_BIG(DISTINCT LastEditedWhen)`; đây là số dòng trùng **giá trị timestamp**, không phải duplicate event hay số group trùng. Tất cả cột `LastEditedWhen` liệt kê dưới đây có 0 NULL ở snapshot này.

| Bảng | DISTINCT `LastEditedWhen` | Dòng vượt DISTINCT | Min | Max |
| --- | ---: | ---: | --- | --- |
| `Sales.Orders` | 2,129 | 71,466 | 2013-01-01 11:00 | 2016-05-31 12:00 |
| `Sales.OrderLines` | 1,970 | 229,442 | 2013-01-01 11:00 | 2016-05-31 12:00 |
| `Sales.Invoices` | 1,069 | 69,441 | 2013-01-02 07:00 | 2016-05-31 12:00 |
| `Sales.InvoiceLines` | 1,069 | 227,196 | 2013-01-01 12:00 | 2016-05-31 12:00 |
| `Sales.CustomerTransactions` | 1,069 | 96,078 | 2013-01-02 11:30 | 2016-05-31 12:00 |
| `Warehouse.StockItemHoldings` | 2 | 225 | 2016-05-31 07:00 | 2016-05-31 12:00 |
| `Warehouse.StockItemTransactions` | 1,973 | 234,694 | 2013-01-01 12:00 | 2016-05-31 12:00 |

Trên hợp trực tiếp current + archive, `Sales.Customers` có 714 version rows nhưng chỉ 65 `ValidFrom` và 4 `ValidTo` khác nhau; `Warehouse.StockItems` có 671 version rows, 18 `ValidFrom` và 14 `ValidTo` khác nhau. Period timestamps cũng không độc nhất. Các giá trị max của `LastEditedWhen` dừng ở 2016-05-31, phù hợp một bản dữ liệu lịch sử đứng yên, nhưng **không chứng minh** cơ chế cập nhật thực tế hoặc delete capture.

**Proposed cho WWI-04:** nếu khảo sát watermark, phải xem xét timestamp trùng, tie-breaker theo PK, late update, delete, replay và index. Không chốt chiến lược incremental trong Phase 1.2.

## Rủi ro chất lượng dữ liệu cần diễn giải

| Quan sát Verified | Diễn giải còn mở |
| --- | --- |
| 3,085 order chưa có invoice | Không tự gọi là canceled hoặc failed. |
| 44,245 invoice có `CustomerID <> BillToCustomerID` | Customer role theo KPI chưa được duyệt. |
| 26,637 customer payment transactions có `InvoiceID` NULL | NULL theo metadata và phân bố transaction type; không phải orphan. |
| 4,626 invoice lines có `LineProfit < 0` | Chưa có quy tắc profit/COGS hoặc ngưỡng lỗi. |
| Một customer history row có `ValidFrom = ValidTo` | Phân biệt raw archive với `FOR SYSTEM_TIME ALL` khi đếm version. |
| Bốn stock movements có `Quantity = 0` | Cần xét transaction type và quy tắc stocktake. |
| 9 purchase-line pairs không có receipt movement | Có thể là chưa nhận; chưa tự kết luận lỗi. |
| 227/227 holdings khác tổng movement thô | Opening balance/stocktake chưa được định nghĩa; không tính daily balance. |

## Giới hạn

**Verified** là kết quả truy vấn hiện tại. **Unverified** gồm lịch sử đầy đủ, business effective time, semantics revenue/COGS, chính sách watermark và các quy tắc data quality. **Proposed** là phân tích Phase 1.3/WWI-03/04 chờ phê duyệt. **Not Applicable** trong task này: triển khai ETL, warehouse schema, dbt, Airflow, Power BI và cập nhật SQL Server/PostgreSQL.
