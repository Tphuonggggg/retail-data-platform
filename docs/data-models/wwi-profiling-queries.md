# SQL Profiling Queries — WWI Phase 1.2

**Trạng thái: Verified — các câu lệnh dưới đây là `SELECT` đã dùng để đối chiếu số liệu.** Chạy trên `WideWorldImporters` bằng Windows integrated authentication, ví dụ `sqlcmd -S '.\SQLEXPRESS' -d WideWorldImporters -E -C -b -Q "<SELECT>"`. `-C` chỉ tin cậy chứng chỉ TLS local cho client. Không dùng credential trong file, không DML/DDL, không thay đổi CDC/Change Tracking. Các phép đếm trực tiếp dùng `COUNT_BIG(*)`; kết quả là snapshot của lúc truy vấn, không phải ảnh chụp transaction đồng thời trên toàn database.

## Q01 — Exact count và PK uniqueness

Thay cặp bảng/PK từ [metadata dictionary](wwi-metadata-dictionary.md); đã chạy cho 9 bảng MVP và hai archive. History có nhiều version cho một business ID nên `COUNT_BIG(*) - COUNT_BIG(DISTINCT ID)` **không** là lỗi PK.

```sql
SELECT COUNT_BIG(*) AS rows_exact,
       COUNT_BIG(DISTINCT OrderID) AS distinct_pk,
       COUNT_BIG(*) - COUNT_BIG(DISTINCT OrderID) AS duplicate_pk_rows
FROM Sales.Orders;
-- Cùng mẫu cho:
-- Sales.OrderLines(OrderLineID), Sales.Invoices(InvoiceID),
-- Sales.InvoiceLines(InvoiceLineID),
-- Sales.CustomerTransactions(CustomerTransactionID),
-- Sales.Customers(CustomerID), Sales.Customers_Archive(CustomerID),
-- Warehouse.StockItems(StockItemID), Warehouse.StockItems_Archive(StockItemID),
-- Warehouse.StockItemHoldings(StockItemID),
-- Warehouse.StockItemTransactions(StockItemTransactionID).
```

## Q02 — NULL, ngày và cờ Sales

```sql
SELECT COUNT_BIG(*) AS rows_exact,
       SUM(CASE WHEN PickedByPersonID IS NULL THEN 1 ELSE 0 END) AS picked_by_null,
       SUM(CASE WHEN BackorderOrderID IS NULL THEN 1 ELSE 0 END) AS backorder_null,
       SUM(CASE WHEN CustomerPurchaseOrderNumber IS NULL THEN 1 ELSE 0 END) AS po_number_null,
       SUM(CASE WHEN PickingCompletedWhen IS NULL THEN 1 ELSE 0 END) AS picking_null,
       MIN(OrderDate) AS min_date, MAX(OrderDate) AS max_date,
       MIN(LastEditedWhen) AS min_edit, MAX(LastEditedWhen) AS max_edit
FROM Sales.Orders;

SELECT COUNT_BIG(*) AS rows_exact,
       SUM(CASE WHEN UnitPrice IS NULL THEN 1 ELSE 0 END) AS unit_price_null,
       SUM(CASE WHEN PickingCompletedWhen IS NULL THEN 1 ELSE 0 END) AS picking_null,
       MIN(PickingCompletedWhen) AS min_picking,
       MAX(PickingCompletedWhen) AS max_picking
FROM Sales.OrderLines;

SELECT COUNT_BIG(*) AS rows_exact,
       SUM(CASE WHEN OrderID IS NULL THEN 1 ELSE 0 END) AS order_null,
       SUM(CASE WHEN ConfirmedDeliveryTime IS NULL THEN 1 ELSE 0 END) AS delivery_null,
       SUM(CASE WHEN ConfirmedReceivedBy IS NULL THEN 1 ELSE 0 END) AS received_by_null,
       SUM(CASE WHEN CustomerID <> BillToCustomerID THEN 1 ELSE 0 END) AS customer_differs_bill_to,
       SUM(CASE WHEN IsCreditNote = 1 THEN 1 ELSE 0 END) AS credit_note_rows,
       MIN(InvoiceDate) AS min_invoice_date, MAX(InvoiceDate) AS max_invoice_date,
       MIN(ConfirmedDeliveryTime) AS min_delivery,
       MAX(ConfirmedDeliveryTime) AS max_delivery
FROM Sales.Invoices;

SELECT COUNT_BIG(*) AS rows_exact,
       SUM(CASE WHEN UnitPrice IS NULL THEN 1 ELSE 0 END) AS unit_price_null
FROM Sales.InvoiceLines;

SELECT COUNT_BIG(*) AS rows_exact,
       SUM(CASE WHEN InvoiceID IS NULL THEN 1 ELSE 0 END) AS invoice_null,
       SUM(CASE WHEN PaymentMethodID IS NULL THEN 1 ELSE 0 END) AS payment_method_null,
       SUM(CASE WHEN FinalizationDate IS NULL THEN 1 ELSE 0 END) AS finalized_date_null,
       SUM(CASE WHEN IsFinalized IS NULL THEN 1 ELSE 0 END) AS finalized_flag_null,
       MIN(TransactionDate) AS min_transaction_date,
       MAX(TransactionDate) AS max_transaction_date,
       MIN(FinalizationDate) AS min_finalization_date,
       MAX(FinalizationDate) AS max_finalization_date
FROM Sales.CustomerTransactions;
```

