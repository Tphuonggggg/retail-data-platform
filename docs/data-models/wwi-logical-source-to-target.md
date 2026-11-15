# WWI Source-to-Target Logical Mapping — DW-01

**DW-01 logical mapping accepted; không DDL/dbt SQL.** [Dictionary đích](wwi-fact-dimension-dictionary.md), [Dictionary nguồn](wwi-metadata-dictionary.md), [Contracts](wwi-source-contracts.md). Logical mapping được nghiệm thu theo targeted review; các physical/SCD2/reference dependency decisions chưa được chốt. Precision đích dưới đây là yêu cầu bảo toàn, chưa là PostgreSQL physical type.

Join aliases: `il` Sales.InvoiceLines; `i` Sales.Invoices; `ol` Sales.OrderLines; `o` Sales.Orders; `m` Warehouse.StockItemTransactions; `h` Warehouse.StockItemHoldings; `c` Sales.Customers; `p` Warehouse.StockItems. `J-I`: il.InvoiceID=i.InvoiceID; `J-O`: ol.OrderID=o.OrderID, cả hai many-to-one. Source columns đã có dictionary trừ reference labels được đánh dấu riêng. Không thêm FK từ InvoiceLine sang OrderLine.

`H`: historical lookup theo NK + accepted episode/basis, B3 whole-day consensus cho date-only hoặc exact-time khi proof đủ; **không** tự dùng 00:00 business date làm business-effective timestamp. `C`: chọn đúng một current dimension version theo run công bố. Giá trị nguồn bắt buộc NULL → DQ; optional NULL giữ nguyên. Lookup unresolved giữ NK và lý do, B4 đã duyệt controlled Core U; I block affected scope. Physical member encoding và lookup algorithm chuyển DW-03; [Final Specification](wwi-final-scd2-design-specification.md) là logical policy hiện hành.

