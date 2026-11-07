# Kiểm kê database WWI — Phase 1.1

**Trạng thái: Verified từ metadata SQL Server; chưa COUNT trực tiếp.** Khảo sát lúc 2026-11-07 03:53 UTC qua Windows integrated authentication, chỉ chạy truy vấn `SELECT` trên `.\SQLEXPRESS` / `WideWorldImporters`. Không lưu thông tin xác thực hoặc dữ liệu dòng nghiệp vụ. Xem [truy vấn kiểm chứng](wwi-metadata-queries.md).

## Tổng quan

| Thuộc tính | Giá trị metadata |
| --- | --- |
| SQL Server ProductVersion / Edition | `17.0.1000.7` / `Express Edition (64-bit)` |
| Database / trạng thái / compatibility level | `WideWorldImporters` / `ONLINE` / `130` |
| Schema nhìn thấy trong `sys.schemas` | 23; 4 schema có user table |
| User tables | 48 = 31 bảng hiện hành + 17 history tables |
| System-versioned temporal tables | 17 bảng hiện hành, ghép với 17 history tables |
| Row count | `sys.partitions.rows` cho heap/clustered index (`index_id IN (0,1)`); **metadata estimate**, không phải `COUNT(*)` xác nhận |

## Danh sách schema

| Schema | Số user table |
| --- | ---: |
| `Application` | 15 |
| `DataLoadSimulation` | 0 |
| `db_accessadmin` | 0 |
| `db_backupoperator` | 0 |
| `db_datareader` | 0 |
| `db_datawriter` | 0 |
| `db_ddladmin` | 0 |
| `db_denydatareader` | 0 |
| `db_denydatawriter` | 0 |
| `db_owner` | 0 |
| `db_securityadmin` | 0 |
| `dbo` | 0 |
| `guest` | 0 |
| `INFORMATION_SCHEMA` | 0 |
| `Integration` | 0 |
| `PowerBI` | 0 |
| `Purchasing` | 7 |
| `Reports` | 0 |
| `Sales` | 12 |
| `Sequences` | 0 |
| `sys` | 0 |
| `Warehouse` | 14 |
| `Website` | 0 |

Các schema có bảng nghiệp vụ: `Application`, `Purchasing`, `Sales`, `Warehouse`. Các schema còn lại có 0 user table theo `sys.tables` tại thời điểm khảo sát; sự hiện diện của schema không đồng nghĩa có bảng.

## Danh sách bảng và phân loại

