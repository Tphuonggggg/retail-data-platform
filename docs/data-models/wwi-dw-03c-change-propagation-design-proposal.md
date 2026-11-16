# WWI DW-03C — Final Change Propagation & Recovery Design Specification

**Stage 3, 2026-11-16. CP-01–CP-06 APPROVED — Logical Policy; D1/D2 APPROVED — Logical Policy; D3 APPROVED — Governance Policy; D4 CONFIRMED.** Owner task “DW-03C Stage 3 — Owner D1–D3 Approvals & Final Design Acceptance” cho conditional design closure sau mandatory criteria/QA. Current review/result tại [Assessment](wwi-dw-03c-assessment.md). Production modules **Not implemented yet**; CP-T01–CP-T30 **NOT RUN**. Không đổi DW-01/02/03A/03B/B1–B9/INC/ACK.

**Final current status:** DW-03C **DONE — Design** sau18/18 mandatory design criteria/actual documentation QA; physical/runtime/action gates pending. Stage1/2 records giữ history; DW-04 TODO, không tự triển khai task tiếp.

## 1. Inputs, approved constraints và assurance boundary

[Work plan](wwi-dw-03c-work-plan.md) giữ baseline/dependencies/evidence E01–E10; [Decision Register](wwi-dw-03c-decision-register.md) giữ sáu đề xuất; [Assessment](wwi-dw-03c-assessment.md) giữ design coverage/QA/readiness. Không lặp source dictionary, KPI formulas hoặc SCD2 algorithms đã có.

Flow: accepted PostgreSQL Raw → dbt Staging → Core DW → Analytics Marts → Certified analytical publication. Các node là **logical build responsibilities**, không dbt models/schema/DAG đang chạy. Giữ stack và Sales-first.

Approved authorities: [DW-01](wwi-logical-dw-design.md)/[Fact-Dimension Dictionary](wwi-fact-dimension-dictionary.md)/[Marts](wwi-logical-data-marts.md); [Final SCD2](wwi-final-scd2-design-specification.md)/[ADRs](../adr/README.md); [DW-03A](wwi-dw-03a-full-raw-design-proposal.md)/[A01–A06](wwi-dw-03a-decision-register.md); [INC-01–INC-06](wwi-dw-03b-decision-register.md)/[ACK01–ACK06](wwi-dw-03b-incremental-design-proposal.md). [BRD](../requirements/wwi-business-rules-decision-matrix.md)/[KPI Catalog](../../analytics/kpi-definitions/wwi-kpi-candidate-catalog.md) giữ nguyên.

Sáu bảo đảm phải tách: **candidate change detection**, **Current-State Convergence**, **complete intermediate event history**, **temporal source history**, **analytical SCD2 history**, **Certified analytical outputs**. DW-03B chỉ hướng convergence với source state C/S_C/R_C đã định nghĩa; không full CDC, không tái tạo intermediate changes đã mất giữa observations. CP không nâng guarantee hoặc dùng source timestamp làm transaction ordering/global truth.

Input eligibility: accepted Raw publication với compatible source generation/scope/contract/projection/serialization và consistency proof A02; unknown/mixed/incomplete source boundary → hold downstream complete/certified claim. Current-State Convergence của Raw không đồng nghĩa SCD2 historical correctness hoặc automatic certification. G01–G08, RG01–RG12/B5 vẫn open runtime gates; xem work plan, không đóng gate bởi documentation QA.

## 2. CP-01 — Model inventory và source-to-target impact

### Model aliases — giữ nguyên logical grains đã duyệt

| Alias | Exact model | Declared responsibility / grain |
| --- | --- | --- |
| OH | int_order_header | 1 OrderID; all Orders, gồm chưa invoice/no-line |
| IH | int_invoice_header | 1 InvoiceID; all Invoices, nullable OrderID/no-line được giữ |
| DD | dim_date | Calendar date; invoice/order/movement roles; range/key format chưa tự chọn |
| DC | dim_customer | Source CustomerID + analytical episode/opaque SK, buyer và bill-to role-playing |
| DP | dim_product | Source StockItemID + analytical episode/opaque SK; current role riêng |
| DM | dim_movement_type | TransactionTypeID reference; contract extension/controlled mapping còn gate |
| FI | fact_invoice_line | 1 InvoiceLineID; date/buyer/bill-to từ IH, product từ line |
| FO | fact_order_line | 1 OrderLineID; date/buyer từ OH |
| FM | fact_stock_movement | 1 StockItemTransactionID; signed quantity, movement date/type |
| FC | fact_inventory_current | 1 StockItemID trong current published state, không daily history |
| SD | mart_sales_daily | 1 InvoiceDate; lines totals và independent invoice header counts |
| SP | mart_sales_product_daily | InvoiceDate × source StockItemID |
| CS | mart_customer_sales | InvoiceDate × source CustomerID × customer_role |
| RM | mart_customer_repeat_monthly | OrderMonth × source Buyer CustomerID |
| MD | mart_inventory_movement_daily | Movement calendar date × StockItemID × TransactionTypeID |
| IC | mart_inventory_current | 1 source StockItemID trong một published state |

Chín current tables + hai physical H đều từ **một WWI source**. Các matrix source rows dưới đây là CP-01 logical propagation contract sau Stage 2 approval, không bằng chứng source changes thực tế; D1–D3 đã approved đúng cấp tại Stage3, physical/runtime/action evidence gates vẫn pending. Chỉ xử lý input đã accepted theo INC; watermark/capture nằm ngoài CP implementation.

### Source-to-target impact matrix — 11 populations

Mỗi row cover INSERT/UPDATE/correction; disappearance chỉ candidate trừ khi separate removal action được duyệt. H rows là occurrence/multiset evidence, không auto logical events.

| Source entity / business key | Change category | Intermediate impact | Dimension impact | Fact impact | Mart / KPI impact | Reprocessing scope | Required reconciliation | Blocking conditions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sales.Orders / OrderID | New/header-only date/buyer/ref correction; controlled removal | OH independently, giữ all headers | DD required order dates, DC buyer lookup metadata | FO toàn child line union old/new OrderID; không cascade invoice data | RM; S01/C01/C02 từ header, không loại order chưa invoice | Old/new buyer-month/date; all affected children; quarterly request dùng full quarter headers | Distinct header PK/population, line qty riêng, buyer-month numerator/denominator | Missing header/child coverage, mixed pins, invalid date/role/identity; absence chưa confirmed không retraction |
| Sales.OrderLines / OrderLineID | Insert/qty-price/product/OrderID correction | OH source population không đổi vì line count | DP; DD/DC từ affected OH | FO same source grain, parent/product relookup | Không thêm mart thứ7 hoặc đổi S01/C01/C02 vì thêm line; product-filter variants chưa duyệt không publish | Old/new parent/product detail groups và applicable approved consumers | Per-PK qty/nullable UnitPrice/PickedQuantity, no InvoiceLine matching assumption | Parent/product invalid/missing population, unsupported line-based header counts |
| Sales.Invoices / InvoiceID | Header-only InvoiceDate/buyer/bill-to/OrderID/eligibility field correction | IH independently | DD; DC two roles separate, DP relookup FI theo new date nếu cần | FI tất cả lines của header dù line timestamp không đổi | SD/SP/CS; S02–S06/C03/C04, S09 optional | Old/new dates + product/customer-role groups, invoice count/AIV full denominator | Header count/all lines; FI amounts/role totals, optional OrderID giữ | Missing children, mixed header/line revisions, role fan-out; credit-note rule chưa có phải review |
| Sales.InvoiceLines / InvoiceLineID | Insert/amount-tax-qty/profit/product/InvoiceID correction | IH count độc lập; changed line không thành new invoice | DP; date/customer roles từ old/new IH | FI replace/update same PK, no additive replay | SD/SP/CS; S03–S06/C03/C04/S09 optional, product-filtered distinct riêng | Old/new InvoiceID,date,StockItemID,buyer/bill-to; groups rỗng phải rút stale output | Exact per-PK values; S03=S04+S05, line sums vs header population | Incomplete IH/Product/input, rounding/identity conflicts, count theo line hoặc role double sum |
| Sales.CustomerTransactions / CustomerTransactionID | Type/amount/balance/finalization/reference correction | IH chỉ tham chiếu đối soát optional InvoiceID, không invent header | Reference/type validation; không tự thêm DC financial role | Không financial/payment fact mới trong bốn facts | Sales certification reconciliation I06/I07 nếu dependency khai báo; không allocation hoặc cộng amount vào SD/CS | Own PK/type + affected invoice diagnostic population khi type/link có evidence | Transaction sums theo type riêng; invoice amounts grouped riêng; NULL payment InvoiceID hợp lệ | Fan-out/allocation suy từ CustomerID; missing controlled reference hoặc recon evidence; source anomaly disposition pending |
| Sales.Customers / CustomerID | New entity/admitted attribute/current/boundary correction; disappearance/reappearance | OH/IH source roles không rewrite; re-resolve lookup metadata nếu affected | DC candidate episode/revision theo approved vector/Type1 scope | FI buyer/bill-to và FO buyer chỉ affected NK/role/interval; không FM customer dimension mới | CS/RM descriptor/coverage; C03/C04 và C05 optional current DC; NK counts/totals giữ khi chỉ rekey | NK/incarnation+selected versions+roles+interval; no blanket historical rekey | Registry/identity/coverage/R-U-I; source measures và distinct NK conserved | Proven overlap/multi-match I; insufficient proof U; B7 Type1 scope chưa approve hoặc B8 ambiguity không auto entity action |
| Sales.Customers_Archive / NK CustomerID, no source PK | Added/corrected/missing H occurrences, duplicate starts/zero-duration | OH/IH lookup dependencies, không source-role changes | DC reconcile H+current+forward; physical occurrence khác episode | FI/FO historical resolution/re-resolution candidates | CS/RM historical attribution/certification; enterprise measures không tự đổi | Evidence-affected NK/role/exact interval/day; widen khi cannot bound | H multiset/origin/100ns, bridge/registry/supersession, before/after fact maps | Generation/basis mismatch, indistinguishable lineage → uncertainty; I block, no invented historical fallback |
| Warehouse.StockItems / StockItemID | New/admitted Type1 or packaging Type2/current correction | OH/IH không change source population | DP historical/current revision; không tự đổi DD/DM vì product | FI/FO/FM affected product roles; FC current version same-state | SP/MD/IC và filtered dependent views; source measures không dùng master price/cost | NK/episode/interval/selected attrs; FC full compatible state nếu current pointer đổi | Exact source qty/amount conservation, lookup 0..1, compatible Product-holdings pins | Missing current-state match, unapproved Type1 mode, invalid identity, mixed holdings/Product generations |
| Warehouse.StockItems_Archive / NK StockItemID, no source PK | H occurrences/period correction/retention change | Không header source rewrite | DP historical/current-forward bridge | FI/FO/FM historical lookup/rekey; FC chỉ khi current dependency thật sự đổi | SP/MD historical descriptors/certification; IC nếu current role affected | Evidence-bounded NK/roles/periods, no analytical episodes do Tags-only history | H multiset/zero-duration/registry/lookup exactness và source totals | Raw occurrence dedupe, unsupported business-time inference, lost forward evidence/generation conflict |
| Warehouse.StockItemHoldings / StockItemID | Complete current snapshot qty/cost/field diff; candidate absence | Không OH/IH | DP current published-state lookup | FC replace compatible current state, no additive snapshots | IC/I04; LastCostPrice không tự tạo COGS | Candidate current-state scope + changed item closure; baseline full current rebuild | Unique NK/count/QuantityOnHand same observed state, observed_at khác published_at | Partial snapshot/mixed Product version, candidate absence treated zero/delete, daily-balance invention |
| Warehouse.StockItemTransactions / StockItemTransactionID | Insert/signed qty/date/type/product/link correction; controlled removal | Không OH/IH source rewrite; invoice link là diagnostic | DD movement date, DP historical role, DM reference lookup | FM same PK, preserve signed decimal/zero adjustments | MD/I01/I02/I03 optional/I05 optional; không update holdings từ movement | Old/new movement date/item/type/doc group | Per-PK signed qty/counts, issue↔invoice grouped riêng; receipt check only approved PO dependency | Unknown type/sign policy/missing reference, mixed generations, no direct movement-line fact join hoặc balance inference |

