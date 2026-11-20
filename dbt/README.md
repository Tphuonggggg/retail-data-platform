# Sales Analytics — dbt runtime đã nghiệm thu

## INGEST-INCR-01 — explicit input versions

Runner thêm `--input-kind INCREMENTAL --capture-id <validated-version-uuid>`. FULL vẫn mặc định và giữ guard cũ. Incremental guard kiểm tra parent/root/scope/contract/VALIDATED; `sales_raw_input()` chọn đúng sáu typed state functions trên cùng UUID cho staging và fidelity test. Không dùng publication pointer/latest, không mix versions. YAML rules/measures, Buyer/Bill-to, grains, historical U/NK/reasons và observed-current references giữ nguyên.

Incremental dùng session `work_mem=64MB`, max_parallel_workers_per_gather=0, jit=off, threads=1; không ALTER SYSTEM/container. Truyền qua libpq PGOPTIONS và giữ inherited read-only options; installed adapter không nhận profile key `options`. Run-start kiểm tra actual settings, sai thì fail. `--work-mem-mb 4|16|64` cho benchmark có kiểm soát; FULL mặc định4MB. Memory này tính trên từng operation, không phải total-process cap. EXPLAIN phát hiện Function Scan ước lượng5 dòng so với70510 thực tế; query64MB riêng lẻ0,62s chưa giải quyết toàn graph. Materialized staging/statistics và jit=off xử lý regression; probe fact full-output4,25s, enable_hashjoin=off bị timeout12s nên không áp dụng. Table models do transform sở hữu được ANALYZE sau build; không ANALYZE Raw. Các lần dừng được ghi trong evidence. Không thêm index/hint/đổi grain để che lỗi.

Rebuild toàn bộ Sales dependency graph là correctness baseline; không thêm dbt incremental materialization. `performance.yml: incremental_staging_materialization: table` cache sáu typed staging của version và chạy ANALYZE trên đúng staging do retail_transform sở hữu. FULL vẫn dùng staging views. Incremental vì vậy có 21 models gồm 2 views/19 tables. Đây là staging hiện hành phục vụ planner/column pruning, không thêm Raw snapshots. Đổi này xử lý regression từ Function Scan cardinality và repeated projection; session64MB riêng lẻ chưa đủ bảo đảm full graph. Không đổi ruleset/measure hash. DQ được tính lại theo version và ruleset; artifacts invocation/YAML và immutable input cho phép giải thích/tái tạo evaluation trước. Serving tables vẫn local development/Uncertified, không phải atomic analytical publication; dùng advisory runner lock và chưa phục vụ BI.

```powershell
.\.venv\Scripts\python.exe dbt/run_dbt.py build --input-kind INCREMENTAL --capture-id c825b18e-fc62-4cf1-8837-b37b4c9f9668
.\.venv\Scripts\python.exe dbt/run_dbt.py test --input-kind INCREMENTAL --capture-id c825b18e-fc62-4cf1-8837-b37b4c9f9668
.\.venv\Scripts\python.exe tests/integration/incremental_acceptance.py --execute --with-sales --version-id c825b18e-fc62-4cf1-8837-b37b4c9f9668 --output .local/incremental-reconciliation.json
```

