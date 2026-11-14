# WWI SCD & Temporal SQL Evidence — DW-02A/B

Các mục C01–C03/P01–P03 bao phủ counts, intervals và precision; L01–L07 bao phủ lookup. `weight` là số source rows trong cùng NK/event time, để giảm repeated comparisons mà vẫn giữ source grain. `MIN(period)` chỉ dùng nhận diện match khi count=1 cho khảo sát; không phải fallback/production algorithm. Internal gaps xét giữa các versions đã có, không bao phủ thời gian trước version đầu.

**SELECT read-only đã chạy trên WWI local ngày 2026-11-14.** Dùng Windows integrated authentication; không DDL/DML, không tạo object/temp table. Kết quả là từng lần đọc, không có transaction snapshot chung. Chỉ lưu aggregates, không customer payload. Lookup proxies phục vụ khảo sát, không phê duyệt as-of/fallback. Precision probes chạy SQL Server, không phải test PostgreSQL conversion.

Attribute-change evidence tái sử dụng [Profiling SQL Q06/Q08](wwi-profiling-queries.md), [Customer profile](wwi-customer-temporal-profiling.md), [Product profile](wwi-inventory-integrity-profiling.md); không tạo bản sao template cùng chức năng.

## C01 Counts & temporal distribution

```sql
SELECT 'current' AS src, COUNT_BIG(*) n,COUNT_BIG(DISTINCT CustomerID) nkeys, CONVERT(varchar(33),MIN(ValidFrom),126) min_from,CONVERT(varchar(33),MAX(ValidFrom),126) max_from, CONVERT(varchar(33),MIN(ValidTo),126) min_to,CONVERT(varchar(33),MAX(ValidTo),126) max_to FROM Sales.Customers
UNION ALL SELECT 'archive',COUNT_BIG(*),COUNT_BIG(DISTINCT CustomerID),CONVERT(varchar(33),MIN(ValidFrom),126),CONVERT(varchar(33),MAX(ValidFrom),126),CONVERT(varchar(33),MIN(ValidTo),126),CONVERT(varchar(33),MAX(ValidTo),126) FROM Sales.Customers_Archive;
SELECT COUNT_BIG(*) AS system_time_all_rows FROM Sales.Customers FOR SYSTEM_TIME ALL;
WITH v AS (SELECT CustomerID AS nk, ValidFrom, ValidTo FROM Sales.Customers UNION ALL SELECT CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive), g AS (SELECT nk,COUNT_BIG(*) n FROM v GROUP BY nk) SELECT n AS versions_per_key,COUNT_BIG(*) AS keys_with_n FROM g GROUP BY n ORDER BY n;
WITH v AS (SELECT CustomerID AS nk, ValidFrom, ValidTo FROM Sales.Customers UNION ALL SELECT CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive) SELECT COUNT_BIG(*) rows_all,COUNT_BIG(DISTINCT ValidFrom) distinct_from,COUNT_BIG(DISTINCT ValidTo) distinct_to,SUM(CASE WHEN ValidTo=CONVERT(datetime2(7),'9999-12-31 23:59:59.9999999') THEN 1 ELSE 0 END) open_ended FROM v;
```

**Verified SELECT 2026-11-14:**

```text
src|n|nkeys|min_from|max_from|min_to|max_to
---|-|-----|--------|--------|------|------
current|663|663|2013-01-01T00:00:00|2016-05-07T00:00:00|9999-12-31T23:59:59.9999999|9999-12-31T23:59:59.9999999
archive|51|46|2013-01-01T00:00:00|2015-06-12T00:00:00|2013-07-01T16:00:00|2015-07-01T16:00:00

(2 rows affected)
system_time_all_rows
--------------------
713

(1 rows affected)
versions_per_key|keys_with_n
----------------|-----------
1|617
2|42
3|3
4|1

(4 rows affected)
rows_all|distinct_from|distinct_to|open_ended
--------|-------------|-----------|----------
714|65|4|663

(1 rows affected)
```

## C02 Interval & identity

```sql
WITH v AS (SELECT CustomerID AS nk, ValidFrom, ValidTo FROM Sales.Customers UNION ALL SELECT CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive), w AS (SELECT *,MAX(ValidTo) OVER(PARTITION BY nk ORDER BY ValidFrom,ValidTo ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) prior_max_to FROM v)
SELECT COUNT_BIG(*) rows_all,SUM(CASE WHEN ValidFrom=ValidTo THEN 1 ELSE 0 END) zero_duration,SUM(CASE WHEN ValidFrom>ValidTo THEN 1 ELSE 0 END) negative_duration,SUM(CASE WHEN prior_max_to>ValidFrom THEN 1 ELSE 0 END) overlaps_prior,SUM(CASE WHEN prior_max_to<ValidFrom THEN 1 ELSE 0 END) internal_gaps FROM w;
WITH v AS (SELECT CustomerID AS nk, ValidFrom, ValidTo FROM Sales.Customers UNION ALL SELECT CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive), g AS (SELECT nk,ValidFrom,ValidTo,COUNT_BIG(*) n FROM v GROUP BY nk,ValidFrom,ValidTo) SELECT COUNT_BIG(*) duplicate_full_identity_groups FROM g WHERE n>1;
WITH v AS (SELECT CustomerID AS nk, ValidFrom, ValidTo FROM Sales.Customers UNION ALL SELECT CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive), g AS (SELECT nk,ValidFrom,COUNT_BIG(*) n FROM v GROUP BY nk,ValidFrom) SELECT COUNT_BIG(*) duplicate_start_identity_groups FROM g WHERE n>1;
```