**External reference/calendar dependencies:** DD không phải source table thứ12: required dates từ OH/IH/FM làm calendar coverage check, calendar repair/range/key/time basis cần approved contract. DM cần Application.TransactionTypes contract extension hoặc controlled mapping trước materialize/type labels; TransactionTypes thay đổi có thể không đổi StockItemTransactions. CustomerCategories/BuyingGroups/PackageTypes/Colors tương tự là existing gates, không tự thêm source ingestion hoặc semantic classification. Missing reference không được gán nhãn/type mặc định để pass.

### CP-01 approved old–new impact envelope — không physical schema

Mỗi accepted change request giữ: source/raw publication pins và generation; source object/PK hoặc H occurrence refs; old/new accepted content; affected NK/incarnation/role/exact interval và analytical episode/SK revision; old/new header IDs, child PK sets, dates, grouping keys; model/KPI/view dependencies; correction authorization; code/contract/policy revisions; completeness/conflict/reconciliation evidence; prior/candidate analytical publication refs. Không đưa PII payload hoặc secrets vào Git/log.

Old-state evidence lấy từ prior pinned compatible publication/retained Raw và registry, new-state từ accepted input pins; không query latest tùy model. Header fan-out dùng **union old/new child PKs** và old/new header values, không chỉ changed-line feed. Changed parent/date/role/type/product phải invalidate cả hai phía; nếu old group rỗng sau correction, candidate replacement phải bỏ row stale, không giữ số cũ. Thiếu prior evidence để giới hạn impact thì widen/full rebuild affected scope hoặc hold; không đoán old groups.

## 3. CP-02 — Dimension/SCD2 propagation

Giữ 5 identities riêng: Raw physical occurrence → observed source state → analytical episode → opaque dimension SK → fact resolved reference/request. Một source occurrence không tự cấp episode/SK; multiple observations có thể support cùng episode khi đủ continuity evidence. Registry, supersession/forward history và B9 exact predicates là dependencies, không transaction tables đã có.

Customer Type2 direction chỉ CustomerCategoryID/BuyingGroupID/BillToCustomerID; CreditLimit/hold optional chưa activate. Product Type2 chỉ UnitPackageID/OuterPackageID/QuantityPerOuter. Type1 chỉ admitted attrs; D1 nay chốt explicit selected-version set theo four anchors ở dưới. Exact selected attrs/versions/action scope của từng correction vẫn theo B7; không implicit current/all-version overwrite. Source bill-to master change không rewrite Invoices.BillToCustomerID hoặc default attribution BUYER.

| Case | Proposed propagation / existing constraint | Episode/SK behavior | Fact/mart effect và gate |
| --- | --- | --- | --- |
| New entity | Validate NK/incarnation/source evidence, admitted vector/basis | Registry new episode/SK chỉ khi identity đủ proof | Re-resolve eligible missing-ref requests; no historical backdate |
| Admitted Type1 update | B7 request chọn attrs/version scope/roles/periods/mode trước apply | Không tự tạo Type2 episode; SK meaning giữ | Refresh selected descriptors/segmentation và recert dependent views; chưa approve scope → hold correction |
| Approved Type2 update | Build candidate analytical episode theo tracked vector/validity evidence | Registry mapping persistent; no ROW_NUMBER/hash SK | Only affected roles/intervals, source fact measures/roles không đổi do master |
| Historical correction | Retain original/source-forward provenance, old/new mappings và authority | Boundary-only vs identity change phân loại trước rekey | Plan affected facts/KPI groups; không blanket restate mọi lịch sử |
| Boundary correction | Prove same NK/incarnation/vector/basis và unique continuity | B1 giữ episode identity/SK, audit validity revision | Re-evaluate requests tại affected boundaries/days; missing proof U, no proxy |
| Overlap/ambiguity | Thiếu proof khác proven conflicting intervals | Uncertain identity giữ Ambiguous; proven conflict không cấp arbitrary survivor | U otherwise-valid facts retained; proven integrity I block affected publication |
| Zero-duration | Giữ exact H evidence/multiplicity, interval không positive | Không tạo fake positive episode chỉ để lookup | No as-of match từ zero-length; preserve source→analytical lineage |
| Source disappearance | Accepted absence evidence theo INC-05, no default entity delete | Keep registry/history; retirement cần controlled approval | Không cascade/retract facts hoặc coi missing member là quantity0 |
| Reappearance | B8 continuity/incarnation investigation | Same entity vs new incarnation cần evidence; chưa đủ Ambiguous | Preserve old references; không reuse old SK cho nghĩa khác |
| Episode split | B1 explicit supersession old→replacement segments | New replacement identities/SKs cho positive segments, không first-segment survivor | Candidate fact remap by role/interval; old publications giữ old mappings |
| Episode merge | Chỉ compatible contiguous episodes có proof | Replacement episode/SK + supersession; no arbitrary old-SK survivor | Không merge A→B→A noncontiguous vì values giống; affected facts/marts recalc |
| Previously U becomes R | Same source fact/NK/role, accepted new evidence/basis và unique match | Resolve theo registry revision; member encoding chưa chọn | Update lookup/reference, preserve fact grain/amount/qty; controlled re-resolution, recert affected breakdown |

Historical lookup theo DW-02: exact-time eligible match hoặc date-only **whole-day one-episode consensus** có basis/coverage proof; không midnight/end-day/current/earliest fallback. Thiếu proof U; proven multi-match/precision corruption I. B4 Core giữ otherwise-valid R+U và NK/role/reason; no source-row drop. Incomplete source input không được relabel U để claim complete. B5 certification độc lập R/U/I.

B9 giữ nguyên F2 verified → Python str/None → bound psycopg → authoritative PostgreSQL TEXT, non-NULL27/seven digits và COLLATE "C" cho exact predicates. Không tạo formatter mới, rounded timestamp join, timezone/day-domain/business-effective meaning giả.

