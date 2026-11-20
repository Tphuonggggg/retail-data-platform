# DATA-AUDIT-01 — Independent End-to-End Audit

**DATA_AUDIT_ACCEPTED**, trong phạm vi capture-pinned local Sales Analytics đã triển khai. Không phát hiện CRITICAL/HIGH data-correctness issue; không phát hiện current source drift trong các lần đọc. Đây không phải chứng nhận source point-in-time consistency hoặc historical SCD2.

## Baseline, thời gian và an toàn

- Branch: refactor/mvp-simplification; implementation baseline: cdfac7f59f6fb4d7fba5e4d27e0c1f6506b8429f.
- Pin: 5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8, tương ứng runs.run_id / raw._run_id; không đổi metadata runs.capture_id riêng.
- Source thực: DESKTOP-OBDFK6B\\SQLEXPRESS / WideWorldImporters, Windows principal DESKTOP-OBDFK6B\\PC, product17.0.1000.7.
- Giữ nguyên Owner-approved development profile: Encrypt=yes, TrustServerCertificate=yes, explicit admin opt-in. Không tuyên bố strict certificate-chain verification.
- Target: retail-raw-postgres-1 / retail_raw18.7 / 127.0.0.1:55434. Read-only sessions retail_ingest và retail_transform; default_transaction_read_only=on, statement_timeout120s, session parallel workers0. Không đổi global settings.
- Giữ advisory lock941062 trong audit để không đụng một transformation build đồng thời.
- Audit/report window 2026-11-20T17:48:23.128683+07:00 ??n 2026-11-20T18:02:59.890169+07:00 (Asia/Bangkok).
- Không Full Load, dbt build/run, model/config/data repair, SQL Server changes, provisioning, publication, DDL/ANALYZE/VACUUM hoặc Docker resource changes. Chỉ thêm artifacts trong thư mục audit này.

## Cách kiểm độc lập và giới hạn kết luận

1. Quét toàn bộ 11 source objects bằng SELECT theo approved projection, dùng F2 exact7 cho datetime2 và native varbinary cho geography. Không giới hạn mẫu.
2. Quét đúng Raw run pin. Audit serializer tự triển khai typed canonical JSON → SHA256 từng row, so sánh Counter multiset đầy đủ/multiplicity. Không gọi ingestion codec cho cả hai phía. Digest công bố là SHA256(count/modular-sum/xor); phép so sánh thực dùng full row-hash multiset, không chỉ fingerprint tổng.
3. Exact decimal/date/bit/NULL/text/native binary được phân biệt. Unicode không normalize, NULL không bằng empty string; seven-digit timestamps không chuyển thành Python datetime.
4. Stored ingestion audit được kiểm lại bổ sung bằng Raw-only legacy codec; không dùng nó làm bằng chứng độc lập Source–Raw.
5. Schema mapping kiểm Source types/length/precision/nullability, Raw types/scale/collation và technical UUID/ordinal fields. Current PK schema/data uniqueness/key sets, physical history multiplicity và ordinals1..N được kiểm riêng.
6. DQ evaluator Python đọc Raw và YAML, tự đánh giá rules; không gọi production failure_sql hoặc dbt quality macros. Record status, every violated rule, severity/action/lineage/version/eligibility được đối chiếu thực tế.
7. Facts/dimensions có per-field Raw comparisons; KPI expectations lấy từ Raw bằng SQL/Decimal độc lập, không gọi metric macro. Existing reconciliation chỉ là cross-check bổ sung.
8. Source scans nối tiếp, không controlled writer freeze/snapshot. Current equality không chứng minh nguồn đồng nhất tại một thời điểm lịch sử. Stored consistency vẫn UNVERIFIED, capture chưa publish.

## A — Source → Raw

