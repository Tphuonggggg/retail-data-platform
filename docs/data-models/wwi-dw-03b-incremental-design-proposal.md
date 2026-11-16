# WWI DW-03B — Incremental Load Logical Design Specification

**Stage 2, 2026-11-16. DW-03B DONE — Design. INC-01–INC-06 APPROVED — Logical Policy** theo Owner task “DW-03B Stage 2 — Owner Logical Approval & Design Finalization”, conditional acceptance sau mandatory criteria/QA tại [Assessment](wwi-dw-03b-assessment.md). Production ingestion **Not implemented yet**; IT01–IT21 **NOT RUN**. Không thay DW-01/DW-02/A01–A06/B1–B9; physical algorithms/parameters còn gates.

## 1. Phạm vi, evidence và giới hạn bảo đảm

Kiến trúc giữ nguyên: SQL Server WWI read-only → Python ingestion → PostgreSQL Raw → dbt Staging → Core DW → Analytics Marts. Airflow chỉ điều phối khi được triển khai. Chín current tables và hai associated physical history tables thuộc cùng một nguồn WWI; không là 11 hệ thống độc lập. Sales end-to-end trước, Customer/Inventory mở rộng sau.

[Work plan](wwi-dw-03b-work-plan.md) giữ dependencies/evidence index E01–E10; [Decision Register](wwi-dw-03b-decision-register.md) giữ approval; [Assessment](wwi-dw-03b-assessment.md) giữ QA/readiness. Tái sử dụng [Source Contracts](wwi-source-contracts.md), [Dictionary](wwi-metadata-dictionary.md), [Extraction Matrix](wwi-extraction-requirements-matrix.md), [Validation Matrix](../requirements/wwi-source-validation-matrix.md), không thay bằng contracts mới.

**Verified — historical:** số dòng/duplicate timestamps dưới đây lấy khảo sát 2026-11-07; temporal duplicate-start được tái kiểm 2026-11-14; source flags/B9 proof từ DW-03A 2026-11-15. **Unverified:** nguồn hiện đang có writer hay không, mọi write path có tăng timestamp hay không, transaction commit delay, retention/cleanup policy thực tế và nguồn có thay đổi kể từ baseline. Stage 1 và Stage 2 không kết nối DB, không chạy lại profiling, không sửa B9 sandbox. Owner approval chốt policy, không làm mới các source observations lịch sử.

### Approved assurance và verified consistent source boundary

Owner phê duyệt **Current-State Convergence**, không complete intermediate event history. Năm lớp bảo đảm không đồng nhất: **candidate detection** tìm rows có thể đổi; **current-state convergence** chứng minh state tại boundary được chọn; **complete event/change history** cần evidence của mọi change, không được cam kết; **temporal source history** là physical evidence còn giữ bởi nguồn; **analytical SCD2 history** do DW-02 evidence/registry/validity policy quyết định, không là bản sao H.

Định nghĩa logical boundary **C** gồm source instance/database + restore/generation lineage, declared source scope/populations, approved contract/projection/canonicalization revisions, capture identity, observation interval và **consistency proof reference**. Trạng thái **S_C** là toàn source population đúng scope trong verified no-writes window, hoặc trạng thái của separately approved verified consistent source copy. Phạm vi interval bao trùm chọn bounds, reads/current-H/counts/value checks và source reconciliation cần thiết. Local capture ID không là native snapshot token; read-only login hoặc timestamp cũ không chứng minh static source.

**R_C** là current-state projection từ compatible pinned full base + accepted delta/complete-snapshot memberships, theo cùng generation/scope/versions, không phải toàn append-only Raw rows. Current-state convergence chỉ được claim khi full key coverage/counts/per-key canonical values của R_C khớp S_C và temporal populations được đối soát multiset riêng. Không trộn source state từ nhiều thời điểm để kiểm một R_C.

Reference correctness path ở WWI scale: complete consistent full-table comparison trước publication mang claim converged, dùng cùng C để tìm cả updates ngoài window; reconcile/apply candidate differences rồi verify state đến eligibility. W-only PASS hoặc matching window totals không đủ để claim full-state convergence. Nếu chưa có proof tương đương cho tối ưu, phải dùng full comparison hoặc hold claim/publication; không gọi incomplete state là successful normal publication. Physical execution/verification algorithm vẫn RG03/G08, không triển khai ở đây.

**Chi phí:** full-table comparison vẫn đọc toàn eligible source population dù chỉ changed rows được ghi thêm vào Raw. Đây là state-based incremental application với full-read correctness baseline, không cam kết tránh mọi full scan hoặc benchmark tiết kiệm IO. Periodic full reconciliation tiếp tục theo L01/INC-03, cadence chờ measurement/approval; không mặc định một lịch.

Mức bảo đảm phải ghi riêng:

- Transport đúng và replay không nhân bản: có thể kiểm với sealed capture, không chứng minh completeness của change detection.
- State convergence: full reconciliation trên context nhất quán có thể tìm khác biệt trạng thái còn tồn tại, nếu có full payload/key coverage.
- Complete event history: không thể cam kết cho bảng ordinary bằng watermark hoặc periodic snapshot. INSERT rồi DELETE, hoặc A→B→A giữa hai observations có thể không còn dấu vết. Temporal chỉ giữ được evidence còn tồn tại trong history, không tự là complete event log.
- Không đặt SLA mất dữ liệu bằng 0 hoặc maximum detection lag khi chưa có source write/retention/consistency contract. Nếu Owner cần mọi intermediate event, đây là capability gap cần proposal riêng; không tự bật CDC/Change Tracking.

### Phân biệt các loại identity và thời gian

| Khái niệm | Nghĩa / giới hạn |
| --- | --- |
| Source record | Một current row trên source PK; không phải mọi lần UPDATE của row đó |
| Physical temporal occurrence | Một physical row current hoặc H, full payload/period/origin; H không có PK như current |
| Current-state observation | Trạng thái đọc được trong capture/context/window có bằng chứng; khác source event time |
| Logical change candidate | So sánh observations có thể suy INSERT/UPDATE/absence; phải ghi basis, không tự có transaction/event identity |
| Analytical SCD2 episode | Chỉ hình thành theo DW-02 tracked vector/validity/registry; Raw không cấp episode/SK |
| Checkpoint | Bằng chứng phần công việc đã công bố theo contract revision/source generation; không chỉ một timestamp |
| Source system-time / observed_at / published_at | Ba ý nghĩa khác nhau; không gán business-effective time hoặc dùng publication time làm source update |

