# Truy vấn kiểm chứng metadata WWI — Phase 1.1

**Trạng thái: Verified — các truy vấn dưới đây chỉ đọc catalog SQL Server.** Đã chạy ngày 2026-11-07 với Windows integrated authentication trên `.\SQLEXPRESS`, database `WideWorldImporters`. `sqlcmd -E -C` dùng quyền Windows hiện có và tin cậy chứng chỉ TLS local trong phiên client; không ghi credential hoặc thay đổi cấu hình server. Có thể chạy từng khối `SELECT` bằng `sqlcmd -S '.\SQLEXPRESS' -d WideWorldImporters -E -C -b -Q "<query>"` hoặc công cụ SQL tương đương. Không chạy DDL/DML, không bật CDC/Change Tracking.

## Q01 — Server, database và schema

```sql
SELECT CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(128)) AS product_version,
       CAST(SERVERPROPERTY('Edition') AS nvarchar(128)) AS edition,
       d.name, d.state_desc, d.compatibility_level, d.is_cdc_enabled
FROM sys.databases AS d
WHERE d.name = DB_NAME();

SELECT SYSUTCDATETIME() AS assessed_at_utc;

SELECT s.name AS schema_name, COUNT(t.object_id) AS user_table_count
FROM sys.schemas AS s
LEFT JOIN sys.tables AS t
  ON t.schema_id = s.schema_id AND t.is_ms_shipped = 0
GROUP BY s.name
ORDER BY s.name;
```

## Q02 — Table inventory và metadata row count

`rows` lấy từ `sys.partitions`, chỉ cộng `index_id` 0/1 để tránh đếm nhiều index. Đây là **metadata estimate**, không phải `COUNT(*)`.

```sql
SELECT s.name AS schema_name, t.name AS table_name,
       t.temporal_type_desc,
       hs.name AS history_schema, ht.name AS history_table,
       COALESCE(SUM(CASE WHEN p.index_id IN (0,1) THEN p.rows ELSE 0 END),0)
         AS metadata_rows
FROM sys.tables AS t
JOIN sys.schemas AS s ON s.schema_id = t.schema_id
LEFT JOIN sys.tables AS ht ON ht.object_id = t.history_table_id
LEFT JOIN sys.schemas AS hs ON hs.schema_id = ht.schema_id
LEFT JOIN sys.partitions AS p ON p.object_id = t.object_id
WHERE t.is_ms_shipped = 0
GROUP BY s.name, t.name, t.temporal_type_desc, hs.name, ht.name
ORDER BY s.name, t.name;
```

## Q03 — Column, data type, nullability, default và versioning

Đã lọc chín bảng MVP theo `s.name + '.' + t.name`. Có thể bỏ filter để kiểm kê các bảng ngoài MVP.

```sql
SELECT s.name + '.' + t.name AS source_table, c.column_id, c.name AS column_name,
       ty.name AS data_type, c.max_length, c.precision, c.scale,
       c.is_nullable, c.is_identity, c.is_computed, c.is_hidden,
       c.generated_always_type_desc,
       dc.name AS default_constraint_name, dc.definition AS default_definition
FROM sys.tables AS t
JOIN sys.schemas AS s ON s.schema_id = t.schema_id
JOIN sys.columns AS c ON c.object_id = t.object_id
JOIN sys.types AS ty ON ty.user_type_id = c.user_type_id
LEFT JOIN sys.default_constraints AS dc ON dc.object_id = c.default_object_id
WHERE s.name + '.' + t.name IN
  ('Sales.Customers','Sales.Orders','Sales.OrderLines','Sales.Invoices',
   'Sales.InvoiceLines','Sales.CustomerTransactions','Warehouse.StockItems',
   'Warehouse.StockItemHoldings','Warehouse.StockItemTransactions')
ORDER BY s.name, t.name, c.column_id;
```

## Q04 — PK, unique constraint và FK

