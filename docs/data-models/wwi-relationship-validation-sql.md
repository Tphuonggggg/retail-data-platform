# WWI Relationship Validation SQL — Phase 1.3

**Trạng thái:** các nhóm `SELECT`/metadata dưới đây đã được dùng để kiểm tra `WideWorldImporters` local ngày 2026-11-07 bằng Windows integrated authentication. Không ghi credential, không DML/DDL, không tạo bảng tạm, không sửa source. Kết quả là snapshot của từng truy vấn, không phải transaction snapshot chung. Các profile số liệu rộng hơn có ở [Phase 1.2 SQL](wwi-profiling-queries.md).

## R01 — FK metadata, nullable và trust

```sql
SELECT OBJECT_SCHEMA_NAME(fk.parent_object_id)+'.'+OBJECT_NAME(fk.parent_object_id) AS child_table,
       fk.name AS fk_name, pc.name AS child_column,
       OBJECT_SCHEMA_NAME(fk.referenced_object_id)+'.'+OBJECT_NAME(fk.referenced_object_id) AS parent_table,
       rc.name AS parent_column, c.is_nullable, fk.is_disabled, fk.is_not_trusted
FROM sys.foreign_keys AS fk
JOIN sys.foreign_key_columns AS x ON x.constraint_object_id=fk.object_id
JOIN sys.columns AS pc ON pc.object_id=x.parent_object_id AND pc.column_id=x.parent_column_id
JOIN sys.columns AS rc ON rc.object_id=x.referenced_object_id AND rc.column_id=x.referenced_column_id
JOIN sys.columns AS c ON c.object_id=x.parent_object_id AND c.column_id=x.parent_column_id
WHERE fk.parent_object_id IN (
  OBJECT_ID('Sales.Customers'), OBJECT_ID('Sales.Orders'),
  OBJECT_ID('Sales.OrderLines'), OBJECT_ID('Sales.Invoices'),
  OBJECT_ID('Sales.InvoiceLines'), OBJECT_ID('Sales.CustomerTransactions'),
  OBJECT_ID('Warehouse.StockItemHoldings'), OBJECT_ID('Warehouse.StockItemTransactions'),
  OBJECT_ID('Purchasing.PurchaseOrders'), OBJECT_ID('Purchasing.PurchaseOrderLines'))
  AND pc.name IN ('CustomerID','BillToCustomerID','OrderID','InvoiceID',
                  'StockItemID','TransactionTypeID','PurchaseOrderID')
ORDER BY child_table, child_column;
```

Kết quả: 20 cạnh FK thuộc tập trên, đều `is_disabled=0`, `is_not_trusted=0`. Nullable gồm `Invoices.OrderID`, `CustomerTransactions.InvoiceID`, `StockItemTransactions.CustomerID/InvoiceID/PurchaseOrderID`.

## R02 — Cardinality theo parent, phân biệt schema và snapshot

Mẫu được chạy cho các cặp trong bảng dưới đây. Thay `<parent>`, `<child>`, `<parent_pk>`, `<child_fk>` bằng định danh SQL trong bảng. Với FK nullable, `WHERE <child_fk> IS NOT NULL` chỉ áp dụng trong CTE `g`. Kết quả là số parent có 0/1/>1 child và số child lớn nhất; không tạo UNIQUE constraint.

```sql
WITH g AS (
  SELECT <child_fk> AS id, COUNT_BIG(*) AS n
  FROM <child>
  WHERE <child_fk> IS NOT NULL
  GROUP BY <child_fk>
)
SELECT COUNT_BIG(*) AS parents,
       SUM(CASE WHEN g.n IS NULL THEN 1 ELSE 0 END) AS zero_child,
       SUM(CASE WHEN g.n=1 THEN 1 ELSE 0 END) AS one_child,
       SUM(CASE WHEN g.n>1 THEN 1 ELSE 0 END) AS many_child,
       MAX(g.n) AS max_child
FROM <parent> AS p LEFT JOIN g ON p.<parent_pk>=g.id;
```

