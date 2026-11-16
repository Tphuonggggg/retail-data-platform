# WWI DW-04 — Overall Architecture & Design Acceptance

**DW-04 DONE — Design Acceptance, ngày2026-11-16;20/20 mandatory design criteria và static/staged QA PASS theo conditional Owner authority.** Chỉ review/bàn giao thiết kế. [Gate Register](wwi-implementation-gate-register.md) giữ original gates; [Handoff](wwi-implementation-readiness-handoff.md) giữ readiness, milestone contracts và test mapping. Không thay accepted specifications.

## 1. Baseline và authority

Branch `main`, HEAD thực tế `b298d7d6f130094869fe8dbb0ba04d55f2e767e1`, message `docs: finalize DW-03C propagation and recovery design`; working tree/index sạch trước task, không remote. Hash125 baseline files được ghi để kiểm scope;115 file ngoài10 file sửa phải giữ nguyên byte. Owner DW-04 cho phép conditional design acceptance và một documentation commit sau QA đạt, không triển khai.

Đã đối chiếu AGENTS/Scope/Roadmap/Tasks, source inventory/profiling/dictionary/relationships/contracts, extraction/raw/validation requirements, BRD/KPI/K01–K13, DW-01 seven deliverables, DW-02 classification/identity/lookup/cutover/final specification/test/ADRs, DW-03A/B/C work plans/specifications/registers/assessments và B9 evidence. SQL/snapshot/B9 ở đây là **evidence lịch sử**, không chạy lại hoặc xác minh service hiện tại. Không biến source counts thành production thresholds.

## 2. Cross-stage architecture review

| Authority | Kết quả đối chiếu, không thay approval |
| --- | --- |
| [Source Contracts](wwi-source-contracts.md), [Extraction Matrix](wwi-extraction-requirements-matrix.md), [Metadata Dictionary](wwi-metadata-dictionary.md) | 9 current +2 physical H, explicit full projection/NULL/numeric/Unicode/binary/geography/computed fidelity. Nullable FK NULL khác orphan. Extraction candidates thời Phase1.4 được refined bởi accepted DW-03, không thay source population. |
| [BRD](../requirements/wwi-business-rules-decision-matrix.md), [KPI Catalog](../../analytics/kpi-definitions/wwi-kpi-candidate-catalog.md) | 12 approved rules/22 IDs; invoiced sales không recognized revenue; buyer/bill-to riêng; payment allocation/refund/daily balance/official COGS không được suy diễn. |
| [DW-01](wwi-logical-dw-design.md), [Dictionary](wwi-fact-dimension-dictionary.md), [Marts](wwi-logical-data-marts.md) | 2 headers/4 dims/4 facts/6 marts. Line vs header populations riêng, không multi-fact detail JOIN cộng measures. SCD candidates ở mốc DW-01 được refined bởi DW-02, không mở lại grain/KPI. |
| [DW-02 Final Spec](wwi-final-scd2-design-specification.md), [ADRs](../adr/README.md) | B1–B8 Approved Logical. Analytical episodes không mặc định business-effective history. Persistent opaque SK/registry; continuity giữ SK, split/merge replacement+supersession, không arbitrary survivor. Date-only dùng whole-day consensus; R/U giữ đủ population, I chặn affected unit; không current/earliest fallback. |
| [DW-03A Register](wwi-dw-03a-decision-register.md), [Full/Raw](wwi-dw-03a-full-raw-design-proposal.md) | A01/A03/A04/A06 Logical, A02 Conditional, A05 Direction Only. A02 cần verified static no-writes interval hoặc approved verified consistent copy; interactive read-only/old timestamps/matching counts không đủ. Capture/run/attempt/logical batch/publication riêng; immutable evidence; replay sealed capture khác new-context capture; reconciled Raw trước accepted publication. |
| [B9 Approval Evidence](wwi-dw-03a-evidence-approval-readiness.md), [PoC](../../tests/integration/b9_precision/README.md) | Approved Physical Raw Temporal Representation: verified F2→Python str/None→bound psycopg→authoritative TEXT/C exact comparator,27chars/7digits/NULL. Không datetime/microsecond authoritative, không đổi system-time thành business-effective; không whole Raw/index/retention/runtime approval. |
| [DW-03B Register](wwi-dw-03b-decision-register.md), [Incremental](wwi-dw-03b-incremental-design-proposal.md) | INC-01–06 Approved Logical; current-state convergence, không complete CDC/intermediate-event guarantee. Timestamp+PK chỉ candidate/pagination; same-time/backdated/late-commit cần full reconciliation. Complete consistent compatible snapshots; absence candidate khác confirmed removal; full comparison vẫn full source-read cost; durable accepted publication trước checkpoint ACK. |
| [DW-03C Register](wwi-dw-03c-decision-register.md), [Propagation/Recovery](wwi-dw-03c-change-propagation-design-proposal.md) | CP-01–06/D1/D2 Logical Approved, D3 Governance Approved,D4 Confirmed. Old/new impact groups và unchanged members; full affected-mart rebuild baseline A; ratios/distinct counts tính lại, không sum changed-row deltas. D1 frozen selected set neo analytical base+accepted Raw+registry revision+recorded build identity; không đổi Type2/source measure/time meaning, không bỏ B7 per-request authorization. |
| D2/D3, AP01–06 | Subject/view publication có complete transitive dependency graph/exact shared pins, không ép platform-wide rebuild. Cross-subject consumer cần compatible joint manifest hoặc hold. DQ detect/recommend; Owner authorize lifecycle; operator execute/audit. Rollback chỉ existing compatible validated appropriately Certified target; không có thì hold, không uncertified fallback. AP01 source pins/AP02 graph/AP03 registry/AP04 recon/AP05 tier certification/AP06 durable promotion-ACK vẫn cần runtime proof. |