CP-02/B7 yêu cầu rekey plan ghi fact PK+role, old/new SK/episode/revision, affected interval/day, evidence/mapping rationale, source-measure invariant, dependency/old-new group diff và rollback target. Registry reservations/assignments khi build fail không được reuse SK đổi nghĩa; restore compatible registry/forward/supersession/publications set theo B2. Physical allocator/transaction/rollback algorithm còn Pending.


### D1 approved selected-version binding — effective Stage 3

Explicit Type1 selected-version set phải anchored đồng thời tới **pinned analytical base/publication**, **compatible accepted Raw publication**, **persistent dimension registry revision**, **recorded analytical build identity**. Selected members/field scope và source correction evidence được record reproducibly trong request/build lineage; selection không silently đổi khi build/retry, không resolve bằng dynamic current/latest/earliest. Content/generation/base mismatch → hold/revalidate/new controlled request, không mutate old selection.

Correction values từ compatible accepted Raw/source-forward evidence, theo controlled revision/restatement/B7; preserve approved analytical episodes/historical lookup/SK continuity, split-merge replacement/supersession, otherwise-valid U/source measures. No source-time→business-effective inference hoặc Type2 attribute changes. Current-only intent nếu có phải là exact explicit selected set trong approved request tại pinned base, không runtime default. Physical registry/member encoding/lookup/selection execution chưa được approve/tested.

No conflict found với accepted DW-02: D1 fixes logical selected-version contract, không revoke B7 per-request audit/reconciliation/rollback/field admission, B1 identity/SK rules, B3 lookup hoặc B9 exact text. Type1-only không tự cấp episode/SK hoặc thay transaction price/quantity; affected descriptors/groups recalc theo full affected-mart baseline.

## 4. CP-03 — Fact update, reclassification và restatement

Idempotency logical scope: compatible pinned evidence + source grain + transformation/correction/registry revision. Retry không là additive event. New model build có thể lưu separate immutable candidate output nhưng serving một row/grain trong accepted membership; append audit không đồng nghĩa SUM mọi versions. Upsert vs replacement là physical options chưa chốt.

| Fact | Source grain / update-replacement identity | Dependencies / lookup | Measure/correction/reclassification handling | Recalculation và idempotency | Reconciliation / publication gate |
| --- | --- | --- | --- | --- | --- |
| fact_invoice_line | Source system+InvoiceLineID trong generation; không InvoiceID×OrderLineID | Line+IH, DD invoice date, DC buyer/bill-to, DP product, registry revision | Replace exact quantity/tax/ExtendedPrice/optional LineProfit; header-only date/roles affect all lines. Master correction không thay invoice source roles/price; no recognized revenue/COGS | Recompute affected line PK closure từ pins; source key update khác new additive sale; union old/new invoice/product/role groups | PK coverage, amounts exact, S03=S04+S05; independent header S02/AIV; 0..1 eligible match/role, U retained/I block |
| fact_order_line | Source system+OrderLineID trong generation | Line+OH, DD order date, DC buyer, DP product | Quantity/PickedQuantity/nullable UnitPrice đúng source; header correction affects children; không tạo AOV/amount KPI mới | Recompute same PK, reparent OrderID/StockItemID old/new; keep orders no invoice; no InvoiceLine1:1 assumption | Source line count/qty/nulls; header count/repeat từ OH riêng; no fan-out |
| fact_stock_movement | Source system+StockItemTransactionID trong generation | Movement+DD/DP/DM references, optional invoice/PO diagnostic | Preserve decimal signed quantity/zero; changed date/type/item/link là update/reclassification cùng PK, không thêm movement mới | Rebuild same PK + old/new date/item/type/doc groups; approved removal action riêng | Per-PK/count/signed sums by type, issue group↔invoice-item group; no ABS-all hoặc holdings/daily balance inference |
| fact_inventory_current | Source StockItemID trong candidate current published state | Complete Holdings state + compatible current DP/Raw pins; không DD daily FK | Replace/rebuild current qty, no SUM across states; source absence !=0/delete. Product pointer change cần new compatible state, không mutate old published state | Baseline full current-state replacement; current SK lookup theo state pins; observed_at/extraction window và published_at riêng | Unique source item/current-state count+qty equality; incomplete/mixed Product-holdings hold, no historical daily state claim |

**CP-03 controlled restatement boundary; action procedure còn gated:** chỉ khi source/entity evidence và action scope được Owner duyệt theo B7/B8/INC-05; reference-only missing/candidate absence không xóa historical transaction fact. Correction request phải phân biệt observation membership, business retirement, source-record correction và historical fact retraction. Giữ before/after/source lineage; affected candidate output có thể exclude approved retracted PK, đối soát expected eligible population và explicit retraction accounting. Physical tombstone/encoding/action criteria vẫn open CP-03, không tự cascade hoặc purge.

FC/IC là current observation membership của complete compatible snapshot: đề xuất phản ánh item present/absent đúng observed state theo INC-05, giữ prior state/audit và absence candidate, không gán missing quantity0 hoặc retire entity. Đây khác historical transaction retraction; nếu chưa chứng minh đầy đủ membership/compatibility hoặc action semantics, hold candidate current publication và giữ prior state với đúng as-of, không claim nó là current source state mới.

Fact measures correction khác dimension-only rekey: rekey hợp lệ conserve original measures/NK grain, chỉ attribution/coverage thay; source measure correction cần exact old/new values. Chưa bound được affected interval → widen conservative scope/hold trước promotion. Reprocessing từ sealed compatible input không query latest để “sửa” history; generation mismatch phải new candidate/correction plan có proof, không ghép inputs hoặc regenerate SK.

## 5. CP-04 — Mart invalidation/rebuild alternatives

| Option | Ưu điểm | Trade-off / correctness obligations | Current Stage 2 disposition |
| --- | --- | --- | --- |
| A. Full rebuild từng affected mart từ complete pinned dependencies | Đơn giản, oracle dễ kiểm, loại stale old groups tự nhiên | Full read/compute/storage; phải complete input, atomic serving membership | **APPROVED — CP-04 baseline**, không rebuild unrelated marts |
| B. Affected partition replacement | Giảm work khi date/scope rõ | Union old/new partitions; rebuild toàn population trong partition, include unchanged rows; validate non-overlap/coverage | Deferred optimization sau measured evidence/full-equivalence tests |
| C. Targeted key-group recomputation | Scope nhỏ nhất khi closure rõ | Khó distinct counts/ratios/dimension grouping/empty groups; không chỉ aggregate changed rows | Chỉ proposal tối ưu riêng, không MVP default |

Không có benchmark/chi phí đo mới. A **APPROVED — Logical Policy, CP-04** làm correctness baseline; không physical partition/index decision hoặc runtime performance claim. Thiếu reliable impact closure thì full rebuild affected scope hoặc hold, không claim targeted completeness.

| Mart | Upstream dependencies / grain | Impacted grouping keys / scope | Proposed recalculation | Reconciliation | Publication eligibility |
| --- | --- | --- | --- | --- | --- |
| mart_sales_daily | FI+IH/DD; InvoiceDate | Union old/new InvoiceDate, header population cả no-line khi source thật complete | A full affected mart; B full old/new dates; line sums và header counts aggregate riêng trước join1:1 date | S02 từ all IH; S03/S04/S05 same population, S06 ratio recomputed numerator/denominator, S09 optional | Compatible complete IH/FI/date pins, no count fan-out/missing-line-as0; B5 thresholds trước Certified |
| mart_sales_product_daily | FI/DD/DP; InvoiceDate×StockItemID | Old/new date/product; descriptor/registry mode revision nếu view dùng | A; B/C recompute all matching lines trong affected groups, remove empty group | Source amounts/qty by NK/day; distinct invoice counts không cộng across products; standard S06 không đổi denominator | Approved product-filter semantics, historical breakdown coverage/certification riêng; no NK→all SK join |
| mart_customer_sales | FI/IH/DC/DD; InvoiceDate×source CustomerID×customer_role | Old/new dates + Buyer/Bill-to keys **từng role**, affected label/episode views | A per declared role/view dependency; recompute group complete; rekey không tạo extra role rows | Mỗi role riêng total=S05, BUYER mặc định explicit; no SUM cả roles, no payment allocation | Single-role aggregate contract và pinned mapping; source-role totals/coverage validated; C03/C04 giữ scope |
| mart_customer_repeat_monthly | OH/DD/DC; OrderMonth×Buyer CustomerID | Old/new buyer-month/date ranges, quarter request phải dùng all-quarter OH | A; B/C group all distinct orders theo eligible OH, không chỉ changed lines/headers | S01/C01/C02; repeat numerator≤active denominator; NULL when denominator0; distinct buyer across periods tính lại | Complete all OH including uninvoiced/no-line, no product-filtered variant chưa duyệt; rates không average/sum |
| mart_inventory_movement_daily | FM/DD/DP/DM; movement date×StockItemID×TransactionTypeID | Old/new date/item/type, reference label/mapping revision | A; B/C complete group recompute preserves negative/zero values | Count/signed quantity by type, I01 type10 issue sign convention, I02 type11, I03/I05 optional | Complete movement/type contract/pins, no daily balance claim, no unapproved type classification |
| mart_inventory_current | FC/DP same state; StockItemID | New current-state membership, changed holdings/Product references | A full current replacement ưu tiên scale nhỏ; no snapshots sum, no “latest DP” dynamic join | Count/source item/QuantityOnHand same observed state, I04 total; observation/publication metadata rõ | Complete Holdings/Product compatible state, no partial snapshot→zero/delete; current data khác historical daily balance |

