# WWI KPI Definitions & Scope Catalog — Phase 1.5

**BRD-01–BRD-12 đã được Project Owner phê duyệt; các KPI MVP dưới đây là định nghĩa nghiệp vụ được duyệt ở mức tài liệu, chưa được triển khai/kiểm thử trong warehouse.** `Verified SQL` chỉ chứng minh phép tính nguồn ở snapshot khảo sát, không xác nhận accounting semantics hay chất lượng pipeline. Giữ nguyên KPI ID S01–S10, C01–C05, I01–I07. Xem [KPI Verification](wwi-kpi-verification-sql.md), [Source Contracts](../../docs/data-models/wwi-source-contracts.md) và [Business Rules Matrix](../../docs/requirements/wwi-business-rules-decision-matrix.md).

## Quy ước chung

- Mỗi công thức tính trên grain được ghi, rồi mới aggregate; không join nhiều bảng line/transaction/movement để cộng measures.
- Order metrics dùng `OrderDate`; invoice metrics dùng `InvoiceDate`; movement metrics dùng `TransactionOccurredWhen`; current holdings theo extraction time. Chưa chốt chính sách as-of/restate kỹ thuật.
- `ExtendedPrice`, `TaxAmount`, `LineProfit`, `TransactionAmount`, `QuantityOnHand` là cột nguồn. `Invoiced Sales Before Tax` là quy ước phân tích được duyệt, không là `Recognized Revenue` hoặc doanh thu kế toán.
- `COUNT_BIG(DISTINCT ...)` và phép group customer chỉ tính population đã nêu. NULL optional không tự bị loại trừ trừ khi công thức yêu cầu và quyết định đã duyệt.

| Lớp phạm vi | KPI ID | Trạng thái |
| --- | --- | --- |
| MVP Core | S01, S02, S03, S04, S05, S06, C01, C02, C03, I01, I02, I04 | Business definition approved; technical validation pending |
| MVP Optional | S09, C04, C05, I03, I05 | Business scope approved; source semantics/implementation validation pending theo từng KPI |
| Deferred | S07, S08 | Ngoài MVP hiện tại; không công bố AOV hay Recognized Revenue |
| Not Supported by Current Evidence | S10, I06, I07 | Ngoài MVP; không suy giá trị bằng 0 hoặc dựng daily balance/risk |

**Quy tắc chung cho Core/Optional:** mọi amount và count chỉ tính trong cùng population/khoảng thời gian đã lọc; grain nguồn theo từng mục; `SUM` trên line/movement và `COUNT` trên header riêng, ratio tính lại từ tử/mẫu. Không join payment transaction vào invoice line để cộng amount. NULL trong khóa/ngày bắt buộc là lỗi DQ; NULL ở optional FK không tự là orphan. Tiền giữ precision nguồn; đơn vị tiền/thuế và rounding cho semantic model cần technical validation trước công bố. Source SQL ở K01–K13 là reconciliation cấp nguồn, không thay thế test warehouse.

## Sales/Invoicing

### S01 — Order Count (MVP Core; Verified source SQL K01)

- **Business definition/purpose:** số order được tạo trong kỳ để theo dõi đầu vào Sales, gồm order chưa invoice; không là số sale hoàn tất.
- **Formula/source/grain:** `COUNT_BIG(*)` từ `Sales.Orders`, một `OrderID`; ngày `OrderDate`; filter kỳ theo ngày đặt; unit order; cộng qua các kỳ rời nhau.
- **Double count/DQ/approval:** không join OrderLines trước khi đếm; PK unique, `OrderDate` NOT NULL; đếm order trong kỳ kể cả chưa invoice. BRD-01/02 approved; cancellation/as-of kỹ thuật chưa được chốt. Đối soát K01 theo kỳ.

### S02 — Invoice Count (MVP Core; Verified source SQL K01)