## Q03 — Year/month theo business date

```sql
SELECT 'Orders' AS source_table, YEAR(OrderDate) AS yr, MONTH(OrderDate) AS mo,
       COUNT_BIG(*) AS rows_exact
FROM Sales.Orders GROUP BY YEAR(OrderDate), MONTH(OrderDate)
UNION ALL
SELECT 'OrderLines_by_OrderDate', YEAR(o.OrderDate), MONTH(o.OrderDate), COUNT_BIG(*)
FROM Sales.OrderLines AS l JOIN Sales.Orders AS o ON o.OrderID = l.OrderID
GROUP BY YEAR(o.OrderDate), MONTH(o.OrderDate)
UNION ALL
SELECT 'Invoices', YEAR(InvoiceDate), MONTH(InvoiceDate), COUNT_BIG(*)
FROM Sales.Invoices GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
UNION ALL
SELECT 'InvoiceLines_by_InvoiceDate', YEAR(i.InvoiceDate), MONTH(i.InvoiceDate), COUNT_BIG(*)
FROM Sales.InvoiceLines AS l JOIN Sales.Invoices AS i ON i.InvoiceID = l.InvoiceID
GROUP BY YEAR(i.InvoiceDate), MONTH(i.InvoiceDate)
UNION ALL
SELECT 'CustomerTransactions', YEAR(TransactionDate), MONTH(TransactionDate), COUNT_BIG(*)
FROM Sales.CustomerTransactions GROUP BY YEAR(TransactionDate), MONTH(TransactionDate)
ORDER BY source_table, yr, mo;
```

## Q04 — Order/invoice/line cardinality và date consistency

```sql
WITH invoice_per_order AS (
  SELECT OrderID, COUNT_BIG(*) AS n
  FROM Sales.Invoices WHERE OrderID IS NOT NULL GROUP BY OrderID
)
SELECT COUNT_BIG(*) AS orders,
       SUM(CASE WHEN x.n IS NULL THEN 1 ELSE 0 END) AS no_invoice,
       SUM(CASE WHEN x.n = 1 THEN 1 ELSE 0 END) AS one_invoice,
       SUM(CASE WHEN x.n > 1 THEN 1 ELSE 0 END) AS multiple_invoice,
       MAX(x.n) AS max_invoices_per_order
FROM Sales.Orders AS o LEFT JOIN invoice_per_order AS x ON x.OrderID = o.OrderID;

WITH lines_per_invoice AS (
  SELECT InvoiceID, COUNT_BIG(*) AS n FROM Sales.InvoiceLines GROUP BY InvoiceID
)
SELECT COUNT_BIG(*) AS invoices,
       SUM(CASE WHEN l.n IS NULL THEN 1 ELSE 0 END) AS no_line,
       SUM(CASE WHEN l.n = 1 THEN 1 ELSE 0 END) AS one_line,
       SUM(CASE WHEN l.n > 1 THEN 1 ELSE 0 END) AS multi_line,
       MAX(l.n) AS max_lines
FROM Sales.Invoices AS i LEFT JOIN lines_per_invoice AS l ON l.InvoiceID = i.InvoiceID;

WITH lines_per_order AS (
  SELECT OrderID, COUNT_BIG(*) AS n FROM Sales.OrderLines GROUP BY OrderID
)
SELECT SUM(CASE WHEN i.OrderID IS NULL THEN 1 ELSE 0 END) AS no_order_id,
       SUM(CASE WHEN ol.n IS NULL AND i.OrderID IS NOT NULL THEN 1 ELSE 0 END)
         AS linked_order_no_lines,
       SUM(CASE WHEN ol.n > 1 THEN 1 ELSE 0 END) AS linked_order_multi_lines,
       MAX(ol.n) AS max_order_lines_for_invoice
FROM Sales.Invoices AS i LEFT JOIN lines_per_order AS ol ON ol.OrderID = i.OrderID;

SELECT SUM(CASE WHEN i.CustomerID <> o.CustomerID THEN 1 ELSE 0 END)
         AS invoice_order_customer_mismatch,
       SUM(CASE WHEN o.OrderDate > i.InvoiceDate THEN 1 ELSE 0 END)
         AS invoice_before_order,
       SUM(CASE WHEN CAST(i.InvoiceDate AS datetime2(7)) > i.ConfirmedDeliveryTime
                THEN 1 ELSE 0 END) AS delivery_before_invoice
FROM Sales.Invoices AS i JOIN Sales.Orders AS o ON o.OrderID = i.OrderID;
```

