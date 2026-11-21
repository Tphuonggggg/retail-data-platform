# powerbi

[Hướng dẫn kết nối và quyền retail_bi_reader](access.md): POWERBI-ACCESS-01 runtime PASS trên `127.0.0.1:55434/retail_raw`, đúng 12 Sales objects. Dùng Database authentication bằng tài khoản reader, không dùng ingestion/transform/admin. Mật khẩu riêng chỉ lưu trong ignored private profile; không công bố trong tài liệu. [Model-level dbt grants đã kiểm chứng sau rebuild](persistent-grants.md) qua POWERBI-ACCESS-02; chưa có report/dashboard.

Sở hữu Power BI project/report files, dashboard assets, report-specific documentation và semantic/report tests khi triển khai. Không sở hữu SQL marts hoặc định nghĩa KPI chung.

**Chưa có report/dashboard assets.** Analytics trước đây chỉ có README và KPI documents: KPI chuyển nguyên nghĩa về [docs](../docs/requirements/kpi-definitions/README.md); marts thuộc [dbt](../dbt/README.md). Không tạo placeholder .pbix/.pbip hoặc report mới trong refactor.

Power BI bắt đầu sau Sales Warehouse/Mart runtime acceptance. Buyer/Bill-to/date basis/denominator theo [KPI Catalog](../docs/requirements/kpi-definitions/wwi-kpi-candidate-catalog.md).
