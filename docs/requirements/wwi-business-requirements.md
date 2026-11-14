# WWI Business Requirements — Phase 1.5

**Trạng thái: BRD-01–BRD-12 và định nghĩa nghiệp vụ KPI MVP đã được Project Owner phê duyệt trong Phase 1.5; triển khai/technical validation chưa thực hiện.** Phạm vi ba subject areas MVP theo [PROJECT_SCOPE.md](../../PROJECT_SCOPE.md); Sales/Invoicing được ưu tiên end-to-end. Fact/dimension grain và schema chưa được duyệt. Bằng chứng nguồn: [Metadata Dictionary](../data-models/wwi-metadata-dictionary.md), [Data Profiling](../data-models/wwi-data-profiling.md), [Source Relationships](../data-models/wwi-source-relationships.md), [Source Contracts](../data-models/wwi-source-contracts.md). Câu hỏi cụ thể ở [Business Questions](wwi-business-questions-use-cases.md); định nghĩa ở [KPI Catalog](../../analytics/kpi-definitions/wwi-kpi-candidate-catalog.md).

## BR-S — Sales/Invoicing

- **Objective:** mô tả quy mô đặt hàng, lập invoice, Invoiced Sales Before Tax, Tax Amount và Invoice Amount Including Tax theo `OrderDate`/`InvoiceDate`; không gọi các measure này là Recognized Revenue.
- **Business questions:** bao nhiêu order/invoice theo kỳ; bao nhiêu order chưa invoice; lượng và amount invoice line thay đổi thế nào; buyer và bill-to khác nhau ra sao; có thể dùng ngày invoice hay confirmed delivery cho từng mục tiêu báo cáo?
- **Entities:** `Sales.Customers`, `Orders`, `OrderLines`, `Invoices`, `InvoiceLines`, `CustomerTransactions`; `Warehouse.StockItems` là master của line. `Application.TransactionTypes` là reference cho transaction.
- **Quy trình dữ liệu quan sát:** customer → order header/lines → invoice header/lines → customer invoice transaction; payment transaction là luồng riêng, `InvoiceID` NULL trong toàn bộ 26.637 payment rows của snapshot. Stock issue nối invoice nhưng không có FK tới từng invoice line. Đây là quan hệ nguồn, không khẳng định quy trình nghiệp vụ bắt buộc cho mọi giao dịch tương lai.
- **Use cases:** theo dõi order count theo `OrderDate`, invoice count và ba measure invoice theo `InvoiceDate`; Average Invoice Value Before Tax trên cùng invoice population; buyer là role mặc định của Sales, bill-to là góc nhìn billing; đối soát invoice line với invoice transaction ở `InvoiceID` mà không cộng trùng.
- **KPI:** S01–S06 Core; S09 Source-Reported Line Profit Optional. S07 AOV và S08 Recognized Revenue deferred; S10 Refund/Credit Note không được bằng chứng hiện tại hỗ trợ. Official Gross Profit/COGS deferred. Xem catalog để biết công thức, grain và test.
- **Giới hạn nguồn:** 3.085 order chưa invoice; `Invoices.OrderID` nullable theo schema dù snapshot 0 NULL; 84 invoice thiếu `ConfirmedDeliveryTime`; không có FK OrderLine→InvoiceLine; `CustomerTransactions` khác grain InvoiceLines, không cộng hai amount với nhau. `IsCreditNote=1` có 0 rows, không đủ dữ liệu cho refund chi tiết.

## BR-C — Customer Analytics

