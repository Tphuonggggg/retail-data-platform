# WWI Source Contracts — Phase 1.4

**MVP-RESET-01 hi?n h?nh:** data/business/fidelity contracts gi? nguy?n; historical dedicated-identity/global permission/ACL/security approval prerequisites ???c supersede b?i current PROJECT_SCOPE.md/AGENTS.md. Sales-first MVP; advanced incremental/SCD2/recovery l? milestones sau, kh?ng claim runtime implemented.

**Trạng thái: Project Owner đã chấp thuận tài liệu Phase 1.4; các extraction policies vẫn Proposed.** Contract logic cho đúng chín bảng MVP trong `WideWorldImporters` trên SQL Server chỉ đọc; chưa phải quyền/chính sách extraction đã triển khai. Danh sách **toàn bộ cột, SQL datatype, nullable, default, PK/FK** nằm tại [Metadata Dictionary](wwi-metadata-dictionary.md), mục cùng tên bảng. Tài liệu này dẫn chiếu thay vì lặp lại định nghĩa cột. Số liệu snapshot và NULL lấy từ [Phase 1.2](wwi-data-profiling.md); quan hệ và cardinality từ [Phase 1.3](wwi-source-relationships.md). Kiến nghị vận hành ở [Extraction Requirements Matrix](wwi-extraction-requirements-matrix.md).

## Quy ước chung

- **Source grain** là một dòng bảng hiện hành theo PK; temporal archive là các phiên bản riêng, không thay grain bảng current.
- **Full load candidate**: có PK và SELECT đã dùng để profiling; chưa xác minh quyền extraction trong service account, isolation, ảnh chụp nhất quán nhiều bảng, thời gian chạy, hoặc khả năng đọc đủ cột. Full load cần giữ nguyên giá trị nguồn và cùng một bộ cột đã công bố trong dictionary, không ngầm đổi business meaning.
- **Incremental candidate** chỉ là cột/thông tin có thể khảo sát. `LastEditedWhen`, `ValidFrom/ValidTo` **chưa được duyệt làm watermark**; timestamp trùng, update/delete capture và tie-breaker còn mở ở WWI-04. Full scan/đối chiếu PK cũng chỉ là phương án cần đánh giá, không là chính sách.
- **Checks nguồn** là kỳ vọng để kiểm chứng lại lúc extraction; các con số ngày 2026-11-07 là baseline quan sát, không phải ngưỡng cố định. FK nullable phải tách NULL hợp lệ khỏi orphan. Các FK tới bảng ngoài chín bảng MVP vẫn tồn tại, xem dictionary; kiểm tra qua nguồn hoặc contract phụ thuộc khi được duyệt.
- **Cột cần bảo toàn** gồm PK, FK, cột nghiệp vụ, giá trị thời gian và nullable đúng theo dictionary. Chưa chọn projection tối ưu hoặc physical type của PostgreSQL.

### Candidate extraction columns theo bảng

Các cột dưới đây là **đầu vào khảo sát cho full read/chia phạm vi đọc**, không phải watermark được duyệt. Ngày nghiệp vụ không bắt được update/delete nếu chỉ lọc theo ngày; bảng line không có ngày nghiệp vụ riêng.

| Bảng | Candidate key / change information | Date/filter candidate và giới hạn |
| --- | --- | --- |
| `Sales.Customers` | `CustomerID`, `ValidFrom/ValidTo` current/archive | Period là system-time; không có business-effective policy. |
| `Sales.Orders` | `OrderID`, `LastEditedWhen` | `OrderDate` cho phân bố/phạm vi đọc nếu được duyệt; không là update watermark. |
| `Sales.OrderLines` | `OrderLineID`, `LastEditedWhen` | Không có order business date trên line; join `Orders.OrderDate` để lọc phải kiểm chi phí và consistency. |
| `Sales.Invoices` | `InvoiceID`, `LastEditedWhen` | `InvoiceDate`; `ConfirmedDeliveryTime` nullable, không là update watermark. |
| `Sales.InvoiceLines` | `InvoiceLineID`, `LastEditedWhen` | Không có invoice business date trên line; join header để lọc phải kiểm chi phí và consistency. |
| `Sales.CustomerTransactions` | `CustomerTransactionID`, `LastEditedWhen` | `TransactionDate`; không tự thay change timestamp. |
| `Warehouse.StockItems` | `StockItemID`, `ValidFrom/ValidTo` current/archive | Period là system-time; không là cost/price history đã duyệt. |
| `Warehouse.StockItemHoldings` | `StockItemID`, `LastEditedWhen` | Chỉ current state, không có daily date grain. |
| `Warehouse.StockItemTransactions` | `StockItemTransactionID`, `LastEditedWhen` | `TransactionOccurredWhen` cho phân bố/phạm vi đọc, không bắt mọi update. |