## Q05 — Transaction types, payment và cột nguồn tài chính

```sql
SELECT ct.TransactionTypeID, tt.TransactionTypeName, COUNT_BIG(*) AS rows_exact,
       SUM(CASE WHEN ct.InvoiceID IS NULL THEN 1 ELSE 0 END) AS invoice_null,
       SUM(CASE WHEN ct.PaymentMethodID IS NULL THEN 1 ELSE 0 END) AS method_null,
       SUM(ct.TransactionAmount) AS source_amount
FROM Sales.CustomerTransactions AS ct
JOIN Application.TransactionTypes AS tt ON tt.TransactionTypeID = ct.TransactionTypeID
GROUP BY ct.TransactionTypeID, tt.TransactionTypeName;

SELECT IsFinalized, COUNT_BIG(*) AS rows_exact
FROM Sales.CustomerTransactions GROUP BY IsFinalized;

SELECT TransactionTypeID,
       SUM(CASE WHEN TransactionAmount < 0 THEN 1 ELSE 0 END) AS negative_amount,
       SUM(CASE WHEN TransactionAmount = 0 THEN 1 ELSE 0 END) AS zero_amount,
       SUM(CASE WHEN TransactionAmount > 0 THEN 1 ELSE 0 END) AS positive_amount
FROM Sales.CustomerTransactions GROUP BY TransactionTypeID;

SELECT SUM(CAST(Quantity AS decimal(38,3))) AS quantity_sum,
       SUM(UnitPrice) AS sum_unit_prices,
       MIN(Quantity) AS min_qty, MAX(Quantity) AS max_qty,
       MIN(UnitPrice) AS min_unit_price, MAX(UnitPrice) AS max_unit_price,
       SUM(CASE WHEN Quantity <= 0 THEN 1 ELSE 0 END) AS nonpositive_qty,
       SUM(CASE WHEN UnitPrice < 0 THEN 1 ELSE 0 END) AS negative_price
FROM Sales.OrderLines;

SELECT SUM(CAST(Quantity AS decimal(38,3))) AS quantity_sum,
       SUM(UnitPrice) AS sum_unit_prices,
       SUM(TaxAmount) AS tax_sum, SUM(ExtendedPrice) AS extended_sum,
       SUM(LineProfit) AS line_profit_sum,
       MIN(Quantity) AS min_qty, MAX(Quantity) AS max_qty,
       MIN(UnitPrice) AS min_price, MAX(UnitPrice) AS max_price,
       MIN(TaxAmount) AS min_tax, MAX(TaxAmount) AS max_tax,
       MIN(ExtendedPrice) AS min_extended, MAX(ExtendedPrice) AS max_extended,
       MIN(LineProfit) AS min_profit, MAX(LineProfit) AS max_profit,
       SUM(CASE WHEN Quantity <= 0 THEN 1 ELSE 0 END) AS nonpositive_qty,
       SUM(CASE WHEN UnitPrice < 0 THEN 1 ELSE 0 END) AS negative_price,
       SUM(CASE WHEN TaxAmount < 0 THEN 1 ELSE 0 END) AS negative_tax,
       SUM(CASE WHEN ExtendedPrice < 0 THEN 1 ELSE 0 END) AS negative_extended,
       SUM(CASE WHEN LineProfit < 0 THEN 1 ELSE 0 END) AS negative_profit
FROM Sales.InvoiceLines;

WITH il AS (
  SELECT InvoiceID, SUM(ExtendedPrice) AS amount
  FROM Sales.InvoiceLines GROUP BY InvoiceID
), ct AS (
  SELECT InvoiceID, COUNT_BIG(*) AS n, SUM(TransactionAmount) AS amount
  FROM Sales.CustomerTransactions
  WHERE TransactionTypeID = 1 AND InvoiceID IS NOT NULL GROUP BY InvoiceID
)
SELECT COUNT_BIG(*) AS invoices,
       SUM(CASE WHEN ct.InvoiceID IS NULL THEN 1 ELSE 0 END) AS no_invoice_transaction,
       SUM(CASE WHEN ct.n <> 1 THEN 1 ELSE 0 END) AS not_one_transaction,
       SUM(CASE WHEN il.amount = ct.amount THEN 1 ELSE 0 END) AS amount_match,
       SUM(CASE WHEN il.amount <> ct.amount THEN 1 ELSE 0 END) AS amount_mismatch
FROM Sales.Invoices AS i
LEFT JOIN il ON il.InvoiceID = i.InvoiceID
LEFT JOIN ct ON ct.InvoiceID = i.InvoiceID;
```