**Verified SELECT 2026-11-14:**

```text
rows_all|zero_duration|negative_duration|overlaps_prior|internal_gaps
--------|-------------|-----------------|--------------|-------------
714|1|0|0|0

(1 rows affected)
duplicate_full_identity_groups
------------------------------
0

(1 rows affected)
duplicate_start_identity_groups
-------------------------------
1

(1 rows affected)
```

## C03 Precision probes

```sql
WITH v AS (SELECT CustomerID AS nk, ValidFrom, ValidTo FROM Sales.Customers UNION ALL SELECT CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive) SELECT SUM(CASE WHEN DATEPART(nanosecond,ValidFrom)%1000<>0 THEN 1 ELSE 0 END) from_submicro,SUM(CASE WHEN DATEPART(nanosecond,ValidTo)%1000<>0 AND ValidTo<CONVERT(datetime2(7),'9999-12-31') THEN 1 ELSE 0 END) finite_to_submicro,SUM(CASE WHEN ValidTo=CONVERT(datetime2(7),'9999-12-31 23:59:59.9999999') THEN 1 ELSE 0 END) sentinel_requires_separate_conversion FROM v;
WITH v AS (SELECT CustomerID AS nk, ValidFrom, ValidTo FROM Sales.Customers UNION ALL SELECT CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive), t AS (SELECT nk,ValidFrom,ValidTo,DATEADD(nanosecond,-(DATEPART(nanosecond,ValidFrom)%1000),ValidFrom) tf,DATEADD(nanosecond,-(DATEPART(nanosecond,ValidTo)%1000),ValidTo) tt FROM v), g AS (SELECT nk,tf,tt,COUNT_BIG(*) n FROM t GROUP BY nk,tf,tt) SELECT COUNT_BIG(*) truncated_full_key_collision_groups FROM g WHERE n>1;
WITH v AS (SELECT CustomerID AS nk, ValidFrom, ValidTo FROM Sales.Customers UNION ALL SELECT CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive), t AS (SELECT nk,CAST(ValidFrom AS datetime2(6)) rf,CAST(ValidTo AS datetime2(6)) rt FROM v WHERE ValidTo<CONVERT(datetime2(7),'9999-12-31')),g AS (SELECT nk,rf,rt,COUNT_BIG(*) n FROM t GROUP BY nk,rf,rt) SELECT COUNT_BIG(*) sqlserver_rounded_finite_full_key_collision_groups FROM g WHERE n>1;
WITH v AS (SELECT CustomerID AS nk, ValidFrom, ValidTo FROM Sales.Customers UNION ALL SELECT CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive) SELECT SUM(CASE WHEN ValidFrom<ValidTo AND DATEADD(nanosecond,-(DATEPART(nanosecond,ValidFrom)%1000),ValidFrom)=DATEADD(nanosecond,-(DATEPART(nanosecond,ValidTo)%1000),ValidTo) THEN 1 ELSE 0 END) positive_intervals_collapsed_by_truncation FROM v;
```

**Verified SELECT 2026-11-14:**

```text
from_submicro|finite_to_submicro|sentinel_requires_separate_conversion
-------------|------------------|-------------------------------------
0|0|663

(1 rows affected)
truncated_full_key_collision_groups
-----------------------------------
0

(1 rows affected)
sqlserver_rounded_finite_full_key_collision_groups
--------------------------------------------------
0

(1 rows affected)
positive_intervals_collapsed_by_truncation
------------------------------------------
0

(1 rows affected)
```

## P01 Counts & temporal distribution

