# WWI DW-03A — Full Extraction & Raw Logical Design / Physical Proposals

**IN_PROGRESS — Owner Logical Approval Milestone, 2026-11-15.** A01/A03/A04/A06 **Approved — Logical Policy**; A02 **Approved — Conditional Logical Policy**; A05 **Approved — PoC Direction Only (F2)** theo [Decision Register](wwi-dw-03a-decision-register.md). B1–B8/DW-02 không đổi; B9 **Pending Physical Approval**. Chỉ những logical principles được nêu trong approval là Approved; physical options/execution methods bên dưới vẫn cần evidence/review. Không final DW-03A acceptance hoặc runtime authorization. Runtime: **Not implemented yet**.

## 1. Evidence và phạm vi

[Work plan](wwi-dw-03a-work-plan.md), [Decision Register](wwi-dw-03a-decision-register.md) và [Assessment](wwi-dw-03a-assessment.md) giữ status/approval/QA. Dùng lại [inventory](wwi-database-inventory.md), [dictionary](wwi-metadata-dictionary.md), [profiling](wwi-data-profiling.md), [source contracts](wwi-source-contracts.md), [extraction matrix](wwi-extraction-requirements-matrix.md), [raw requirements](../requirements/wwi-raw-layer-requirements.md), [validation matrix](../requirements/wwi-source-validation-matrix.md). Không lập lại dictionary hoặc chạy lại profiling toàn bộ.

**Verified historical evidence:** metadata/profiles 2026-11-07 và temporal recheck 2026-11-14. Count dưới đây là reference ở lần khảo sát, không expected constants khi load. Git sạch là baseline Stage 1; hiện có các thay đổi Stage 1–3 chưa commit được bảo toàn, chưa có executable ingestion/Raw schema. **Latest verified source evidence 2026-11-15:** trusted TCP/encryption PASS, SNAPSHOT OFF, RCSI OFF, database READ_WRITE; metadata/interactive SELECT rights đủ 9 current + 2 H. [Evidence report](wwi-dw-03a-evidence-approval-readiness.md) section 10 thay kết luận TLS/current flags Unverified trước đây. Writer exclusion, full extraction consistency, service-account access, adapter fidelity và source/target performance vẫn Unverified; READ_WRITE không chứng minh đang có writes.

Thiết kế giữ kiến trúc SQL Server read-only → Python ingestion → PostgreSQL Raw → dbt staging → Kimball Core → marts → Power BI. Airflow orchestration thuộc implementation sau này. Design bao phủ chín MVP tables; **Sales end-to-end trước** vẫn giữ. Associated archives là evidence của hai master entities, không thêm hai business sources hoặc subject areas.

## 2. A1 / A01 — Full Extraction Design Matrix

Phân loại: **T** current system-versioned table; **H** physical temporal archive; **O** ordinary non-temporal current table; **S** current-state snapshot, không temporal. O chứa current records của bảng transaction, không là complete history của mọi row revision. T và H có populations khác nhau; chín bảng current đều PK một cột theo dictionary.

Method **F** đề xuất: explicit approved column projection, đọc full population không business filters; current PK ascending/keyset hoặc một streaming cursor, bounded fetch/load chunks trong cùng consistency context A02. Không OFFSET resume qua source snapshot mới. Mọi count/aggregate nguồn dùng cùng context nếu claim exact reconciliation. Không dùng `LastEditedWhen` làm CDC hoặc full-load eligibility filter.

| Source / class | PK/NK và extraction grain | Reference population / đặc điểm | Temporal metadata / source types | Initial full method đề xuất | Validation và Raw preservation |
| --- | --- | --- | --- | --- | --- |
| Sales.Customers / T | CustomerID, một current customer | 663 current; self BillTo FK; 31 columns, geography/PII/nullable fields | ValidFrom/ValidTo datetime2(7), date, decimal(18,2/3), Unicode, bit, geography | F current; separate H stream Customers_Archive trong cùng context | Current PK unique, BillTo refs, NULL/types; giữ toàn projected fields/periods, không chỉ Type2 vector |
| Sales.Orders / O | OrderID, một header | 73.595; gồm 3.085 chưa invoice; 16 columns | OrderDate/ExpectedDeliveryDate date; LastEditedWhen và nullable PickingCompletedWhen datetime2(7) | F, không inner join invoice/line để lọc | Count/key-set, Customer/backorder refs, header population; giữ comments/NULL/time, không tự canceled status |
| Sales.OrderLines / O | OrderLineID, một source line | 231.412; 12 columns, không mapping 1:1 InvoiceLine | Quantity/PickedQuantity int; nullable UnitPrice decimal(18,2), TaxRate decimal(18,3); datetime2(7) | F độc lập; lấy parent trong cùng context, không join làm nhân/drop rows | Unique PK, Order/StockItem refs; giữ nullable price, exact quantity/times, không lấy master price |
| Sales.Invoices / O | InvoiceID, một header | 70.510; 25 columns; OrderID optional, Buyer/BillTo riêng | InvoiceDate date; ConfirmedDeliveryTime nullable datetime2(7); Unicode/bit/int | F tất cả headers kể cả optional OrderID; giữ no-line nếu xuất hiện | PK, parent/role checks, NULL delivery; không lọc recognized revenue/status chưa duyệt |
| Sales.InvoiceLines / O | InvoiceLineID, một line | 228.265; 13 columns; LineProfit âm không mặc định invalid | Quantity int; monetary decimal(18,2), rates decimal(18,3); datetime2(7) | F độc lập rồi grouped reconciliation với header | PK/Invoice/StockItem refs, per-key amounts + totals; không join payments/movements vào payload |
| Sales.CustomerTransactions / O | CustomerTransactionID, một transaction | 97.147; 14 columns; 26.637 payment InvoiceID NULL | TransactionDate/date fields, TransactionAmount/tax/balance decimal(18,2), bit, datetime2(7) | F mọi types; không chỉ InvoiceID non-NULL | Count/sums theo type riêng; giữ optional InvoiceID/PaymentMethodID; không payment allocation |
| Warehouse.StockItems / T | StockItemID, một current item | 227 current; 25 columns, varbinary Photo, computed Tags, CustomFields | ValidFrom/ValidTo datetime2(7); decimal(18,2/3), Unicode, bit, varbinary(max) | F current + separate H StockItems_Archive cùng context | Unique PK, nullable/descriptive fields, blobs và computed output; không lọc chỉ admitted dimension fields |
| Warehouse.StockItemHoldings / S | StockItemID, một current holding | 227; QuantityOnHand tổng 30.343.296 ở snapshot cũ; 9 columns | QuantityOnHand/stocktake int, LastCostPrice decimal(18,2), LastEditedWhen datetime2(7) | Full current-state read; capture window/context cùng Product current | PK/ref, exact quantity/value sum, complete coverage; không daily historical balance hoặc overwrite state trước validation |
| Warehouse.StockItemTransactions / O | StockItemTransactionID, một movement | 236.667; 11 columns; signed/zero quantities, optional invoice/PO/customer/supplier | Quantity decimal(18,3); TransactionOccurredWhen/LastEditedWhen datetime2(7) | F mọi types, giữ signs; optional parents không làm inner join filter | PK, qty theo type, non-NULL RI; type/reference validation ngoài chín bảng là dependency chưa có ingestion approval |