## 2. INC-01 — Per-source Incremental Extraction Strategy Matrix

LEW = LastEditedWhen, datetime2(7), non-NULL theo metadata và có 0 NULL trong baseline. Tất cả bảy bảng có LEW đều là ordinary/current-state tables; Customers/StockItems không có LEW. Không mặc định default timestamp hoặc PK sequence chứng minh mọi UPDATE đều được theo dõi. Các số là **reference observations**, không fixed acceptance counts.

Approved source-specific detection direction; notation của logical contract: **W** = LEW candidate window + replay nếu được chứng minh, luôn kèm periodic full key/value reconciliation; **S** = full consistent current snapshot comparison; **T** = direct current + physical H capture và multiset comparison, trước mắt full nhỏ; period filtering chỉ tối ưu bổ sung sau proof. INC-01/04/05 đã Approved — Logical Policy ở Stage 2; exact physical algorithms/period-filter optimization và scheduling chưa được chọn.

| Source / loại | PK hoặc NK / baseline | Change fields và độ tin cậy | INSERT / UPDATE candidates | DELETE candidates | Current/H và full reconciliation | Khuyến nghị / missing-data risk |
| --- | --- | --- | --- | --- | --- | --- |
| Sales.Orders / ordinary | OrderID / 73,595 | LEW: 2,129 distinct; behavior trên mọi write path Unverified | W + PK new/row-value diff; không chỉ PK cao | Complete S key absence → candidate, không từ delta | Full header PK+payload; giữ 3,085 order chưa invoice ở baseline | W có điều kiện, S fallback; bỏ header-only change làm sai order/date/buyer/repeat |
| Sales.OrderLines / ordinary | OrderLineID / 231,412 | LEW: 1,970 distinct | W độc lập với Orders; full row diff khi recon | Complete key absence, kiểm parent/filter/race | Full PK+OrderID/StockItemID/quantity/price/fields | W có điều kiện; không suy line change từ header, không match InvoiceLine 1:1 |
| Sales.Invoices / ordinary | InvoiceID / 70,510 | LEW: 1,069 distinct | W + header value diff; date/buyer/bill-to changes độc lập lines | Complete key absence → candidate | Full PK+roles/date/nullable OrderID và fields | W có điều kiện; line LEW không bắt header-only change |
| Sales.InvoiceLines / ordinary | InvoiceLineID / 228,265 | LEW: 1,069 distinct | W + per-PK row/amount diff | Complete key absence → candidate | Full PK/parent/product/amount/tax/qty; grouped invoice diagnostics | W có điều kiện; equal LEW có thể che sửa amount trên key cũ |
| Sales.CustomerTransactions / ordinary | CustomerTransactionID / 97,147 | LEW: 1,069 distinct | W + per-PK balances/finalization/value diff | Complete key absence → candidate | Full PK/type/amount/nullable InvoiceID; reconcile theo type riêng | W có điều kiện; không bỏ payment InvoiceID NULL hoặc phân bổ payment tự động |
| Sales.Customers / temporal current | CustomerID / 663 | ValidFrom/ValidTo; không LEW; current sentinel không là change cursor | T current diff + H evidence; observation không tự là business event | Complete current absence + H/context/identity investigation | Cùng context với Customers_Archive; current PK riêng | Full T phù hợp baseline nhỏ; system-time/late commit không đủ globally ordered feed |
| Sales.Customers_Archive / physical H | Không PK; NK CustomerID / 51 rows, 46 IDs | ValidFrom/ValidTo exact; same-start duplicate, 1 zero-duration | New/changed multiset occurrences, không gán INSERT/UPDATE log operation nếu thiếu proof | H absence là retention/correction candidate, không tự là customer delete | Direct H full payload+period+origin+multiplicity; current+H 714 so SYSTEM_TIME ALL 713 | Full T; không DISTINCT, start-key/hash/ordinal identity; corrections có thể làm period filter bỏ sót |
| Warehouse.StockItems / temporal current | StockItemID / 227 | ValidFrom/ValidTo; không LEW | T current diff, full-field changes giữ cả Tags/CustomFields/Photo | Current absence với identity/consistency evidence | Cùng context StockItems_Archive; current-state Product/holdings pin tương thích | Full T; Raw changes không tự trigger packaging SCD2 |
| Warehouse.StockItems_Archive / physical H | Không PK; NK StockItemID / 444 rows | Periods exact; 671 current+H rows, boundaries trùng | Full multiset delta/correction evidence, không scalar watermark duy nhất | H disappearance điều tra cleanup/retention/generation | Direct H capture full payload/period/origin; giữ multiplicity | Full T; không giả history append-only vĩnh viễn hoặc đủ mọi transaction |
| Warehouse.StockItemHoldings / current state | StockItemID PK/FK / 227 | LEW chỉ 2 distinct, 225 rows vượt distinct | S full payload diff cho insert/update, LEW diagnostic | Complete S key absence → candidate; partial snapshot không inference | Full state count/keys/value/qty/NULL cùng context Product phù hợp | S mỗi accepted observation; không dựng daily balance hoặc cộng state cũ+mới |
| Warehouse.StockItemTransactions / ordinary | StockItemTransactionID / 236,667 | LEW: 1,973 distinct | W + signed decimal qty/type/date/reference diff | Complete key absence → candidate | Full PK+qty/type/optional links; grouped issue diagnostics | W có điều kiện; business TransactionOccurredWhen không là update watermark |

W là approved conditional candidate direction, chỉ thực thi sau technical algorithm/source-context/write-behavior tests và appropriate implementation authorization. Chưa đủ proof thì dùng full-state comparison để chứng minh R_C=S_C hoặc hold normal converged publication; không claim W complete. Full scans phải đo chi phí trước cadence, kể cả khi chỉ ghi changed rows.


### Final per-source contract — publication, tests và recovery

