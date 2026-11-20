# ANALYTICS-DISCOVERY-01 — Sales Insight Discovery

**SALES_INSIGHT_DISCOVERY_COMPLETE — hoàn tất 2026-11-21.** Đây là phân tích dữ liệu và đề xuất nội dung dashboard để Owner review; chưa tạo PBIX, DAX, semantic model, mart mới hoặc dashboard assets. Thời điểm thu thập SQL được lưu bằng UTC trong JSON, tách khỏi business dates.

Evidence: [25 truy vấn SQL](queries.sql), [kết quả và lineage/preservation](results.json), [runner chỉ đọc](analyze.py). Mỗi `Qxx` dưới đây là một query có tên trong SQL và một entry tương ứng trong JSON; số tiền giữ decimal ở output, chỉ làm tròn khi trình bày.

## 1. Population, contracts và giới hạn

- Branch lúc bắt đầu: `refactor/mvp-simplification`, HEAD `e23f56fd987c7631113c752e2415e4014f5f3d62`, working tree sạch.
- Tất cả 21 model đang chứa đúng input version `c825b18e-fc62-4cf1-8837-b37b4c9f9668`. Đây là **current analytical input của local models**, không phải Certified/Raw publication: publication pointer vẫn NULL, source consistency vẫn UNVERIFIED. Root Full Load là `5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8`.
- Model pins/ruleset/measure version, hai header view definitions và SHA256 của SQL/config được kiểm tra/lưu trong JSON. Default customer role BUYER; Customer/Product dimensions là observed-current của cùng version, không phải historical SCD2 đã resolved.
- Cả19 warehouse table content digests/counts còn khớp bằng chứng INGEST-INCR-01 đã nghiệm thu; runner dừng nếu drift so với accepted baseline, không chỉ kiểm tra version stamp. Các SELECT dùng một repeatable snapshot và không chạy model/pipeline.
- Contracts: [KPI catalog](../../requirements/kpi-definitions/wwi-kpi-candidate-catalog.md), [BRD](../../requirements/wwi-business-rules-decision-matrix.md), [measure YAML](../../../dbt/config/measures.yml), [business YAML](../../../dbt/config/business_rules.yml). Các dòng technical pending trong catalog là lịch sử; runtime evidence hiện hành ở [Sales dbt](../../../dbt/README.md) và [incremental acceptance](../../audits/ingest-incr-01/evidence.json).
- S05 = SUM(ExtendedPrice−TaxAmount); S04 = SUM(TaxAmount); S03 = SUM(ExtendedPrice). S02 đếm invoice header, S01 đếm order header; S06=AIV=S05/S02 cùng population, denominator 0 → NULL. Không average các AIV/tháng để tính AIV năm; không gọi AIV là AOV. Giữ eligibility và cả VALID/WARNING đủ điều kiện.
- Invoice measures dùng InvoiceDate; Order Count dùng OrderDate. Units là source quantities, chưa chuẩn hóa package/piece. Chưa xác nhận mã currency trong semantic contract nên không gắn USD/BRL hoặc ký hiệu tiền. Invoiced Sales không là recognized revenue; LineProfit không là official Gross Profit/COGS.
- WWI là dataset của đồ án; findings mô tả snapshot này, không chứng minh tác động thực tế lên một doanh nghiệp. Business dates 2013–2016 khác ngày chạy phân tích năm 2026; không dùng relative-date “YTD năm nay”. Source consistency UNVERIFIED và calendar đủ ngày không chứng minh tất cả giao dịch nghiệp vụ đều đầy đủ/final.

### Coverage và headline — Q01–Q04, Q25