**Kết luận:** không phát hiện mandatory architectural contradiction còn thiếu authority. Concrete source method/profile/schema/adapters/values/runtime là implementation prerequisites có owner/gate; không tự chọn datatype/timezone/day-domain/reference labels/rounding/per-action approvals.

## 3. Source-to-target coverage

Mỗi hàng: **Design complete** cho contract/routing; **Physical implementation pending / Runtime validation pending**. CustomerTransactions giữ Raw/staging/reconciliation nhưng không thêm fact tài chính. H là physical occurrence population, không giả có PK hoặc dùng FOR SYSTEM_TIME ALL thay physical archive.

| Source population | Extraction / Raw contract | Logical Staging | Dimension / Fact / Header | Mart / KPI | Quality gates | Owner / stage |
| --- | --- | --- | --- | --- | --- | --- |
| Sales.Customers | CustomerID; current + linked H validated separately | stg_customers; no history inference | dim_customer; order/invoice role lookups | C01–C03 via headers/lines; C04/C05 optional | G01–08; RG06/09; CG02/05; B5 | IN/ST→DW; M3–M5, M8; Customer expansion WWI-12 |
| Sales.Orders | OrderID; complete headers incl. uninvoiced/no-line | stg_orders | int_order_header; fact_order_line parent | S01/C01/C02; mart_customer_repeat_monthly | G01/08; RG09; CG01/05; header distinct/RI | IN→DW; M3–M5; M6 Sales; WWI-12 repeat mart |
| Sales.OrderLines | OrderLineID; no FK to InvoiceLine | stg_order_lines | fact_order_line; product/buyer/date | Product-filtered distinct explicitly labelled; no unsupported C02 product filter | G06/08; CG01/05; no line fan-out | IN→DW; M3–M5 |
| Sales.Invoices | InvoiceID; nullable OrderID; buyer/bill-to distinct | stg_invoices | int_invoice_header; fact_invoice_line parent | S02/S06; daily Sales; C03/C04 via distinct roles | G01/08; RG09; CG01/05; header/line coverage | IN→DW; M3–M6 |
| Sales.InvoiceLines | InvoiceLineID; source amount/tax/profit exact | stg_invoice_lines | fact_invoice_line | S03/S04/S05/S06; optional S09; sales daily/product/customer sales marts | G06/08; CG01/04/05; source reconciliation K02/K10/K13 | IN→DW/AO; M3–M6 |
| Sales.CustomerTransactions | CustomerTransactionID; nullable InvoiceID preserved | stg_customer_transactions; reconciliation population | No fifth financial fact; type1 grouped source check only | Supports invoice reconciliation; no payment allocation/refund KPI | G06/08; CG10; no invoice-line×payment join | IN/DQ; capture M3/M4 per authorized slice; no Finance expansion |
| Warehouse.StockItems | StockItemID; current + linked H; preserve excluded Raw fields | stg_stock_items | dim_product; historical/current roles | Sales product grouping; Inventory later | G03–06; RG06; CG02/05/09; B5 | IN→DW; M3–M5/M8, Inventory WWI-13 |
| Warehouse.StockItemHoldings | StockItemID; complete current state, not history | stg_stock_item_holdings | fact_inventory_current; same-state current Product | I04; mart_inventory_current | G01/08; RG09; CG05; no time-additivity/daily balance | IN→DW/AO; WWI-13; M pattern reused |
| Warehouse.StockItemTransactions | StockItemTransactionID; signed decimal; optional invoice/PO refs | stg_stock_item_transactions | fact_stock_movement; date/product/movement-type | I01/I02; I03/I05 optional; movement daily mart | G06/08; CG10; no line-level match or opening-balance invention | IN→DW/AO; WWI-13 after approved reference |
| Sales.Customers_Archive | Physical H occurrences; no enforced PK; incl. zero duration | Occurrence-preserving stg_customer_history | dim_customer registry/evidence; not business-effective history by default | Historical lookup status/coverage; same approved customer KPIs | G03/05; RG05/06; CG02/09; multiset reconciliation | IN/ST→DW; M3–M5 baseline, M7/M8 changes |
| Warehouse.StockItems_Archive | Physical H occurrences; retain all source fields/duplicates | Occurrence-preserving stg_product_history | dim_product registry/evidence | Sales Product lookup; Inventory later, no invented historical cost | G03/05/06; RG05/06; CG02/09 | IN/ST→DW; M3–M5 baseline, M7/M8 changes |