Các tổng `UnitPrice`, `ExtendedPrice`, `TaxAmount`, `LineProfit`, `TransactionAmount` là **số liệu nguồn**; truy vấn không định nghĩa KPI.

## Q06 — Customer temporal versions, validity và as-of

```sql
SELECT COUNT_BIG(*) AS current_rows, COUNT_BIG(DISTINCT CustomerID) AS current_ids,
       MIN(ValidFrom) AS min_from, MAX(ValidFrom) AS max_from,
       MIN(ValidTo) AS min_to, MAX(ValidTo) AS max_to,
       MIN(AccountOpenedDate) AS min_account_opened,
       MAX(AccountOpenedDate) AS max_account_opened
FROM Sales.Customers;
SELECT COUNT_BIG(*) AS archive_rows, COUNT_BIG(DISTINCT CustomerID) AS archive_ids,
       MIN(ValidFrom) AS min_from, MAX(ValidFrom) AS max_from,
       MIN(ValidTo) AS min_to, MAX(ValidTo) AS max_to,
       SUM(CASE WHEN ValidFrom = ValidTo THEN 1 ELSE 0 END) AS zero_duration
FROM Sales.Customers_Archive;

WITH v AS (
  SELECT CustomerID, ValidFrom, ValidTo FROM Sales.Customers
  UNION ALL SELECT CustomerID, ValidFrom, ValidTo FROM Sales.Customers_Archive
), n AS (SELECT CustomerID, COUNT_BIG(*) AS versions FROM v GROUP BY CustomerID)
SELECT versions, COUNT_BIG(*) AS customer_ids FROM n GROUP BY versions ORDER BY versions;

WITH v AS (
  SELECT CustomerID, ValidFrom, ValidTo FROM Sales.Customers
  UNION ALL SELECT CustomerID, ValidFrom, ValidTo FROM Sales.Customers_Archive
), r AS (
  SELECT CustomerID, ValidFrom, ValidTo,
         LEAD(ValidFrom) OVER
           (PARTITION BY CustomerID ORDER BY ValidFrom, ValidTo) AS next_from
  FROM v
)
SELECT COUNT_BIG(*) AS raw_versions,
       SUM(CASE WHEN ValidFrom = ValidTo THEN 1 ELSE 0 END) AS zero_duration,
       SUM(CASE WHEN ValidFrom > ValidTo THEN 1 ELSE 0 END) AS negative_duration,
       SUM(CASE WHEN next_from < ValidTo THEN 1 ELSE 0 END) AS overlaps,
       SUM(CASE WHEN next_from > ValidTo THEN 1 ELSE 0 END) AS gaps,
       SUM(CASE WHEN next_from = ValidTo THEN 1 ELSE 0 END) AS adjacent
FROM r;

SELECT COUNT_BIG(*) AS for_system_time_all_rows
FROM Sales.Customers FOR SYSTEM_TIME ALL;

WITH v AS (
  SELECT CustomerID, ValidFrom, ValidTo FROM Sales.Customers
  UNION ALL SELECT CustomerID, ValidFrom, ValidTo FROM Sales.Customers_Archive
)
SELECT COUNT_BIG(*) AS raw_versions,
       COUNT_BIG(DISTINCT ValidFrom) AS distinct_valid_from,
       COUNT_BIG(DISTINCT ValidTo) AS distinct_valid_to
FROM v;
```