| Target logical field | Source columns / join | Biến đổi | NULL và type/precision | Lookup | Validation evidence / approval |
| --- | --- | --- | --- | --- | --- |
| fact_invoice_line.source_invoice_line_id | il.InvoiceLineID | Copy; unique grain | Required integer | — | PK dictionary; logical accepted, physical pending |
| .source_invoice_id / source_order_id | il.InvoiceID; i.OrderID qua J-I | Copy references | InvoiceID required int; OrderID nullable int, không inner join o | — | R01/R02; logical accepted, physical pending |
| .invoice_date_key | i.InvoiceDate qua J-I | Calendar lookup, giữ source date | Required date; không đổi timezone date | Calendar | BRD-02; logical accepted, physical pending |
| .buyer_customer_key / bill_to_customer_key | i.CustomerID / i.BillToCustomerID qua J-I | Hai lookup riêng vào dim_customer.CustomerID | Required NK int; FK unresolved theo policy | H độc lập từng role | BRD-08, K12; logical accepted, physical pending |
| .product_key | il.StockItemID | Lookup dim_product | Required NK int | H | FK/coverage; logical accepted, physical pending |
| .quantity / unit_price | il.Quantity / il.UnitPrice | Copy, không thay bằng master | Quantity int required; UnitPrice decimal(18,2) nullable, không coalesce 0 | — | Source profile; logical accepted, physical pending |
| .invoiced_sales_before_tax | il.ExtendedPrice, il.TaxAmount | ExtendedPrice−TaxAmount | Cả hai required decimal(18,2); intermediate/result phải đủ precision cho subtraction và SUM, không float/round sớm | — | BRD-03, K02/K10; rule Approved, logical mapping accepted |
| .tax_amount / invoice_amount_including_tax | il.TaxAmount / il.ExtendedPrice | Copy | Required decimal(18,2); SUM đủ precision | — | K02/K03; rule Approved, logical mapping accepted |
| .source_reported_line_profit | il.LineProfit | Copy optional analytical measure | Required decimal(18,2) ở nguồn; optional trong model, không tự coi âm là lỗi | — | BRD-05, K13; logical accepted, physical pending |
| fact_order_line.source_order_line_id / source_order_id | ol.OrderLineID / OrderID | Copy | Required int; unique OrderLineID | — | PK/FK; logical accepted, physical pending |
| .order_date_key / buyer_customer_key | o.OrderDate / CustomerID qua J-O | Calendar; customer lookup | Required date/int; header thiếu → DQ, không âm thầm drop line | H buyer | BRD-01/02/08; logical accepted, physical pending |
| .product_key | ol.StockItemID | Lookup | Required int NK | H | PK/FK; logical accepted, physical pending |
| .ordered_quantity / source_picked_quantity | ol.Quantity / PickedQuantity | Copy | Required int; tổng đủ precision/count | — | Source dictionary; logical accepted, physical pending |
| .source_unit_price | ol.UnitPrice | Copy, chưa tạo order value | Nullable decimal(18,2) | — | Không đổi NULL thành 0; logical accepted, physical pending |
| fact_stock_movement.source_movement_id | m.StockItemTransactionID | Copy | Required int unique | — | PK K07; logical accepted, physical pending |
| .product_key / movement_type_key | m.StockItemID / TransactionTypeID | Lookup product/type | Required integer NK | H product; reference type policy TBD | R03/R05; logical accepted, physical pending |
| .movement_date_key / source_occurred_at | m.TransactionOccurredWhen | Calendar date projection + copy timestamp | Required datetime2(7); bảo toàn 7 fractional digits trước chuyển đổi vật lý; timezone chưa xác định | Calendar | K07/K08; logical accepted, physical pending |
| .signed_quantity | m.Quantity | Copy có dấu, không cast bigint | Required decimal(18,3); SUM đủ precision | — | I01–I05; logical accepted, physical pending |
| .source_invoice_id / source_purchase_order_id | m.InvoiceID / PurchaseOrderID | Copy optional references | Nullable int giữ NULL, RI trên non-NULL | — | R03/R05; logical accepted, physical pending |
| fact_inventory_current.source_stock_item_id / product_key | h.StockItemID | Copy unique grain + current lookup | Required int | C | Holdings PK/FK; logical accepted, physical pending |
| .quantity_on_hand | h.QuantityOnHand | Copy | Required int; sum đủ precision; missing row không là 0 | — | K07; logical accepted, physical pending |
| .observed_at / published_at / published_state_id / batch_id | Raw manifest/target publication | observed_at = observation nguồn; published_at = công bố validated state đích; không WWI columns | Hai thời điểm riêng; timezone/type TBD; published_at chỉ có khi publish thành công | Product SK đã resolve theo state ID, không latest-at-query | Complete snapshot và publication test tương lai; logical requirement accepted, physical Proposed |
| int_order_header.order_id / order_date / buyer_nk | o.OrderID / OrderDate / CustomerID | Copy mọi header; không join line để xác định population | Required int/date/int | H nếu cần attribute; distinct dùng NK | K01/K04/K11, R02; logical accepted, physical pending |
| int_invoice_header.invoice_id / invoice_date / buyer_nk / billto_nk / is_credit_note | i.InvoiceID / InvoiceDate / CustomerID / BillToCustomerID / IsCreditNote | Copy mọi header; aggregate line rồi left join khi tính | Required int/date/int/int/bit; thiếu line cảnh báo, incomplete batch chặn publish | H nếu dùng attributes | K01/K10/K12; logical accepted, physical pending |
| dim_date.date_key / calendar attributes | Ngày calendar do đích sinh từ range hợp lệ | Derive date/year/month/day/quarter; không fiscal assumption | Deterministic key candidate, physical TBD | — | Range/unique/date roundtrip test; logical accepted, physical pending |
| dim_customer.customer_key / source_customer_id | c.CustomerID; archive cùng NK | Đích cấp SK mỗi accepted version, giữ NK | int nguồn → logical identifier; SK physical TBD | DW-02 | NK+version uniqueness/coverage; logical accepted, physical pending |
| .name/category_id/buying_group_id/billto_nk | c.CustomerName/CustomerCategoryID/BuyingGroupID/BillToCustomerID | Copy; billto là source reference, không thay fact billto | nvarchar(100) name; int IDs, BuyingGroupID nullable | Version attribute theo policy | Dictionary, K06; logical accepted, physical pending |
| .credit_limit/account_opened_date/is_on_credit_hold | c.CreditLimit/AccountOpenedDate/IsOnCreditHold | Copy nếu đưa vào dimension đã duyệt | CreditLimit nullable decimal(18,2); date và bit theo dictionary | SCD candidates DW-02 | Customer profile; logical accepted, physical pending |
| dim_product.product_key / source_stock_item_id | p.StockItemID; archive cùng NK | SK mỗi accepted version; giữ NK | Required int NK | DW-02 | Version uniqueness/coverage; logical accepted, physical pending |
| .name/brand/size/color_id | p.StockItemName/Brand/Size/ColorID | Copy, không ép NULL thành label thật | nvarchar(100)/(50)/(20), int nullable theo dictionary | DW-02 | Product profile; logical accepted, physical pending |
| .unit_package_id/outer_package_id/quantity_per_outer/is_chiller_stock | p.UnitPackageID/OuterPackageID/QuantityPerOuter/IsChillerStock | Copy; chưa tạo unit conversion KPI mới | Required int/int/int/bit | DW-02 | Source dictionary; logical accepted, physical pending |
| customer/product source_valid_from/to | c/p.ValidFrom/ValidTo và archive tương ứng | Copy source period riêng với DW validity | datetime2(7); năm 9999 và precision phải bảo toàn; zero-duration đánh dấu | Không mặc định business time | Temporal profiling; logical accepted, physical pending |
| customer/product dw_valid_from/to/is_current/history_basis/lookup_status | Version policy và lineage đích | Technical metadata; chưa gán source period trực tiếp | Physical type/interval/flags ở DW-02 | DW-02 | Interval uniqueness/as-of tests chưa chạy; logical accepted, physical pending |
| dim_movement_type.source_type_id / movement_type_key | m.TransactionTypeID; Application.TransactionTypes.TransactionTypeID | Conform NK, SK đích | int; reference source ngoài 9 bảng | Type history policy TBD | FK verified; ingestion dependency Pending Approval |
| .type_name | Application.TransactionTypes.TransactionTypeName | Copy sau approval contract/ingestion | nvarchar(50), required; metadata SELECT ngày 2026-11-14 | SCD1 candidate, history policy chưa đánh giá | Cột/type/NULL Verified; ingestion dependency Pending Approval |