Staging names là nhãn routing logic, không tạo model/schema. Sales slice chỉ capture đủ dependency closure được giao, không cần triển khai mọi Customer/Inventory trước; full-scope11-population claim đòi đủ11. Application.TransactionTypes/category/group/package/color labels và Purchasing dependencies ngoài9 contracts cần extension/controlled mapping approval CG10, không tự thêm nguồn.

## 4. Logical model inventory

| Model | Accepted grain | Contract cần giữ |
| --- | --- | --- |
| int_order_header | 1 OrderID; all Orders | S01/C01/C02; OrderDate and buyer, no line requirement |
| int_invoice_header | 1 InvoiceID; all Invoices | S02/S06; InvoiceDate, buyer/bill-to; genuine no-line vs incomplete capture distinguished |
| dim_date | 1 calendar date | Invoice/order/movement roles; date-only not temporal instant proxy |
| dim_customer | 1 approved analytical episode / NK | Type2 CategoryID/BuyingGroupID/BillToCustomerID; optional credit/hold not activated; B1–B8 registry/lookup |
| dim_product | 1 approved analytical episode / NK | Type2 UnitPackageID/OuterPackageID/QuantityPerOuter; admitted others Type1; Tags excluded analytically, preserved Raw |
| dim_movement_type | 1 source TransactionTypeID / controlled reference | Application.TransactionTypes outside nine contracts: CG10 contract extension or controlled mapping before use |
| fact_order_line | 1 OrderLineID | OrderDate; buyer/product; quantity; no direct invoice-line match |
| fact_invoice_line | 1 InvoiceLineID | InvoiceDate; buyer/bill-to/product; ExtendedPrice, TaxAmount, difference; optional source LineProfit |
| fact_stock_movement | 1 StockItemTransactionID | Signed decimal quantity by movement date/type/item; optional document references |
| fact_inventory_current | 1 StockItemID in current published state | Product version resolved from same current state; observed_at ≠ published_at; no daily date FK |
| mart_sales_daily | 1 InvoiceDate | S02–S06; optional S09; header counts and line sums independently aggregated |
| mart_sales_product_daily | 1 InvoiceDate × StockItemID | S03–S05; optional S09; product-distinct invoice count not additive |
| mart_customer_sales | 1 InvoiceDate × CustomerID × customer_role | C03/C04; mandatory single BUYER or BILL_TO filter; enterprise totals once |
| mart_customer_repeat_monthly | 1 OrderMonth × Buyer CustomerID | S01/C01/C02; all order headers; distinct/rate recalculated outside month |
| mart_inventory_movement_daily | 1 movement date × StockItemID × TransactionTypeID | I01/I02; optional I03/I05; no daily balance |
| mart_inventory_current | 1 StockItemID in one published state | I04; no sum across snapshots/time |