So sánh thuộc tính: chạy mẫu sau cho từng cột ngoài `CustomerID`, `ValidFrom`, `ValidTo` theo [metadata dictionary](wwi-metadata-dictionary.md). Thay **cả hai** vị trí `<column>` bằng cùng tên cột từ dictionary. Với `DeliveryLocation`, thay bằng biểu thức `DeliveryLocation.STAsBinary()`. Đã kiểm tra đủ 28 cột; chỉ `CreditLimit` (51 transition/46 ID) và `LastEditedBy` (50/46) khác 0.

```sql
WITH v AS (
  SELECT CustomerID, ValidFrom, ValidTo, <column> AS val FROM Sales.Customers
  UNION ALL
  SELECT CustomerID, ValidFrom, ValidTo, <column> AS val FROM Sales.Customers_Archive
), r AS (
  SELECT CustomerID, val,
         LAG(val) OVER (PARTITION BY CustomerID ORDER BY ValidFrom, ValidTo) AS prev,
         ROW_NUMBER() OVER (PARTITION BY CustomerID ORDER BY ValidFrom, ValidTo) AS rn
  FROM v
)
SELECT COUNT_BIG(*) AS changed_transitions,
       COUNT_BIG(DISTINCT CustomerID) AS changed_ids
FROM r
WHERE rn > 1
  AND (val <> prev OR (val IS NULL AND prev IS NOT NULL)
                   OR (val IS NOT NULL AND prev IS NULL));
```

As-of tại **00:00 của business date**, không phải business effective time:

```sql
WITH v AS (
  SELECT CustomerID, ValidFrom, ValidTo FROM Sales.Customers
  UNION ALL SELECT CustomerID, ValidFrom, ValidTo FROM Sales.Customers_Archive
), coverage AS (
  SELECT o.OrderID,
         MAX(CASE WHEN v.ValidFrom <= CAST(o.OrderDate AS datetime2(7))
                   AND v.ValidTo > CAST(o.OrderDate AS datetime2(7))
                  THEN 1 ELSE 0 END) AS covered
  FROM Sales.Orders AS o LEFT JOIN v ON v.CustomerID = o.CustomerID
  GROUP BY o.OrderID
)
SELECT COUNT_BIG(*) AS orders, SUM(covered) AS covered_orders FROM coverage;
-- Cùng mẫu cho Invoices(InvoiceID, InvoiceDate) và
-- CustomerTransactions(CustomerTransactionID, TransactionDate).
```

## Q07 — Inventory NULL, balance, signed movement và time