- **Business definition/purpose:** số invoice phát hành theo kỳ, để đo volume chứng từ; không đồng nhất với Order Count.
- **Formula/source/grain:** `COUNT_BIG(*)` `Sales.Invoices`, một `InvoiceID`; `InvoiceDate`; filter kỳ theo ngày invoice; unit invoice; cộng kỳ rời nhau.
- **Double count/DQ/approval:** không join InvoiceLines hoặc CustomerTransactions để đếm; PK unique; mọi invoice trong kỳ theo nguồn, không thêm status filter chưa duyệt. BRD-01/02 approved. `IsCreditNote` tương lai cần kiểm chứng; snapshot max một invoice/order không là constraint. Đối soát K01.

### S03 — Invoice Amount Including Tax (MVP Core; Verified source SQL K02/K03)

- **Business definition/purpose:** tổng giá trị invoice gồm thuế theo `InvoiceLines.ExtendedPrice`; **không gọi là recognized revenue**.
- **Formula/source/grain:** `SUM(InvoiceLines.ExtendedPrice)` trên `InvoiceLineID`, join duy nhất `Invoices.InvoiceID` để lấy `InvoiceDate`; cùng invoice population của S04–S06, không thêm eligibility chưa được duyệt; đơn vị tiền nguồn; cộng các line/kỳ không chồng nhau.
- **Double count/DQ/approval:** không cộng thêm `CustomerTransactions.TransactionAmount` vì type 1 phản ánh cùng amount; kiểm line PK/FK và tổng theo InvoiceID; BRD-01/03 approved, accounting semantics/credit note tương lai cần kiểm chứng. Đối soát K02/K03.

### S04 — Invoice Tax Amount (MVP Core; Verified source SQL K02)

- **Business definition/purpose:** tổng `InvoiceLines.TaxAmount` như measure thuế invoice riêng theo BRD-03.
- **Formula/source/grain:** `SUM(TaxAmount)` trên `InvoiceLineID`; `InvoiceDate` qua header; cùng invoice population của S03/S05/S06, không thêm eligibility chưa được duyệt; đơn vị tiền nguồn; cộng line/kỳ không chồng nhau.
- **Double count/DQ/approval:** không join payment hoặc movement; kiểm NULL/precision và RI line→invoice; BRD-03 approved, accounting treatment ngoài kết luận từ SQL. Đối soát K02 và S03 = S04 + S05 cùng population.

### S05 — Invoiced Sales Before Tax (MVP Core; Verified source arithmetic K02)

- **Business definition/purpose:** measure mặc định cho Invoiced Sales trước thuế theo BRD-03; là quy ước phân tích dự án, không phải recognized revenue hay xác nhận chuẩn kế toán.
- **Formula/source/grain:** `SUM(ExtendedPrice - TaxAmount)` trên `InvoiceLineID` từ `Sales.InvoiceLines`, join `Sales.Invoices` bằng `InvoiceID` để lấy `InvoiceDate`; cùng invoice population của S03/S04/S06; đơn vị tiền nguồn; cộng line/kỳ rời nhau. `SUM(UnitPrice*Quantity)` chỉ là đối soát arithmetic ở snapshot, không là công thức chính.
- **Double count/DQ/approval:** tính ở line trước khi tổng hợp; không join transaction/payment. BRD-03 approved. Kiểm `S03 − S04 = S05` và arithmetic/precision từng line (K02); credit note/discount/rounding mới cần technical validation, không tự suy chính sách kế toán.

### S06 — Average Invoice Value Before Tax (MVP Core; Verified source SQL K10)

- **Business definition/purpose:** bình quân Invoiced Sales Before Tax trên mỗi invoice theo BRD-06, **không gọi là AOV**.
- **Formula/source/grain:** `S05 / S02` cùng invoice population, filter và `InvoiceDate`; numerator grain `InvoiceLineID`, denominator distinct `InvoiceID`; tiền nguồn/invoice; denominator 0 → NULL/không công bố kỳ đó. Tính ratio sau khi aggregate, không cộng/average ratio kỳ.
- **Double count/DQ/approval:** tổng line theo invoice hoặc join 1:N đúng một lần; kiểm invoice không có line/duplicate line và numerator/denominator cùng filter. BRD-06 approved; K10 Verified 2.443,08 trên toàn snapshot; số 2.808,73 ở K02 là bình quân **gồm thuế**, không phải S06.

