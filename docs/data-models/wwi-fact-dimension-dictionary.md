# WWI Fact & Dimension Dictionary — DW-01

**DW-01 logical design accepted.** Bốn grain và logical contracts được nghiệm thu; SCD attributes, lookup/fallback policy và physical types vẫn là candidates cho các task sau. [Đặc tả tổng](wwi-logical-dw-design.md), [mapping](wwi-logical-source-to-target.md), [source dictionary](wwi-metadata-dictionary.md) là các tham chiếu. Runtime: Not implemented yet.

**Cập nhật SCD direction sau DW-01, không đổi fact grain/Bus Matrix:** [ADR-SCD-01–06](../adr/README.md) nay được Owner duyệt. Product Type2 chỉ UnitPackageID/OuterPackageID/QuantityPerOuter; các analytical fields khác chỉ Type1 nếu admitted, excluded/audit không tự đổi class. Persistent registry, whole-day analytical consensus, reconciled hybrid cutover, exact 100 ns và controlled unresolved core/certified gates là accepted directions. Các mục SCD candidates của snapshot DW-01 dưới đây phải đọc cùng [classification hiện hành](wwi-scd-attribute-classification.md); physical/technical procedures vẫn pending.

## Quy ước fact

**Lookup invariant được nghiệm thu:** mỗi fact row, cho từng dimension role, có 0 hoặc 1 matching real version trong bước resolve; >1 là ambiguity phải chặn publication/tái xử lý, không DISTINCT hoặc chọn MAX để che fan-out. Không JOIN fact với tất cả SCD2 versions chỉ bằng natural key. Published FK phải trỏ một SK đã resolve hoặc member theo policy DW-02 được duyệt. Với 0 match, giữ source NK/lookup_status và payload; unknown/inferred/pending publication, historical fallback và business-effective time vẫn do DW-02 quyết định. Diagrams mô tả quan hệ FK của trạng thái đã resolve/publish, không chứng minh source historical coverage.

Logical uniqueness = source system + source PK; không bắt buộc fact surrogate riêng ở bước này. Mọi row có source PK, lineage batch/run, observation/extraction time và source change information theo raw contract; đây là metadata do hệ thống đích tạo, không phải cột WWI. Dimension FK phải resolve tối đa một version và trace được natural key; missing lookup giữ payload để tái xử lý, không inner join làm mất fact. Unknown/inferred policy chờ DW-02; không công bố bằng chứng lịch sử giả. Measures được lấy đúng nguồn, không thay bằng current product price/cost.

| Fact | Grain / source key | Logical foreign keys / references | Measures và additive | Date basis |
| --- | --- | --- | --- | --- |
| fact_invoice_line | 1 InvoiceLineID; Sales.InvoiceLines | invoice_date_key → dim_date; buyer_customer_key và bill_to_customer_key → dim_customer; product_key → dim_product; InvoiceID và nullable OrderID là degenerate references | quantity SUM; unit_price không additive; invoiced_sales_before_tax = ExtendedPrice−TaxAmount SUM; tax_amount = TaxAmount SUM; invoice_amount_including_tax = ExtendedPrice SUM; source_reported_line_profit = LineProfit SUM optional | Invoices.InvoiceDate; delivery timestamp nếu giữ chỉ evidence |
| fact_order_line | 1 OrderLineID; Sales.OrderLines | order_date_key; buyer_customer_key; product_key; OrderID reference | ordered_quantity = Quantity SUM; source_unit_price nullable, không additive; source_picked_quantity = PickedQuantity SUM phục vụ đối soát, không KPI mới | Orders.OrderDate |
| fact_stock_movement | 1 StockItemTransactionID; Warehouse.StockItemTransactions | movement_date_key; product_key; movement_type_key; nullable source InvoiceID/PurchaseOrderID chỉ references, không FK sang fact | signed_quantity = Quantity SUM theo type; issue = −SUM(Quantity) type 10; receipt = SUM type 11; signed adjustment = SUM type 12; movement count = count PK | Ngày từ TransactionOccurredWhen; giữ timestamp gốc |
| fact_inventory_current | 1 StockItemID trong current published state; Warehouse.StockItemHoldings | product_key → current version; source_stock_item_id unique; không date FK | quantity_on_hand = QuantityOnHand; cộng item tại cùng published state, không additive theo thời gian | observed_at/extraction window; không là business inventory day |

Quantity cộng giữa product là tổng source units theo catalog; phân tích unit/package phải giữ giới hạn, không tự đổi outer thành unit trên mọi fact. Numeric không dùng float, giữ phần lẻ movement `decimal(18,3)`. Header count không là additive line measure. Không cộng UnitPrice hoặc averaging average invoice values.

## fact_invoice_line

Header join bắt buộc `InvoiceLines.InvoiceID = Invoices.InvoiceID`, many-to-one; buyer/bill-to lấy **trên invoice**, không tính lại từ Customers hiện hành. Product từ line StockItemID. Header-only date/role update phải cập nhật tất cả affected lines dù line LastEditedWhen không đổi. Product/customer history correction có thể cần rekey/restatement sau DW-02.