**Empty/old groups:** grouping key move cần candidate old group được recompute về đúng new result hoặc remove khi không còn population; không chỉ upsert new group. Nếu zero/dense calendar rows được dùng, phải có approved complete-coverage semantics, không fill missing data bằng0. Unchanged rows cùng group vẫn thuộc recompute population.

S01/C01 arbitrary date ranges vẫn từ OH, không phân bổ monthly RM xuống ngày; quarterly repeat phải tính lại từ OH toàn quý. C05 optional current customer category từ current DC một row/NK, không tạo mart thứ7 hoặc count versions. Type1/historical label mode không tự được chọn bởi rebuild method; B7 approval riêng trước descriptor restatement.

## 6. CP-05 — Approved analytical publication and D2/D3 contracts

**Durable logical identity/pinning obligations đã Approved; tên dưới đây là contract labels, chưa physical schema/ID algorithm:** source Raw publication pin set; build_request_id; execution run/attempt IDs; model_build_id cùng code/contract/policy/registry/evidence revisions; correction/restate request; candidate analytical_publication_id; manifest/member refs; prior/predecessor publication; consumer consumption/ACK refs. Raw publication ID không là analytical publication ID hoặc dimension SK. Hash chỉ integrity aid, không source-occurrence/episode identity.

Một build request xác định immutable inputs, dependency closure, reporting scope/period/filter/role, registry mapping revision và requested certification tier. Same request+same content có thể reuse accepted outputs nếu exact compatibility/reconciliation proof; same identity+different content là conflict. New code/policy/upstream generation tạo request khác, không silently resume old one.

~~~mermaid
flowchart LR
    R[Accepted Raw pin set] --> S[Staging build]
    S --> D[Dimension and registry revision]
    S --> H[Header intermediates]
    D --> F[Fact builds]
    H --> F
    D --> M[Mart builds]
    F --> M
    H --> M
    M --> Q[Reconciliation and tier gates]
    Q --> P[Candidate publication manifest]
    P --> A[Atomic compatible visibility]
    A --> C[Consumers pin analytical publication]
~~~

Graph mô tả dependencies, không yêu cầu mọi model rebuild nếu unchanged output đã được chứng minh compatible. Inventory current có DP-current/state dependency riêng; Financial transactions là reconciliation support, không fact thứ5. DD và DM required reference/calendar dependencies phải explicit, không tạo source contract ngoài scope.

### AP01–AP06 — logical gates, không runtime PASS

| Gate | Required inputs | Required durable evidence | Expected logical state | Failure outcome | Publication blocker | Recovery responsibility | Runtime proof required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AP01 Raw acceptance/pins | Accepted Raw manifest/context C/generation, INC checkpoint+scope/contract/projection revisions | Accepted ledger/member/content, no-writes or approved copy proof, source-state coverage/recon, ACK01–06 bindings | Eligible pinned source set; không Raw→Certified auto | Hold downstream complete claim, retain diagnostic input refs | Unaccepted/incomplete/mixed/qualified-use-unapproved source state | Ingestion/source DBA+ DQ reviewer; Owner method authorization | Actual source consistency/access/fidelity/key-value/H multiset and checkpoint read-back before downstream use |
| AP02 Dependency graph | Declared target KPI/view scope, stage/header/dim/fact/mart builds, code/registry/reference/policy versions | Complete immutable graph/member manifest, shared dependency compatibility and old/new impact closure | Compatible dependency-complete subject/view candidate under approved D2; cross-subject candidate needs verified joint consumer manifest | No latest-per-model substitution, no cross-subject consistency overclaim | Missing dependency/pin/shared compatibility, incompatible registry/generation, absent/invalid joint proof → hold cross-subject certification/publication | DW/storage/consumer owner+ DQ; DQ/consumer verifies approved D2 scope; Owner reviews concrete execution release | Model pin/read isolation/compatibility and consumer refresh tests CP-T01/17/23/28/30 |
| AP03 Registry/lookup integrity | Source occurrence/forward evidence, persistent registry/supersession, accepted lookup basis and role requests | Exact B9/whole-day proof, per-fact-role before/after/R-U-I/registry refs; frozen D1 selected set/four-anchor/build reference and B7 correction scope | R/U/I correctly classified; explicit D1 selection reproducible/frozen under compatible anchors | Proven I hold affected closure, valid U retained in Core, no fallback | Conflicting identity/precision, unsupported current/earliest match, missing/mutated selected set, incompatible anchor or unapproved field/action scope | DW/registry custodian+ DQ; Owner correction plan review | CP-T06–15/29 full registry/lookup/restore correctness, no SK reset/unsupported history |
| AP04 Reconciliation/quality | Complete candidate source-model populations, approved KPI grain/date/role/formulas, old/new corrections | Per-key counts/values/groups, source-measure invariants or explained corrections, NULL/signed/absolute diagnostics and approved disposition | Reconciled candidate, not Certified yet | Hold failed/incomplete/invalid closure, no tolerance invented | Missing keys/groups, fan-out, stale empty groups, dropped U/I or unexplained differences | DQ+model owners; Owner approves exceptions/values | CP-T03/04/16/18/19/24, full affected-mart oracle, ratios/distinct/population equality |
| AP05 Tiered certification | Requested KPI/view/filter/period/role dependencies, coverage evidence, approved threshold-policy revision | Row+value coverage/check result, eligibility/basis/policy/accepted model pins; D3 action authorization when lifecycle affected | Eligible certificate for explicit view only; unproven breakdown Uncertified | No whole-dashboard certification from subset; known-invalid state marked for governance review/hold | B5 numeric thresholds not approved, incompatible dependencies, integrity fail; per-incident Owner authorization required before revoke/reinstate/rollback, no valid certified replacement → hold | DQ detects/collects/recommends; Owner authorizes lifecycle/threshold values; Operator executes authorized transition/audit | CP-T13/18/19/30 per-view tier boundary and invalidation/rollback tests under approved D3 logical policy and per-action authorization |
| AP06 Durable promotion/ACK | Complete approved publication unit from D2, manifest/membership/certification result, expected predecessor/content and per-action Owner authorization + existing compatible validated appropriately certified rollback target when relevant | Durable acceptance/commit outcome, pointer transition/member/checkpoint bindings, consumer pin acknowledgements/audit | One coherent accepted analytical revision, ACK only after read-back; physical status Unverified | Unknown commit inspect durable state; same request reuse accepted result, stale/conflicting request hold | Unknown outcome, partial visibility, pointer regression, missing D2 consumer enforcement or unauthorized D3 lifecycle transition | Storage/orchestration+consumer owner+ DQ; Owner release/rollback authority | CP-T20–30 actual ACK-loss/retry/race/fencing/transaction/consumer visibility proof; no task-success-only advance |

B5 đã approved **Tiered Certification**: R/U/I là lookup axis khác Certified/Uncertified. Không chọn numeric coverage/reconciliation tolerance. Enterprise/NK-source KPI có thể được certify riêng **sau** đủ population/integrity/recon/approved thresholds, không certify toàn mart/dashboard hoặc historical segmentation đang thiếu proof.

Atomic **visibility** cho declared dependency-complete analytical scope/view set, không khẳng định distributed transaction xuyên Raw/dbt/Power BI. Candidate model data có thể persist để retry nhưng normal readers chỉ thấy accepted manifest; staging done/dimension done/mart done riêng không tự publish Certified. Promote coherent mapping of required Core/dim/mart builds + per-view certification revision, current analytical pointer và durable acceptance; physical transaction/schema/locking/CAS/swap chưa chọn. CP-05/06 logical policies đã Approved; D2 subject/view unit và D3 role/governance đã Approved; physical/runtime enforcement/proof vẫn Pending.

Consumer/report refresh phải pin exact analytical publication/certification membership cho toàn query/refresh, không đọc latest riêng mỗi table. Old valid publication giữ lineage/as-of và compatibility khi new candidate fail; không silently move Raw pointer về cũ hoặc gọi old publication “current source state” sau source correction. Nếu known integrity error ảnh hưởng publication đã Certified, đề xuất hold/review affected certification/revocation, cảnh báo scope; D3 authority nay Approved: DQ/Validation detects/collects/recommends, Project Owner authorizes revoke/reinstate/rollback, Operator executes authorized transition with durable audit. Consumer pins phải được notify/block theo approved policy, không tiếp tục claim known-invalid Certified validity; actual channel/RBAC/enforcement proof vẫn implementation gates.

