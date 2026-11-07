# Metadata dictionary các bảng MVP — Phase 1.1

**Trạng thái: Verified từ `sys.tables`, `sys.columns`, `sys.types`, `sys.default_constraints`, `sys.key_constraints` và `sys.foreign_keys`.** Khảo sát 2026-11-07 trên `WideWorldImporters` bằng truy vấn `SELECT` chỉ đọc. Đây là metadata schema, chưa kiểm tra giá trị thực tế hoặc chốt warehouse grain. Xem [metadata queries](wwi-metadata-queries.md).

Quy ước: `NULL = Có/Không` phản ánh `sys.columns.is_nullable`; độ dài `nchar/nvarchar` tính theo ký tự (metadata `max_length` tính theo byte); `max` là `max_length=-1`. Default hiển thị `constraint_name: definition`; `sequence` là default expression, không phải identity. `PK` và `UQ` lấy từ key constraints; `FK` lấy từ foreign key constraints. `computed` và `AS_ROW_START/END` là metadata cột, không phải bằng chứng semantics nghiệp vụ. Tất cả 9 bảng có PK; 51 FK xuất phát từ các bảng này đều enabled và trusted theo metadata.

## `Sales.Customers` (31 cột)

Customer master; `BillToCustomerID` tự tham chiếu, không tự đồng nhất với `CustomerID` trong KPI.

| Cột | SQL type | NULL | Default constraint | Tạo tự động / version | Khóa / FK |
| --- | --- | --- | --- | --- | --- |
| `CustomerID` | `int` | Không | `DF_Sales_Customers_CustomerID`: `(NEXT VALUE FOR [Sequences].[CustomerID])` | — | PK |
| `CustomerName` | `nvarchar(100)` | Không | — | — | UQ |
| `BillToCustomerID` | `int` | Không | — | — | FK → `Sales.Customers.CustomerID` |
| `CustomerCategoryID` | `int` | Không | — | — | FK → `Sales.CustomerCategories.CustomerCategoryID` |
| `BuyingGroupID` | `int` | Có | — | — | FK → `Sales.BuyingGroups.BuyingGroupID` |
| `PrimaryContactPersonID` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `AlternateContactPersonID` | `int` | Có | — | — | FK → `Application.People.PersonID` |
| `DeliveryMethodID` | `int` | Không | — | — | FK → `Application.DeliveryMethods.DeliveryMethodID` |
| `DeliveryCityID` | `int` | Không | — | — | FK → `Application.Cities.CityID` |
| `PostalCityID` | `int` | Không | — | — | FK → `Application.Cities.CityID` |
| `CreditLimit` | `decimal(18,2)` | Có | — | — | — |
| `AccountOpenedDate` | `date` | Không | — | — | — |
| `StandardDiscountPercentage` | `decimal(18,3)` | Không | — | — | — |
| `IsStatementSent` | `bit` | Không | — | — | — |
| `IsOnCreditHold` | `bit` | Không | — | — | — |
| `PaymentDays` | `int` | Không | — | — | — |
| `PhoneNumber` | `nvarchar(20)` | Không | — | — | — |
| `FaxNumber` | `nvarchar(20)` | Không | — | — | — |
| `DeliveryRun` | `nvarchar(5)` | Có | — | — | — |
| `RunPosition` | `nvarchar(5)` | Có | — | — | — |
| `WebsiteURL` | `nvarchar(256)` | Không | — | — | — |
| `DeliveryAddressLine1` | `nvarchar(60)` | Không | — | — | — |
| `DeliveryAddressLine2` | `nvarchar(60)` | Có | — | — | — |
| `DeliveryPostalCode` | `nvarchar(10)` | Không | — | — | — |
| `DeliveryLocation` | `geography` | Có | — | — | — |
| `PostalAddressLine1` | `nvarchar(60)` | Không | — | — | — |
| `PostalAddressLine2` | `nvarchar(60)` | Có | — | — | — |
| `PostalPostalCode` | `nvarchar(10)` | Không | — | — | — |
| `LastEditedBy` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `ValidFrom` | `datetime2(7)` | Không | — | AS_ROW_START | — |
| `ValidTo` | `datetime2(7)` | Không | — | AS_ROW_END | — |

## `Sales.Orders` (16 cột)

Order header; `BackorderOrderID` tự tham chiếu nullable.