[Bus Matrix](wwi-logical-dw-design.md), [Mapping](wwi-logical-source-to-target.md), [Star Schemas](wwi-logical-star-schemas.md), [Change Impact Matrix](wwi-change-impact-matrix.md) giữ nguyên. Snapshot max1 invoice/order không là schema1:1; OrderLine không có direct InvoiceLine FK. Header đầy đủ gồm chưa invoice/no-line; incomplete capture không được giả là empty hợp lệ. Lookup tối đa1 admitted dimension version/request. Customer sales bắt buộc một role; enterprise sales không cộng BUYER+BILL_TO. Inventory Product cùng current published state; observed_at ≠ published_at, không daily historical balance.

## 5. KPI và BRD traceability

| KPI ID | Scope | Business name | Model / consumer route | Evidence / correctness |
| --- | --- | --- | --- | --- |
| S01 | Core | Order Count | int_order_header; repeat mart only whole months; arbitrary days read header | K01; header count; no invoice filter |
| S02 | Core | Invoice Count | int_invoice_header → mart_sales_daily | K01; distinct invoice under Product differs global count |
| S03 | Core | Invoice Amount Including Tax | fact_invoice_line → Sales daily/product/customer roles | K02/K03; never add CustomerTransactions |
| S04 | Core | Invoice Tax Amount | fact_invoice_line → same Sales population | K02; numeric fidelity |
| S05 | Core | Invoiced Sales Before Tax | fact_invoice_line → same Sales population | K02; S03−S04; not Recognized Revenue |
| S06 | Core | Average Invoice Value Before Tax | Sales daily + invoice header population | K10; S05/S02, zero denominator NULL; no average of ratios |
| S07 | Deferred | Average Order Value | No MVP output | Eligibility/order amount/cohort not approved; no S06 relabel |
| S08 | Deferred | Recognized Revenue | No MVP output | No accounting recognition/date assumption |
| S09 | Optional | Source-Reported Line Profit | fact_invoice_line → Sales marts if separately enabled | K02/K13; negative allowed per evidence; not official Gross Profit/COGS |
| S10 | Unsupported | Credit Note / Refund Amount | No MVP output | No refund from payment/uninvoiced/receipt; not zero default |
| C01 | Core | Active Buyers with Orders | int_order_header / repeat mart distinct NK within selected period | K04; no sum distinct across periods |
| C02 | Core | Monthly Repeat Order Customer Rate | int_order_header → repeat monthly | K11; ≥2/≥1 distinct orders; recalc quarter from headers |
| C03 | Core | Invoiced Sales Before Tax by Buyer | fact_invoice_line → customer sales BUYER | K12; buyer from invoice, one role; no current BillTo inference |
| C04 | Optional | Invoiced Sales Before Tax by Bill-to | fact_invoice_line → customer sales BILL_TO if enabled | K12; billing attribution separate from buyer |
| C05 | Optional | Current Customer Category Distribution | one current dim_customer row per NK; no new seventh mart | K06; labels/reference approval; not historical segmentation |
| I01 | Core | Stock Issue Quantity | fact_stock_movement → movement daily type10 | K07; −SUM signed Quantity; preserve source signs |
| I02 | Core | Stock Receipt Quantity | fact_stock_movement → movement daily type11 | K07; SUM Quantity; no return assumption |
| I03 | Optional | Signed Stock Adjustments | movement daily type12 if enabled | K07; signed sum incl. zero; no default absolute value |
| I04 | Core | Current Quantity On Hand | fact_inventory_current → inventory current | K07; same published state, observed_at shown; no daily balance |
| I05 | Optional | Product Movement Trend | movement daily → month/item/type if enabled | K08; preserve signed quantities and type scope |
| I06 | Unsupported | Daily Closing Inventory Balance | No MVP output | No validated opening balance/stocktake policy |
| I07 | Unsupported | Stockout Risk | No MVP output | No approved demand/lead-time/risk model |

