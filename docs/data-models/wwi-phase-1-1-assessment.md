# Báo cáo đánh giá Phase 1.1 — WWI Source Inventory & Database Metadata

**Trạng thái: nội dung Phase 1.1 đã được Project Owner review và chấp thuận; WWI-02 vẫn `IN_PROGRESS`.** Khảo sát trực tiếp SQL Server local ngày 2026-11-07 bằng Windows integrated authentication và truy vấn `SELECT` trên `WideWorldImporters`. Không truy xuất dữ liệu nghiệp vụ theo hàng, không ghi credential và không sửa database. Các số dòng dưới đây là **metadata estimate**, không phải `COUNT(*)`. Phản hồi chấp thuận này cho phép Phase 1.2, không tự chốt source contract hoặc các Open Decisions.

## 1. Tóm tắt điều hành

**Verified:** SQL Server `17.0.1000.7`, Express Edition (64-bit); database `WideWorldImporters` ONLINE, compatibility level 130. Có 23 schema nhìn thấy, trong đó bốn schema có user table: `Application` (15), `Purchasing` (7), `Sales` (12), `Warehouse` (14). Tổng 48 user tables gồm 31 bảng hiện hành và 17 history tables. Chín bảng MVP có 156 cột, 9 PK, 2 unique constraints và 51 FK xuất phát từ chúng. Metadata toàn database có 98 FK, không disabled hoặc untrusted. CDC và Change Tracking không bật theo catalog.

**Giới hạn:** Metadata khẳng định cấu trúc, không khẳng định cardinality thực tế của dữ liệu, tính đầy đủ của temporal history, semantics KPI hoặc một incremental watermark an toàn. WWI-02 vẫn cần Phase 1.2/1.3 và owner review.

Quy ước trạng thái trong báo cáo: **Verified** = đối chiếu trực tiếp với catalog/`SELECT` hiện tại; **Documented but Unverified** = được ghi trong tài liệu nhưng chưa có kiểm chứng dữ liệu/hành vi; **Proposed** = bước khảo sát tiếp theo; **Not Applicable** = không thuộc Phase 1.1. Thiết kế fact/dimension, định nghĩa KPI, triển khai PostgreSQL, ingestion, dbt, Airflow và Power BI đều **Not Applicable** trong lần khảo sát này.

## 2. Database overview và schema/table inventory

Xem [Database Inventory Report](wwi-database-inventory.md) để có đủ 23 schema, 48 bảng, phân loại nghiệp vụ/reference/history và row count metadata cho từng bảng. Các schema ngoài bốn schema trên có 0 user table tại thời điểm khảo sát. Purchasing được kiểm kê để hiểu FK từ Inventory, chưa vào MVP.

## 3. Đánh giá chín bảng MVP

| Bảng | Vai trò sơ bộ | PK | FK quan trọng từ bảng này | Cột thời gian đáng chú ý | Temporal | Cần xác minh tiếp ở Phase 1.2/1.3 |
| --- | --- | --- | --- | --- | --- | --- |
| `Sales.Customers` | Customer master | `CustomerID` | `BillToCustomerID` → Customers; category/group, city, delivery method, people | `AccountOpenedDate`, `ValidFrom`, `ValidTo` | Có → `Sales.Customers_Archive` | Vai trò bill-to; độ phủ history và as-of |
| `Sales.Orders` | Order header | `OrderID` | `CustomerID` → Customers; `BackorderOrderID` tự tham chiếu; people | `OrderDate`, `ExpectedDeliveryDate`, `PickingCompletedWhen`, `LastEditedWhen` | Không | Order lifecycle, nullable backorder/picking |
| `Sales.OrderLines` | Order line | `OrderLineID` | `OrderID` → Orders; `StockItemID` → StockItems; package type | `PickingCompletedWhen`, `LastEditedWhen` | Không | Picking vs invoicing, line matching |
| `Sales.Invoices` | Invoice header | `InvoiceID` | `CustomerID`, `BillToCustomerID` → Customers; `OrderID` → Orders (nullable); people/delivery method | `InvoiceDate`, `ConfirmedDeliveryTime`, `LastEditedWhen` | Không | Invoice vs delivery date; credit note; nullable order link |
| `Sales.InvoiceLines` | Invoice line | `InvoiceLineID` | `InvoiceID` → Invoices; `StockItemID` → StockItems; package type | `LastEditedWhen` | Không | `LineProfit`/tax semantics, invoice line grain |
| `Sales.CustomerTransactions` | Customer ledger transaction | `CustomerTransactionID` | `CustomerID` → Customers; `InvoiceID` → Invoices (nullable); transaction/payment type | `TransactionDate`, `FinalizationDate`, `LastEditedWhen` | Không | Phân biệt invoice, payment và outstanding balance |
| `Warehouse.StockItems` | Stock item master | `StockItemID` | `SupplierID` → Purchasing.Suppliers; color/package types | `ValidFrom`, `ValidTo` | Có → `Warehouse.StockItems_Archive` | Cost/price history, SCD2 coverage |
| `Warehouse.StockItemHoldings` | Tồn hiện tại | `StockItemID` | Cùng `StockItemID` → StockItems; `LastEditedBy` → People | `LastEditedWhen` | Không | Không suy daily balance; cần đối soát opening/current holdings |
| `Warehouse.StockItemTransactions` | Stock movement | `StockItemTransactionID` | `StockItemID`, `TransactionTypeID`; Customer/Invoice/Supplier/PurchaseOrder nullable | `TransactionOccurredWhen`, `LastEditedWhen` | Không | Dấu quantity, loại movement và liên kết Purchasing/Sales |

