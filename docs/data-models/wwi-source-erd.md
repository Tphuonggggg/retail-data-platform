# WWI Source ERD — Phase 1.3

**Trạng thái:** mô hình quan hệ nguồn dựa trên FK enabled/trusted và nullable metadata, đối chiếu snapshot ngày 2026-11-07. Chờ Project Owner review. `||` = đúng một parent cho child; `o|` = parent tùy chọn đối với child; `o{` = 0..N child theo schema; `o|` ở phía child = 0..1 child khi child FK cũng là PK. Số lượng thực tế ở [relationship contract](wwi-source-relationships.md). Diagram chỉ vẽ FK thực; quan hệ quan sát không có FK được ghi bên dưới.

## 1. Sales & Invoicing

```mermaid
erDiagram
    Sales_Customers ||--o{ Sales_Orders : "CustomerID"
    Sales_Orders ||--o{ Sales_OrderLines : "OrderID"
    Sales_Orders o|--o{ Sales_Invoices : "OrderID nullable"
    Sales_Invoices ||--o{ Sales_InvoiceLines : "InvoiceID"
    Warehouse_StockItems ||--o{ Sales_OrderLines : "StockItemID"
    Warehouse_StockItems ||--o{ Sales_InvoiceLines : "StockItemID"
    Sales_Customers {
        int CustomerID PK
    }
    Sales_Orders {
        int OrderID PK
        int CustomerID FK
    }
    Sales_OrderLines {
        int OrderLineID PK
        int OrderID FK
        int StockItemID FK
    }
    Sales_Invoices {
        int InvoiceID PK
        int OrderID FK
        int CustomerID FK
        int BillToCustomerID FK
    }
    Sales_InvoiceLines {
        int InvoiceLineID PK
        int InvoiceID FK
        int StockItemID FK
    }
    Warehouse_StockItems {
        int StockItemID PK
    }
```

## 2. Customer & Financial Transactions

Hai cạnh từ `Sales_Customers` tới `Sales_Invoices` thể hiện **hai role khác nhau**, cùng tham chiếu `Customers.CustomerID`. Cạnh tự tham chiếu là `Customers.BillToCustomerID`.

```mermaid
erDiagram
    Sales_Customers ||--o{ Sales_Customers : "BillToCustomerID"
    Sales_Customers ||--o{ Sales_Orders : "buyer CustomerID"
    Sales_Customers ||--o{ Sales_Invoices : "buyer CustomerID"
    Sales_Customers ||--o{ Sales_Invoices : "BillToCustomerID"
    Sales_Customers ||--o{ Sales_CustomerTransactions : "CustomerID"
    Sales_Invoices o|--o{ Sales_CustomerTransactions : "InvoiceID nullable"
    Application_TransactionTypes ||--o{ Sales_CustomerTransactions : "TransactionTypeID"
    Sales_Customers {
        int CustomerID PK
        int BillToCustomerID FK
    }
    Sales_Orders {
        int OrderID PK
        int CustomerID FK
    }
    Sales_Invoices {
        int InvoiceID PK
        int CustomerID FK
        int BillToCustomerID FK
    }
    Sales_CustomerTransactions {
        int CustomerTransactionID PK
        int CustomerID FK
        int InvoiceID FK
        int TransactionTypeID FK
    }
    Application_TransactionTypes {
        int TransactionTypeID PK
    }
```

## 3. Inventory & Purchasing Dependencies

`StockItemHoldings.StockItemID` đồng thời là PK và FK, nên phía holdings là 0..1 theo schema. Purchasing chỉ xuất hiện để giải thích phụ thuộc của receipt, chưa mở rộng MVP.

