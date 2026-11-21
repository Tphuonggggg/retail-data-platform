# Dashboard guide — bản triển khai chưa nghiệm thu dữ liệu

Mở [RetailSalesAnalytics.pbip](RetailSalesAnalytics/RetailSalesAnalytics.pbip) bằng Desktop. Bản gốc `Sales_Dashboard.pbix` được bảo toàn và backup trong ignored `.local/powerbi-sales-01`. Không dùng các screenshots như dashboard thay thế.

## Bốn trang

| Trang | Visuals đã định nghĩa | Slicers/interaction | Runtime status |
|---|---|---|---|
| 01 Sales Performance | 4 cards; monthly Sales/PY line; Invoice Count/AIV dual axis; exact decomposition bars; monthly matrix; dynamic narrative | Year/Date, page navigation, clear slicers | Chưa có Import data; chưa đối soát DAX |
| 02 Product Contribution | 4 cards; Pareto/80% line; TopN Sales và Units bars; scatter; history-aware rank matrix | Year/Date/Product/TopN/rank basis cho detail | Chưa có Import data; scroll/rank interactions chưa nghiệm thu |
| 03 Sales Attribution | 4 cards; aligned Buyer và Bill-to bars; cumulative concentration; selected-role detail matrix | Year/Date/Role; hai bar charts không cross-filter nhau | Chưa có Import data; scale consistency/filter behavior còn cần kiểm |
| 04 Exceptions & Coverage | 4 cards; negative LineProfit by Product; monthly warning count/rate; weekday activity; warning matrix; direct order-reference matrix; blocked-data notice | Year/Date, product drill qua warning chart | Warning fields đủ; backorder classification chưa được hỗ trợ |

Tổng 72 visual containers gồm charts/cards/matrices/slicers/text/buttons. Tất cả analytical visuals bind vào columns/measures thật, không background charts. Background nguyên bản được trích từ Owner PBIX; theme navy/blue/teal/orange, sidebar buttons thật có PageNavigation, active-page styling; reset dùng ClearAllSlicers. Có thể cần Ctrl+click khi authoring trong Desktop. Chưa chứng minh thao tác click/sync/drill-through bằng runtime tests.

Không cross-page sync mặc định để tránh chọn Product/Role vô tình đổi population các trang khác. Tooltips cơ bản đã bind vào scatter; custom tooltip/drill-through pages chưa triển khai. Không Region/Store/Category giả. Các cards trống hiện tại thể hiện model chưa được refresh, không phải doanh số bằng 0.

## Thao tác còn cần để hoàn thành

1. Trong Desktop mở project trên, bấm **Refresh** để xử lý đủ 6 imported tables và các calculated tables. Nếu hỏi credential, dùng Database / `retail_bi_reader` với mật khẩu local đã đồng bộ; không dùng postgres/transform/ingest. Private profile không tự đồng bộ vào Power BI credential store.
2. Nếu còn credential cũ cho đúng server/database, sửa credential của riêng nguồn đó. Không tắt privacy/TLS hoặc thay security settings. Bản source cuối dùng navigation, không còn native query identity phụ.
3. Save project; khi có data, chạy [bộ DAX test](dax-validation-queries.json) bằng [query_model.ps1](query_model.ps1), đối soát với [SQL](validation.sql). Chỉ sau khi headline đúng mới kiểm các filtered contexts và charts.
4. Page1 chọn năm2016: Jan–May Sales YoY −0,20%, invoices +0,90%, AIV −1,09% theo SQL. Page2 clear filters: top20% share64,52%, 69/227 SKU đạt80%, Top10 overlap0. Page3 clear filters: top5 Buyer1,07%, Bill-to63,75%, hai totals đều172261341,20. Đây là SQL benchmarks, không hardcode vào DAX.
5. Page4 kiểm4626 negative eligible invoice lines, warning rate denominator228265 lines,178 zero-transaction Sundays. Không gọi warnings là official losses hoặc Chủ nhật không giao dịch là thiếu dữ liệu. Direct-link gaps không là failed fulfillment.
6. Kiểm tất cả navigation/slicers, empty periods, matrix totals, TopN, product/multi-product và role contexts; chụp lại4 trang có data. Đo refresh/model size/query times thật, save rồi reopen. Chưa thực hiện các bước này nên chưa được nghiệm thu dashboard.

## Backorder extension chờ phê duyệt riêng

12 objects hiện tại không chứa BackorderOrderID. [SELECT proposal](proposals/order_reference_extension.sql) cho view `sales_marts.mart_order_invoice_reference`, grain một eligible OrderID/version, chỉ source FK references, không lifecycle status. Cần Owner phê duyệt object thứ13 + SELECT reader + dbt model/tests và điều chỉnh allowlist/preflight; chưa tạo view, chưa chạy dbt/GRANT. Source dependencies là existing order header, invoice header và staging Orders; BI reader chỉ được đọc view mới nếu được duyệt, không được cấp staging. Chỉ sau runtime reconciliation mới bổ sung linked/unresolved categories.