Rollback theo D3 chỉ được chọn **existing compatible validated appropriately certified target** với per-action Owner authorization, audit/new controlled transition; không xóa Raw/build/registry evidence hoặc tái dùng SK đổi nghĩa. Nếu prior inputs/schema/registry không còn compatible, hold/manual recovery, không pointer rollback đơn lẻ. Nếu không valid replacement thì hold affected publication, không expose uncertified fallback. Source supersession không tự invalidate tất cả successful historical builds, nhưng stale candidate không được promote như newest state nếu predecessor/generation request không còn hợp lệ.

## 7. CP-06 — Failure, retry và concurrency matrix

Proposal separates raw acceptance checkpoint, downstream build progress, analytical publication acceptance và consumer acknowledgement. Raw checkpoint đã accepted không lùi vì mart fail; downstream ACK chỉ sau AP01–06 và durable read-back, không theo task exit0. Theo [DW-03B ACK01–ACK06](wwi-dw-03b-incremental-design-proposal.md), giữ source identity/content/consistency/recon/commit/predecessor/pins; CP không sửa ACK contract.

| Case / failure boundary | Durable evidence required | Safe retry behavior | Idempotency scope | Conflict detection | Rollback/compensation | Publication eligibility | Manual trigger |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CP-R01 RawPublished, downstream never starts | Raw accepted manifest/pins, intended request/consumption ledger, no fabricated build completion | Discover unconsumed accepted pin set, create/resume logical downstream request | Same Raw pins+code/policy/registry/request | Different source generation/code or already accepted downstream result | Giữ prior analytics, Raw không rollback | Chỉ sau dependency builds/AP gates, không Raw→Certified tự động | Missing intent/evidence/pins hoặc provenance không khôi phục |
| CP-R02 Staging complete, dimension fail | Sealed staging build manifest/inputs, registry reservations/revisions, dimension failure reason | Reuse staged content nếu exact fingerprints compatible; retry dimension candidate | Same staging/policy/registry lineage | Changed input/canonicalization hoặc registry identity conflict | Prior publication retained; no opaque SK reuse/purge | No partial dimension visible as accepted analytics | Registry ambiguity, no compatible recovery set |
| CP-R03 Dimensions complete, fact fail | Candidate dimension/registry manifests, old publication pins, fact attempt/chunks | Reuse complete compatible dims; rebuild affected fact scope từ same pins | Same dimension revision + source PK/correction request | Stale registry revision, duplicate grain/dangling FK | Giữ old compatible fact-dim publication, candidate invisible | Chưa fact/recon/marts thì no promotion | Cannot prove stable mapping/supersession/ref integrity |
| CP-R04 Facts complete, mart fail | Accepted candidate fact/header/dim inputs, mart scope/old-new groups | Recompute affected mart A/B/C từ full declared population | Same mart request+pinned dependencies | Different role/filter/period/input versions | Non-promotion; không expose mixture new facts/old certified mart | All dependencies cho selected tier/view đủ AP gates | Missing old scope/evidence hoặc ambiguous output membership |
| CP-R05 All builds done, reconciliation fails | Exact expected/actual count/key/value/group diffs, validation-policy revision | Re-run checks same immutable content; correct via new request nếu input/code đổi | Same validation request/content | Netting totals hide per-key differences, coverage unknown | Hold candidate; no numeric tolerance tự đặt | Không promote failed/incomplete/invalid scope | Unexplained drift, invalid data/threshold cần Owner |
| CP-R06 Certification commit success, ACK lost | Durable analytical acceptance+manifest/membership+certification/pointer outcome+predecessor | Read-back accepted result, return same logical ACK; newer pointer không lùi | Same publication request/content | Commit unknown vs accepted vs conflicting revision | No blind double publish; known noncommit mới retry with guards | Eligible once durable acceptance/compatibility proven | Outcome unresolved hoặc ledger/member mismatch |
| CP-R07 Same source publication processed twice | Request fingerprint, accepted build/analytical publication IDs/content | Reuse/return same accepted result when truly same request; new code/policy là request mới | Raw pins+code/policy/registry+reporting scope | Same ID different content hoặc duplicate accepted grain | No additive facts/mart deltas hoặc extra episodes | Same result only after AP validation, no current-pointer regression | Conflicting requests without lineage |
| CP-R08 Two runs target same analytical publication | Expected predecessor/revision, input/content fingerprints, accepted outcome/attempt lineage | Equivalent-content loser reuses winner; differing content hold/review, not last-writer-wins | One logical target request/content | Compare source/registry/model versions/predecessor, no assumed wall-clock ordering | Retain losing candidate evidence, published winner unchanged; no SK meaning rollback | Coherent single accepted outcome, physical fencing/locking unchosen | Unresolvable race/multiple accepted outcomes |
| CP-R09 Previous Raw publication superseded | Old/new accepted Raw lineage/generations, target request freshness intent and current analytical parent | Finish old pinned build as traceable historical candidate if eligible; latest promotion revalidate/new request | Explicit old/new pin set, not “latest” query | Stale-parent/new-generation incompatibility | No silent Raw/analytics regression; preserve prior valid set | Do not promote stale as newest; historical scoped use needs declared intent/approval | Missing generation bridge or policy on outstanding requests |
| CP-R10 Historical correction/restatement | B7 approval, affected NK/roles/intervals/old-new group maps, per-key before/after+pins | Candidate re-resolve/recompute facts+complete affected groups, reuse compatible evidence only | Correction request+mapping/source revision | Duplicate apply, changed scope/payload, unapproved Type1 mode | Prior compatible publication retained, rollback whole affected closure not measures-only inverse guesses | Recon/certification review và atomic compatible revision | Cannot bound impact/old proof/authority hoặc known prior certification error |
| CP-R11 Episode split/merge | B1 replacement identities/supersession, registry+exact intervals, affected fact-role map | Retry same registry assignments/mapping request, rekey/restate affected closure | Same correction/registry revision | Arbitrary survivor/SK reuse, noncontiguous merge hoặc >1 match | Preserve old IDs for old publication; no delete/recycle registry | New compatible dim/fact/mart mapping + coverage gates | Missing lineage/ambiguous episode identity/restore mismatch |
| CP-R12 Recovery observes changed upstream generation | Pinned original generation/context + new generation evidence/schema/policy bridge | Do not mix; resume sealed original if available/declared, otherwise hold/new request+rebaseline review | Original capture/request distinct new source context | Restore/reset/schema/contract/registry incompatibility | Retain diagnostics/prior accepted set, no splice/assume equivalent rebuild | New generation promotion only after consistency/recon/mapping proof | Lost original evidence/registry/forward history or unsupported remap |

**CP-06 guarded recovery đã Approved; physical alternatives chưa chọn:** serialize logical publication promotions; optimistic predecessor/content validation; or broader parallel builds with guarded promotion. Approved direction cho phép isolated candidate work nhưng một accepted transition cho cùng logical target/predecessor, durable evidence trước ACK. Exact locks/CAS/isolation/fencing/allocator/config/deadlock retry policy vẫn proposal riêng; không khẳng định runtime safety đã kiểm.

## 8. Reconciliation, data quality và impact completeness

[Source Validation Matrix](../requirements/wwi-source-validation-matrix.md) I01–I12 vẫn dùng ở Raw; DW-03B state equality/multiset proof là input. Downstream checks đề xuất:

| Boundary | Reconciliation contract | Failure behavior |
| --- | --- | --- |
| Raw→Staging | Exact accepted source keys/fields/types/NULL/time/origin/multiplicity; no filter drop unless approved model population | Hold complete projection/fidelity claim, preserve original evidence |
| Staging→OH/IH | One header/source PK; independent all-header population, optional FK/no-line/uninvoiced preserved | Missing batch/header not zero/count0; no line-derived invoice/order population |
| Evidence→DC/DP/registry | Occurrence lineage vs episode/identity, continuity/supersession, 0..1 valid role lookup, R/U/I partition | Proven I block dependency closure; U retained otherwise-valid Core; no fallback |
| Sources/headers→facts | Source PK uniqueness/count/eligible membership, per-key measures/qty/date/roles, raw+mapping revision pins | No duplicate additive updates or dropped U, no financial/movement fan-out |
| Core→marts | Complete group population, old/new group union, ratios/distinct recomputed, per-role and signed/absolute/NULL diagnostics | Totals equality alone không prove groups/keys; remove stale empty groups in candidate |
| Builds→Certified | Per KPI/view/filter/period lineage/threshold policy, row+value coverage, complete compatible graph, durable promotion | B5 thresholds missing → no Certified; no partial certified state; scope-aware hold |

Rekey-only source fact measures conserved; source amount correction compares exact approved before/after values with source, không force unchanged total. Expected coverage không suy từ extracted/accepted count nếu original scope incomplete. Numeric coverage/tolerance/severity/noise thresholds vẫn pending Owner, không tự đặt100% hoặc ratios để pass.

Sales source header/input completeness khác historical dimension U: otherwise-valid source facts có thể Core U theo B4, nhưng thiếu whole input stream phải hold complete-input claim, không unknown-member để che missing rows. Invalidation closure unknown → conservative affected subject/period scope hold; independent validated tiers có thể assessed riêng theo B5 khi dependency proof đủ.