| Cột | SQL type | NULL | Default constraint | Tạo tự động / version | Khóa / FK |
| --- | --- | --- | --- | --- | --- |
| `OrderID` | `int` | Không | `DF_Sales_Orders_OrderID`: `(NEXT VALUE FOR [Sequences].[OrderID])` | — | PK |
| `CustomerID` | `int` | Không | — | — | FK → `Sales.Customers.CustomerID` |
| `SalespersonPersonID` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `PickedByPersonID` | `int` | Có | — | — | FK → `Application.People.PersonID` |
| `ContactPersonID` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `BackorderOrderID` | `int` | Có | — | — | FK → `Sales.Orders.OrderID` |
| `OrderDate` | `date` | Không | — | — | — |
| `ExpectedDeliveryDate` | `date` | Không | — | — | — |
| `CustomerPurchaseOrderNumber` | `nvarchar(20)` | Có | — | — | — |
| `IsUndersupplyBackordered` | `bit` | Không | — | — | — |
| `Comments` | `nvarchar(max)` | Có | — | — | — |
| `DeliveryInstructions` | `nvarchar(max)` | Có | — | — | — |
| `InternalComments` | `nvarchar(max)` | Có | — | — | — |
| `PickingCompletedWhen` | `datetime2(7)` | Có | — | — | — |
| `LastEditedBy` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `LastEditedWhen` | `datetime2(7)` | Không | `DF_Sales_Orders_LastEditedWhen`: `(sysdatetime())` | — | — |

## `Sales.OrderLines` (12 cột)

Dòng order và trạng thái picking; khác grain với invoice line.

| Cột | SQL type | NULL | Default constraint | Tạo tự động / version | Khóa / FK |
| --- | --- | --- | --- | --- | --- |
| `OrderLineID` | `int` | Không | `DF_Sales_OrderLines_OrderLineID`: `(NEXT VALUE FOR [Sequences].[OrderLineID])` | — | PK |
| `OrderID` | `int` | Không | — | — | FK → `Sales.Orders.OrderID` |
| `StockItemID` | `int` | Không | — | — | FK → `Warehouse.StockItems.StockItemID` |
| `Description` | `nvarchar(100)` | Không | — | — | — |
| `PackageTypeID` | `int` | Không | — | — | FK → `Warehouse.PackageTypes.PackageTypeID` |
| `Quantity` | `int` | Không | — | — | — |
| `UnitPrice` | `decimal(18,2)` | Có | — | — | — |
| `TaxRate` | `decimal(18,3)` | Không | — | — | — |
| `PickedQuantity` | `int` | Không | — | — | — |
| `PickingCompletedWhen` | `datetime2(7)` | Có | — | — | — |
| `LastEditedBy` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `LastEditedWhen` | `datetime2(7)` | Không | `DF_Sales_OrderLines_LastEditedWhen`: `(sysdatetime())` | — | — |

## `Sales.Invoices` (25 cột)

Invoice header; `OrderID` có thể NULL; `ConfirmedDeliveryTime` là computed nullable.

| Cột | SQL type | NULL | Default constraint | Tạo tự động / version | Khóa / FK |
| --- | --- | --- | --- | --- | --- |
| `InvoiceID` | `int` | Không | `DF_Sales_Invoices_InvoiceID`: `(NEXT VALUE FOR [Sequences].[InvoiceID])` | — | PK |
| `CustomerID` | `int` | Không | — | — | FK → `Sales.Customers.CustomerID` |
| `BillToCustomerID` | `int` | Không | — | — | FK → `Sales.Customers.CustomerID` |
| `OrderID` | `int` | Có | — | — | FK → `Sales.Orders.OrderID` |
| `DeliveryMethodID` | `int` | Không | — | — | FK → `Application.DeliveryMethods.DeliveryMethodID` |
| `ContactPersonID` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `AccountsPersonID` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `SalespersonPersonID` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `PackedByPersonID` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `InvoiceDate` | `date` | Không | — | — | — |
| `CustomerPurchaseOrderNumber` | `nvarchar(20)` | Có | — | — | — |
| `IsCreditNote` | `bit` | Không | — | — | — |
| `CreditNoteReason` | `nvarchar(max)` | Có | — | — | — |
| `Comments` | `nvarchar(max)` | Có | — | — | — |
| `DeliveryInstructions` | `nvarchar(max)` | Có | — | — | — |
| `InternalComments` | `nvarchar(max)` | Có | — | — | — |
| `TotalDryItems` | `int` | Không | — | — | — |
| `TotalChillerItems` | `int` | Không | — | — | — |
| `DeliveryRun` | `nvarchar(5)` | Có | — | — | — |
| `RunPosition` | `nvarchar(5)` | Có | — | — | — |
| `ReturnedDeliveryData` | `nvarchar(max)` | Có | — | — | — |
| `ConfirmedDeliveryTime` | `datetime2(7)` | Có | — | computed | — |
| `ConfirmedReceivedBy` | `nvarchar(4000)` | Có | — | computed | — |
| `LastEditedBy` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `LastEditedWhen` | `datetime2(7)` | Không | `DF_Sales_Invoices_LastEditedWhen`: `(sysdatetime())` | — | — |