Danh sách **đủ 156 cột**, kiểu dữ liệu/độ dài, NULL, default, computed/versioning, PK/UQ/FK và 51 FK cụ thể nằm trong [Metadata Dictionary](wwi-metadata-dictionary.md). Các vai trò trên là mô tả sơ bộ để khảo sát; không phải fact/dimension design.

## 4. Keys, constraints, index và temporal

**Verified:** Chín PK và hai unique constraints: `Sales.Customers.CustomerName`, `Warehouse.StockItems.StockItemName`. `Warehouse.StockItemHoldings.StockItemID` vừa là PK vừa FK tới `Warehouse.StockItems`. Các FK của chín bảng đều enabled/trusted. Chi tiết index và 17 cặp current/history trong [Temporal & Index Assessment](wwi-temporal-index-assessment.md).

**Verified:** Toàn database có 45 clustered B-tree, 99 nonclustered B-tree, một clustered columnstore và hai nonclustered columnstore indexes. `Sales.CustomerTransactions` clustered theo `TransactionDate`; `Sales.Invoices` có nonclustered index trên `ConfirmedDeliveryTime`; `Sales.InvoiceLines.LastEditedWhen` ở nonclustered columnstore; `Warehouse.StockItemTransactions.LastEditedWhen` ở clustered columnstore. Không có B-tree key trên `LastEditedWhen` trong chín bảng MVP. Đây là bằng chứng index hiện có, **không** phải phê duyệt chiến lược incremental.

## 5. Rủi ro nguồn ban đầu

| Mức xác minh | Rủi ro/giới hạn | Ảnh hưởng |
| --- | --- | --- |
| Verified | CDC/Change Tracking đều tắt; WWI gốc phải chỉ đọc | Chưa có change feed được xác minh; cần WWI-04 thiết kế môi trường thử nghiệm độc lập. |
| Verified | Chỉ `Sales.Customers` và `Warehouse.StockItems` temporal trong 9 bảng MVP | Không thể coi Orders/Invoices/Movements có temporal history. |
| Documented but Unverified | `ValidFrom/ValidTo` history có thể không phủ từ đầu mọi giao dịch | Chưa đủ căn cứ ánh xạ SCD2 chính xác theo mọi ngày. |
| Documented but Unverified | `LastEditedWhen` có trên nhiều bảng nhưng không có B-tree key ở MVP | Chưa xác minh completeness, độ trễ hoặc hiệu năng extraction. |
| Verified | `Invoices.OrderID`, `CustomerTransactions.InvoiceID` và nhiều FK movement nullable | Join theo đường bắt buộc có thể loại dòng; cần profile tỷ lệ NULL trước mapping. |
| Documented but Unverified | `IsCreditNote`, `LineProfit`, `CustomerID`/`BillToCustomerID` chưa có quy tắc nghiệp vụ được duyệt | Không định nghĩa revenue, COGS, refund hoặc fact grain ở Phase 1.1. |
| Verified | Client cần tùy chọn tin cậy chứng chỉ TLS local khi dùng `sqlcmd` | Thiết kế kết nối Phase 2 phải xác minh phương án TLS phù hợp, không đưa credential vào repo. |

## 6. Deliverables và SQL kiểm chứng