| Thuộc tính | Quan sát |
|---|---:|
| Business date range | 01/01/2013–31/05/2016 |
| Calendar rows / expected days / missing daily mart dates | 1.247 / 1.247 / 0 |
| Months / boundary-incomplete months theo rule hiện hành | 41 / 0 |
| Năm dương lịch đủ 12 tháng | 2013, 2014, 2015; 2016 chỉ 01–05 |
| Invoice lines / invoices / orders | 228.265 / 70.510 / 73.595 |
| S05 Sales Before Tax | 172.261.341,20 |
| S04 Tax / S03 Including Tax | 25.782.098,25 / 198.043.439,45 |
| S06 AIV / Source Units | 2.443,08 / 8.950.628 |
| Negative/zero S05 lines; excluded invoice lines | 0 / 0 / 0 |
| Products / buyers / bill-to accounts có Sales | 227 / 663 / 263 |
| DQ population | 604.672 = 600.046 VALID + 4.626 WARNING; 0 INVALID/quarantine |

| Năm | Sales trước thuế | Invoice Count | AIV | Phạm vi |
|---|---:|---:|---:|---|
| 2013 | 45.707.188,00 | 18.767 | 2.435,51 | 12 tháng |
| 2014 | 49.929.487,20 | 20.303 | 2.459,22 | 12 tháng |
| 2015 | 53.991.490,45 | 22.250 | 2.426,58 | 12 tháng |
| 2016 | 22.633.175,55 | 9.190 | 2.462,80 | 5 tháng; không so trực tiếp với cả năm 2015 |

### Grain và join contract

| Input | Grain / cách dùng |
|---|---|
| fact_invoice_line | Một InvoiceLineID/version; eligible Sales, tax, source units, source LineProfit; không join fact_order_line để cộng Sales |
| fact_order_line | Một OrderLineID/version; order-line drill, không làm denominator Order Count |
| int_order_header / int_invoice_header | Một OrderID / InvoiceID; hai population/date basis riêng |
| dim_customer / dim_product / dim_date | Một observed customer/product hoặc calendar date/version; natural keys được kiểm tra unique trước label join |
| mart_sales_daily | Một calendar date; Sales/InvoiceDate và orders/OrderDate được aggregate riêng trước khi kết hợp |
| mart_sales_product_daily | InvoiceDate × StockItemID; amount/units cộng được; distinct invoice count không cộng xuyên products |
| mart_customer_sales | InvoiceDate × customer × một reporting role; hiện chỉ BUYER |
| mart_sales_customer_summary | Customer × role, summary trên toàn period; không join vào customer daily để cộng lần nữa |
| mart_sales_monthly | Calendar month, complete-period flags và coverage-aware MoM/YoY |

## 2. Business questions và hypotheses

Mỗi direction dưới đây có số liệu đầy đủ trong JSON. Các interpretation/action ở mục 3 tách khỏi causal hypotheses; direction D06/D08 là khám phá bổ sung, không tự thành KPI mới.