Xem [workflow/limitations](../ingestion/README.md#ingest-incr-01--sales-snapshot-diff-2026-11-20) và [runtime evidence](../docs/audits/ingest-incr-01/evidence.json). Không thay accepted KPI hoặc tự resolve historical SCD2 bằng current dimension. Missing Product trong fixture tạo relationship violation/quarantine, giữ source key/history U và loại contribution khỏi eligible Sales; không tự tạo dimension giả.

**DBT_SALES_RUNTIME_ACCEPTED — 2026-11-20.** PostgreSQL 18.7, dbt-core 1.11.17, dbt-postgres 1.11.0, Python 3.12.10. Đã build 21 models: 8 views và 13 tables; 69 dbt data tests PASS. Đây là biến đổi local-development của unpublished capture, **không phải Certified publication hoặc bằng chứng source point-in-time consistency**.

## Phạm vi và capture

Sales/Invoicing; Customer/Product chỉ là dimensions phục vụ Sales. Không CustomerTransactions/payment allocation, customer-repeat/profile analytics, Inventory/Purchasing/Finance, historical SCD2 runtime, incremental, Airflow hoặc Power BI report.

Pin bắt buộc: `5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8`. Task gọi đây là capture; về mặt Raw schema, pin này chính là `ingestion_meta.runs.run_id` và `raw.*._run_id`. Metadata `runs.capture_id` riêng được giữ nguyên, không dùng thay run pin. Mọi source predicate dùng chính xác `_run_id`; không fallback latest, không đọc các serving views đang rỗng. Assertion kiểm succeeded/full/contract/scope/all-11 audits, rồi kiểm live counts sáu Sales dependencies. Initial/final typed digest kiểm lại đầy đủ 11 objects/939208 rows qua ingestion verifier: PASS; control metadata và publication pointer không đổi.

Source consistency vẫn UNVERIFIED. Publication ledger0, pointerNULL. Không publish hoặc thay source. Database `retail_raw` tại `127.0.0.1:55434`; ordinary transformations dùng `retail_transform` không admin, chỉ SELECT Raw/meta, sở hữu dw_staging/dw_intermediate/dw_core/sales_marts/dq/dbt_sales_test. Provisioning privileged đã được Owner phê duyệt và thực thi riêng; [infrastructure evidence](../infrastructure/README.md#dbt-sales-01--khôi-phục-runtime-ngày-2026-11-20). Không chạy lại provisioning.

## Cấu trúc và dependencies

```text
dbt_project.yml / profiles.yml.example
configuration.py           closed YAML validator/compiler
execute.py / run_dbt.py     explicit pin, execution lock, private dbt invocation
config/                    business_rules, measures, quality_rules, performance
models/staging/            six typed capture-pinned views + Raw lineage
models/quality/            violations → status → quarantine
models/intermediate/       full Orders/Invoices header populations
models/core/               Date/Customer/Product + OrderLine/InvoiceLine facts
models/marts/              Sales daily/product/customer/summary/monthly
macros/                    registered operations, capture and quality gates
tests/unit/                fast deterministic Python/Jinja tests
tests/integration/         DQ/pins/grains/keys/lookup gates
tests/reconciliation/      independent per-row Raw/fact comparisons
acceptance.py              real PostgreSQL fixtures, independent metrics, content snapshots
benchmark.py               SELECT-only EXPLAIN ANALYZE on frozen compiled SQL
```

Staging → DQ → headers/dimensions → facts → marts. Required staging remains complete; no DISTINCT or filtering to hide bad source rows. Core facts keep rows with their flags; eligibility filters belong to analytical populations. Header populations come directly from Orders/Invoices, not their lines or invoiced orders. Buyer/Bill-to are separate invoice fields; no invoice-line/order-line or fact-to-fact join.

## Installation và execution

Dependencies chỉ ở [root requirements](../requirements.txt). Dùng project-local venv hiện có; không cài global. Profiles/secret nằm trong ignored `.local/dbt`; runner không ghi password vào command arguments/logs/Git.

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
$pin = '5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8'
.venv\Scripts\python.exe dbt/run_dbt.py validate --capture-id $pin
.venv\Scripts\python.exe dbt/run_dbt.py debug --capture-id $pin
.venv\Scripts\python.exe dbt/run_dbt.py compile --capture-id $pin
.venv\Scripts\python.exe dbt/run_dbt.py build --capture-id $pin
.venv\Scripts\python.exe dbt/run_dbt.py test --capture-id $pin
```

Không cần dbt packages/deps. Build là full rebuild của dbt-owned models, không reload/truncate Raw. Runner kiểm canonical UUID, target/role và capture trước mọi dbt command; giữ session advisory lock 941062 trong suốt invocation để tránh hai builds khác config đè nhau.

**YAML loading có thực:** runner dùng SafeLoader có duplicate-key rejection → schema/enum validation → compile registered operations → canonical SHA256 → tạo invocation project riêng trong `.local/dbt/invocations/<uuid>` với `vars.sales_contract` trong dbt_project.yml. Model/macro/test code được snapshot vào invocation này; dbt thực sự đọc vars đó. Không giả định dbt tự đọc config/*.yml, không truyền SQL tự do từ YAML. Execution metadata/manifest/run_results/compiled SQL được giữ private để đối chiếu. `--config-dir` chỉ dành cho cấu hình thí nghiệm đã được validate.

## Cấu hình nghiệp vụ và measures

- [business_rules.yml](config/business_rules.yml): các BRD Sales được hỗ trợ, date basis OrderDate/InvoiceDate, amount basis ExtendedPrice−TaxAmount, một customer role BUYER mặc định hoặc BILL_TO; optional NULL và zero/negative được giữ, không invent statuses/invalid monetary domains.
- [measures.yml](config/measures.yml): S01/S02/S03/S04/S05/S06, source units, customer-role sales, task-scoped captured MoM/YoY. Source fact/grain/aggregation/dependencies/eligibility/date/null/divide-by-zero/dimensions/version bắt buộc và được validate.
- Ratio dùng tổng tử / tổng mẫu; denominator0 → NULL. Amount tolerance = 0; ratio-only absolute tolerance = 1e-12 cho sai khác scale phép chia PostgreSQL numeric so với Python Decimal, không áp dụng vào tiền.
- Invoice quantities/amounts lấy từ lines; invoice count từ mọi eligible invoice headers. Order count theo OrderDate, giữ cả order chưa invoice. Negative/zero không tự bị loại. Không recognized revenue, official profit/COGS, refund inference hoặc payment allocation.
- S05 là Invoiced Sales Before Tax. Units Sold là source Quantity, không tự quy đổi package/outer units. Không tự đặt currency BRL từ dự án/dataset trước.
- Product-filtered invoice_count là DISTINCT InvoiceID trong mỗi date/product; không cộng thành enterprise Invoice Count.
- Customer mart giữ grain đã duyệt date/customer/role. Summary đáp ứng yêu cầu một customer/role; không đổi grain logical mart cũ. Chỉ một role trong một build, không UNION cả hai rồi SUM.
- MoM/YoY dùng dense calendar months và Raw-derived amount; thiếu comparator, comparator0 hoặc kỳ biên chưa nằm trọn trong captured date range → NULL. Coverage flag không chứng nhận source completeness. Không SUM growth rates hoặc average daily AIV.

## DQ, flags và quarantine

[quality_rules.yml](config/quality_rules.yml) có 108 enabled rules. Supported types: not_null, unique (registered source PK), accepted_values (typed non-NULL domain), min_value/max_value/between (finite numeric), relationship (compatible source PK), date_order và registered_expression credit_note_review. Không nhận free SQL/unknown types/unknown columns; business IDs và measure IDs/dependencies có registry đóng.

Thêm validation rule bằng declarative fields rule_id/object/column/type/enabled/severity/action/expected/message; ID phải unique. Thêm operation hoặc business/measure ID mới cần đăng ký code và tests, không dán SQL vào YAML. Domain chưa có bằng chứng chỉ warning; current source LineProfit âm không bị coi invalid.

- VALID: không violation; WARNING: có warning nhưng không ERROR; INVALID: có ERROR.
- is_valid = status khác INVALID; has_warning độc lập; quarantine chỉ khi rule action quarantine. WARNING không tự INVALID.
- Actions flag/quarantine/fail_pipeline khác nhau. Fatal violations được lưu và gate chặn downstream; macro fatal/nonfatal đã được fast-test.
- is_sales_eligible/is_order_eligible xét riêng transaction và parent header; record VALID có thể không eligible khi parent invalid mà không tự quarantine record đó.
- dq.record_status: một row/source occurrence/ruleset. dq.validation_violations: nhiều violated rules/record. dq.quarantine_records: một reference/record, không copy Raw payload.
- actual_value dùng NULL hoặc md5 representation; original value lấy bằng Raw lookup, không in PII vào logs.
- Parent membership sets được deduplicate chỉ để biểu diễn boolean existence và tránh fan-out; source PK duplicates vẫn là fatal rule, không deduplicate facts.
- Staging giữ capture_id, source_object, source_business_key, _raw_row_ordinal, record_identity, ruleset_version, evaluation_id. Downstream giữ hoặc tái dựng được lineage qua headers/facts. Evaluation ID deterministic theo run pin/ruleset; rerun không tạo duplicate logical records.
- Monetary/numeric giữ exact types; datetime2(7) authoritative là TEXT COLLATE C/seven digits. Source periods không được gán thành business effective time; không có timestamp presentation conversion âm thầm.

```sql
SELECT source_object,dq_status,count(*)
FROM dq.record_status GROUP BY 1,2 ORDER BY 1,2;
SELECT rule_id,severity,action,count(*)
FROM dq.validation_violations GROUP BY 1,2,3;
SELECT * FROM dq.quarantine_records;
-- Exact Raw lookup for a Sales.InvoiceLines violation:
SELECT r.*
FROM raw.sales_invoicelines r
JOIN dq.validation_violations v
  ON r._run_id=v.capture_id AND r._row_ordinal=v._raw_row_ordinal
WHERE v.source_object='Sales.InvoiceLines'
  AND v.rule_id='SALES_INVOICELINES_LINE_PROFIT_MIN_VALUE'
LIMIT 1;
```

Ruleset SHA256: `39d3afd2fef434eb82e656480892b958e0d5fa9d34e2086eeda0bffb0dd3000f`.
Measure SHA256: `86ac5adfd16901e62f9d100ba567b9e60bca60b9ead94c54ddcb3ecddfc69e91`.
Changing config changes hashes and rebuilds affected outputs. Thí nghiệm disable LineProfit warning: ruleset fc80a52a… → 604672 VALID/0 warnings, Sales unchanged; default đã được restore. Evidence cũ giữ trong private invocation artifacts, không trộn versions trong output cuối.

## Models runtime — rows, grain, ownership

| Model | Grain | Materialization | Rows | Execution |
|---|---|---|---:|---:|
| dq.quarantine_records | quarantined occurrence/ruleset | table | 0 | 0.079s |
| dq.record_status | source occurrence/ruleset | table | 604672 | 1.137s |
| dq.validation_violations | source occurrence/rule/ruleset | table | 4626 | 13.13s |
| dw_core.dim_customer | current CustomerID/capture | table | 663 | 0.083s |
| dw_core.dim_date | date | table | 1247 | 0.091s |
| dw_core.dim_product | current StockItemID/capture | table | 227 | 0.071s |
| dw_core.fact_invoice_line | InvoiceLineID | table | 228265 | 0.932s |
| dw_core.fact_order_line | OrderLineID | table | 231412 | 0.829s |
| sales_marts.mart_customer_sales | InvoiceDate/customer/selected role | table | 66463 | 0.462s |
| sales_marts.mart_sales_customer_summary | customer/selected role | table | 663 | 0.051s |
| sales_marts.mart_sales_daily | calendar date | table | 1247 | 0.405s |
| sales_marts.mart_sales_monthly | calendar month | table | 41 | 0.208s |
| sales_marts.mart_sales_product_daily | InvoiceDate/StockItemID | table | 141561 | 0.352s |
| dw_intermediate.int_invoice_header | InvoiceID | view | 70510 | 0.069s |
| dw_intermediate.int_order_header | OrderID | view | 73595 | 0.048s |
| dw_staging.stg_sales_customers | one current source PK/capture | view | 663 | 0.117s |
| dw_staging.stg_sales_invoicelines | one current source PK/capture | view | 228265 | 0.053s |
| dw_staging.stg_sales_invoices | one current source PK/capture | view | 70510 | 0.035s |
| dw_staging.stg_sales_orderlines | one current source PK/capture | view | 231412 | 0.06s |
| dw_staging.stg_sales_orders | one current source PK/capture | view | 73595 | 0.033s |
| dw_staging.stg_warehouse_stockitems | one current source PK/capture | view | 227 | 0.034s |

Mọi grain/key/pin test PASS; per-model execution times lấy từ stable rerun run_results.json, không phải ước tính. Physical output sizes tổng ở các materialized tables: 459653120 bytes; views không copy Raw.

Customer/Product keys nhận diện observed current capture, không phải durable analytical episode registry. Facts giữ historical keys NULL/U với source NK/reason/lineage; observed relationship keys riêng được kiểm tới đúng natural key/date. Invoice historical unresolved: 228265 cho mỗi Buyer/Bill-to/Product role; order Buyer/Product 231412 mỗi role. Đây là SCD2-deferred, không source orphan và không historical current/earliest fallback. Marts group theo source IDs/date, Uncertified; source NK không được join vào mọi historical versions.

## Ba mức tests và kết quả

```powershell
# Level 1: 27 fast tests, khoảng 1.5s; không DB/materialization.
.venv\Scripts\python.exe -m unittest discover -s dbt/tests/unit -p test_configuration.py -v
# Toàn bộ offline regression, gồm 126 tests cũ + 27 tests mới:
.venv\Scripts\python.exe scripts/run_checks.py
# Level 2: explicit real PostgreSQL synthetic fixtures, chỉ schema dbt_sales_test:
.venv\Scripts\python.exe dbt/acceptance.py fixtures --execute --output .local/sales-fixtures.json
# Level 3: real accepted capture:
.venv\Scripts\python.exe dbt/run_dbt.py build --capture-id $pin
.venv\Scripts\python.exe dbt/acceptance.py reconcile --execute --output .local/sales-reconcile.json
.venv\Scripts\python.exe dbt/acceptance.py snapshot --execute --output .local/sales-snapshot.json
```

Level2 fixtures labelled SYNTHETIC_EXAMPLE_ONLY: 5 records → VALID2, WARNING1, INVALID2; 4 violations, 2 actual quarantine rows; one valid-but-parent-ineligible record not quarantined. Additional duplicate-occurrence check2 and missing-capture rejection PASS. Latest fixture prefix `dbt_sales_test.fixture_cfe6af032542` identifies records/violations/status/quarantine tables; re-running fixtures creates a new isolated prefix and preserves earlier evidence. Không insert synthetic records vào Raw.

Real DQ: 604672 evaluated = VALID600046 + WARNING4626 + INVALID0. Violations4626, all SALES_INVOICELINES_LINE_PROFIT_MIN_VALUE/WARNING/flag. Quarantine0 trên dữ liệu thật; không fabricate invalid data để tăng số liệu.

Full runtime: debug/compile/build/test PASS; 69 dbt tests, 129 independent reconciliation checks, gồm 1329 ratio comparisons. Max ratio difference 4.9462366e-17 dưới tolerance1e-12. Raw-derived expectations không gọi metric macro; per-row facts/Raw, grouped date/product/customer, header counts, product DISTINCT counts, included/excluded, key and coverage checks đều PASS.

| Measure | Raw expected = actual | Difference |
|---|---:|---:|
| Invoiced Sales Before Tax | 172261341.20 | 0 |
| Invoice Amount Including Tax | 198043439.45 | 0 |
| Invoice Tax Amount | 25782098.25 | 0 |
| Source Units Sold | 8950628 | 0 |
| Invoice Count | 70510 | 0 |
| Order Count | 73595 | 0 |
| Eligible invoice lines | 228265 | 0 |
| Excluded invoice lines / amount | 0 / 0 | 0 |

Stable rerun: all21 model row counts và all13 materialized-table content digests giống hệt. Initial/final accepted Raw typed-row digests all11 PASS; runs/object_runs/contracts/audits/publications/current-pointer hashes unchanged. Không source mutation, ingestion rerun hoặc publication.

## Performance đã đo và xử lý failures

[performance.yml](config/performance.yml) dùng staging/header views, DQ/core/marts tables, threads1, indexesfalse. Không thêm Raw indexes; kế hoạch dùng available source key indexes và parent-key membership sets. Baseline query plans được lưu trước tối ưu.

| Run có evidence | dbt engine | CLI wall | Notes |
|---|---:|---:|---|
| Baseline 21 models /65 tests | 34.851s | 39.768s | DQ17.411s |
| Lazy diagnostics, same21 models /65 tests | 26.019s | 30.595s | DQ11.582s, same capture/config |
| Final accepted21 models /69 tests | 28.788s | 33.192s | expanded checks |
| Stable rerun21 models /69 tests | 28.553s | 32.890s | DQ13.130s, all content unchanged |
| Standalone69 dbt tests | 10.150s | 14.362s | no rebuild |

Single-machine measured runs, cache/load có thể khác; không cam kết phần trăm cải thiện chung. Predicate pushdown trên run pin, one evaluation reused, parent membership joins và lazy diagnostics được giữ; không bỏ quality checks để tăng tốc.

Failures đã xử lý và giữ evidence:
- Legacy container bind missing → runtime-only junction, original container/volume intact.
- dbt test-schema naming và monthly interval syntax → bounded fixes, compile/build lại PASS.
- First population test có correlated expensive plan: chủ động cancel chính query của retail_transform sau >120s, sửa thành set comparison; không claim canceled run PASS.
- Config warning-off làm lộ plan outlier: old DQ457.837s; shared parent-key join implementation sau sửa chạy toàn config build33.297s wall/28.761s engine, warnings0 đúng dự kiến. Default đã restore.
- threads2 fail vì Docker /dev/shm64MiB; giữ threads1, không recreate/resize container, không prune hoặc xóa volume.
- JIT on/off không cải thiện đáng kể: original query17.407s/18.058s; final13.244s/12.929s; giữ server default. Không thay PostgreSQL global settings.

Plans và timings ở private invocation/benchmark JSONs; [benchmark.py](benchmark.py) chỉ EXPLAIN ANALYZE SELECT, read-only và statement timeout60s. Không lấy failed/aborted run làm successful performance baseline.

## Power BI readiness và giới hạn

Marts có dữ liệu thật, grains rõ, sẵn sàng chuẩn bị local Sales report. Kết nối PostgreSQL `127.0.0.1:55434`, database retail_raw, schema sales_marts. Dùng BI identity có SELECT phù hợp khi triển khai report; không dùng postgres hoặc chia sẻ transformation secret. Chưa tạo BI reader/report/dashboard trong task này.

Sales Amount = SUM(sales_amount); AIV = SUM(sales_amount)/SUM(invoice_count), denominator0 → BLANK/NULL. Không SUM daily AIV, growth rates hoặc product-filtered distinct counts. Customer role hiện BUYER; Buyer/Bill-to không SUM chung. Labels/current dimensions phải ghi observed-current, không historical attribution.

Không atomic/certified multi-model publication, không historical SCD2, incremental hoặc recovery production. Chỉ sử dụng outputs sau successful full build và acceptance; failed build có thể để lại model generations khác nhau, phải restore/rebuild và kiểm lại contract pins. Snapshot source UNVERIFIED giữ nguyên. Power BI/Airflow và các domain khác vẫn ngoài task.