Ma trận ở trên giữ key/detection/candidate/update/delete/temporal fields. Bảng dưới hoàn thiện obligations cho **từng** source, không thay source dictionary hoặc chọn SQL/index. **P0** áp dụng từng row: approved consistency boundary C + đầy đủ declared membership + exact canonical fidelity + same-state key/value hoặc H multiset reconciliation + accepted attempt/manifests + atomic publication/pins/predecessor validation. P0 thiếu proof → hold normal publication. Bảng nêu thêm checks riêng; shared physical/runtime dependencies xem RG01–RG12 trong work plan.

| Source contract | Candidate logic / key-occurrence requirement | Required snapshot/reconciliation / P0 bổ sung | UPDATE/absence limits và temporal evidence | Implementation tests (NOT RUN) | Recovery dependencies |
| --- | --- | --- | --- | --- | --- |
| Sales.Orders | W inclusive + stable LEW/OrderID cursor; full comparison bắt key cũ | Header PK/full payload mọi Orders, không inner-join invoice; date/buyer old/new refs | Same/backdated LEW có thể miss; full absence chỉ candidate; không temporal evidence nguồn | IT02–07/12/15–19/21 trên Orders | RG01/03/04/08/09; giữ header old/new grouping input cho DW-03C |
| Sales.OrderLines | W riêng trên LEW/OrderLineID; full row candidate diff | PK+OrderID/StockItemID và mọi fields, compatible parent pins/quantity/price | Không suy updates từ header; no OrderLine–InvoiceLine identity; absence candidate | IT02–07/12/15–18/20/21 trên OrderLines | RG03/05/08/09; affected parent/product refs, sealed content |
| Sales.Invoices | W riêng trên LEW/InvoiceID; header changes độc lập lines | All header PK/date/buyer/bill-to/OrderID/IsCreditNote; no-line/optional refs không bị drop | Same-time old-key correction phải recon; absence candidate; không suy delivery recognition | IT02–07/12/15–19/21 trên Invoices | RG03/08/09; old/new InvoiceDate/roles/header-child keys |
| Sales.InvoiceLines | W LEW/InvoiceLineID + exact per-PK diff | Parent/Product pins, quantities/ExtendedPrice/TaxAmount/LineProfit/full payload | Backdated amount change ngoài window cần full recon; absence candidate | IT02–07/12/15–18/20/21 trên InvoiceLines | RG03/05/08/09; old/new invoice/product membership |
| Sales.CustomerTransactions | W LEW/CustomerTransactionID + exact row diff | Full PK/type/finalization/amount/balance, nullable InvoiceID; group type riêng | Equal-time updates có thể miss; absence candidate; không infer payment allocation | IT02–07/12/15–18/20/21 trên CustomerTransactions | RG03/05/08/09; reference type/optional parent contract |
| Sales.Customers | T direct full current CustomerID+exact periods/source fields | Current PK/value state và same-C Customers_Archive multiset; buyer/bill-to refs | No LEW; system-time không business time; current absence candidate, H không thay confirmation | IT01/08–10/12–13/15–18/20–21 trên Customers | RG01/05/06/07/08; B2/B6/B8, forward/source evidence bridge |
| Sales.Customers_Archive | T direct full H; NK CustomerID không PK; full occurrence multiplicity | Same-C H count/full canonical multiset; zero-duration/same-start giữ nguyên, origin H | Period không global order; indistinguishable corrections ambiguous; H absence retention candidate | IT01/06/08–10/15–18/20–21 trên Customers_Archive | RG05/06/08/12; retained multiset/original evidence, no ordinal durable key |
| Warehouse.StockItems | T direct current StockItemID+exact periods/full fields | Current state + same-C H, blob/computed fidelity; compatible Product input | No LEW; Tags changes không analytical packaging episode; absence candidate | IT01/08–10/12–13/15–18/20–21 trên StockItems | RG05/06/07/08/09; B9 + registry/forward evidence preservation |
| Warehouse.StockItems_Archive | T full H, StockItemID chỉ NK, không fake unique key | Full canonical H multiset/period/origin/multiplicity cùng current C | Period filter conditional; removed H không Raw purge/entity delete | IT01/06/08–10/15–18/20–21 trên StockItems_Archive | RG05/06/08/12; replay same sealed occurrences, new context new capture |
| Warehouse.StockItemHoldings | S full current snapshot mỗi accepted observation, PK StockItemID | Full key/payload/qty/cost comparison, compatible Product current-state pin | LEW diagnostic; complete absence chỉ candidate, partial không evidence; không daily balance | IT01/11–13/15–18/20–21 trên Holdings | RG01/05/07/08/09; observed_at/published_at riêng, no mixed states |
| Warehouse.StockItemTransactions | W LEW/StockItemTransactionID + full row diff | Signed decimal qty/type/date/optional refs; grouped invoice-item diagnostic đúng population | Old-key/update/delete không từ max PK/business time; absence candidate | IT02–07/12/15–18/20/21 trên StockItemTransactions | RG03/05/08/09; reference contracts, old/new groups; không rebuild balance |

Current observations và entity lifetime là hai axes: complete snapshot membership ghi đúng **present/absent at C** để R_C so được với S_C; absent key không còn thuộc current observed population của snapshot đó. Đây là non-destructive observation membership, giữ old Raw/audit và candidate absence evidence; **không** confirmed business deletion, dimension retirement, cascade fact retraction hoặc historical purge. Các entity actions vẫn RG07/B8. Nếu representation của absence/membership chưa được implement/verify đầy đủ thì hold affected current-state publication; không giữ stale present row rồi claim convergence.

### Sales-first publication và mở rộng có kiểm soát

Sales publication scope lấy DW-03A A06 làm ràng buộc: declared dependency-complete scope (bảy current Sales/master inputs + hai H streams là proposal của DW-03A, exact scope vẫn cần duyệt); không chờ triển khai Inventory analytics. Hai Inventory current streams vẫn được thiết kế ở đây, không tự nạp. Application.TransactionTypes, PackageTypes và external references giữ contract-extension/controlled mapping gate hiện hữu; không ngầm thêm incremental source contract.

## 3. INC-02 — Watermark, boundaries và tie-breakers