| Schema.Table | Nhóm sơ bộ | Temporal type | History table (nếu có) | Rows (metadata) |
| --- | --- | --- | --- | ---: |
| `Application.Cities` | Reference | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Application.Cities_Archive` | 37,940 |
| `Application.Cities_Archive` | History | `HISTORY_TABLE` | — | 28 |
| `Application.Countries` | Reference | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Application.Countries_Archive` | 190 |
| `Application.Countries_Archive` | History | `HISTORY_TABLE` | — | 37 |
| `Application.DeliveryMethods` | Reference | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Application.DeliveryMethods_Archive` | 10 |
| `Application.DeliveryMethods_Archive` | History | `HISTORY_TABLE` | — | 1 |
| `Application.PaymentMethods` | Reference | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Application.PaymentMethods_Archive` | 4 |
| `Application.PaymentMethods_Archive` | History | `HISTORY_TABLE` | — | 1 |
| `Application.People` | Reference | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Application.People_Archive` | 1,111 |
| `Application.People_Archive` | History | `HISTORY_TABLE` | — | 961 |
| `Application.StateProvinces` | Reference | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Application.StateProvinces_Archive` | 53 |
| `Application.StateProvinces_Archive` | History | `HISTORY_TABLE` | — | 104 |
| `Application.SystemParameters` | Cấu hình nghiệp vụ | `NON_TEMPORAL_TABLE` | — | 1 |
| `Application.TransactionTypes` | Reference | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Application.TransactionTypes_Archive` | 13 |
| `Application.TransactionTypes_Archive` | History | `HISTORY_TABLE` | — | 1 |
| `Purchasing.PurchaseOrderLines` | Purchasing / reference | `NON_TEMPORAL_TABLE` | — | 8,367 |
| `Purchasing.PurchaseOrders` | Purchasing / reference | `NON_TEMPORAL_TABLE` | — | 2,074 |
| `Purchasing.SupplierCategories` | Purchasing / reference | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Purchasing.SupplierCategories_Archive` | 9 |
| `Purchasing.SupplierCategories_Archive` | History | `HISTORY_TABLE` | — | 1 |
| `Purchasing.Suppliers` | Purchasing / reference | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Purchasing.Suppliers_Archive` | 13 |
| `Purchasing.Suppliers_Archive` | History | `HISTORY_TABLE` | — | 13 |
| `Purchasing.SupplierTransactions` | Purchasing / reference | `NON_TEMPORAL_TABLE` | — | 2,438 |
| `Sales.BuyingGroups` | Reference | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Sales.BuyingGroups_Archive` | 2 |
| `Sales.BuyingGroups_Archive` | History | `HISTORY_TABLE` | — | 0 |
| `Sales.CustomerCategories` | Reference | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Sales.CustomerCategories_Archive` | 8 |
| `Sales.CustomerCategories_Archive` | History | `HISTORY_TABLE` | — | 1 |
| `Sales.Customers` | Master MVP | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Sales.Customers_Archive` | 663 |
| `Sales.Customers_Archive` | History | `HISTORY_TABLE` | — | 51 |
| `Sales.CustomerTransactions` | Giao dịch MVP | `NON_TEMPORAL_TABLE` | — | 97,147 |
| `Sales.InvoiceLines` | Giao dịch MVP | `NON_TEMPORAL_TABLE` | — | 228,265 |
| `Sales.Invoices` | Giao dịch MVP | `NON_TEMPORAL_TABLE` | — | 70,510 |
| `Sales.OrderLines` | Giao dịch MVP | `NON_TEMPORAL_TABLE` | — | 231,412 |
| `Sales.Orders` | Giao dịch MVP | `NON_TEMPORAL_TABLE` | — | 73,595 |
| `Sales.SpecialDeals` | Cấu hình nghiệp vụ | `NON_TEMPORAL_TABLE` | — | 2 |
| `Warehouse.ColdRoomTemperatures` | Sensor / ngoài MVP | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Warehouse.ColdRoomTemperatures_Archive` | 4 |
| `Warehouse.ColdRoomTemperatures_Archive` | History | `HISTORY_TABLE` | — | 3,654,736 |
| `Warehouse.Colors` | Reference | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Warehouse.Colors_Archive` | 36 |
| `Warehouse.Colors_Archive` | History | `HISTORY_TABLE` | — | 1 |
| `Warehouse.PackageTypes` | Reference | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Warehouse.PackageTypes_Archive` | 14 |
| `Warehouse.PackageTypes_Archive` | History | `HISTORY_TABLE` | — | 0 |
| `Warehouse.StockGroups` | Reference | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Warehouse.StockGroups_Archive` | 10 |
| `Warehouse.StockGroups_Archive` | History | `HISTORY_TABLE` | — | 1 |
| `Warehouse.StockItemHoldings` | Tồn hiện tại MVP | `NON_TEMPORAL_TABLE` | — | 227 |
| `Warehouse.StockItems` | Master MVP | `SYSTEM_VERSIONED_TEMPORAL_TABLE` | `Warehouse.StockItems_Archive` | 227 |
| `Warehouse.StockItems_Archive` | History | `HISTORY_TABLE` | — | 444 |
| `Warehouse.StockItemStockGroups` | Reference | `NON_TEMPORAL_TABLE` | — | 442 |
| `Warehouse.StockItemTransactions` | Movement MVP | `NON_TEMPORAL_TABLE` | — | 236,667 |
| `Warehouse.VehicleTemperatures` | Sensor / ngoài MVP | `NON_TEMPORAL_TABLE` | — | 65,998 |

## Bảng hiện hành ngoài MVP — tóm tắt khóa và phụ thuộc

Đây là tóm tắt metadata của 22 bảng hiện hành ngoài MVP, gồm reference, Purchasing và sensor/configuration. Cột FK đích liệt kê bảng tham chiếu, không khẳng định cardinality thực tế. Chi tiết từng cột ngoài MVP sẽ chỉ mở rộng khi có task tương ứng.

