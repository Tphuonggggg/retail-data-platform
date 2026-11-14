# WWI SCD Attribute Classification Matrix — DW-02A

**DW-02A/B được nghiệm thu ở mức khảo sát/phân loại; SCD-01–07 là Approved Principles.** Các technical policies và Product Type 2 columns cụ thể vẫn Pending Approval. Bao phủ 31 Customer columns và 25 Product columns theo [Metadata Dictionary](wwi-metadata-dictionary.md). Không thay đổi [DW-01](wwi-logical-dw-design.md), bốn fact grains hay [BRD-01–12](../requirements/wwi-business-rules-decision-matrix.md). Runtime: Not implemented yet.

`Type 0 candidate` là đề xuất contract bất biến có policy correction cần duyệt; không khẳng định cột bất biến từ 0 observed change. `Type 1 candidate` thay label hiện hành, có thể đổi cách hiển thị historical facts. `Type 2 candidate` chỉ phục vụ historical analytical meaning đã nêu, không mặc định được đưa vào tracking set. Conditional/optional có thể dùng current-only Type 1 hoặc loại bỏ nếu Owner không cần historical grouping. Excluded khỏi analytical dimension không có nghĩa xóa raw payload.

Observed change dùng lại profiling đã Verified 2026-11-07: Q06 kiểm 28 Customer thuộc tính ngoài NK/period; Q08 kiểm 22 Product thuộc tính ngoài NK/period, null-safe; geography so STAsBinary. Không chạy lại attribute comparisons trong DW-02A/B; temporal counts/identity/lookup được tái kiểm riêng ngày 2026-11-14. 0 là không quan sát transition trong snapshot, không phải không thể thay đổi. NK uniqueness current không chứng minh natural key không bao giờ bị reuse.

## Approved Principles — Project Owner approval

| ID | Quyết định được duyệt | Technical policy còn mở |
| --- | --- | --- |
| SCD-01 | Customer Type 2 direction: CustomerCategoryID, BuyingGroupID, BillToCustomerID. CustomerID là NK. CreditLimit/IsOnCreditHold optional, chưa kích hoạt MVP | CustomerName Type1 candidate; AccountOpenedDate Type0 candidate/correction policy; version validity và algorithm chưa duyệt |
| SCD-02 | Product Type2 chỉ cho grouping/packaging có analytical requirement; StockItemName Type1 candidate. Không thay transaction price; CustomFields/Tags ngoài analytical scope | Danh sách cụ thể bên dưới là recommendation, chưa approved tracking set |
| SCD-03 | Hybrid: dùng temporal history đủ evidence và forward tracking sau pipeline hoạt động | Cutover/coverage/validity chưa chốt; system-time không mặc định business-effective |
| SCD-04 | Giữ zero-duration trong Raw/audit; không là interval dương | Mapping source identity sang DW version còn mở |
| SCD-05 | Không fallback current/earliest khi thiếu evidence; unresolved phải rõ | Unknown/inferred/pending publication policy chưa chọn |
| SCD-06 | Bảo toàn source temporal identity/precision; chưa chọn đầu/cuối ngày | Representation/SK/lookup policy chờ duyệt |
| SCD-07 | Phải đánh giá fact/role/mart propagation và restatement | Không blanket restate; phạm vi/approval/remapping chưa chọn |

## Customer — Sales.Customers và Sales.Customers_Archive