Theo B4, accounting trên complete declared population/cùng source fact grain phải tách R/U/I disjoint: any required role I → fact I; otherwise any U → fact U; đủ required roles R → fact R. Expected source rows = R+U+I chỉ khi completeness đã prove; I retained/audited và block affected publication, không loại I/U khỏi denominator để tăng coverage. R/U/I lookup không đồng nghĩa certification status, và equation không là numeric quality threshold mới.

## 9. Proposed integration test matrix

Mọi **CP-T01–CP-T30 = PLANNED / NOT RUN**. Không fixtures/source updates hoặc builds thực thi trong Stage 1. Dùng CP-R cases và existing CD-T/IT specs làm dependencies, không lấy B9 precision PASS thay downstream tests.

| Test | Preconditions / input change | Expected assertions / output | Recovery / gate coverage |
| --- | --- | --- | --- |
| CP-T01 | Accepted invoice/header+lines pins; chỉ đổi InvoiceDate/buyer/bill-to | FI all related PKs re-evaluated dù line LEW không đổi, SD/SP/CS old/new groups đúng, roles riêng | CP-01/03/04; no line-only detection |
| CP-T02 | Accepted OH; chỉ đổi OrderDate/buyer, gồm uninvoiced/no-line headers | OH/FO propagated; old/new buyer-month recompute, S01/C01/C02 đúng, no Invoice population substitution | Header-only/incomplete group negative |
| CP-T03 | Same InvoiceLineID sửa ExtendedPrice/TaxAmount/qty | Same grain update, correct new measures, no additive duplicate; AIV numerator/header denominator same pins | Per-key vs aggregate equality |
| CP-T04 | Line đổi parent/product/date group, old group trở nên rỗng | Union old/new child/group closure, remove stale row, recompute all unchanged members in groups | Full rebuild oracle vs partial replacement |
| CP-T05 | New entity/new order line/replayed source capture | Correct registry only when evidence, one fact/key, no artificial order count theo line, no fake history | New entity/idempotency |
| CP-T06 | Approved D1 four-anchor contract, future authorized environment/action scope; admitted Type1 correction, explicit frozen selected-version plan | No new Type2 episode; selected label scope only, unapproved mode rejected, grouping/recert impact audited | B7 before/after/rollback |
| CP-T07 | Approved Type2 vector và late historical evidence | Candidate episode/mapping theo proof; only affected role/time requests re-resolve, no source price rewrite | B3/B6, no business-time inference |
| CP-T08 | Boundary-only correction with proven unique continuity | Same episode/SK, validity revision audit, exact-time/full-day requests re-evaluate | B1/B9 precision |
| CP-T09 | Approved episode split proposal input | Replacement IDs/SKs, supersession/role rekey, old publication mappings retained, no first-segment survivor | CP-R11, registry recovery |
| CP-T10 | Contiguous merge và negative noncontiguous A→B→A | Replacement identity only valid merge; noncontiguous collapse rejected; totals conserved on rekey | CP-R11, identity conflict |
| CP-T11 | Previously U fact, new eligible unique dimension evidence | Same fact PK/measures, source NK/reason retained audit; U→R candidate, affected breakdown recert only after gates | B4/B5 re-resolution |
| CP-T12 | Direct H zero-duration/duplicate-start/duplicate occurrence corpus | Raw multiplicity exact, no fabricated positive lookup episode, text100ns not rounded | B9/occurrence vs episode |
| CP-T13 | Missing basis/coverage vs proven overlapping/multi-match periods | Lack proof→U, proven conflict→I block affected closure; no MAX/current/earliest fallback | Core R+U, no partial Certified |
| CP-T14 | Partial snapshot absence, complete candidate absence, separately authorized confirmed retraction | Partial not evidence; candidate no business deletion; controlled action only explicit scope, no historical purge | INC-05/B8/CP-03 |
| CP-T15 | Entity disappears/reappears same NK, continuity evidence missing/present | Ambiguous when missing; new incarnation only evidence; no SK meaning reuse | Registry/entity lifetime |
| CP-T16 | Movement decimal quantity/sign/date/type/product correction | Same movement PK; signed/zero values preserved, old/new groups recomputed, no holdings balance | FM/MD/type contract |
| CP-T17 | Complete holdings/Product state and incompatible state negative | FC/IC same compatible current state, observed_at và published_at có ngữ nghĩa riêng, no SUM states/daily-history claim | Current DP lookup/pins |
| CP-T18 | Multiple payments InvoiceID NULL; Buyer≠Bill-to | No allocation/fact-to-fact join, separate role totals=S05, no enterprise double count | BRD-08/10, CT recon only |
| CP-T19 | Header populations/products/time filters và buyer một order mỗi tháng | Distinct invoice product counts not additive, monthly vs quarterly repeat recomputed, no average rates/AIV | Six mart grain/denominator controls |
| CP-T20 | Raw accepted, downstream request never starts | Recover unconsumed accepted request, old analytics retained, Raw checkpoint không lùi | CP-R01 |
| CP-T21 | Staging sealed, dimension build failure mid-registry | Reuse compatible stage, no conflicting registry SK allocation, no candidate exposure | CP-R02 |
| CP-T22 | Dim/registry complete, fact partial failure | Retry exact pinned fact scope, no dangling/mixed-generation FKs or duplicate facts | CP-R03 |
| CP-T23 | Facts complete, one required mart fails | No mixed/new partial certified state, selected tier manifest remains unpromoted | CP-R04 |
| CP-T24 | All builds done, key/group recon mismatch though net totals equal | Hold, per-key/group missing/extra detected, no invented tolerance | CP-R05 |
| CP-T25 | Certification commit outcome/ACK lost | Durable manifest/ledger/pointer read-back determines same accepted result; unknown hold, no blind publish | CP-R06/ACK01–06 |
| CP-T26 | Same request replay và two equivalent concurrent attempts | One logical accepted result, second reuses; no additive measures/episodes/pointer regression | CP-R07/08 |
| CP-T27 | Concurrent differing content/stale predecessor | Conflict/hold or reviewed new request; no last-writer-wins; losing candidate retained | CP-R08 |
| CP-T28 | Raw supersession/restore changed generation during recovery | Old pinned output not promoted as newest; no mixed generations, missing bridge manual hold | CP-R09/12 |
| CP-T29 | Approved historical restatement + failure/rollback/new retry | Complete old/new scope, compatible registry+forward/Raw/build set retained, no inverse-delta guess or rekey drift | CP-R10/11/B2/B7 |
| CP-T30 | D2 Logical/D3 Governance Approved, B5 values/per-action authority và runtime setup required trước test; tiered refresh, historical U và invalid certificate/rollback cases | Independent eligible view only, unproven breakdown Uncertified; invalidate/reinstate/rollback only approved authority+compatible target, consumers pin/see scoped lifecycle state | CP-05/B5, atomic visibility |

Future environments: independently approved writable SQL Server sandbox for controlled source changes (original WWI read-only), separate approved PostgreSQL Raw/staging/Core/mart/control sandbox with schema/write authorization, approved transformation/test environment and separate orchestration/consumer simulation when relevant. Existing B9 sandbox không dùng/sửa trong task này, không auto provision. Test scripts/fixtures/dependencies/version pinning/access controls và performance budget cần task/approval riêng. Static docs QA không là execution of any CP-T.

Future evidence mỗi test: scenario/input fixture revision, expected vs actual PK/values/groups/lookup/manifest, pinned generation/model/registry revisions, failure injection boundary, retry/attempt/outcome proof và certification visibility/consumer pins. Source payload/credentials không commit; không benchmark trước measured test.

## 10. Stage 2 focused design review — historical pre-approval record

**Historical boundary:** toàn section10 giữ Stage2 alternatives/recommendations/Pending/blocker evidence trước Stage3 Owner approvals. Không current status/authority hoặc reason giữ task mở; current approved binding tại sections3/6/12 và register. Các trạng thái tại section này khác CP approvals: **D1–D3 PENDING OWNER APPROVAL**, **D4 CONFIRMED — existing approved baseline**. Không có quyền chốt D1–D3 bằng implementation judgement hoặc dùng QA PASS thay Owner approval. Phần D1/B7 invariant đã accepted không được mở lại.

### D1 — Type 1 selected-version contract

**Verified — document review:** Final SCD2 section B7 và ADR-SCD-01 chỉ chốt request phải khai báo NK/incarnation/admitted attrs/roles/affected intervals/selected versions, audit/recon/rollback. Các documents nói rõ **không default current-only hoặc all-version overwrite**, mode/exact selected scope review trước execution. Vì vậy không có accepted global Type1 mode để tự áp; CustomerName còn candidate nếu chưa admitted, AccountOpenedDate correction không tự Type2/KPI mới.