Full build giữ toàn bộ invoice lines cùng source snapshot/validated run, resolve dimensions và reconcile count/PK/amount trước công bố. Rebuild không nhân duplicate theo InvoiceLineID. Đối soát K02/K03/K10/K12/K13: tổng ba amount, LineProfit và distinct InvoiceID; Invoice Count/S06 dùng header population đầy đủ. 84 NULL delivery không làm mất invoice. IsCreditNote mới xuất hiện là scenario cần review policy, không tự thêm refund logic.

Rủi ro: join với OrderLines, payments hay movements gây fan-out; nullable Invoices.OrderID không cho phép inner join Orders để lọc invoice. Snapshot max một invoice/order không là constraint. Không có OrderLineID mapping trực tiếp. Nhãn Recognized Revenue/Gross Profit/COGS ngoài model MVP.

## fact_order_line

Join `OrderLines.OrderID = Orders.OrderID`; buyer và order date trên header. Không sinh line giả cho order không line, không thay orders bằng tập invoiced orders. S01/C01/C02 đi qua intermediate order header mô tả trong [đặc tả](wwi-logical-dw-design.md). UnitPrice nullable giữ NULL, không tự lấy StockItems.UnitPrice hoặc thay bằng 0. Chưa tạo order amount/AOV từ Quantity×UnitPrice.

Full build giữ mọi source line, kể cả thuộc 3.085 order chưa invoice tại baseline. Reconcile 231.412 baseline line IDs theo cùng run; header count riêng 73.595 là historical evidence, không ngưỡng cố định. Incremental re-evaluate line insert/update và header-only date/customer change; khi line chuyển OrderID/product phải restate cả nhóm cũ và mới. Không join invoice lines để tính ordered quantity.

## fact_stock_movement

Signed quantity không lấy ABS đại trà. Quantity=0 ở type 12 giữ lại; dòng âm không mặc định lỗi. InvoiceID và PurchaseOrderID NULL hợp lệ theo type; không tạo dimension PO hay core purchasing fact. Full build giữ 1 row/movement với decimal precision nguồn, kiểm count/signed sum theo type; baseline K07 236.667 movements chỉ evidence.

Đối soát issues và invoice lines **tổng hợp riêng** ở `(InvoiceID, StockItemID)`, không ghép từng line; receipts với PO lines ở `(PurchaseOrderID, StockItemID)` và conversion có bằng chứng khi dependency được duyệt. Không cam kết 1:1 từ pair match của snapshot. Incremental update date/type/product/quantity/document link phải restate các group cũ/mới; product version change cần lookup/rekey policy. Không suy holdings hoặc daily closing balance từ movement.

## fact_inventory_current

`observed_at` là thời điểm extractor ghi nhận observation holdings, kèm extraction_start/end để mô tả window; `published_at` là thời điểm hệ thống đích công bố validated state cho consumer. Đây là hai metadata khác nhau, không thay bằng source LastEditedWhen, không suy observed_at là snapshot nguyên tử. `published_state_id` liên kết holdings và tập Product version/SK được resolve trong cùng publication; không join động sang dimension có is_current mới nhất ở thời điểm query. Nếu Product current pointer đổi, republish/rekey nhất quán theo policy DW-03C, không âm thầm đổi version của state đã công bố. Physical publication transaction/retention chưa được chọn.

Full build/replacement chỉ công bố khi snapshot holdings đầy đủ/validated; current target một StockItemID duy nhất. Quan hệ dim_product là current version, một real resolved version có tối đa một current fact cho item trong state này; candidate unknown chung có thể được nhiều source NK dùng nên không đặt uniqueness trên product_key khi chưa chốt policy. Product master có thể chưa có holding. Observation metadata gồm observed_at, extraction_start/end, batch_id/run_id và published_state_id (đều technical proposed), không mặc định atomic source snapshot.

Snapshot comparison phát hiện inserted/changed/missing keys; key vắng trong partial/failed batch không được xem là delete/zero stock. Sau dimension current pointer thay đổi cần rekey current fact nếu được duyệt. Reconcile PK count và SUM QuantityOnHand cùng snapshot; baseline 227 rows/30.343.296 units. Không cộng nhiều published states hoặc dùng LastEditedWhen làm ngày tồn kho. Snapshot retention ở raw không tự biến Core Fact thành lịch sử ngày.

## Dimensions và version identity