```mermaid
erDiagram
    Warehouse_StockItems ||--o| Warehouse_StockItemHoldings : "StockItemID PK FK"
    Warehouse_StockItems ||--o{ Warehouse_StockItemTransactions : "StockItemID"
    Application_TransactionTypes ||--o{ Warehouse_StockItemTransactions : "TransactionTypeID"
    Sales_Invoices o|--o{ Warehouse_StockItemTransactions : "InvoiceID nullable"
    Sales_Customers o|--o{ Warehouse_StockItemTransactions : "CustomerID nullable"
    Purchasing_PurchaseOrders o|--o{ Warehouse_StockItemTransactions : "PurchaseOrderID nullable"
    Purchasing_PurchaseOrders ||--o{ Purchasing_PurchaseOrderLines : "PurchaseOrderID"
    Warehouse_StockItems ||--o{ Purchasing_PurchaseOrderLines : "StockItemID"
    Warehouse_StockItems {
        int StockItemID PK
    }
    Warehouse_StockItemHoldings {
        int StockItemID PK,FK
    }
    Warehouse_StockItemTransactions {
        int StockItemTransactionID PK
        int StockItemID FK
        int TransactionTypeID FK
        int InvoiceID FK
        int CustomerID FK
        int PurchaseOrderID FK
    }
    Application_TransactionTypes {
        int TransactionTypeID PK
    }
    Sales_Invoices {
        int InvoiceID PK
    }
    Sales_Customers {
        int CustomerID PK
    }
    Purchasing_PurchaseOrders {
        int PurchaseOrderID PK
    }
    Purchasing_PurchaseOrderLines {
        int PurchaseOrderLineID PK
        int PurchaseOrderID FK
        int StockItemID FK
    }
```

## 4. MVP tổng thể rút gọn

```mermaid
erDiagram
    Sales_Customers ||--o{ Sales_Orders : "CustomerID"
    Sales_Customers ||--o{ Sales_Invoices : "CustomerID or BillToCustomerID roles"
    Sales_Orders ||--o{ Sales_OrderLines : "OrderID"
    Sales_Orders o|--o{ Sales_Invoices : "OrderID nullable"
    Sales_Invoices ||--o{ Sales_InvoiceLines : "InvoiceID"
    Sales_Invoices o|--o{ Sales_CustomerTransactions : "InvoiceID nullable"
    Warehouse_StockItems ||--o{ Sales_OrderLines : "StockItemID"
    Warehouse_StockItems ||--o{ Sales_InvoiceLines : "StockItemID"
    Warehouse_StockItems ||--o| Warehouse_StockItemHoldings : "StockItemID PK FK"
    Warehouse_StockItems ||--o{ Warehouse_StockItemTransactions : "StockItemID"
    Sales_Invoices o|--o{ Warehouse_StockItemTransactions : "InvoiceID nullable"
    Purchasing_PurchaseOrders o|--o{ Warehouse_StockItemTransactions : "PurchaseOrderID nullable"
```

Sơ đồ tổng thể lược bớt self-FK, `TransactionTypes`, Purchasing lines và cạnh `StockItemTransactions.CustomerID` cho dễ đọc; ba sơ đồ trên là tham chiếu chi tiết. Cạnh Customers→Invoices trong sơ đồ rút gọn đại diện **hai FK riêng**, không phải một join key thay thế được.

## Quan sát không thể hiện như FK

- `OrderLines ↔ InvoiceLines`: **không có FK**. Quantity khớp ở 228.265 cặp `(OrderID, StockItemID)` của snapshot, nhưng không bảo đảm 1:1 tương lai.
- `StockItemTransactions ↔ InvoiceLines`: cùng `InvoiceID` và `StockItemID` chỉ cho phép đối soát theo nhóm; không có FK tới `InvoiceLineID`.
- `StockItemTransactions ↔ PurchaseOrderLines`: cùng `PurchaseOrderID` và `StockItemID` chỉ cho phép đối soát theo nhóm; không có FK tới `PurchaseOrderLineID`.
- `Customer Payment Received ↔ Invoices`: `InvoiceID` NULL ở toàn bộ 26.637 payment transactions; không có payment allocation FK trong các bảng khảo sát.
- `Customers_Archive` và `StockItems_Archive` là version history, không phải parent master có PK business ID duy nhất; không đưa vào sơ đồ FK nguồn.