```sql
SELECT 'current' AS src, COUNT_BIG(*) n,COUNT_BIG(DISTINCT StockItemID) nkeys, CONVERT(varchar(33),MIN(ValidFrom),126) min_from,CONVERT(varchar(33),MAX(ValidFrom),126) max_from, CONVERT(varchar(33),MIN(ValidTo),126) min_to,CONVERT(varchar(33),MAX(ValidTo),126) max_to FROM Warehouse.StockItems
UNION ALL SELECT 'archive',COUNT_BIG(*),COUNT_BIG(DISTINCT StockItemID),CONVERT(varchar(33),MIN(ValidFrom),126),CONVERT(varchar(33),MAX(ValidFrom),126),CONVERT(varchar(33),MIN(ValidTo),126),CONVERT(varchar(33),MAX(ValidTo),126) FROM Warehouse.StockItems_Archive;
SELECT COUNT_BIG(*) AS system_time_all_rows FROM Warehouse.StockItems FOR SYSTEM_TIME ALL;
WITH v AS (SELECT StockItemID AS nk, ValidFrom, ValidTo FROM Warehouse.StockItems UNION ALL SELECT StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems_Archive), g AS (SELECT nk,COUNT_BIG(*) n FROM v GROUP BY nk) SELECT n AS versions_per_key,COUNT_BIG(*) AS keys_with_n FROM g GROUP BY n ORDER BY n;
WITH v AS (SELECT StockItemID AS nk, ValidFrom, ValidTo FROM Warehouse.StockItems UNION ALL SELECT StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems_Archive) SELECT COUNT_BIG(*) rows_all,COUNT_BIG(DISTINCT ValidFrom) distinct_from,COUNT_BIG(DISTINCT ValidTo) distinct_to,SUM(CASE WHEN ValidTo=CONVERT(datetime2(7),'9999-12-31 23:59:59.9999999') THEN 1 ELSE 0 END) open_ended FROM v;
```

**Verified SELECT 2026-11-14:**

```text
src|n|nkeys|min_from|max_from|min_to|max_to
---|-|-----|--------|--------|------|------
current|227|227|2016-05-31T23:00:00|2016-05-31T23:12:00|9999-12-31T23:59:59.9999999|9999-12-31T23:59:59.9999999
archive|444|227|2013-01-01T00:00:00|2016-05-31T23:09:00|2016-05-31T23:00:00|2016-05-31T23:12:00

(2 rows affected)
system_time_all_rows
--------------------
671

(1 rows affected)
versions_per_key|keys_with_n
----------------|-----------
2|55
3|129
4|41
5|2

(4 rows affected)
rows_all|distinct_from|distinct_to|open_ended
--------|-------------|-----------|----------
671|18|14|227

(1 rows affected)
```

## P02 Interval & identity

```sql
WITH v AS (SELECT StockItemID AS nk, ValidFrom, ValidTo FROM Warehouse.StockItems UNION ALL SELECT StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems_Archive), w AS (SELECT *,MAX(ValidTo) OVER(PARTITION BY nk ORDER BY ValidFrom,ValidTo ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) prior_max_to FROM v)
SELECT COUNT_BIG(*) rows_all,SUM(CASE WHEN ValidFrom=ValidTo THEN 1 ELSE 0 END) zero_duration,SUM(CASE WHEN ValidFrom>ValidTo THEN 1 ELSE 0 END) negative_duration,SUM(CASE WHEN prior_max_to>ValidFrom THEN 1 ELSE 0 END) overlaps_prior,SUM(CASE WHEN prior_max_to<ValidFrom THEN 1 ELSE 0 END) internal_gaps FROM w;
WITH v AS (SELECT StockItemID AS nk, ValidFrom, ValidTo FROM Warehouse.StockItems UNION ALL SELECT StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems_Archive), g AS (SELECT nk,ValidFrom,ValidTo,COUNT_BIG(*) n FROM v GROUP BY nk,ValidFrom,ValidTo) SELECT COUNT_BIG(*) duplicate_full_identity_groups FROM g WHERE n>1;
WITH v AS (SELECT StockItemID AS nk, ValidFrom, ValidTo FROM Warehouse.StockItems UNION ALL SELECT StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems_Archive), g AS (SELECT nk,ValidFrom,COUNT_BIG(*) n FROM v GROUP BY nk,ValidFrom) SELECT COUNT_BIG(*) duplicate_start_identity_groups FROM g WHERE n>1;
```

**Verified SELECT 2026-11-14:**

```text
rows_all|zero_duration|negative_duration|overlaps_prior|internal_gaps
--------|-------------|-----------------|--------------|-------------
671|0|0|0|0

(1 rows affected)
duplicate_full_identity_groups
------------------------------
0

(1 rows affected)
duplicate_start_identity_groups
-------------------------------
0

(1 rows affected)
```

## P03 Precision probes