| Parent (`parent_pk`) | Child (`child_fk`) | 0 / 1 / >1; max |
| --- | --- | --- |
| `Sales.Customers(CustomerID)` | `Sales.Orders(CustomerID)` | 0 / 0 / 663; 150 |
| `Sales.Orders(OrderID)` | `Sales.OrderLines(OrderID)` | 0 / 8.596 / 64.999; 5 |
| `Sales.Orders(OrderID)` | `Sales.Invoices(OrderID)` | 3.085 / 70.510 / 0; 1 |
| `Sales.Invoices(InvoiceID)` | `Sales.InvoiceLines(InvoiceID)` | 0 / 5.572 / 64.938; 5 |
| `Warehouse.StockItems(StockItemID)` | `Sales.OrderLines(StockItemID)` | 0 / 0 / 227; 1.123 |
| `Warehouse.StockItems(StockItemID)` | `Sales.InvoiceLines(StockItemID)` | 0 / 0 / 227; 1.123 |
| `Sales.Customers(CustomerID)` | `Sales.Customers(BillToCustomerID)` | 400 / 261 / 2; 201 |
| `Sales.Invoices(InvoiceID)` | `Sales.CustomerTransactions(InvoiceID)` | 0 / 70.510 / 0; 1 |
| `Warehouse.StockItems(StockItemID)` | `Warehouse.StockItemHoldings(StockItemID)` | 0 / 227 / 0; 1 |
| `Warehouse.StockItems(StockItemID)` | `Warehouse.StockItemTransactions(StockItemID)` | 0 / 0 / 227; 1.767 |
| `Sales.Invoices(InvoiceID)` | `Warehouse.StockItemTransactions(InvoiceID)` | 0 / 5.572 / 64.938; 5 |
| `Purchasing.PurchaseOrders(PurchaseOrderID)` | `Purchasing.PurchaseOrderLines(PurchaseOrderID)` | 0 / 150 / 1.924; 34 |
| `Purchasing.PurchaseOrders(PurchaseOrderID)` | `Warehouse.StockItemTransactions(PurchaseOrderID)` | 2 / 150 / 1.922; 34 |

## R03 — RI dữ liệu, NULL khác orphan

Chạy anti-join cho từng cặp contract theo mẫu; đối với FK nullable, NULL được báo riêng. [Phase 1.2 SQL Q09](wwi-profiling-queries.md) ghi các quan hệ ưu tiên đã kiểm trước đó.

```sql
SELECT COUNT_BIG(*) AS child_rows,
       SUM(CASE WHEN c.<child_fk> IS NULL THEN 1 ELSE 0 END) AS null_fk,
       SUM(CASE WHEN c.<child_fk> IS NOT NULL AND p.<parent_pk> IS NULL
                THEN 1 ELSE 0 END) AS orphan_nonnull
FROM <child> AS c LEFT JOIN <parent> AS p
  ON p.<parent_pk>=c.<child_fk>;
```

Các cặp bổ sung đã chạy và có **0 orphan**: `Customers.BillToCustomerID→Customers`, `Invoices.CustomerID→Customers`, `Invoices.BillToCustomerID→Customers`, `OrderLines.StockItemID→StockItems`, `CustomerTransactions.TransactionTypeID→TransactionTypes`, `StockItemTransactions.TransactionTypeID→TransactionTypes`, `StockItemTransactions.CustomerID→Customers`, `PurchaseOrderLines.PurchaseOrderID→PurchaseOrders`, `PurchaseOrderLines.StockItemID→StockItems`. Riêng `StockItemTransactions.CustomerID` có 8.402 NULL; các NULL FK khác ở [Phase 1.2 integrity report](wwi-inventory-integrity-profiling.md).

## R04 — Customer roles và financial transactions

```sql
SELECT COUNT_BIG(*) AS customers,
       SUM(CASE WHEN CustomerID=BillToCustomerID THEN 1 ELSE 0 END) AS self_bill_to,
       SUM(CASE WHEN CustomerID<>BillToCustomerID THEN 1 ELSE 0 END) AS other_bill_to,
       COUNT_BIG(DISTINCT BillToCustomerID) AS bill_to_ids
FROM Sales.Customers;

SELECT COUNT_BIG(*) AS invoices,
       SUM(CASE WHEN i.CustomerID=i.BillToCustomerID THEN 1 ELSE 0 END) AS same_roles,
       SUM(CASE WHEN i.CustomerID<>i.BillToCustomerID THEN 1 ELSE 0 END) AS different_roles,
       SUM(CASE WHEN i.CustomerID<>o.CustomerID THEN 1 ELSE 0 END) AS order_buyer_mismatch,
       SUM(CASE WHEN i.BillToCustomerID<>c.BillToCustomerID THEN 1 ELSE 0 END)
         AS current_customer_bill_to_mismatch
FROM Sales.Invoices AS i
JOIN Sales.Orders AS o ON o.OrderID=i.OrderID
JOIN Sales.Customers AS c ON c.CustomerID=i.CustomerID;

SELECT t.TransactionTypeID, t.TransactionTypeName, COUNT_BIG(*) AS rows_exact,
       SUM(CASE WHEN ct.InvoiceID IS NULL THEN 1 ELSE 0 END) AS invoice_null,
       SUM(CASE WHEN ct.InvoiceID IS NOT NULL AND ct.CustomerID=i.CustomerID
                THEN 1 ELSE 0 END) AS matches_invoice_buyer,
       SUM(CASE WHEN ct.InvoiceID IS NOT NULL AND ct.CustomerID=i.BillToCustomerID
                THEN 1 ELSE 0 END) AS matches_invoice_bill_to
FROM Sales.CustomerTransactions AS ct
JOIN Application.TransactionTypes AS t ON t.TransactionTypeID=ct.TransactionTypeID
LEFT JOIN Sales.Invoices AS i ON i.InvoiceID=ct.InvoiceID
GROUP BY t.TransactionTypeID,t.TransactionTypeName;
```

