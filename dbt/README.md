# dbt Sales Warehouse

21 models: six staging inputs, quality violations/status/quarantine, Orders/Invoices headers, Date/Customer/Product dimensions, OrderLine/InvoiceLine facts and five Sales marts. YAML trong config là nguồn business rules, measures, DQ thresholds và performance; không sửa để vượt validation.

## Cài đặt

Cài requirements.txt ở root. Private transform profile do run_dbt.py tạo trong .local/dbt/invocations; xem profiles.yml.example. Target retail_raw, localhost55434, retail_transform; không dùng postgres cho transformations. Role/schema provisioning nằm ở infrastructure/postgres/warehouse và cần authorization riêng.

## Lệnh

```powershell
.venv\Scripts\python.exe dbt/run_dbt.py validate --capture-id <uuid>
.venv\Scripts\python.exe dbt/run_dbt.py debug --input-kind FULL --capture-id <full-run-uuid>
.venv\Scripts\python.exe dbt/run_dbt.py compile --input-kind FULL --capture-id <full-run-uuid>
.venv\Scripts\python.exe dbt/run_dbt.py build --input-kind INCREMENTAL --capture-id <validated-version-uuid>
.venv\Scripts\python.exe dbt/run_dbt.py test --input-kind INCREMENTAL --capture-id <validated-version-uuid>
```

validate chỉ kiểm tra config. compile/build/test có runtime guards và có thể kết nối DB; build thay serving tables nên cần authorization/lý do vận hành. Không chạy khi chỉ cleanup. Không fallback latest/publication pointer. FULL dùng _run_id; INCREMENTAL dùng immutable parent/root/version và typed state functions.

Staging FULL dùng views; INCREMENTAL có thể materialize tables theo performance.yml để tránh repeated Function Scans. Runner truyền PGOPTIONS ở session, giữ inherited read-only safeguards; không ALTER SYSTEM. ANALYZE chỉ trên bảng transform sở hữu. Advisory runner lock ngăn hai transformations đồng thời; không phải atomic publication cho consumers.

## DQ, grains và grants

Giữ tests SQL trong tests/integration, tests/reconciliation và staging_fidelity.sql: pins, population accounting, keys, grains, historical unresolved handling, ratios, quarantine và per-row fidelity. Python regression ở tests/unit kiểm business configuration và model-level BI grants. acceptance.py/bi_grants_acceptance.py là các tiện ích kiểm chứng có kiểm soát, không phải bước build mặc định; đọc --help trước khi chạy fixtures/rebuild.

Sales theo approved eligibility/InvoiceDate; Order Count theo Orders/OrderDate. Buyer và Bill-to không cộng. Historical keys chưa resolve giữ U/NK/reasons, observed keys chỉ phục vụ current labels. Không suy COGS/revenue accounting từ source LineProfit.

Grants SELECT cho retail_bi_reader được khai báo ở đúng12 models, không ở project/folder level. Không mở Raw/staging/DQ/meta cho BI. Xem [quyền BI](../README.md), [model](README.md), [KPI](README.md) và [vận hành](README.md).

## Model grains và measures

Date: ngày/version; Customer/Product: observed key/version; int_order_header:OrderID; int_invoice_header:InvoiceID; fact_order_line:OrderID+OrderLineID; fact_invoice_line:InvoiceLineID. Marts daily/monthly/product-daily/customer-daily/customer-summary có grain riêng; không join fact-to-fact để cộng Sales hoặc cộng overlapping distinct counts.

| ID | Measure | Source / grain | Aggregation / ratio | Date | Eligibility |
|---|---|---|---|---|---|
|S01|Order Count|int_order_header / OrderID|count|OrderDate|is_order_eligible|
|S02|Invoice Count|int_invoice_header / InvoiceID|count|InvoiceDate|is_sales_eligible|
|S03|Invoice Amount Including Tax|fact_invoice_line / InvoiceLineID|sum|InvoiceDate|is_sales_eligible|
|S04|Invoice Tax Amount|fact_invoice_line / InvoiceLineID|sum|InvoiceDate|is_sales_eligible|
|S05|Invoiced Sales Before Tax|fact_invoice_line / InvoiceLineID|sum|InvoiceDate|is_sales_eligible|
|S06|Average Invoice Value Before Tax|fact_invoice_line / InvoiceLineID|S05/S02|InvoiceDate|is_sales_eligible|
|UNITS|Source Units Sold|fact_invoice_line / InvoiceLineID|sum|InvoiceDate|is_sales_eligible|
|C03|Sales by Selected Customer Role|fact_invoice_line / InvoiceLineID|sum|InvoiceDate|is_sales_eligible|
|MOM|Month-over-Month Captured Sales Growth|mart_sales_monthly / month|S05/S05|InvoiceDate|is_sales_eligible|
|YOY|Year-over-Year Captured Sales Growth|mart_sales_monthly / month|S05/S05|InvoiceDate|is_sales_eligible|