```sql
WITH v AS (SELECT StockItemID AS nk, ValidFrom, ValidTo FROM Warehouse.StockItems UNION ALL SELECT StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems_Archive) SELECT SUM(CASE WHEN DATEPART(nanosecond,ValidFrom)%1000<>0 THEN 1 ELSE 0 END) from_submicro,SUM(CASE WHEN DATEPART(nanosecond,ValidTo)%1000<>0 AND ValidTo<CONVERT(datetime2(7),'9999-12-31') THEN 1 ELSE 0 END) finite_to_submicro,SUM(CASE WHEN ValidTo=CONVERT(datetime2(7),'9999-12-31 23:59:59.9999999') THEN 1 ELSE 0 END) sentinel_requires_separate_conversion FROM v;
WITH v AS (SELECT StockItemID AS nk, ValidFrom, ValidTo FROM Warehouse.StockItems UNION ALL SELECT StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems_Archive), t AS (SELECT nk,ValidFrom,ValidTo,DATEADD(nanosecond,-(DATEPART(nanosecond,ValidFrom)%1000),ValidFrom) tf,DATEADD(nanosecond,-(DATEPART(nanosecond,ValidTo)%1000),ValidTo) tt FROM v), g AS (SELECT nk,tf,tt,COUNT_BIG(*) n FROM t GROUP BY nk,tf,tt) SELECT COUNT_BIG(*) truncated_full_key_collision_groups FROM g WHERE n>1;
WITH v AS (SELECT StockItemID AS nk, ValidFrom, ValidTo FROM Warehouse.StockItems UNION ALL SELECT StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems_Archive), t AS (SELECT nk,CAST(ValidFrom AS datetime2(6)) rf,CAST(ValidTo AS datetime2(6)) rt FROM v WHERE ValidTo<CONVERT(datetime2(7),'9999-12-31')),g AS (SELECT nk,rf,rt,COUNT_BIG(*) n FROM t GROUP BY nk,rf,rt) SELECT COUNT_BIG(*) sqlserver_rounded_finite_full_key_collision_groups FROM g WHERE n>1;
WITH v AS (SELECT StockItemID AS nk, ValidFrom, ValidTo FROM Warehouse.StockItems UNION ALL SELECT StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems_Archive) SELECT SUM(CASE WHEN ValidFrom<ValidTo AND DATEADD(nanosecond,-(DATEPART(nanosecond,ValidFrom)%1000),ValidFrom)=DATEADD(nanosecond,-(DATEPART(nanosecond,ValidTo)%1000),ValidTo) THEN 1 ELSE 0 END) positive_intervals_collapsed_by_truncation FROM v;
```

**Verified SELECT 2026-11-14:**

```text
from_submicro|finite_to_submicro|sentinel_requires_separate_conversion
-------------|------------------|-------------------------------------
0|0|227

(1 rows affected)
truncated_full_key_collision_groups
-----------------------------------
0

(1 rows affected)
sqlserver_rounded_finite_full_key_collision_groups
--------------------------------------------------
0

(1 rows affected)
positive_intervals_collapsed_by_truncation
------------------------------------------
0

(1 rows affected)
```

## L01 Invoice Buyer

```sql
WITH v AS (SELECT CustomerID nk,ValidFrom,ValidTo FROM Sales.Customers UNION ALL SELECT CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive), e AS (SELECT CustomerID nk,CAST(InvoiceDate AS datetime2(7)) event_at FROM Sales.Invoices), g AS (SELECT nk,event_at,COUNT_BIG(*) weight FROM e GROUP BY nk,event_at), d AS (SELECT *,CAST(CAST(event_at AS date) AS datetime2(7)) day_start,DATEADD(nanosecond,-100,DATEADD(day,1,CAST(CAST(event_at AS date) AS datetime2(7)))) day_end FROM g)
SELECT SUM(d.weight) source_rows,
SUM(CASE WHEN a.n=0 THEN d.weight ELSE 0 END) start_no_match,SUM(CASE WHEN a.n>1 THEN d.weight ELSE 0 END) start_multi,
SUM(CASE WHEN b.n=0 THEN d.weight ELSE 0 END) end_no_match,SUM(CASE WHEN b.n>1 THEN d.weight ELSE 0 END) end_multi,
SUM(CASE WHEN a.n=1 AND b.n=1 AND (a.vf<>b.vf OR a.vt<>b.vt) THEN d.weight ELSE 0 END) changed_version_within_day,
SUM(CASE WHEN c.n>1 THEN d.weight ELSE 0 END) multiple_positive_versions_in_day,
SUM(CASE WHEN x.n=0 THEN d.weight ELSE 0 END) event_no_match,SUM(CASE WHEN x.n>1 THEN d.weight ELSE 0 END) event_multi
FROM d
OUTER APPLY (SELECT COUNT_BIG(*) n,MIN(ValidFrom) vf,MIN(ValidTo) vt FROM v WHERE v.nk=d.nk AND ValidFrom<=day_start AND day_start<ValidTo) a
OUTER APPLY (SELECT COUNT_BIG(*) n,MIN(ValidFrom) vf,MIN(ValidTo) vt FROM v WHERE v.nk=d.nk AND ValidFrom<=day_end AND day_end<ValidTo) b
OUTER APPLY (SELECT COUNT_BIG(*) n FROM v WHERE v.nk=d.nk AND ValidFrom<ValidTo AND ValidFrom<=day_end AND ValidTo>day_start) c
OUTER APPLY (SELECT COUNT_BIG(*) n FROM v WHERE v.nk=d.nk AND ValidFrom<=event_at AND event_at<ValidTo) x;
```

