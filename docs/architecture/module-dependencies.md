# Module Dependencies

**Planned — Not implemented yet.** Mũi tên là phụ thuộc thiết kế, không phải import code đã tồn tại.

```mermaid
flowchart LR
  C[WWI source contract / business decisions] --> IG[ingestion]
  W[WWI SQL Server read-only] --> IG
  IG --> ST[storage raw/staging]
  ST --> TR[transformation dbt/SQL]
  TR --> DW[storage warehouse PostgreSQL]
  DW --> AN[analytics marts/Power BI]
  OR[orchestration Airflow] -. điều phối .-> IG
  OR -. điều phối .-> TR
  DQ[data-quality] -. kiểm tra .-> IG
  DQ -. kiểm tra .-> TR
  DQ -. đối soát .-> DW
  MO[monitoring] -. quan sát .-> OR
  TS[tests] -. xác minh .-> IG
  TS -. xác minh .-> TR
  IF[infrastructure] -. môi trường .-> IG
  IF -. môi trường .-> DW
```

Sales pipeline từ extract đến mart, Airflow, data quality và monitoring được hoàn thiện trước khi mở rộng Customer rồi Inventory Movements. Quality checks cơ bản là dependency của ingestion/warehouse, không chờ Phase 6. Các module không phụ thuộc ngược từ nguồn vào analytics. `docs` ghi source contract và quyết định; `.github` chứa CI sau khi Git/code được thiết lập; `scripts` hỗ trợ task cụ thể.