## `Sales.InvoiceLines` (13 cột)

Dòng invoice; có `LineProfit` nhưng ý nghĩa nghiệp vụ còn mở.

| Cột | SQL type | NULL | Default constraint | Tạo tự động / version | Khóa / FK |
| --- | --- | --- | --- | --- | --- |
| `InvoiceLineID` | `int` | Không | `DF_Sales_InvoiceLines_InvoiceLineID`: `(NEXT VALUE FOR [Sequences].[InvoiceLineID])` | — | PK |
| `InvoiceID` | `int` | Không | — | — | FK → `Sales.Invoices.InvoiceID` |
| `StockItemID` | `int` | Không | — | — | FK → `Warehouse.StockItems.StockItemID` |
| `Description` | `nvarchar(100)` | Không | — | — | — |
| `PackageTypeID` | `int` | Không | — | — | FK → `Warehouse.PackageTypes.PackageTypeID` |
| `Quantity` | `int` | Không | — | — | — |
| `UnitPrice` | `decimal(18,2)` | Có | — | — | — |
| `TaxRate` | `decimal(18,3)` | Không | — | — | — |
| `TaxAmount` | `decimal(18,2)` | Không | — | — | — |
| `LineProfit` | `decimal(18,2)` | Không | — | — | — |
| `ExtendedPrice` | `decimal(18,2)` | Không | — | — | — |
| `LastEditedBy` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `LastEditedWhen` | `datetime2(7)` | Không | `DF_Sales_InvoiceLines_LastEditedWhen`: `(sysdatetime())` | — | — |

## `Sales.CustomerTransactions` (14 cột)

Giao dịch khách hàng; `InvoiceID` và `PaymentMethodID` có thể NULL.

| Cột | SQL type | NULL | Default constraint | Tạo tự động / version | Khóa / FK |
| --- | --- | --- | --- | --- | --- |
| `CustomerTransactionID` | `int` | Không | `DF_Sales_CustomerTransactions_CustomerTransactionID`: `(NEXT VALUE FOR [Sequences].[TransactionID])` | — | PK |
| `CustomerID` | `int` | Không | — | — | FK → `Sales.Customers.CustomerID` |
| `TransactionTypeID` | `int` | Không | — | — | FK → `Application.TransactionTypes.TransactionTypeID` |
| `InvoiceID` | `int` | Có | — | — | FK → `Sales.Invoices.InvoiceID` |
| `PaymentMethodID` | `int` | Có | — | — | FK → `Application.PaymentMethods.PaymentMethodID` |
| `TransactionDate` | `date` | Không | — | — | — |
| `AmountExcludingTax` | `decimal(18,2)` | Không | — | — | — |
| `TaxAmount` | `decimal(18,2)` | Không | — | — | — |
| `TransactionAmount` | `decimal(18,2)` | Không | — | — | — |
| `OutstandingBalance` | `decimal(18,2)` | Không | — | — | — |
| `FinalizationDate` | `date` | Có | — | — | — |
| `IsFinalized` | `bit` | Có | — | computed | — |
| `LastEditedBy` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `LastEditedWhen` | `datetime2(7)` | Không | `DF_Sales_CustomerTransactions_LastEditedWhen`: `(sysdatetime())` | — | — |

## `Warehouse.StockItems` (25 cột)

Stock item master; có temporal history và FK tới Purchasing supplier.