| Choice | Selection reference | Benefit | Risk / effect |
| --- | --- | --- | --- |
| A. Explicit current-only | Current episode/version ở **target base analytical publication+registry revision**, không dynamic runtime is_current | Scope nhỏ, thuận current labels | Không sửa retained historical versions khi đó là intent; reports phải nói current-label mode |
| B. Explicit enumerated version set | Request liệt kê exact eligible episode/version IDs/SKs/revisions từ pinned target base; có thể singleton current hoặc retained selection | Exact auditable scope theo B7, không implicit blanket overwrite | Cần impact closure và chứng minh selected versions cùng entity/generation; request review overhead |
| C. All retained eligible versions | Explicit request enumerates toàn eligible versions của NK tại base revision | Nhất quán label khi correction có evidence áp toàn bộ | Broad historical regroup; không được default, không sửa Type2 identity/vector hoặc invent historical meaning |

**Recommendation B — Pending Owner Approval.** Đây là selected-version/reference-point policy đề xuất, không tự approve A/C hoặc chính sách default mới. Mỗi request vẫn cần Owner-approved admitted-field/action scope theo B7.

- **Selection reference point:** declare target prior accepted analytical publication P_base + registry revision, NK/incarnation/roles/fields, explicit version member IDs và correction intent; không lựa chọn bằng latest lúc retry.
- **Source publication pin:** correction values/provenance lấy accepted Raw R_correction (và compatible source/forward evidence khi cần) với source generation/contract/context C; target/base Raw pins có thể khác publication nhưng phải có continuity/compatibility proof, không infer business-effective date.
- **Generation compatibility:** source identity/incarnation, registry/supersession mapping, schema/code/policy/basis revisions phải compatible; changed generation hoặc accepted target base superseded cần revalidation/new request, không reuse stale selection tự động.
- **Correction behavior:** candidate attribute-value revision trên exact selected set; original evidence/prior publications giữ nguyên. Type1-only không tự tạo Type2 episode/new SK hoặc đổi nghĩa accepted key; separate Type2/source-measure change phải own evidence/request.
- **Facts/marts:** source fact grain/measures/roles invariant cho Type1-only; dependent descriptors/filter groupings và certification re-evaluate, full affected-mart rebuild theo CP-04. Fact FK rekey chỉ khi separate approved mapping correction đòi hỏi, không vì label thay.
- **Reconciliation:** selected versions/attrs before–after đúng request, unselected versions preserved, stable episode/SK map, fact population/measures conserved, old/new groups and per-role totals/coverage accounted. Không claim chỉ totals equality đủ.
- **Approval needed:** Owner accept reference-point + explicit set mode B hoặc chọn A/C và report implications; per-request field/scope approval vẫn required. Physical selected-member encoding/algorithm còn runtime gate. D1 là approval boundary còn mở, không missing B7 approval.

### D2 — Analytical publication unit / cross-subject compatibility

CP-05 đã approve dependency-complete atomic visibility/pins, nhưng **smallest concrete unit và enforcement/combination rule chưa fixed** bởi A06 Raw scope hoặc Stage 1 proposal. Không coi Raw snapshot ID là analytical shared commit.

| Choice | Unit | Sales-first / compatibility implications | Recommendation |
| --- | --- | --- | --- |
| A. Platform-wide atomic | All subject facts/dims/six marts trong một revision | Simple all-platform pin nhưng coupling Sales với future Inventory, large rebuild scope | Không khuyến nghị initial MVP |
| B. Dependency-complete subject/view bundle | Declared selected KPI/view scope + all transitive required builds/mappings/reference/header populations | Sales views publish khi own closure complete, no need unrelated marts; shared dependencies phải pinned compatible | **Recommended — Pending Owner Approval** |
| C. Mixed publications with explicit compatibility | Multiple accepted subject/view revisions combined by declared compatibility/consumer contract | Flexible, nhưng độc lập latest pointers không prove joint state; registry/Raw/filter cross-check phức tạp | Future option, không implicit MVP default |

**Recommended B design, chưa được Owner chọn:**

- **Smallest safe unit:** selected KPI/view+period/filter/role scope và transitive dependency closure, gồm complete numerator/denominator/populations; không một model task tùy ý. Nếu view bao gồm count/AIV thì IH population là required dù some headers no-line. Scope không bị cắt sau failure để che missing rows.
- **Shared compatibility:** reuse unchanged DD/DC/DP/reference/registry/model builds chỉ khi exact pinned revision/content hoặc explicit compatibility evidence chứng minh all requested references/validity/admitted attrs/policies không conflict. Same NK/SK labels không đủ. Future Customer/Inventory publication phải own closure và consistent input proof; không mix observation generations thành global source snapshot.
- **Consumer pinning:** one refresh/query chooses accepted analytical bundle ID+exact member/certification revisions. Dashboard cross-subject muốn joint guarantee phải có **joint consumer manifest** chứng minh union closure compatibility; nếu không có, report từng as-of độc lập, không cross-publication consistency claim.
- **Version identity:** bundle identity riêng build/run/attempt/Raw/SK; bind source pin set, code/contracts, registry/supersession, policies, model membership, certification scope và predecessor. Physical ID encoding/table/cache mechanism chưa chọn.
- **Promotion boundary:** AP01–AP06 cho selected closure, guarded coherent visibility của membership+certificate/pointer transition; no distributed transaction assumption. Missing D2 consumer/shared compatibility contract → hold final eligibility.
- **Supersession:** new accepted revision declares predecessor/affected view scope; old pins/audit retained. Retries return same accepted result; source supersession không authority move pointer backwards hoặc claim older source is newest. Invalid certification lifecycle governed D3.
- **Sales-first:** first approved Sales view bundle includes only its complete required Sales/master/header mappings; Customer/Product dependencies không buộc hoàn thành full Customer Analytics/Inventory marts. Exact initial view set/pins vẫn declared/reviewed, không tự đổi rollout scope.
- **Approval needed:** Owner choose B unit/combination rule hoặc A/C with trade-offs. Physical enforcement proof tiếp tục deferred; choice itself chưa bị gắn runtime PASS.

### D3 — Invalid Certified data, revocation và rollback governance

**Already approved:** B5 scoped tiering, no false Certified claim, CP-05 previous valid versions/non-partial visibility, CP-06 guarded/durable transitions. **Not established:** approval chain cho revocation/reinstatement/rollback và consumer invalidation semantics; AGENTS Owner authority không tự là full operational delegation policy.

**Recommendation — Pending Owner Approval:** Project Owner là authority phê duyệt revoke/reinstate/rollback và affected scope; DQ/data owner records anomaly và holds candidate/promotion theo existing integrity gates; operator executes only authorized auditable transitions. Không tự cấp quyền revoke cho scheduler/DQ runtime hoặc giả đã có approval cho rollback.

| Situation | Proposed hold/invalidate handling | Authority / evidence / consumer effect |
| --- | --- | --- |
| Candidate build/reconciliation/certification fail trước promote | Existing gates hold/non-promote, prior compatible valid state retained với đúng as-of | Failure/validation/member refs; no candidate labeled Certified, no source checkpoint regression |
| Proven integrity/amount/pin/generation defect trong publication đã Certified | Flag affected scope as invalid-for-further-claim/review, investigate closure; formal revoke/invalidate transition theo Owner-approved D3 policy | Owner authorizes affected certificate/publication action; evidence reason, impacted descendants/consumers/periods, policy/actor/time; no destructive delete |
| Missing coverage/threshold-policy applicability sau change | Do not silently continue/regrant Certified; proposed hold/re-evaluate relevant KPI/view tier | Threshold-policy revision và actual coverage, no invented numeric tolerance; unrelated independently valid scopes reviewed riêng |
| Proposed rollback to prior publication | Chỉ allowed khi Owner approve và target proved valid/compatible; otherwise hold/manual correction | Validate Raw/source as-of/generation, registry/SK/graph/schema/code/policy, required tiers/reconciliation/consumer pins và known-error exclusion |
| Corrected rebuild / reinstatement | New candidate content/revision re-evaluated AP gates; Owner lifecycle approval khi required | New certification/pointer transition audit, no mutate old content hoặc declare old invalid output “fixed” by pointer only |
| Supersession without proven defect | New accepted revision marks predecessor superseded, không đồng nghĩa old output historically invalid | Old consumer pins retained with exact historical as-of; no latest freshness claim or automatic revoke |

**Rollback conditions đề xuất:** prior target không thuộc known invalid closure; source state/observation as-of disclosed; source/registry/forward/supersession/model schemas and dependencies compatible; certification policies/threshold approvals still applicable hoặc revalidated; counts/keys/measures/roles/coverage pass; predecessor/content/durable outcome guards và consumer pin set complete. Không rollback một dimension pointer riêng khỏi referenced facts hoặc reset registry/SKs. Raw checkpoint không lùi vì analytics rollback.

**Audit contract đề xuất:** incident/correction/request IDs, defect evidence/rule version, old/candidate/target publications and certification members, dependency/consumer closure, source/registry/code/policy pins, authorization actor/time/scope, reason, validation checks, transition outcome/read-back/consumer acknowledgements và supersession/restatement lineage. Không secrets/source payload dumps.

