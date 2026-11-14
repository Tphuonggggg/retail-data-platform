# WWI KPI Candidate Verification SQL — Phase 1.5

**Trạng thái: source arithmetic/observations; BRD-01–BRD-12 đã được duyệt ở mức nghiệp vụ.** K01–K09 là các `SELECT` đã chạy read-only trên `WideWorldImporters` local ngày 2026-11-09 bằng Windows integrated authentication; không DDL/DML, không tạo object. Kết quả là từng snapshot truy vấn, không có transaction snapshot chung. K10–K13 kiểm công thức được duyệt; trạng thái chạy của từng query ghi riêng. SQL arithmetic không xác nhận accounting semantics, warehouse hay KPI runtime. Xem [KPI Catalog](wwi-kpi-candidate-catalog.md), [Source Contracts](../../docs/data-models/wwi-source-contracts.md), [Phase 1.2 Profiling SQL](../../docs/data-models/wwi-profiling-queries.md). Không join InvoiceLines và CustomerTransactions để cộng amount.

## K01 — Order/invoice counts và delivery coverage (S01, S02)

```sql
SELECT COUNT_BIG(*) AS order_count FROM Sales.Orders;
SELECT COUNT_BIG(*) AS invoice_count,
       SUM(CASE WHEN ConfirmedDeliveryTime IS NULL THEN 1 ELSE 0 END) AS delivery_null,
       SUM(CASE WHEN IsCreditNote=1 THEN 1 ELSE 0 END) AS credit_notes
FROM Sales.Invoices;
SELECT COUNT_BIG(*) AS orders_no_invoice
FROM Sales.Orders AS o
WHERE NOT EXISTS (SELECT 1 FROM Sales.Invoices AS i WHERE i.OrderID=o.OrderID);
```

**Verified:** 73.595 orders, 70.510 invoices, 84 delivery NULL, 0 credit notes, 3.085 orders chưa invoice. Đây là tổng toàn snapshot; kỳ báo cáo theo `OrderDate`/`InvoiceDate` phải lọc riêng.

## K02 — Source invoice line amounts, tax và arithmetic (S03–S05, S09 source column; S06 cũ gồm thuế)

```sql
SELECT COUNT_BIG(*) AS invoice_lines,
       SUM(CAST(ExtendedPrice AS decimal(38,2))) AS sum_extended,
       SUM(CAST(TaxAmount AS decimal(38,2))) AS sum_tax,
       SUM(CAST(UnitPrice AS decimal(38,4))*Quantity) AS sum_unit_times_qty,
       SUM(CAST(ExtendedPrice AS decimal(38,2))-CAST(TaxAmount AS decimal(38,2)))
         AS sum_extended_less_tax,
       SUM(CAST(LineProfit AS decimal(38,2))) AS sum_line_profit,
       SUM(CASE WHEN LineProfit<0 THEN 1 ELSE 0 END) AS negative_profit,
       SUM(CASE WHEN CAST(UnitPrice AS decimal(38,4))*Quantity <>
                     CAST(ExtendedPrice AS decimal(38,4))-CAST(TaxAmount AS decimal(38,4))
                THEN 1 ELSE 0 END) AS pricing_arithmetic_diff
FROM Sales.InvoiceLines;

SELECT CAST(SUM(CAST(l.ExtendedPrice AS decimal(38,2))) /
            CAST((SELECT COUNT_BIG(*) FROM Sales.Invoices) AS decimal(38,2))
            AS decimal(18,2)) AS avg_source_amount_per_invoice
FROM Sales.InvoiceLines AS l;
```

**Verified source snapshot:** 228.265 lines; ExtendedPrice **198.043.439,45**; TaxAmount **25.782.098,25**; cả `SUM(UnitPrice*Quantity)` và `SUM(ExtendedPrice-TaxAmount)` **172.261.341,20**; arithmetic mismatches 0; `SUM(LineProfit)` **85.729.180,90**, negative LineProfit 4.626 rows; average **including-tax** amount/invoice **2.808,73**, không phải S06 sau phê duyệt. BRD-03 dùng chênh lệch amount-tax làm Invoiced Sales Before Tax theo quy ước phân tích; SQL này không xác nhận doanh thu kế toán hoặc Gross Profit.

## K03 — Invoice-line amount đối chiếu invoice transaction, không cộng hai lần (S03)