## `Sales.Customers`

- **Vai trò / grain:** một customer master hiện hành trên `CustomerID`; `BillToCustomerID` là self-FK, không thay buyer key.
- **PK / khóa liên quan:** `CustomerID`; `BillToCustomerID` bắt buộc, các FK category/contact/location xem dictionary. 663 current rows có PK duy nhất trong snapshot.
- **Cột / datatype:** [Dictionary — `Sales.Customers`](wwi-metadata-dictionary.md), 31 cột. `ValidFrom`, `ValidTo` là `datetime2(7)` period; `BillToCustomerID` là `int`. Nullable của các thuộc tính khác theo dictionary.
- **Temporal / extraction candidate:** system-versioned với `Sales.Customers_Archive` (51 rows/46 IDs); current và archive có grain khác nhau. `ValidFrom/ValidTo` chỉ là system-time candidate; không có `LastEditedWhen` ở current table.
- **Full load:** đọc đủ current rows và period columns; nếu cần version history phải quy định extraction riêng cho archive, không ngầm nhập archive như current. Cần gắn batch/run metadata bên ngoài payload nguồn.
- **Dependencies / checks:** tự tham chiếu bill-to; Orders, Invoices, CustomerTransactions và StockItemTransactions tham chiếu CustomerID. Kiểm PK, required customer/bill-to, self-FK, period validity và version count. Một archive row zero-duration cần giữ trong đối soát raw archive; `FOR SYSTEM_TIME ALL` ít hơn hợp trực tiếp một row.
- **Unverified:** business effective time, SCD2 attributes, coverage lịch sử, khả năng phát hiện delete và ảnh chụp nhất quán giữa current/archive.

## `Sales.Orders`

- **Vai trò / grain:** một order header trên `OrderID`; 73.595 rows snapshot.
- **PK / khóa liên quan:** `OrderID`; `CustomerID` bắt buộc; `BackorderOrderID` self-FK nullable. `PickedByPersonID` nullable; các FK khác theo dictionary.
- **Cột / datatype:** [Dictionary — `Sales.Orders`](wwi-metadata-dictionary.md), 16 cột; `OrderDate` và `LastEditedWhen` giữ đúng datatype nguồn trong dictionary.
- **Temporal / extraction candidate:** non-temporal; `LastEditedWhen` có 0 NULL nhưng chỉ 2.129 giá trị khác nhau trong snapshot. `OrderID` là candidate tie-breaker, chưa phê duyệt.
- **Full load:** giữ cả order chưa invoiced (3.085 ở baseline), không tự phân loại canceled/failed; đọc đủ header và các FK/timestamps, đối soát `COUNT_BIG(*)` cùng thời điểm kiểm tra.
- **Dependencies / checks:** Customers; là parent của OrderLines và optional parent của Invoices. Kiểm PK, `CustomerID`, self-FK non-NULL, ngày nguồn, duplicate PK, số order thiếu invoice như observation riêng.
- **Unverified:** update behavior của `LastEditedWhen`, delete capture, status semantics, consistency với invoice khi đọc khác thời điểm.

## `Sales.OrderLines`

- **Vai trò / grain:** một order line trên `OrderLineID`; 231.412 rows snapshot.
- **PK / khóa liên quan:** `OrderLineID`; `OrderID`, `StockItemID`, `PackageTypeID` bắt buộc. `UnitPrice` 0 NULL, `PickingCompletedWhen` 3.147 NULL ở baseline.
- **Cột / datatype:** [Dictionary — `Sales.OrderLines`](wwi-metadata-dictionary.md), 12 cột; giữ source `Quantity`, `UnitPrice`, `LastEditedWhen` đúng datatype.
- **Temporal / extraction candidate:** non-temporal; `LastEditedWhen` có 0 NULL nhưng nhiều trùng; `OrderLineID` candidate tie-breaker chưa duyệt.
- **Full load:** giữ đủ line kể cả order chưa invoice; không dùng InvoiceLines làm bản sao/đối ứng 1:1 theo schema.
- **Dependencies / checks:** Orders, StockItems và PackageTypes ngoài chín bảng MVP. Kiểm PK, required FK, NULL distribution, quantity/price nguồn, RI và count theo parent.
- **Unverified:** line update/delete detection, relation nghiệp vụ line-to-line với InvoiceLines, source-consistent read cùng Orders.

