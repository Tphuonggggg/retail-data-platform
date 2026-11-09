# WWI Source Relationships — Phase 1.3

**Trạng thái:** Verified metadata và snapshot quan sát ngày 2026-11-07; Project Owner đã chấp thuận ở mức tài liệu/khảo sát ngày 2026-11-09. Đây là mô hình **nguồn SQL Server**, không phải schema warehouse hay quyết định KPI. PK/FK và nullable lấy từ [metadata dictionary](wwi-metadata-dictionary.md), đối chiếu bằng [Relationship Validation SQL](wwi-relationship-validation-sql.md). Các số snapshot không là constraint lâu dài.

## Quy ước relationship contract

`1 → 0..N` nghĩa là mỗi child có một parent bắt buộc, một parent có thể có 0..N child theo schema. `0..1 → 0..N` nghĩa là FK child nullable. `1 → 0..1` ở holdings do child PK cũng là FK. Cột “Phân bố” có dạng `parent không child / đúng 1 / >1; max child` tại snapshot. RI = orphan với FK khác NULL; NULL báo riêng. Không suy ra uniqueness child FK từ số liệu hiện có.

| Child / source table | Parent table; join key | Schema; nullable FK | RI; phân bố snapshot | Join risk | SQL evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `Sales.Orders` | `Sales.Customers`; `Orders.CustomerID = Customers.CustomerID` | 1 → 0..N; Không | 0 orphan; `0/0/663; max 150` | Customer có nhiều order | R01,R02,R03 | Verified |
| `Sales.OrderLines` | `Sales.Orders`; `OrderID` | 1 → 0..N; Không | 0 orphan; `0/8.596/64.999; max 5` | Header lặp khi join line | R01,R02,R03 | Verified |
| `Sales.Invoices` | `Sales.Orders`; `OrderID` | 0..1 → 0..N; Có | 0 orphan, 0 NULL; `3.085/70.510/0; max 1` | 1:1 chỉ quan sát | R01,R02,R03 | Verified |
| `Sales.InvoiceLines` | `Sales.Invoices`; `InvoiceID` | 1 → 0..N; Không | 0 orphan; `0/5.572/64.938; max 5` | Không join trực tiếp OrderLines | R01,R02,R03,R06 | Verified |
| `Sales.OrderLines` | `Warehouse.StockItems`; `StockItemID` | 1 → 0..N; Không | 0 orphan; `0/0/227; max 1.123` | Item lặp qua orders | R01,R02,R03 | Verified |
| `Sales.InvoiceLines` | `Warehouse.StockItems`; `StockItemID` | 1 → 0..N; Không | 0 orphan; `0/0/227; max 1.123` | Item lặp qua invoices | R01,R02,R03 | Verified |
| `Sales.Customers` (bill-to role) | `Sales.Customers`; `BillToCustomerID = CustomerID` | 1 → 0..N tự tham chiếu; Không | 0 orphan; `400/261/2; max 201` | Buyer ≠ bill-to | R01,R02,R03,R04 | Verified |
| `Sales.Invoices` (buyer role) | `Sales.Customers`; `Invoices.CustomerID = CustomerID` | 1 → 0..N; Không | 0 orphan; 70.510 invoice | Không thay bằng bill-to | R01,R03,R04 | Verified |
| `Sales.Invoices` (bill-to role) | `Sales.Customers`; `Invoices.BillToCustomerID = CustomerID` | 1 → 0..N; Không | 0 orphan; 70.510 invoice | Hai role cùng parent table, join bằng alias riêng | R01,R03,R04 | Verified |
| `Sales.CustomerTransactions` | `Sales.Customers`; `CustomerID` | 1 → 0..N; Không | 0 orphan; 97.147 transaction | CustomerID ở invoice transaction là bill-to trong snapshot | R01,R03,R04 | Verified |
| `Sales.CustomerTransactions` | `Sales.Invoices`; `InvoiceID` | 0..1 → 0..N; Có | 0 orphan, 26.637 NULL; `0/70.510/0; max 1` | Payment không có InvoiceID | R01,R02,R03,R04 | Verified |
| `Sales.CustomerTransactions` | `Application.TransactionTypes`; `TransactionTypeID` | 1 → 0..N; Không | 0 orphan; type 1: 70.510, type 3: 26.637 | Type không thay allocation | R01,R03,R04 | Verified |
| `Warehouse.StockItemHoldings` | `Warehouse.StockItems`; `StockItemID` (child PK/FK) | 1 → 0..1; Không | 0 orphan; `0/227/0; max 1` | Holdings là current state, không có ngày | R01,R02,R03,R05 | Verified |
| `Warehouse.StockItemTransactions` | `Warehouse.StockItems`; `StockItemID` | 1 → 0..N; Không | 0 orphan; `0/0/227; max 1.767` | Movement grain khác holdings | R01,R02,R03,R05 | Verified |
| `Warehouse.StockItemTransactions` | `Sales.Invoices`; `InvoiceID` | 0..1 → 0..N; Có | 0 orphan, 8.402 NULL; `0/5.572/64.938; max 5` | Không có InvoiceLineID FK | R01,R02,R03,R05 | Verified |
| `Warehouse.StockItemTransactions` | `Purchasing.PurchaseOrders`; `PurchaseOrderID` | 0..1 → 0..N; Có | 0 orphan, 228.309 NULL; `2/150/1.922; max 34` | Receipt không FK trực tiếp tới PO line | R01,R02,R03,R05 | Verified |
| `Warehouse.StockItemTransactions` | `Sales.Customers`; `CustomerID` | 0..1 → 0..N; Có | 0 orphan, 8.402 NULL | Chỉ là FK nguồn, không xác lập customer KPI | R01,R03,R05 | Verified |
| `Warehouse.StockItemTransactions` | `Application.TransactionTypes`; `TransactionTypeID` | 1 → 0..N; Không | 0 orphan; type 10/11/12 | Kiểm tra type trước đối soát | R01,R03,R05 | Verified |
| `Purchasing.PurchaseOrderLines` | `Purchasing.PurchaseOrders`; `PurchaseOrderID` | 1 → 0..N; Không | 0 orphan; `0/150/1.924; max 34` | Dependency, chưa là subject area MVP | R01,R02,R03,R05 | Verified |
| `Purchasing.PurchaseOrderLines` | `Warehouse.StockItems`; `StockItemID` | 1 → 0..N; Không | 0 orphan; 8.367 lines | PO line không FK trực tiếp movement | R01,R03,R05 | Verified |