| Candidate | Có ích cho | Thiếu bảo đảm / trade-off | Đánh giá đề xuất |
| --- | --- | --- | --- |
| Timestamp-only LEW > H | Ít rows, dễ triển khai | Bỏ bằng H, late commit, backdated/unchanged LEW và deletes | Không dùng như correctness guarantee |
| Composite (LEW, PK) | Deterministic keyset trong **cùng source context** trên unique current PK | Key cũ với LEW không tăng có thể nằm trước cursor; transaction commit muộn cũng vậy | Chỉ pagination cursor, không complete CDC |
| Bounded lookback + replay | Đọc lại equal-time/late updates trong window | Không bắt giá trị cũ hơn lower bound; tăng read/load; không bắt transient events/delete | Candidate đi cùng full reconciliation; chưa có numeric interval |
| Temporal period filter | Giảm H/current scan khi đặc tính đã đo | Transaction-begin time, zero-duration, retention/corrections và duplicate boundaries; không source occurrence identity | Tối ưu có điều kiện, không sole feed |
| Full snapshot row comparison | Tìm trạng thái khác trên mọi key/field trong snapshot | Full read cost; bỏ intermediate revisions; cần coherent context | Fallback state assurance; ưu tiên holdings/master nhỏ |
| Full reconciliation | Kiểm key/value/multiset toàn population tại thời điểm kiểm | Không tái tạo event đã mất; nguồn thay đổi giữa đọc không proof exactness | Bắt buộc theo L01; cadence còn chờ evidence/approval |

### Conditional watermark logical contract — exact algorithm chưa chọn

Ký hiệu H = **published** high-watermark candidate trước đó của đúng source object/generation/contract; U = upper boundary candidate được xác lập trong same approved source context; L = lower replay bound theo policy được duyệt. Không lấy wall clock, max PK hoặc orchestrator end time làm default U.

Một phương án U để kiểm chứng là MAX(LEW) của full eligible source population trong cùng context, ghi cả NULL/empty-population status; phương án khác là source-time cutoff có proof về write/commit horizon. Chưa chọn một trong hai. MAX(LEW) chỉ là upper value quan sát, không committed frontier: transaction commit muộn/backdated vẫn có thể xuất hiện với LEW ≤ U. MAX của riêng page hoặc rows đã load không được thay source-bound evidence; empty population không tạo sentinel checkpoint hoặc tự advance.

- Inclusive-boundary policy đã Approved; một expression candidate cần technical validation là **closed window L ≤ LEW ≤ U**, bao gồm equality ở hai biên; lần kế tiếp replay boundary, không cộng một tick. Window overlap xử lý bằng evidence/idempotency, không loại rows tùy ý. Khi chưa duyệt lookback, L chưa có giá trị vận hành; không âm thầm chọn 0 ngày.
- Trong window cố định, stable ordering (LEW ASC, PK ASC) và page tiếp dùng tuple **strictly greater** last tuple; upper U giữ nguyên. Cursor chỉ resume cùng live defensible context. Một extraction request mới từ context mới có capture_id mới.
- Chỉ đổi H→U khi dependency scope đã sealed, reconciled, durable publication identity được xác nhận và predecessor/version precondition đạt. H không phải max tuple của page đã đọc. Có thể publication mới mà H không tăng, ví dụ equal-time correction.
- U < H, đổi schema/type/basis, nguồn restore/replace, hoặc conflicting generation → hold và rebaseline proposal; không silently giảm H. Empty result không tự chứng minh nguồn không đổi; nếu không có defensible U/context, giữ checkpoint cũ/unknown.
- LEW NULL, out-of-range hoặc invalid timestamp: ghi exception/missing candidate coverage, không COALESCE về min và mark complete; chọn full comparison hoặc hold theo policy Owner. Giữ exact B9, không convert authoritative cursor sang datetime microsecond.
- Source read có thể thay đổi khi paging: fixed U không tạo snapshot. G01/A02 áp dụng cả incremental: no-writer proof hoặc separately approved consistent copy; thiếu proof hold normal publication. Không tự bật SNAPSHOT/RCSI hoặc tạo locking transaction dài.
- Request window và query/canonicalization version phải nằm trong immutable manifest để replay cùng predicate/basis. Source count/window checks cùng context; count ngoài context chỉ diagnostic.

**Synthetic counterexample:** đã xử lý LEW=t, PK=100. Sau đó key 10 đổi payload nhưng vẫn LEW=t; tuple > (t,100) bỏ key 10. Inclusive replay t có thể bắt trạng thái còn tồn tại đó; nếu LEW bị sửa về t cũ hơn L, replay vẫn bỏ. INSERT PK cao không bắt UPDATE/DELETE PK cũ. Đây là ví dụ giả định, không khẳng định WWI đã có các writes này.

## 4. INC-03 — Lookback, late updates, replay và backfill

| Tình huống | Proposed handling / bằng chứng | Giới hạn |
| --- | --- | --- |
| Late commit hoặc backdated correction | Ghi observation window, source timestamp, cùng key old/new bytes; recon tìm mismatch ngoài window | Polling lag không đo đủ commit lag nếu không có source ground truth |
| Equal timestamp trên nhiều keys | Inclusive replay window + current-key pagination, giữ exact source values | Cursor không duy nhất trên H, không nâng H chỉ vì lấy xong page |
| Cùng key, cùng LEW, payload khác | Giữ hai observations/lineage, investigate precedence/source-context proof | Không dùng timestamp+PK làm idempotency ID của mọi row revision |
| Overlap windows/repeated execution | Sealed capture replay cùng logical content/accepted attempt, không apply current state hai lần | Hai captures mới có thể cùng payload; giữ cả evidence, serving không append facts mù |
| Out-of-order observations | Compare pinned base/predecessor/generation; stale capture không ghi đè newer state | observed_at lớn không tự là source commit order; cần conflict/rebase handling |
| Replay sealed capture | Giữ capture/batch/content refs, versions; run/attempt có thể mới | Không requery source rồi gọi là same capture |
| Historical backfill/new source read | Capture mới, scope/time/basis/base pin riêng; reconcile overlap trước publication | Không lùi main checkpoint/pointer, không splice generations không tương thích |
| Correction vào dữ liệu đã publish | Immutable correction evidence + source keys/old/new dependency envelope cho DW-03C | Không tự rekey/restate/cascade hoặc đổi approved BRD/KPI |

