# powerbi

## POWERBI-SALES-01 — POWERBI_SALES_PARTIAL

Mở [RetailSalesAnalytics.pbip](RetailSalesAnalytics/RetailSalesAnalytics.pbip). Đã triển khai definitions cho4 trang/72 containers/77 measures, dùng6 approved PostgreSQL objects; Desktop mở/reload được. **Chưa phải dashboard hoàn tất:** model mới chưa Import được dữ liệu qua API, baseline DAX BLANK, một visual Attribution còn lỗi; interactions/refresh chưa nghiệm thu. [Validation và blockers](validation.md).

- [Semantic model, grains và relationships](semantic-model.md).
- [Hướng dẫn4 trang và bước Desktop còn thiếu](dashboard-guide.md).
- [SQL kiểm chứng bằng reader](validation.sql), [results](sql-validation.json), [77 DAX definitions](measures.dax), [15 DAX test contexts](dax-validation-queries.json).
- [Screenshots4 trang trước refresh](qa/) là evidence chưa hoàn tất, không thay report hoặc chứng minh số liệu.

Original `Sales_Dashboard.pbix` còn nguyên; backup trong ignored `.local/powerbi-sales-01`, SHA trong [inspection](original-inspection.json). PBIX và `.pbi` cache bị Git ignore vì chứa imported business data; chỉ definitions/assets/evidence aggregates được track. Không thay Raw/DW/source, không chạy ingestion/dbt hoặc publish.

[Hướng dẫn kết nối và quyền retail_bi_reader](access.md): POWERBI-ACCESS-01 runtime PASS trên `127.0.0.1:55434/retail_raw`, đúng 12 Sales objects. Dùng Database authentication bằng tài khoản reader, không dùng ingestion/transform/admin. Mật khẩu riêng chỉ lưu trong ignored private profile; không công bố trong tài liệu. [Model-level dbt grants đã kiểm chứng sau rebuild](persistent-grants.md) qua POWERBI-ACCESS-02.

Sở hữu Power BI project/report files, dashboard assets, report-specific documentation và semantic/report tests khi triển khai. Không sở hữu SQL marts hoặc định nghĩa KPI chung.

KPI contracts thuộc [docs](../docs/requirements/kpi-definitions/README.md); marts thuộc [dbt](../dbt/README.md). Các thông tin trước đây chưa có report là snapshot trước POWERBI-SALES-01; current authoring status ở đầu trang, chưa nghiệm thu chức năng.

Power BI bắt đầu sau Sales Warehouse/Mart runtime acceptance. Buyer/Bill-to/date basis/denominator theo [KPI Catalog](../docs/requirements/kpi-definitions/wwi-kpi-candidate-catalog.md).