| Object | Source now | Captured Raw | Difference | Digest / Integrity |
|---|---|---|---|---|
| Sales.CustomerTransactions | 97147 | 97147 | 0 | PASS |
| Sales.Customers | 663 | 663 | 0 | PASS |
| Sales.Customers_Archive | 51 | 51 | 0 | PASS |
| Sales.InvoiceLines | 228265 | 228265 | 0 | PASS |
| Sales.Invoices | 70510 | 70510 | 0 | PASS |
| Sales.OrderLines | 231412 | 231412 | 0 | PASS |
| Sales.Orders | 73595 | 73595 | 0 | PASS |
| Warehouse.StockItemHoldings | 227 | 227 | 0 | PASS |
| Warehouse.StockItemTransactions | 236667 | 236667 | 0 | PASS |
| Warehouse.StockItems | 227 | 227 | 0 | PASS |
| Warehouse.StockItems_Archive | 444 | 444 | 0 | PASS |

Tổng 939208 rows ở Source scan và accepted Raw; mọi count difference0, full independent content multiset PASS. Không current drift quan sát được. Các hash đầy đủ ở [evidence.json](evidence.json), check IDs/SQL/timing ở [queries.json](queries.json).

History Customers_Archive/StockItems_Archive đọc trực tiếp physical archives; giữ occurrence multiplicity. Current-table PK uniqueness với hai archives là NOT_APPLICABLE, không đổi thành PASS. Duplicate full payload và duplicate (NK,ValidFrom,ValidTo) của hai archives quan sát được đều0.

Base StockItemHoldings có681 rows across three captures; selected capture chỉ227. Hai captures khác là smoke/retry đã tồn tại, không contamination. Failed attempts có0 committed payload rows trên cả11 tables. Metadata object set, statuses/counts, audits, ordinal boundaries và total selected populations khớp.

## B/C — Metadata, capture isolation và staging

- Raw-only durable audit PASS; source count COUNT_BIG được kiểm bổ sung sau full scans.
- Exactly expected11 object populations và21 model relations; actual materializations8 views/13 tables.
- Actual stage view contents, full-column multisets và business-key sets khớp Raw; không silent filtering/NULL coercion/rounding.
- Stage definitions không dùng raw.current_* hoặc publication views; pin explicit. Null-safe capture/ruleset/evaluation và measure-version checks PASS.
- Raw control hashes trước/sau không đổi; publication ledger0, pointerNULL.

| Actual staging view | Rows |
|---|---|
| dw_staging.stg_sales_customers | 663 |
| dw_staging.stg_sales_invoicelines | 228265 |
| dw_staging.stg_sales_invoices | 70510 |
| dw_staging.stg_sales_orderlines | 231412 |
| dw_staging.stg_sales_orders | 73595 |
| dw_staging.stg_warehouse_stockitems | 227 |

## D — DQ và quarantine

| Classification | Actual |
|---|---|
| Evaluated | 604672 |
| VALID | 600046 |
| WARNING | 4626 |
| INVALID | 0 |
| Violations | 4626 |
| Quarantine | 0 |

Tổng evaluated = VALID + WARNING + INVALID =604672. Có4626 violations/4626 distinct records, tất cả rule SALES_INVOICELINES_LINE_PROFIT_MIN_VALUE / WARNING / flag. Việc phân loại được tái tính từ Raw, không tin sẵn status của production.

108 enabled rules có IDs unique; actual violations dùng đúng rule/ruleset và tồn tại Raw occurrence tương ứng. NULL-safe version, duplicate status/violation keys, quarantine membership và fact eligibility/flags đều PASS.

Representative actual warnings dưới đây không chứa customer identifiers/names/contact data:

| Raw ordinal | Record identity | Actual LineProfit |
|---|---|---|
| 96574 | 7a15ea44a59e61425ff7b3f70bf1030a | -48.00 |
| 96668 | 6c09040e3b4d98e9a7226fe001b53086 | -48.00 |
| 96777 | bb1313c741fe0a69973795594dbcbba1 | -36.00 |