| Dimension | Natural / surrogate key | Attributes đề xuất và nguồn | SCD candidates / role | Giới hạn historical lookup |
| --- | --- | --- | --- | --- |
| dim_date | calendar date / date_key; format allocation TBD | full_date, calendar_year/month/day, month_start, quarter do đích tính từ calendar | SCD0 calendar, sửa lỗi calendar theo policy riêng; invoice/order/movement date role | date-only không cung cấp giờ để chọn temporal version; range bao phủ dữ liệu và late dates cần duyệt |
| dim_customer | source_system + Customers.CustomerID / customer_key mỗi version | CustomerName, CustomerCategoryID, BuyingGroupID nullable, BillToCustomerID natural reference, CreditLimit nullable, AccountOpenedDate, IsOnCreditHold; chỉ chọn thuộc tính phục vụ customer analytics, không đưa contact/address nhạy cảm mặc định | NK stable SCD0; name correction SCD1 candidate; category/group/bill-to/credit/hold SCD2 candidates; buyer và bill-to role | Chỉ CreditLimit quan sát thay đổi trong history; period là system-time, không business effective. Không suy category lịch sử từ current |
| dim_product | source_system + StockItems.StockItemID / product_key mỗi version | StockItemName, Brand nullable, Size nullable, ColorID nullable, UnitPackageID, OuterPackageID, QuantityPerOuter, IsChillerStock; Tags excluded theo ADR-SCD-01 | NK SCD0 candidate; Type2 chỉ UnitPackageID/OuterPackageID/QuantityPerOuter; analytical fields khác Type1 nếu admitted, correction scope pending; current role cho holdings | History chỉ CustomFields/Tags đổi trong snapshot, không price/cost history; không lấy current UnitPrice làm giá giao dịch |
| dim_movement_type | TransactionTypes.TransactionTypeID / movement_type_key | TransactionTypeID; TransactionTypeName nvarchar(50) required, metadata bổ sung trong mapping | SCD0 ID; tên mô tả SCD1 candidate, phân nhóm 10/11/12 có evidence; history policy chưa đánh giá | Reference table dependency chưa được phép ingestion; có ValidFrom/ValidTo nhưng chưa đánh giá history coverage/lookup |

Source types/NULL chi tiết theo dictionary. Customer/product version metadata proposed: source_valid_from/to, dw_valid_from/to, is_current, history_basis, lookup_status và lineage. Không sao chép source period thành dw business validity trước DW-02. Forward-tracked SCD2 chỉ xác nhận từ lúc quan sát có kiểm chứng, không tạo lịch sử trước đó. Customer direction theo SCD-01 và Product set theo ADR-SCD-01 đã được ghi nhận ở classification; validity/lookup và correction procedures chưa được chốt.

## Unknown, late dimensions và temporal evidence

| Dimension | Unknown/lookup candidate | Source dependency và giới hạn |
| --- | --- | --- |
| dim_date | Ngày required sai/ngoài range: pending hoặc unknown có lý do; không dùng ngày extract thay business date | Calendar đích; timezone của movement date và date-range mở rộng chờ DW-03A |
| dim_customer | Unknown chung/inferred theo NK/pending là ba phương án chưa chốt cho cả buyer và bill-to | Customers current+archive; category/group labels ngoài chín bảng cần approval; lịch sử trước observation không được suy |
| dim_product | Giữ NK và lookup status nếu không có đúng một version; current fact cần current version duy nhất | StockItems current+archive; color/package labels ngoài chín bảng; historical price/cost không được chứng minh |
| dim_movement_type | Unknown type chưa có reference phải báo accepted-value exception, không gán mặc định issue/receipt | TransactionTypes cần contract/approval; system-time/history chưa đánh giá, không invent label cho type mới |

Candidates để DW-02 chọn: (a) unknown member chung + giữ source NK và lý do; (b) inferred member riêng theo NK rồi hoàn thiện; (c) giữ fact pending publication nếu không đảm bảo lookup. Phân biệt missing source parent, late extraction, lịch sử không phủ và not-applicable; không dùng một mã NULL cho tất cả. SK convention chưa chốt. Tối đa một match cho mỗi role; nhiều match là lỗi ambiguity, không chọn MAX version tùy ý. SCD1 và SCD2 có thể làm thay đổi cách nhóm historical measures khác nhau, cần restatement contract.

Customer: current+archive 714 rows, 1 zero-duration, 0 overlap/gap giữa các version quan sát; `FOR SYSTEM_TIME ALL` chỉ 713. Product: 671 rows, 0 zero-duration, 0 overlap/gap; chỉ 444 transitions CustomFields/Tags. Đây không chứng minh coverage trước version đầu hoặc business effective time. Zero-duration không có interval dương để lookup; giữ raw evidence, không tự kéo dài/loại bỏ archive. Date-only 00:00 từng match customer ở profiling chỉ là proxy; bill-to role/as-of và product invoice-date lookup cần kiểm riêng. Giao dịch ngoài coverage cần fallback được duyệt, không backdate version đầu.

## Dependencies ngoài chín bảng MVP — Pending Approval

TransactionTypes cần thiết để materialize dim_movement_type có tên; metadata/profiling đã đọc nhưng chưa có ingestion contract. CustomerCategories/BuyingGroups để thêm labels cho C05/group; Colors/PackageTypes để giải thích color/package IDs; Purchasing.Suppliers nếu bổ sung supplier labels. PurchaseOrders/PurchaseOrderLines chỉ đối soát receipt, không tự ingestion subject area. Trước khi nạp cần projection, NULL/type/PK/history/change contract và approval; trong DW-01 chỉ dùng các ID đã có trong chín bảng hoặc labels từ evidence có ghi nguồn, không mặc định các bảng reference đã nạp.