## `Sales.Invoices`

- **Vai trò / grain:** một invoice header trên `InvoiceID`; 70.510 rows snapshot.
- **PK / khóa liên quan:** `InvoiceID`; `CustomerID` buyer và `BillToCustomerID` bill-to là hai FK bắt buộc; `OrderID` FK nullable dù baseline có 0 NULL.
- **Cột / datatype:** [Dictionary — `Sales.Invoices`](wwi-metadata-dictionary.md), 25 cột; giữ `InvoiceDate`, `ConfirmedDeliveryTime`, `IsCreditNote`, `LastEditedWhen` theo datatype/nullable nguồn.
- **Temporal / extraction candidate:** non-temporal; `LastEditedWhen` 0 NULL nhưng trùng; `InvoiceID` candidate tie-breaker chưa duyệt.
- **Full load:** đọc mọi invoice kể cả `OrderID` NULL nếu xuất hiện về sau; không áp đặt một invoice/order do snapshot hiện max 1 nhưng FK không unique.
- **Dependencies / checks:** Customers qua hai role, Orders optional; parent InvoiceLines và CustomerTransactions optional. Kiểm PK, required buyer/bill-to, nullable order, date/null delivery và RI.
- **Unverified:** revenue/tax/credit note semantics, update/delete coverage, business meaning của buyer/bill-to cho KPI.

## `Sales.InvoiceLines`

- **Vai trò / grain:** một invoice line trên `InvoiceLineID`; 228.265 rows snapshot.
- **PK / khóa liên quan:** `InvoiceLineID`; `InvoiceID`, `StockItemID`, `PackageTypeID` bắt buộc. Không có FK tới `OrderLineID`.
- **Cột / datatype:** [Dictionary — `Sales.InvoiceLines`](wwi-metadata-dictionary.md), 13 cột; giữ nguyên `Quantity`, `UnitPrice`, `TaxAmount`, `ExtendedPrice`, `LineProfit`, `LastEditedWhen` theo datatype nguồn.
- **Temporal / extraction candidate:** non-temporal; `LastEditedWhen` 0 NULL nhưng trùng; `InvoiceLineID` candidate tie-breaker chưa duyệt.
- **Full load:** đọc đủ line và các amount nguồn; không gọi `ExtendedPrice` là recognized revenue hoặc suy COGS từ `LineProfit`.
- **Dependencies / checks:** Invoices, StockItems, PackageTypes. Kiểm PK, required FK, count, sum cột nguồn theo invoice/line grain; 4.626 `LineProfit < 0` là observation, chưa là lỗi.
- **Unverified:** business eligibility của amount, mapping với OrderLines, update/delete capture và consistent read cùng header.

## `Sales.CustomerTransactions`

- **Vai trò / grain:** một customer transaction trên `CustomerTransactionID`; 97.147 rows snapshot.
- **PK / khóa liên quan:** `CustomerTransactionID`; `CustomerID`, `TransactionTypeID` bắt buộc; `InvoiceID` và `PaymentMethodID` nullable.
- **Cột / datatype:** [Dictionary — `Sales.CustomerTransactions`](wwi-metadata-dictionary.md), 14 cột; giữ `TransactionDate`, `TransactionAmount`, `IsFinalized`, `LastEditedWhen` đúng datatype.
- **Temporal / extraction candidate:** non-temporal; `LastEditedWhen` 0 NULL nhưng trùng; `CustomerTransactionID` candidate tie-breaker chưa duyệt.
- **Full load:** giữ cả type 1 invoice transactions lẫn type 3 payment transactions, kể cả `InvoiceID` NULL; không phân bổ payment sang invoice.
- **Dependencies / checks:** Customers, TransactionTypes, optional Invoices/PaymentMethods. Kiểm PK/FK, phân phối type, nullable theo type, tổng `TransactionAmount` theo type riêng; không cộng vào invoice-line amount như cùng grain.
- **Unverified:** payment allocation, transaction semantics ngoài type đã quan sát, update/delete capture và finalization rules.

## `Warehouse.StockItems`