**Verified SELECT 2026-11-14:**

```text
source_rows|start_no_match|start_multi|end_no_match|end_multi|changed_version_within_day|multiple_positive_versions_in_day|event_no_match|event_multi
-----------|--------------|-----------|------------|---------|--------------------------|---------------------------------|--------------|-----------
70510|0|0|0|0|6|6|0|0

(1 rows affected)
```

## L02 Invoice Bill-to

```sql
WITH v AS (SELECT CustomerID nk,ValidFrom,ValidTo FROM Sales.Customers UNION ALL SELECT CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive), e AS (SELECT BillToCustomerID nk,CAST(InvoiceDate AS datetime2(7)) event_at FROM Sales.Invoices), g AS (SELECT nk,event_at,COUNT_BIG(*) weight FROM e GROUP BY nk,event_at), d AS (SELECT *,CAST(CAST(event_at AS date) AS datetime2(7)) day_start,DATEADD(nanosecond,-100,DATEADD(day,1,CAST(CAST(event_at AS date) AS datetime2(7)))) day_end FROM g)
SELECT SUM(d.weight) source_rows,
SUM(CASE WHEN a.n=0 THEN d.weight ELSE 0 END) start_no_match,SUM(CASE WHEN a.n>1 THEN d.weight ELSE 0 END) start_multi,
SUM(CASE WHEN b.n=0 THEN d.weight ELSE 0 END) end_no_match,SUM(CASE WHEN b.n>1 THEN d.weight ELSE 0 END) end_multi,
SUM(CASE WHEN a.n=1 AND b.n=1 AND (a.vf<>b.vf OR a.vt<>b.vt) THEN d.weight ELSE 0 END) changed_version_within_day,
SUM(CASE WHEN c.n>1 THEN d.weight ELSE 0 END) multiple_positive_versions_in_day,
SUM(CASE WHEN x.n=0 THEN d.weight ELSE 0 END) event_no_match,SUM(CASE WHEN x.n>1 THEN d.weight ELSE 0 END) event_multi
FROM d
OUTER APPLY (SELECT COUNT_BIG(*) n,MIN(ValidFrom) vf,MIN(ValidTo) vt FROM v WHERE v.nk=d.nk AND ValidFrom<=day_start AND day_start<ValidTo) a
OUTER APPLY (SELECT COUNT_BIG(*) n,MIN(ValidFrom) vf,MIN(ValidTo) vt FROM v WHERE v.nk=d.nk AND ValidFrom<=day_end AND day_end<ValidTo) b
OUTER APPLY (SELECT COUNT_BIG(*) n FROM v WHERE v.nk=d.nk AND ValidFrom<ValidTo AND ValidFrom<=day_end AND ValidTo>day_start) c
OUTER APPLY (SELECT COUNT_BIG(*) n FROM v WHERE v.nk=d.nk AND ValidFrom<=event_at AND event_at<ValidTo) x;
```

**Verified SELECT 2026-11-14:**

```text
source_rows|start_no_match|start_multi|end_no_match|end_multi|changed_version_within_day|multiple_positive_versions_in_day|event_no_match|event_multi
-----------|--------------|-----------|------------|---------|--------------------------|---------------------------------|--------------|-----------
70510|0|0|0|0|6|6|0|0

(1 rows affected)
```

## L03 Order Buyer