- [Database Inventory Report](wwi-database-inventory.md): schema, bảng, phân loại và row count metadata.
- [Metadata Dictionary](wwi-metadata-dictionary.md): 9 bảng MVP, 156 cột, PK/UQ/FK.
- [Table Classification & Dependency Summary](wwi-database-inventory.md): nhóm bảng và phụ thuộc Sales/Inventory/Reference/Purchasing.
- [Temporal & Index Assessment](wwi-temporal-index-assessment.md): 17 cặp history và index inventory.
- [SQL metadata queries](wwi-metadata-queries.md): các truy vấn `SELECT` để tái kiểm chứng.
- Tài liệu này là Phase 1.1 Assessment Report.

## 7. Acceptance checklist

| Acceptance Criterion | Evidence | PASS/PARTIAL/FAIL | Remarks |
| --- | --- | --- | --- |
| Database inventory có đủ schema và bảng | 23 schema, 48 bảng từ `sys.schemas`/`sys.tables`; inventory đầy đủ | PASS | Số dòng là metadata estimate. |
| Metadata bảng MVP đầy đủ | 9 bảng, 156 cột trong dictionary; kiểu, NULL, default, computed, versioning | PASS | Chưa profile giá trị dữ liệu. |
| PK/FK được xác minh | 9 PK, 51 FK từ MVP; 98 FK toàn DB, 0 disabled/untrusted | PASS | FK không tự quyết định warehouse grain. |
| Temporal tables xác định chính xác | 17 cặp current/history, period từ `sys.periods` | PASS | Độ phủ lịch sử nghiệp vụ chưa xác minh. |
| Nhận định index có bằng chứng | 59 indexes trên 9 bảng MVP, phân loại B-tree/columnstore và key trong assessment | PASS | Chưa chạy execution plan. |
| Không trình bày giả định chưa xác minh như sự thật | Phân biệt Verified, Documented but Unverified, Proposed trong báo cáo | PASS | Vai trò nghiệp vụ chỉ sơ bộ. |
| Không thay đổi ngoài phạm vi | Chỉ tạo/cập nhật Markdown của WWI-02/Phase 1.1 và trạng thái Phase 1 | PASS | Không triển khai runtime. |
| Liên kết Markdown nội bộ hợp lệ | Kiểm tra 144 liên kết nội bộ sau khi tạo tài liệu, không phát hiện link gãy | PASS | Kiểm tra đích file; không kiểm chứng anchor ngoài repo. |
| Không có credential trong tài liệu | Chỉ ghi phương thức integrated authentication; quét pattern secret trước báo cáo | PASS | Không ghi giá trị kết nối bí mật. |
| Không tác động dữ liệu nguồn | Các lệnh thực thi chỉ là `SELECT` metadata; không DML/DDL | PASS | Không khẳng định nguồn không đổi do tiến trình khác. |

## 8. Open questions và đề xuất Phase 1.2

1. Độ phủ thời gian thực tế của history `Sales.Customers` và `Warehouse.StockItems` đến đâu so với order/invoice dates? **Proposed:** profile min/max và khoảng trống theo cách chỉ đọc, chưa kết luận SCD2.
2. Phân bố NULL và số lượng dòng của các liên kết `Invoices.OrderID`, `CustomerTransactions.InvoiceID`, movement Customer/Invoice/Supplier/PurchaseOrder là bao nhiêu? **Proposed:** dùng `SELECT COUNT(*)` có kiểm soát ở Phase 1.2; không suy từ nullable metadata.
3. `CustomerID` và `BillToCustomerID` dùng cho từng câu hỏi phân tích nào; `IsCreditNote`, `LineProfit`, tax và delivery confirmation có ý nghĩa nghiệp vụ gì? **Proposed:** phối hợp WWI-03, chưa chốt KPI.
4. `LastEditedWhen` có phản ánh mọi UPDATE, có thể trùng timestamp, và xóa được ghi nhận không? **Proposed:** WWI-04 thiết kế kiểm chứng trong môi trường độc lập, không sửa WWI gốc.
5. `StockItemHoldings` và `StockItemTransactions` có đủ thông tin để tái dựng balance theo ngày không? **Proposed:** phân tích opening balance và loại movement trước inventory mart.

Phase 1.2 đã được chủ dự án cho phép riêng và kết quả được ghi tại [báo cáo Phase 1.2](wwi-phase-1-2-assessment.md). Phase 1.3/WWI-03 chưa được phép bắt đầu. WWI-02 tiếp tục `IN_PROGRESS`, chưa đủ điều kiện `DONE`.