```sql
SELECT COUNT_BIG(*) AS stock_items,
       SUM(CASE WHEN ColorID IS NULL THEN 1 ELSE 0 END) AS color_null,
       SUM(CASE WHEN Brand IS NULL THEN 1 ELSE 0 END) AS brand_null,
       SUM(CASE WHEN Size IS NULL THEN 1 ELSE 0 END) AS size_null,
       SUM(CASE WHEN Barcode IS NULL THEN 1 ELSE 0 END) AS barcode_null,
       SUM(CASE WHEN RecommendedRetailPrice IS NULL THEN 1 ELSE 0 END) AS retail_null,
       MIN(UnitPrice) AS min_unit_price, MAX(UnitPrice) AS max_unit_price,
       SUM(CASE WHEN UnitPrice <= 0 THEN 1 ELSE 0 END) AS nonpositive_unit_price,
       MIN(ValidFrom) AS min_valid_from, MAX(ValidFrom) AS max_valid_from
FROM Warehouse.StockItems;

SELECT COUNT_BIG(*) AS holdings,
       SUM(CAST(QuantityOnHand AS bigint)) AS quantity_on_hand,
       SUM(CAST(LastStocktakeQuantity AS bigint)) AS last_stocktake_qty,
       SUM(CASE WHEN QuantityOnHand < 0 THEN 1 ELSE 0 END) AS negative_on_hand,
       SUM(CASE WHEN QuantityOnHand = 0 THEN 1 ELSE 0 END) AS zero_on_hand,
       MIN(QuantityOnHand) AS min_on_hand, MAX(QuantityOnHand) AS max_on_hand,
       MIN(LastCostPrice) AS min_last_cost, MAX(LastCostPrice) AS max_last_cost,
       SUM(CASE WHEN LastCostPrice < 0 THEN 1 ELSE 0 END) AS negative_last_cost,
       MIN(LastEditedWhen) AS min_edit, MAX(LastEditedWhen) AS max_edit
FROM Warehouse.StockItemHoldings;

SELECT COUNT_BIG(*) AS movements,
       SUM(CASE WHEN CustomerID IS NULL THEN 1 ELSE 0 END) AS customer_null,
       SUM(CASE WHEN InvoiceID IS NULL THEN 1 ELSE 0 END) AS invoice_null,
       SUM(CASE WHEN SupplierID IS NULL THEN 1 ELSE 0 END) AS supplier_null,
       SUM(CASE WHEN PurchaseOrderID IS NULL THEN 1 ELSE 0 END) AS po_null,
       SUM(CASE WHEN Quantity < 0 THEN 1 ELSE 0 END) AS negative_qty,
       SUM(CASE WHEN Quantity = 0 THEN 1 ELSE 0 END) AS zero_qty,
       SUM(CASE WHEN Quantity > 0 THEN 1 ELSE 0 END) AS positive_qty,
       SUM(Quantity) AS signed_qty_sum,
       MIN(Quantity) AS min_qty, MAX(Quantity) AS max_qty,
       MIN(TransactionOccurredWhen) AS min_when,
       MAX(TransactionOccurredWhen) AS max_when,
       SUM(CASE WHEN CustomerID IS NOT NULL AND InvoiceID IS NULL THEN 1 ELSE 0 END)
         AS customer_without_invoice,
       SUM(CASE WHEN SupplierID IS NOT NULL AND PurchaseOrderID IS NULL THEN 1 ELSE 0 END)
         AS supplier_without_po
FROM Warehouse.StockItemTransactions;

SELECT m.TransactionTypeID, t.TransactionTypeName, COUNT_BIG(*) AS rows_exact,
       SUM(m.Quantity) AS signed_qty,
       MIN(m.Quantity) AS min_qty, MAX(m.Quantity) AS max_qty,
       SUM(CASE WHEN m.InvoiceID IS NOT NULL THEN 1 ELSE 0 END) AS invoice_links,
       SUM(CASE WHEN m.PurchaseOrderID IS NOT NULL THEN 1 ELSE 0 END) AS po_links
FROM Warehouse.StockItemTransactions AS m
JOIN Application.TransactionTypes AS t ON t.TransactionTypeID = m.TransactionTypeID
GROUP BY m.TransactionTypeID, t.TransactionTypeName;

SELECT CASE WHEN InvoiceID IS NOT NULL AND PurchaseOrderID IS NOT NULL THEN 'both'
            WHEN InvoiceID IS NOT NULL THEN 'invoice_only'
            WHEN PurchaseOrderID IS NOT NULL THEN 'po_only'
            ELSE 'neither' END AS link_pattern,
       COUNT_BIG(*) AS rows_exact
FROM Warehouse.StockItemTransactions
GROUP BY CASE WHEN InvoiceID IS NOT NULL AND PurchaseOrderID IS NOT NULL THEN 'both'
              WHEN InvoiceID IS NOT NULL THEN 'invoice_only'
              WHEN PurchaseOrderID IS NOT NULL THEN 'po_only'
              ELSE 'neither' END;

SELECT YEAR(TransactionOccurredWhen) AS yr, MONTH(TransactionOccurredWhen) AS mo,
       COUNT_BIG(*) AS rows_exact
FROM Warehouse.StockItemTransactions
GROUP BY YEAR(TransactionOccurredWhen), MONTH(TransactionOccurredWhen)
ORDER BY yr, mo;
```

## Q08 — StockItems temporal history