| ID / câu hỏi và vì sao cần | Hypothesis để kiểm tra | Measures / dimensions | SQL | Quan sát và diễn giải / caveat |
|---|---|---|---|---|
| D01 — Sales tăng nhờ volume hay AIV? Giúp chọn drill đúng | Sales 2016 thấp vì ít invoice | S05/S02/S06, UNITS; InvoiceDate, same-MMDD window; S01 riêng OrderDate | Q03–Q05 | 01–05/2016 Sales −0,20%, invoices +0,90%, AIV −1,09%; hypothesis ít invoice không đúng ở aggregate. Count/AIV decomposition là identity, không phải price/campaign causality |
| D02 — Giá trị và quantity tập trung vào cùng SKU? Tránh một ranking áp dụng mọi quyết định | Top Sales cũng là top Units | S05/UNITS; product, date, observed label | Q06–Q07 | Top10 hai ranking không giao nhau; source units khác package, không suy physical throughput/margin |
| D03 — Có thực sự theo quy tắc 80/20? Quyết định mức coverage cần trên trang portfolio | 20% SKU tạo 80% Sales | S05; product/date, cumulative share | Q07 | Cần69/227 SKU cho80%; nhóm top20% làm tròn lên46 SKU chỉ tạo64,52%; không tự cắt long tail |
| D04 — Sales phụ thuộc customer hay billing group? Tránh hiểu sai concentration | Buyer và Bill-to cho cùng mức tập trung | S05/C03 attribution; một role/lần, invoice-time keys | Q08–Q09 | Top5 Buyer1,07% so với Bill-to63,75%; hai role đều reconcile riêng về tổng S05. Không là credit/default risk |
| D05 — Negative LineProfit rải rác hay có cấu trúc? Ưu tiên investigation | Warnings là isolated line outliers | Source LineProfit diagnostic, line count/rate; product/month | Q13–Q15, Q23, Q25 | 4 SKU có100% lines âm, chứa88,93% warnings; cần kiểm tra source definition/master data, không gọi là lỗ chính thức hoặc tự loại Sales |
| D06 — Có mùa vụ/volatility không? Tránh forecast từ chart thô | July cao chỉ do tháng dài | S05 và active-day diagnostic; month-of-year, complete years | Q10–Q12, Q24 | July normalized1,1489; sau điều chỉnh active days còn1,1099, chỉ3 quan sát/năm-tháng. Có pattern mô tả; chưa chứng minh mùa vụ/causal driver |
| D07 — Lifetime bottom có bất lợi về lịch sử quan sát? So SKU công bằng | Mọi SKU có cùng exposure | S05/UNITS, first observed sale, active months; cùng window | Q06, Q19, Q22 | 8 SKU có5 tháng,219 SKU có41 tháng; SKU222 đổi rank150→32 ở same 01–05/2016. First sale không chứng minh ngày launch |
| D08 — AIV có che skew/outliers? Cần distribution/context | Invoice amounts quanh mean, lớn bất thường là lỗi | Invoice-level S05 aggregate; percentiles/Tukey, InvoiceDate | Q16 | Median1.649, AIV2.443,08; p99≈13.482,49;4.844 invoices vượt Tukey upper. Diagnostic thống kê, không DQ exclusion; continuous percentiles dùng double precision |
| D09 — Order–invoice gap có là mất bán hàng? Tránh funnel sai | 3.085 order không direct invoice là3.085 thất bại | S01/S02, header membership/self-FK; OrderDate | Q17–Q18, Q21 | 3.080 được invoiced order khác tham chiếu qua BackorderOrderID. Không chứng minh completion, không quy đổi gap sang lost Sales |
| D10 — Zero daily activity là thiếu data? Tránh dashboard fill/filter sai | 178 zero dates phân bố ngẫu nhiên | S05/S02/S01; dense date, ISO weekday | Q02, Q11 | Toàn bộ178 Chủ nhật có0 orders/invoices; calendar không thiếu dòng. Không chứng minh ngày đóng cửa hoặc source transaction completeness |

## 3. Tám insight candidates có evidence

Confidence dưới đây áp dụng cho **mô tả trong pinned dataset**; không là mức tin cậy của nguyên nhân hoặc khả năng khái quát ra doanh nghiệp thật.

### I01 — Sales đầu 2016 đi ngang dù invoice count tăng

- **Evidence/period:** Q05, 01–05/2015 Sales22.679.145,45/9.108 invoices/AIV2.490,02; 01–05/2016 Sales22.633.175,55/9.190/AIV2.462,80. Sales −0,20%, invoices +0,90%, AIV −1,09%; delta Sales −45.969,90.
- **Implication/action:** Trang Overview cần đặt volume và AIV cạnh tăng trưởng Sales; drill product/basket mix để đặt hypothesis về AIV, không kết luận do giảm giá hay campaign. Arithmetic volume component +204.182,03; AIV component −247.919,89; interaction −2.232,04 (Q05), không phải causal attribution.
- **Confidence/caveat:** Cao về arithmetic. Same-MMDD window có152 calendar days/130 active invoice days năm2016 so với151/129 năm2015; Sales/active day giảm0,97%, invoices/active day chỉ tăng0,12%. Đây là observed-active days, không phải lịch làm việc đã được nghiệp vụ xác nhận.

### I02 — Không áp đặt quy tắc 80/20 cho portfolio