**12 Core +5 Optional +2 Deferred +3 Unsupported =22.**17 Core/Optional chưa có warehouse runtime validation. Không tự bật Optional, không gán unsupported=0. Catalog giữ formula/date/filter/NULL semantics chính thức. S06/C02 tính lại cùng numerator/denominator; Product distinct-count không additive; rounding/precision cần technical proof.

| Rule | Nội dung giữ nguyên | Model / exclusion |
| --- | --- | --- |
| BRD-01 | Separate order/invoice populations | 2 headers + invoice/order facts; S01–05 |
| BRD-02 | OrderDate / InvoiceDate | date roles; delivery not revenue basis |
| BRD-03 | Before-tax convention, tax separately | S03−S04=S05; no accounting claim |
| BRD-04 | Recognition deferred | S08 absent from release |
| BRD-05 | Optional source LineProfit; official GP/COGS deferred | S09 only if validated/enabled |
| BRD-06 | AIV not AOV | S06 numerator/denominator same population; S07 deferred |
| BRD-07 | No supported detailed refund scope | S10 unsupported; no fabricated 0 |
| BRD-08 | Buyer default, bill-to separate | role-playing keys + single-role semantic gate |
| BRD-09 | Monthly repeat from order headers | C02; uninvoiced retained; quarterly recomputation |
| BRD-10 | No invoice payment allocation inference | CustomerTransactions evidence/recon only; no fifth fact |
| BRD-11 | Current holdings and movements, no daily balance | I04 current; I06 unsupported |
| BRD-12 | Stockout risk outside MVP | I07 unsupported |

## 6. Documentation findings và sửa đúng phạm vi

| Finding | Thay đổi tài liệu | Approved authority |
| --- | --- | --- |
| F01 — overview vẫn gọi SCD2/incremental policy là Open | Ghi đúng approved logical/physical-representation scope, pending concrete implementation/values | DW-02/03 approvals, không mở lại policy |
| F02 — ingestion/staging và blanket deduplicate/quarantine có thể mất occurrences | dbt sở hữu staging; immutable Raw giữ physical source occurrences; retry idempotency khác valid source duplicates; incomplete/invalid capture hold publication, không drop để giả complete | A01/A03/B9/INC/CP |
| F03 — flow nói toàn bộ SCD2 làm sau Sales | Minimum Customer/Product registry/lookup/R-U-I tại M5, expanded analytics sau Sales | DW-01 L05/DW-02 |
| F04 — candidate M6 trước incremental/orchestration trái tracker | Reconcile theo WWI-07/08→09→10→11; không đổi task dependencies | Existing TASKS/ROADMAP |
| F05 — current navigation còn DW-04 TODO | Latest DW-04 status có điều kiện sau QA; Stage3 trước đó là lịch sử | Owner conditional authority; parent/phase giữ riêng |

Không sửa prior approved source/SQL/BRD/KPI/ADR/DW/B9 evidence; không tạo tài liệu chức năng trùng thứ tư.

## 7. Implementation handoff và test obligations

[Gate Register](wwi-implementation-gate-register.md): **31 original gates**, G01–08/RG01–12/CG01–10/B5, đủ approval/implementation/evidence/owner/target/deps/blocker/status. A trước task start, B trước Raw acceptance, C trước incremental publish, D trước SCD2/facts acceptance, E trước Certified output. Gate có thể chặn nhiều checkpoint; B9 PoC không đóng production gates.

[Handoff](wwi-implementation-readiness-handoff.md): **18 components**,2 class1 Ready,13 class2 Ready with prerequisites,3 class3 Blocked pending Owner/technical decision. Class4 dành extensions/unsupported outputs ngoài main components. Class3: concrete source consistency proof/method, least-privilege access, approved B5/quality numeric values trước Certified. Đây là owned implementation gates, không thiếu logical architecture decision. Operational Readiness chưa đạt; production modules **Not implemented yet**.