**Đo lookback trước chọn số:** trong writable sandbox được duyệt, ghi transaction begin/commit và timestamp behavior cho mọi test write path; đo observation lag, timestamp skew/backdating, long transaction và outage/recovery duration. Trên read-only nguồn, dùng Q11/repeated coherent snapshots và mismatch ngoài window để quan sát state changes; không có ground truth commit thì không tuyên bố maximum lateness. Đề xuất window từ measured envelope + reviewed margin/cost, kèm điều kiện hết hiệu lực; không lấy max lịch sử 2016 làm delay sample.

**Full reconciliation bắt buộc** theo L01 và khi timestamp guarantee chưa đủ, source generation/schema/policy thay đổi, history cleanup hoặc cutoff gap, prolonged outage vượt evidence horizon, unexplained drift/mismatch, failed/partial capture, checkpoint lineage thiếu, hoặc trước rebuild/restate compatibility claim. Lịch định kỳ và trigger thresholds phải Owner duyệt; một lần recon sạch không bảo đảm mọi writes tương lai.

## 5. INC-04 — Temporal incremental và hybrid compatibility

Khuyến nghị full capture hai cặp current/H ở baseline nhỏ, mỗi stream giữ origin và cùng consistency context. Period-based candidate (current ValidFrom, H ValidTo hoặc interval overlap) chỉ là optimization bổ sung được thử riêng. Không lọc H chỉ theo ValidFrom: version có start cũ có thể mới được chuyển vào history.

Engine semantics: periods dùng transaction-begin system time; transaction bắt đầu sớm/commit muộn có thể làm một occurrence mới visible mang period cũ. Nhiều changes trong một transaction có thể tạo zero-duration rows. Direct physical H reads giữ chúng, không dùng FOR SYSTEM_TIME ALL thay raw capture. Đây là engine behavior, không kết quả thử write trên WWI. Xem [Microsoft temporal overview](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal/overview?view=sql-server-ver17).

INC-04 approved preservation obligations; concrete adapters/optimizations vẫn technical gates:

1. Reuse nguyên **F2 đã verified**, không viết formatter mới: [DW-03A evidence section 5.1](wwi-dw-03a-evidence-approval-readiness.md) và [B9 code](../../tests/integration/b9_precision/poc.py). Source F2 → Python str/None → bound psycopg → authoritative TEXT; non-NULL 27 characters/seven fractional digits, COLLATE "C" cho exact ordering/comparison. NULL/min/max/sentinel/100 ns và source basis giữ nguyên. Không chọn secondary representation/index.
2. H không có source PK; direct multiset comparison phải giữ full payload/period/origin và occurrence count. Current→H có thể đổi ValidTo của source evidence; không suy hai changes nghiệp vụ chỉ vì chuyển origin. Locator trong capture khác durable occurrence identity.
3. Repeated same-start hoặc exact-duplicate rows không dedupe theo NK+period/hash. So multiset cho biết thêm/bớt occurrence count nhưng không luôn xác định row nào đã bị sửa. Khi lineage không phân biệt được, giữ ambiguity, không gán arbitrary ROW_NUMBER/physical address thành source identity.
4. Newly visible H, corrected H và removal phải được tìm bằng complete current/H comparison tại reconciliation. System-versioning đang bật thường không cho direct H DML; correction/restore/maintenance capability không được mặc định có hoặc chạy. Kiểm versioning/history object/schema/source generation continuity trước diễn giải diff. [Microsoft limitations](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal/considerations-limitations?view=sql-server-ver17) là cơ sở engine.
5. History retention/cleanup thực tế **Unverified**. Metadata/read-only inspection và DBA evidence cần có trước optimization. Cleanup có thể làm source H không còn occurrence; không xóa retained Raw/forward history theo source absence. Rebaseline sau mất retention horizon không phục hồi được evidence đã biến mất trước capture. [Microsoft retention](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal/manage-retention?view=sql-server-ver17) mô tả capability, không chứng minh WWI đang bật cleanup.
6. Giữ source generation/restore lineage, contract/projection/serialization/policy và exact context. Full và delta từ generations khác không tự merge. Thay DB/copy có thể giữ PK/period giống; equality không chứng minh cùng incarnation.
7. Hybrid D04/B6: giữ source-backed và observation-backed evidence, reconcile bridge ở compatible generation; full reload không bỏ forward observations/registry/supersession. Raw giữ occurrences, DW-02 mới xác định analytical episodes theo admitted tracking vector. Unreconciled basis → U hoặc proven conflict → I theo policy, không current/earliest fallback.
8. Date-only lookup vẫn cần full-day one-episode proof B3; exact transport PASS không giải quyết business-effective validity. Không tự cấp SK, regenerate SK hoặc collapse noncontiguous equal values.

## 6. INC-05 — Snapshot comparison và delete evidence

Ưu tiên full-table snapshot cho StockItemHoldings (227 rows tại baseline); current masters nhỏ đi cùng T. Kích thước lịch sử chỉ là planning input: cần measured scan/adapter/storage cost trước cadence, không xây distributed hashing service.

INC-05 approved snapshot comparison contract:

- Hai snapshots **complete, consistent**, same declared full population/source generation/contract/projection, compatible canonicalization, được pin rõ. So keys hai chiều: new key, retained key, missing key. Compare full row values cho retained key.
- Key-only comparison tìm presence/absence, không bắt quantity/cost/field UPDATE. Row-count equality và tổng quantity cũng không đủ.
- Canonical row serialization phải versioned, có tên/thứ tự/type/precision/length của fields; distinguish NULL/rỗng/text "NULL", delimiters, Unicode/trailing spaces, exact decimal scale/value, exact B9 periods, bytes/geography/computed theo G06. Không binary float, trim/casefold hoặc JSONB-only payload loss.
- Hash chỉ accelerator. Lưu original source-preserving payload; digest equality không chứng minh identity/multiplicity hoặc tuyệt đối no-collision. Với holdings nhỏ, direct exact value comparison là phương án đơn giản hơn; algorithm/hash/digest format chưa chốt.
- Missing key từ delta là **không có observation**, không là delete. Missing key từ complete consistent full snapshot là **delete candidate**, giữ prior evidence. Partial/failed/filter-mismatched snapshot **không được sinh delete candidate**.
- Candidate phải có old/new snapshot refs, key, absence coverage, consistency/projection/permission/source continuity evidence; investigate source filters/RLS/permission changes, parent-child implications, retention và restore. Repeat coherent absence hỗ trợ điều tra nhưng không tự chứng minh business deletion.
- Verified source removal cần defensible source/DBA evidence phù hợp semantics; approved retirement/retraction policy mới cho downstream action. Stage 2 không chốt số lần xác nhận/tombstone encoding/hard-delete policy; không cascade hoặc xóa historical fact/Raw.
- Reappearance: ghi new observation, liên kết prior absence candidate. Theo B8, reactivation vs new incarnation cần evidence; chưa đủ → Ambiguous, không tạo incarnation hoặc reuse SK cho nghĩa khác.
- Holdings publication là current state mới, không cộng snapshots và không daily balance. Product version phải phù hợp cùng published state; observed_at khác published_at.