| Attribute | Source Column | Business Meaning | Observed Changes | Recommended SCD Type | Reason | KPI Impact | Evidence | Approval Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CustomerID | Customers.CustomerID; archive cùng cột | Khóa customer | Không so transition NK; current unique | Business/natural key; Type 0 candidate | Giữ định danh xuyên versions; bất biến là contract đề xuất, không suy từ snapshot | S01/C01/C02 distinct theo NK, hai invoice roles | Dictionary + C01/C02 hoặc P01/P02 | Approved NK — SCD-01; immutability/correction policy pending |
| CustomerName | Customers.CustomerName; archive cùng cột | Tên hiển thị | 0 / 0 NK | Type 1 candidate | Sửa tên hiển thị; nếu đổi mang nghĩa phân loại cần review trước overwrite | Đổi label; không đổi amounts/counts | Q06; Customer temporal profiling | Pending Approval |
| BillToCustomerID | Customers.BillToCustomerID; archive cùng cột | Liên kết bill-to của master | 0 / 0 NK | Type 2 tracking direction approved; technical policy pending | Lịch sử affiliation có ích phân tích customer profile; không thay role ghi trên invoice | C03/C04 giữ Invoices roles, không tự reattribute | Q06; Customer temporal profiling | Approved direction — SCD-01 |
| CustomerCategoryID | Customers.CustomerCategoryID; archive cùng cột | Phân nhóm customer | 0 / 0 NK | Type 2 tracking direction approved; technical policy pending | Chỉ khi Owner cần segmentation lịch sử; C05 hiện tại không tự đòi SCD2 | C05 dùng current; historical grouping C03 chỉ sau approval; ref R1 | Q06; Customer temporal profiling | Approved direction — SCD-01 |
| BuyingGroupID | Customers.BuyingGroupID; archive cùng cột | Nhóm mua hàng | 0 / 0 NK | Type 2 tracking direction approved; technical policy pending | Historical customer grouping nếu được duyệt; không phải requirement KPI mới | C03 grouping optional, R2 | Q06; Customer temporal profiling | Approved direction — SCD-01 |
| PrimaryContactPersonID | Customers.PrimaryContactPersonID; archive cùng cột | Người liên hệ | 0 / 0 NK | Excluded | Không cần KPI MVP; tránh mở People contract/PII | Không tác động KPI; R3 nếu mở lại | Q06; Customer temporal profiling | Pending Approval |
| AlternateContactPersonID | Customers.AlternateContactPersonID; archive cùng cột | Người liên hệ phụ | 0 / 0 NK | Excluded | Không cần KPI MVP/PII | Không; R3 | Q06; Customer temporal profiling | Pending Approval |
| DeliveryMethodID | Customers.DeliveryMethodID; archive cùng cột | Phương thức giao | 0 / 0 NK | Excluded | Không có shipping KPI; cần contract thêm nếu dùng | Không; R4 | Q06; Customer temporal profiling | Pending Approval |
| DeliveryCityID | Customers.DeliveryCityID; archive cùng cột | Thành phố giao | 0 / 0 NK | Excluded | Geo analytics chưa có requirement; giữ raw theo contract | Không; R5 | Q06; Customer temporal profiling | Pending Approval |
| PostalCityID | Customers.PostalCityID; archive cùng cột | Thành phố thư tín | 0 / 0 NK | Excluded | Không có KPI và lịch sử geo chưa xác minh | Không; R5 | Q06; Customer temporal profiling | Pending Approval |
| CreditLimit | Customers.CreditLimit; archive cùng cột | Hạn mức tín dụng customer | 51 transitions / 46 NK | Optional Type 2 candidate; chưa kích hoạt MVP | BR-C đã nêu câu hỏi thay đổi CreditLimit; có observed history; không tạo Finance KPI | Optional customer-profile history, không revenue/COGS | Q06; Customer temporal profiling | Approved optional status — SCD-01; activation pending |
| AccountOpenedDate | Customers.AccountOpenedDate; archive cùng cột | Ngày mở tài khoản | 0 / 0 NK | Type 0 candidate | Ngày gốc có ý nghĩa ổn định; correction cần policy, không coi 0 change là bằng chứng bất biến | Không tự thêm tenure KPI | Q06; Customer temporal profiling | Pending Approval |
| StandardDiscountPercentage | Customers.StandardDiscountPercentage; archive cùng cột | Mức discount master | 0 / 0 NK | Excluded | Không dùng để tính lại invoice amount lịch sử | S05 giữ line amounts | Q06; Customer temporal profiling | Pending Approval |
| IsStatementSent | Customers.IsStatementSent; archive cùng cột | Cờ gửi statement | 0 / 0 NK | Excluded | Billing operation ngoài KPI MVP | Không | Q06; Customer temporal profiling | Pending Approval |
| IsOnCreditHold | Customers.IsOnCreditHold; archive cùng cột | Trạng thái credit hold | 0 / 0 NK | Optional Type 2 candidate; chưa kích hoạt MVP | Profile trạng thái theo thời gian nếu được Owner duyệt; không tự lọc giao dịch theo cờ current | Historical customer segmentation optional | Q06; Customer temporal profiling | Approved optional status — SCD-01; activation pending |
| PaymentDays | Customers.PaymentDays; archive cùng cột | Điều khoản thanh toán | 0 / 0 NK | Excluded | Finance extension; không có payment allocation KPI | Không | Q06; Customer temporal profiling | Pending Approval |
| PhoneNumber | Customers.PhoneNumber; archive cùng cột | Điện thoại | 0 / 0 NK | Excluded | PII/contact không cần dimension phân tích | Không | Q06; Customer temporal profiling | Pending Approval |
| FaxNumber | Customers.FaxNumber; archive cùng cột | Fax | 0 / 0 NK | Excluded | Contact không có requirement | Không | Q06; Customer temporal profiling | Pending Approval |
| DeliveryRun | Customers.DeliveryRun; archive cùng cột | Tuyến giao | 0 / 0 NK | Excluded | Không có logistics dimension/KPI | Không | Q06; Customer temporal profiling | Pending Approval |
| RunPosition | Customers.RunPosition; archive cùng cột | Vị trí tuyến | 0 / 0 NK | Excluded | Không có logistics requirement | Không | Q06; Customer temporal profiling | Pending Approval |
| WebsiteURL | Customers.WebsiteURL; archive cùng cột | Website | 0 / 0 NK | Excluded | Không phục vụ KPI MVP | Không | Q06; Customer temporal profiling | Pending Approval |
| DeliveryAddressLine1 | Customers.DeliveryAddressLine1; archive cùng cột | Địa chỉ giao dòng 1 | 0 / 0 NK | Excluded | PII/chi tiết không cần dimension | Không | Q06; Customer temporal profiling | Pending Approval |
| DeliveryAddressLine2 | Customers.DeliveryAddressLine2; archive cùng cột | Địa chỉ giao dòng 2 | 0 / 0 NK | Excluded | PII/chi tiết không cần dimension | Không | Q06; Customer temporal profiling | Pending Approval |
| DeliveryPostalCode | Customers.DeliveryPostalCode; archive cùng cột | Mã bưu chính giao | 0 / 0 NK | Excluded | Không có geo KPI | Không | Q06; Customer temporal profiling | Pending Approval |
| DeliveryLocation | Customers.DeliveryLocation; archive cùng cột | Tọa độ giao | 0 / 0 NK | Excluded | Geo không thuộc requirement, payload geography | Không | Q06; Customer temporal profiling | Pending Approval |
| PostalAddressLine1 | Customers.PostalAddressLine1; archive cùng cột | Địa chỉ thư tín dòng 1 | 0 / 0 NK | Excluded | PII không cần analytics | Không | Q06; Customer temporal profiling | Pending Approval |
| PostalAddressLine2 | Customers.PostalAddressLine2; archive cùng cột | Địa chỉ thư tín dòng 2 | 0 / 0 NK | Excluded | PII không cần analytics | Không | Q06; Customer temporal profiling | Pending Approval |
| PostalPostalCode | Customers.PostalPostalCode; archive cùng cột | Mã bưu chính thư tín | 0 / 0 NK | Excluded | Không có geo KPI | Không | Q06; Customer temporal profiling | Pending Approval |
| LastEditedBy | Customers.LastEditedBy; archive cùng cột | Người sửa nguồn | 50 / 46 NK | Technical/audit metadata | Giữ lineage khi cần; không là business SCD2 trigger | Không version dimension chỉ vì editor đổi | Q06; Customer temporal profiling | Approved audit principle — SCD-01/04/06; implementation pending |
| ValidFrom | Customers.ValidFrom; archive cùng cột | System period start | Period distribution, không attribute transition count | Technical/audit metadata | Bảo toàn source identity riêng với DW validity | Không dùng trực tiếp làm business effective | C01/C02 hoặc P01/P02 trong SQL evidence | Approved audit principle — SCD-01/04/06; implementation pending |
| ValidTo | Customers.ValidTo; archive cùng cột | System period end | Period distribution, không attribute transition count | Technical/audit metadata | Bảo toàn source precision và zero-duration | Lookup policy chưa chọn | C01/C02 hoặc P01/P02 trong SQL evidence | Approved audit principle — SCD-01/04/06; implementation pending |

