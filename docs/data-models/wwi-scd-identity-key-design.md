# WWI Source Identity, Surrogate Keys & Precision Options — DW-02C

**DW-02C DONE ở mức thiết kế — Accepted Architecture Directions D02/D05, technical policies Pending Approval.** [ADR-SCD-02](../adr/scd-02-persistent-surrogate-key-registry.md) chọn persistent registry + opaque SK; [ADR-SCD-05](../adr/scd-05-exact-temporal-precision.md) yêu cầu exact 100 ns. [SCD-01–07](wwi-scd-attribute-classification.md) và [A/B evidence](wwi-scd-temporal-evidence.md) giữ nguyên vai trò. Không chọn physical datatype, registry schema hoặc allocator implementation. Runtime: Not implemented yet.

## Năm loại định danh phải tách biệt

| Identity | Logical content / mục đích | Uniqueness/stability requirement |
| --- | --- | --- |
| Natural key | source instance + entity + CustomerID hoặc StockItemID | Giữ business entity qua versions; source reset/NK reuse phải có policy incarnation, không mặc định cùng khách/product mãi mãi |
| Source temporal version identity | Exact source periods + NK + evidence origin/provenance, liên kết physical row occurrence | `(CustomerID, ValidFrom)` **đã không unique**; full tuple hiện unique trong snapshot nhưng không là source-enforced durable key |
| SCD2 business version | Một analytical version episode của cùng NK, approved Type2 vector, validity/history_basis và revision lineage | Nhiều source rows có thể map cùng episode; cùng vector A xuất hiện sau B không phải episode A cũ |
| Warehouse surrogate key | Opaque identifier trỏ đúng một dimension business version, không chứa business meaning | Không đổi ý nghĩa SK đã published; replay phải giữ mapping theo policy; physical type chưa chọn |
| Historical lookup key | Fact identity + role + source NK + event date/time precision + history basis/policy revision | Đây là lookup context/request, không phải NK-only JOIN hoặc source row ID; kết quả có SK + status/evidence lineage |

Các logical fields trong tài liệu là proposed target metadata, không là cột nguồn WWI mới. Source SQL/cột lấy từ [Source Contracts](wwi-source-contracts.md) và [DW-01 Mapping](wwi-logical-source-to-target.md).

## Source versions không đồng nhất business versions

Verified A/B: Customer physical UNION ALL=714, ALL=713, một zero-duration và một duplicate-start group; Product=671, chỉ CustomFields/Tags đổi theo profiling, hiện ngoài analytical scope. Tất cả approved Customer Category/Group/Bill-to có 0 observed changes trong snapshot. CreditLimit có history nhưng SCD-01 giữ optional, chưa bật. Không tự tạo 714/671 business versions hoặc dùng CreditLimit làm trigger khi chưa activated.

**Mutable ValidTo:** current row có sentinel; khi được đóng/move vào archive, end-period và physical location thay đổi. Vì vậy full `(NK, from, to)` là snapshot row identity candidate, không mặc định durable source-version ID. Phải liên kết open/closed observations bằng evidence và revision mapping, không tạo thêm business episode chỉ do đóng interval hoặc chuyển current→archive. Hai row cùng from với end khác nhau có thể là zero-duration + positive row, không tùy tiện coi cùng version.

Proposed mapping contract: giữ raw occurrence lineage và exact periods, phân biệt current/archive/batch; business-version registry có quan hệ nhiều source occurrences→một version khi approved Type2 vector và validity compatible. Không merge qua gap, qua history_basis khác nhau hoặc non-contiguous A→B→A chỉ vì cùng hash. Technical/editor-only hoặc Type1-only changes không tự tạo Type2 episode. Xử lý zero-duration giữ Raw/audit, không interval dương (Approved SCD-04); cách attach audit evidence vào episode vẫn Pending Approval.

## Hai phương án đã xem xét — K-A được chọn ở mức architecture

| Phương án | Identity/SK design đề xuất | Replay/rebuild | Ưu / đánh đổi |
| --- | --- | --- | --- |
| K-A — Persistent registry + opaque SK | Exact source occurrence/revision mapping → stable business_version_id → SK cấp một lần và persist; source identity raw không bị biến thành SK | Replay tìm registry đã committed; rebuild giữ registry/key mappings để facts không đổi SK. Full reset registry là rebuild khác, cần remap/rebuild facts trong publication mới | Dễ giữ SK khi end-period được đóng hoặc correction; cần durable registry backup, concurrency uniqueness và recovery contract |
| K-B — Deterministic SK từ canonical immutable business-version identity | Có stable episode identity tách khỏi mutable boundaries; deterministic encoding/hash của namespace+episode ID+policy generation; không hash mutable payload/ValidTo trực tiếp làm SK | Cùng episode identity/policy cho cùng key; nếu identity derivation dựa ordinal/backfill thì có thể đổi keys, cần explicit mapping migration | Tái lập khi stable identity thật sự được bảo toàn; nguồn không có unique episode ID nên vẫn cần registry/identity evidence. Collision/algorithm/versioning tăng độ phức tạp |