Lookup tái kiểm: join raw.sales_invoicelines._run_id + _row_ordinal vào violation.capture_id + _raw_row_ordinal, rồi đối chiếu source business key và LineProfit<0. Warning hash representation cũng khớp Raw value.

Real invalid/quarantine =0. Hành vi quarantine được kiểm **chỉ đọc** từ fixture namespace đã có sẵn: fixture_cfe6af032542, input5, quarantine2, states[['WARNING', 1], ['INVALID', 2], ['VALID', 2]]. Không tạo synthetic records trong audit và không trộn fixture results vào số liệu thật.

## E/F — Dimensions và facts

- dim_date1247 unique dates/keys, range2013-01-01..2016-05-31; year/month/day/quarter/month_start đúng.
- dim_customer663 và dim_product227: current natural keys/SKs unique, raw population đầy đủ, mọi admitted attributes và exact source periods khớp Raw. Deterministic observed-capture keys tái tính độc lập.
- fact_invoice_line228265, fact_order_line231412: source grain unique, per-row IDs/price/quantity/date/roles/measures khớp; exact last-edited text/profit/lineage được kiểm thêm.
- Customer buyer/Bill-to/Product/date observed FKs map đúng natural member; không nhầm buyer với current master bill-to.
- Historical keys giữ NULL/U như accepted deferral; invoice Buyer/Bill-to/Product U228265 mỗi role. Đây không phải observed FK orphan; audit không chứng nhận historical attribute lookup.

## G — Business accuracy và marts

| Mart | Actual rows |
|---|---|
| sales_marts.mart_customer_sales | 66463 |
| sales_marts.mart_sales_customer_summary | 663 |
| sales_marts.mart_sales_daily | 1247 |
| sales_marts.mart_sales_monthly | 41 |
| sales_marts.mart_sales_product_daily | 141561 |

| KPI | Raw = Actual | Difference |
|---|---|---|
| Sales Before Tax | 172261341.20 | 0 |
| Tax Amount | 25782098.25 | 0 |
| Including Tax | 198043439.45 | 0 |
| Units Sold | 8950628 | 0 |
| Invoice Count | 70510 | 0 |
| Order Count | 73595 | 0 |

Amount differences0. Daily tax/including-tax/header counts, monthly units/invoice counts, product distinct invoices, customer daily counts và customer summary first/last invoice dates đều đối chiếu riêng từ Raw. Không chỉ kiểm grand totals.

69 SELECT-equivalent dbt tests và independent Raw-based checks gồm1329 ratios PASS; approved tolerance chỉ dành cho ratio1e-12, money0. Max ratio absolute difference4.9462366e-17. Average Invoice Value không phải AOV; recognized revenue/official profit/COGS/refunds/payment allocation vẫn ngoài scope.

Customer mart grain =InvoiceDate/customer/selected role; summary mới là một customer/role. Role hiện BUYER; không cộng Buyer và Bill-to. Product-filtered DISTINCT InvoiceID không additive giữa products. Capture/date coverage và MoM/YoY NULL/zero/comparator behavior được kiểm độc lập.

## H — Storage và performance diagnostics

| Schema | Actual bytes | MiB |
|---|---|---|
| dbt_sales_test | 327680 | 0.312 |
| dq | 145973248 | 139.211 |
| dw_core | 253370368 | 241.633 |
| ingestion_meta | 172032 | 0.164 |
| raw | 267821056 | 255.414 |
| sales_marts | 60063744 | 57.281 |

Database bytes tại thời điểm đo: 738105023 bytes (703.912 MiB). Schema totals là heap+indexes+TOAST, views không copy Raw; chênh so với database total gồm catalog/metadata/khác. [storage_report.csv](storage_report.csv) ghi bytes và estimated_rows **tách biệt** actual COUNT, không dùng estimate làm expected data count.

Largest relation: dq.record_status, total144113664 bytes,604672 rows; hai facts tiếp theo133767168/118554624 bytes. Raw history/captures và core/marts là các grain/lineage khác nhau, chưa có bằng chứng copy toàn Raw dư thừa.