## Product — Warehouse.StockItems và StockItems_Archive

| Attribute | Source Column | Business Meaning | Observed Changes | Recommended SCD Type | Reason | KPI Impact | Evidence | Approval Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| StockItemID | StockItems.StockItemID; archive cùng cột | Khóa product | Không so transition NK; current unique | Business/natural key; Type 0 candidate | Giữ định danh xuyên versions | Distinct item theo NK | Dictionary + C01/C02 hoặc P01/P02 | Pending Approval |
| StockItemName | StockItems.StockItemName; archive cùng cột | Tên sản phẩm | 0 / 0 NK | Type 1 candidate | Tên hiển thị/sửa lỗi; semantic reclassification phải review trước | Đổi label; amounts/qty không đổi | Q08; Inventory temporal profiling | Pending Approval |
| SupplierID | StockItems.SupplierID; archive cùng cột | Nhà cung cấp | 0 / 0 NK | Excluded | Supplier analytics/Purchasing ngoài MVP | Không; R6 nếu mở lại | Q08; Inventory temporal profiling | Pending Approval |
| ColorID | StockItems.ColorID; archive cùng cột | Màu sản phẩm | 0 / 0 NK | Type 2 candidate — conditional | Historical product grouping nếu cần; không suy từ current | Product grouping S03–S05/I01–I05; R7 | Q08; Inventory temporal profiling | Pending Approval |
| UnitPackageID | StockItems.UnitPackageID; archive cùng cột | Quy cách unit | 0 / 0 NK | Type 2 candidate | Lịch sử packaging có ý nghĩa diễn giải quantity theo thời gian; không đổi source measure | Quantity interpretation; R8 | Q08; Inventory temporal profiling | Pending Approval |
| OuterPackageID | StockItems.OuterPackageID; archive cùng cột | Quy cách outer | 0 / 0 NK | Type 2 candidate | Packaging history; không tự quy đổi mọi fact sang outer | Receipt reconciliation dependency; R8 | Q08; Inventory temporal profiling | Pending Approval |
| Brand | StockItems.Brand; archive cùng cột | Thương hiệu | 0 / 0 NK | Type 2 candidate — conditional | Historical product grouping nếu Owner duyệt | Product mart grouping; nullable, không invent Unknown brand thật | Q08; Inventory temporal profiling | Pending Approval |
| Size | StockItems.Size; archive cùng cột | Kích cỡ | 0 / 0 NK | Type 2 candidate — conditional | Giữ historical product grouping nếu có semantic change | Product mart grouping; không đổi measures | Q08; Inventory temporal profiling | Pending Approval |
| LeadTimeDays | StockItems.LeadTimeDays; archive cùng cột | Lead time nguồn | 0 / 0 NK | Excluded | Stockout/Purchasing không thuộc MVP | Không tạo I07 | Q08; Inventory temporal profiling | Pending Approval |
| QuantityPerOuter | StockItems.QuantityPerOuter; archive cùng cột | Unit mỗi outer | 0 / 0 NK | Type 2 candidate | Packaging conversion context lịch sử, chưa tự áp cost/demand rule | Receipt grouped reconciliation; source unit quantity giữ nguyên | Q08; Inventory temporal profiling | Pending Approval |
| IsChillerStock | StockItems.IsChillerStock; archive cùng cột | Cờ hàng lạnh | 0 / 0 NK | Type 2 candidate — conditional | Historical product segmentation nếu cần | Grouping product/current inventory theo mode duyệt | Q08; Inventory temporal profiling | Pending Approval |
| Barcode | StockItems.Barcode; archive cùng cột | Mã barcode | 0 / 0 NK | Excluded | Không có requirement barcode analytics; không thay StockItemID làm NK | Không | Q08; Inventory temporal profiling | Pending Approval |
| TaxRate | StockItems.TaxRate; archive cùng cột | Thuế suất master | 0 / 0 NK | Excluded | Invoice TaxAmount là nguồn KPI; không recompute theo current master | S04 giữ InvoiceLines.TaxAmount | Q08; Inventory temporal profiling | Pending Approval |
| UnitPrice | StockItems.UnitPrice; archive cùng cột | Giá bán master | 0 / 0 NK | Excluded | Không thay transaction UnitPrice hoặc tái dựng historical price | Không thay S03–S06 | Q08; Inventory temporal profiling | Approved no-price-substitution — SCD-02; field policy pending |
| RecommendedRetailPrice | StockItems.RecommendedRetailPrice; archive cùng cột | Giá đề xuất | 0 / 0 NK | Excluded | Không có KPI pricing/master price | Không | Q08; Inventory temporal profiling | Pending Approval |
| TypicalWeightPerUnit | StockItems.TypicalWeightPerUnit; archive cùng cột | Khối lượng unit | 0 / 0 NK | Excluded | Không có weight/logistics KPI | Không | Q08; Inventory temporal profiling | Pending Approval |
| MarketingComments | StockItems.MarketingComments; archive cùng cột | Nội dung marketing | 0 / 0 NK | Excluded | Text không cần dimension KPI | Không | Q08; Inventory temporal profiling | Pending Approval |
| InternalComments | StockItems.InternalComments; archive cùng cột | Ghi chú nội bộ | 0 / 0 NK | Excluded | Không cần analytical attributes | Không | Q08; Inventory temporal profiling | Pending Approval |
| Photo | StockItems.Photo; archive cùng cột | Ảnh sản phẩm | 0 / 0 NK | Excluded | Binary lớn, không có analytical requirement | Không | Q08; Inventory temporal profiling | Pending Approval |
| CustomFields | StockItems.CustomFields; archive cùng cột | JSON/custom payload | 444 transitions / 227 NK | Excluded | Có changes nhưng chưa có approved analytical subfield; không version toàn JSON | Không biến mọi source version thành SCD2 | Q08; Inventory temporal profiling | Approved scope exclusion — SCD-02 |
| Tags | StockItems.Tags; archive cùng cột | Tags computed | 444 transitions / 227 NK | Excluded | Có changes nhưng phụ thuộc CustomFields; chưa có requirement chính thức | Không tạo hai triggers trùng nghĩa | Q08; Inventory temporal profiling | Approved scope exclusion — SCD-02 |
| SearchDetails | StockItems.SearchDetails; archive cùng cột | Search computed | 0 / 0 NK | Excluded | Phục vụ search nguồn; không KPI | Không | Q08; Inventory temporal profiling | Pending Approval |
| LastEditedBy | StockItems.LastEditedBy; archive cùng cột | Người sửa nguồn | 0 / 0 NK | Technical/audit metadata | Không business SCD2 trigger | Audit only | Q08; Inventory temporal profiling | Pending Approval |
| ValidFrom | StockItems.ValidFrom; archive cùng cột | System period start | Period distribution, không attribute transition count | Technical/audit metadata | Source identity riêng DW validity | Không chọn business effective | C01/C02 hoặc P01/P02 trong SQL evidence | Pending Approval |
| ValidTo | StockItems.ValidTo; archive cùng cột | System period end | Period distribution, không attribute transition count | Technical/audit metadata | Bảo toàn source precision | Coverage/identity, không policy tự chốt | C01/C02 hoặc P01/P02 trong SQL evidence | Pending Approval |