**D02 Accepted:** chọn K-A. K-B chỉ giữ để trace trade-off, không còn là production alternative đang chờ chọn. Không dùng ROW_NUMBER theo thời gian làm durable episode ID/SK. Sequence/UUID/encoding/physical integer width và registry objects vẫn Pending Implementation Detail; approval architecture không phê duyệt các thuật toán đó.

Hash chỉ hỗ trợ so sánh/lookup candidate. Canonicalization cần phân biệt NULL/rỗng, collation/case, string encoding, decimal scale, attribute order, source precision và policy version. Khi digest bằng nhau vẫn phải kiểm identity/attribute equality theo contract; khác payload cùng hash là collision/error, không overwrite/merge âm thầm. Nhiều episodes có vector giống nhau không có cùng identity. Không dùng hash chưa đủ fields thay chứng cứ uniqueness.

## SK stability và correction scenarios

| Scenario | Yêu cầu logic / đề xuất Pending Approval |
| --- | --- |
| No-change replay / retry | Published version identity→SK giữ nguyên; không cấp key mới cho cùng occurrence/episode đã accepted |
| Current source period bị đóng | Link revision về đúng episode nếu evidence xác định duy nhất; thay end boundary không làm SK mang entity/version meaning khác |
| Source versions khác nhau nhưng cùng Type2 vector | Có thể map nhiều occurrences vào cùng episode khi contiguous/cùng basis, policy approved; giữ audit và Type1 correction provenance |
| Late history chèn/split interval | Không đổi nội dung SK đã dùng sang episode khác; đánh giá preserve old segment identity hay tạo replacement versions + explicit old→new map. Chỉ rekey affected facts sau approval |
| Rebuild giữ mapping | Restore registry và publication lineage; kiểm same version IDs/SKs, facts/marts totals và lookup outcomes |
| Rebuild từ đầu mất mapping | Không cam kết SK giống cũ. Namespace/generation mới hoặc migration map; rebuild toàn bộ dependent FKs trong một validated publication, không mix keys hai generations |
| Hash collision / duplicate full source rows | Chặn publish affected identity; lưu audit reason; không lấy first/max. Chọn discriminator chỉ sau review source semantics |
| Tracking set đổi | Version policy generation mới; phải đánh giá backfill/reclassification và SK reuse, không rehash toàn dimension làm đổi keys hàng loạt |

## Episode identity feasibility & registry invariants

**Approved Design Constraints D02:** một analytical episode có một opaque identity được registry giữ độc lập với source period revisions; một published SK không được đổi nghĩa sang NK/incarnation/episode khác. Chỉ source occurrence identity không đủ thay cho analytical episode identity. Các metadata logic dưới là thiết kế khả thi để review, không phải physical registry schema.

**Proposed Technical Policy cho DW-02E:** registry giữ episode identity, NK/incarnation, tracking-policy generation, Type2 vector/equality evidence, accepted validity revisions/history_basis, source-occurrence mapping, SK assignment và supersession lineage. Khi nhận evidence mới, trước hết tìm episode đã registered theo mapping/proven continuity; chưa có thì tạo candidate identity một lần và persist mapping. Không derive ID từ ordinal, mutable start/end, payload hash hoặc ingestion run. Replay dùng cùng accepted mapping; duplicate requests/concurrent allocation cần uniqueness enforcement ở implementation. Audit observations mới không phải episodes mới.