- **Evidence/segment:** Q07,69/227 SKU (30,40%) để đạt80% Sales;46 SKU top20% làm tròn lên đóng64,52%. Top10 đóng32,63%, top1 chỉ6,45%.
- **Implication/action:** Pareto phải tính động theo date/product selection với denominator được ghi rõ. Đánh giá coverage một tập SKU trước khi ưu tiên, không giả một ngưỡng20% luôn đủ hoặc xóa SKU tail.
- **Confidence/caveat:** Cao; S05 lines/product totals đều dương ở version này (Q01/Q07). Đây là Sales contribution, không cost-to-serve, strategic assortment hay profitability.

### I03 — Top sản phẩm theo Sales và theo Units phục vụ hai câu hỏi khác nhau

- **Evidence:** Q07 cho intersection top10 bằng0; top10 Sales tạo32,63% Sales nhưng chỉ5,92% source units. Q06: Air cushion machine (Blue), SKU215, Sales11.107.251,00 từ5.849 source units; rank Sales1 nhưng Units156.
- **Implication/action:** Product page cần toggle hai ranking và tooltip về source unit/package. Không dùng ranking Sales làm proxy cho số lượng xử lý, hoặc ranking Units để định giá/đầu tư tự động.
- **Confidence/caveat:** Cao về rankings; chưa chuẩn hóa đơn vị và chưa có inventory/cost/service-effort analysis. Product labels là observed-current, không historical attribute reconstruction.

### I04 — Concentration thay đổi lớn khi đổi vai trò customer

- **Evidence:** Q08,663 buyers: top1=0,22%, top5=1,07%;263 bill-to accounts: top1=31,64%, top5=63,75%. Q09 có44.245/70.510 invoice với hai role khác nhau;2 bill-to accounts phục vụ nhiều buyer, tối đa201 buyer/account.
- **Implication/action:** Buyer là default Sales view; Bill-to là billing-attribution lens riêng với single selection và nhãn rõ. Giải thích role trước khi kể câu chuyện “phụ thuộc customer”.
- **Confidence/caveat:** Cao; mỗi role riêng đều sum đúng172.261.341,20, không cộng hai role. Không suy credit exposure, receivable hay default risk từ Sales concentration; không dùng current CRM BillTo để thay invoice-time key.

### I05 — Source LineProfit âm có cấu trúc theo bốn biến thể SKU

- **Evidence:** Q13–Q15/Q23:4.626/228.265 lines (2,03%),18 products,4.494 invoices bị ảnh hưởng. Source LineProfit âm cộng −320.493,55; Sales trên warning lines4.962.959,45 (2,88% tổng S05) vẫn được tính.
- Bốn SKU145/142/143/144, Halloween zombie mask (Light Brown), các size XL/S/M/L, có1.071/1.044/1.017/982 negative lines; mỗi SKU100% lines âm. Tổng4.114 lines=88,93% warnings; negative source-profit sum của nhóm−274.500,00 (85,65% tổng âm).
- **Implication/action:** Ưu tiên kiểm tra định nghĩa Source LineProfit, product master/cost/unit mapping của nhóm biến thể với business owner. Dashboard mở investigation table, không tự tăng giá, sửa nguồn, đổi threshold hoặc chuyển WARNING thành INVALID.
- **Confidence/caveat:** Cao về source pattern; nguyên nhân chưa xác minh. LineProfit chỉ source-reported diagnostic/optional S09, không official loss/Gross Profit/COGS. DQ denominator ở đây là invoice lines, không604.672 records của toàn DQ.

### I06 — Zero Sundays là pattern trong dữ liệu, không phải lỗ hổng calendar

- **Evidence:** Q02/Q11:1247 calendar days không thiếu daily mart rows;178 Chủ nhật có0 orders/invoices/Sales; tất cả1069 ngày còn lại có invoice. Thứ Bảy có5.885 invoices/178 ngày và AIV2.575,60, khác weekdays.
- **Implication/action:** Giữ0 trong daily chart, hiển thị day-of-week; phân biệt average/calendar day với average/observed-active day. Không tự loại Chủ nhật để làm đẹp tăng trưởng hoặc fill0 thành missing.
- **Confidence/caveat:** Cao về pattern; không có business calendar để khẳng định cửa hàng đóng cửa hay demand bằng0. Calendar completeness không chứng minh source business completeness.