- **Objective:** phân tích hoạt động và phân nhóm customer theo vai trò mua hàng và bill-to được ghi trong nguồn; giữ ranh giới giữa hiện trạng customer và lịch sử system-time.
- **Business questions:** bao nhiêu buyer có order/invoice trong kỳ; tỷ lệ đặt lại theo định nghĩa nào; amount nguồn theo buyer hay bill-to; nhóm CustomerCategoryID hiện hành có phân bố gì; thay đổi CreditLimit trong history có thể dùng as-of đến mức nào?
- **Entities:** `Sales.Customers`/`Customers_Archive`, `Orders`, `Invoices`, `InvoiceLines`, `CustomerTransactions`; `CustomerCategories` là reference ngoài chín bảng MVP nếu cần nhãn tên thay ID.
- **Quy trình dữ liệu quan sát:** `Orders.CustomerID` là buyer FK; `Invoices.CustomerID` là buyer và `Invoices.BillToCustomerID` là payer/bill-to role riêng. `Customers.BillToCustomerID` tự tham chiếu; invoice transaction CustomerID khớp bill-to trong snapshot, payment không gắn invoice qua FK.
- **Use cases:** buyer có order, buyer có invoice, số order theo buyer, order-based repeat, source amount theo buyer hoặc bill-to, phân bố current `CustomerCategoryID`.
- **KPI:** C01 Active Buyers, C02 Monthly Repeat Order Customer Rate và C03 Invoiced Sales Before Tax by Buyer là Core; C04 bill-to và C05 current category là Optional. C02 dùng ≥2 distinct OrderID trong cùng tháng / ≥1 distinct OrderID trong tháng theo `OrderDate`; quý tính lại trên cả quý. Không gọi C03 là Recognized Revenue.
- **Giới hạn nguồn:** 44.245 invoice có buyer khác bill-to; system-time không đồng nghĩa business-effective time. Current+archive có một customer version zero-duration, `FOR SYSTEM_TIME ALL` không trả dòng đó. Chưa chứng minh lịch sử SCD2 đầy đủ cho mọi giao dịch.

## BR-I — Inventory Movements

- **Objective:** mô tả luồng xuất/nhập/điều chỉnh hàng theo movement và current holding; không dựng số dư lịch sử khi thiếu opening balance/quy tắc stocktake.
- **Business questions:** issue/receipt/adjustment quantity theo kỳ và item; movement type nào có invoice/PO link; current QuantityOnHand là bao nhiêu tại thời điểm đọc; có đủ điều kiện tính daily closing balance hoặc stockout risk không?
- **Entities:** `Warehouse.StockItems`/`StockItems_Archive`, `StockItemHoldings`, `StockItemTransactions`; `Application.TransactionTypes`, `Sales.Invoices` và `Purchasing.PurchaseOrders/PurchaseOrderLines` chỉ là dependency để xác minh link/quantity. Purchasing chuyên sâu ngoài MVP.
- **Quy trình dữ liệu quan sát:** type 10 Stock Issue nối invoice; type 11 Stock Receipt nối PO; type 12 Stock Adjustment at Stocktake không nối hai chứng từ. Holdings là current state, không phải historical snapshot.
- **Use cases:** lượng issue/receipt/adjustment và xu hướng theo `TransactionOccurredWhen`; đối soát issue với invoice lines ở `(InvoiceID,StockItemID)` và receipt với PO lines ở `(PurchaseOrderID,StockItemID)` khi population nhất quán; xem current holding.
- **KPI:** I01 Stock Issue, I02 Stock Receipt và I04 Current Quantity On Hand là Core; I03 Signed Adjustments và I05 Movement Trend là Optional. I06 Daily Balance và I07 Stockout Risk ngoài MVP, không có bằng chứng hiện tại để công bố.
- **Giới hạn nguồn:** 4 movement Quantity=0, 9 PO-line pairs chưa receipt, 227/227 holdings không bằng tổng movement thô. Không mặc định các trường hợp đó là lỗi hoặc định nghĩa COGS.

## Phạm vi và thứ tự

Các business rules Phase 1.5 đã được duyệt; technical validation, chính sách as-of/incremental/SCD2 và thiết kế physical warehouse còn cần task tiếp theo. Customer và Inventory tiếp tục thuộc MVP nhưng triển khai tuần tự theo roadmap; không mở rộng Purchasing/Finance, tạo schema, pipeline hoặc Power BI trong bước này.