```sql
SELECT COUNT_BIG(*) AS history_rows, COUNT_BIG(DISTINCT StockItemID) AS history_ids,
       MIN(ValidFrom) AS min_from, MAX(ValidFrom) AS max_from,
       MIN(ValidTo) AS min_to, MAX(ValidTo) AS max_to
FROM Warehouse.StockItems_Archive;

WITH v AS (
  SELECT StockItemID, ValidFrom, ValidTo FROM Warehouse.StockItems
  UNION ALL SELECT StockItemID, ValidFrom, ValidTo FROM Warehouse.StockItems_Archive
), n AS (SELECT StockItemID, COUNT_BIG(*) AS versions FROM v GROUP BY StockItemID)
SELECT versions, COUNT_BIG(*) AS stock_item_ids FROM n GROUP BY versions ORDER BY versions;

WITH v AS (
  SELECT StockItemID, ValidFrom, ValidTo FROM Warehouse.StockItems
  UNION ALL SELECT StockItemID, ValidFrom, ValidTo FROM Warehouse.StockItems_Archive
), r AS (
  SELECT ValidFrom, ValidTo,
         LEAD(ValidFrom) OVER
           (PARTITION BY StockItemID ORDER BY ValidFrom, ValidTo) AS next_from
  FROM v
)
SELECT COUNT_BIG(*) AS raw_versions,
       SUM(CASE WHEN ValidFrom >= ValidTo THEN 1 ELSE 0 END) AS zero_or_negative,
       SUM(CASE WHEN next_from < ValidTo THEN 1 ELSE 0 END) AS overlaps,
       SUM(CASE WHEN next_from > ValidTo THEN 1 ELSE 0 END) AS gaps,
       SUM(CASE WHEN next_from = ValidTo THEN 1 ELSE 0 END) AS adjacent
FROM r;

WITH v AS (
  SELECT StockItemID, ValidFrom, ValidTo FROM Warehouse.StockItems
  UNION ALL SELECT StockItemID, ValidFrom, ValidTo FROM Warehouse.StockItems_Archive
)
SELECT COUNT_BIG(*) AS raw_versions,
       COUNT_BIG(DISTINCT ValidFrom) AS distinct_valid_from,
       COUNT_BIG(DISTINCT ValidTo) AS distinct_valid_to
FROM v;
```

Lặp mẫu so sánh thuộc tính ở Q06 với `StockItemID`, `Warehouse.StockItems`, `Warehouse.StockItems_Archive` cho 22 cột ngoài PK/period. Kết quả khác 0: `CustomFields` và cột computed `Tags`, mỗi cột 444 transition/227 ID; 20 cột còn lại bằng 0.

Độ phủ system-time tại thời điểm movement (không chứng minh business effective time):

```sql
WITH v AS (
  SELECT StockItemID, ValidFrom, ValidTo FROM Warehouse.StockItems
  UNION ALL
  SELECT StockItemID, ValidFrom, ValidTo FROM Warehouse.StockItems_Archive
), coverage AS (
  SELECT m.StockItemTransactionID,
         MAX(CASE WHEN v.ValidFrom <= m.TransactionOccurredWhen
                   AND v.ValidTo > m.TransactionOccurredWhen THEN 1 ELSE 0 END) AS covered
  FROM Warehouse.StockItemTransactions AS m
  LEFT JOIN v ON v.StockItemID = m.StockItemID
  GROUP BY m.StockItemTransactionID
)
SELECT COUNT_BIG(*) AS movements, SUM(covered) AS covered_movements
FROM coverage;
```

## Q09 — Referential integrity trực tiếp

Chạy mẫu sau cho từng mapping; NULL hợp lệ được đếm riêng với orphan. Các mapping đã kiểm tra: `Orders.CustomerID → Customers`, `OrderLines.OrderID → Orders`, `Invoices.OrderID → Orders`, `InvoiceLines.InvoiceID → Invoices`, `InvoiceLines.StockItemID → StockItems`, `CustomerTransactions.CustomerID → Customers`, `CustomerTransactions.InvoiceID → Invoices`, `StockItemTransactions.StockItemID → StockItems`, `StockItemTransactions.InvoiceID → Invoices`, `StockItemTransactions.PurchaseOrderID → PurchaseOrders`, `StockItemHoldings.StockItemID → StockItems`.

```sql
SELECT COUNT_BIG(*) AS child_rows,
       SUM(CASE WHEN c.OrderID IS NULL THEN 1 ELSE 0 END) AS null_fk,
       SUM(CASE WHEN c.OrderID IS NOT NULL AND p.OrderID IS NULL
                THEN 1 ELSE 0 END) AS orphan_nonnull
FROM Sales.Invoices AS c
LEFT JOIN Sales.Orders AS p ON p.OrderID = c.OrderID;
-- Thay bảng/khóa theo mapping ở trên; giữ điều kiện FK IS NOT NULL
-- trong phép đếm orphan.
```

## Q10 — Đối soát invoice, receipt và current holdings