## 7. INC-06 — Final logical checkpoint và recovery contract

Logical checkpoint contract đã Approved, không là bảng/DDL. Fields tối thiểu để review: source/generation/scope/object, detection-policy/contract/projection/serialization versions, base raw_publication_id, expected predecessor/revision, capture/logical_batch/accepted attempt refs, exact L/U nếu áp dụng, page cursor riêng, sealed-content refs/fingerprint, coverage/consistency/reconciliation evidence, target publication result và audit/reason. Với S/T, checkpoint chủ yếu là accepted snapshot/multiset/publication identity, không ép có scalar timestamp.

### Logical checkpoint state machine

~~~mermaid
stateDiagram-v2
    [*] --> Planned
    Planned --> Extracting
    Extracting --> Sealed: Complete source-context evidence
    Sealed --> Loaded: Exact accepted content
    Loaded --> Reconciling
    Reconciling --> Eligible: P0 and compatible state checks
    Eligible --> CommitOutcomeUnknown: Publication attempted
    CommitOutcomeUnknown --> RawPublished: Durable acceptance proven
    CommitOutcomeUnknown --> Eligible: Durable noncommit proven and predecessor valid
    CommitOutcomeUnknown --> Hold: Outcome unresolved or conflict
    RawPublished --> Acknowledged: Progress binding read back
    Acknowledged --> Acknowledged: Retry returns same accepted result
    Extracting --> Hold
    Sealed --> Hold
    Loaded --> Hold
    Reconciling --> Hold
    Eligible --> Hold
    Hold --> Planned: New context means new capture
~~~

Các milestones/transition guards là logical contract, không physical enums/tables/locking selection. Streaming load có thể overlap extraction; Loaded complete chỉ sau seal. Retry retained sealed content có thể resume đúng stage/new attempt sau durable checks, không requery rồi reuse capture identity. Context mất trước completion → abandoned candidate và capture mới, giữ old evidence. ACK không thể suy từ job exit code hoặc pointer hiện tại một mình.

**ACK contract — phải kiểm đủ trước acknowledged progress:**

| Guard | Bằng chứng bắt buộc | Khi thiếu/conflict |
| --- | --- | --- |
| ACK01 Identity/content | Run/attempt/capture/logical batch/publication refs; accepted attempt, immutable seal, content/projection/policy fingerprints và original lineage tương ứng | Hold; same identity/different content là conflict, không skip |
| ACK02 Source state | Boundary C/source generation/scope/consistency proof; candidate L/U/cursor basis nếu có; coverage cùng source-state population | No normal publish/ACK; full-read counts ngoài C chỉ diagnostic |
| ACK03 Reconciliation | Key coverage/counts/per-key exact values; H multiset/NULL/precision, required dependency completeness, R_C=S_C khi claim converged | Hold failed/incomplete scope, không advance |
| ACK04 Durable publication | Accepted ledger và exact membership+base+revision cùng logical outcome; checkpoint transition bound publication; commit outcome known | Unknown commit → inspect durable evidence, không blind retry |
| ACK05 Predecessor/concurrency | Accepted predecessor/content/expected revision hợp lệ tại commit; replay request same accepted outcome; current pointer có thể newer nhưng không lùi | Stale incompatible candidate hold/rebase; successful old replay ACK same result, không move pointer |
| ACK06 Consumption/access | Downstream dùng compatible pinned publication set, candidates không visible như normal state; Raw progress khác Core/mart consumption | Không certify Core/mart từ Raw ACK hoặc expose partial generation |

Checkpoint effective progress phải được xác định từ durable accepted publication hoặc được atomically bound với nó bằng cơ chế review sau; riêng write metadata sau load không đủ. H→U là candidate progress chỉ được acknowledge sau ACK01–06; empty/equal-time correction có thể có new publication với H không tăng. Không tự chọn table schema, CAS/locks/isolation, checkpoint encoding hoặc cross-system transaction. Physical proof RG08/G08 và DW-03C handoff còn Pending.

Delta publication phải tham chiếu immutable compatible base + ordered accepted delta membership + explicit coverage/evidence; không query mỗi bảng latest. Candidate checkpoints có thể khác theo stream nhưng không advance độc lập làm dependency scope mixed. Replaying old capture không chuyển current pointer ngược. Stale-base candidate cần revalidate/rebase thành request/capture lineage mới phù hợp hoặc hold, không last-writer-wins theo observed_at.

| Failure | Logical response / completion evidence | Checkpoint / visibility |
| --- | --- | --- |
| 1. Extraction interrupted | Giữ chunks/attempt; resume chỉ same live approved context và exact continuation; mất context → abandon, new capture | Không advance/publish partial |
| 2. Partial Raw load | Retained sealed chunks + durable content/manifest read-back; retry exact missing content, reject changed bytes under same identity | Không advance; committed candidates invisible |
| 3. Loaded nhưng reconciliation fail | Hold candidate, ghi diff/reason/expected population; rerun check cùng capture hoặc capture mới nếu source context khác | Previous publication/checkpoint giữ nguyên |
| 4. Reconciliation PASS, publication fail | Candidate eligible chưa là published; inspect durable transaction outcome trước retry, predecessor check | Chưa confirmed commit thì không ACK/advance |
| 5. Publication commit, orchestrator crash | Read ledger+manifest+checkpoint binding và pointer revision; xác nhận same result; nếu newer publication tồn tại không roll back | Effective checkpoint phản ánh accepted commit; ACK phục hồi |
| 6. Retry sau success | Same request/content trả accepted publication; same identity/different content conflict | Không double apply/measures, không pointer regression |
| 7. Source đổi khi extraction | G01 context proof fail/unknown → hold; không dùng matching counts làm no-writer proof | Không nối pages/current-H từ incompatible contexts |
| 8. Correction ảnh hưởng published data | New immutable correction/capture, base pin, old/new keys/group evidence, controlled re-resolution/restatement handoff | Không mutate accepted evidence hoặc tự rekey; DW-03C thiết kế propagation |