```sql
WITH v AS (SELECT CustomerID nk,ValidFrom,ValidTo FROM Sales.Customers UNION ALL SELECT CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive), e AS (SELECT CustomerID nk,CAST(OrderDate AS datetime2(7)) event_at FROM Sales.Orders), g AS (SELECT nk,event_at,COUNT_BIG(*) weight FROM e GROUP BY nk,event_at), d AS (SELECT *,CAST(CAST(event_at AS date) AS datetime2(7)) day_start,DATEADD(nanosecond,-100,DATEADD(day,1,CAST(CAST(event_at AS date) AS datetime2(7)))) day_end FROM g)
SELECT SUM(d.weight) source_rows,
SUM(CASE WHEN a.n=0 THEN d.weight ELSE 0 END) start_no_match,SUM(CASE WHEN a.n>1 THEN d.weight ELSE 0 END) start_multi,
SUM(CASE WHEN b.n=0 THEN d.weight ELSE 0 END) end_no_match,SUM(CASE WHEN b.n>1 THEN d.weight ELSE 0 END) end_multi,
SUM(CASE WHEN a.n=1 AND b.n=1 AND (a.vf<>b.vf OR a.vt<>b.vt) THEN d.weight ELSE 0 END) changed_version_within_day,
SUM(CASE WHEN c.n>1 THEN d.weight ELSE 0 END) multiple_positive_versions_in_day,
SUM(CASE WHEN x.n=0 THEN d.weight ELSE 0 END) event_no_match,SUM(CASE WHEN x.n>1 THEN d.weight ELSE 0 END) event_multi
FROM d
OUTER APPLY (SELECT COUNT_BIG(*) n,MIN(ValidFrom) vf,MIN(ValidTo) vt FROM v WHERE v.nk=d.nk AND ValidFrom<=day_start AND day_start<ValidTo) a
OUTER APPLY (SELECT COUNT_BIG(*) n,MIN(ValidFrom) vf,MIN(ValidTo) vt FROM v WHERE v.nk=d.nk AND ValidFrom<=day_end AND day_end<ValidTo) b
OUTER APPLY (SELECT COUNT_BIG(*) n FROM v WHERE v.nk=d.nk AND ValidFrom<ValidTo AND ValidFrom<=day_end AND ValidTo>day_start) c
OUTER APPLY (SELECT COUNT_BIG(*) n FROM v WHERE v.nk=d.nk AND ValidFrom<=event_at AND event_at<ValidTo) x;
```

**Verified SELECT 2026-11-14:**

```text
source_rows|start_no_match|start_multi|end_no_match|end_multi|changed_version_within_day|multiple_positive_versions_in_day|event_no_match|event_multi
-----------|--------------|-----------|------------|---------|--------------------------|---------------------------------|--------------|-----------
73595|0|0|0|0|6|6|0|0

(1 rows affected)
```

## L04 Invoice Product

```sql
WITH v AS (SELECT StockItemID nk,ValidFrom,ValidTo FROM Warehouse.StockItems UNION ALL SELECT StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems_Archive), e AS (SELECT l.StockItemID nk,CAST(i.InvoiceDate AS datetime2(7)) event_at FROM Sales.InvoiceLines l JOIN Sales.Invoices i ON i.InvoiceID=l.InvoiceID), g AS (SELECT nk,event_at,COUNT_BIG(*) weight FROM e GROUP BY nk,event_at), d AS (SELECT *,CAST(CAST(event_at AS date) AS datetime2(7)) day_start,DATEADD(nanosecond,-100,DATEADD(day,1,CAST(CAST(event_at AS date) AS datetime2(7)))) day_end FROM g)
SELECT SUM(d.weight) source_rows,
SUM(CASE WHEN a.n=0 THEN d.weight ELSE 0 END) start_no_match,SUM(CASE WHEN a.n>1 THEN d.weight ELSE 0 END) start_multi,
SUM(CASE WHEN b.n=0 THEN d.weight ELSE 0 END) end_no_match,SUM(CASE WHEN b.n>1 THEN d.weight ELSE 0 END) end_multi,
SUM(CASE WHEN a.n=1 AND b.n=1 AND (a.vf<>b.vf OR a.vt<>b.vt) THEN d.weight ELSE 0 END) changed_version_within_day,
SUM(CASE WHEN c.n>1 THEN d.weight ELSE 0 END) multiple_positive_versions_in_day,
SUM(CASE WHEN x.n=0 THEN d.weight ELSE 0 END) event_no_match,SUM(CASE WHEN x.n>1 THEN d.weight ELSE 0 END) event_multi
FROM d
OUTER APPLY (SELECT COUNT_BIG(*) n,MIN(ValidFrom) vf,MIN(ValidTo) vt FROM v WHERE v.nk=d.nk AND ValidFrom<=day_start AND day_start<ValidTo) a
OUTER APPLY (SELECT COUNT_BIG(*) n,MIN(ValidFrom) vf,MIN(ValidTo) vt FROM v WHERE v.nk=d.nk AND ValidFrom<=day_end AND day_end<ValidTo) b
OUTER APPLY (SELECT COUNT_BIG(*) n FROM v WHERE v.nk=d.nk AND ValidFrom<ValidTo AND ValidFrom<=day_end AND ValidTo>day_start) c
OUTER APPLY (SELECT COUNT_BIG(*) n FROM v WHERE v.nk=d.nk AND ValidFrom<=event_at AND event_at<ValidTo) x;
```

**Verified SELECT 2026-11-14:**

```text
source_rows|start_no_match|start_multi|end_no_match|end_multi|changed_version_within_day|multiple_positive_versions_in_day|event_no_match|event_multi
-----------|--------------|-----------|------------|---------|--------------------------|---------------------------------|--------------|-----------
228265|0|0|0|0|284|284|0|0

(1 rows affected)
```

## L05 Order Product