### S07 — Average Order Value (Deferred; ngoài MVP)

- **Business definition/purpose:** amount trung bình trên một order đủ điều kiện theo cùng cohort; chỉ dùng sau khi định nghĩa “order value”.
- **Formula/source/grain:** phương án invoice cohort `SUM(eligible invoice-line amount) / COUNT_BIG(DISTINCT eligible Orders.OrderID)` theo order hoặc invoice date đã chọn; nguồn Orders→Invoices→InvoiceLines; grain trước tổng hợp là InvoiceLineID, denominator OrderID; unit tiền/order; ratio phải tính lại từ tử/mẫu.
- **Double count/DQ/open:** 3.085 orders chưa invoice, `Invoices.OrderID` nullable, snapshot một invoice/order không là constraint. Eligibility, amount trước/sau thuế, date/cohort/as-of và cách xử lý multi-invoice cần duyệt; không tự dùng S06 làm AOV.

### S08 — Recognized Revenue (Deferred; ngoài MVP)

- **Business definition/purpose:** amount được công nhận theo sự kiện nghiệp vụ đã chọn; hiện chưa có quy tắc được duyệt.
- **Formula/source/grain:** hai phương án để review: tổng `eligible InvoiceLines` theo `InvoiceDate`, hoặc theo `Invoices.ConfirmedDeliveryTime` khi đủ điều kiện giao; grain InvoiceLineID, unit tiền/kỳ, cộng sau lọc. Cần chọn nguồn amount S03/S05, tax, credit, NULL delivery và as-of trước khi tính KPI.
- **Double count/DQ/open:** không cộng invoice transaction type 1 với invoice lines; 84 delivery NULL và 70.426 delivery date sau invoice date; revenue recognition/tax/eligibility vẫn Open.

### S09 — Source-Reported Line Profit (MVP Optional; Verified source SQL K02/K13)

- **Business definition/purpose:** chỉ tổng hợp cột `InvoiceLines.LineProfit` như measure phân tích do nguồn báo cáo; không gọi là Gross Profit chính thức. Official Gross Profit/COGS deferred.
- **Formula/source/grain:** `SUM(InvoiceLines.LineProfit)` trên `InvoiceLineID`, join `Invoices.InvoiceID` cho `InvoiceDate`; cùng invoice population/filter, đơn vị tiền nguồn; cộng line/kỳ rời nhau. Không suy historical COGS.
- **Double count/DQ/approval:** không join cost/movement hoặc transaction để cộng; 4.626 line âm không tự là lỗi. BRD-05 approved cho optional source measure; semantics lợi nhuận nguồn, precision/eligibility cần technical validation trước report; K02 đối soát tổng cột, không chứng minh Gross Profit.

### S10 — Credit Note / Refund Amount (Not Supported by Current Evidence; ngoài MVP)

- **Business definition/purpose:** theo dõi hoàn/điều chỉnh nếu nguồn hỗ trợ; hiện không triển khai refund chi tiết trong MVP.
- **Formula/source/grain:** **không định nghĩa công thức refund** từ dữ liệu hiện có. `Invoices.IsCreditNote=1` có 0 row trong snapshot; không có bảng returns/refunds chi tiết trong contract chín bảng. Date/filter/unit/aggregation chưa áp dụng.
- **Double count/DQ/open:** không suy refund từ order chưa invoice, payment transaction hoặc stock receipt. Cần nguồn/biz rule riêng và scope approval trước KPI.

## Customer Analytics

### C01 — Active Buyers with Orders (MVP Core; Verified source SQL K04)