| Trường hợp | Quy tắc feasibility đề xuất / hành vi ambiguity |
| --- | --- |
| Boundary-only correction giữ được identity | Cùng NK/incarnation và tracking-policy generation, Type2 vector không đổi, occurrence lineage map duy nhất về một episode, không biến thành split/merge hoặc chồng episode khác: giữ episode ID/SK, thêm validity revision. Facts có thể cần re-resolution do coverage đổi nhưng không tự cấp SK mới |
| Open current → closed archive | Liên kết source revisions bằng exact evidence và known episode mapping; đóng ValidTo không tự tạo episode. Same-start zero-duration row vẫn giữ audit, không bị merge tùy ý vào positive interval |
| Nhiều source occurrences cùng analytical state | Chỉ map về cùng episode nếu chứng minh contiguous coverage, compatible basis và unique identity. Không merge qua gaps hoặc noncontiguous A→B→A; equal hash/vector là điều kiện chưa đủ |
| Split một episode thành nhiều positive segments | Lập candidate supersession plan old→replacement episode IDs/SKs và exact interval map; giữ old mapping cho publication cũ. Default proposal không tự cho segment đầu giữ old ID; mọi survivor exception phải có justification và approval, không tạo SK mang hai nghĩa |
| Merge episodes | Chỉ continuous compatible evidence mới được đề xuất merge; tạo replacement identity/supersession map theo policy được duyệt, giữ audit old IDs. Không tự merge noncontiguous hoặc cross-basis episodes dù cùng values |
| Không xác định duy nhất episode continuity | Giữ candidate mapping ở IDENTITY_AMBIGUITY; nếu conflict giữa accepted identities/intervals thì integrity-invalid và block affected publication. Nếu chỉ thiếu coverage thì unresolved theo D06, không tạo arbitrary identity/current/earliest match |

**Invariants khi replay/rebuild/recovery:** mapping accepted episode→SK tồn tại và kiểm được; mapping không dangling tới episode bị mất; mỗi active fact role không có hai matches; superseded mappings không được gán lại ý nghĩa; registry/source-audit/forward evidence/lookup-policy và publication generation phải tương thích. Recovery cần phục hồi cả registry lẫn revision/supersession và mapping provenance, không chỉ danh sách SK.

Giữ registry/evidence đầy đủ: replay và controlled rebuild đối soát cùng episode/SK mappings. Mất registry: restore backup đã kiểm integrity và reconcile evidence trước publish; nếu không phục hồi được, không claim SK stability, giữ affected publication/rebuild candidate pending. Chỉ sau approval mới dùng generation mới với explicit FK remap/rebuild dependent scope, không mix old/new namespaces. Backup frequency, RPO/RTO, reservation/transaction protocol, exact split/merge/rekey procedures và episode-ID allocation encoding cần DW-02E/DW-03 quyết định trước implementation. Đây là feasible logical path có ambiguity stop rule, không claim runtime persistence đã tồn tại.

## Precision representation options — không chọn physical type

Kế thừa capability/evidence tại [Temporal Precision Assessment](wwi-scd-temporal-assessment.md): datetime2(7) giữ 100 ns, PostgreSQL timestamp microsecond; sentinel và date-only ambiguity chưa giải quyết bằng datatype. Probes SQL Server không là PostgreSQL conversion tests.

| Option | Preservation / joins / intervals | Portability / ưu | Collision và rủi ro |
| --- | --- | --- | --- |
| P-A canonical full-precision representation | Giữ đủ 7 digits, exact format và source semantics; equality theo canonical values. Interval compare phải chuẩn hóa range/calendar/timezone rồi so exact | Dễ audit/export; không mất source identity ở raw | Format/collation/parse khác có thể sai ordering; text tùy ý không tự có typed interval semantics |
| P-B precision-preserving ticks | Value 100 ns theo epoch/range được xác định; exact compare/equality cho intervals | Portable nếu mọi client dùng cùng epoch và signed range; ordering rõ | Epoch/timezone/range/overflow, sentinel conversion cần test; chưa chọn type/epoch |
| P-C microsecond timestamp + exact source identity riêng | Timestamp cho truy vấn coarse; canonical/ticks/residual giữ exact source period | Thuận query tools, tách analytical time khỏi source identity | Exact identity riêng chỉ giữ key **không khôi phục lookup chính xác** nếu interval predicate vẫn dùng rounded timestamp; phải dùng exact representation cho boundary resolution hoặc mark ambiguity |

**D05 Accepted:** lossless source temporal values ở độ chính xác 100 ns là yêu cầu bắt buộc, không chỉ khuyến nghị. Lựa chọn P-A/B/C, canonical encoding/ticks epoch và physical mapping vẫn Pending Approval. Không dùng beginning/end-of-day, UTC conversion từ business date hoặc precision loss để tự resolve version. Tests cần sentinel/year rollover, 100 ns differences, same-start zero-duration, round-trip, finite adjacent intervals và collision checks.

## Chuyển giao

[Lookup/Unresolved Specification](wwi-scd-historical-lookup-design.md) dùng các identities trên; [Forward/Cutover/Recovery](wwi-scd-forward-cutover-design.md) xác định impact/state options; [Assessment & Test Matrix](wwi-dw-02cd-assessment.md) ghi nghiệm thu thiết kế. Accepted Directions không đồng nghĩa technical procedures đã approved. [DW-02E plan](wwi-dw-02e-work-plan.md) chỉ chuẩn bị kế hoạch; DW-02E/DW-03 chưa bắt đầu.