```sql
WITH v AS (SELECT StockItemID nk,ValidFrom,ValidTo FROM Warehouse.StockItems UNION ALL SELECT StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems_Archive), e AS (SELECT l.StockItemID nk,CAST(o.OrderDate AS datetime2(7)) event_at FROM Sales.OrderLines l JOIN Sales.Orders o ON o.OrderID=l.OrderID), g AS (SELECT nk,event_at,COUNT_BIG(*) weight FROM e GROUP BY nk,event_at), d AS (SELECT *,CAST(CAST(event_at AS date) AS datetime2(7)) day_start,DATEADD(nanosecond,-100,DATEADD(day,1,CAST(CAST(event_at AS date) AS datetime2(7)))) day_end FROM g)
SELECT SUM(d.weight) source_rows,
SUM(CASE WHEN a.n=0 THEN d.weight ELSE 0 END) start_no_match,SUM(CASE WHEN a.n>1 THEN d.weight ELSE 0 END) start_multi,
SUM(CASE WHEN b.n=0 THEN d.weight ELSE 0 END) end_no_match,SUM(CASE WHEN b.n>1 THEN d.weight ELSE 0 END) end_multi,
SUM(CASE WHEN a.n=1 AND b.n=1 AND (a.vf<>b.vf OR a.vt<>b.vt) THEN d.weight ELSE 0 END) changed_version_within_day,
SUM(CASE WHEN c.n>1 THEN d.weight ELSE 0 END) multiple_positive_versions_in_day,
SUM(CASE WHEN x.n=0 THEN d.weight ELSE 0 END) event_no_match,SUM(CASE WHEN x.n>1 THEN d.weight ELSE 0 END) event_multi
FROM d
OUTER APPLY (SELECT COUNT_BIG(*) n,MIN(ValidFrom) vf,MIN(ValidTo) vt FROM v WHERE v.nk=d.nk AND ValidFrom<=day_start AND day_start<ValidTo) a
OUTER APPLY (SELECT COUNT_BIG(*) n,MIN(ValidFrom) vf,MIN(ValidTo) vt FROM v WHERE v.nk=d.nk AND ValidFrom<=day_end AND day_end<ValidTo) b
OUTER APPLY (SELECT COUNT_BIG(*) n FROM v WHERE v.nk=d.nk AND ValidFrom<ValidTo AND ValidFrom<=day_end AND ValidTo>day_start) c
OUTER APPLY (SELECT COUNT_BIG(*) n FROM v WHERE v.nk=d.nk AND ValidFrom<=event_at AND event_at<ValidTo) x;
```

**Verified SELECT 2026-11-14:**

```text
source_rows|start_no_match|start_multi|end_no_match|end_multi|changed_version_within_day|multiple_positive_versions_in_day|event_no_match|event_multi
-----------|--------------|-----------|------------|---------|--------------------------|---------------------------------|--------------|-----------
231412|0|0|0|0|291|291|0|0

(1 rows affected)
```

## L06 Movement Product

```sql
WITH v AS (SELECT StockItemID nk,ValidFrom,ValidTo FROM Warehouse.StockItems UNION ALL SELECT StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems_Archive), e AS (SELECT StockItemID nk,TransactionOccurredWhen event_at FROM Warehouse.StockItemTransactions), g AS (SELECT nk,event_at,COUNT_BIG(*) weight FROM e GROUP BY nk,event_at), d AS (SELECT *,CAST(CAST(event_at AS date) AS datetime2(7)) day_start,DATEADD(nanosecond,-100,DATEADD(day,1,CAST(CAST(event_at AS date) AS datetime2(7)))) day_end FROM g)
SELECT SUM(d.weight) source_rows,
SUM(CASE WHEN a.n=0 THEN d.weight ELSE 0 END) start_no_match,SUM(CASE WHEN a.n>1 THEN d.weight ELSE 0 END) start_multi,
SUM(CASE WHEN b.n=0 THEN d.weight ELSE 0 END) end_no_match,SUM(CASE WHEN b.n>1 THEN d.weight ELSE 0 END) end_multi,
SUM(CASE WHEN a.n=1 AND b.n=1 AND (a.vf<>b.vf OR a.vt<>b.vt) THEN d.weight ELSE 0 END) changed_version_within_day,
SUM(CASE WHEN c.n>1 THEN d.weight ELSE 0 END) multiple_positive_versions_in_day,
SUM(CASE WHEN x.n=0 THEN d.weight ELSE 0 END) event_no_match,SUM(CASE WHEN x.n>1 THEN d.weight ELSE 0 END) event_multi
FROM d
OUTER APPLY (SELECT COUNT_BIG(*) n,MIN(ValidFrom) vf,MIN(ValidTo) vt FROM v WHERE v.nk=d.nk AND ValidFrom<=day_start AND day_start<ValidTo) a
OUTER APPLY (SELECT COUNT_BIG(*) n,MIN(ValidFrom) vf,MIN(ValidTo) vt FROM v WHERE v.nk=d.nk AND ValidFrom<=day_end AND day_end<ValidTo) b
OUTER APPLY (SELECT COUNT_BIG(*) n FROM v WHERE v.nk=d.nk AND ValidFrom<ValidTo AND ValidFrom<=day_end AND ValidTo>day_start) c
OUTER APPLY (SELECT COUNT_BIG(*) n FROM v WHERE v.nk=d.nk AND ValidFrom<=event_at AND event_at<ValidTo) x;
```