### I07 — Lifetime ranking làm mờ sản phẩm có lịch sử ngắn

- **Evidence:** Q19/Q22:219 SKU có41 observed active months;8 SKU có5 tháng (first observed sale02–07/01/2016), tổng Sales1.142.515,20. SKU222 Chocolate beetles250g đứng150 theo lifetime nhưng32 khi so tất cả227 SKU cùng01–05/2016; SKU226 đổi158→43.
- **Implication/action:** Hiển thị first observed sale/active months và cho so lifetime với comparable window; tránh gắn nhãn underperformer chỉ từ lifetime bottom rank.
- **Confidence/caveat:** Cao về exposure/rank shift; first observed sale không là ngày launch hoặc availability. Không biết stockout, promotion, cost hay distribution để khuyến nghị tăng/giảm assortment.

### I08 — Order–invoice gap không là số đơn thất bại

- **Evidence:** Q17/Q18:3.085 orders không có invoice trực tiếp;2.924 có OrderDate trước tháng invoice cuối. Q21:3.080 trong số này được order khác có invoice tham chiếu qua BackorderOrderID;5 không có incoming reference. Cả3.085 có order lines.
- **Implication/action:** Trình bày Order Count và Invoice Count như hai population/date basis; không dùng73595−70510 hoặc invoice/order ratio làm conversion/lost-Sales KPI. Nếu cần backlog/fulfillment phải khảo sát lifecycle và source quantity mapping riêng.
- **Confidence/caveat:** Cao về quan hệ snapshot. Linked parent có invoice không chứng minh phần backorder đã fulfilled; không join trực tiếp OrderLine–InvoiceLine vì không có mapping đã được duyệt. Không quy đổi các order này thành lost revenue/refund/canceled.

### Khám phá bổ sung chưa nâng thành kết luận kinh doanh

- **Mùa vụ:** Q10 July index1,1489 so với mean month trong từng năm đủ12 tháng; Q24 còn1,1099 sau điều chỉnh observed-active days (range1,1070–1,1113), chỉ3 annual observations2013–2015. Có pattern đáng xem, chưa đủ forecast hoặc giải thích bởi mùa hè/campaign/holidays; chưa kiểm soát Saturday mix, giá, assortment và demand. Dùng heatmap khám phá nếu còn nhu cầu, không mặc định tạo forecasting page.
- **Volatility:** Q12 CV monthly2013/2014/2015 lần lượt11,32%/8,54%/7,86%;2016 chỉ5 tháng nên không so ngang như cả năm. Không suy ra vận hành ổn định hơn vì còn trend/calendar confounding.
- **Distribution:** Q16 median invoice1.649 thấp hơn AIV2.443,08; p99≈13.482,49, max32.026. Có4.844 invoice trên Tukey upper≈6.640,46. Percentile/Tukey là diagnostics, không chuẩn fraud/DQ; không loại các invoice này khỏi S05.
- **Bottom products:** Q06 có đủ227 ranks. SKU209 Packing knife9mm có lifetime Sales57.361,50, Units30.350,41 active months; thấp về Sales nhưng không thấp tương ứng về Units. Không dùng bottom Sales làm bằng chứng ngừng bán.

## 4. Dashboard content proposal — chờ Owner review, chưa thiết kế/triển khai report

Ưu tiên bốn trang nhỏ. Persistent context: selected period, InvoiceDate/OrderDate basis, Buyer/Bill-to role, source-unit label, data through31/05/2016, version/Uncertified. Mỗi trang tối đa khoảng3 analytical visuals; không cần gauge, pie nhiều nhóm hoặc bản đồ khi chưa có câu hỏi địa lý được xác minh.