```sql
WITH i AS (
  SELECT InvoiceID, StockItemID, COUNT_BIG(*) AS line_rows,
         SUM(CAST(Quantity AS decimal(38,3))) AS qty
  FROM Sales.InvoiceLines GROUP BY InvoiceID, StockItemID
), m AS (
  SELECT InvoiceID, StockItemID, COUNT_BIG(*) AS movement_rows,
         SUM(Quantity) AS qty
  FROM Warehouse.StockItemTransactions
  WHERE TransactionTypeID = 10 GROUP BY InvoiceID, StockItemID
)
SELECT COUNT_BIG(*) AS pairs,
       SUM(CASE WHEN i.InvoiceID IS NULL THEN 1 ELSE 0 END) AS movement_only,
       SUM(CASE WHEN m.InvoiceID IS NULL THEN 1 ELSE 0 END) AS invoice_only,
       SUM(CASE WHEN i.qty = -m.qty THEN 1 ELSE 0 END) AS quantity_match,
       SUM(CASE WHEN i.qty <> -m.qty THEN 1 ELSE 0 END) AS quantity_mismatch,
       SUM(CASE WHEN i.line_rows <> m.movement_rows THEN 1 ELSE 0 END)
         AS row_count_mismatch
FROM i FULL OUTER JOIN m
  ON i.InvoiceID = m.InvoiceID AND i.StockItemID = m.StockItemID;

WITH p AS (
  SELECT l.PurchaseOrderID, l.StockItemID,
         SUM(CAST(l.ReceivedOuters AS decimal(38,3)) * s.QuantityPerOuter)
           AS received_units
  FROM Purchasing.PurchaseOrderLines AS l
  JOIN Warehouse.StockItems AS s ON s.StockItemID = l.StockItemID
  GROUP BY l.PurchaseOrderID, l.StockItemID
), m AS (
  SELECT PurchaseOrderID, StockItemID, SUM(Quantity) AS qty
  FROM Warehouse.StockItemTransactions
  WHERE TransactionTypeID = 11 GROUP BY PurchaseOrderID, StockItemID
)
SELECT COUNT_BIG(*) AS pairs,
       SUM(CASE WHEN p.PurchaseOrderID IS NULL THEN 1 ELSE 0 END) AS movement_only,
       SUM(CASE WHEN m.PurchaseOrderID IS NULL THEN 1 ELSE 0 END) AS po_line_only,
       SUM(CASE WHEN p.received_units = m.qty THEN 1 ELSE 0 END)
         AS quantity_match,
       SUM(CASE WHEN p.received_units <> m.qty THEN 1 ELSE 0 END)
         AS quantity_mismatch
FROM p FULL OUTER JOIN m
  ON p.PurchaseOrderID = m.PurchaseOrderID AND p.StockItemID = m.StockItemID;

WITH m AS (
  SELECT StockItemID, SUM(Quantity) AS qty
  FROM Warehouse.StockItemTransactions GROUP BY StockItemID
)
SELECT COUNT_BIG(*) AS stock_items,
       SUM(CASE WHEN CAST(h.QuantityOnHand AS decimal(38,3)) = m.qty
                THEN 1 ELSE 0 END) AS equal_raw_cumulative,
       SUM(CASE WHEN CAST(h.QuantityOnHand AS decimal(38,3)) <> m.qty
                THEN 1 ELSE 0 END) AS mismatch_raw_cumulative
FROM Warehouse.StockItemHoldings AS h JOIN m ON m.StockItemID = h.StockItemID;
```

## Q11 — Timestamp NULL, duplicates và range

Áp dụng cho bảy bảng có `LastEditedWhen` trong [Data Profiling Report](wwi-data-profiling.md); đây không phải phép thử completeness của change feed.

```sql
SELECT COUNT_BIG(*) AS rows_exact,
       SUM(CASE WHEN LastEditedWhen IS NULL THEN 1 ELSE 0 END) AS null_timestamps,
       COUNT_BIG(DISTINCT LastEditedWhen) AS distinct_timestamps,
       COUNT_BIG(*) - COUNT_BIG(DISTINCT LastEditedWhen) AS rows_over_distinct,
       MIN(LastEditedWhen) AS min_timestamp,
       MAX(LastEditedWhen) AS max_timestamp
FROM Sales.Orders;
-- Lặp cho Sales.OrderLines, Sales.Invoices, Sales.InvoiceLines,
-- Sales.CustomerTransactions, Warehouse.StockItemHoldings,
-- Warehouse.StockItemTransactions.
```

Mọi truy vấn chỉ trả thống kê tổng hợp. Các câu SQL/kiểm tra này không chốt KPI, fact grain, SCD2 hoặc incremental policy.