- **Vai trò / grain:** một stock item master hiện hành trên `StockItemID`; 227 current rows snapshot.
- **PK / khóa liên quan:** `StockItemID`; `SupplierID`, package FKs bắt buộc; `ColorID` nullable và các thuộc tính optional theo dictionary.
- **Cột / datatype:** [Dictionary — `Warehouse.StockItems`](wwi-metadata-dictionary.md), 25 cột; `ValidFrom/ValidTo` là `datetime2(7)` period. Giữ source fields/nullable, gồm `CustomFields` và computed `Tags` đúng metadata nguồn.
- **Temporal / extraction candidate:** system-versioned với 444 archive rows; period timestamps chỉ system-time candidate, không phải cost history hoặc watermark đã duyệt.
- **Full load:** đọc current master trước line/movement để kiểm FK; history nếu cần là extraction riêng, không nhập lẫn current.
- **Dependencies / checks:** Supplier, Colors, PackageTypes ngoài chín bảng MVP; parent của OrderLines, InvoiceLines, Holdings, StockItemTransactions. Kiểm PK, required FK, NULL, unit price nguồn, period validity.
- **Unverified:** business-effective history, delete capture, ý nghĩa thay đổi `CustomFields`/`Tags`, cost/pricing history.

## `Warehouse.StockItemHoldings`

- **Vai trò / grain:** một **current holding** trên `StockItemID` (PK đồng thời FK); 227 rows snapshot, không có date grain.
- **PK / khóa liên quan:** `StockItemID` duy nhất và bắt buộc; `LastEditedBy` FK.
- **Cột / datatype:** [Dictionary — `Warehouse.StockItemHoldings`](wwi-metadata-dictionary.md), 9 cột; giữ `QuantityOnHand`, `LastStocktakeQuantity`, `LastCostPrice`, `LastEditedWhen` đúng datatype nguồn.
- **Temporal / extraction candidate:** non-temporal; `LastEditedWhen` chỉ có 2 giá trị khác nhau trong 227 rows; `StockItemID` candidate tie-breaker chưa duyệt.
- **Full load:** xem là ảnh current state tại thời điểm đọc; cần gắn `extracted_at`/batch, không diễn giải thành daily snapshot lịch sử.
- **Dependencies / checks:** StockItems. Kiểm PK/FK, count, NULL, nonnegative observation và tổng holdings; không yêu cầu bằng tổng movement thô.
- **Unverified:** opening balance, stocktake rules, update/delete capture và mức nhất quán khi movement đang thay đổi.

## `Warehouse.StockItemTransactions`

- **Vai trò / grain:** một stock movement trên `StockItemTransactionID`; 236.667 rows snapshot.
- **PK / khóa liên quan:** `StockItemTransactionID`; `StockItemID`, `TransactionTypeID` bắt buộc; `CustomerID`, `InvoiceID`, `SupplierID`, `PurchaseOrderID` nullable.
- **Cột / datatype:** [Dictionary — `Warehouse.StockItemTransactions`](wwi-metadata-dictionary.md), 11 cột; giữ `Quantity` có dấu, `TransactionOccurredWhen`, `LastEditedWhen` đúng datatype.
- **Temporal / extraction candidate:** non-temporal; `LastEditedWhen` 0 NULL nhưng trùng nhiều; PK candidate tie-breaker chưa duyệt.
- **Full load:** giữ đầy đủ type 10 issue, 11 receipt, 12 adjustment; giữ FK nullable đúng nguồn, không suy movement nào không có invoice/PO là invalid.
- **Dependencies / checks:** StockItems, TransactionTypes; optional Invoices, Customers, PurchaseOrders/Suppliers ngoài MVP. Kiểm PK, RI non-NULL, type và signed quantity theo type. Đối soát issue với invoice lines theo `(InvoiceID,StockItemID)` chỉ khi population/time nhất quán; receipt/PO line là dependency kiểm tra, không mở rộng Purchasing MVP.
- **Unverified:** opening balance, daily balance, update/delete capture, quan hệ line-level với InvoiceLines/PO lines.

## Điều kiện chung trước thiết kế extraction thực tế

Xác minh quyền service account, projection đầy đủ, hiệu năng/query plan ở SQL Server Express, isolation được cho phép, nguồn có thay đổi khi chạy hay không, timestamp update behavior, delete detection và phương án đối soát khi đọc nhiều bảng. Các quyết định này chưa được phê duyệt ở Phase 1.4.