### Temporal archive populations — A01 approved scope, access/fidelity gates còn mở

| H stream | Grain / reference evidence | Proposed preservation |
| --- | --- | --- |
| Sales.Customers_Archive | 51 physical rows, 46 NK; current+H=714; SYSTEM_TIME ALL=713 | Đọc trực tiếp physical archive với origin H và exact periods; giữ một zero-duration row. CustomerID+ValidFrom đã không unique; không dùng làm Raw uniqueness constraint |
| Warehouse.StockItems_Archive | 444 physical rows; current+H=671 | Giữ từng source occurrence, full projected payload và periods; không collapse chỉ vì Type2 vector không đổi |

Owner đã duyệt A01 full-preservation scope gồm chín current tables và hai physical archives H, hỗ trợ B1/B2/B6. Logical scope approval không thay effective least-privilege access và concrete projection/type-fidelity verification. Không dùng temporal `AS OF` hoặc `ALL` thay physical evidence capture; không `DISTINCT`/UNION dedupe archive. Current và H phải cùng source consistency context hoặc được ghi qualified/incomplete; row chuyển current→archive giữa reads không được diễn giải như hai business events.

### Data type fidelity — yêu cầu mapping, chưa chốt physical schema

| Source family | Candidate Raw representation / kiểm soát |
| --- | --- |
| int, bit | Exact integer/boolean mapping, giữ NULL; source PK values không regenerate. Không chạy defaults/sequence nguồn ở target |
| decimal(18,2), decimal(18,3) | Exact decimal/numeric path, không binary float hoặc rounding sớm. Preserve value + source precision/scale trong contract; aggregate đủ capacity, field/null profile checks |
| nvarchar(n/max) | Unicode text, length/encoding/NULL/rỗng/trailing spaces được kiểm; không trim/case-fold/normalize payload. Adapter phải xét ký tự không biểu diễn trực tiếp trong target encoding; unresolved fidelity chặn capture claim, không thay byte âm thầm |
| date | Giữ calendar date, không gán 00:00/timezone thành business instant |
| datetime2(7) | Exact representation theo A05/B9 cho cả periods và ordinary timestamps; không qua microsecond-only conversion rồi thêm số 0 để giả precision |
| varbinary(max) | Exact bytes/byte length/content validation, không decode thành text hoặc bỏ Photo vì không nằm trong analytical dimension |
| geography | Candidate SQL Server native serialized binary + type/version/SRID provenance; PoC reconstruct và byte/value equivalence trước chọn adapter. Không tự thêm PostGIS hoặc chỉ giữ tọa độ/WKB rồi claim toàn source value bảo toàn |
| CustomFields/Tags, computed/string JSON | Giữ original textual/computed output và metadata computed flag, không tái tính Tags. JSONB có thể là derived convenience sau này, không là sole lossless copy |