| Cột | SQL type | NULL | Default constraint | Tạo tự động / version | Khóa / FK |
| --- | --- | --- | --- | --- | --- |
| `StockItemID` | `int` | Không | `DF_Warehouse_StockItems_StockItemID`: `(NEXT VALUE FOR [Sequences].[StockItemID])` | — | PK |
| `StockItemName` | `nvarchar(100)` | Không | — | — | UQ |
| `SupplierID` | `int` | Không | — | — | FK → `Purchasing.Suppliers.SupplierID` |
| `ColorID` | `int` | Có | — | — | FK → `Warehouse.Colors.ColorID` |
| `UnitPackageID` | `int` | Không | — | — | FK → `Warehouse.PackageTypes.PackageTypeID` |
| `OuterPackageID` | `int` | Không | — | — | FK → `Warehouse.PackageTypes.PackageTypeID` |
| `Brand` | `nvarchar(50)` | Có | — | — | — |
| `Size` | `nvarchar(20)` | Có | — | — | — |
| `LeadTimeDays` | `int` | Không | — | — | — |
| `QuantityPerOuter` | `int` | Không | — | — | — |
| `IsChillerStock` | `bit` | Không | — | — | — |
| `Barcode` | `nvarchar(50)` | Có | — | — | — |
| `TaxRate` | `decimal(18,3)` | Không | — | — | — |
| `UnitPrice` | `decimal(18,2)` | Không | — | — | — |
| `RecommendedRetailPrice` | `decimal(18,2)` | Có | — | — | — |
| `TypicalWeightPerUnit` | `decimal(18,3)` | Không | — | — | — |
| `MarketingComments` | `nvarchar(max)` | Có | — | — | — |
| `InternalComments` | `nvarchar(max)` | Có | — | — | — |
| `Photo` | `varbinary(max)` | Có | — | — | — |
| `CustomFields` | `nvarchar(max)` | Có | — | — | — |
| `Tags` | `nvarchar(max)` | Có | — | computed | — |
| `SearchDetails` | `nvarchar(max)` | Không | — | computed | — |
| `LastEditedBy` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `ValidFrom` | `datetime2(7)` | Không | — | AS_ROW_START | — |
| `ValidTo` | `datetime2(7)` | Không | — | AS_ROW_END | — |

## `Warehouse.StockItemHoldings` (9 cột)

Tồn hiện tại theo `StockItemID`; không là lịch sử daily balance.

| Cột | SQL type | NULL | Default constraint | Tạo tự động / version | Khóa / FK |
| --- | --- | --- | --- | --- | --- |
| `StockItemID` | `int` | Không | — | — | PK; FK → `Warehouse.StockItems.StockItemID` |
| `QuantityOnHand` | `int` | Không | — | — | — |
| `BinLocation` | `nvarchar(20)` | Không | — | — | — |
| `LastStocktakeQuantity` | `int` | Không | — | — | — |
| `LastCostPrice` | `decimal(18,2)` | Không | — | — | — |
| `ReorderLevel` | `int` | Không | — | — | — |
| `TargetStockLevel` | `int` | Không | — | — | — |
| `LastEditedBy` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `LastEditedWhen` | `datetime2(7)` | Không | `DF_Warehouse_StockItemHoldings_LastEditedWhen`: `(sysdatetime())` | — | — |

## `Warehouse.StockItemTransactions` (11 cột)

Movement; các liên kết Customer/Invoice/Supplier/PurchaseOrder đều nullable.

| Cột | SQL type | NULL | Default constraint | Tạo tự động / version | Khóa / FK |
| --- | --- | --- | --- | --- | --- |
| `StockItemTransactionID` | `int` | Không | `DF_Warehouse_StockItemTransactions_StockItemTransactionID`: `(NEXT VALUE FOR [Sequences].[TransactionID])` | — | PK |
| `StockItemID` | `int` | Không | — | — | FK → `Warehouse.StockItems.StockItemID` |
| `TransactionTypeID` | `int` | Không | — | — | FK → `Application.TransactionTypes.TransactionTypeID` |
| `CustomerID` | `int` | Có | — | — | FK → `Sales.Customers.CustomerID` |
| `InvoiceID` | `int` | Có | — | — | FK → `Sales.Invoices.InvoiceID` |
| `SupplierID` | `int` | Có | — | — | FK → `Purchasing.Suppliers.SupplierID` |
| `PurchaseOrderID` | `int` | Có | — | — | FK → `Purchasing.PurchaseOrders.PurchaseOrderID` |
| `TransactionOccurredWhen` | `datetime2(7)` | Không | — | — | — |
| `Quantity` | `decimal(18,3)` | Không | — | — | — |
| `LastEditedBy` | `int` | Không | — | — | FK → `Application.People.PersonID` |
| `LastEditedWhen` | `datetime2(7)` | Không | `DF_Warehouse_StockItemTransactions_LastEditedWhen`: `(sysdatetime())` | — | — |