Runtime crash/retry/race/ACK-loss/transaction tests **NOT RUN**; G08/DW-03C giữ ownership. Phân biệt hai acknowledgement: extraction progress cursor không có quyền đổi completeness checkpoint; downstream consumption checkpoint riêng, không được advance theo Raw khi Core/mart chưa published.

## 8. Full reconciliation và mismatch disposition

So **accepted Raw state được tái dựng từ pinned base+deltas**, không đếm toàn bộ append-only observations như source current. Không so incremental-window count với toàn source count. History comparison dùng retained capture evidence của đúng source population; history removal không là authorized purge của Raw.

Với H, comparison target là **source-visible H multiset tại C** theo đúng capture membership, không tổng mọi archive observations từng giữ trong Raw. History disappearance/cleanup được ghi riêng trong snapshot/multiset lineage để đối soát observed population; original Raw/forward evidence vẫn retained, không purge hoặc diễn giải thành business delete. Nếu chưa biểu diễn được membership/coverage tương thích thì hold H-completeness claim thay vì dedupe hoặc sửa old evidence để cân count.

| Layer / mapping | Logical checks, same context/population | Mismatch classification / action |
| --- | --- | --- |
| Per-table current S01/I01–03 | Exact COUNT_BIG, PK uniqueness và key-set hai chiều; full value comparison | Missing/extra/current duplicate, incomplete extraction vs source drift; hold complete claim |
| Amount I04/I06 | Per-PK exact InvoiceLine amounts/tax/profit, CT amounts theo type; counts NULL/signs và aggregates | Conversion vs real source correction; không amount netting che mismatch; tolerance chưa duyệt |
| Quantity I08/I09 | Per-PK quantities; signed movement theo type; grouped InvoiceID+StockItemID chỉ khi inputs complete | Unit/type/population mismatch; không direct line/movement fact join |
| Headers/RI I05/I07 | Independent Orders/Invoices populations; optional FK NULL riêng; invoice/transaction diagnostics theo approved type references | Missing dependency/partial generation vs genuine source orphan; không drop headers |
| Temporal S06/I11 | Current/H counts riêng, full exact multiset+multiplicity, zero-duration, overlap/gap/origin/source generation | New occurrence, changed period/payload, moved origin, disappeared H hoặc ambiguous identity; investigate, không dedupe |
| Holdings | Full PK/value/qty snapshot và compatible Product current state | Missing key candidate/incomplete snapshot; không compare toàn movements thành balance |
| Incremental reconstruction | Candidate window coverage vs extracted rows; affected old/new keys và reconstructed state vs full capture | Timestamp blind spot, stale base, incompatible policy/generation, missed changes |
| Runtime/publication I12 | Accepted attempt/content, manifests/ledger/base pins, duplicate attempts, checkpoint binding | Unknown commit, double delivery, partial visibility; hold/recover via durable evidence |

Mismatch process: retain source/raw refs + context + rule version → classify transport/canonicalization, source-state drift, missed change, retention/generation, valid source anomaly hoặc unresolved identity → determine dependency/period impact → propose recapture/rebaseline/rebuild/restate with Owner review. Full rebuild không tự giải quyết thiếu forward history hoặc registry; restore/reconcile compatible evidence trước claim equivalence. Numerical thresholds/severity/cadence và Certified gates vẫn pending; không đặt tolerance để PASS.

## 9. Tương thích DW-01/DW-02/DW-03A

| Approved contract | Compatibility requirement / handoff |
| --- | --- |
| A01/A03 physical evidence | 9 current+2H, full admitted source projection, immutable captures; no hash/start-key dedupe |
| A02/G01 | Conditional coherent source context; source read-only account không chứng minh no writers; missing proof holds normal publish |
| A04/A06 | Separate identities; sealed replay/new-context-new-capture; coherent publication and pins; RawPublished khác Certified |
| B1/B2/ADR-SCD-02 | Không regenerate SK từ cursor/order/hash; preserve registry, revisions, supersession, compatible recovery |
| B3/B4/B5 | Exact transport không thay full-day validity; R/U/I và tiered certification/numeric gates giữ nguyên; no current/earliest fallback |
| B6/ADR-SCD-04 | History/forward bridge/source generation reconcile; no lost forward observations after full reload, no duplicate episodes |
| B7/B8 | Corrections qua old/new scope audit/rekey/restatement review; delete candidates không retire entity; reappearance Ambiguous nếu thiếu proof |
| DW-01 headers/customer roles | Detect headers độc lập; order chưa invoice giữ nguyên; buyer/bill-to riêng; header-only changes phải tạo impact envelope dù lines không đổi |
| Inventory Current | Product current version phù hợp cùng state, observation/publication khác nhau; không daily history |
| G01–G08 | Giữ toàn bộ gates DW-03A; Stage 2 không đóng source privileges, adapters/full Raw physical/retention/runtime gates |

Không phát hiện yêu cầu buộc đổi accepted architecture ở vòng này. Owner đã chấp nhận assurance Current-State Convergence, không complete intermediate events. Các **capability limits** được giữ rõ: complete transient-event capture, deterministic occurrence linkage khi H indistinguishable, reliable maximum lateness và confirmed-delete semantics chưa được nguồn chứng minh. Nếu Owner yêu cầu mạnh hơn, báo gap để duyệt riêng; không silently sửa architecture.

## 10. Runtime acceptance test specifications và SQL Server test environment

Mọi IT01–IT21: **PLANNED / NOT RUN**. Đây là test specification, không evidence thực thi. Kết quả B9 lịch sử chỉ kiểm representation/transport, không cho phép writes task này.