**Verified SELECT 2026-11-14:**

```text
source_rows|start_no_match|start_multi|end_no_match|end_multi|changed_version_within_day|multiple_positive_versions_in_day|event_no_match|event_multi
-----------|--------------|-----------|------------|---------|--------------------------|---------------------------------|--------------|-----------
236667|0|0|0|0|293|293|0|0

(1 rows affected)
```

## L07 Current Product availability

```sql
SELECT COUNT_BIG(*) holding_rows,SUM(CASE WHEN p.StockItemID IS NULL THEN 1 ELSE 0 END) missing_current_product,SUM(CASE WHEN p.ValidTo<>CONVERT(datetime2(7),'9999-12-31 23:59:59.9999999') THEN 1 ELSE 0 END) non_open_current_product FROM Warehouse.StockItemHoldings h LEFT JOIN Warehouse.StockItems p ON p.StockItemID=h.StockItemID;
```

**Verified SELECT 2026-11-14:**

```text
holding_rows|missing_current_product|non_open_current_product
------------|-----------------------|------------------------
227|0|0

(1 rows affected)
```

## C04 Customer duplicate-start follow-up

```sql
WITH v AS (
  SELECT CustomerID nk,ValidFrom,ValidTo FROM Sales.Customers
  UNION ALL SELECT CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive
),g AS (
  SELECT nk,ValidFrom,COUNT_BIG(*) n,
         SUM(CASE WHEN ValidFrom=ValidTo THEN 1 ELSE 0 END) z
  FROM v GROUP BY nk,ValidFrom
)
SELECT COUNT_BIG(*) duplicate_start_groups,SUM(z) zero_rows_in_duplicate_groups
FROM g WHERE n>1;
WITH v AS (
  SELECT CustomerID nk,ValidFrom,ValidTo FROM Sales.Customers
  UNION ALL SELECT CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive
),g AS (
  SELECT nk,ValidFrom,COUNT_BIG(*) n FROM v WHERE ValidFrom<ValidTo
  GROUP BY nk,ValidFrom
)
SELECT COUNT_BIG(*) positive_only_duplicate_start_groups FROM g WHERE n>1;
```

**Verified SELECT 2026-11-14:** duplicate_start_groups=1; zero_rows_in_duplicate_groups=1; positive_only_duplicate_start_groups=0. Không loại physical zero-duration khỏi raw/audit; query positive-only chỉ là phân tích sensitivity, không chốt DW filtering policy.


## C05 Period year distribution

```sql
WITH v AS (SELECT ValidFrom,ValidTo FROM Sales.Customers UNION ALL SELECT ValidFrom,ValidTo FROM Sales.Customers_Archive)
SELECT 'ValidFrom' AS period_field,YEAR(ValidFrom) AS period_year,COUNT_BIG(*) AS version_rows FROM v GROUP BY YEAR(ValidFrom)
UNION ALL SELECT 'ValidTo',YEAR(ValidTo),COUNT_BIG(*) FROM v GROUP BY YEAR(ValidTo)
ORDER BY period_field,period_year;
```

**Verified SELECT 2026-11-14:**

```text
period_field|period_year|version_rows
------------|-----------|------------
ValidFrom|2013|644
ValidFrom|2014|31
ValidFrom|2015|34
ValidFrom|2016|5
ValidTo|2013|18
ValidTo|2014|17
ValidTo|2015|16
ValidTo|9999|663

(8 rows affected)
```

## P04 Period year distribution

```sql
WITH v AS (SELECT ValidFrom,ValidTo FROM Warehouse.StockItems UNION ALL SELECT ValidFrom,ValidTo FROM Warehouse.StockItems_Archive)
SELECT 'ValidFrom' AS period_field,YEAR(ValidFrom) AS period_year,COUNT_BIG(*) AS version_rows FROM v GROUP BY YEAR(ValidFrom)
UNION ALL SELECT 'ValidTo',YEAR(ValidTo),COUNT_BIG(*) FROM v GROUP BY YEAR(ValidTo)
ORDER BY period_field,period_year;
```

**Verified SELECT 2026-11-14:**

```text
period_field|period_year|version_rows
------------|-----------|------------
ValidFrom|2013|219
ValidFrom|2016|452
ValidTo|2016|444
ValidTo|9999|227

(4 rows affected)
```