Kết quả: 263 self bill-to, 400 other, 263 bill-to IDs; 26.265 invoice same role, 44.245 different; order buyer mismatch 0, current customer bill-to mismatch 0. Type 1: 70.510 dòng, 0 NULL InvoiceID, 26.265 khớp buyer, 70.510 khớp bill-to. Type 3: 26.637 dòng, tất cả InvoiceID NULL.

## R05 — Inventory links và Purchase dependency

```sql
SELECT TransactionTypeID, COUNT_BIG(*) AS rows_exact,
       SUM(CASE WHEN InvoiceID IS NOT NULL THEN 1 ELSE 0 END) AS invoice_link,
       SUM(CASE WHEN PurchaseOrderID IS NOT NULL THEN 1 ELSE 0 END) AS po_link
FROM Warehouse.StockItemTransactions GROUP BY TransactionTypeID;

SELECT COUNT_BIG(*) AS po_lines, COUNT_BIG(DISTINCT PurchaseOrderID) AS po_ids,
       COUNT_BIG(DISTINCT StockItemID) AS stock_item_ids
FROM Purchasing.PurchaseOrderLines;
```

Type 10: 228.265 invoice links; type 11: 8.358 PO links; type 12: 44 không có hai link. `PurchaseOrderLines`: 8.367 dòng, 2.074 PO IDs, 227 stock items. Xem [Phase 1.2 SQL Q10](wwi-profiling-queries.md) cho đối soát quantity ở grain `(InvoiceID,StockItemID)` và `(PurchaseOrderID,StockItemID)`; không có FK tới từng line.

## R06 — OrderLine/InvoiceLine chỉ đối chiếu composite key

```sql
WITH ol AS (
  SELECT OrderID,StockItemID,COUNT_BIG(*) AS line_count,SUM(CAST(Quantity AS bigint)) AS qty
  FROM Sales.OrderLines GROUP BY OrderID,StockItemID
), il AS (
  SELECT i.OrderID,l.StockItemID,COUNT_BIG(*) AS line_count,
         SUM(CAST(l.Quantity AS bigint)) AS qty
  FROM Sales.InvoiceLines AS l JOIN Sales.Invoices AS i ON i.InvoiceID=l.InvoiceID
  GROUP BY i.OrderID,l.StockItemID
)
SELECT COUNT_BIG(*) AS composite_keys,
       SUM(CASE WHEN ol.OrderID IS NULL THEN 1 ELSE 0 END) AS invoice_only,
       SUM(CASE WHEN il.OrderID IS NULL THEN 1 ELSE 0 END) AS order_only,
       SUM(CASE WHEN ol.qty=il.qty THEN 1 ELSE 0 END) AS qty_match,
       SUM(CASE WHEN ol.qty<>il.qty THEN 1 ELSE 0 END) AS qty_mismatch,
       SUM(CASE WHEN ol.line_count>1 THEN 1 ELSE 0 END) AS repeated_order_key,
       SUM(CASE WHEN il.line_count>1 THEN 1 ELSE 0 END) AS repeated_invoice_key
FROM ol FULL OUTER JOIN il
  ON il.OrderID=ol.OrderID AND il.StockItemID=ol.StockItemID;
```

Snapshot: 231.412 composite keys, 0 invoice-only, 3.147 order-only, 228.265 quantity match, 0 mismatch hoặc repeated key. **Không** suy ra line-level FK hoặc ràng buộc 1:1.

```sql
SELECT COUNT_BIG(*) AS orders_without_invoice,
       SUM(CASE WHEN o.PickingCompletedWhen IS NULL THEN 1 ELSE 0 END) AS picking_null
FROM Sales.Orders AS o
WHERE NOT EXISTS (
  SELECT 1 FROM Sales.Invoices AS i WHERE i.OrderID=o.OrderID
);
```

Kết quả: 3.085 order chưa có invoice và cả 3.085 có `PickingCompletedWhen` NULL. Đây là quan sát, chưa có business status được duyệt.
