# WWI DW-03A — Evidence & Approval Readiness

**IN_PROGRESS — Owner Logical Approval Milestone, 2026-11-15.** Section 11 là trạng thái approval hiện hành: A01/A03/A04/A06 Approved — Logical Policy; A02 Approved — Conditional Logical Policy; A05 Approved — PoC Direction Only (F2). **Sections 1–10 giữ nguyên evidence/trạng thái lịch sử trước instruction approval này**; section 10 vẫn là SQL evidence có thể tái kiểm chứng, không có SQL/driver/PG test mới trong milestone này. Trusted TCP/source SQL subset PASS, F1 zero-fraction fixed-width FAIL; Python DBAPI/PG/full-runtime proof còn NOT RUN. B9 **Pending Physical Approval**, B1–B8/DW-02 không đổi. DW-03A IN_PROGRESS, final acceptance NOT PERFORMED; không bắt đầu DW-03B/C.

## 1. Baseline, authority và evidence levels

Branch `main`; HEAD `eeb22c224e767059581c3b10a3bb3f5d1f1cc0fb`. Stage 2 bắt đầu với **8 file Stage 1 chưa commit**: ba root files `TASKS.md`, `ROADMAP.md`, `CHANGELOG.md`, index `docs/data-models/README.md` và bốn DW-03A documents. Không staged files; không reset hoặc thay pre-existing work bằng bản HEAD. Hash snapshot đầu Stage 2 gồm 112 working files.

Đầu vào: [Stage 1 proposal](wwi-dw-03a-full-raw-design-proposal.md), [work plan](wwi-dw-03a-work-plan.md), [register](wwi-dw-03a-decision-register.md), [assessment](wwi-dw-03a-assessment.md), [source contracts](wwi-source-contracts.md), [raw requirements](../requirements/wwi-raw-layer-requirements.md), [DW-01](wwi-logical-dw-design.md), [DW-02](wwi-final-scd2-design-specification.md), [ADR index](../adr/README.md). Tài liệu này bổ sung source consistency evidence, A01 checklist, detailed temporal PoC và atomic publication contract; không nhân bản dictionary hoặc đổi accepted decisions.

**Verified historical source evidence** là khảo sát ngày 2026-11-07/14. **Verified local** chỉ kiểm tra config không lộ credential, CLI help và synthetic arithmetic/format trong Python. **Unverified current source capability** do TLS handshake thất bại. **Proposed** là mọi refinement/approval wording bên dưới; **NOT RUN** áp cho SQL formatter, actual driver, PostgreSQL và crash/concurrency/persistence PoCs chưa thực thi. Không chuyển local proof thành end-to-end proof.

## 2. A01 — Extraction completeness checklist

| Check | Source evidence / review result | Stage 2 verification boundary |
| --- | --- | --- |
| Đủ chín current sources | Source contracts và nine-row A1 matrix: Customers, Orders, OrderLines, Invoices, InvoiceLines, CustomerTransactions, StockItems, Holdings, StockItemTransactions | Đã đối chiếu tài liệu/coverage; không refresh live counts |
| Current và physical history tách populations | Customers current 663/H 51; StockItems current 227/H 444 theo [profiling](wwi-data-profiling.md), [temporal assessment](wwi-scd-temporal-assessment.md) | Verified historical, current state Unverified; riêng origin/current/H và stream manifests |
| Zero-duration giữ nguyên | Customer direct current+H 714, SYSTEM_TIME ALL 713; một zero-duration trong [C01/C02/C04 evidence](wwi-scd-temporal-evidence.md) | Không positive interval, không xóa record/audit để match counts |
| Không double count physical H với temporal query results | A01 chỉ capture direct current + direct H; temporal AS OF/ALL là diagnostic/lookup query, không third ingestion population | Logical route reviewed; runtime enforcement NOT RUN |
| Không dedupe versions theo NK/start/hash | Customer NK+ValidFrom duplicate-start group đã verified; full tuple unique chỉ ở snapshot; raw archive có repeated NK hợp lệ | Preserve multiset/multiplicity; technical capture locator không là durable source/episode identity |
| Datatype/scale/NULL traceable | [Dictionary](wwi-metadata-dictionary.md) đủ 156 current source columns, PK/FK/type/null/default/computed/period metadata; geography/blob/Unicode/decimals và scale 7 trong projection contract | Historical metadata verified; current metadata và adapters chưa verified. Không dùng analytical field subset thay full approved Raw projection |
| Header/line/optional FK không làm mất rows | [relationships](wwi-source-relationships.md), [validation I01–I12](../requirements/wwi-source-validation-matrix.md); Orders không cần invoice, payment optional InvoiceID | Explicit full source projection, không inner join/filter/drop; raw completeness khác historical dimension resolution |
| Sales-first dependency-complete scope | Candidate `SALES_FULL_V1`: Customers current/H, StockItems current/H và Orders/OrderLines/Invoices/InvoiceLines/CustomerTransactions = **7 current + 2 H streams** | Scope/version phải được Owner duyệt trước capture. Hai Inventory transaction/state tables được design nhưng không bắt Sales chờ Inventory analytics |
| Reference dependencies ngoài scope | TransactionTypes/PackageTypes/customer category labels và Purchasing refs không tự được ingestion approval | Copy raw IDs, ghi separately verified/unverified reference checks; không claim đã load/validate mọi reference. Future published scope phải nêu dependencies/check applicability |

Raw current PK uniqueness được kiểm riêng với history occurrence multiplicity. Không cần tạo artificial occurrence IDs có nghĩa lịch sử để vượt thiếu source key; ambiguity được giữ cho downstream. A01 logical principle có thể được Owner review có điều kiện, nhưng exact preservation/current permission tests vẫn chặn implementation và publication.

## 3. A02 — Source Consistency Evidence Report

### 3.1 Connection/config inspection trước metadata attempt

- Search trong workspace, gồm ignored config names và loại `.git`: chỉ tìm `.env.example`. Không tìm active connection file trong phạm vi repo; không công bố nội dung credential/connection string.
- Chỉ kiểm presence và allowlisted boolean security flags: `Encrypt`, `TrustServerCertificate`, `HostNameInCertificate`; example không có các flags đó. Không có process environment names khớp nhóm SQLCMD/SQLSERVER/MSSQL/DB_/DATABASE_/ODBC/PG connection được kiểm. Không dump environment values.
- `sqlcmd -?` xác nhận installed ODBC CLI version **17.0.1000.7**, hỗ trợ `-N[s|m|o]`; đây là **CLI version**, không live database engine version. Không connector database chuyên dụng nào được dùng.
- Không tìm được valid trusted connection profile trong phạm vi đã inspect; không kết luận mọi cấu hình trên máy đều không tồn tại. Không dò credential store, đổi trust store hoặc chọn hostname override để né validation.

### 3.2 Actual metadata probe

Chạy cùng endpoint/database đã ghi trong project, integrated authentication, encryption **mandatory**, không `-C` hoặc `TrustServerCertificate=true`:

```powershell
sqlcmd -S '.\SQLEXPRESS' -d WideWorldImporters -E -Nm -l 5 -t 15 -b -W -s '|' -Q $metadataStageTwo
```

`$metadataStageTwo` chỉ gồm SELECT: (1) DB_NAME/ProductVersion/Edition/snapshot_isolation_state_desc/is_read_committed_snapshot_on/is_read_only/state_desc từ sys.databases; (2) temporal_type_desc/current→history schema/table mappings và HAS_PERMS_BY_NAME SELECT cho 9 current + 2 H; (3) sys.columns datetime2 datatype/precision/scale/is_nullable/is_hidden/generated_always_type_desc. Không DML/DDL hoặc config statement. Quyền interactive nếu sau này verify được cũng không chứng minh service-account permissions.

**Observed:** `Microsoft ODBC Driver 18 for SQL Server : SSL Provider: The certificate chain was issued by an authority that is not trusted`; tiếp theo `Client unable to establish connection`; native **`metadata_probe_exit=1`**. Không có row kết quả, không có successful metadata SELECT. PowerShell wrapper in exit code rồi kết thúc không phải bằng chứng SQL success.