| Ưu tiên/trang | Purpose, key questions và KPI cards | Visuals và interactions | Filters / required inputs | Story sequence |
|---|---|---|---|---|
| P1 — Sales performance | Sales đi ngang do volume hay AIV? Cards S05/S02/S06/UNITS; S01 trong khối OrderDate riêng | Monthly trend + aligned volume/AIV drill; comparable-window year comparison; optional weekday context qua tooltip/drill. Click month thu hẹp cùng invoice population, không average monthly AIV | Date/comparison window; Buyer default. mart_sales_monthly/daily, dim_date; không thêm Product slicer vào S06 hiện mới có date contract | Size → comparable change → volume/AIV → calendar caveat |
| P2 — Product contribution | Tập SKU nào tạo value/units, ranking có công bằng? Cards S05/UNITS | Một ranking bar toggle Sales/Units; dynamic Pareto; exposure table có lifetime/comparable rank, first observed sale. Click SKU lọc table/trend; reset/clear TopN rõ ràng | Date/product, same-period option. mart_sales_product_daily + dim_product current; fact_invoice_line cho distinct invoices nếu cần | Contribution → quantity contrast → exposure-aware comparison |
| P3 — Sales attribution | Buyer và billing group có khác concentration? Card S05 và selected-role label; customer count chỉ diagnostic invoice population | Pareto/customer contribution; role contrast; table/drill phù hợp quyền truy cập. Chỉ một role tại một thời điểm, không stack/sum Buyer và Bill-to. Source drill không export contact data | Date/role. Existing buyer mart_customer_sales/summary; Bill-to lens từ invoice fact/headers cần future semantic validation vì mart hiện chỉ BUYER | Default buyer diversity → bill-to consolidation → limits of risk interpretation |
| P4 — Source-profit exceptions & coverage | Warnings nằm ở đâu, có bị hiểu sai là loss/data loss? Diagnostic cards negative-line count/rate, source LineProfit sum có nhãn; không GP card | Product exception table; monthly warning rate có denominator; coverage/order-invoice reference diagnostic nhỏ. Click warning segment là investigation, không default-filter toàn report thành VALID-only | InvoiceDate/product cho warnings từ fact_invoice_line; dq rule/record identity chỉ semijoin/dedup khi cần. Order reference diagnostics theo OrderDate dùng headers/staging, không gộp thành funnel | Preserve Sales → locate structured source warning → investigate → explain unsupported conclusions |

P3 Bill-to toggle, P4 source-profit optional diagnostic và mọi diagnostic mới cần được Owner chấp thuận cách trình bày/semantic scope trong task Power BI. Đây không phải phê duyệt measure mới hoặc thay YAML/KPI catalog.

### Measure-to-visual và filter guardrails

| Measure / diagnostic | Visual purpose | Input / aggregation / context |
|---|---|---|
| S05/S03/S04 | Overview amount/tax context, product/customer contributions | SUM đúng một eligible invoice-line population; không cộng các mart totals với nhau |
| S02 | Invoice volume/trend | Invoice headers; Product selection tương lai phải semijoin matching eligible invoice IDs, không SUM product_filtered_invoice_count qua products |
| S06 AIV | Overview time comparison | SUM S05 / S02 cùng dates/population; không AVG monthly/daily ratios. Không tự mở product/customer dimensions ngoài measure YAML đã duyệt |
| S01 | Separate order activity | Order headers/OrderDate; bao gồm order chưa invoice. Không gọi ratio S02/S01 là conversion |
| UNITS | Product/date volume lens | Source Quantity, không package conversion hoặc physical pieces giả định |
| C03 / role Sales attribution | Concentration | Một role và một eligible invoice population. Buyer mart hiện hữu; Bill-to từ source role keys của invoice, không current CRM remapping |
| Pareto/rank/exposure | Portfolio investigation | Derived diagnostics từ S05; denominator và TopN theo cùng filter, stable tie-break SKU ID. Không hardcode80/20 |
| Source LineProfit / negative rate | Optional exceptions, không official profit | Source field và COUNT negative eligible invoice lines / COUNT eligible invoice lines; không trừ warning Sales; không join violation rows trực tiếp làm nhân measures |
| Percentiles/active-day indices/CV | Tooltips/exploration | Descriptive statistics trên declared population; không thay definitions S05/S06 hoặc làm forecast guarantee |

## 5. Unsupported questions và dữ liệu cần bổ sung