```sql
WITH l AS (
  SELECT InvoiceID,SUM(CAST(ExtendedPrice AS decimal(38,2))) AS amount
  FROM Sales.InvoiceLines GROUP BY InvoiceID
), t AS (
  SELECT InvoiceID,COUNT_BIG(*) AS n,SUM(CAST(TransactionAmount AS decimal(38,2))) AS amount
  FROM Sales.CustomerTransactions
  WHERE TransactionTypeID=1 AND InvoiceID IS NOT NULL GROUP BY InvoiceID
)
SELECT COUNT_BIG(*) AS invoices,
       SUM(CASE WHEN t.n=1 AND l.amount=t.amount THEN 1 ELSE 0 END) AS matched,
       SUM(CASE WHEN t.InvoiceID IS NULL OR l.InvoiceID IS NULL OR
                     t.n<>1 OR l.amount<>t.amount THEN 1 ELSE 0 END) AS unmatched
FROM Sales.Invoices AS i
LEFT JOIN l ON l.InvoiceID=i.InvoiceID
LEFT JOIN t ON t.InvoiceID=i.InvoiceID;

SELECT TransactionTypeID,COUNT_BIG(*) AS rows_exact,
       SUM(CAST(TransactionAmount AS decimal(38,2))) AS amount,
       SUM(CASE WHEN InvoiceID IS NULL THEN 1 ELSE 0 END) AS invoice_null
FROM Sales.CustomerTransactions GROUP BY TransactionTypeID;
```

**Verified:** 70.510/70.510 invoices match, 0 mismatch. Type 1: 70.510 rows, amount 198.043.439,45, InvoiceID NULL 0. Type 3 payments: 26.637 rows, amount **−197.776.428,01**, InvoiceID NULL 26.637. Không suy payment allocation hoặc cộng type 1 amount với ExtendedPrice.

## K04 — Purchasing customer và order-based repeat (C01, C02)

```sql
WITH per_customer AS (
  SELECT CustomerID,COUNT_BIG(*) AS orders
  FROM Sales.Orders GROUP BY CustomerID
)
SELECT COUNT_BIG(*) AS purchasing_customers,
       SUM(CASE WHEN orders>=2 THEN 1 ELSE 0 END) AS repeat_customers,
       MIN(orders) AS min_orders_per_customer,
       MAX(orders) AS max_orders_per_customer
FROM per_customer;

SELECT COUNT_BIG(DISTINCT CustomerID) AS invoice_buyer_customers,
       COUNT_BIG(DISTINCT BillToCustomerID) AS invoice_billto_customers
FROM Sales.Invoices;
```

**Verified toàn lịch sử snapshot:** 663 buyers có order; cả 663 có ≥2 order, min 4/max 150 order/buyer. Invoice buyer IDs 663, bill-to IDs 263. Không suy tỷ lệ repeat cho từng kỳ hoặc định nghĩa repeat purchase đã được duyệt.

## K05 — Invoice-line amount theo hai customer roles (C03, C04)

```sql
WITH a AS (
  SELECT i.CustomerID,SUM(CAST(l.ExtendedPrice AS decimal(38,2))) AS amount
  FROM Sales.Invoices AS i JOIN Sales.InvoiceLines AS l ON l.InvoiceID=i.InvoiceID
  GROUP BY i.CustomerID
)
SELECT COUNT_BIG(*) AS buyer_groups,SUM(amount) AS sum_group_amount FROM a;

WITH a AS (
  SELECT i.BillToCustomerID,SUM(CAST(l.ExtendedPrice AS decimal(38,2))) AS amount
  FROM Sales.Invoices AS i JOIN Sales.InvoiceLines AS l ON l.InvoiceID=i.InvoiceID
  GROUP BY i.BillToCustomerID
)
SELECT COUNT_BIG(*) AS billto_groups,SUM(amount) AS sum_group_amount FROM a;
```

**Verified:** 663 buyer groups và 263 bill-to groups; mỗi cách group riêng đều cộng lại thành **198.043.439,45**. Không cộng hai kết quả role với nhau.

## K06 — Current customer category distribution (C05)

```sql
SELECT CustomerCategoryID,COUNT_BIG(*) AS current_customers
FROM Sales.Customers GROUP BY CustomerCategoryID ORDER BY CustomerCategoryID;
```

**Verified:** category IDs 3/4/5/6/7 có tương ứng 459/58/51/48/47 current customers, tổng 663. Đây là current snapshot, không là historical segmentation.

## K07 — Movements theo type và current holdings (I01–I04)

```sql
SELECT TransactionTypeID,COUNT_BIG(*) AS movement_count,
       SUM(CAST(Quantity AS bigint)) AS signed_qty,
       SUM(CASE WHEN Quantity=0 THEN 1 ELSE 0 END) AS zero_qty
FROM Warehouse.StockItemTransactions GROUP BY TransactionTypeID ORDER BY TransactionTypeID;

SELECT COUNT_BIG(*) AS holding_rows,
       SUM(CAST(QuantityOnHand AS bigint)) AS current_qty,
       SUM(CASE WHEN QuantityOnHand=0 THEN 1 ELSE 0 END) AS zero_current_qty
FROM Warehouse.StockItemHoldings;
```