TLS chain failure không xác định chứng chỉ tự ký hay CA cụ thể, không chứng minh account thiếu SELECT, SNAPSHOT OFF hoặc source unavailable về mặt SQL engine. Không giảm encryption, không dùng certificate bypass, không thay server/client trust configuration. [Microsoft sqlcmd](https://learn.microsoft.com/en-us/sql/tools/sqlcmd/sqlcmd-utility?view=sql-server-ver17) mô tả các encryption/certificate options; task chỉ sử dụng validation path nêu trên.

| Capability | Evidence hiện có | Current conclusion |
| --- | --- | --- |
| Database name/version/edition | Inventory cũ ghi WideWorldImporters, engine 17.0.1000.7 Express; Stage 2 handshake không trả row | Verified historical only; current Unverified |
| snapshot_isolation_state_desc | Không có successful current query | **UNVERIFIED — connection limitation**, không enabled/disabled assertion |
| is_read_committed_snapshot_on | Không có current result | Unverified; RCSI không thay transaction SNAPSHOT |
| Temporal configuration/history mappings | Historical Customers→Customers_Archive, StockItems→StockItems_Archive | Verified historical; current mapping query NOT EXECUTED successfully |
| SELECT permissions current/H | HAS_PERMS query không có result | Unverified cho connection hiện tại/service account |
| Database read-only flag | is_read_only query không có result | Unverified; project read-only policy khác database read-only state |
| Writer activity/static window | Không có external writer-control evidence trong extraction interval | Unverified; old timestamps/repeated counts không phải no-write proof |

### 3.3 Decision classification và alternatives

| State khi có evidence | Hành vi đề xuất |
| --- | --- |
| ON verified | Có thể review C1 single-session read-only SNAPSHOT cho required scope; vẫn cần session/permission/resource và full-read proof. ON flag chưa phải executed extraction proof |
| OFF verified | C1 không khả dụng ở cấu hình đó; không tự ALTER. Review evidence-backed static window, externally provided consistent copy hoặc operationally approved SERIALIZABLE |
| Transition/non-ready verified | Không coi như ON-ready; phải ghi exact state và kiểm lại hợp lệ trước extraction |
| **Unverified do connection/permission limitation — trạng thái hiện tại** | Giữ capability Unverified và **normal-publication blocker**. Không chọn fallback theo giả định flags OFF |

Static window cần source-owner evidence toàn required scope không có writer trong **toàn extraction interval**, gồm background processes và current/H changes; read-only client, counts/hash trước–sau hoặc historical max date không đủ. Consistent copy cần verified restore/snapshot provenance, source identity và task tạo/cấp copy riêng; không tạo ở Stage 2, không assumption edition support. SERIALIZABLE cần review blocking/resource impact, không mặc định sử dụng. RCSI/per-table/windowed captures không nâng thành common transactional snapshot; qualified diagnostic access chỉ theo explicit Owner approval, normal publication vẫn hold. Xem [Microsoft isolation levels](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-transaction-isolation-level-transact-sql?view=sql-server-ver17).

**Safest next action:** Owner/DBA cung cấp trusted endpoint/certificate-chain/client profile hợp lệ và read-only access, sau đó chạy lại SELECT metadata. Tác nhân không tự cài certificate, đổi trust settings hoặc disable validation. Chưa có source consistency approach nào được verified cho execution hiện tại.

## 4. A03/A04 — Identity, lifecycle, retention và crash/retry refinement

Kiến trúc được reviewer khuyến nghị giữ nguyên: Immutable Raw Captures → Reconciliation → Published Manifest → Downstream pinned publication. **Logical principle vẫn Proposed** cho đến Owner phê duyệt.

| Identity / conceptual key | Lifecycle / invariant đề xuất |
| --- | --- |
| Pipeline run_id | Invocation/orchestration attempt container; run mới không tự tạo source state mới; không làm source snapshot identity |
| Execution attempt_id + logical batch link | Failed/retry attempts đều retained audit; một batch có nhiều attempts nhưng chỉ accepted sealed content được chọn vào membership |
| capture_id + source_instance/provenance + consistency evidence | Nhận diện một source observation context. Re-extract sau reconnect/new state tạo capture mới; snapshot token nguồn chỉ ghi nếu thật sự có, không bịa từ wall clock |
| logical_batch_id = capture + source object + current/H population + projection version | Required logical population của capture, có chunk/range/seal proof; không reuse batch identity cho changed observation |
| raw-record/chunk locator | Chỉ unique trong retained sealed content; source PK và archive occurrences giữ riêng. Ordinal/digest không trở thành analytical episode/SK hoặc dedupe key lịch sử |
| manifest_id + immutable content revision | Membership/coverage/versions/content bindings đã seal không sửa âm thầm; changed membership tạo revision/candidate mới |
| publication_id + scope_id/scope_version + predecessor revision | Durable accepted publication event riêng source capture/run; retries của cùng publication request không apply lần hai |

Failed capture không phục vụ published readers; đủ sealed content chỉ replay nếu content/batch/contract/context proof tương thích. Capture mới có thể supersede candidate cũ nhưng không xóa evidence của attempts hoặc publication cũ. Full reload không truncate source history, accepted forward observations, registry evidence hoặc incompatible-publication audit. Logical dedupe chỉ chống repeated delivery/attempt của cùng sealed content; identical physical archive payload vẫn giữ multiplicity.

### Retention alternatives — số ngày và physical mechanism chưa duyệt

| Alternative | Trade-off / bảo vệ evidence |
| --- | --- |
| Giữ mọi captures vô hạn | Dễ audit nhưng growth/PII/cost chưa kiểm soát; không default production |
| Short failed/retry retention + long published/lineage retention | Giảm bytes; chỉ purge sau dependency proof, không mất accepted evidence, forward observations hoặc unresolved recovery request |
| Reference-aware tiers, archived payload + durable manifest/provenance | Khuyến nghị review: pinned/registry/forward/active-recovery evidence không được purge, cold-tier/codec restore phải verified; không tự thêm storage technology hoặc chọn retention periods |

Owner cần duyệt access roles, retention classes/periods, recovery limits và evidence-required set trước implementation. Published/pinned/superseded manifests hoặc source forward observations được tham chiếu phải có recoverable payload/codec/provenance, không chỉ digest. Policy change/purge request là thao tác cần approval sau này, không thực hiện trong Stage 2.

### Illustrative crash/retry — synthetic IDs, không runtime evidence

1. Run R1 tạo C1/B1/T1; chunks đã commit nhưng extraction seal của required scope chưa đủ: C1 vẫn candidate, không normal publish.
2. Nếu SQL source context mất thì abandon C1; R2 tạo C2, không ghép source reads C2 vào C1 để giả cùng snapshot.
3. Nếu C1 đã có durable full seal và exact content proof trước crash thì T2 replay/reconcile retained C1, không re-read source mới rồi overwrite C1.
4. Validation tạo attestation V1 cho immutable M1. Publication request Q1 dự kiến scope revision r0→r1; target ledger+pointer commit cùng transaction concept.
5. Client mất ACK sau target commit: retry Q1 đọc durable publication P1. Same request/content → trả P1, không append duplicate hoặc update pointer lần hai.
6. Nếu active scope đã ở P2 mới hơn thì replay Q1 không đẩy pointer về P1. Rollback hợp lệ là controlled publication revision mới trỏ compatible prior manifest, giữ lineage/reconciliation, không ghi đè lịch sử.

## 5. A05/B9 — Source formatter candidates và detailed PoC

Canonical exact text là **preferred PoC direction**, chưa physical approval. Target format đề xuất: 27 ASCII code points `YYYY-MM-DDTHH:mm:ss.fffffff`, NULL riêng; source system-time, observation-time và analytical validity khác nhau. datetime2 không timezone-aware; không append Z hoặc tự UTC/business-effective conversion cho ordinary values. Native microsecond projection chỉ derived, không thay authoritative exact value.

### 5.1 Source-side candidate queries — NOT RUN

Candidate F1 dùng `CONVERT(varchar(27), value, 126)` và kiểm actual length/digits/typed equality. Không mặc định output luôn fixed seven digits; Microsoft có formatting notes về fractional parts/zeros. Candidate F2 assemble date/time và bảy digits bằng integer source expression để review; vẫn cần execution proof, không tự coi accepted formatter.

```sql
SELECT v.source_value,
       CONVERT(varchar(27), v.source_value, 126) AS style126_candidate,
       CASE WHEN v.source_value IS NULL THEN CAST(NULL AS varchar(27))
            ELSE CONVERT(char(19), v.source_value, 126) + '.' +
                 RIGHT('0000000' + CONVERT(varchar(7),
                       DATEPART(NANOSECOND, v.source_value) / 100), 7)
       END AS explicit_7digits_candidate
FROM (VALUES
    (CAST(N'2026-11-15T12:34:56.1234567' AS datetime2(7))),
    (CAST(N'2026-11-15T12:34:56.1234568' AS datetime2(7))),
    (CAST(N'2026-11-15T12:34:56.0000000' AS datetime2(7))),
    (CAST(N'0001-01-01T00:00:00.0000000' AS datetime2(7))),
    (CAST(N'9999-12-31T23:59:59.9999999' AS datetime2(7))),
    (CAST(NULL AS datetime2(7)))
) AS v(source_value);
```

Đây là SELECT synthetic constants để thử sau khi có trusted connection; không tạo table/variable/schema hoặc chạy ở Stage 2. SQL typed source value là control, không dùng driver-returned Python datetime để dựng lại exact text. Kiểm formatter tại SQL Server trước transfer: canonical length 27/digits 7, `TRY_CONVERT(datetime2(7), candidate,126)` bằng typed source value, NULL và every boundary; source datatype/scale lấy sys.columns, result type metadata được record. Không pad digit đã mất trong client. F2 dựa trên DATEPART nanosecond trả integer fractional components; divide 100 lấy 100 ns units, không float. [CAST/CONVERT](https://learn.microsoft.com/en-us/sql/t-sql/functions/cast-and-convert-transact-sql?view=sql-server-ver17), [DATEPART](https://learn.microsoft.com/en-us/sql/t-sql/functions/datepart-transact-sql?view=sql-server-ver17) là cơ sở phân tích, không engine execution evidence.

Không dùng `DATEDIFF_BIG(NANOSECOND, year0001, value)` trực tiếp cho toàn date range: nanoseconds có thể vượt signed bigint dù 100 ns ticks còn nằm trong range. Local ticks dùng integer Gregorian days/seconds/fraction: `(ordinal−1)×864000000000 + seconds_of_day×10000000 + fractional_7digits`; không `float total_seconds`, không mặc định physical epoch/schema từ phép minh họa.

### 5.2 Local synthetic checks — đã chạy, phạm vi hẹp

Lệnh `python -c $localTemporalChecks`, Python **3.12.10**, exit **0**; chín groups PASS, 0 failed. Fixtures trong memory, không source/driver/PostgreSQL, không script/pipeline artifact.

| ID | Check / expected | Observed result | Limit |
| --- | --- | --- | --- |
| A05-L01 | V1=`2026-11-15T12:34:56.1234567`; exact ticks/reconstruction | 639303428961234567, reconstructed V1, PASS | Local arithmetic/codec only |
| A05-L02 | V2 `.1234568` giữ distinct | Difference=1 tick và exact reconstruction, PASS | Không driver preservation proof |
| A05-L03 | Minimum/sentinel/leap/calendar boundaries | 10 valid fixtures round-trip; min=0, max=3155378975999999999, PASS | Không SQL date parser proof |
| A05-L04 | Defined ASCII byte order bằng civil tick order trên same basis | Sorting 10 fixtures bằng nhau, PASS | Không PostgreSQL COLLATE test |
| A05-L05 | Zero-duration half-open không match; same NK/start không unique occurrence | No positive match; 2 synthetic occurrences nhưng 1 NK/start key, PASS | Counterexample logic, không Raw implementation test |
| A05-L06 | Local None ↔ None | PASS, không string NULL | Không database NULL binding proof |
| A05-L07 | Invalid precision/date/time/Unicode digit/TZ suffix/overflow | 11 invalid strings + value trên sentinel rejected, PASS | Không source converter behavior proof |
| A05-L08 | Fixed-width ASCII/UTF-8 exact encoding | 27 bytes/value và exact local encode/decode, PASS | Không arbitrary NVARCHAR/driver transport proof |
| A05-L09 | Negative control: truncate/round microseconds làm mất precision | V1/V2 collide; sentinel rounding vượt source max detected, PASS | Expected lossy arithmetic, không actual driver/PG rounding result |

Ten valid fixtures: year 0001 zero/100 ns; `1900-02-28T23:59:59.9999999`; `2000-02-29T00:00:00.0000000`; 2026-11-15 midnight, 12:34:56 whole-second, V1, V2; year 9999 final `.9999998` và `.9999999`. Invalid cases gồm 6/8 fractional digits, Z/+07:00 suffix, invalid 1900 leap day/November 31, year 0000/10000, hour 24, non-ASCII digit và string NULL. None là carrier riêng. Các fixtures không phải WWI records.

### 5.3 Detailed PoC execution boundaries — không chọn physical B9

| Case / proof cần có | Chạy ở đâu / authority | Expected acceptance evidence | Current status |
| --- | --- | --- | --- |
| Source F1/F2 exact export + source type/scale/nullability | Trusted SQL connection, SELECT-only constants/catalog; không cần source writes | Actual exact texts, 27 length, 7 digits, min/max/zero/tails, typed reverse equality, SQL metadata | NOT RUN — TLS blocker |
| Real Python connector text binding/return | Approved installed driver + trusted source connection, no automatic install/selection | Driver/version/settings và text return type; no datetime coercion before preservation; every digit/NULL retained | NOT RUN |
| PostgreSQL text parameter echo + equality/order | Approved target connection, SELECT-only constants/parameters; không CREATE SCHEMA/table | Raw text returned byte-for-byte, octet/character lengths và NULL; explicit comparison expression under candidate `COLLATE "C"` | NOT RUN |
| Persistent PG storage and retrieve | Dedicated approved sandbox nếu cần table/write/loader test | Written/read exact text và metadata, commit/rollback and byte equality | NOT RUN — no schema/write permission task này |
| Range/predicate/order | Local math đã kiểm một phần; actual SQL/PG expressions trên synthetic fixtures sau trusted access | Same-basis exact `<`, `<=`, half-open bounds; adjacent 100 ns khác, zero-duration không match; explicit collation/expression | Local subset PASS; engine tests NOT RUN |
| Duplicate boundaries/occurrence multiplicity | Local counterexample đã có; persistence/source replay trong dedicated sandbox | Same NK/from không bị unique/dedup collapse; legit duplicate rows retained, source origin/context traceable | Local example PASS; pipeline NOT RUN |
| Collision/precision-loss detection | Source/driver/PG pipeline hoặc sandbox | V1/V2 không collapse ở exact path; lossy projection bị phát hiện và không used as authority; hash equality không override content checks | Local negative arithmetic PASS; end-to-end NOT RUN |
| Unicode/payload encoding/source scale drift | Approved adapters, synthetic sandbox và metadata read | Exact codepoints/NULL/bytes theo chosen protocol; source type/scale giữ provenance; unsupported conversion hold, no silent replacement | NOT RUN |
| Crash/retry/concurrency/full reload/forward overlap | Dedicated sandbox/task riêng cho failure/write fixtures | Manifest/atomicity/idempotency/restoration evidence theo section 6; original WWI luôn read-only | NOT RUN |

Candidate `COLLATE "C"` được chọn để **thử** byte ordering theo [PostgreSQL collation docs](https://www.postgresql.org/docs/18/collation.html), không đổi database default hoặc tự chốt column/index collation. Local ASCII ordering không chứng minh server/database encoding, expression/index collation hoặc driver equality. System-time semantics được giữ bằng history_basis/provenance; representation equality không tự cho analytical/business-time equivalence.

Full PoC **chưa executed**. B9 vẫn Pending; chín local groups không cho quyền tạo PostgreSQL schema, cài driver hoặc DML WWI/sandbox. P1 text là candidate hướng PoC; datatype/index/storage/codec/driver/physical verification procedure phải được Owner duyệt đúng scope sau evidence.

## 6. A06 — Proposed Atomic Publication Contract

### 6.1 Scope/manifest/pointer definitions

| Concept | Contract proposal |
| --- | --- |
| scope_id + scope_contract_version | Định danh required source populations/dependencies, projection/serialization versions và coverage expectations đã declared trước extraction. Membership changes tạo version/review mới, không xóa failed table khỏi scope để pass |
| Scope membership | List required current/H streams, capture/batch/accepted-attempt/chunk bindings, exact coverage and source-consistency evidence; external checks áp dụng hay chưa verified được ghi rõ |
| Candidate manifest | Draft/candidate revisions không phục vụ consumers; khi seal, freeze membership/content bindings dưới manifest_id/revision. Changed bytes/membership tạo candidate revision mới |
| Validated manifest | Same immutable sealed content + immutable validation attestation/check/gate versions và eligibility decision; không sửa payload để validation pass |
| Published manifest | Durable publication event publication_id/request_id gắn validated manifest, scope/version, predecessor revision và publish audit. RawPublished chưa Certified DW |
| Active pointer | One accepted publication per scope/version tại revision hiện hành; advance phải check expected predecessor/monotonic revision. Không tự dùng wall-clock mới nhất làm concurrency control |
| Failure/rollback states | Candidate PARTIAL/FAILED/HOLD/ABANDONED không normal-visible; superseded/published revisions retained. Rollback là controlled new publication revision trỏ compatible prior content, không overwrite old audit |
| Consumer pin | Resolve publication ID một lần cho run; mọi table/model trong scope đọc đúng manifest membership. Pin required reference/contract/policy versions và compatible downstream dependency generations nếu được dùng |

### 6.2 Atomic visibility và success authority

Đề xuất publish **ledger event + membership visibility + active pointer** cùng một target PostgreSQL control transaction, sau khi immutable candidate và validation đã durable. Đây là requirement để review, không DDL/implemented transaction. Readers không có direct access phục vụ reports từ unvalidated candidates; access/physical enforcement cần approval và test. SQL source capture transaction, PostgreSQL chunk writes và publication transaction là các boundaries riêng, không có assumed distributed commit.

Same request_id + same manifest/content → idempotent accepted result; same request với different content → contract conflict/HOLD, không overwrite. Retry đọc durable target ledger/pointer/membership, không coi external orchestrator success flag là authority. Pointer thay bằng compare-precondition/serialization mechanism chưa chọn; concurrent publish loser không được silently overwrite newer publication. Checkpoint/final orchestration state chỉ phản ánh durable decision sau read-back, không tạo publication truth thứ hai.

Consumer pinning Raw manifest chưa tự pin mutable Warehouse dimensions/registry hoặc external reference labels. Input dependency bundle phải ghi required versions/generations có thể phục hồi. Nếu dependency thay trong lúc consumer chạy: dùng immutable pinned-compatible version; nếu không giữ/pin được thì hold/restart consumer thay vì query latest hoặc claim cross-layer atomicity. Cách hiện thực propagation/recovery thuộc DW-03C sau này, không bắt đầu trong Stage 2.

### 6.3 Seven required failure scenarios

| Scenario | Expected visibility / recovery proposal | Evidence trước runtime |
| --- | --- | --- |
| 1. Một source table extraction fail | Required scope candidate PARTIAL/HOLD; previous publication còn visible. Không exclude failed table hậu kiểm; independent scope chỉ publish nếu đã declared/validated độc lập | Required-stream manifests/seals, same-context proof, prior pointer |
| 2. Raw load complete nhưng reconciliation fail | Loaded candidate retained nhưng không eligible/published; investigate type/count/context/source anomaly, không sửa status thành success | Per-check diffs và retained original evidence; revalidation trên same sealed content |
| 3. Reconciliation pass nhưng publication transaction fail | Validation không đồng nghĩa publication. Nếu rollback chắc chắn thì previous pointer; nếu commit outcome unknown thì read ledger/membership/pointer trước retry | Durable target transaction outcome, request/manifest binding, no partial visible update |
| 4. Publication success, orchestrator crash trước success record | Durable P1 là authority; retry acknowledge existing P1, không republish/add rows | Read-back same request_id/manifest/content và committed publication event |
| 5. Retry sau previous success | Same logical request reuse accepted result; nếu newer P2 đã active, không pointer regression về P1. Intentional rollback cần new controlled revision | Monotonic scope revision/predecessor checks, prior success audit |
| 6. Full capture overlap forward observations | Preserve both evidence tracks; candidate publish HOLD cho tới compatible generation/coverage reconciliation. Không truncate forward hoặc snapshot overwrite observations mới | Source/observation/manifest lineage và verified bridge; exact incremental ordering/cutoff policy còn DW-03B/C, không tự chọn watermark |
| 7. Analytical dependency đổi khi consumer chạy | Consumer tiếp tục pinned-compatible immutable dependency set; nếu thiếu retained version/proof thì fail/hold/restart, không mix new dimension/current reference giữa run | Dependency bundle versions, publication pin, compatible registry/dimension refs; chưa có runtime proof |

### 6.4 Five independent readiness axes

1. **Source capture consistency:** proof common transactional/static context theo approved A02, không suy từ target atomicity.
2. **Raw completeness:** required population/fields/seals/rows và legitimate occurrences đủ, không suy từ job exit code.
3. **Reconciliation eligibility:** checks/fidelity/context/disposition theo approved gates, không tự publication.
4. **Atomic publication:** coherent durable manifest/ledger/pointer và consumer visibility, không tự certified warehouse.
5. **Downstream certification:** B5 KPI/view dependency/row/value gates và approved numerical thresholds; Raw success không thay thế.

Hiện trục 1 chưa verified; 2–4 chỉ documented proposals và tests NOT RUN; 5 chưa có runtime/certification. Không có normal publication hoặc Certified output được xác nhận.

## 7. Consolidated recommendations, approvals và acceptance readiness

[Decision Register](wwi-dw-03a-decision-register.md) ghi từng A01–A06 với recommendations/evidence available/missing/risks/alternatives/trade-offs/impact/proposed approval wording và exact pre-implementation conditions. Reviewer recommendation: A01/A03/A04/A06 logical principle có điều kiện; A02 conditional/source verification; A05 PoC direction only. **Mọi item vẫn Proposed.** Không ghi reviewer là approval authority thay Owner.

| Readiness dimension | Stage 2 result | Gate còn thiếu |
| --- | --- | --- |
| Design documented | Có Stage 1 + focused Stage 2 contract/checklists/PoC | Owner review scope/wording, chưa final acceptance |
| Logical consistency | Không phát hiện conflict B1–B8/DW-01 qua targeted review; published state/axes/retry boundaries rõ hơn | Physical enforcement/concurrency/restore tests chưa chạy |
| Source capability verified | **Chưa — Unverified** | Trusted TLS/access; flags/mappings/permissions/static or snapshot evidence |
| PoC plan complete | Đủ cases source/driver/PG/collation/range/multiplicity/failure để review | Owner direction và connections/sandbox approval phù hợp |
| PoC executed | **Partial local only:** 9 groups PASS; full SQL/driver/PG PoC NOT RUN | Source formatter/actual transport/target storage/predicates tests |
| Runtime implementation | **Not Started** | Task/approval riêng; không implement trong Stage 2 |
| Owner approval A01–A06 | **Chưa có** | Explicit logical/PoC-direction approvals; physical/runtime scope riêng |
| DW-03A final approval/closure readiness | **Chưa đủ, giữ IN_PROGRESS** | Source capability/precision proof và Owner decisions chưa đủ; không đóng bằng documented plan |

Safest sequence đề xuất: Owner review conditional logical wording → Owner/DBA chuẩn bị trusted read-only connectivity → read-only metadata/formatter verification → approved connector/target read-only PoC hoặc dedicated sandbox khi cần writes → review physical B9/publication enforcement/retention details. Đây là next-action plan, không authorization hoặc bắt đầu DW-03B/C.

## 8. Actual validation và Git boundary

Actual outputs được kiểm tra sau khi hoàn thiện Stage 2 documents:

| Command / check | Observed output | Result / boundary |
| --- | --- | --- |
| `git status --short`, branch/log đầu Stage 2 | main, HEAD eeb22c224e767059581c3b10a3bb3f5d1f1cc0fb; 8 Stage 1 dirty files, no staged | PASS — baseline/pre-existing work recorded |
| `python -c $safeConfigInspection` | Chỉ .env.example trong matching workspace configs; TLS flags absent trong example; relevant process env names empty; values không công bố | PASS — scoped inspection, không trusted connection proof |
| `sqlcmd -?` | Installed CLI 17.0.1000.7, -N[s/m/o] và -C có trong help | PASS — CLI capability only |
| `sqlcmd -E -Nm ... -Q $metadataStageTwo` | Certificate-chain untrusted; client unable to establish connection; native metadata_probe_exit=1, no rows | FAILED — connectivity; source isolation Unverified |
| `python -c $localTemporalChecks` | Python 3.12.10; exit 0; 9 groups PASS, 0 failed, 10 valid/11 invalid fixtures + overflow case | PASS — local synthetic checks only |
| `python -c $stageTwoQa` links/anchors | 576 local Markdown links, 2 fragments; 0 broken targets/anchors | PASS — document QA |
| Cùng QA — scope/hash/security/format | 6 Stage 2 changed files; total Git dirty 9 including Stage 1; 107 protected initial files unchanged; 0 scope/secret-pattern/binary/format/table/write-statement errors | PASS — accepted materials và 3 Stage 1 root changes preserved |
| Cùng QA — decisions/coverage/status | 6 decisions Proposed, 6 draft approval statements, 9 current/2 H streams, 9 local groups documented, 7 failure scenarios, 21 existing tests NOT RUN; task statuses unchanged | PASS — proposal coverage/status, không Owner approval |
| `git diff --check` và actual diff/content review | Exit 0; tracked diff chỉ existing Stage 1 management/index scope; new documents và Stage 2 revisions đã review theo initial hashes/content | PASS — no executable artifacts |
| HEAD/index checks | HEAD giữ baseline; staged files empty | PASS — no commit/push |

Không có successful live SELECT/PG test, DML/DDL/config/trust change hoặc dependency install. Existing CD-T01–21 và A-P01–06 full pipeline PoCs vẫn NOT RUN; chỉ A05-L01–09 local subset đã thực thi. Pattern scan không bảo đảm phát hiện mọi dạng secret; các flags/value inspection được giới hạn để tránh lộ credentials. Git LF→CRLF notices không phải diff-check failures. QA PASS không giải quyết source/TLS/physical-proof blockers hoặc final design acceptance.

Phạm vi sửa Stage 2: bốn DW-03A documents, focused report này và `docs/data-models/README.md`. Ba root management changes của Stage 1 được giữ nguyên byte hash; accepted DW-02/ADR/source/scope/KPI artifacts giữ nguyên. Không stage/commit/push, HEAD giữ eeb22c2…; DW-03A IN_PROGRESS, B/C/DW-04 TODO, WWI-04/Phase 1 In Progress. Không tự final design acceptance hoặc phase closure.

## 9. Stage 3 — Targeted TLS/driver evidence và connection stop condition

Ngày 2026-11-15. Branch main, HEAD eeb22c224e767059581c3b10a3bb3f5d1f1cc0fb; đầu Stage 3 có 9 files dirty của Stage 1/2, không staged. Snapshot 113 working files để bảo toàn công việc trước. Stage 3 chỉ cập nhật tài liệu này; không thêm architecture proposal/code/schema hoặc sửa các file khác.

### 9.1 Diagnostic findings và interpretation

- Verified installed **sqlcmd ODBC variant 17.0.1000.7 NT**, path dưới Client SDK/ODBC/180/Tools/Binn. Installed 64-bit SQL Server ODBC drivers: **17.10.6.1**, **18.6.2.1**, và legacy SQL Server driver file version 10.0.26100.9974. Không dùng driver cũ để né encryption/validation mặc định.
- Registry instance map xác nhận `SQLEXPRESS → MSSQL17.SQLEXPRESS`. Read-only `SuperSocketNetLib` inspection trả **Certificate thumbprint rỗng**, **ForceEncryption=0**, ForceStrictEncryption không có value. Đây là configured values, không chứng minh certificate server đang present hoặc độ mã hóa của một live connection; client policy vẫn mandatory.
- `Cert:\LocalMachine\My` có một certificate công khai candidate **Subject=Issuer=CN=localhost**, DNS SAN `localhost`, Server Authentication EKU, validity 2026-09-21 đến 2031-09-21. Exact certificate không có trong LocalMachine Root hoặc CurrentUser Root được đọc. **Chỉ xác minh public metadata và root membership**, không truy private key, export certificate, build/download chain hoặc đổi certificate store.
- Empty explicit binding **không loại trừ automatic certificate selection**. Không xác nhận candidate localhost là certificate SQL Server thực sự sử dụng. Endpoint hiện hành là local alias `.\SQLEXPRESS`; presented identity/expected hostname matching vẫn **Unverified**, không tự đổi hostname hoặc override để thử đoán.
- Startup Parameters key đọc được nhưng không tìm SQLArg values để lấy error-log path. Read-only Setup-based Log/ERRORLOG path check gặp **Access is denied**; không đọc được startup certificate-loading evidence. Không escalate, đổi ACL, hoặc kết luận fallback/self-generated certificate đã được verified.
- Workspace config inspection vẫn chỉ thấy `.env.example`; related process connection environment names rỗng. CurrentUser/LocalMachine SQL Server DSN indexes đều **0 SQL Server DSNs**; không matching project profile. Phạm vi này không chứng minh toàn bộ cấu hình/secret stores trên máy không tồn tại; không dò credential store hoặc công bố secret values.
- Python environment được dùng cho checks **không có pyodbc, pymssql, psycopg, psycopg2** theo `importlib.util.find_spec`; không import kết nối hoặc cài package. Không có approved active PostgreSQL connection trong project/process profile đã inspect; không đoán default host/port/password.

**Trusted source connectivity NOT ESTABLISHED / BLOCKED.** Stage 3 không lặp lại SQL connection bằng cấu hình đã lỗi tại Stage 2. Latest actual encrypted probe vẫn là Stage 2 native exit 1/certificate-chain-untrusted; không có failed SQL probe mới được bịa. Stage 3 dừng connection-dependent testing sau diagnosis. Database name/version/updateability/session identity/isolation/SELECT permissions/temporal mappings hiện tại tiếp tục **Unverified**; historical metadata không bị đổi thành current verification.

### 9.2 Test/evidence ledger — actual commands và guarded NOT RUN

Môi trường local: Windows/PowerShell 5.1.26100.9818, existing Python 3.12 environment; không database config hoặc auth changes. Registry/certificate chỉ đọc public/config metadata; command summaries dưới đây không chứa credential/private key.

| Test ID | Purpose | Environment | Actual command/query | Expected result | Actual result | Status | Implication |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S3-01 | Identify CLI/SQL drivers | Local executable + HKLM ODBC | `Get-Command sqlcmd`; `sqlcmd -?`; Get-ItemProperty ODBCINST.INI và DLL VersionInfo | Record installed variant/version | ODBC sqlcmd 17.0.1000.7; SQL ODBC 17.10.6.1/18.6.2.1 và legacy driver | PASS | Tool availability, không source connection proof |
| S3-02 | Non-secret project/config discovery | Workspace/process env/HKCU-HKLM DSN | `rg --files --hidden --no-ignore` config patterns; inspect env names; Get-ItemProperty ODBC.INI indexes/allowlisted fields | Find trusted project profile nếu có, không lộ values | .env.example only, related env names empty, 0 SQL Server DSNs | PASS — inspection | Không tìm valid trusted profile trong inspected scope; A02 remains gated |
| S3-03 | Read configured TLS binding | HKLM SQL instance registry | Get-ItemProperty Instance Names/SQL và SuperSocketNetLib | Obtain binding/encryption config | Instance MSSQL17.SQLEXPRESS; Certificate empty, ForceEncryption 0 | PASS — observation | Không infer actual presented certificate, SNAPSHOT hoặc live encryption |
| S3-04 | Inspect public cert/trust membership | LocalMachine My, machine/user Root | Get-ChildItem certificate providers, public Subject/Issuer/DNS/EKU/dates và thumbprint membership comparisons | Public metadata/trust membership without private-key/store changes | CN/SAN localhost candidate; self-issued; exact cert absent in inspected Roots | PASS — observation | Candidate chưa verified là server cert hoặc valid trusted route |
| S3-05 | Server-name/certificate identity match | Existing endpoint + public metadata | Compare available config metadata; no TLS/hostname override probe | Verify identity presented by SQL endpoint | Actual presented certificate unknown; local alias cannot establish verified DNS match | BLOCKED | DBA phải xác nhận loaded cert và approved DNS endpoint |
| S3-06 | Obtain actual SQL startup cert evidence | Parameters/Setup registry + Log/ERRORLOG | Get-Item/Get-ItemProperty config; Test-Path/Get-Content on Setup-derived error log | Read public certificate-loading line | SQLArg values không available; log path check Access is denied, no cert log read | BLOCKED | Không claim self-generated/fallback cert; cần DBA cung cấp sanitized evidence |
| S3-07 | Establish trusted source connection | SQL Server source | Không thực thi connection attempt mới: failed Stage 2 config không có remediation/trusted alternative | Trusted mandatory-encryption validation before SELECT | No approved trusted route established; no -C/TrustServerCertificate bypass | BLOCKED | Dừng connection-dependent tests; không authentication/config change |
| S3-08 | Current DB/isolation/perms/temporal mappings | Trusted source session required | NOT RUN; SELECT metadata/session identity/HAS_PERMS/history mapping plan có sẵn | Current DB/version/updateability, identity, SNAPSHOT/RCSI, 9 current + 2 H rights/mappings | No current SQL rows; all capabilities Unverified | BLOCKED | A02 không được approve normal publication hoặc assume flags ON/OFF |
| S3-09 | Exact SQL source formatter | Trusted source session required | NOT RUN; F1/F2 SELECT-only synthetic/actual temporal columns trong section 5 | V1 text 2026-11-15T12:34:56.1234567, len 27, ns 123456700; boundaries/NULL/order | Không có SQL formatter result; no source rows read/changed | NOT RUN | B9 source conversion proof thiếu; Stage 2 local PASS không thay thế |
| S3-10 | Python connector availability | Existing Python environment | `importlib.util.find_spec` cho pyodbc/pymssql/psycopg/psycopg2; metadata version nếu available | Record dependency availability, không install | Cả 4 modules unavailable trong interpreter được kiểm | PASS — inventory | Future connector needs explicit dependency/version approval |
| S3-11 | SQL→Python exact text transport | Trusted source + approved Python driver required | NOT RUN: TLS blocked và Python SQL drivers unavailable | Fetch text trực tiếp, exact seven digits/type metadata/NULL/boundaries | No Python database connection, no driver precision evidence | NOT RUN | A05/B9 driver proof thiếu; không native datetime authoritative carrier |
| S3-12 | PostgreSQL parameter SELECT | Approved target connection/driver required | NOT RUN: active approved PG profile chưa có và psycopg/psycopg2 unavailable | Text echo/equality/7 digits/explicit collation/NULL | No PG connection/query/object creation | NOT RUN | Không claim target round-trip; SELECT-only sau này cũng không chứng minh persistence |

Source-session identity và effective permissions chỉ có thể ghi sau TLS thành công; không infer từ Windows process/registry access. Không chạy lại 9 local Stage 2 groups hoặc 21 existing pipeline scenarios để tạo cảm giác có source progress. Persistence/failure/concurrency vẫn NOT RUN cho future approved sandbox.

### 9.3 Exact remediation requirements — DBA/Owner action, chưa được thực hiện

1. **Xác nhận certificate thực tế:** DBA đọc startup ERRORLOG và SQL Server Configuration Manager cho SQLEXPRESS, cung cấp public thumbprint/Subject/SAN/Issuer/validity/EKU và chain evidence đã lọc. Agent hiện không đọc log do ACL; không đề xuất nới ACL tự động. Không dùng localhost candidate làm proof server identity.
2. **Chọn trusted server certificate hợp lệ:** nếu chưa có certificate phù hợp, DBA chuẩn bị certificate do CA phù hợp phát hành, Server Authentication EKU, validity/key/provider requirements đáp ứng SQL Server, SAN chứa DNS/FQDN mà client thực sự dùng. Xác định approved server endpoint và instance/port mapping; không giả định local alias `.` là certificate DNS identity.
3. **Server binding/private-key access:** nếu cần, Owner phê duyệt DBA cấu hình certificate qua SQL Server Configuration Manager, cấp SQL service quyền dùng private key và lên lịch restart theo quy trình. Đây là server/certificate configuration change ngoài task, không thực hiện. Không đổi authentication hoặc isolation để chữa TLS; ForceEncryption=0 không là lý do giảm client encryption.
4. **Client trust chain:** admin/DBA phân phối approved root/intermediate CA chain hoặc cung cấp trusted profile có sẵn theo policy. Mọi certificate-store installation/change cần approval riêng; không tự trust leaf/self-issued candidate hoặc dùng bypass. Private keys không được gửi vào Git/AI/logs.
5. **Verify một trusted connection sau remediation:** dùng approved DNS endpoint khớp SAN, Windows integrated authentication như hiện hành, encryption mandatory và certificate validation enabled; không -C/TrustServerCertificate=true. Chỉ sau handshake thành công mới SELECT DB_NAME/version/session identity, sys.databases flags, catalog mappings/scale và effective SELECT quyền 9 current + 2 H. Nếu SNAPSHOT OFF thì report OFF, không enable; static window/copy vẫn cần evidence riêng.
6. **Precision tests sau gates:** chạy SQL SELECT-only F1/F2 trên synthetic/allowed temporal source fields; lưu actual text/length/ns/NULL/year boundaries/order/source metadata. Python connector và target driver/version cần Owner approval nếu phải install; sau đó mới SQL→Python text và approved PostgreSQL parameter SELECT. Không tạo schema, write source hoặc coi SELECT-only echo là persisted storage proof.

Cơ sở remediation: [Microsoft certificate requirements](https://learn.microsoft.com/en-us/sql/database-engine/configure-windows/certificate-requirements?view=sql-server-ver17) và [SQL Server certificate configuration](https://learn.microsoft.com/en-us/sql/database-engine/configure-windows/configure-sql-server-encryption?view=sql-server-ver17). Đây là requirements cho DBA review, không là authorization tự áp dụng.

### 9.4 Updated readiness và stop

A01/A03/A04/A06 không có runtime evidence mới, tiếp tục Proposed với conditions Stage 2. A02 trusted capability verification vẫn BLOCKED; không có SNAPSHOT/RCSI/read-only/perms result hiện tại, không static-window proof hoặc normal publication eligibility. A05 source/driver/target PoC vẫn NOT RUN; dependency inventory bổ sung missing-driver evidence. **B9 Pending Physical Approval**, **DW-03A IN_PROGRESS**, A01–A06 **PROPOSED**; DW-03B/C và DW-04 TODO, WWI-04/Phase 1 In Progress. Không final acceptance, commit hoặc push.

Stage 3 chỉ thêm targeted diagnostic evidence/blocker/remediation vào file này. Chưa đổi SQL Server/Windows trust/registry/authentication, không đọc private keys, không install package hoặc tạo database objects. Document QA đã chạy bằng `python -c $stageThreeQa`: PASS; đúng 1 file thay đổi so baseline Stage 3, 112 protected initial files giữ SHA-256, 576 local links/2 fragments và 0 broken targets/anchors; 0 secret-pattern/format/table errors; 12 Stage 3 test records; A01–A06/status gates giữ nguyên. `git diff --check` exit 0, index rỗng, branch main/HEAD giữ baseline. Tổng 9 dirty files gồm pre-existing Stage 1/2; không stage/commit/push. QA chỉ kiểm tài liệu, không giải quyết TLS hoặc tạo precision execution evidence. Dừng connection-dependent testing tại TLS blocker, không mở rộng architecture proposal.

## 10. Verified SQL evidence update — trạng thái hiện hành ngày 2026-11-15

### 10.1 Authority, connection và ranh giới kiểm chứng

Owner cung cấp endpoint TCP, trusted command, OFF/OFF/read-only=0 và formatter V1 PASS. Vòng này **direct SELECT tái kiểm chứng** các kết quả đó, bổ sung catalog/type/permission metadata và bounded temporal samples. Các lỗi TLS ở sections 3/9 là **lịch sử trước endpoint mới**, không còn là blocker của connection này. Không suy ra cert binding/issuer đã thay đổi; task không đọc/chỉnh trust store hoặc cấu hình server.

Native invocation thực tế được Python stdlib `subprocess.run` gọi bằng argv; dạng PowerShell tương đương để tái kiểm chứng mỗi query Q01–Q07 bên dưới:

```powershell
sqlcmd -S 'tcp:DESKTOP-OBDFK6B,1433' -d WideWorldImporters -E -Nm -l 5 -t 20 -b -y 0 -w 65535 -f 65001 -Q $query
```

`$query` là nguyên văn SQL của từng Q tương ứng; timeout 20 giây mỗi command. Không `-C`, hostname override, password, giảm encryption hoặc SQL write/config statements. CLI ODBC version 17.0.1000.7; installed SQL ODBC 18.6.2.1 là toolchain quan sát, chưa pipeline dependency approval.

| Evidence | Actual result | Classification / limitation |
| --- | --- | --- |
| Q01 source identity | DESKTOP-OBDFK6B\\SQLEXPRESS; WideWorldImporters; engine 17.0.1000.7 Express Edition (64-bit); compatibility 130 | Verified current, native exit 0 |
| Trusted TCP/TLS | Q01 TCP/NTLM; Q06 encrypt_option=TRUE; mandatory -Nm và không bypass | PASS cho endpoint/account/connection đã thử; không thay proof service account |
| Isolation flags | snapshot_isolation_state_desc=OFF; is_read_committed_snapshot_on=false | SNAPSHOT unavailable theo current configuration; RCSI OFF; không enable |
| Database protection | is_read_only=false; Updateability=READ_WRITE | Database-level read-only OFF; **không chứng minh active writes** |
| Observation time Q01 | 2026-11-15T08:39:09.5988553 UTC | Chỉ metadata observation, không capture_id hoặc snapshot token |
| Interactive authority | IS_SRVROLEMEMBER('sysadmin')=1; HAS_PERMS SELECT=1 cho 11 objects | Quyền rộng, không least-privilege read-only service account; task chỉ SELECT |
| Common extraction context | Các probes là separate commands, không full capture/transaction hoặc writer exclusion | Unverified; không chứng minh cross-table consistency |
| Writer control/copy/locking proof | Không có extraction window, writer inventory/controls, verified copy hoặc SERIALIZABLE execution | Chưa verified; A02/A06 publication gates còn giữ |

Một command chuẩn bị đầu tiên bị CLI từ chối do `-h` không tương thích `-y 0`, exit 1 trước query; đã bỏ `-h`. Hai lần đọc Q03 qua wrapper gặp JSON parser lỗi vì sqlcmd chia FOR JSON thành các dòng chunk; native query path đã trả exit 0, nhưng wrapper không hoàn tất parse. Parser sau đó nối CR/LF trong JSON payload (SQL đã escape string content), rồi Q03 re-run thành công. Đây là lỗi invocation/output handling, không TLS/source-data failures. Chỉ kết quả thành công cuối được dùng ở tables dưới. Python ở đây chỉ chạy CLI/parse JSON, **không là Python DBAPI transport PoC**.

### 10.2 Current/H metadata, quyền và source types

Q02 direct catalog result: **9 current + 2 physical H**, 156 current columns + 56 H columns = 212; đúng mappings đã có trong dictionary/contracts. Không thêm source contract hoặc refresh full profiling/counts. Hai H không PK; không phát minh archive occurrence key hoặc dedupe bằng NK/start/hash.

| Object | Temporal type | PK | Columns | SELECT | Associated history |
| --- | --- | --- | --- | --- | --- |
| Sales.Customers | SYSTEM_VERSIONED_TEMPORAL_TABLE | CustomerID | 31 | 1 | Sales.Customers_Archive |
| Sales.Customers_Archive | HISTORY_TABLE | Không có PK | 31 | 1 | — |
| Sales.CustomerTransactions | NON_TEMPORAL_TABLE | CustomerTransactionID | 14 | 1 | — |
| Sales.InvoiceLines | NON_TEMPORAL_TABLE | InvoiceLineID | 13 | 1 | — |
| Sales.Invoices | NON_TEMPORAL_TABLE | InvoiceID | 25 | 1 | — |
| Sales.OrderLines | NON_TEMPORAL_TABLE | OrderLineID | 12 | 1 | — |
| Sales.Orders | NON_TEMPORAL_TABLE | OrderID | 16 | 1 | — |
| Warehouse.StockItemHoldings | NON_TEMPORAL_TABLE | StockItemID | 9 | 1 | — |
| Warehouse.StockItems | SYSTEM_VERSIONED_TEMPORAL_TABLE | StockItemID | 25 | 1 | Warehouse.StockItems_Archive |
| Warehouse.StockItems_Archive | HISTORY_TABLE | Không có PK | 25 | 1 | — |
| Warehouse.StockItemTransactions | NON_TEMPORAL_TABLE | StockItemTransactionID | 11 | 1 | — |

Q03 có **19 datetime2 column definitions, tất cả precision=27/scale=7**, gồm 15 current và 4 H. Bốn current period fields ở Customers/StockItems là AS_ROW_START/AS_ROW_END; bốn archive period fields NOT_APPLICABLE; tất cả tám period columns NOT NULL, not hidden. Chỉ ba datetime2 current columns nullable: Orders.PickingCompletedWhen, OrderLines.PickingCompletedWhen và Invoices.ConfirmedDeliveryTime; trường cuối computed theo Q06. Source precision 27 là catalog display precision, không 27 fractional digits.

| Current source type | Column count |
| --- | --- |
| bit | 6 |
| date | 6 |
| datetime2 | 15 |
| decimal(18,2) | 13 |
| decimal(18,3) | 6 |
| geography | 1 |
| int | 71 |
| nvarchar | 37 |
| varbinary | 1 |

Q06 kiểm tra cột quan trọng theo tên/type: OrderLines.Quantity, InvoiceLines.Quantity và Holdings.QuantityOnHand là int; StockItemTransactions.Quantity là decimal(18,3). Amounts/price/profit/cost thuộc decimal(18,2); TaxRate/discount/weight thuộc decimal(18,3). Giữ source scale/NULL, không float hoặc tự chọn rounding/target types. DeliveryLocation geography nullable; Photo varbinary(max) nullable; ReturnedDeliveryData nvarchar(max) nullable, cần adapter fidelity riêng. Group MAX(max_length) trong Q03 chỉ tổng hợp family, không đại diện mọi text column; Q06 trả per-column -1 cho MAX fields. Q07 describe-result trả **F1 varchar(27), F2 varchar(27), nullable=true**; không là physical PostgreSQL datatype approval.

### 10.3 A02 comparison — Proposed, không Owner approval

Giữ IDs C1–C5 của proposal. Theo task mới: A=C2, B=C5, C=C3. C1 bị loại trên current source vì SNAPSHOT OFF; RCSI cũng OFF. Không bật flags hoặc dùng NOLOCK để thay consistency proof.

| Tiêu chí | A — Evidence-backed static window (C2) | B — Verified consistent copy / separately approved snapshot environment (C5) | C — Single read-only SERIALIZABLE transaction (C3) |
| --- | --- | --- | --- |
| Isolation guarantee | Source state nhất quán nếu thực sự không có writer trên toàn required scope/interval, gồm current/H | Theo verified point/state của bản copy và writer exclusion sau tạo; loose file copies không đủ | Serializable logical outcome qua shared/range locks cho reads trong một transaction; **không snapshot tại start time** |
| Prerequisites | Inventory apps/jobs/scripts/manual writers; source-owner enforced controls và timestamps bao trùm cả reconciliation reads | Owner/DBA chuẩn bị bằng cơ chế được hỗ trợ trên môi trường/edition; storage/access/source identity/provenance riêng | Owner operational approval, một session/transaction, đủ read rights/capacity, reviewed locking/timeout/deadlock envelope |
| Effect on source | Extractor chỉ SELECT, không tự thay DB config; writer coordination cần Owner làm/phê duyệt riêng | Việc tạo copy có source IO/backup/storage implications ngoài task; extraction đọc bản độc lập được cấp | Không DML nhưng locks có thể block writers; metadata/schema interactions và target backpressure kéo dài transaction |
| Operational risks | Writer không được kiểm kê phá guarantee; repeated counts/hash và old max timestamp không phát hiện mọi transient writes | Copy provenance không rõ, source state lệch hoặc writer trên copy; không mặc định SQL Server Express hỗ trợ database snapshot feature | Blocking/deadlocks/timeout/resource pressure trên Express; failed session không thể reuse context |
| Full extraction feasibility | Ít complexity nhất cho local portfolio **nếu** static condition chứng minh được suốt declared streams | Khả thi có điều kiện trên copy đã verify; extra setup/storage nhưng giảm ảnh hưởng nguồn gốc | Có thể về semantics, chưa benchmark/execute; không mặc định phù hợp full extraction dài |
| Verification requirements | Owner/writer inventory, control evidence và interval audit; supplemental rereads chỉ hỗ trợ, không thay no-write proof | Creation/restore point và consistency evidence, exact source/config identity, permissions, no-writer controls và object mapping | Approved transaction/isolation/session evidence, scope/read completeness, locks/resource limits và controlled test task riêng |
| Failure handling | Control bị vi phạm hoặc context không chứng minh được → fail/hold candidate, capture mới trong window mới | Copy invalid/mapping/writer/context drift → hold; verify/reprepare theo task riêng, không splice original+copy | Timeout/deadlock/disconnect → abandon partial candidate, transaction rollback/end theo execution design; retry capture mới, không weaker isolation silently |
| Owner approval needs | Duyệt method/scope/window/evidence, operational coordination và gates trước extraction | Duyệt task tạo/cấp/verify copy, storage/quyền/data-handling và capture method riêng | Separate explicit operational approval trước long transaction; chưa được thực thi ở task này |

**Khuyến nghị:** A là hướng đơn giản nhất có thể bảo vệ được cho local portfolio **khi có bằng chứng thật**; hiện chưa có bằng chứng đó. Nếu không bảo đảm A, ưu tiên trình B trong task độc lập; không tự chuyển sang C. Thiếu chosen-method proof → WINDOWED_UNVERIFIED, hold normal publication; A06 qualified diagnostic use cần approval riêng. Thay đổi này là **proposal revision do verified flags**, không ghi A02 Approved. Cơ sở semantics: [Microsoft isolation levels](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-transaction-isolation-level-transact-sql?view=sql-server-ver17).

### 10.4 B9 SQL source precision — actual outcomes

Owner V1 được ghi nhận PASS và direct Q04 xác nhận lại: text `2026-11-15T12:34:56.1234567`, len 27, nanosecond 123456700. **Không nâng một fixture PASS thành toàn B9 PASS.**

| Fixture — synthetic test constants | Expected canonical text | F1 length / exact text | F2 length / exact text + typed reverse | Nanosecond |
| --- | --- | --- | --- | --- |
| FRACTION_MAX | `2026-11-15T12:34:56.9999999` | 27 / PASS | 27 / PASS | 999999900 |
| LEAP_DAY | `2000-02-29T00:00:00.0000000` | 19 / FAIL fixed width | 27 / PASS | 0 |
| MAX_MINUS_TICK | `9999-12-31T23:59:59.9999998` | 27 / PASS | 27 / PASS | 999999800 |
| MIN | `0001-01-01T00:00:00.0000000` | 19 / FAIL fixed width | 27 / PASS | 0 |
| MIN_PLUS_TICK | `0001-01-01T00:00:00.0000001` | 27 / PASS | 27 / PASS | 100 |
| NEXT_SECOND | `2026-11-15T12:34:57.0000000` | 19 / FAIL fixed width | 27 / PASS | 0 |
| NULL_VALUE | SQL NULL | NULL / PASS | NULL / PASS | NULL |
| ONE_TICK | `2026-11-15T12:34:56.0000001` | 27 / PASS | 27 / PASS | 100 |
| SENTINEL | `9999-12-31T23:59:59.9999999` | 27 / PASS | 27 / PASS | 999999900 |
| TAIL_NINE | `2026-11-15T12:34:56.0000009` | 27 / PASS | 27 / PASS | 900 |
| TRAILING_ZERO | `2026-11-15T12:34:56.1234560` | 27 / PASS | 27 / PASS | 123456000 |
| V1 | `2026-11-15T12:34:56.1234567` | 27 / PASS | 27 / PASS | 123456700 |
| V2 | `2026-11-15T12:34:56.1234568` | 27 / PASS | 27 / PASS | 123456800 |
| ZERO | `2026-11-15T12:34:56.0000000` | 19 / FAIL fixed width | 27 / PASS | 0 |

Q04: F2 **14/14 cases PASS** (13 non-NULL len 27 + SQL NULL riêng); reverse datetime2(7) equality không mất digit. Binary exact comparison dùng varbinary để tránh padded/collation equality; 13×13=**169 ordered pairs, 0 mismatch** giữa typed comparison và F2 dưới SQL Server Latin1_General_100_BIN2. V1/V2 khác đúng một source 100 ns unit. Đây là SQL Server comparison; PostgreSQL collation/predicate tests NOT RUN.

**F1 fixed-width suite FAIL ở 4/13 non-NULL fixtures:** ZERO, NEXT_SECOND, MIN, LEAP_DAY trả len 19, không có `.0000000`. Không nói source value mất precision ở whole seconds; lỗi là không đạt canonical fixed-width contract. F1 V1 riêng vẫn PASS. F2 explicit seven-digit assembly sửa được cases đã thử nhưng chỉ là candidate để tiếp tục transport PoC, chưa physical approval.

Q05 bounded actual samples: TOP(2) mỗi current/H stream = 8 row occurrences, thêm TOP(1) Customer archive zero-duration = 9 sample occurrences/18 period cells. Một record có thể xuất hiện lại giữa sample selectors; đây không là unique count/full capture. Không lấy contact/financial payload hoặc loại zero-duration.

| Population selector | Period cells | F1 len 19 cells | F2 typed reverse / length | Distinct F2 values trong sample |
| --- | --- | --- | --- | --- |
| Customers/current | 4 | 2 | 4/4, len 27 | `2013-01-01T00:00:00.0000000`; `9999-12-31T23:59:59.9999999` |
| Customers/history | 4 | 4 | 4/4, len 27 | `2013-01-01T00:00:00.0000000`; `2014-07-01T16:00:00.0000000`; `2015-07-01T16:00:00.0000000` |
| Customers/history/zero-duration | 2 | 2 | 2/2, len 27 | `2014-07-01T16:00:00.0000000` |
| StockItems/current | 4 | 2 | 4/4, len 27 | `2016-05-31T23:11:00.0000000`; `9999-12-31T23:59:59.9999999` |
| StockItems/history | 4 | 4 | 4/4, len 27 | `2013-01-01T00:00:00.0000000`; `2016-05-31T23:00:00.0000000`; `2016-05-31T23:11:00.0000000` |

F2 **18/18 sampled cells PASS**, 27 characters và SQL typed equality; current sentinel đủ bảy digits, zero-duration Customer giữ from=to. **Verified chỉ các columns/cells đã lấy mẫu**, không full-population fidelity, source occurrence uniqueness, driver transport hoặc PostgreSQL persistence. Metadata Q03 xác nhận source scale 7; không tự kết luận system-time là business-effective history hoặc thay DW-02 lookup rules.

### 10.5 Reproducible SQL evidence — các query đã thực thi thành công

Q01–Q07 dưới đây dùng cùng argv ở 10.1; mỗi final command native exit **0**, mandatory encryption và validation, SELECT-only. SQL CTE/JSON payload chỉ phục vụ diagnostic evidence, không tạo code artifact/table/schema hoặc generator. Q01 timestamp là timestamp riêng của lần query, probes không shared extraction transaction.

**Q01 — source/session/database flags**

```sql
SELECT @@SERVERNAME AS server_name,DB_NAME() AS database_name,
CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(128)) AS product_version,
CAST(SERVERPROPERTY('Edition') AS nvarchar(128)) AS edition,
compatibility_level,snapshot_isolation_state_desc,is_read_committed_snapshot_on,is_read_only,
CAST(DATABASEPROPERTYEX(DB_NAME(),'Updateability') AS nvarchar(30)) AS updateability,
CAST(CONNECTIONPROPERTY('net_transport') AS nvarchar(40)) AS net_transport,
CAST(CONNECTIONPROPERTY('auth_scheme') AS nvarchar(40)) AS auth_scheme,
IS_SRVROLEMEMBER('sysadmin') AS interactive_session_is_sysadmin,
CONVERT(varchar(33),SYSUTCDATETIME(),126) AS observed_at_utc
FROM sys.databases WHERE database_id=DB_ID()
FOR JSON PATH,WITHOUT_ARRAY_WRAPPER,INCLUDE_NULL_VALUES;
```

**Q02 — 11 objects, PK và effective SELECT**

```sql
SELECT JSON_QUERY((
SELECT q.schema_name,q.table_name,t.temporal_type_desc,t.is_memory_optimized,
hs.name AS history_schema,ht.name AS history_table,
HAS_PERMS_BY_NAME(q.schema_name+'.'+q.table_name,'OBJECT','SELECT') AS can_select,
(SELECT COUNT(*) FROM sys.columns AS c WHERE c.object_id=t.object_id) AS column_count,
JSON_QUERY((SELECT c.name AS column_name FROM sys.indexes AS ix
 JOIN sys.index_columns AS ic ON ic.object_id=ix.object_id AND ic.index_id=ix.index_id
 JOIN sys.columns AS c ON c.object_id=ic.object_id AND c.column_id=ic.column_id
 WHERE ix.object_id=t.object_id AND ix.is_primary_key=1
 ORDER BY ic.key_ordinal FOR JSON PATH)) AS primary_key
FROM (VALUES
 ('Sales','Customers'),('Sales','Customers_Archive'),('Sales','Orders'),
 ('Sales','OrderLines'),('Sales','Invoices'),('Sales','InvoiceLines'),
 ('Sales','CustomerTransactions'),('Warehouse','StockItems'),
 ('Warehouse','StockItems_Archive'),('Warehouse','StockItemHoldings'),
 ('Warehouse','StockItemTransactions')) AS q(schema_name,table_name)
LEFT JOIN sys.schemas AS s ON s.name=q.schema_name
LEFT JOIN sys.tables AS t ON t.schema_id=s.schema_id AND t.name=q.table_name
LEFT JOIN sys.tables AS ht ON ht.object_id=t.history_table_id
LEFT JOIN sys.schemas AS hs ON hs.schema_id=ht.schema_id
ORDER BY q.schema_name,q.table_name
FOR JSON PATH,INCLUDE_NULL_VALUES)) AS source_objects
FOR JSON PATH,WITHOUT_ARRAY_WRAPPER;
```

**Q03 — datetime2 definitions và current type groups**

```sql
SELECT JSON_QUERY((
 SELECT s.name AS schema_name,t.name AS table_name,c.name AS column_name,
 TYPE_NAME(c.user_type_id) AS source_type,c.precision,c.scale,c.is_nullable,
 c.is_hidden,c.generated_always_type_desc
 FROM sys.tables AS t JOIN sys.schemas AS s ON s.schema_id=t.schema_id
 JOIN sys.columns AS c ON c.object_id=t.object_id
 WHERE ((s.name='Sales' AND t.name IN ('Customers','Customers_Archive','Orders','OrderLines','Invoices','InvoiceLines','CustomerTransactions'))
 OR (s.name='Warehouse' AND t.name IN ('StockItems','StockItems_Archive','StockItemHoldings','StockItemTransactions')))
 AND TYPE_NAME(c.user_type_id)='datetime2'
 ORDER BY s.name,t.name,c.column_id FOR JSON PATH,INCLUDE_NULL_VALUES)) AS datetime2_columns,
JSON_QUERY((
 SELECT s.name AS schema_name,t.name AS table_name,TYPE_NAME(c.user_type_id) AS source_type,
 c.precision,c.scale,MAX(c.max_length) AS max_length_bytes,COUNT(*) AS column_count,
 SUM(CASE WHEN c.is_nullable=1 THEN 1 ELSE 0 END) AS nullable_columns
 FROM sys.tables AS t JOIN sys.schemas AS s ON s.schema_id=t.schema_id
 JOIN sys.columns AS c ON c.object_id=t.object_id
 WHERE (s.name='Sales' AND t.name IN ('Customers','Orders','OrderLines','Invoices','InvoiceLines','CustomerTransactions'))
 OR (s.name='Warehouse' AND t.name IN ('StockItems','StockItemHoldings','StockItemTransactions'))
 GROUP BY s.name,t.name,c.user_type_id,c.precision,c.scale
 ORDER BY s.name,t.name,source_type FOR JSON PATH)) AS current_type_groups
FOR JSON PATH,WITHOUT_ARRAY_WRAPPER;
```

**Q04 — 14 synthetic precision fixtures và 169 ordered pairs**

```sql
WITH fixtures AS (
 SELECT fixture_id, expected_text, CONVERT(datetime2(7),expected_text,126) AS dt
 FROM (VALUES
 ('V1','2026-11-15T12:34:56.1234567'),
 ('V2','2026-11-15T12:34:56.1234568'),
 ('ZERO','2026-11-15T12:34:56.0000000'),
 ('ONE_TICK','2026-11-15T12:34:56.0000001'),
 ('TAIL_NINE','2026-11-15T12:34:56.0000009'),
 ('FRACTION_MAX','2026-11-15T12:34:56.9999999'),
 ('NEXT_SECOND','2026-11-15T12:34:57.0000000'),
 ('MIN','0001-01-01T00:00:00.0000000'),
 ('MIN_PLUS_TICK','0001-01-01T00:00:00.0000001'),
 ('MAX_MINUS_TICK','9999-12-31T23:59:59.9999998'),
 ('SENTINEL','9999-12-31T23:59:59.9999999'),
 ('TRAILING_ZERO','2026-11-15T12:34:56.1234560'),
 ('LEAP_DAY','2000-02-29T00:00:00.0000000'),
 ('NULL_VALUE',NULL)) v(fixture_id,expected_text)
), formatted AS (
 SELECT *, CONVERT(varchar(27),dt,126) AS f1,
 CASE WHEN dt IS NULL THEN CAST(NULL AS varchar(27))
 ELSE CONVERT(char(19),dt,126)+'.'+RIGHT('0000000'+CONVERT(varchar(7),DATEPART(NANOSECOND,dt)/100),7) END AS f2
 FROM fixtures
)
SELECT JSON_QUERY((
 SELECT fixture_id,expected_text,f1,LEN(f1) AS f1_length,f2,LEN(f2) AS f2_length,
 DATEPART(NANOSECOND,dt) AS nanosecond_part,
 CASE WHEN CONVERT(varbinary(27),f1)=CONVERT(varbinary(27),expected_text) OR (dt IS NULL AND f1 IS NULL) THEN 1 ELSE 0 END AS f1_exact,
 CASE WHEN CONVERT(varbinary(27),f2)=CONVERT(varbinary(27),expected_text) OR (dt IS NULL AND f2 IS NULL) THEN 1 ELSE 0 END AS f2_exact,
 CASE WHEN TRY_CONVERT(datetime2(7),f2,126)=dt OR (dt IS NULL AND f2 IS NULL) THEN 1 ELSE 0 END AS f2_typed_roundtrip
 FROM formatted ORDER BY fixture_id FOR JSON PATH,INCLUDE_NULL_VALUES)) AS fixtures,
(SELECT COUNT(*) FROM formatted a CROSS JOIN formatted b WHERE a.dt IS NOT NULL AND b.dt IS NOT NULL) AS ordered_pairs,
(SELECT COUNT(*) FROM formatted a CROSS JOIN formatted b
 WHERE a.dt IS NOT NULL AND b.dt IS NOT NULL AND
 (CASE WHEN a.dt<b.dt THEN -1 WHEN a.dt>b.dt THEN 1 ELSE 0 END <>
 CASE WHEN a.f2 COLLATE Latin1_General_100_BIN2 < b.f2 COLLATE Latin1_General_100_BIN2 THEN -1
 WHEN a.f2 COLLATE Latin1_General_100_BIN2 > b.f2 COLLATE Latin1_General_100_BIN2 THEN 1 ELSE 0 END)) AS f2_order_mismatches
FOR JSON PATH,WITHOUT_ARRAY_WRAPPER;
```

**Q05 — bounded actual current/H period samples**

```sql
WITH samples AS (
 SELECT 'Customers/current' AS origin,ValidFrom,ValidTo FROM (SELECT TOP (2) CustomerID,ValidFrom,ValidTo FROM Sales.Customers ORDER BY CustomerID) a
 UNION ALL SELECT 'Customers/history',ValidFrom,ValidTo FROM (SELECT TOP (2) CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive ORDER BY CustomerID,ValidFrom,ValidTo) b
 UNION ALL SELECT 'StockItems/current',ValidFrom,ValidTo FROM (SELECT TOP (2) StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems ORDER BY StockItemID) c
 UNION ALL SELECT 'StockItems/history',ValidFrom,ValidTo FROM (SELECT TOP (2) StockItemID,ValidFrom,ValidTo FROM Warehouse.StockItems_Archive ORDER BY StockItemID,ValidFrom,ValidTo) d
 UNION ALL SELECT 'Customers/history/zero-duration',ValidFrom,ValidTo FROM (SELECT TOP (1) CustomerID,ValidFrom,ValidTo FROM Sales.Customers_Archive WHERE ValidFrom=ValidTo ORDER BY CustomerID,ValidFrom,ValidTo) e
), cells AS (
 SELECT origin,p.column_name,p.dt FROM samples
 CROSS APPLY (VALUES ('ValidFrom',ValidFrom),('ValidTo',ValidTo)) p(column_name,dt)
), formatted AS (
 SELECT *,CONVERT(varchar(27),dt,126) AS f1,
 CASE WHEN dt IS NULL THEN CAST(NULL AS varchar(27))
 ELSE CONVERT(char(19),dt,126)+'.'+RIGHT('0000000'+CONVERT(varchar(7),DATEPART(NANOSECOND,dt)/100),7) END AS f2
 FROM cells
)
SELECT JSON_QUERY((
 SELECT origin,column_name,f1,LEN(f1) AS f1_length,f2,LEN(f2) AS f2_length,DATEPART(NANOSECOND,dt) AS nanosecond_part,
 CASE WHEN TRY_CONVERT(datetime2(7),f2,126)=dt OR (dt IS NULL AND f2 IS NULL) THEN 1 ELSE 0 END AS f2_typed_roundtrip
 FROM formatted ORDER BY origin,column_name,dt FOR JSON PATH,INCLUDE_NULL_VALUES)) AS temporal_samples,
(SELECT COUNT(*) FROM samples) AS sampled_row_occurrences,
(SELECT COUNT(*) FROM samples WHERE ValidFrom=ValidTo) AS zero_duration_sample_occurrences
FOR JSON PATH,WITHOUT_ARRAY_WRAPPER;
```

**Q06 — encrypted session và relevant per-column types**

```sql
SELECT JSON_QUERY((
 SELECT net_transport,encrypt_option,auth_scheme FROM sys.dm_exec_connections WHERE session_id=@@SPID
 FOR JSON PATH)) AS current_connection,
JSON_QUERY((
 SELECT s.name AS schema_name,t.name AS table_name,c.name AS column_name,TYPE_NAME(c.user_type_id) AS source_type,
 c.precision,c.scale,c.max_length AS max_length_bytes,c.is_nullable,c.is_computed
 FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id JOIN sys.columns c ON c.object_id=t.object_id
 WHERE ((s.name='Sales' AND t.name IN ('Customers','Orders','OrderLines','Invoices','InvoiceLines','CustomerTransactions'))
 OR (s.name='Warehouse' AND t.name IN ('StockItems','StockItemHoldings','StockItemTransactions')))
 AND (TYPE_NAME(c.user_type_id) IN ('decimal','geography','varbinary') OR c.name IN ('Quantity','QuantityOnHand','ConfirmedDeliveryTime','ReturnedDeliveryData'))
 ORDER BY s.name,t.name,c.column_id FOR JSON PATH)) AS relevant_columns
FOR JSON PATH,WITHOUT_ARRAY_WRAPPER;
```

**Q07 — projected formatter result metadata**

```sql
SELECT JSON_QUERY((SELECT name,system_type_name,is_nullable FROM sys.dm_exec_describe_first_result_set(N'SELECT CONVERT(varchar(27),v.dt,126) AS f1,CASE WHEN v.dt IS NULL THEN CAST(NULL AS varchar(27)) ELSE CONVERT(char(19),v.dt,126)+''.''+RIGHT(''0000000''+CONVERT(varchar(7),DATEPART(NANOSECOND,v.dt)/100),7) END AS f2 FROM (VALUES (CAST(NULL AS datetime2(7)))) v(dt);',NULL,0) WHERE is_hidden=0 FOR JSON PATH)) AS formatter_result_metadata FOR JSON PATH,WITHOUT_ARRAY_WRAPPER;
```

### 10.6 Python/PostgreSQL readiness và isolated dependencies — chỉ đề xuất

Direct inventory `python -c $dw03DependencyCheck`, CPython **3.12.10, 64-bit**, importlib.util.find_spec cho pyodbc/pymssql/psycopg/psycopg2 trả false cả bốn. Scoped repo/process inspection: chỉ `.env.example`, related connection environment names rỗng. Không active approved PostgreSQL profile trong phạm vi đã inspect; không kết luận toàn máy không có PostgreSQL, không đoán host/port/account hoặc đọc secret stores. Không có approved installed Python DB driver để test, nên SQL→Python DBAPI và PostgreSQL SELECT đều **NOT RUN**.

| Component | Exact proposed dependency / existing tool | Approval/evidence boundary |
| --- | --- | --- |
| Source Python adapter | pyodbc==5.5.0 | Proposed cho CPython 3.12 x64; chưa install/import/connect hoặc chọn làm pipeline driver |
| Source native ODBC | Existing ODBC Driver 18 for SQL Server 18.6.2.1 | Không install/upgrade; source profile Integrated auth, Encrypt=yes, TrustServerCertificate=no; approved least-privilege identity cần riêng |
| Optional target adapter | psycopg[binary]==3.3.9, gồm matching psycopg-binary==3.3.9 | Chỉ sau approved target profile/scope; binary extra tránh tự cài compiler/libpq hệ thống; transitive resolved versions phải record trước run |
| Python/runtime | Existing CPython 3.12.10 x64 + isolated venv | Không đổi global environment, pip version hoặc dependency manifests trong task này |

Đã đối chiếu official distribution metadata ngày 2026-11-15: [pyodbc 5.5.0](https://pypi.org/project/pyodbc/5.5.0/) có cp312 win_amd64 wheel, SHA-256 `42093f86f5132eca861a21b01b3871c766973b569aeb5716b4ba4a48409228fa`; [psycopg-binary 3.3.9](https://pypi.org/project/psycopg-binary/3.3.9/) có cp312 win_amd64 wheel, SHA-256 `1ce1a6f04211626ca1a3deadee560235e8686e3888fb18f78d2be3e83bceabc4`. Đây là upstream artifact metadata, **không local download/hash verification hoặc compatibility PASS**. Cách dùng binary extra theo [official Psycopg installation](https://www.psycopg.org/psycopg3/docs/basic/install.html).

**Proposed procedure — chưa thực thi, chờ Owner approval dependency/version/scope:**

1. Owner duyệt source-only pyodbc trước; target extra chỉ khi cấp approved PostgreSQL read-only connection và phép parameter SELECT. Xác nhận dedicated read-only source identity; không dùng interactive sysadmin như deployment default.
2. Tạo venv ngoài repository, kiểm interpreter/pip hiện có; không overwrite venv đã tồn tại hoặc tự nâng pip. Review wheel/source/hash và full resolved transitive set, ghi exact versions trước precision run.
3. Sau approval, command mẫu dưới đây tạo môi trường mới và chỉ install binary distributions; không fallback build hoặc thêm package khi lỗi. Chưa tạo requirements/lock/venv files ở vòng này.
4. Future read-only PoC fetch source-side F2 bằng Python string/NULL trước native datetime coercion; kiểm length/type/metadata/digits/boundaries. PostgreSQL chỉ parameter echo/byte equality/order/range/NULL trong read-only transaction được duyệt, không schema/table.
5. SELECT-only PG echo vẫn không là persistent storage/load/recovery proof. Storage/atomicity/crash/concurrency cần sandbox/task/approval riêng. Credentials qua approved env/config, không log values.

```powershell
# PROPOSED ONLY - NOT RUN. Sau Owner approval; dung path moi, khong overwrite.
$pocVenvPath = Join-Path $env:LOCALAPPDATA 'RetailDataPlatform\venvs\dw03a-poc'
if (Test-Path -LiteralPath $pocVenvPath) { throw 'Choose a new approved venv path' }
py -3.12 -m venv $pocVenvPath
& "$pocVenvPath\Scripts\python.exe" -m pip --version
& "$pocVenvPath\Scripts\python.exe" -m pip install --only-binary=:all: 'pyodbc==5.5.0'
# Chi sau khi target adapter/profile duoc phe duyet rieng:
& "$pocVenvPath\Scripts\python.exe" -m pip install --only-binary=:all: 'psycopg[binary]==3.3.9'
```

### 10.7 Consolidated execution/readiness và Owner gates

| Check | Actual result | Status / remaining boundary |
| --- | --- | --- |
| Trusted endpoint/session + flags — Q01/Q06 | TCP, NTLM, encrypt TRUE; OFF/OFF/READ_WRITE | PASS — capability subset, không static/full context |
| 9 current + 2 H/permissions — Q02 | 11 visible, SELECT=1, current/H mappings và PK/null-H-PK recorded | PASS — interactive quyền rộng; service identity pending |
| Source/result types — Q03/Q06/Q07 | 156 current + 56 H columns; 19 datetime2(7); decimal/int/special types và formatter varchar(27) nullable | PASS — metadata only, không transport adapters |
| Owner V1 và direct Q04 V1 | Text 27/ns123456700 | PASS — riêng SQL synthetic formatter case |
| F1 canonical fixed-width suite — Q04 | 4 zero-fraction non-NULL cases len 19 | FAIL — canonical fixed-width candidate trên các cases này |
| F2 SQL fixtures/order — Q04 | 14 cases PASS, 169 pairs/0 mismatch | PASS — SQL source-side subset |
| Actual temporal source columns — Q05 | 18/18 sampled cells reverse equal, length 27; zero-duration retained | PASS — bounded SQL sample only |
| Python dependency/config inventory | Four DB modules absent, no active approved target profile in inspected scope | PASS — inventory, không driver availability |
| SQL→Python DBAPI / PG parameter SELECT | Không approved installed driver / target connection | NOT RUN |
| PG persistence/Raw completeness/atomicity/recovery/performance | Không environment/task/approval triển khai | NOT RUN; A-P01–06 full PoCs và CD-T01–21 chưa executed |
| Chosen source consistency | No static-window/copy/long-transaction execution evidence | Unverified; normal publication hold |
| A01–A06 / B9 / task closure | Mọi decisions vẫn Proposed; B9 Pending Physical Approval | DW-03A IN_PROGRESS; final acceptance NOT PERFORMED |

**Owner decisions đề nghị tiếp theo:** (1) review A01/A03/A04/A06 logical wording với gates đã có; (2) review A02 hướng static window/evidence package hoặc giao task consistent copy nếu không kiểm soát được writers; (3) review A05 F2 next-PoC direction, pinned dependencies/isolated environment và read-only identities/connections. Không xin hoặc suy ra B9 physical approval chỉ từ source formatter PASS. Không có authorization tự đổi source, tạo copy, cài package hoặc bắt đầu DW-03B/C.

**Acceptance readiness:** evidence update của task hiện tại đủ cho Owner review; DW-03A design acceptance **chưa đủ** vì A01–A06 chưa approved, full-extraction consistency, end-to-end type/100 ns fidelity, target proof và publication enforcement còn thiếu. Không source DML/DDL/config, PostgreSQL connection/change, dependency install, pipeline/full extraction, long SERIALIZABLE transaction hoặc phase transition. QA và files/Git record sau validation nằm trong assessment section 10; không dùng document QA thay runtime proof.


## 11. Formal Owner Logical Approval — current milestone

### 11.1 Authority, scope và trạng thái

Project Owner instruction **“DW-03A — Record Project Owner Logical Design Approvals”**, ngày 2026-11-15, là formal approval source. Approval không phát sinh từ reviewer recommendations, local math hoặc SQL fixture PASS. [Decision Register](wwi-dw-03a-decision-register.md) giữ đầy đủ recorded decision text và limits.

| Decision | Formal level | Approval boundary / evidence còn phải có |
| --- | --- | --- |
| A01 | APPROVED — Logical Policy | Complete source-preserving 9 current + 2 H; origins/occurrences/NULL/types/temporal evidence; no silent dedupe/overlapping temporal-query populations; fidelity/completeness gates còn mở |
| A02 | APPROVED — Conditional Logical Policy | Static window phải có defensible no-write evidence toàn extraction interval; nếu không thì separately approved verified copy; hold publication khi thiếu proof; method/operational evidence chưa verified |
| A03 | APPROVED — Logical Policy | Immutable captures/reconciled manifests/downstream pinned identities; preserve incremental/SCD2 evidence; physical schema/retention/access/capacity chưa approved |
| A04 | APPROVED — Logical Policy | Separate run/attempt/capture/logical batch/publication, compatible sealed retry và new-context/new-capture; durable-state/recovery evidence trước production |
| A05 | APPROVED — PoC Direction Only | F2 preferred source-side PoC candidate; SQL-only success không approve final datatype/adapter/encoding/collation; B9 Pending Physical Approval |
| A06 | APPROVED — Logical Policy | Dependency-complete atomic ledger/membership/active-pointer transitions và compatible consumer pins; crash/retry/concurrency/rollback/visibility phải verify; Raw không Certified Mart |

A02 giữ nguyên verified OFF/OFF/READ_WRITE; không tự enable SNAPSHOT/RCSI, dùng NOLOCK claim, tạo copy hoặc chạy long SERIALIZABLE transaction. Current interactive sysadmin connection không là ingestion least-privilege proof. B1–B8 và accepted DW-02/ADRs giữ nguyên; “Pending Physical Approval” của B9 là cùng open gate với tên “Pending — Physical Implementation” ở backlog DW-02.

### 11.2 Evidence disposition — không có execution mới

| Evidence | Verified result được bảo toàn | Boundary hiện hành |
| --- | --- | --- |
| Trusted source connectivity/metadata | Q01–Q03/Q06/Q07 section 10 native exit 0; TCP/encrypt TRUE, nine current/two H, source/result types | Không full extraction hoặc read-only service-account proof |
| F1 V1 | Exact text len27, nanosecond123456700 PASS | Một synthetic source case; không nói toàn F1 PASS |
| F1 zero-fraction fixed width | ZERO/NEXT_SECOND/MIN/LEAP_DAY len19, FAIL canonical requirement | Value whole-second không bị bịa thành precision loss; F1 không chosen fixed-width path |
| F2 fixtures/order | 14/14 fixtures PASS; 169 ordered pairs/0 mismatch | SQL Server-side; chỉ hỗ trợ preferred PoC candidate approval |
| Actual temporal samples | 18/18 sampled period cells round-trip equal, sentinel/zero-duration giữ nguyên | Bounded sample, không full population hoặc DBAPI/PG |
| Python SQL driver / PG parameter-persistence | NOT RUN theo prior verified inventory/profile limits | Không install hoặc recheck DB connection trong documentation milestone |
| Full capture/publication/recovery/concurrency | NOT RUN | Approved logical contract không là runtime validation |

SQL queries, observed values và historical QA records ở sections 1–10 không bị sửa để khớp approval. Không nâng failed F1 cases, scoped SQL samples hoặc CLI subprocess parsing thành transport/storage PASS.

### 11.3 Remaining technical gates và narrow B9 handoff

[Work Plan](wwi-dw-03a-work-plan.md) section 5 là backlog authoritative **G01–G08**: consistency proof; least-privilege ingestion account; Python SQL transport; PG parameter/persistence; exact ordering/collisions; special adapters; physical Raw/retention; publication atomicity/recovery/concurrency. Mỗi gate có dependencies/authority/evidence/status; không duplicate một backlog thứ hai tại đây.

Narrow B9 plan ở work plan section 6: **source F2 → pyodbc str/None → psycopg text parameter → byte/digit/NULL/order/round-trip checks** trên approved isolated environment. Dependency/version/venv installation và target/source identities/profiles cần separate authorization; chưa install hoặc tạo database objects. Read-only PG parameter echo khác persisted storage proof; persistence còn gate/task riêng với explicit write approval, không tự tạo bảng ở milestone này. Final PostgreSQL datatype/adapter/encoding/collation chưa được chọn.

### 11.4 Design approval, final acceptance và Git boundary

Logical decisions đã được ghi **Approved đúng cấp**, không còn pending Owner approval của sáu directions. [Assessment](wwi-dw-03a-assessment.md) section 11 tách documentation/design milestone checklist khỏi implementation test criteria. Final DW-03A acceptance **NOT PERFORMED**; concrete method/physical/B9 design disposition và full verification chưa hoàn tất. Runtime tests là gates trước execution/publication, không bị đổi thành PASS khi logical policy approved.

Current Owner instruction cho phép **một documentation-only commit sau QA/staged diff/secret checks**; thay thế stop “không commit” của các vòng trước tại milestone này. Không push hoặc mở DW-03B/C. Chỉ sửa 9 Markdown paths đã có changes, giữ các tài liệu/ADRs/nguồn ngoài scope bằng initial hashes; actual QA/Git outcome ghi trong assessment section 11. Không source/target query hoặc config/write, dependency install, full extraction hoặc pipeline trong vòng này.
