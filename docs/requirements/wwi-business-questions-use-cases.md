# WWI Business Questions & Use Cases — Phase 1.5

**Trạng thái: câu hỏi nghiệp vụ Phase 1.5 đã được phân loại theo BRD-01–BRD-12 được duyệt; dashboard chưa triển khai.** Xem [Business Requirements](wwi-business-requirements.md), [KPI Catalog](../../analytics/kpi-definitions/wwi-kpi-candidate-catalog.md) và nguồn WWI. Các câu hỏi Deferred/Unsupported giữ để giải thích giới hạn, không là cam kết MVP.

| ID | Subject area / câu hỏi | Use case / người dùng giả định | Nguồn và grain cần giữ | KPI candidates | Giới hạn / quyết định |
| --- | --- | --- | --- | --- | --- |
| BQ-S01 | Có bao nhiêu order được tạo theo tháng? | Theo dõi volume bán hàng đầu vào | `Orders.OrderID`, `OrderDate`; một order | S01 | Order chưa invoice vẫn là order; không gọi là sale/revenue. |
| BQ-S02 | Có bao nhiêu invoice theo tháng và bao nhiêu order chưa invoice? | Theo dõi chuyển đổi chứng từ | `Invoices.InvoiceID`, `InvoiceDate`; anti-join Orders→Invoices | S02 | `OrderID` nullable theo schema; snapshot max một invoice/order không là constraint. |
| BQ-S03 | Invoiced Sales Before Tax, Tax Amount và Invoice Amount Including Tax theo invoice date là bao nhiêu? | Đối soát chứng từ và phân bố theo kỳ | `InvoiceLines.InvoiceLineID` + `Invoices.InvoiceDate`; tổng hợp line trước khi join bảng khác | S03–S05 | BRD-03 duyệt measure báo cáo; không đồng nghĩa Recognized Revenue. |
| BQ-S04 | Ngày nào dùng cho invoice metrics? | Calendar cho KPI MVP | `Invoices.InvoiceDate`; `ConfirmedDeliveryTime` chỉ là quan sát nguồn | S02–S06 | BRD-02 duyệt InvoiceDate; Recognized Revenue S08 deferred. |
| BQ-S05 | Bình quân invoice và profit nguồn được báo thế nào? | Báo cáo có tên chính xác | Invoices/InvoiceLines riêng grain | S06,S09 | AIV trước thuế Core; LineProfit nguồn Optional; AOV S07 và official Gross Profit deferred. |
| BQ-S06 | Credit note/refund có đo được không? | Giải thích loại trừ phạm vi | `Invoices.IsCreditNote` và bảng nguồn đã khảo sát | S10 | BRD-07: ngoài MVP, không đủ bằng chứng hiện tại. |
| BQ-C01 | Có bao nhiêu buyer tạo order/invoice? | Customer activity theo kỳ | DISTINCT `Orders.CustomerID` hoặc `Invoices.CustomerID`; xác định tập trước | C01 | Order-based và invoice-based population khác nhau. |
| BQ-C02 | Tỷ lệ buyer có ít nhất hai order trong cùng tháng là bao nhiêu? | Theo dõi repeat order | Distinct OrderID theo buyer và tháng `OrderDate` | C02 | BRD-09 duyệt tử/mẫu theo tháng; không dùng tỷ lệ toàn lịch sử hoặc cộng tỷ lệ tháng. |
| BQ-C03 | Invoiced Sales Before Tax thuộc buyer hay bill-to? | Phân tích hai customer roles | `Invoices.CustomerID` và `BillToCustomerID` hai vai trò | C03–C04 | Buyer Core mặc định, bill-to Optional billing; không cộng hai phân bố. |
| BQ-C04 | Có thể phân nhóm customer theo thuộc tính nguồn không? | Segmentation sơ bộ | `Customers.CustomerCategoryID` current; history nếu dùng cần as-of | C05 | Current attributes không tự đại diện lịch sử. |
| BQ-I01 | Lượng xuất/nhập/điều chỉnh theo tháng là bao nhiêu? | Theo dõi movement | `StockItemTransactions.StockItemTransactionID`, type, signed `Quantity`, `TransactionOccurredWhen` | I01–I03,I05 | Type 12 có cả số âm/dương/0; không loại 0 tự động. |
| BQ-I02 | Tồn hiện tại là bao nhiêu? | Quan sát current holdings | `StockItemHoldings.StockItemID`, `QuantityOnHand` | I04 | Chỉ current state tại thời điểm đọc. |
| BQ-I03 | Có thể tính daily balance hoặc stockout risk không? | Giải thích loại trừ phạm vi | Movements + holdings, cần opening balance/time rule | I06–I07 | BRD-11/12: ngoài MVP, chưa đủ bằng chứng; không dựng snapshot ngày. |

**Thứ tự:** Core Sales được thiết kế/kiểm thử trước Customer rồi Inventory theo roadmap. BRD đã duyệt ở mức nghiệp vụ; technical validation và physical warehouse design chưa thực hiện.