Trình tự ưu tiên **M1→M2→M3→M4→M5→M7→M8→M9→M6**, có thể song song M5/M7 theo dependencies sau M4 khi Owner giao. M1–9 là work packages, không thay Phase2–9. M5 cần baseline SCD lookup; M8 change/restate/certification controls, không Certified mart khi M6 inputs/B5/E proof chưa đủ. M9 không phụ thuộc M6 chưa release. Customer WWI-12 rồi Inventory WWI-13 sau Sales WWI-11. Basic tests/CI bắt đầu từ code đầu tiên, không chờ monitoring hoặc Phase9.

**72 tests NOT RUN**: CD-T01–21,IT01–21,CP-T01–30; Handoff gắn từng ID với earliest milestone/must-pass-before gate. Full changed-state scenarios ở M7 không cho phép dời Raw key/value/archive fidelity khỏi M4 hoặc initial SCD correctness khỏi M5. Inventory live tests trước WWI-13 publication. Historical B9 executed bounded tests được tách riêng, không chạy lại trong DW-04.

## 8. Acceptance và parent/phase boundary

| ID | Mandatory criterion | Evidence | Result |
| --- | --- | --- | --- |
| D4-AC01 | Baseline/authority hợp lệ, không triển khai | HEAD/branch/clean baseline §1, phạm vi13 Markdown §9 | PASS |
| D4-AC02 | Source coverage 9 current +2 physical H | 11 populations §3; source contracts và occurrence preservation | PASS |
| D4-AC03 | Đủ2 headers/4 dims/4 facts/6 marts, grain đúng | 16 logical objects §4; giữ NK/header/current state | PASS |
| D4-AC04 | KPI/BRD đầy đủ, loại trừ đúng | 22 KPI,12 BRD §5;12 Core/5 Optional/2 Deferred/3 Unsupported | PASS |
| D4-AC05 | Approved cross-stage policies không xung đột | Authority/contract review §2; không chốt physical defaults | PASS |
| D4-AC06 | Source consistency/least privilege vẫn là prerequisite | A02/G01/G02/RG01/RG02; không coi interactive PoC là production proof | PASS |
| D4-AC07 | Raw fidelity/B9/physical occurrences/reconciliation | G03–G08; exact TEXT/C; không DISTINCT archive | PASS |
| D4-AC08 | Incremental convergence/absence/checkpoint đúng | INC-01–06; RG03–10; no complete-event promise | PASS |
| D4-AC09 | SCD2 registry/lookup/R-U-I/Type1 rules nhất quán | B1–B8/D1; minimum Sales dims at M5, changes M8 | PASS |
| D4-AC10 | Impact/full affected rebuild đúng | CP-01–04/D4; old/new+unchanged group members; CG01–04 | PASS |
| D4-AC11 | Publication/compatibility/lifecycle đúng | D2/D3; AP01–06; CG05–07; B5 values pending | PASS |
| D4-AC12 | 31 gates giữ identity/owner/proof/target/blocker | Gate Register G01–08/RG01–12/CG01–10/B5; A–E | PASS |
| D4-AC13 | 18 readiness components tách design/runtime | Handoff R01–18; classes1/2/3/4, no production readiness claim | PASS |
| D4-AC14 | M1–9 có inputs/outputs/deps/tests/DoD/demo | Handoff9 contracts; reconciled WWI-05–16; sequence §7 | PASS |
| D4-AC15 | Đủ72 planned tests, earliest stage, không false PASS | CD-T01–21/IT01–21/CP-T01–30 NOT RUN; B9 historical riêng | PASS |
| D4-AC16 | Không trì hoãn correctness đến monitoring | A/B/C/D/E gates trước relevant acceptance/publication; initial SCD M5 | PASS |
| D4-AC17 | Sửa đúng documentation drift, không architecture change | §6; overview/data-flow và current status navigation | PASS |
| D4-AC18 | Parent/phase completion kiểm riêng | §8; WWI-04/Phase1 IN_PROGRESS; Phase2–9 Not Started | PASS |
| D4-AC19 | Static QA, scope/protected files/links/secrets đạt | §9 — actual static QA PASS | PASS |
| D4-AC20 | Staged QA + focused docs-only commit phù hợp | §9 — staged scope/content/security/diff QA PASS; no push/remote | PASS |