Các công thức/NULL/zero policies và dimension eligibility đầy đủ nằm trong config/measures.yml; config/business_rules.yml và quality_rules.yml là contracts executable, không phải historical reports. Zero denominator giữ NULL, money reconciliation tolerance0, ratio1e-12. Sales dùng invoice eligibility, WARNING không tự bị loại; invalid/quarantine không contribute. Profit/COGS/refund accounting chưa được certified.

## Thiết kế SCD deferred — không phải runtime đã hoàn tất

### ADR-SCD-01 — Product Attribute Tracking (D01)

Tập Type 2 của dim_product chỉ gồm **UnitPackageID, OuterPackageID, QuantityPerOuter**. Các analytical attributes còn lại dùng Type 1 **nếu đã được duyệt đưa vào dimension**. Không tự đưa thuộc tính Excluded hoặc technical/audit metadata thành Type 1; CustomFields/Tags tiếp tục ngoài analytical scope. NK và metadata không là Type1 descriptive attributes.

Chỉ tracked Type2 attributes kích hoạt analytical historical version; Type1 changes không tự tạo SCD2 episode. Không thay transaction UnitPrice bằng master product price. Type1 correction lên các versions hiện có phải được đánh giá impact trước khi triển khai.

### ADR-SCD-02 — Persistent Surrogate Key Registry (D02)

Persistent Registry cấp và quản lý **Opaque SK** cho analytical versions của Customer/Product. Natural key, source occurrence identity, analytical version identity và warehouse SK là các khái niệm riêng. Không dùng ROW_NUMBER theo thời gian làm durable SK; không mặc định CustomerID + ValidFrom unique.

Registry phải có stable mapping, backup/recovery, version supersession và integrity validation. SK stability chỉ được claim khi registry/identity evidence đầy đủ. Boundary corrections, split/merge và late corrections phải có rekey/restatement policy; không đổi nghĩa SK đang referenced.

### ADR-SCD-03 — Whole-Day Analytical Consensus (D03)

Date-only facts chỉ resolve khi chứng minh **full relevant-day coverage** và duy nhất **một analytical version identity** cho toàn khoảng thời gian sự kiện có thể phát sinh. Thiếu analytical validity/coverage hoặc có nhiều analytical episodes phù hợp thì unresolved. Không dùng beginning/end-of-day proxy.

Nhiều source occurrences không nhất thiết là nhiều analytical versions nếu được hợp nhất hợp lệ theo tracked attributes và validity. Không gộp noncontiguous episodes chỉ vì cùng values. Integrity multi-match phải chặn publication trong scope bị ảnh hưởng.

### ADR-SCD-04 — Reconciled Hybrid Cutover (D04)

Reconcile verified WWI temporal history với forward-observed changes. Bảo toàn source-backed/observation-backed lineage; source system-time, observation-time và analytical validity là các ngữ nghĩa riêng.

Không invent business-effective timestamps/intermediate changes, không double-create analytical versions khi cùng thay đổi xuất hiện ở history và observation. Full reload không được làm mất forward evidence. Không hòa giải được thì giữ trạng thái chưa xác minh, không ép nối timeline.

### ADR-SCD-05 — Exact Temporal Precision (D05)

Bảo toàn exact **100 ns** representation của SQL Server temporal values liên quan tới source identity và validity assessment. Chưa phê duyệt PostgreSQL physical datatype.

Không phụ thuộc duy nhất vào microsecond timestamps cho identity hoặc interval predicates khi precision loss có thể làm sai lookup. Phân biệt source exact values với timestamps dùng display/ordinary analytics. Phải kiểm chứng round-trip, boundary predicates, collisions, sentinels và open-ended intervals.

### ADR-SCD-06 — Controlled Unresolved Publication & Certified Mart Gate (D06)

Core facts được giữ unresolved historical dimension references **có kiểm soát**, giữ source population và reconciliation. Certified analytical marts phải qua quality/coverage gates đã được xác định và phê duyệt. Integrity multi-match do history/identity/interval phải chặn publication ở scope bị ảnh hưởng.

Phân biệt missing reference, historical coverage gap, date-only ambiguity, precision error và integrity violation. Unknown/unresolved không là successful historical match. Không silent fallback current/earliest, không drop source fact chỉ vì unresolved dimension lookup. Marts không được claim historical grouping đầy đủ khi chưa qua coverage gate.

Không tự chốt physical algorithms/cutover hoặc coi system-time làbusiness effective time. Runtime hiện giữ unresolved historical keys/reasons và observed-current references; không tuyên bố historical lookup đầy đủ.

Type1 correction cần impact scope, audit/reconciliation và rollback riêng; không tự overwrite mọi version hoặc biến AccountOpenedDate correction thành episode SCD2. Packaging Type2 whitelist không mở rộng sang Tags/CustomFields. Các giá trị cutover, historical fallback, schema/algorithm chưa triển khai không được tự chốt chỉ từ thiết kế này.
