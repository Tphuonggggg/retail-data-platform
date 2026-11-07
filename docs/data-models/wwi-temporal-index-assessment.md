# Đánh giá temporal và index — Phase 1.1

**Trạng thái: Verified từ catalog SQL Server; đánh giá khả năng incremental là Proposed/Documented but Unverified.** Truy vấn `SELECT` trên database WWI ngày 2026-11-07. Không tạo hoặc sửa index, không bật CDC/Change Tracking. Xem [metadata queries](wwi-metadata-queries.md).

## Temporal metadata

`sys.tables` ghi nhận 17 bảng `SYSTEM_VERSIONED_TEMPORAL_TABLE` và 17 history tables. `sys.periods` xác định period columns như sau; số history rows là **metadata estimate** từ `sys.partitions`, không phải `COUNT(*)`.

| Bảng hiện hành | History table | Period start / end | Retention metadata | History rows (metadata) |
| --- | --- | --- | --- | ---: |
| `Application.Cities` | `Application.Cities_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 28 |
| `Application.Countries` | `Application.Countries_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 37 |
| `Application.DeliveryMethods` | `Application.DeliveryMethods_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 1 |
| `Application.PaymentMethods` | `Application.PaymentMethods_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 1 |
| `Application.People` | `Application.People_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 961 |
| `Application.StateProvinces` | `Application.StateProvinces_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 104 |
| `Application.TransactionTypes` | `Application.TransactionTypes_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 1 |
| `Purchasing.SupplierCategories` | `Purchasing.SupplierCategories_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 1 |
| `Purchasing.Suppliers` | `Purchasing.Suppliers_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 13 |
| `Sales.BuyingGroups` | `Sales.BuyingGroups_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 0 |
| `Sales.CustomerCategories` | `Sales.CustomerCategories_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 1 |
| `Sales.Customers` | `Sales.Customers_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 51 |
| `Warehouse.ColdRoomTemperatures` | `Warehouse.ColdRoomTemperatures_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 3,654,736 |
| `Warehouse.Colors` | `Warehouse.Colors_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 1 |
| `Warehouse.PackageTypes` | `Warehouse.PackageTypes_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 0 |
| `Warehouse.StockGroups` | `Warehouse.StockGroups_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 1 |
| `Warehouse.StockItems` | `Warehouse.StockItems_Archive` | `ValidFrom` / `ValidTo` | `-1` / `INFINITE` | 444 |

Trong 9 bảng MVP, chỉ `Sales.Customers` và `Warehouse.StockItems` là system-versioned. `Sales.Orders`, `Sales.OrderLines`, `Sales.Invoices`, `Sales.InvoiceLines`, `Sales.CustomerTransactions`, `Warehouse.StockItemHoldings` và `Warehouse.StockItemTransactions` là `NON_TEMPORAL_TABLE`. Retention `-1 / INFINITE` là thiết lập metadata, **không chứng minh** history bắt đầu từ thời điểm giao dịch đầu tiên hoặc đủ để lookup SCD2 cho mọi ngày.

## Index inventory của 9 bảng MVP

Toàn database có 45 `CLUSTERED`, 99 `NONCLUSTERED`, 1 `CLUSTERED COLUMNSTORE` và 2 `NONCLUSTERED COLUMNSTORE` indexes theo `sys.indexes`. Bảng dưới đây liệt kê index của 9 bảng MVP; cột key để `—` đối với columnstore vì `key_ordinal` không áp dụng. `UQ` là unique index/constraint, không suy ra từ tên.