Native binary conversion của geography dùng SQL Server serialization theo [Microsoft geography](https://learn.microsoft.com/en-us/sql/t-sql/spatial-geography/spatial-types-geography-transact-sql?view=sql-server-ver17); đó là cơ sở chọn candidate, **chưa là verified adapter**. JSONB không giữ mọi textual details của JSON theo [PostgreSQL JSON](https://www.postgresql.org/docs/18/datatype-json.html). Không mở rộng analytical field admission vì Raw giữ source fields. PII/blobs cần quyền truy cập và retention approval, không đưa raw payload vào Git/logs.

## 3. A2 / A02 — Source Consistency Options Matrix

Các guarantees bên dưới là semantics engine được đối chiếu primary documentation, **không phải kết quả thử trên WWI hiện tại**. [Microsoft isolation levels](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-transaction-isolation-level-transact-sql?view=sql-server-ver17) phân biệt RCSI theo statement và SNAPSHOT theo transaction, với ALLOW_SNAPSHOT_ISOLATION là prerequisite. [Locking/versioning guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide?view=sql-server-ver17) là nguồn trade-offs vận hành.

| Candidate | Preconditions | Guarantees | Limitations | Operational impact | Verification | Recommendation | Owner decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 One read-only SNAPSHOT transaction | Cần snapshot state ON; hiện đã verified OFF nên không khả dụng | Nếu được hỗ trợ/enabled sẵn: cùng transaction-visible committed state xuyên scope | Không business-effective snapshot hoặc independently shared context; hiện không được tự enable | Long transaction/version retention và resource pressure nếu được dùng sau này | Flag ON/session/resource/context proof tại môi trường được duyệt riêng | Loại khỏi lựa chọn thực thi trên WWI hiện hành | Không tự đổi DB config; thay đổi sau này cần approval riêng |
| C2 Verified no-writer/static-source window | DBA/source owner có evidence nguồn không thay đổi trong toàn window, đầy đủ mọi writers; không tự set DB read-only | Consistent static state có điều kiện với evidence thật | Account read-only hoặc old max timestamp không chứng minh source static; before/after count/hash không đủ proof | Repeated scans; phụ thuộc vận hành ngoài extractor | Attestation/write controls + windows + rereads; không suy từ profiler cũ | Khuyến nghị ưu tiên có điều kiện cho local portfolio với cấu hình hiện hành | Owner chấp thuận method/evidence/window; chưa thực hiện writer controls trong task này |
| C3 Serializable single transaction | Source operation approval/permissions và capacity cho locking | Serializable logical read consistency, không gọi là snapshot tại start time | Blocking/deadlock/resource risk; giữ transaction lâu, không tự áp trên source | Range/shared locks có thể cản writers | Engine semantics + DBA reviewed load/concurrency tests | Alternative cân nhắc riêng, không MVP default | Phê duyệt operational impact trước use |
| C4 RCSI hoặc per-table reads | RCSI phải enabled nếu claim statement snapshot; hiện RCSI OFF; mỗi statement/cursor context được ghi | RCSI khi enabled chỉ statement snapshot; locking READ COMMITTED per-table read không có guarantee MVCC point-in-time | Paging/count/table khác statement có thể khác state; không gọi locking read là statement snapshot | Shorter contexts, reread/reconcile overhead | Header/line/current/H drift, count/key/aggregate comparisons; label windowed khi chưa proof | Diagnostic/qualified captures, không global snapshot claim | Chỉ publish qualified Raw nếu Owner duyệt rõ limitation/use restrictions; default hold normal publication |
| C5 DBA-provided consistent copy/snapshot | Edition/capability/license/quyền và task tạo bản độc lập được phê duyệt | Theo verified consistent copy state và writer exclusion, không mặc định mọi copy là consistent | Chưa có sẵn/verified; không tạo snapshot/restore/clone ở đây hoặc assume Express hỗ trợ database snapshot feature | Additional storage/operations | Restore/copy provenance, source identity, no-writer và consistency evidence | Proposed fallback ưu tiên khi không chứng minh được C2 | Task/approval riêng; không đổi stack |
| NOLOCK/READ UNCOMMITTED hoặc REPEATABLE READ-only claim | Có thể SELECT nhưng không đáp ứng full snapshot requirement | Không được dùng như chứng minh full snapshot | Dirty/missing/duplicate observations hoặc phantoms; REPEATABLE READ không chặn mọi insert | Ít khóa không bù được lack of guarantee | Xem engine semantics | Không đề xuất cho validated full capture | Không xin chọn shortcut này |

**A02 — Approved Conditional Logical Policy; concrete method chưa verified:** SNAPSHOT/RCSI OFF nên không chọn C1. Ưu tiên C2 static window chỉ khi chứng minh không có writes toàn required scope/interval; nếu thiếu kiểm soát đó, ưu tiên review C5 consistent copy được chuẩn bị và phê duyệt riêng. C3 chỉ khi Owner chấp thuận riêng rủi ro locking/operational envelope; không chạy transaction dài ở task này. [Evidence report](wwi-dw-03a-evidence-approval-readiness.md) section 10 so sánh đầy đủ ba phương án A=C2, B=C5, C=C3, không đổi IDs thiết kế cũ. Chưa có method proof thì giữ **WINDOWED_UNVERIFIED**, hold normal publication; reconciliation pass/FK hợp lệ không chứng minh common source state. Diagnostic/qualified use cần approval riêng. Temporal AS OF hai masters không sửa consistency của ordinary transaction tables.

Source account cần SELECT theo từng current/archive object và metadata visibility. Trusted endpoint và interactive permissions đã verified; interactive session có sysadmin nên không là least-privilege service-account proof. Flags đọc qua [sys.databases](https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/sys-databases-transact-sql?view=sql-server-ver17) hiện là OFF/OFF/READ_WRITE; no-writer evidence, service account, target profile và resource limits còn thiếu. Không tự bật SNAPSHOT/RCSI/Change Tracking hoặc CDC. Capture evidence không bịa LSN/exportable snapshot token từ timestamp.

### Execution outline đề xuất, không phải pipeline đã triển khai

1. Preflight contract/schema signature, exact adapters, source capabilities và declared publication scope. Dùng explicit columns, gồm hidden/generated periods nếu có; schema drift hold thay vì SELECT * âm thầm đổi payload.
2. Tạo candidate capture/source-context manifest; transaction/read method chỉ dùng sau approval. Counts/reference aggregates và rows cùng context khi claim exact source comparison.
3. Đọc masters current+H rồi headers/lines/transactions theo dependencies; thứ tự không tự tạo consistency. Cursor/fetch chunks nối cùng context; current PK keyset có predicate/coverage manifest. H thiếu unique source key ưu tiên một uninterrupted stream; không resume OFFSET rồi assume không mất duplicate occurrences.
4. Load immutable candidate chunks vào PostgreSQL trong target transactions riêng, lưu chunk identity/count/digest. Tốc độ target có thể kéo dài source context: đo limits trước implementation, không đặt chunk size/timeout giả định để claim performance.
5. Khi streams/capture đầy đủ, seal manifest, kiểm target và reconcile; đóng source context. Publish target state qua A06 sau gates. Không có distributed transaction SQL Server↔PostgreSQL trong proposal.

Sales-first publication scope đề xuất: Customers/StockItems current+H và năm Sales transaction/header/line tables; đây là bảy current tables + hai H streams phục vụ Sales, không phải yêu cầu hoàn thiện Customer/Inventory analytics trước Sales. Design hai Inventory tables vẫn đầy đủ ở matrix; khi mở Inventory cần source context/master evidence tương thích mới, không gọi hai scopes khác thời điểm là một global snapshot. Scope/gates phải khai báo trước capture, không cắt scope hậu kiểm để che batch lỗi.

## 4. A3 / A03 — Raw Architecture Alternatives

| Option | Ưu điểm | Trade-off / replay / history | Đánh giá đề xuất |
| --- | --- | --- | --- |
| R1 Append-only batch snapshots + published manifest/view | Giữ source values/capture evidence và projection | Repeated full loads tăng storage; manifest/pointer cần quản lý. Chưa thêm second copy | Immutable captures/reconciled manifests/pinned identities Approved ở mức logic; view/layout/retention/access/capacity pending physical approval |
| R2 Current-state Raw mirror | Serving nhẹ, storage bounded hơn | Upsert ghi đè evidence/attempts, khó zero-duration/hybrid/rebuild; phải thêm audit để đáp ứng B2/B6 | Không đủ khi dùng một mình |
| R3 Generic immutable row envelopes + materialized current mirror | Flexible events, audit và serving riêng | More copies, generic serialization/type fidelity và per-field querying phức tạp | Có thể phù hợp sau, chưa cần làm default |
| R4 Full hybrid event log + snapshots + current mirror | Rich incremental features | Complexity/retention/compaction trước DW-03B decisions, nhiều publication boundaries | Không đề xuất Stage 1 MVP |

**R1 recommended:** source-shaped append-only capture records + control manifests; published state là immutable membership set được consumer pin theo `raw_publication_id`, có current pointer/view chọn membership, không materialize thêm mirror mặc định. Không TRUNCATE/overwrite prior batches khi full reload; không áp SCD2, generate episode hoặc Warehouse SK tại Raw. Physical per-source relation/layout/index/partition/loading mechanism chưa chọn; structured typed columns là candidate để giữ decimals/blobs/NULL, kèm exact temporal serialization. Không mặc định JSONB envelope đủ lossless.

```mermaid
flowchart LR
  S["WWI approved read context"] --> E["Full current + physical history capture"]
  E --> R["PostgreSQL immutable Raw candidates"]
  R --> Q["Completeness / fidelity / reconciliation"]
  Q --> P["Atomic published membership"]
  P --> D["dbt staging pins publication ID"]
  D --> C["Kimball Core: separate SCD2 policies"]
  C --> M["Marts: separate certification gates"]
```

Sơ đồ là proposal, không mô tả pipeline đang chạy. Storage growth ước lượng theo tổng các captures được giữ: `sum(rows × average source payload + per-record metadata) + manifest/index/backup overhead`; Photo/Unicode/history/failed attempts có thể chi phối. Chưa đo average bytes, compression, throughput hoặc retention cost; không đưa số benchmark giả định thành evidence.

### Conceptual objects và keys — không DDL

| Object concept | Logical key / identity | Purpose / constraints |
| --- | --- | --- |
| Source/contract descriptor | source_instance_id + object + contract/projection/serialization versions | Một WWI source; restore/incarnation lineage phải rõ, không coi schema Sales/Warehouse là hai sources |
| Capture manifest | capture_id + declared scope + source-context evidence | source observation identity riêng run/batch; snapshot label không tự guarantee transaction consistency |
| Stream batch | logical_batch_id = capture + object + population(current/H) + projection version | Một logical population; one accepted attempt, counts/key/range/manifest evidence; FULL mode hiện tại |
| Execution attempt/chunk manifest | attempt_id; batch + stable chunk_id trong sealed content | Retry identity riêng, exact content equality/digest/count trước skip; không reuse chunk ID cho changed payload |
| Immutable Raw records | technical capture-record locator liên kết batch/accepted attempt/chunk/record ordinal | Giữ source PK/NK/value/source object/periods/origin. Current PK unique trong complete source population là validation; archived repeated NK hợp lệ |
| Validation/quarantine ledger | batch/attempt + check/reason + record reference | Raw evidence còn nguyên; quarantine không tự hợp thức hóa publish thiếu source rows |
| Published membership / current pointer | raw_publication_id → complete immutable batches và manifest revisions | Atomic visibility cùng source-context scope; consumer pin publication, không query latest độc lập từng table |

Record ordinal chỉ là locator của **sealed capture content**, không durable source occurrence identity hoặc analytical episode/SK. Archive exact duplicate physical rows nếu có vẫn phải giữ multiplicity; payload hash bằng nhau không cho phép collapse. Không source-enforced unique occurrence key thì ghi limitation/ambiguity, không tự phát minh ordinal có nghĩa lịch sử. Retry source query mới có thứ tự tie khác không được reuse old ordinal để claim same observation; replay dựa retained sealed capture.

Retention cần Owner duyệt: published/candidate/failed captures, raw PII/photo bytes, manifests/serialization versions và forward evidence. Chưa đặt số ngày hoặc tự purge. Không giữ full snapshots vô hạn theo mặc định: theo dõi rows/bytes/repeated captures/storage growth, sau đó proposal retention/compaction có dependency/reference protection. Không xóa evidence đang dùng bởi registry/supersession/publication hoặc accepted forward history. Raw retention không thay backup/restore compatible registry set theo B2.

### Interface cho incremental tương lai, không chọn incremental strategy

Manifest hỗ trợ extraction_mode và source change metadata/basis riêng; future capture có thể là FULL/INCREMENTAL/BACKFILL theo approved contract. Published membership nêu explicit covered population và base-publication link khi sau này có deltas; partial delta không giả full snapshot. Source rows và source deletion evidence/audit sẽ đi qua contract DW-03B, không định nghĩa watermark/tombstone/event precedence tại đây. Append-only retention không tự là CDC. Staging/Core consume accepted membership, source row revisions và origin; không phải viết lại Raw để giữ history sau này.

## 5. A4 / A04 — Batch Metadata, Lineage & Idempotency

| Metadata group | Fields concept / semantics |
| --- | --- |
| Execution | pipeline_run_id cho invocation; attempt_id cho retry; started/ended/error class/retry_of. Một run có nhiều batches; retry có thể run mới |
| Logical capture | capture_id, scope, consistency_class/evidence, source_instance/restore lineage, engine/schema/contract/projection/serialization versions, context/session linkage, capture start/end |
| Snapshot identity | source_snapshot_id **nullable** nếu không có real source identifier; local capture_id không masquerade native snapshot token. Source context window và consistency proof riêng |
| Source stream/batch | schema/table/object/population current/H, extraction_mode, logical_batch_id, source PK fields, chunk coverage, batch↔capture link |
| Counts | expected/source_count + measurement context/time/status; extracted unique logical records; Raw-loaded unique records; rejected distinct logical record count; duplicate delivery attempts và attempted rows riêng |
| Row lineage | source PK/NK, exact temporal values/origin, raw-record locator, batch/attempt/chunk IDs, optional payload digest/canonicalization version; sensitive payload không log |
| Times | extraction_start/end, extracted_at/observed window, loaded/sealed/validated/published_at riêng. Pipeline metadata đề xuất UTC; source timestamps giữ original semantics/precision |
| Quality/publication | extraction/load/validation statuses, source completeness/consistency classification, check counts/diffs, quarantine refs, publication ID/prior ID/approval reference/manifest fingerprint |
| Recovery | retry_of/supersedes attempt, retained-content refs, target commit outcome, error/reason, restore/publication revision, cancellation/abandonment audit |

`batch_id` không phải `run_id`; capture/snapshot không phải publication. Batch identity gắn immutable observed content. Full re-extract ở thời điểm khác là **capture mới**, không retry same snapshot dù source values tình cờ giống. Replaying sealed batch có thể run/attempt mới nhưng cùng accepted logical rows. Các metadata này là logical proposal; physical datatype, ID allocation và table names chưa duyệt.

Candidate execution states: PLANNED → EXTRACTING → EXTRACTED_COMPLETE → LOADING → LOADED → VALIDATING → VALIDATED; streaming có thể EXTRACTING/LOADING overlap nhưng không coi complete trước seal. Failures → FAILED/PARTIAL, context lost → ABANDONED candidate; không chuyển thành complete bằng sửa status. Publication axis riêng: UNPUBLISHED → ELIGIBLE → RAW_PUBLISHED; QUALIFIED chỉ khi Owner explicitly approve limited Raw use; REJECTED/HOLD cho gate fail. Các labels chưa là enums/schema được triển khai.

| Failure phase | Proposed retry/recovery | Idempotency/publication rule |
| --- | --- | --- |
| Trước extraction complete | Giữ diagnostics/chunks; chỉ resume nếu same live source context + exact continuation được chứng minh. Mất context thì abandon và capture mới | Không ghép old/new observations thành full snapshot |
| Trong loading | Nếu exact chunk còn retained/sealed thì retry same logical chunk; commit outcome unknown phải inspect target manifest/content trước retry | Same chunk ID + changed bytes là conflict; không bỏ legit archive duplicates |
| Raw loaded, metadata chưa finalize | Đọc durable chunk/capture manifests và source completion proof; đủ evidence thì reconcile/finalize, thiếu thì hold | Không mark loaded chỉ vì row count bằng; không nạp lại mù tạo double rows |
| Trong reconciliation | Re-run checks trên same immutable capture, cùng check/version/context | Source count requery ở snapshot mới không thay expected count cũ |
| Trước publication | Candidate invisible, giữ previous publication; retry compare manifests và eligibility | Không exposed table-by-table partial generation |
| Sau publication hoặc ACK mất | Tra publication ledger/manifest identity; nếu already published thì return same logical result | Không apply lần hai hoặc chuyển pointer ngược nếu newer publication đã được approved; concurrent publication có version/precondition checks |

**Synthetic lineage example — minh họa IDs, không WWI row thực:** run R1 tạo capture C1, scope S, batch B1 cho Invoices, attempt T1 và chunk K1; Raw locator C1/B1/K1/ordinal gắn source InvoiceID giả định 100. Target đã commit chunk nhưng client mất ACK: T2 inspect K1 content/count/manifest rồi reuse, không append lần hai. Nếu SQL source context đã mất trước khi toàn scope complete, C1 partial không publish; re-extract là C2/B2, không gán các dòng mới vào C1. Không cấp Warehouse SK hoặc analytical episode cho ví dụ.

## 6. A5 / A05–B9 — Exact Temporal Representation Proposal

Logical exact 100 ns đã duyệt. SQL Server datetime2 có scale tối đa 7 và không mang timezone offset theo [Microsoft datetime2](https://learn.microsoft.com/en-us/sql/t-sql/data-types/datetime2-transact-sql?view=sql-server-ver17). PostgreSQL timestamp có resolution microsecond theo [PostgreSQL datetime](https://www.postgresql.org/docs/18/datatype-datetime.html); numeric/integer capabilities theo [PostgreSQL numeric](https://www.postgresql.org/docs/18/datatype-numeric.html). Python datetime fields/resolution cũng microsecond theo [Python 3.12 datetime](https://docs.python.org/3.12/library/datetime.html). Vì vậy bảo toàn tại target chưa đủ nếu driver đã mất chữ số thứ bảy trước đó.

**A05 — Approved PoC Direction Only:** F2 explicit seven-digit source-side formatting là preferred candidate cho precision PoC; test carrier là canonical text 27 ASCII characters `YYYY-MM-DDTHH:mm:ss.fffffff`, NULL riêng, trước Python datetime coercion. P1 authoritative Raw text/storage vẫn là physical proposal, **không được chọn bằng PoC direction approval**. Canonicalization chỉ làm trên output đã giữ đủ precision, không reconstruct digit đã mất. Chưa chốt physical text type/collation/index hoặc expression/driver implementation. Exact comparison phải dùng normalized format và verified bytewise ordering hoặc derived exact representation đã được duyệt; không dùng target default collation hoặc timestamp(6) predicate một cách ngầm định.

| Candidate | Round-trip / driver và source extraction | Sorting/range/boundaries | Storage/index cost & maintainability | dbt/SCD2 impact |
| --- | --- | --- | --- | --- |
| P1 Fixed-precision canonical text | Giữ đủ 7 digits nếu lấy source text đúng; tránh timestamp coercion. Source CAST/CONVERT length/style phải PoC, không assume style tự luôn đủ 7 digits | Fixed-width valid dates + approved bytewise comparator; zero-duration/adjacent/sentinel giữ exact. Timezone/basis phải compatible | 27 ASCII payload bytes/value trước row/index overhead; wider indexes, validation/parsing cần quản lý; không benchmark | Raw audit dễ; stage giữ exact column, không cast-only timestamp cho historical predicates |
| P2 Integer 100 ns ticks | Exact integer path từ full components, không float total_seconds. Candidate civil epoch 0001-01-01, không tự UTC | Integer ordering thuận interval logic; epoch/range/calendar phải versioned; zero/open-end giữ exact | Candidate 8-byte bigint; compact hơn text về scalar payload, codec phức tạp hơn; exact source conversion cần PoC | dbt numeric predicates có thể dùng sau approval; display timestamp chỉ derived |
| P3 Numeric packed calendar encoding | 21-digit `YYYYMMDDhhmmssfffffff` như exact decimal integer, leading zeros reconstruct bằng fixed-width rule | Numeric ordering với valid fixed-format calendar; không phải elapsed duration/ticks, không trừ packed values để tính thời gian | Candidate exact numeric, variable storage/index overhead; tránh float và implicit scale rounding | Giữ exact digits nhưng semantic codec/validation kém quen thuộc; không mặc định dùng cho target |
| P4 Native timestamp + residual | Microsecond base **truncate**, residual digit 0–9 và exact source text/provenance; mọi bước phải giữ residual từ nguồn chưa mất precision | Compare tuple(base,residual), không chỉ base; rounding base cần rule khác, không gán residual sau lossy conversion | Native base 8 bytes + component/row/index overhead; composite indexes/queries, sentinel và carry risk | Thuận ordinary timestamp tools nhưng SCD2 queries phải dùng exact tuple; dễ accidental timestamp-only join |
| P5 Native timestamp only | Không giữ 100 ns nói chung | Distinct values có thể collapse/round, adjacency/sentinel có thể đổi | Đơn giản nhưng không đáp ứng D05 | Không đề xuất cho authoritative temporal source value |

Các lựa chọn text/ticks/numeric giữ civil value và declared source semantics; không tự gán Z/UTC vào mọi LastEditedWhen hoặc TransactionOccurredWhen. Period engine được mô tả theo UTC transaction begin trong [Microsoft temporal overview](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal/overview?view=sql-server-ver17); điều đó không biến ordinary source datetime2/business date thành UTC hoặc business-effective time. Pipeline observed_at UTC là metadata proposal riêng. Không so chéo history_basis chỉ vì cùng encoding.

### Synthetic round-trip vectors — mathematical expectations, không database/driver results

V1=`2026-11-15T12:34:56.1234567`; V2=`2026-11-15T12:34:56.1234568`. Hai giá trị cách nhau 100 ns. Canonical ticks candidate epoch 0001-01-01 với Gregorian civil arithmetic; chưa chọn epoch vật lý.

| Representation | V1 exact encoding / reconstruction | V2 / fidelity result dự kiến |
| --- | --- | --- |
| P1 text | `2026-11-15T12:34:56.1234567` → cùng chuỗi | Giữ `.1234568`, khác V1 |
| P2 ticks | `639303428961234567` → V1 | `639303428961234568`, khác 1 tick |
| P3 numeric packed | `202611151234561234567` → pad 21 digits rồi parse → V1 | `202611151234561234568`, khác 1 packed unit tại vị trí này |
| P4 base+residual | base `2026-11-15T12:34:56.123456`, residual `7` → V1 | Cùng base, residual `8`; tuple phân biệt |
| P5 timestamp-only | Nếu truncate: `.1234560`; nếu nearest-microsecond round: `.1234570` | V1/V2 có thể collapse; không thể round-trip exact. Actual converter behavior chưa verified |

Sentinel `9999-12-31T23:59:59.9999999` → candidate ticks `3155378975999999999`, dưới signed bigint max `9223372036854775807`; minimum year 0001 → 0 theo candidate epoch. P3 sentinel packed `999912312359599999999`. P4 truncate base `.999999` + residual 9 tránh carry giả; P5 rounding có thể sang năm 10000, không round-trip SQL datetime2 range. Đây là derivation số học, không kiểm SQL cast/driver/PostgreSQL.

Zero-duration giữ from=to exact, không interval dương; same `(NK,ValidFrom)` có thể nhiều physical occurrences. B9 encoding không phải source occurrence key và không thay registry episode identity. Hash/text equality không tự dedupe occurrences.

### Required end-to-end PoC — chưa hoàn tất; SQL subset mới trong evidence section 10

1. SQL source export → chosen driver → Python carrier → PostgreSQL → return exact source representation; kiểm every digit cho V1/V2/NULL/minimum/sentinel/leap day/year rollover/trailing zeros và whole seconds. Record driver/server/PostgreSQL/codec versions, settings, expected/actual bytes/value.
2. Chứng minh source expression đủ length/scale, locale-independent; style/default formatting và trailing-zero cases theo [Microsoft CAST/CONVERT](https://learn.microsoft.com/en-us/sql/t-sql/functions/cast-and-convert-transact-sql?view=sql-server-ver17). Padding chỉ hợp lệ khi source value đã exact; không padding để chữa mất precision.
3. Exact ordering/predicates half-open, adjacent 100 ns boundaries, same-start zero-duration/positive occurrence; các analytical matches không dựa timestamp(6). Text collation/ticks overflow/packed numeric validity/residual tuple và NULL semantics đều có negative cases.
4. Compare expected row multiplicity, source/full-period identities, collision cases; no driver auto-coercion/rounding. Conversion conflict hoặc mất proof phải hold fidelity gate, không route thành successful match.
5. Test schema/transport serialization of decimals/Unicode/varbinary/geography và protected payload; compatible restore/codec version trước rebuild. PoC fixtures synthetic hoặc isolated approved environment, không DML WWI gốc.

## 7. A6 / A06 — Reconciliation & Publication Proposal

Counts definition đề xuất: `E` distinct delivered logical records của sealed extraction; `L` accepted Raw logical records; `Q` rejected logical records retained with references/evidence, không duplicate retry attempts. `E=L+Q` chỉ là transport accounting khi L/Q disjoint và complete; **Q>0 hoặc thiếu fidelity/required source rows không được tự coi full capture complete**. Source `S=E` chỉ claim khi cùng exact context/population; count unknown phải giữ unknown, không fill bằng extracted count. Failed attempts/delivery retries đếm riêng, không cộng vào E. Archive comparisons dùng multiset/multiplicity, không chỉ distinct NK.

| Gate / existing validation mapping | Checks và evidence cần có | Proposed failure/publication behavior |
| --- | --- | --- |
| Completeness S01/I01–03 | Expected scope/streams/ranges, same-context COUNT_BIG, source↔capture↔Raw key-set/multiset, missing/extra/duplicate deliveries; current PK unique | Missing stream/range/row/unknown context hold; baseline historical counts không làm hardcoded threshold |
| Types/precision S02/S08/I04 | Required/optional NULL profiles, Unicode/blobs/UDT, exact decimal and 100 ns per-field comparisons | Reject/retain original evidence, hold complete-fidelity claim; không silent casts/default/rounding |
| Temporal S06/I11 | Current/H riêng, exact periods/source origin/multiplicity, zero/negative/overlap/gap distributions; full tuple vs same-start collisions | Zero-duration giữ audit, không fail chỉ vì tồn tại; proven corruption hold; history coverage gap không được xóa hoặc invent fill |
| Source→Raw measures I06/I08 | Per-PK values rồi sums/count/NULL/min/max theo source table/context; invoice ExtendedPrice/TaxAmount/LineProfit, CT TransactionAmount riêng; signed movement qty và holdings cùng capture | No cross-grain SUM; aggregate equality một mình không đủ vì netting/missing keys; tolerance cần approval, không tự đặt |
| RI/header-line S03–05/I05 | Orders→Customers, OrderLines→Orders/Product, invoice role/FK và optional OrderID, InvoiceLines→Invoice/Product, CT optional Invoice, holdings/movement→Product | Missing parent do inconsistent scope khác historical unresolved dimension; không drop headers/lines hoặc silent source repair; external reference checks phải ghi unverified nếu chưa có contract |
| Cross-source arithmetic I07/I09 | Group riêng invoice lines↔invoice transactions theo InvoiceID; issues↔invoice lines theo InvoiceID+StockItemID khi scope/type contracts đủ | Diagnostic source consistency check, không tạo KPI/allocation/line-level FK. New discrepancy cần investigation/Owner severity policy, không sửa nguồn |
| Purchasing dependency I10 | Chỉ đánh giá khi có separately approved PO contract/read evidence | NOT APPLICABLE cho initial Sales scope nếu chưa mở Purchasing; không thêm PO ingestion mặc định |
| Replay/partial I12 | Manifest coverage/accepted attempts/content digests, idempotent retries, unknown commit recovery, eligible state version | Partial/failed candidates invisible trong normal published membership; giữ prior publication |
| Context/security/retention | Proven consistency class, TLS/least privilege, protected payload retention/serialization versions | No schema/permission/precision bypass; qualified publication phải explicit Owner approval, không default |

Hash chỉ là supplementary digest cho content/chunk tamper/replay checks; canonicalization/version/NULL/length/decimal/temporal/binary distinctions phải rõ. Không dùng SQL CHECKSUM/hashing-only làm proof source population hoặc occurrence identity; collisions/netting và unavailable same-context source digest không được che. Exact equality/row accounting không có tolerance tự chọn; business DQ thresholds và semantic discrepancies vẫn cần approved policy. Raw giữ faithful source anomalies; raw invalid fidelity/incomplete capture khác source business anomaly được preserve và report. Historical dimension lookup U là Core concern, không lý do loại raw row.

### Eligible, atomic visibility và rollback

**A06 — Approved Logical Policy:** dependency-complete atomic publication với coherent ledger/membership/active-pointer transitions và compatible consumer pins. Crash/retry/concurrency/rollback/atomic visibility phải verified trước runtime; RawPublished không là Certified marts. Detailed gate implementation dưới đây vẫn cần review. Normal `RawPublished` chỉ khi declared scope đã được duyệt trước, mọi required batch/attempt sealed, source consistency proof đạt approved class, target rows/counts/keys/types/precision reconciled, required source anomaly disposition rõ và manifests immutable. ExtractionComplete → LoadComplete → Reconciled → RawPublished là các milestones khác nhau. Downstream models/certified KPI có D06/B5 gates riêng; không tự Certified chỉ vì RawPublished.

PostgreSQL candidate rows có thể được commit từng chunk để recovery; reader bình thường chỉ truy cập accepted published membership, không thấy candidates. Publication ledger và pointer/membership visibility đổi trong cùng target control transaction sau check generation/version; consumer/dbt run pin publication ID cho mọi source table, không từng model query latest khác nhau. Đây là architectural requirement/proposal, chưa chọn isolation/physical objects/transaction implementation.

PostgreSQL loaded nhưng orchestrator mất ACK: read-back accepted chunk/content manifests + complete extraction seal và publication ledger; nếu đã published thì không apply lại, nếu loaded đủ mà chưa published thì validate/finalize có kiểm concurrency. Nếu seal/context proof mất thì hold/abandon; không suy từ loaded row count rằng source extraction đã complete. SQL Server/PG không có assumed shared commit. Rollback publication chỉ chọn compatible prior set và audit; không xóa candidate evidence hoặc registry. Rollback Raw pointer không tự rollback Core/mart đã consume; downstream lineage/impact/correction execution thuộc DW-03C, ở đây chỉ yêu cầu không expose mixed states.

## 8. DW-02 Compatibility Review

| Accepted constraint | Proposed preservation / giới hạn |
| --- | --- |
| B1/B2 durable registry và identity continuity | Raw retained evidence/serialization/manifests hỗ trợ registry restore, nhưng không tạo registry/SK; compatible registry/publication recovery vẫn cần thiết kế/test riêng |
| Occurrence ≠ episode ≠ SK | Full T/H rows, source PK và raw locators khác analytical identity; không dedupe theo vector/start hoặc phát minh durable occurrence order |
| B3 whole-day consensus/no fallback | Exact source timestamps/bases có thể hỗ trợ proof; Raw không resolve dimension hoặc chọn current/earliest/time proxy |
| B4 valid U / integrity I | Giữ source population; source-fidelity/consistency gates không được lẫn với historical lookup U. Core/mart status không được suy từ transport success |
| B5 Tiered Certification | RawPublished và Certified KPI/view tách biệt; numerical gates chưa duyệt, không label Certified |
| B6 hybrid/forward retention | Append-only capture/history origin, full reload giữ accepted forward evidence; source original full snapshot không đủ recreate lost observations |
| B7 correction/rekey/restatement | Immutable old/new captures + source/context lineage để re-resolution; không silently mutate source values/historical SKs |
| B8 delete/incarnation | Missing partial/incremental không delete; consistent full absence chỉ candidate; Raw không tự tạo incarnation, unknown identity giữ Ambiguous downstream |
| D05/B9 exact precision | SQL F1 V1 PASS nhưng fixed-width zero cases FAIL; F2 source fixtures/ordering/bounded actual periods PASS. Driver/PG/full preservation PoC NOT RUN; local math xem Stage 2, SQL evidence xem section 10; B9 physical approval pending |
| DW-01 grains/KPI/Inventory | Giữ headers và optional refs, no fan-out joins/source-derived extra facts; holdings current, không daily balance; no revenue/COGS/payment allocation changes |

Không phát hiện architecture conflict cần sửa accepted decisions trong Stage 1; đây là compatibility review của proposal, chưa phải final design acceptance. Các missing proofs/approvals trong [Decision Register](wwi-dw-03a-decision-register.md) vẫn chặn implementation và normal publication.

## 9. Stage 2 refinement — lịch sử trước Owner logical approval

[Evidence & Approval Readiness](wwi-dw-03a-evidence-approval-readiness.md) là focused evidence/contract hiện hành cho A01–A06: extraction completeness checklist; safe config/TLS/source capability report; identity/retention/crash sequence; F1/F2 SQL source formatter candidates và detailed PoC; scope/manifest/ledger/pointer/pinning contract và 7 failure cases. Không đổi kiến trúc Stage 1 hoặc accepted DW-02.

Stage 2 từng bị TLS blocker; kết luận technical trước approval được ghi tại evidence section 10: trusted connectivity/flags/mappings/interactive permissions và SQL formatter subset đã verified; common full-extraction consistency vẫn **Unverified**, normal-publication blocker giữ nguyên. Chín local groups PASS và SQL F2 subset PASS không thay Python/PostgreSQL/end-to-end proof hoặc chọn B9 physical representation. Ở thời điểm review trước approval, reviewer chỉ đề xuất principle/PoC direction và sáu quyết định còn Proposed; current Owner approval ở section 10 dưới đây và Decision Register thay trạng thái đó. Pinned Raw membership không tự bảo đảm mutable downstream dependency consistency; missing compatible version phải hold/restart. Chưa final acceptance, runtime implementation hoặc Certified output.

## 10. Owner Logical Approval Milestone — current design boundary

Authority: Project Owner instruction **“DW-03A — Record Project Owner Logical Design Approvals”**, 2026-11-15. Ghi nhận A01/A03/A04/A06 Approved — Logical Policy; A02 Approved — Conditional Logical Policy; A05 Approved — PoC Direction Only. [Decision Register](wwi-dw-03a-decision-register.md) giữ canonical approval/limits, không phê duyệt toàn bộ technical alternatives của proposal này.

- **A01:** full source-preserving scope 9 current + 2 physical archives; source origins/physical occurrences/NULL/types/temporal evidence giữ nguyên; không silent history dedupe hoặc overlapping temporal-query ingestion. Full fidelity/completeness còn implementation gate.
- **A02:** WWI SNAPSHOT/RCSI OFF được giữ nguyên. Static window chỉ khi defensible no-write evidence toàn extraction interval; nếu không thì separately approved verified consistent copy. Không NOLOCK consistency claim hoặc tự chạy long SERIALIZABLE; thiếu proof hold normal publication. Concrete method/operational evidence chưa verified.
- **A03/A04:** immutable captures/reconciled manifests/pinned IDs và distinct run/attempt/capture/logical batch/publication; replay compatible sealed content không duplicate, new context tạo capture mới. Retention/schema/access/capacity, durable-state/recovery procedures còn pending.
- **A05:** F2 preferred PoC candidate; F1 V1 PASS nhưng 4 zero-fraction fixed-width FAIL; F2 14/14 SQL fixtures, 169 ordering comparisons, 18/18 actual period samples PASS. Chỉ SQL-side evidence; Python/PG NOT RUN, B9 Pending Physical Approval; không final PostgreSQL datatype/adapter/encoding/collation.
- **A06:** dependency-complete atomic ledger/membership/pointer và compatible downstream pins; crash/retry/concurrency/rollback/visibility proof trước runtime; Raw publication không Certified Mart publication.

[Work Plan](wwi-dw-03a-work-plan.md) sections 5–6 là explicit backlog G01–G08 và narrow B9 handoff; [Assessment](wwi-dw-03a-assessment.md) section 11 tách milestone design checks khỏi runtime tests. Logical policy đã approved không đồng nghĩa chosen extraction method, retention periods, physical schema, final B9 hoặc production readiness đã approved/verified.

DW-03A IN_PROGRESS, chưa final acceptance; DW-03B/C/DW-04 TODO, WWI-04/Phase 1 In Progress. Current task chỉ cập nhật tài liệu/QA và documentation-only commit theo Owner; không PoC execution, install, tables, database changes hoặc push.