- **Business definition/purpose:** số buyer có ít nhất một order trong kỳ để đo hoạt động đặt hàng, không mặc định đã giao/ghi nhận revenue.
- **Formula/source/grain:** `COUNT_BIG(DISTINCT Orders.CustomerID)` từ grain OrderID, `OrderDate`; filter kỳ; unit customer; không cộng distinct counts các kỳ để được unique cả năm.
- **Double count/DQ/approval:** không join OrderLines; kiểm CustomerID FK, role buyer theo BRD-08 và `OrderDate` theo BRD-02; distinct count không cộng qua kỳ. Đối soát K04 cho toàn snapshot và theo kỳ khi triển khai.

### C02 — Monthly Repeat Order Customer Rate (MVP Core; Verified source SQL K11)

- **Business definition/purpose:** tỷ lệ buyer đặt ít nhất hai order khác nhau trong cùng tháng theo BRD-09; đo đặt lại, không đồng nghĩa repeat purchase đã giao.
- **Formula/source/grain:** trên `Sales.Orders`, nhóm `(YEAR(OrderDate), MONTH(OrderDate), CustomerID)` và đếm distinct `OrderID`; tử = buyer có ≥2 distinct OrderID/tháng, mẫu = buyer có ≥1/tháng. `OrderDate`, grain OrderID trước nhóm; unit %; mẫu 0 → NULL/không công bố. Quý tính lại trên toàn quý từ Orders, không cộng hoặc bình quân tỷ lệ tháng.
- **Double count/DQ/approval:** không join OrderLines hoặc đếm dòng; gồm order chưa invoice, cùng period/filter/as-of cho tử/mẫu. BRD-09 approved; K11 đã chạy theo tháng, K04 toàn lịch sử không là tỷ lệ tháng. Restatement/as-of kỹ thuật chuyển WWI-04.

### C03 — Invoiced Sales Before Tax by Buyer (MVP Core; Verified source SQL K12)

- **Business definition/purpose:** phân bố measure S05 theo buyer `Invoices.CustomerID`, vai trò mặc định của Sales Analytics; không là Recognized Revenue.
- **Formula/source/grain:** join `InvoiceLines.InvoiceID`→`Invoices.InvoiceID`, group `Invoices.CustomerID`, `SUM(ExtendedPrice-TaxAmount)`; grain InvoiceLineID, `InvoiceDate`; cùng invoice population/filter S05; tiền nguồn/buyer; cộng group trong một role.
- **Double count/DQ/approval:** không join payment/OrderLines; tổng các buyer groups bằng S05 ở K12. BRD-03/08 approved; K05 lịch sử chỉ kiểm grouping gồm thuế, không là kết quả C03 mới.

### C04 — Invoiced Sales Before Tax by Bill-to (MVP Optional; Verified source SQL K12)

- **Business definition/purpose:** phân bố cùng measure S05 theo `Invoices.BillToCustomerID` cho góc nhìn billing, không thay thế C03.
- **Formula/source/grain:** group `SUM(InvoiceLines.ExtendedPrice-InvoiceLines.TaxAmount)` theo `Invoices.BillToCustomerID`; grain InvoiceLineID, `InvoiceDate`; cùng invoice population/filter S05; tiền nguồn/bill-to; tổng group phải bằng S05.
- **Double count/DQ/approval:** không cộng phân bố buyer và bill-to; 44.245 invoices khác role. BRD-08 approved; K12 kiểm riêng từng tổng, K05 lịch sử chỉ là grouping gồm thuế.

### C05 — Current Customer Category Distribution (MVP Optional; Verified source SQL K06)

- **Business definition/purpose:** số customer hiện hành theo `CustomerCategoryID` để mô tả segmentation nguồn hiện tại.
- **Formula/source/grain:** `COUNT_BIG(*) GROUP BY Customers.CustomerCategoryID` trên current CustomerID; **snapshot/extraction time**, không gắn lịch sử giao dịch; unit customer; group counts cộng bằng current customer count.
- **Double count/DQ/open:** không join Orders trước khi đếm; kiểm PK/category FK. Lịch sử category/as-of, segment eligibility và nhãn reference cần quyết định/kiểm chứng riêng.

## Inventory Movements

### I01 — Stock Issue Quantity (MVP Core; Verified source SQL K07)