| Bảng | Index | Loại | Unique / vai trò | Key columns | Filter |
| --- | --- | --- | --- | --- | --- |
| `Sales.Customers` | `PK_Sales_Customers` | `CLUSTERED` | PK | `CustomerID` | — |
| `Sales.Customers` | `UQ_Sales_Customers_CustomerName` | `NONCLUSTERED` | UQ | `CustomerName` | — |
| `Sales.Customers` | `FK_Sales_Customers_CustomerCategoryID` | `NONCLUSTERED` | — | `CustomerCategoryID` | — |
| `Sales.Customers` | `FK_Sales_Customers_BuyingGroupID` | `NONCLUSTERED` | — | `BuyingGroupID` | — |
| `Sales.Customers` | `FK_Sales_Customers_PrimaryContactPersonID` | `NONCLUSTERED` | — | `PrimaryContactPersonID` | — |
| `Sales.Customers` | `FK_Sales_Customers_AlternateContactPersonID` | `NONCLUSTERED` | — | `AlternateContactPersonID` | — |
| `Sales.Customers` | `FK_Sales_Customers_DeliveryMethodID` | `NONCLUSTERED` | — | `DeliveryMethodID` | — |
| `Sales.Customers` | `FK_Sales_Customers_DeliveryCityID` | `NONCLUSTERED` | — | `DeliveryCityID` | — |
| `Sales.Customers` | `FK_Sales_Customers_PostalCityID` | `NONCLUSTERED` | — | `PostalCityID` | — |
| `Sales.Customers` | `IX_Sales_Customers_Perf_20160301_06` | `NONCLUSTERED` | — | `IsOnCreditHold,CustomerID,BillToCustomerID` | — |
| `Sales.CustomerTransactions` | `CX_Sales_CustomerTransactions` | `CLUSTERED` | — | `TransactionDate` | — |
| `Sales.CustomerTransactions` | `FK_Sales_CustomerTransactions_CustomerID` | `NONCLUSTERED` | — | `CustomerID` | — |
| `Sales.CustomerTransactions` | `FK_Sales_CustomerTransactions_TransactionTypeID` | `NONCLUSTERED` | — | `TransactionTypeID` | — |
| `Sales.CustomerTransactions` | `FK_Sales_CustomerTransactions_InvoiceID` | `NONCLUSTERED` | — | `InvoiceID` | — |
| `Sales.CustomerTransactions` | `FK_Sales_CustomerTransactions_PaymentMethodID` | `NONCLUSTERED` | — | `PaymentMethodID` | — |
| `Sales.CustomerTransactions` | `IX_Sales_CustomerTransactions_IsFinalized` | `NONCLUSTERED` | — | `IsFinalized` | — |
| `Sales.CustomerTransactions` | `PK_Sales_CustomerTransactions` | `NONCLUSTERED` | PK | `CustomerTransactionID` | — |
| `Sales.InvoiceLines` | `PK_Sales_InvoiceLines` | `CLUSTERED` | PK | `InvoiceLineID` | — |
| `Sales.InvoiceLines` | `FK_Sales_InvoiceLines_InvoiceID` | `NONCLUSTERED` | — | `InvoiceID` | — |
| `Sales.InvoiceLines` | `FK_Sales_InvoiceLines_StockItemID` | `NONCLUSTERED` | — | `StockItemID` | — |
| `Sales.InvoiceLines` | `FK_Sales_InvoiceLines_PackageTypeID` | `NONCLUSTERED` | — | `PackageTypeID` | — |
| `Sales.InvoiceLines` | `NCCX_Sales_InvoiceLines` | `NONCLUSTERED COLUMNSTORE` | — | — | — |
| `Sales.Invoices` | `PK_Sales_Invoices` | `CLUSTERED` | PK | `InvoiceID` | — |
| `Sales.Invoices` | `FK_Sales_Invoices_CustomerID` | `NONCLUSTERED` | — | `CustomerID` | — |
| `Sales.Invoices` | `FK_Sales_Invoices_BillToCustomerID` | `NONCLUSTERED` | — | `BillToCustomerID` | — |
| `Sales.Invoices` | `FK_Sales_Invoices_OrderID` | `NONCLUSTERED` | — | `OrderID` | — |
| `Sales.Invoices` | `FK_Sales_Invoices_DeliveryMethodID` | `NONCLUSTERED` | — | `DeliveryMethodID` | — |
| `Sales.Invoices` | `FK_Sales_Invoices_ContactPersonID` | `NONCLUSTERED` | — | `ContactPersonID` | — |
| `Sales.Invoices` | `FK_Sales_Invoices_AccountsPersonID` | `NONCLUSTERED` | — | `AccountsPersonID` | — |
| `Sales.Invoices` | `FK_Sales_Invoices_SalespersonPersonID` | `NONCLUSTERED` | — | `SalespersonPersonID` | — |
| `Sales.Invoices` | `FK_Sales_Invoices_PackedByPersonID` | `NONCLUSTERED` | — | `PackedByPersonID` | — |
| `Sales.Invoices` | `IX_Sales_Invoices_ConfirmedDeliveryTime` | `NONCLUSTERED` | — | `ConfirmedDeliveryTime` | — |
| `Sales.OrderLines` | `PK_Sales_OrderLines` | `CLUSTERED` | PK | `OrderLineID` | — |
| `Sales.OrderLines` | `FK_Sales_OrderLines_OrderID` | `NONCLUSTERED` | — | `OrderID` | — |
| `Sales.OrderLines` | `FK_Sales_OrderLines_PackageTypeID` | `NONCLUSTERED` | — | `PackageTypeID` | — |
| `Sales.OrderLines` | `IX_Sales_OrderLines_AllocatedStockItems` | `NONCLUSTERED` | — | `StockItemID` | — |
| `Sales.OrderLines` | `IX_Sales_OrderLines_Perf_20160301_01` | `NONCLUSTERED` | — | `PickingCompletedWhen,OrderID,OrderLineID` | — |
| `Sales.OrderLines` | `IX_Sales_OrderLines_Perf_20160301_02` | `NONCLUSTERED` | — | `StockItemID,PickingCompletedWhen` | — |
| `Sales.OrderLines` | `NCCX_Sales_OrderLines` | `NONCLUSTERED COLUMNSTORE` | — | — | — |
| `Sales.Orders` | `PK_Sales_Orders` | `CLUSTERED` | PK | `OrderID` | — |
| `Sales.Orders` | `FK_Sales_Orders_CustomerID` | `NONCLUSTERED` | — | `CustomerID` | — |
| `Sales.Orders` | `FK_Sales_Orders_SalespersonPersonID` | `NONCLUSTERED` | — | `SalespersonPersonID` | — |
| `Sales.Orders` | `FK_Sales_Orders_PickedByPersonID` | `NONCLUSTERED` | — | `PickedByPersonID` | — |
| `Sales.Orders` | `FK_Sales_Orders_ContactPersonID` | `NONCLUSTERED` | — | `ContactPersonID` | — |
| `Warehouse.StockItemHoldings` | `PK_Warehouse_StockItemHoldings` | `CLUSTERED` | PK | `StockItemID` | — |
| `Warehouse.StockItems` | `PK_Warehouse_StockItems` | `CLUSTERED` | PK | `StockItemID` | — |
| `Warehouse.StockItems` | `UQ_Warehouse_StockItems_StockItemName` | `NONCLUSTERED` | UQ | `StockItemName` | — |
| `Warehouse.StockItems` | `FK_Warehouse_StockItems_SupplierID` | `NONCLUSTERED` | — | `SupplierID` | — |
| `Warehouse.StockItems` | `FK_Warehouse_StockItems_ColorID` | `NONCLUSTERED` | — | `ColorID` | — |
| `Warehouse.StockItems` | `FK_Warehouse_StockItems_UnitPackageID` | `NONCLUSTERED` | — | `UnitPackageID` | — |
| `Warehouse.StockItems` | `FK_Warehouse_StockItems_OuterPackageID` | `NONCLUSTERED` | — | `OuterPackageID` | — |
| `Warehouse.StockItemTransactions` | `CCX_Warehouse_StockItemTransactions` | `CLUSTERED COLUMNSTORE` | — | — | — |
| `Warehouse.StockItemTransactions` | `FK_Warehouse_StockItemTransactions_StockItemID` | `NONCLUSTERED` | — | `StockItemID` | — |
| `Warehouse.StockItemTransactions` | `FK_Warehouse_StockItemTransactions_TransactionTypeID` | `NONCLUSTERED` | — | `TransactionTypeID` | — |
| `Warehouse.StockItemTransactions` | `FK_Warehouse_StockItemTransactions_CustomerID` | `NONCLUSTERED` | — | `CustomerID` | — |
| `Warehouse.StockItemTransactions` | `FK_Warehouse_StockItemTransactions_InvoiceID` | `NONCLUSTERED` | — | `InvoiceID` | — |
| `Warehouse.StockItemTransactions` | `FK_Warehouse_StockItemTransactions_SupplierID` | `NONCLUSTERED` | — | `SupplierID` | — |
| `Warehouse.StockItemTransactions` | `FK_Warehouse_StockItemTransactions_PurchaseOrderID` | `NONCLUSTERED` | — | `PurchaseOrderID` | — |
| `Warehouse.StockItemTransactions` | `PK_Warehouse_StockItemTransactions` | `NONCLUSTERED` | PK | `StockItemTransactionID` | — |

