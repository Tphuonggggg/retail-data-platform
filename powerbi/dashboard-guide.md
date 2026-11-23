# Hướng dẫn Retail Sales Analytics — bản redesign

Mở [RetailSalesAnalytics.pbip](RetailSalesAnalytics/RetailSalesAnalytics.pbip). Dữ liệu có sẵn, đúng version `c825b18e-fc62-4cf1-8837-b37b4c9f9668`; không cần chạy dbt/ingestion để xem. Kết nối theo [hướng dẫn reader](access.md); không lưu mật khẩu trong Git/report definitions.

| Trang chính | Nội dung |
|---|---|
| Sales Performance | Bốn KPI Sales/Invoices/AIV/Units; monthly Sales/PY trend lớn và volume/AIV cùng timeline. Monthly matrix/decomposition ở Explore details. |
| Product Contribution | Pareto theo rank số/đường 80%, hai TopN bars. Ranking matrix và scatter ở detail. |
| Sales Attribution | Concentration curve chủ đạo; hai bars có cùng trục 0–100% và nhãn tỷ trọng. Đây là cùng Sales theo hai roles, không cộng. |
| Exceptions & Coverage | Warning concentration, monthly count/rate, clustered weekday counts đủ Sunday. Không gọi negative LineProfit là certified accounting loss. |

## Filter và navigation

- Year/Date đồng bộ giữa bốn main pages và detail. Product chỉ đồng bộ Product overview/detail. TopN đồng bộ Product/Attribution; Top5 cards luôn là Top5.
- Attribution role ở Customer Roles detail, điều khiển matrix. Hai role charts overview luôn độc lập để so sánh, không bị role selector làm mất một phía.
- Explore details là page navigation; không đồng nghĩa với truyền data-point filter. Drill-through context menu chỉ áp dụng khi visual có field phù hợp. Monthly detail nhận Date.month_start; Product detail nhận Product.stock_item_name. Customer detail khai báo theo Buyer.customer_name; không khẳng định mọi Bill-to point có cùng drill target. Back trả về selection nguồn.
- Reset filters dùng ClearAllSlicers, không restore bookmark defaults. Sync group có thể làm date/TopN ở trang khác đổi theo. Không hứa reset xóa mọi external/drill-through filter.
- Chart selection cấu hình DataFilter giữa các charts thông thường; Pareto numeric-rank axis không lọc TopN bars, các charts Buyer/Bill-to không lọc chéo nhau. Tooltips giữ context. Các hành vi click thực tế còn chờ kiểm thử.

## Cách đọc

2016 chỉ có January–May. PY dịch cùng các ngày đang chọn lùi 12 tháng; không so full2016 với full2015. Decomposition cần một calendar year; BLANK khi nhiều năm là guard có chủ đích. Trend vẫn hiển thị monthly comparisons qua nhiều năm.

Sales là invoiced sales before tax theo InvoiceDate; không tự gọi recognized revenue/net profit. Chưa có currency contract để gắn USD/BRL/VND. Units là source quantity, không bảo đảm cùng packaging. AIV là ratio của totals, không phải trung bình AIV con.

Ranks dùng product selection hiện hành. Lifetime bỏ Date filter; latest captured YTD dùng năm cuối dữ liệu, không phải năm máy. Zero overlap khác empty population. Zero-transaction Sundays không phải missing calendar dates. Order chưa direct invoice không mặc nhiên fulfillment failure; BackorderOrderID chưa mở rộng vào model.

## Nghiệm thu

[Báo cáo redesign](dashboard-guide.md) có ảnh trước/sau, inventories và checklist. **137 checks/12 tests PASS không thay UI click tests.** Original PBIX được bảo toàn; không publish và không thay PostgreSQL/Raw/dbt/ingestion.