- **Business definition/purpose:** magnitude xuất kho theo movement type 10.
- **Formula/source/grain:** `-SUM(Quantity)` trên `StockItemTransactionID` với `TransactionTypeID=10`; `TransactionOccurredWhen`; filter kỳ/type; unit stock units; cộng movement cùng kỳ.
- **Double count/DQ/open:** không join InvoiceLines để cộng quantity; kiểm type, signed quantity và PK; return/reversal semantics nếu có sau này còn mở.

### I02 — Stock Receipt Quantity (MVP Core; Verified source SQL K07)

- **Business definition/purpose:** số unit nhập theo movement type 11.
- **Formula/source/grain:** `SUM(Quantity)` trên movement ID, type 11; `TransactionOccurredWhen`; filter kỳ/type; unit stock units; cộng movement.
- **Double count/DQ/open:** không join PO lines trực tiếp để cộng; kiểm type, PO link và quantity; Purchasing chuyên sâu ngoài MVP.

### I03 — Signed Stock Adjustments (MVP Optional; Verified source SQL K07)

- **Business definition/purpose:** tổng điều chỉnh kho có dấu theo movement type 12, không gọi là receipt/issue.
- **Formula/source/grain:** `SUM(Quantity)` trên movement ID, type 12; `TransactionOccurredWhen`; filter kỳ/type; unit stock units signed; cộng movement nhưng báo cả số dương/âm/0.
- **Double count/DQ/open:** bốn dòng Quantity=0 chưa là lỗi; stocktake semantics và netting rule còn mở.

### I04 — Current Quantity On Hand (MVP Core; Verified source SQL K07)

- **Business definition/purpose:** tổng tồn hiện hành tại thời điểm đọc bảng holdings.
- **Formula/source/grain:** `SUM(StockItemHoldings.QuantityOnHand)` trên `StockItemID`; **extraction/snapshot time**, không theo ngày giao dịch; unit stock units current; cộng giữa item một snapshot, không cộng qua nhiều snapshot thời gian.
- **Double count/DQ/open:** không join movements rồi cộng holdings lặp; kiểm PK/FK và count; opening balance/daily history chưa có.

### I05 — Product Movement Trend (MVP Optional; Verified source SQL K08)

- **Business definition/purpose:** số movement/quantity theo tháng và stock item/type để thấy xu hướng nguồn.
- **Formula/source/grain:** `COUNT_BIG(*)`, `SUM(Quantity)` theo `YEAR/MONTH(TransactionOccurredWhen), StockItemID, TransactionTypeID` trên movement ID; unit rows/stock units; chỉ cộng các nhóm cùng định nghĩa, giữ dấu.
- **Double count/DQ/open:** không join invoice/PO lines trước group; kiểm timestamps/type/PK; diễn giải demand/stockout từ movement cần business rule.

### I06 — Daily Closing Inventory Balance (Not Supported by Current Evidence; ngoài MVP)

- **Business definition/purpose:** tồn cuối ngày từng item nếu có opening balance và quy tắc hiệu lực.
- **Formula/source/grain:** `opening_balance(item,day0) + cumulative signed movements` là công thức **chỉ mang tính điều kiện**, hiện thiếu opening balance đáng tin và stocktake rules; daily date basis/aggregation chưa áp dụng.
- **Double count/DQ/open:** 227/227 holdings khác tổng movement thô; không tạo daily snapshot hoặc claim Verified balance.

### I07 — Stockout Risk (Not Supported by Current Evidence; ngoài MVP)

- **Business definition/purpose:** cảnh báo nguy cơ hết hàng theo nhu cầu và thời gian bổ sung hàng.
- **Formula/source/grain:** chưa có công thức được bảo vệ; cần demand/forecast, reorder/lead-time và thời điểm inventory snapshot được duyệt. Unit/date/filter/aggregation chưa áp dụng.
- **Double count/DQ/open:** `QuantityOnHand=0` hiện có 0 item chỉ nói về snapshot current, không chứng minh stockout lịch sử hoặc risk tương lai.