DW-04 tracker criterion gồm consistency/no mandatory blocker và “Owner nghiệm thu WWI-04”. Task hiện tại cho phép conditional **DW-04** design acceptance, yêu cầu parent criteria kiểm riêng: Owner overall parent sign-off giữ là **parent checkpoint**, không suy từ subtask DONE. WWI-04 cần DW-01–04 accepted và watermark/tie-breaker/delete/history/as-of/independent INSERT-UPDATE-DELETE test design được duyệt: specifications/approvals đã có; actual72 runtime tests NOT RUN thuộc triển khai. Không biến parent design criterion thành tuyên bố pipeline đã test, không tự ghi Owner đã close parent.

Phase1 gate “các quyết định ảnh hưởng Sales schema/pipeline được duyệt; giới hạn snapshot/temporal rõ” đã đối chiếu: logical/business policies và giới hạn đủ; cụ thể physical/source consistency/reference/numeric prerequisites cần Owner review tại relevant gate. Chưa có independent overall parent/Phase1 closure record hoặc authorization Phase2 trong task này. **WWI-04 IN_PROGRESS; Phase1 In Progress; Phase2–9 Not Started.** Đề nghị Owner review closure và giao bounded implementation task riêng; đây không là DW-04 architecture contradiction.

## 9. Static QA và change manifest

**QA PASS — actual static checks ngày2026-11-16:**128 visible text files/122 Markdown;946 local links+anchors,0 broken. Exact coverage11 source populations/16 models/22 KPI/12 BRD/31 original gates/18 components/9 milestones/72 original scenario IDs; mỗi scenario giữ NOT RUN và có earliest/use gate.20 acceptance criteria PASS sau review hợp đồng và QA.115 protected baseline SHA-256 giữ nguyên; đúng13 Markdown paths, no unrelated/code/config/dependency/B9 edits.

Secret scan128 files và13 staged blobs:0 high-confidence key/token/private-key/credential-URI findings; actual ignored sandbox secret value không xuất hiện trong Git content. Local credential files vẫn ignored; không .venv/source extracts/database/binary staged. Size/UTF-8/fence/table/trailing-whitespace/scope checks PASS; largest staged document37.087 bytes. Staged blobs khớp working tree sau Git line-ending normalization; git diff --check và git diff --cached --check PASS; configured identity có, không active hooks/remote. LF→CRLF warnings theo Git hiện có, không đổi config. Final staged verification phải lặp sau status update trước commit; không runtime tests được chạy.

13 Markdown files (10 sửa +3 mới):

- `AGENTS.md`
- `PROJECT_SCOPE.md`
- `ROADMAP.md`
- `TASKS.md`
- `README.md`
- `CHANGELOG.md`
- `docs/data-models/README.md`
- `docs/architecture/README.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/data-flow.md`
- `docs/data-models/wwi-dw-04-assessment.md`
- `docs/data-models/wwi-implementation-gate-register.md`
- `docs/data-models/wwi-implementation-readiness-handoff.md`

Giữ prior accepted evidence byte-for-byte. Chỉ focused documentation commit sau QA với message `docs: complete DW-04 architecture acceptance and implementation handoff`; không remote/push. Commit hash báo sau commit, không nhúng hash của chính nó vào commit.

## Owner follow-up — 2026-11-16, sau design review

[APPROVAL-01–05](../architecture/wwi-phase-1-closure-approval.md) giải quyết parent/phase sign-off còn thiếu ở hồ sơ trên: WWI-04 DONE — Design; Phase1 Completed — Requirements & Source Design; Phase2/WWI-05/M1A IN_PROGRESS — Authorized, ban đầu chỉ bounded verification sau Checkpoint A QA+commit. Historical parent-IN_PROGRESS/no-start statements giữ mốc trước approval. M2+ chưa được giao;31 gates/72 NOT RUN tests/architecture/B9 không đổi, không operational readiness approval.