## Evidence và reference dependencies

### SCD-02 — danh sách Product Type 2 cụ thể để Owner review

**Khuyến nghị, chưa phê duyệt/kích hoạt:** ưu tiên `UnitPackageID`, `OuterPackageID`, `QuantityPerOuter` vì packaging context liên quan diễn giải unit/receipt reconciliation; không dùng để tự tính lại source fact quantity hoặc cost. `ColorID`, `Brand`, `Size`, `IsChillerStock` chỉ nên tracking khi Owner xác nhận nhu cầu grouping lịch sử của product sales/movement; nếu không cần thì dùng current-only classification theo policy được duyệt sau. Các cột đều có 0 transitions trong snapshot Q08, nên không invent historical changes. Product source history đang đổi CustomFields/Tags không phải trigger cho tracking set này.

Metadata được tái kiểm SELECT ngày 2026-11-14, cùng với Metadata Dictionary hiện có:

```sql
SELECT c.name,t.name AS type_name,c.max_length,c.precision,c.scale,c.is_nullable
FROM sys.columns AS c JOIN sys.types AS t ON t.user_type_id=c.user_type_id
WHERE c.object_id=OBJECT_ID(N'Warehouse.StockItems')
AND c.name IN (N'Brand',N'Size',N'ColorID',N'UnitPackageID',N'OuterPackageID',
               N'QuantityPerOuter',N'IsChillerStock')
ORDER BY c.column_id;
```

