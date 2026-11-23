# Retail Sales Analytics

Mở [bản chính](RetailSalesAnalytics/RetailSalesAnalytics.pbip). Giữ đầy đủ Report, SemanticModel/TMDL, assets và hidden Detail pages. Original Sales_Dashboard.pbix là bản gốc của Owner, không xóa.

Model có14tables/9relationships/87measures, sáu imports theo version đã nghiệm thu. Bốn trang chính: Sales Performance, Product Contribution, Sales Attribution, Exceptions & Coverage; bốn detail pages phục vụ tra cứu. DAX đã được đối soát137checks; đây là kết quả lịch sử, không thay kiểm tra runtime mới. UI click/sync/reset/drill-through chưa nghiệm thu đầy đủ.

- [Cách đọc và sử dụng](dashboard-guide.md).
- [Grain, keys, DAX và date semantics](semantic-model.md).
- [Quyền BI reader](access.md), [grants sau rebuild](persistent-grants.md).
- [SELECT reconciliation](validation.sql), [runner](validate_sql.py).

TMDL là nguồn model hiện hành; không dùng generator cũ để tạo lại. Tests đọc bằng TOM kèm Desktop và fixture nhỏ trong tests/fixtures. Không commit cache, credentials hoặc source extracts. Không dùng bản sao .local/reopen-check làm report chính.