**Verified:** type 10 issue 228.265 rows, signed −8.950.628 (magnitude 8.950.628); type 11 receipt 8.358 rows, +139.418.326; type 12 adjustment 44 rows, signed −18 và 4 zero rows. Current holdings 227 rows, tổng QuantityOnHand **30.343.296**, zero current rows 0. Không suy daily balance từ các tổng này.

## K08 — Movement trends (I05)

```sql
WITH g AS (
  SELECT YEAR(TransactionOccurredWhen) AS yr,MONTH(TransactionOccurredWhen) AS mo,
         StockItemID,TransactionTypeID,COUNT_BIG(*) AS n,
         SUM(CAST(Quantity AS bigint)) AS q
  FROM Warehouse.StockItemTransactions
  GROUP BY YEAR(TransactionOccurredWhen),MONTH(TransactionOccurredWhen),
           StockItemID,TransactionTypeID
)
SELECT COUNT_BIG(*) AS trend_groups,SUM(n) AS movement_rows,SUM(q) AS signed_qty
FROM g;

SELECT YEAR(TransactionOccurredWhen) AS yr,COUNT_BIG(*) AS movement_count,
       SUM(CAST(Quantity AS bigint)) AS signed_qty
FROM Warehouse.StockItemTransactions
GROUP BY YEAR(TransactionOccurredWhen) ORDER BY yr;
```

**Verified:** 9.636 month×item×type groups; cộng lại 236.667 movement rows và signed quantity 130.467.680. Yearly row counts: 2013 63.306, 2014 68.386, 2015 74.451, 2016 đến tháng 5 30.524. Đây là trend movement, không là stock balance.

## K09 — InvoiceDate so với confirmed delivery date (S08 decision evidence)

```sql
SELECT COUNT_BIG(*) AS invoices,
       SUM(CASE WHEN ConfirmedDeliveryTime IS NULL THEN 1 ELSE 0 END) AS delivery_null,
       SUM(CASE WHEN ConfirmedDeliveryTime IS NOT NULL AND
                     CAST(ConfirmedDeliveryTime AS date)=InvoiceDate THEN 1 ELSE 0 END)
         AS same_day,
       SUM(CASE WHEN ConfirmedDeliveryTime IS NOT NULL AND
                     CAST(ConfirmedDeliveryTime AS date)>InvoiceDate THEN 1 ELSE 0 END)
         AS later_day,
       SUM(CASE WHEN ConfirmedDeliveryTime IS NOT NULL AND
                     CAST(ConfirmedDeliveryTime AS date)<InvoiceDate THEN 1 ELSE 0 END)
         AS earlier_day
FROM Sales.Invoices;
```

**Verified:** 70.510 invoices; delivery NULL 84, same day 0, later day 70.426, earlier day 0. Đây là bằng chứng ngày khác nhau, không chọn revenue recognition basis.

## K10 — Average Invoice Value Before Tax (S06)

```sql
WITH invoice_amount AS (
  SELECT i.InvoiceID, i.InvoiceDate,
         SUM(CAST(l.ExtendedPrice AS decimal(38,2)) - CAST(l.TaxAmount AS decimal(38,2))) AS before_tax
  FROM Sales.Invoices AS i
  LEFT JOIN Sales.InvoiceLines AS l ON l.InvoiceID = i.InvoiceID
  GROUP BY i.InvoiceID, i.InvoiceDate
)
SELECT COUNT_BIG(*) AS invoice_count,
       SUM(COALESCE(before_tax, 0)) AS invoiced_sales_before_tax,
       CAST(SUM(COALESCE(before_tax, 0)) / NULLIF(CAST(COUNT_BIG(*) AS decimal(38,2)), 0) AS decimal(18,2)) AS average_invoice_value_before_tax,
       SUM(CASE WHEN before_tax IS NULL THEN 1 ELSE 0 END) AS invoices_without_lines
FROM invoice_amount;
```

**Verified source SQL ngày 2026-11-14:** 70.510 invoice, numerator 172.261.341,20, S06 **2.443,08** tiền nguồn/invoice, invoice không có line 0. Numerator = S05, denominator = S02 cùng population. Query theo kỳ cần lọc `InvoiceDate` trong CTE ở header trước tổng hợp. Zero denominator → NULL.

## K11 — Monthly Repeat Order Customer Rate (C02)