## Constraint inventory đã xác minh

| Bảng | Loại | Constraint | Cột / tham chiếu |
| --- | --- | --- | --- |
| `Sales.Customers` | PK | `PK_Sales_Customers` | `CustomerID` |
| `Sales.Customers` | UQ | `UQ_Sales_Customers_CustomerName` | `CustomerName` |
| `Sales.CustomerTransactions` | PK | `PK_Sales_CustomerTransactions` | `CustomerTransactionID` |
| `Sales.InvoiceLines` | PK | `PK_Sales_InvoiceLines` | `InvoiceLineID` |
| `Sales.Invoices` | PK | `PK_Sales_Invoices` | `InvoiceID` |
| `Sales.OrderLines` | PK | `PK_Sales_OrderLines` | `OrderLineID` |
| `Sales.Orders` | PK | `PK_Sales_Orders` | `OrderID` |
| `Warehouse.StockItemHoldings` | PK | `PK_Warehouse_StockItemHoldings` | `StockItemID` |
| `Warehouse.StockItems` | PK | `PK_Warehouse_StockItems` | `StockItemID` |
| `Warehouse.StockItems` | UQ | `UQ_Warehouse_StockItems_StockItemName` | `StockItemName` |
| `Warehouse.StockItemTransactions` | PK | `PK_Warehouse_StockItemTransactions` | `StockItemTransactionID` |
| `Sales.Customers` | FK | `FK_Sales_Customers_AlternateContactPersonID_Application_People` | `AlternateContactPersonID` → `Application.People.PersonID` |
| `Sales.Customers` | FK | `FK_Sales_Customers_Application_People` | `LastEditedBy` → `Application.People.PersonID` |
| `Sales.Customers` | FK | `FK_Sales_Customers_BillToCustomerID_Sales_Customers` | `BillToCustomerID` → `Sales.Customers.CustomerID` |
| `Sales.Customers` | FK | `FK_Sales_Customers_BuyingGroupID_Sales_BuyingGroups` | `BuyingGroupID` → `Sales.BuyingGroups.BuyingGroupID` |
| `Sales.Customers` | FK | `FK_Sales_Customers_CustomerCategoryID_Sales_CustomerCategories` | `CustomerCategoryID` → `Sales.CustomerCategories.CustomerCategoryID` |
| `Sales.Customers` | FK | `FK_Sales_Customers_DeliveryCityID_Application_Cities` | `DeliveryCityID` → `Application.Cities.CityID` |
| `Sales.Customers` | FK | `FK_Sales_Customers_DeliveryMethodID_Application_DeliveryMethods` | `DeliveryMethodID` → `Application.DeliveryMethods.DeliveryMethodID` |
| `Sales.Customers` | FK | `FK_Sales_Customers_PostalCityID_Application_Cities` | `PostalCityID` → `Application.Cities.CityID` |
| `Sales.Customers` | FK | `FK_Sales_Customers_PrimaryContactPersonID_Application_People` | `PrimaryContactPersonID` → `Application.People.PersonID` |
| `Sales.CustomerTransactions` | FK | `FK_Sales_CustomerTransactions_Application_People` | `LastEditedBy` → `Application.People.PersonID` |
| `Sales.CustomerTransactions` | FK | `FK_Sales_CustomerTransactions_CustomerID_Sales_Customers` | `CustomerID` → `Sales.Customers.CustomerID` |
| `Sales.CustomerTransactions` | FK | `FK_Sales_CustomerTransactions_InvoiceID_Sales_Invoices` | `InvoiceID` → `Sales.Invoices.InvoiceID` |
| `Sales.CustomerTransactions` | FK | `FK_Sales_CustomerTransactions_PaymentMethodID_Application_PaymentMethods` | `PaymentMethodID` → `Application.PaymentMethods.PaymentMethodID` |
| `Sales.CustomerTransactions` | FK | `FK_Sales_CustomerTransactions_TransactionTypeID_Application_TransactionTypes` | `TransactionTypeID` → `Application.TransactionTypes.TransactionTypeID` |
| `Sales.InvoiceLines` | FK | `FK_Sales_InvoiceLines_Application_People` | `LastEditedBy` → `Application.People.PersonID` |
| `Sales.InvoiceLines` | FK | `FK_Sales_InvoiceLines_InvoiceID_Sales_Invoices` | `InvoiceID` → `Sales.Invoices.InvoiceID` |
| `Sales.InvoiceLines` | FK | `FK_Sales_InvoiceLines_PackageTypeID_Warehouse_PackageTypes` | `PackageTypeID` → `Warehouse.PackageTypes.PackageTypeID` |
| `Sales.InvoiceLines` | FK | `FK_Sales_InvoiceLines_StockItemID_Warehouse_StockItems` | `StockItemID` → `Warehouse.StockItems.StockItemID` |
| `Sales.Invoices` | FK | `FK_Sales_Invoices_AccountsPersonID_Application_People` | `AccountsPersonID` → `Application.People.PersonID` |
| `Sales.Invoices` | FK | `FK_Sales_Invoices_Application_People` | `LastEditedBy` → `Application.People.PersonID` |
| `Sales.Invoices` | FK | `FK_Sales_Invoices_BillToCustomerID_Sales_Customers` | `BillToCustomerID` → `Sales.Customers.CustomerID` |
| `Sales.Invoices` | FK | `FK_Sales_Invoices_ContactPersonID_Application_People` | `ContactPersonID` → `Application.People.PersonID` |
| `Sales.Invoices` | FK | `FK_Sales_Invoices_CustomerID_Sales_Customers` | `CustomerID` → `Sales.Customers.CustomerID` |
| `Sales.Invoices` | FK | `FK_Sales_Invoices_DeliveryMethodID_Application_DeliveryMethods` | `DeliveryMethodID` → `Application.DeliveryMethods.DeliveryMethodID` |
| `Sales.Invoices` | FK | `FK_Sales_Invoices_OrderID_Sales_Orders` | `OrderID` → `Sales.Orders.OrderID` |
| `Sales.Invoices` | FK | `FK_Sales_Invoices_PackedByPersonID_Application_People` | `PackedByPersonID` → `Application.People.PersonID` |
| `Sales.Invoices` | FK | `FK_Sales_Invoices_SalespersonPersonID_Application_People` | `SalespersonPersonID` → `Application.People.PersonID` |
| `Sales.OrderLines` | FK | `FK_Sales_OrderLines_Application_People` | `LastEditedBy` → `Application.People.PersonID` |
| `Sales.OrderLines` | FK | `FK_Sales_OrderLines_OrderID_Sales_Orders` | `OrderID` → `Sales.Orders.OrderID` |
| `Sales.OrderLines` | FK | `FK_Sales_OrderLines_PackageTypeID_Warehouse_PackageTypes` | `PackageTypeID` → `Warehouse.PackageTypes.PackageTypeID` |
| `Sales.OrderLines` | FK | `FK_Sales_OrderLines_StockItemID_Warehouse_StockItems` | `StockItemID` → `Warehouse.StockItems.StockItemID` |
| `Sales.Orders` | FK | `FK_Sales_Orders_Application_People` | `LastEditedBy` → `Application.People.PersonID` |
| `Sales.Orders` | FK | `FK_Sales_Orders_BackorderOrderID_Sales_Orders` | `BackorderOrderID` → `Sales.Orders.OrderID` |
| `Sales.Orders` | FK | `FK_Sales_Orders_ContactPersonID_Application_People` | `ContactPersonID` → `Application.People.PersonID` |
| `Sales.Orders` | FK | `FK_Sales_Orders_CustomerID_Sales_Customers` | `CustomerID` → `Sales.Customers.CustomerID` |
| `Sales.Orders` | FK | `FK_Sales_Orders_PickedByPersonID_Application_People` | `PickedByPersonID` → `Application.People.PersonID` |
| `Sales.Orders` | FK | `FK_Sales_Orders_SalespersonPersonID_Application_People` | `SalespersonPersonID` → `Application.People.PersonID` |
| `Warehouse.StockItemHoldings` | FK | `FK_Warehouse_StockItemHoldings_Application_People` | `LastEditedBy` → `Application.People.PersonID` |
| `Warehouse.StockItemHoldings` | FK | `PKFK_Warehouse_StockItemHoldings_StockItemID_Warehouse_StockItems` | `StockItemID` → `Warehouse.StockItems.StockItemID` |
| `Warehouse.StockItems` | FK | `FK_Warehouse_StockItems_Application_People` | `LastEditedBy` → `Application.People.PersonID` |
| `Warehouse.StockItems` | FK | `FK_Warehouse_StockItems_ColorID_Warehouse_Colors` | `ColorID` → `Warehouse.Colors.ColorID` |
| `Warehouse.StockItems` | FK | `FK_Warehouse_StockItems_OuterPackageID_Warehouse_PackageTypes` | `OuterPackageID` → `Warehouse.PackageTypes.PackageTypeID` |
| `Warehouse.StockItems` | FK | `FK_Warehouse_StockItems_SupplierID_Purchasing_Suppliers` | `SupplierID` → `Purchasing.Suppliers.SupplierID` |
| `Warehouse.StockItems` | FK | `FK_Warehouse_StockItems_UnitPackageID_Warehouse_PackageTypes` | `UnitPackageID` → `Warehouse.PackageTypes.PackageTypeID` |
| `Warehouse.StockItemTransactions` | FK | `FK_Warehouse_StockItemTransactions_Application_People` | `LastEditedBy` → `Application.People.PersonID` |
| `Warehouse.StockItemTransactions` | FK | `FK_Warehouse_StockItemTransactions_CustomerID_Sales_Customers` | `CustomerID` → `Sales.Customers.CustomerID` |
| `Warehouse.StockItemTransactions` | FK | `FK_Warehouse_StockItemTransactions_InvoiceID_Sales_Invoices` | `InvoiceID` → `Sales.Invoices.InvoiceID` |
| `Warehouse.StockItemTransactions` | FK | `FK_Warehouse_StockItemTransactions_PurchaseOrderID_Purchasing_PurchaseOrders` | `PurchaseOrderID` → `Purchasing.PurchaseOrders.PurchaseOrderID` |
| `Warehouse.StockItemTransactions` | FK | `FK_Warehouse_StockItemTransactions_StockItemID_Warehouse_StockItems` | `StockItemID` → `Warehouse.StockItems.StockItemID` |
| `Warehouse.StockItemTransactions` | FK | `FK_Warehouse_StockItemTransactions_SupplierID_Purchasing_Suppliers` | `SupplierID` → `Purchasing.Suppliers.SupplierID` |
| `Warehouse.StockItemTransactions` | FK | `FK_Warehouse_StockItemTransactions_TransactionTypeID_Application_TransactionTypes` | `TransactionTypeID` → `Application.TransactionTypes.TransactionTypeID` |