| Bảng | PK column | FK tới bảng | Cột date/time |
| --- | --- | --- | --- |
| `Application.Cities` | `CityID` | `Application.People`, `Application.StateProvinces` | `ValidFrom`, `ValidTo` |
| `Application.Countries` | `CountryID` | `Application.People` | `ValidFrom`, `ValidTo` |
| `Application.DeliveryMethods` | `DeliveryMethodID` | `Application.People` | `ValidFrom`, `ValidTo` |
| `Application.PaymentMethods` | `PaymentMethodID` | `Application.People` | `ValidFrom`, `ValidTo` |
| `Application.People` | `PersonID` | `Application.People` | `ValidFrom`, `ValidTo` |
| `Application.StateProvinces` | `StateProvinceID` | `Application.Countries`, `Application.People` | `ValidFrom`, `ValidTo` |
| `Application.SystemParameters` | `SystemParameterID` | `Application.Cities`, `Application.People` | `LastEditedWhen` |
| `Application.TransactionTypes` | `TransactionTypeID` | `Application.People` | `ValidFrom`, `ValidTo` |
| `Purchasing.PurchaseOrderLines` | `PurchaseOrderLineID` | `Application.People`, `Purchasing.PurchaseOrders`, `Warehouse.PackageTypes`, `Warehouse.StockItems` | `LastReceiptDate`, `LastEditedWhen` |
| `Purchasing.PurchaseOrders` | `PurchaseOrderID` | `Application.DeliveryMethods`, `Application.People`, `Purchasing.Suppliers` | `OrderDate`, `ExpectedDeliveryDate`, `LastEditedWhen` |
| `Purchasing.SupplierCategories` | `SupplierCategoryID` | `Application.People` | `ValidFrom`, `ValidTo` |
| `Purchasing.Suppliers` | `SupplierID` | `Application.Cities`, `Application.DeliveryMethods`, `Application.People`, `Purchasing.SupplierCategories` | `ValidFrom`, `ValidTo` |
| `Purchasing.SupplierTransactions` | `SupplierTransactionID` | `Application.PaymentMethods`, `Application.People`, `Application.TransactionTypes`, `Purchasing.PurchaseOrders`, `Purchasing.Suppliers` | `TransactionDate`, `FinalizationDate`, `LastEditedWhen` |
| `Sales.BuyingGroups` | `BuyingGroupID` | `Application.People` | `ValidFrom`, `ValidTo` |
| `Sales.CustomerCategories` | `CustomerCategoryID` | `Application.People` | `ValidFrom`, `ValidTo` |
| `Sales.SpecialDeals` | `SpecialDealID` | `Application.People`, `Sales.BuyingGroups`, `Sales.CustomerCategories`, `Sales.Customers`, `Warehouse.StockGroups`, `Warehouse.StockItems` | `StartDate`, `EndDate`, `LastEditedWhen` |
| `Warehouse.ColdRoomTemperatures` | `ColdRoomTemperatureID` | — | `RecordedWhen`, `ValidFrom`, `ValidTo` |
| `Warehouse.Colors` | `ColorID` | `Application.People` | `ValidFrom`, `ValidTo` |
| `Warehouse.PackageTypes` | `PackageTypeID` | `Application.People` | `ValidFrom`, `ValidTo` |
| `Warehouse.StockGroups` | `StockGroupID` | `Application.People` | `ValidFrom`, `ValidTo` |
| `Warehouse.StockItemStockGroups` | `StockItemStockGroupID` | `Application.People`, `Warehouse.StockGroups`, `Warehouse.StockItems` | `LastEditedWhen` |
| `Warehouse.VehicleTemperatures` | `VehicleTemperatureID` | — | `RecordedWhen` |

## Phân loại và phụ thuộc cần lưu ý

- **Sales/Invoicing MVP:** `Sales.Customers`, `Orders`, `OrderLines`, `Invoices`, `InvoiceLines`, `CustomerTransactions`. `Orders → OrderLines`, `Orders → Invoices`, `Invoices → InvoiceLines` và `Invoices → CustomerTransactions` là các FK có thật; `Invoices.OrderID` và `CustomerTransactions.InvoiceID` nullable. Những quan hệ này chưa xác lập grain của fact warehouse.
- **Inventory MVP:** `Warehouse.StockItems` là master; `StockItemHoldings` là trạng thái hiện tại với PK/FK `StockItemID`; `StockItemTransactions` ghi movement và có FK tùy chọn đến `Sales.Invoices` / `Purchasing.PurchaseOrders`. Không suy ra daily balance từ holdings.
- **Reference:** `Application.People`, `Cities`, `DeliveryMethods`, `PaymentMethods`, `TransactionTypes`, các category/group và package/color tables hỗ trợ FK của MVP. `Purchasing.Suppliers` là phụ thuộc của `Warehouse.StockItems`; Purchasing vẫn ngoài MVP.
- **History:** bảng `*_Archive` là temporal history tương ứng; không mặc định có lịch sử đủ để ánh xạ SCD2 theo mọi ngày giao dịch.
- **Ngoài MVP:** `Purchasing.PurchaseOrders`, `PurchaseOrderLines`, `SupplierTransactions` chỉ được ghi nhận để hiểu phụ thuộc. Bảng sensor và cấu hình được kiểm kê, chưa thiết kế pipeline.

Xem [metadata dictionary](wwi-metadata-dictionary.md), [temporal/index assessment](wwi-temporal-index-assessment.md) và [báo cáo Phase 1.1](wwi-phase-1-1-assessment.md).