LOW optimization opportunity: ruleset_version + evaluation_id riêng trong record_status chiếm59257856 bytes (~56.5MiB). Có thể benchmark compact/binary version encoding hoặc association trước migration; phải giữ traceability. Không tự tối ưu schema/index/data trong audit.

pg_stat_statements chưa cài: historical heavy-query statistics NOT_APPLICABLE. Có safe EXPLAIN FORMAT JSON, không EXPLAIN ANALYZE/ANALYZE/extension installation. Client query/scan timings ghi riêng trong queries.json, không gọi chúng là server-only benchmark.

## I — Regression và kết quả phân loại

{'PASS': 475, 'NOT_APPLICABLE': 3, 'WARNING': 2}. T?ng480 checks, kh?ng FAIL/BLOCKED/DRIFT.

- Fresh dbt debug/compile exit0. Inspect installed dbt test materialization: store-failures branch có thể drop/create relation; audit không dùng dbt test adapter path.
- Thay thế bằng fresh compiled test SQL SELECT count(failure rows), đọc trong server-side read-only session; all69 PASS.
- Existing offline153 tests PASS; audit-specific7 harness tests PASS (Decimal/float,100ns,Unicode,NULL,multiplicity,parameter binding).
- Không chạy fixtures command của implementation; chỉ đọc fixture tables cũ.
- Một audit-harness attempt lỗi empty parameter tuple khi query chứa LIKE-percent; đã sửa cursor binding thành None khi không có parameters, thêm regression test, chạy lại. Không thay business SQL/data để ép PASS; lỗi harness không phải data corruption.
- Findings CRITICAL0/HIGH0/MEDIUM0. Hai LOW warnings: inherited unproven point-in-time consistency và storage opportunity. Existing source LineProfit warnings là phân loại đúng, không là lỗi audit.
- NOT_APPLICABLE3: current-table PK uniqueness của hai archives và unavailable pg_stat_statements. Không chuyển những mục này thành PASS.

## Reproduce và files

Chạy từ project root, dùng venv hiện có. Audit code/artifacts là thay đổi duy nhất; không sửa tracker, rules hoặc models.

```powershell
.venv\Scripts\python.exe -m unittest discover -s docs/audits/data-audit-01 -p test_audit.py -v
.venv\Scripts\python.exe scripts/run_checks.py
# Với child-process environment PGOPTIONS=-c default_transaction_read_only=on:
.venv\Scripts\python.exe dbt/run_dbt.py debug --capture-id 5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8
.venv\Scripts\python.exe dbt/run_dbt.py compile --capture-id 5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8
# Lấy UUID compile từ .local/dbt/latest.json:
.venv\Scripts\python.exe docs/audits/data-audit-01/audit.py --execute --compiled-project .local/dbt/invocations/<compile-uuid>
```

Actual compile invocation:57278af1-991b-4131-92c0-709c3cd84a0b. Supplemental metadata reads kiểm COUNT_BIG/PK schema/failed payloads/measure pins sau primary scans; không rerun build. Execution window bao gồm verification, supplemental checks và report finalization; per-operation elapsed mới là thời gian thao tác đọc.

- [audit.py](audit.py): read-only verifier, independent serializer/evaluator và check definitions.
- [test_audit.py](test_audit.py): harness-only regression tests.
- [reconciliation.csv](reconciliation.csv): every check/expected/actual/status.
- [dq_findings.csv](dq_findings.csv): findings/limitations by severity.
- [storage_report.csv](storage_report.csv): actual sizes, actual counts, estimates.
- [evidence.json](evidence.json): aggregate results/hashes/provenance/limitations, không source table exports.
- [queries.json](queries.json): SQL/check IDs/parameters/elapsed; không credentials hoặc customer records.

Dừng sau audit; không Power BI, Airflow, Incremental, schema/data fixes hoặc publication.