Các quan hệ FK khác trong nguồn (People, PackageTypes, Suppliers...) được ghi trong metadata dictionary; bảng trên chỉ là contract trọng tâm Phase 1.3. Archive temporal không có FK/version grain giống bảng hiện hành; không vẽ archive như parent giao dịch.

## Sales & Invoicing

**Verified snapshot:** 73.595 orders có 231.412 order lines; 3.085 orders chưa invoiced và 70.510 orders có một invoice. 70.510 invoices có 228.265 invoice lines. Mỗi order thiếu invoice trong snapshot cũng có `PickingCompletedWhen` NULL, nhưng không gán business status. Không có `OrderLineID` trên InvoiceLines hoặc FK trực tiếp giữa hai loại line. Đối chiếu theo `(OrderID, StockItemID)` quan sát 228.265 cặp có quantity bằng nhau, 3.147 cặp chỉ ở OrderLines, không có composite key lặp ở snapshot; kết quả này không tạo ra constraint 1:1 và không bảo đảm cho dữ liệu tương lai.

## Customer & financial transactions

`Customers.BillToCustomerID` là FK tự tham chiếu bắt buộc. 263/663 customer tự bill-to; 400 customer trỏ tới customer khác. 44.245/70.510 invoice có buyer `CustomerID` khác `BillToCustomerID`. `Invoices.CustomerID` khớp `Orders.CustomerID` ở mọi invoice có linked order; `Invoices.BillToCustomerID` khớp `Customers.BillToCustomerID` **hiện hành** của buyer ở snapshot, không chứng minh lịch sử as-of.

`CustomerTransactions` type 1 (*Customer Invoice*) có 70.510 dòng và `InvoiceID` khác NULL; trong snapshot, `CustomerTransactions.CustomerID` của toàn bộ type 1 khớp `Invoices.BillToCustomerID`, còn 26.265 dòng khớp thêm buyer ID. Type 3 (*Customer Payment Received*) có 26.637 dòng, tất cả `InvoiceID` NULL. Không có khóa allocation payment → invoice trong các bảng khảo sát. Không thể phân bổ payment cho từng invoice từ FK hiện có; join qua CustomerID chỉ ghép nhiều giao dịch và nhiều invoice, gây fan-out.

## Inventory & Purchasing dependencies

StockItemHoldings dùng `StockItemID` làm PK/FK, một dòng current holding cho mỗi 227 StockItems trong snapshot. StockItemTransactions có 228.265 issue nối invoice, 8.358 receipt nối purchase order và 44 stocktake adjustment không nối cả hai; 0 dòng nối cả invoice lẫn purchase order. `TransactionTypeID` xác định type quan sát, nhưng không có FK tới `InvoiceLineID` hoặc `PurchaseOrderLineID`.

Đối soát **ở grain `(InvoiceID, StockItemID)`**: issue quantity âm đối ứng 228.265 cặp InvoiceLines, không lệch quantity. Ở grain `(PurchaseOrderID, StockItemID)`, 8.358 receipt pairs khớp số unit tính từ `ReceivedOuters × QuantityPerOuter`, còn 9 PO-line pairs chưa có receipt. Đây là phép kiểm tra snapshot, không phê duyệt business rule Purchasing. Tổng movement lịch sử thô không bằng current holdings ở 227/227 item; opening balance và stocktake rules chưa xác định, nên không tính tồn kho cuối ngày.

## Các phép join cần tránh

- `OrderLines ↔ InvoiceLines` qua OrderID/StockItemID chỉ là phép đối chiếu tổ hợp; không phải FK giữa line. Tránh nhân dòng khi kết hợp measures từ hai line tables.
- `Invoices ↔ CustomerTransactions` theo `CustomerID` thay cho nullable `InvoiceID` có thể nhân dòng và gắn payment sai invoice.
- `Invoices ↔ StockItemTransactions` qua InvoiceID rồi nối thêm InvoiceLines tạo tích số dòng theo từng invoice; đối soát bằng tổng hợp riêng ở cùng grain.
- `StockItemHoldings ↔ StockItemTransactions` lặp current balance theo từng movement; không cộng lại holdings sau join.
- `Customers` buyer và bill-to phải dùng hai alias/role theo đúng FK; không thay `CustomerID` bằng `BillToCustomerID` trong KPI chưa duyệt.

## Open Decisions

Ý nghĩa buyer/bill-to cho KPI, payment allocation, revenue/tax/profit, fact grain, SCD2 as-of, incremental, opening balance và stocktake vẫn chờ phê duyệt. Quan hệ nguồn trong tài liệu này không chốt các quyết định đó.