```sql
SELECT s.name + '.' + t.name AS source_table, kc.type_desc, kc.name AS constraint_name,
       ic.key_ordinal, c.name AS column_name
FROM sys.key_constraints AS kc
JOIN sys.tables AS t ON t.object_id = kc.parent_object_id
JOIN sys.schemas AS s ON s.schema_id = t.schema_id
JOIN sys.index_columns AS ic
  ON ic.object_id = t.object_id AND ic.index_id = kc.unique_index_id
  AND ic.key_ordinal > 0
JOIN sys.columns AS c ON c.object_id = t.object_id AND c.column_id = ic.column_id
ORDER BY s.name, t.name, kc.name, ic.key_ordinal;

SELECT fk.name AS fk_name,
       ps.name + '.' + pt.name AS child_table, pc.name AS child_column,
       rs.name + '.' + rt.name AS parent_table, rc.name AS parent_column,
       fkc.constraint_column_id, fk.is_disabled, fk.is_not_trusted,
       fk.delete_referential_action_desc
FROM sys.foreign_keys AS fk
JOIN sys.foreign_key_columns AS fkc ON fkc.constraint_object_id = fk.object_id
JOIN sys.tables AS pt ON pt.object_id = fk.parent_object_id
JOIN sys.schemas AS ps ON ps.schema_id = pt.schema_id
JOIN sys.columns AS pc
  ON pc.object_id = pt.object_id AND pc.column_id = fkc.parent_column_id
JOIN sys.tables AS rt ON rt.object_id = fk.referenced_object_id
JOIN sys.schemas AS rs ON rs.schema_id = rt.schema_id
JOIN sys.columns AS rc
  ON rc.object_id = rt.object_id AND rc.column_id = fkc.referenced_column_id
ORDER BY ps.name, pt.name, fk.name, fkc.constraint_column_id;

SELECT COUNT(*) AS fk_total,
       SUM(CAST(is_disabled AS int)) AS disabled_fk_count,
       SUM(CAST(is_not_trusted AS int)) AS untrusted_fk_count
FROM sys.foreign_keys;
```

## Q05 — System-versioned temporal và history period

```sql
SELECT s.name + '.' + t.name AS current_table,
       hs.name + '.' + ht.name AS history_table,
       sc.name AS period_start, ec.name AS period_end,
       t.history_retention_period, t.history_retention_period_unit_desc
FROM sys.tables AS t
JOIN sys.schemas AS s ON s.schema_id = t.schema_id
JOIN sys.tables AS ht ON ht.object_id = t.history_table_id
JOIN sys.schemas AS hs ON hs.schema_id = ht.schema_id
JOIN sys.periods AS p ON p.object_id = t.object_id
JOIN sys.columns AS sc
  ON sc.object_id = t.object_id AND sc.column_id = p.start_column_id
JOIN sys.columns AS ec
  ON ec.object_id = t.object_id AND ec.column_id = p.end_column_id
WHERE t.temporal_type = 2
ORDER BY s.name, t.name;
```

## Q06 — Index loại, key, included/partition column

```sql
SELECT s.name + '.' + t.name AS source_table, i.name AS index_name,
       i.type_desc, i.is_unique, i.is_primary_key, i.is_unique_constraint,
       i.has_filter, i.filter_definition,
       ic.key_ordinal, ic.partition_ordinal, ic.is_included_column,
       c.name AS column_name
FROM sys.tables AS t
JOIN sys.schemas AS s ON s.schema_id = t.schema_id
JOIN sys.indexes AS i ON i.object_id = t.object_id AND i.index_id > 0
LEFT JOIN sys.index_columns AS ic
  ON ic.object_id = i.object_id AND ic.index_id = i.index_id
LEFT JOIN sys.columns AS c
  ON c.object_id = ic.object_id AND c.column_id = ic.column_id
WHERE s.name + '.' + t.name IN
  ('Sales.Customers','Sales.Orders','Sales.OrderLines','Sales.Invoices',
   'Sales.InvoiceLines','Sales.CustomerTransactions','Warehouse.StockItems',
   'Warehouse.StockItemHoldings','Warehouse.StockItemTransactions')
ORDER BY s.name, t.name, i.index_id, ic.key_ordinal, ic.index_column_id;

SELECT i.type_desc, COUNT(*) AS index_count
FROM sys.indexes AS i
JOIN sys.tables AS t ON t.object_id = i.object_id
WHERE t.is_ms_shipped = 0 AND i.index_id > 0
GROUP BY i.type_desc;
```

## Q07 — CDC và Change Tracking trạng thái metadata

```sql
SELECT d.name, d.is_cdc_enabled,
       CASE WHEN ctd.database_id IS NULL THEN 0 ELSE 1 END AS ct_enabled,
       ctd.retention_period, ctd.retention_period_units_desc
FROM sys.databases AS d
LEFT JOIN sys.change_tracking_databases AS ctd ON ctd.database_id = d.database_id
WHERE d.name = DB_NAME();

SELECT COUNT(*) AS ct_tables FROM sys.change_tracking_tables;
SELECT COUNT(*) AS cdc_tables FROM sys.tables WHERE is_tracked_by_cdc = 1;
```

Các truy vấn chỉ chứng minh trạng thái metadata tại thời điểm chạy. Chúng không chứng minh việc bắt mọi INSERT/UPDATE/DELETE, độ phủ temporal history hoặc ý nghĩa nghiệp vụ của các cột.