| Chưa trả lời được | Thiếu gì / boundary |
|---|---|
| AIV giảm do giá, discount, campaign hay nhu cầu? | Cần kiểm soát basket/packaging mix, price/discount history, campaign/exposure và phương pháp causal riêng; aggregate identity không đủ |
| Công ty thực sự lỗ/GP/COGS bao nhiêu? | Chưa duyệt official profit/COGS/cost validity/accounting policies; Source LineProfit không thay thế |
| Recognized revenue, refund hoặc invoice đã thu tiền? | Recognition/refund/allocation contracts và nguồn tương ứng; không suy0 từ dữ liệu không hỗ trợ |
| Đơn nào canceled/lost/overdue, backorder đã giao đủ? | Lifecycle/status/as-of/fulfillment rules và line-to-line quantity evidence; không lấy header gap làm trạng thái |
| SKU nào sắp stockout/cần reorder? | Inventory/demand/lead-time policy và scope Inventory riêng; Sales đơn độc không đủ |
| Customer churn, lifetime value, campaign ROI | Customer/Marketing scope, observation windows và costs; không triển khai Customer Analytics trong task này |
| Historical customer category/brand/as-of segmentation | Historical SCD2 unresolved; observed-current labels không là attribute version tại ngày giao dịch |
| Forecast, mùa vụ chắc chắn, business days/holidays | Chỉ3 complete annual cycles, thiếu business calendar/holiday/control variables, cần validation ngoài sample |
| Doanh số tiền tệ quy đổi và physical standardized volume | Currency/FX và package-unit conversion chưa được duyệt |

## 6. Reproduce, validation và handoff

```powershell
cd D:\Code\Retail_Data_Platform\project1_Retail_Data_platform
.\.venv\Scripts\python.exe -X utf8 docs/analytics/sales-discovery-01/analyze.py --execute --capture-id c825b18e-fc62-4cf1-8837-b37b4c9f9668
.\.venv\Scripts\python.exe -X utf8 scripts/validate_repository.py
git diff --check
```

- SQL dùng psycopg named bind `%(pin)s`; runner bind canonical UUID, đọc connection profile private hiện có, không in credentials. Muốn xem một câu: tìm `-- Qxx` trong queries.sql và entry `queries.Qxx` trong results.json. Không chạy SQL file nguyên bản trong psql khi chưa thay named binds bằng parameters đúng client.
- Sessions retail_transform/retail_ingest đều `default_transaction_read_only=on`; không SQL Server connection, DDL/DML/GRANT/ingestion/dbt execution. GUC chỉ session: work_mem64MB, jit off, parallel0, enable_nestloop off, timeout120s. Header-view cardinality làm nested-loop query chậm ở exploratory run đầu; đổi query/session plan, không tạo index/materialization hoặc sửa warehouse để phân tích.
- Giữ runtime advisory locks941061/941062; analyses trong repeatable-read/read-only transaction. So before/after bằng fresh read-only transactions: content multiset hashes/counts cho17 Raw tables +8 metadata tables và19 warehouse tables không đổi. Hai header views được đọc qua version-stamped inputs và definition được lưu. MD5 ở đây là content drift detector, không cryptographic proof chống adversary.
- Check amount S03=S04+S05; invoice line membership so với header count; monthly fact/header/mart EXCEPT ALL mismatch0; product totals và từng customer role riêng cùng reconcile về S05; monthly sum khớp headline; DQ record accounting khớp six staging populations. SQL/query/config hashes lưu để phát hiện thay đổi ở lần reproduce sau.
- Không join marts khác grain để cộng Sales, không average ratios, không mix versions, không loại warnings khỏi eligible Sales, không gán missing source data thành0. Confidence về causal/forecast/accounting được giữ ở mức chưa xác minh.
- Handoff: Owner review8 candidates và bốn page purposes; triển khai P1/P2 trước, P3/P4 sau khi review role/diagnostic presentation. Airflow/Customer/Inventory và Power BI implementation chưa bắt đầu. Không nâng Certified status hoặc đóng parent phase.