## CDC, Change Tracking và tính phù hợp cho incremental

- `sys.databases.is_cdc_enabled = 0`; `sys.change_tracking_databases` không có dòng cho WWI; `sys.change_tracking_tables` có 0 dòng; `sys.tables.is_tracked_by_cdc` có 0 bảng. **Verified metadata**, không phải bằng chứng rằng mọi thay đổi nguồn đều có thể quan sát.
- `Sales.CustomerTransactions` có clustered B-tree trên `TransactionDate`; các nonclustered FK indexes cũng mang `TransactionDate` dưới dạng partition column. Đây là business date, chưa chứng minh là update watermark.
- `Sales.Invoices` có B-tree `IX_Sales_Invoices_ConfirmedDeliveryTime` trên `ConfirmedDeliveryTime`; `Sales.OrderLines` có B-tree liên quan `PickingCompletedWhen`. Chúng chỉ hỗ trợ truy vấn theo cột đó, chưa bảo đảm phát hiện mọi INSERT/UPDATE/DELETE.
- `Sales.InvoiceLines.LastEditedWhen` nằm trong nonclustered columnstore `NCCX_Sales_InvoiceLines`; `Warehouse.StockItemTransactions.LastEditedWhen` và `TransactionOccurredWhen` nằm trong clustered columnstore `CCX_Warehouse_StockItemTransactions`. Columnstore membership không phải ordered B-tree seek.
- Không thấy B-tree index dùng `LastEditedWhen` làm key trong 9 bảng MVP qua `sys.index_columns`. `Sales.Customers` và `Warehouse.StockItems` có period columns, nhưng không được giả định chúng thay thế change feed.
- **Proposed cho WWI-04:** khảo sát riêng tính đơn điệu/độ trễ của `LastEditedWhen`, tie-breaker theo PK, khả năng phát hiện delete, lịch sử as-of, ảnh hưởng của columnstore/partition và phương án môi trường thử nghiệm độc lập. Không chốt watermark trong Phase 1.1.

Xem [database inventory](wwi-database-inventory.md) và [assessment](wwi-phase-1-1-assessment.md).