Không có FK disabled/untrusted trong 51 FK của 9 bảng này; toàn database có 98 FK, cũng không có FK disabled/untrusted theo `sys.foreign_keys`. Quan hệ có FK **không** xác nhận uniqueness phía child hoặc quan hệ một-một, ngoại trừ các key constraints được liệt kê; ví dụ `Warehouse.StockItemHoldings.StockItemID` vừa PK vừa FK tới `Warehouse.StockItems.StockItemID`.

## Giới hạn cần kiểm tra tiếp

- `LastEditedWhen` là metadata cột ở nhiều bảng giao dịch, nhưng chưa chứng minh hành vi cập nhật, tính đơn điệu hoặc khả năng bắt delete.
- `ValidFrom/ValidTo` ở `Sales.Customers` và `Warehouse.StockItems` là period columns; phạm vi history theo thời điểm nghiệp vụ chưa được kiểm chứng.
- `IsCreditNote`, `LineProfit`, các transaction types và invoice/delivery dates cần khảo sát nghiệp vụ ở Phase 1.2/1.3 trước khi định nghĩa KPI.
- Không kết luận `StockItemHoldings` là daily balance, không suy diễn refunds từ credit note.

Xem [inventory](wwi-database-inventory.md), [temporal/index assessment](wwi-temporal-index-assessment.md) và [assessment](wwi-phase-1-1-assessment.md).