| ID | Scenario / môi trường cần — tất cả NOT RUN | Expected assertion / evidence |
| --- | --- | --- |
| IT01 | Read-only metadata/Q11/current+H recheck | Counts/NULL/duplicates/type/index/versioning/retention metadata được ghi, không suy write behavior |
| IT02 | INSERT + replay, writable SQL sandbox | New current PK đúng một accepted state, immutable repeated evidence và counts; original unchanged |
| IT03 | UPDATE key cũ, LEW tăng | Payload diff bắt đúng, cursor boundaries, full state equivalent |
| IT04 | UPDATE key cũ LEW không đổi / backdated | Chứng minh tuple-only miss; replay hoặc full recon phát hiện state; không false CDC |
| IT05 | Nhiều keys cùng LEW, chia nhiều pages | Không missing/double accepted rows, equality biên và stable cursor |
| IT06 | Long transaction commit sau upper-bound selection | Late-visible periods/LEW tested; missing window risk ghi rõ, reconcile tìm state |
| IT07 | Correction nằm ngoài proposed lookback | Full recon tìm mismatch, không claim lookback đủ |
| IT08 | Temporal nhiều UPDATE trong một transaction | Direct H giữ zero-duration và counts, SYSTEM_TIME ALL không thay evidence |
| IT09 | Current→H, duplicate starts/identical H payload | Multiset đúng, không fake unique source key hoặc duplicate analytical episode |
| IT10 | H correction/cleanup/restore, approved maintenance sandbox riêng | Detect coverage/generation change; no automatic Raw purge/splice; normal temporal path không direct H DML |
| IT11 | Holdings update quantity/cost với LEW cũ | Full row compare tìm change, key-only/row-count-only controls không được PASS thay |
| IT12 | DELETE ordinary/current temporal, full vs partial snapshot | Full absence chỉ candidate; partial không tạo candidates; verified policy gate trước action |
| IT13 | Delete→reappearance cùng NK | Audit continuity, Ambiguous khi thiếu incarnation proof, no SK meaning reuse |
| IT14 | INSERT→DELETE hoặc A→B→A giữa polls | Ghi giới hạn state polling, không fabricate missing events |
| IT15 | Interrupted extract/partial load/reconcile fail | Old publication/checkpoint không đổi, content-compatible retry only |
| IT16 | Reconcile PASS/publication fail/unknown commit | Durable read-back trước ACK; no loaded-only advance |
| IT17 | Commit success/crash/retry/concurrent stale base | Exactly one logical publication effect, no regression/mixed dependencies; DW-03C runtime proof |
| IT18 | Replay sealed/backfill/new context/full reload | Distinct capture semantics, forward/registry evidence giữ nguyên, compatible pins |
| IT19 | Header-only date/buyer/bill-to change | Captured headers + old/new dependency envelope dù line LEW không đổi; propagation test DW-03C |
| IT20 | NULL/Unicode/decimal/bytes/geography/time fixtures | Versioned null-safe equality, B9 exact100ns, collision/serialization negatives; không sửa B9 sandbox |
| IT21 | Source drift, reference/generation changes và recon totals netting | Hold inconsistency, full key/value checks phát hiện sai dù count/net totals bằng |

**SELECT-only được phép ở task riêng/readiness tiếp theo:** reuse metadata/profiling/relationship SQL, bounded samples, retained capture comparison, query-plan/scan-cost inspection khi được duyệt; offline fixture review/negative math là design evidence, không E2E writes.

**Writable SQL Server sandbox cần phê duyệt riêng:** local instance/database độc lập do DBA/Owner cấp; source identity/port/database/restore provenance rõ, approved backup/license/access và capacity; không ghi WWI original. Test principal chỉ writable trong sandbox, original least-privilege read-only tách riêng. Dữ liệu test tối thiểu phù hợp FK/types/temporal, không commit backups/payload/PII. Không tự chọn restore/clone method, tạo DB, DML, disable versioning, CDC/CT hoặc change engine configuration. Temporal same-transaction scenarios phải dùng engine behavior; history maintenance/correction là sub-scope riêng, không giả direct H DML khi versioning ON.

Target cho E2E cần **sandbox khác được duyệt**, schema/config approval và test dependencies; B9 existing sandbox không được dùng/sửa cho incremental. Test runner phải validate exact source/target allowlist, dừng nếu trỏ original. Ghi script revision, pre/post state, expected/actual keys/bytes/counts, durable IDs/transaction proof, versions và negative controls; credentials/output ngoài Git. No production capacity/failure claims từ fixture-scale tests.

## 11. Risk register và runtime gates

| Risk | Mức ảnh hưởng thiết kế | Mitigation / gate |
| --- | --- | --- |
| R01 Timestamp unchanged/backdated/late commit | Missed updates | INC-01/02/03 evidence + full reconciliation; không complete CDC claim |
| R02 Mutable source/context không coherent | Mixed state, false deletes | A02/G01 proof; hold |
| R03 H retention/indistinguishable occurrences | History loss/identity uncertainty | INC-04 multiset/generation/retention investigation, preserve forward evidence |
| R04 Partial snapshot interpreted delete | Mass false retire/retraction | INC-05 completeness gate và separate confirmation/action approval |
| R05 Precision/canonicalization/hash collision | Changed identity/equality | B9/G03–06, full payload exact comparison; no hash-only proof |
| R06 Checkpoint/publication split-brain, stale retry | Skips/double apply/regression | INC-06 durable binding/read-back, predecessor pin; G08/DW-03C tests |
| R07 Header/reference changes missed | Wrong groups/roles/type totals | Independent detection, dependency envelope, reference gate |
| R08 Growing immutable captures | Capacity/retention pressure | G07 measured bytes/capacity and approved dependency-safe retention; no invented period |
| R09 Full recon overclaim | Hidden intermediate events | State-vs-event assurance explicitly disclosed, Owner capability acceptance |
| R10 Unknown generation/reappearance | Wrong entity/episode/SK | B8 continuity proof, Ambiguous/hold, no blind merge |

INC-01–INC-06 **APPROVED — Logical Policy** trong [register](wwi-dw-03b-decision-register.md). Numeric/physical details, exact U/window algorithms, confirmation actions và runtime mechanisms vẫn pending theo [RG01–RG12](wwi-dw-03b-work-plan.md); không yêu cầu Owner approve lại logical directions. Design acceptance ở [assessment](wwi-dw-03b-assessment.md) không là runtime PASS. Dừng sau DW-03B; DW-03C/DW-04 TODO, không implementation.