**Consumer visibility đề xuất:** discovery/refresh catalog exposes scoped certification lifecycle revision và source as-of; new refresh cannot quietly pick revoked/held member; pinned historical consumers phải nhận compatibility/validity notice theo approved channel/runbook. Không claim đã thu hồi exported reports/cache artifacts nếu không có delivery/refresh evidence. Notification/revocation propagation channel/owner delegation là D3 review, task này không gửi thông báo hoặc triển khai service.

**Minimum Owner decision:** accept/adjust authority + hold/revoke/reinstate/rollback/consumer contract. Chưa approve D3 thì no automatic lifecycle actions; known-bad scope không được tiếp tục khẳng định valid Certified để né blocker, giữ hold/review/evidence và escalate Owner. Không xóa historical evidence.

### D4 — Rebuild/restatement closure — confirmed approved baseline

CP-04 đã chọn **A full rebuild mỗi affected mart** từ complete compatible dependencies, không unrelated marts. Không còn Pending “chọn A baseline”; B/C optimization chỉ future review/equivalence proof.

| Closure item | Confirmed requirement / impact |
| --- | --- |
| Old/new groups và empty groups | Include previous/replacement date/customer-role/product/type keys, rebuild complete mart population; stale empty group removed, không changed-rows-only aggregate |
| Fact identities | Same InvoiceLineID/OrderLineID/StockItemTransactionID/source-item state grain; header-only union children và source-measure corrections preserve/update exact values |
| Dimension re-resolution | Affected NK/incarnation/roles/exact intervals/days, approved registry/supersession; boundary continuity vs split/merge, U→R no additive measures |
| Historical correction | B7 before/after, source/registry pins/authority và impacted periods; no blanket unapproved history rewriting |
| Customer repeat | Complete OH buyer-month population; date/buyer moves both sides; quarter/arbitrary period distincts/repeat recalc từ whole eligible headers, no averaging monthly flags |
| Source generation compatibility | Same request can't mix restored/new generation with old evidence; hold/new reviewed request when incompatibility not bridged |
| Type1/publication/governance dependencies | D1 selected scope/D2 bundle/D3 lifecycle choice chưa approve; cannot silently bypass để declare full design DONE |
| Reconciliation | Four fact per-key/grain conservation, six full mart oracle rebuilds, roles/distinct/ratios/NULL/signs/old-new population, AP gates trước promote |

**11-source/16-model Stage 2 review:** inventory/source matrix sections2–5 đã rà đủ 9 current+2 H; 2 intermediates,4 dimensions,4 facts,6 marts đúng existing grains. CustomerTransactions vẫn reconciliation-only, Buyer/Bill-to distinct, FM signs preserved, FC state≠daily balance, H multiplicity/B9/registry giữ. Không phát hiện architectural conflict đòi đổi accepted DW-01/02/03A/03B; conditional final acceptance vẫn **PARTIAL** do D1–D3 là explicit Owner decisions chưa có approval.

## 11. Current residual risks / implementation gates

| Risk / open detail | Impact | Proposed disposition / owner gate |
| --- | --- | --- |
| Old/new impact envelope/closure chưa physical | Stale group/partial rekey | CP-01 đã Approved; D2 approved unit; runtime lineage/shared dependency/consumer proof before use |
| Type1 admitted attrs/selected-version mode | Unintended historical regrouping | D1 explicit/frozen four-anchor set approved; B7 per-request attrs/action review, no implicit fallback |
| Confirmed removal/retraction/incarnation evidence | False entity deletion/old facts loss | CP-03/B8 policy/evidence pending, candidate retained |
| Partial rebuild optimization/oracle | Wrong ratios/distinct/empty groups | CP-04 A baseline Approved; B/C future optimize only after equality proof |
| Certification dependency unit/consumer pins | Mixed “Certified” outputs | CP-05 Approved logical guards; D2 subject/view unit Approved, exact manifests/enforcement/schema/runtime tests pending |
| Previously Certified result proven invalid | Old invalid output still represented Certified | D3 governance Approved; per-incident Owner authorization, existing validated certified target or hold, actual notify/block evidence |
| Concurrent promotions/unknown commit | Duplicate apply/regression | CP-06 request/content/predecessor/durable proof; physical concurrency still gate |
| Source/registry generation loss | Unsupported SK equivalence/bridge | B2/B6/RG06/12, hold/manual compatible recovery |
| External reference/calendar contracts | Wrong types/descriptors/date attribution | No auto reference ingestion/classification; Owner approval before affected model publication |
| Numeric thresholds/retention/scheduling | False pass, premature purge | Preserve B5/G/RG pending values; no numeric defaults |

CP-01–CP-06 **APPROVED — Logical Policy** tại [register](wwi-dw-03c-decision-register.md). D1/D2 nay Logical Approved, D3 Governance Approved; Stage2 Pending section10 giữ history. Mandatory design assessment/QA ở [assessment](wwi-dw-03c-assessment.md) quyết định conditional DONE — Design; physical/runtime/action evidence vẫn deferred. DW-04 TODO, WWI-04/Phase1 IN_PROGRESS; không implementation hoặc task tiếp.

## 12. Stage 3 final integration / exact approval scope

Authority: Project Owner task “DW-03C Stage 3 — Owner D1–D3 Approvals & Final Design Acceptance”,2026-11-16. **D1/D2 APPROVED — Logical Policy; D3 APPROVED — Governance Policy; D4 confirmed**. CP-01–06 giữ Approved — Logical Policy.

### D2 initial publication unit — binding current rule

Dependency-complete **subject/view bundle** là initial analytical publication unit, contains/references complete compatible transitive closure. Explicit accepted input publication pins, complete dependency/build/model/registry/version refs, fact-dim-mart compatibility, reconciliation/certification, durable predecessor/promotion evidence và atomic consumer-visible transition đều required. Không force platform-wide rebuild cho isolated subject change; unrelated mart không auto rebuild.

Cross-subject consumers require **joint consumer manifest** pinning verified compatible subject publications. Independent latest publications không đủ. Thiếu valid joint proof → **hold cross-subject certification/publication**; một subject chỉ independently publish khi shared dependency/downstream compatibility requirements của nó đạt, không skip required common dimension/registry/reference checks. Sales-first boundaries giữ nguyên, không phải chờ unrelated Customer/Inventory analytics.

Logical identity/reference/promotion obligations đã chốt; manifest tables, pointer/locking/fencing/physical transaction/consumer enforcement chưa implemented hoặc runtime Approved. No invented algorithm hoặc distributed transaction guarantee.

### D3 governance lifecycle — approved roles and sequence

| Role | Approved responsibility | Boundary |
| --- | --- | --- |
| Data Quality / Validation | Detect problems, collect evidence, recommend hold/revocation | Không tự được delegate revoke/reinstate/rollback authorization hoặc execute ngoài approved operator role |
| Project Owner | Authorize revoke, reinstate hoặc rollback decisions/affected scope | Governance approval hiện tại không tự authorize từng incident/target/action |
| Operator | Execute authorized transitions và record durable audit/outcome | Physical RBAC/fencing/transaction/recovery proof vẫn required trước runtime |

Khi previously Certified publication incorrect: (1) record incident+publication identity; (2) determine affected KPI/view/consumer closure; (3) apply appropriate hold/invalidation policy; (4) preserve original immutable evidence/lineage; (5) Owner authorization cho controlled revoke/reinstate/rollback; (6) notify hoặc block affected consumer pins theo approved logical policy; (7) record executed transition và durable outcome/read-back. Đây là required contract, **không actions đã thực thi**.

Rollback chỉ tới **existing compatible validated appropriately certified target**, không arbitrary previous version. Verify source generation/as-of, registry/episode/SK/supersession, model/dependency/policy/certification/consumer compatibility, explicit approval/predecessor/content trước transition. Không valid replacement → **hold affected publication**, không expose uncertified data. Reinstate/corrected supersession theo complete evidence/gates/Owner authority, no silent destructive overwrite/delete historical publication/build/audit. Old exported/cache outputs không được claim recalled khi thiếu actual delivery/block proof.

### D4 / source-model / recovery consistency check

Full rebuild mỗi affected mart initial baseline, preserve old/new/empty groups/full compatible population/header-only changes/SCD2 re-resolution/distinct-ratios/generation guards. Partition/group optimization chỉ future correctness-equivalence evidence; không introduce MVP optimization.

Reviewed all **11 source populations,16 target models,4 facts,6 marts**, CP-R01–12 và CP-T01–30: approved grains/KPI/roles/NULL/signs/CustomerTransactions reconciliation-only/H multiplicity/B9/registry/lookup semantics không đổi. CP-T30 verifies joint manifest and D3 hold/Owner/Operator/audit/valid-certified rollback/no-replacement behavior in future authorized tests; all tests **NOT RUN**.

No D1 conflict với DW-02 accepted decisions found; no unresolved mandatory architectural/governance choice sau current approvals. Runtime blockers still apply: all G01–08/RG01–12/CG01–10/B5, per-action approvals, actual source consistency/fidelity/build/manifest/RBAC/recovery tests before relevant normal publication. Conditional design acceptance result ở Final Assessment; approvals alone không runtime DONE và không tự bắt đầu DW-04.