```sql
WITH buyer_month AS (
  SELECT YEAR(OrderDate) AS order_year, MONTH(OrderDate) AS order_month,
         CustomerID, COUNT_BIG(DISTINCT OrderID) AS order_count
  FROM Sales.Orders
  GROUP BY YEAR(OrderDate), MONTH(OrderDate), CustomerID
), monthly AS (
  SELECT order_year, order_month,
         COUNT_BIG(*) AS active_buyers,
         SUM(CASE WHEN order_count >= 2 THEN CAST(1 AS bigint) ELSE CAST(0 AS bigint) END) AS repeat_buyers
  FROM buyer_month GROUP BY order_year, order_month
)
SELECT order_year, order_month, active_buyers, repeat_buyers,
       CAST(CAST(repeat_buyers AS decimal(38,6)) / NULLIF(CAST(active_buyers AS decimal(38,6)), 0) AS decimal(18,6)) AS repeat_order_rate
FROM monthly ORDER BY order_year, order_month;
```

**Verified source SQL ngày 2026-11-14:** truy vấn 41 tháng có order. Truy vấn summary trên cùng CTE cho 23.871 lượt buyer-tháng ở mẫu, 19.134 lượt buyer-tháng ở tử; số repeat buyer từng tháng từ 317 đến 540. Các lượt buyer-tháng cộng qua kỳ **không** là số buyer unique toàn lịch sử hoặc tỷ lệ gộp. Tử ≤ mẫu; chỉ từ `Orders`, `OrderDate`, distinct `OrderID`, không join lines. Quý phải tính lại từ order của cả quý.

## K12 — Buyer và Bill-to attribution theo measure trước thuế (C03/C04)

```sql
WITH per_invoice AS (
  SELECT i.InvoiceID, i.InvoiceDate, i.CustomerID AS BuyerCustomerID,
         i.BillToCustomerID,
         SUM(CAST(l.ExtendedPrice AS decimal(38,2)) - CAST(l.TaxAmount AS decimal(38,2))) AS before_tax
  FROM Sales.Invoices AS i
  JOIN Sales.InvoiceLines AS l ON l.InvoiceID = i.InvoiceID
  GROUP BY i.InvoiceID, i.InvoiceDate, i.CustomerID, i.BillToCustomerID
), buyer AS (
  SELECT BuyerCustomerID, SUM(before_tax) AS amount FROM per_invoice GROUP BY BuyerCustomerID
), billto AS (
  SELECT BillToCustomerID, SUM(before_tax) AS amount FROM per_invoice GROUP BY BillToCustomerID
)
SELECT (SELECT SUM(before_tax) FROM per_invoice) AS invoice_total,
       (SELECT SUM(amount) FROM buyer) AS buyer_total,
       (SELECT SUM(amount) FROM billto) AS billto_total,
       (SELECT COUNT_BIG(*) FROM buyer) AS buyer_groups,
       (SELECT COUNT_BIG(*) FROM billto) AS billto_groups;
```

**Verified source SQL ngày 2026-11-14:** `invoice_total = buyer_total = billto_total = 172.261.341,20`; 663 buyer groups, 263 bill-to groups. Hai phân bố là hai góc nhìn, không cộng với nhau. Lọc cùng `InvoiceDate` ở `per_invoice` nếu báo kỳ.

## K13 — Source-Reported Line Profit (S09)

```sql
SELECT COUNT_BIG(*) AS invoice_line_count,
       SUM(CAST(l.LineProfit AS decimal(38,2))) AS source_reported_line_profit,
       SUM(CASE WHEN l.LineProfit < 0 THEN 1 ELSE 0 END) AS negative_line_count
FROM Sales.InvoiceLines AS l
JOIN Sales.Invoices AS i ON i.InvoiceID = l.InvoiceID;
```

**Verified source SQL ngày 2026-11-14:** 228.265 invoice lines, tổng `LineProfit` 85.729.180,90 và 4.626 dòng âm, khớp K02; lọc `i.InvoiceDate` khi báo kỳ. Đây chỉ là cột lợi nhuận do nguồn báo cáo, không chứng minh COGS lịch sử hoặc Gross Profit chính thức.

## Trạng thái kiểm chứng mới

K10–K13 là `SELECT` read-only đã chạy ngày 2026-11-14 trên SQL Server WWI local. Query summary K11 dùng cùng CTE `buyer_month` và nhóm tiếp theo để đếm 41 tháng và cộng tử/mẫu; số liệu theo từng tháng tái kiểm bằng K11. Các truy vấn không có transaction snapshot chung, nên kết quả chỉ là bằng chứng của các lần đọc nguồn. S07 AOV, S08 Recognized Revenue, S10 refund, I06 daily balance và I07 stockout risk không được xác minh như KPI MVP. Test triển khai/semantic model vẫn `Not implemented yet`.