Evidence Kxx ở [SQL KPI](../../analytics/kpi-definitions/wwi-kpi-verification-sql.md); Rxx ở [SQL quan hệ](wwi-relationship-validation-sql.md). Các mapping chỉ có cột nguồn đã kiểm metadata; reference type_name có kiểm chứng bổ sung dưới đây nhưng chưa đủ contract/approval để ingestion.

### Metadata evidence bổ sung cho reference dependency

SELECT chỉ đọc đã chạy ngày 2026-11-14 trên WWI local, không thay object/schema:

```sql
SELECT c.name, t.name AS type_name, c.max_length, c.is_nullable
FROM sys.columns AS c
JOIN sys.types AS t ON t.user_type_id = c.user_type_id
WHERE c.object_id = OBJECT_ID(N'Application.TransactionTypes')
ORDER BY c.column_id;
```

Kết quả: TransactionTypeID int required; TransactionTypeName nvarchar max_length=100 bytes (=50 ký tự) required; LastEditedBy int required; ValidFrom/ValidTo datetime2 required. Có period columns là bằng chứng metadata, chưa quyết định SCD/history source contract cho reference table. Không đưa bảng này vào ingestion scope chỉ từ truy vấn này.

## Precision và validation trước physical design

Đã đối chiếu tài liệu engine ngày 2026-11-14: [SQL Server datetime2](https://learn.microsoft.com/en-us/sql/t-sql/data-types/datetime2-transact-sql?view=sql-server-ver17) hỗ trợ 0–7 fractional digits, precision 100 ns và không chứa timezone offset; [PostgreSQL datetime](https://www.postgresql.org/docs/18/datatype-datetime.html) hỗ trợ timestamp precision 0–6, resolution 1 microsecond. Do đó timestamp đơn thuần không bảo toàn mọi giá trị datetime2(7). Ví dụ giả định `.1234561` và `.1234562` khác nhau ở nguồn có thể trở thành cùng microsecond ở đích, làm mất ordering hoặc co interval. Sentinel `9999-12-31 23:59:59.9999999` cần test conversion riêng, không mặc định cast lossless. Tài liệu PostgreSQL 18 chỉ dùng xác minh capability, không phê duyệt/chuyển version stack dự án.

DW-03A phải so sánh phương án lưu source representation đủ 7 digits/ticks cùng timestamp phục vụ query, hoặc conversion policy có ghi residual/precision loss; **chưa chọn phương án hay physical type**. DW-02 cần bảo đảm interval lookup được đánh giá trên representation đã duyệt, không dùng timestamp bị giảm precision để tự chốt version. Tests cần cover chữ số thứ bảy, interval sát nhau, ties, sentinel, timezone và round-trip. Không tự gán UTC từ datetime2 thiếu offset.

[PostgreSQL numeric](https://www.postgresql.org/docs/18/datatype-numeric.html) là exact numeric; khai báo scale có thể làm tròn input vượt scale. Yêu cầu logic: giữ movement decimal(18,3), monetary columns decimal(18,2), giữ dấu/NULL; subtraction/SUM có capacity đủ và ratio không integer division. Không cast quantity sang bigint hoặc float, không round line trước khi SUM. Chỉ format AIV ở presentation theo policy; rounding mode, tie cases, overflow/aggregate precision và physical numeric(p,s) phải được DW-03A quyết định/kiểm thử. NULL UnitPrice không tự thành 0. Đây là đối chiếu tài liệu, chưa test conversion trên PostgreSQL.

## Reference dependency proposal — chưa triển khai

Ngoài chín source contracts: Application.TransactionTypes phục vụ dim_movement_type; Sales.CustomerCategories/BuyingGroups, Warehouse.Colors/PackageTypes chỉ khi cần labels; Purchasing.PurchaseOrders/PurchaseOrderLines cho đối soát receipt. Không tự thêm source ingestion từ metadata đã đọc.

Với TransactionTypes, đề xuất ưu tiên **contract extension có kiểm soát**: projection tối thiểu TransactionTypeID/TransactionTypeName, metadata period khi cần; xác minh PK/unique/NULL, current/history scope, change semantics, accepted types, lineage và quyền đọc trước approval. Phương án khác là **controlled mapping có version** cho ID 10/11/12 dựa evidence hiện có, kèm source provenance và unknown-type review gate; không hardcode như bảng nguồn đầy đủ, không invent labels cho ID mới. Hai phương án đều Pending Approval, chưa chọn hoặc triển khai. Labels reference khác chỉ được map sau evidence/contract tương ứng.

Source movement Quantity là decimal(18,3): K07/K08 cũ dùng bigint phù hợp giá trị nguyên quan sát, nhưng không là quy tắc conversion warehouse; phải bổ sung kiểm chứng fractional quantity khi triển khai. SQL Server datetime2(7) có precision khác timestamp đích có thể hỗ trợ; DW-03A cần chọn representation bảo toàn ordering/period và kiểm tie ở conversion. Monetary aggregation phải dùng decimal đủ lớn, chỉ format/round AIV ở presentation; currency identity chưa có source currency column được kiểm chứng nên không tự đặt BRL từ dataset trước.

Validation cần: mỗi source PK có đúng một fact; mỗi FK lookup ≤1 version; source−raw−fact sums/count cùng complete run; full outer grouped reconciliation, báo header-only và missing lines riêng; metadata gắn đúng batch; dimension fallback không làm thay amount/count. Không chọn thresholds/checkpoint/isolation ở DW-01.