**Verified metadata:** ColorID int nullable; UnitPackageID/OuterPackageID/QuantityPerOuter int required; Brand nvarchar(50) nullable (100 bytes); Size nvarchar(20) nullable (40 bytes); IsChillerStock bit required. Không có data update hoặc ingestion. Color/package labels cần R7/R8 contract extension. KPI totals S03–S05 và I01–I05 phải invariant khi thêm/rekey dimension version; chỉ cách phân nhóm có thể đổi theo reporting mode được duyệt. Đây không mở KPI mới hoặc phê duyệt physical SCD2 implementation.

Q06/Q08: [Profiling SQL](wwi-profiling-queries.md), [Customer profile](wwi-customer-temporal-profiling.md), [Product profile](wwi-inventory-integrity-profiling.md). C01/C02, P01/P02: [SQL bổ sung](wwi-scd-temporal-evidence.md), các mục C01/C02 và P01/P02; [temporal assessment](wwi-scd-temporal-assessment.md) diễn giải giới hạn.

| Ref | Bảng ngoài chín source contracts | Khi nào cần / trạng thái |
| --- | --- | --- |
| R1 | Sales.CustomerCategories | Labels category/C05; ID đã có, contract/history label còn Pending Approval |
| R2 | Sales.BuyingGroups | Group labels nếu dùng; chưa tự ingestion |
| R3 | Application.People | Contacts/editor labels nếu scope thay đổi; hiện không analytical requirement |
| R4 | Application.DeliveryMethods | Chỉ khi mở delivery analytics |
| R5 | Application.Cities và geo hierarchy | Chỉ khi mở geo analytics, không tự thêm dimensions |
| R6 | Purchasing.Suppliers | Chỉ khi mở supplier analytics, ngoài MVP hiện tại |
| R7 | Warehouse.Colors | Color labels; chưa có approved ingestion contract |
| R8 | Warehouse.PackageTypes | Packaging labels/context; contract/temporal coverage cần duyệt |

Application.TransactionTypes vẫn là dependency dim_movement_type đã nêu ở DW-01, không thuộc classification hai dimensions này. Tên label hiện hành của reference không tự đại diện label lịch sử.

## Impact tới facts và marts

- Customer change: Type 1 chỉ đổi mô tả theo policy; Type 2 có thể thêm version nhưng không tự rekey mọi historical fact. Invoice buyer/bill-to lấy từ invoice header, không rewrite theo Customers.BillToCustomerID mới. C01/C02 distinct theo source CustomerID, không SK; C05 lấy một current row/NK.
- Product change: không sửa transaction price/tax/quantity từ master. Product/day mart grain vẫn NK/day; nếu muốn as-was attributes phải chọn version/reporting mode được duyệt, không JOIN toàn history theo NK. Current inventory Product SK gắn published state, không latest-at-query.
- Version lịch sử nguồn thay đổi chỉ Technical/Excluded attributes có thể không tạo DW Type 2 version; ngược lại 0 observed change không cấm forward tracking thuộc tính Type 2 được Owner duyệt. Không chốt merge/hash/lookup/rekey algorithm trong DW-02A.
