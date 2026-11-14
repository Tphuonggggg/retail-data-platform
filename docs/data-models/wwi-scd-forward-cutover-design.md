# WWI Forward-Tracked SCD2, Hybrid Cutover & Recovery — DW-02D

**DW-02D DONE ở mức thiết kế — D01/D02/D04/D06 Accepted Architecture Directions, technical procedures Pending Approval.** [ADR index](../adr/README.md) ghi quyết định Owner; SCD-01–07 giữ nguyên. [A/B evidence](wwi-scd-temporal-assessment.md), [identity/SK](wwi-scd-identity-key-design.md), [lookup](wwi-scd-historical-lookup-design.md), [DW-01 Change Impact](wwi-change-impact-matrix.md) là đầu vào. Không MERGE/dbt/DDL hoặc test environment. Runtime: Not implemented yet.

## Logical states và time basis

Các trạng thái logic đề xuất: ABSENT, BASELINE_CANDIDATE, VALIDATED_VERSION_SET, PUBLISHED, UNRESOLVED, RETIRED_CANDIDATE và FAILED_CANDIDATE. Đây là state contract để review, chưa có physical status table. Chỉ validated candidate generation được phép trở thành published generation sau approval/gates tương ứng; không để consumer thấy một phần dimension mới và facts/marts cũ lệch key.

Giữ riêng source_valid_from/to, observation window/observed_at, proposed analytical validity/history_basis và published_at. Source temporal intervals là system-time evidence; observation-time chỉ từ lúc batches bắt đầu quan sát, không biến thành business-effective timeline. Trong transition, “version mới” nghĩa analytical episode theo approved tracking set và time policy; không là mọi archive row. Customer tracking direction là Category/Group/Bill-to; credit/hold optional chưa bật. Product Type2 **chỉ UnitPackageID, OuterPackageID, QuantityPerOuter** theo D01. Analytical Product fields khác đã admitted theo Type1 direction; excluded/audit không tự thành Type1. Type1 correction scope/AccountOpenedDate Type0 exception và technical time policy chưa chốt, không overwrite ngay.

## State Transition Matrix

| Scenario / Input State | Detected Change | Expected Dimension State đề xuất | Affected Facts | Required Validation |
| --- | --- | --- | --- | --- |
| Initial full baseline: ABSENT | Current + permitted physical history có evidence | BASELINE_CANDIDATE → validated version set; giữ raw source rows/zero-duration, chỉ approved Type2 changes hình thành positive analytical episodes; insufficient validity → unresolved | Resolve các fact/role theo policy; không backdate baseline tới giao dịch trước coverage | Exact row/key counts, full identity, interval checks, coverage, Type2 vector vs source versions; không tự publish timeline |
| New NK: existing published set | NK mới trong complete validated input | Tạo candidate episode từ evidence basis cho phép; không nhận ngày source business event từ observed_at | New facts/previous missing-reference requests trong scope | NK/incarnation uniqueness, reference contract, source timing, 0/1 role match |
| Type1-only change | Name/correction field đổi, approved Type2 vector không đổi | Không tạo Type2 episode chỉ vì Type1. Options: overwrite label across versions hoặc current-only correction view, phải chọn policy trước; giữ audit | Fact SK thường giữ; report labels/caches có thể cần refresh | Type1 scope/version policy; totals/key invariance; semantic reclassification không tự coi correction |
| Type2 change | Approved vector đổi null-safe | Close/open candidate episodes theo time basis được duyệt; source-backed nếu có evidence, nếu chỉ snapshot thì observation-bounded; không invent business effective_at | Future/unresolved facts hoặc affected historical scope sau approval; không auto-rekey mọi fact | One current per NK theo accepted basis, positive/non-overlapping intervals, source→business mapping, optional attrs không trigger |
| Multiple changes between batches | Snapshot A rồi C; có thể đã qua B hoặc A→B→A | Nếu nguồn history đủ, retain source-backed sequence; nếu chỉ snapshots thì chỉ biết endpoints/observation bounds, không tạo B giả | Facts trong khoảng thiếu evidence có thể unresolved | Gaps/coverage, basis label, lost intermediate uncertainty; không claim complete history |
| No-change replay / metadata-only | Same accepted vector/occurrences; editor hoặc excluded attrs đổi | Reuse mapping/SK; audit observation mới nếu cần, không Type2 episode mới | Không rekey chỉ vì run mới; marts giữ amount/qty/count | Replay identity, canonical equality, same publication semantics; CustomFields/Tags không trigger |
| Late historical correction | Evidence muộn bổ sung/sửa interval hay attributes | Candidate timeline revision, conflict/quarantine nếu không đủ identity; giữ published revision đến approval, không overwrite history âm thầm | Identify exact NK/role/time and old/new keys; rekey/restate đề xuất riêng | Source evidence precedence, overlaps, as-of sensitivity, old→new mapping, totals invariance |
| Delete/missing NK | Key vắng trong snapshot hoặc delete được xác nhận | Partial absence → hold investigation. Confirmed delete: retire current candidate theo policy, preserve history/source audit; reinsert có incarnation decision | Historical facts không cascade delete; new/current facts có unresolved/retirement impact | Complete snapshot proof, delete vs extraction error, source history coverage, NK reuse |
| Failed batch | Input partial hoặc validation/publication lỗi | FAILED_CANDIDATE, published version set trước giữ visible; không tiến checkpoint công bố | Không publish subset dependent facts/marts; giữ affected-work audit | Failure phase, recovery point, registry integrity, no mixed-generation refs |
| Retry | Rerun input của failed attempt | Reconcile candidate/registry với last committed state; reuse committed identities, không reuse SK cho ý nghĩa khác | Reapply đúng scope một lần | Idempotency, stable SK meaning, failed attempts lineage, double-apply checks |
| Backfill/rebuild | Re-read history/full current, hoặc restore registry | Build candidate generation từ **cả forward history đã giữ** và source evidence; clean rebuild không còn forward evidence không được claim tương đương | Existing FK mappings giữ hoặc remap toàn dependent scope trong generation mới sau approval | Registry restore/remap, historic forward retention, full-equivalence, key-set/amount/qty/coverage tests |

Type0 AccountOpenedDate correction là policy còn nghiên cứu: không tự overwrite/reversion do dữ liệu đổi; flag candidate correction request, audit origin và impacts trước khi Owner quyết định. Type1 correction xuyên versions có thể đổi label quá khứ; phải phân biệt label restatement với thay đổi facts.

## Hybrid history cutover — reconciled direction H-A được duyệt

Ba input streams logic: (1) physical source archive, (2) source current row, (3) forward-observed batches. Raw không trộn mất origin; business-version mapping liên kết source revisions thay vì coi archive và current ở hai lần extract là hai sự kiện độc lập. Một observation có thể xác nhận continuation của version cũ, không tự tạo episode.

| Option | Cutover boundary và yêu cầu | Ưu / rủi ro |
| --- | --- | --- |
| H-A reconciled baseline theo NK + generation | Giữ source temporal evidence tới snapshot/cutover window đã validate; bridge current approved vector và source identity tới first forward observation cho từng NK. Chỉ chuyển basis khi continuity được chứng minh; không đủ thì unresolved span | Tái dùng history có evidence, không ép global business effective T. Cần consistency window, source version revision map và retention |
| H-B separate source-backed và observation-backed histories | Giữ hai evidence tracks/bases, lookup policy chỉ chọn một track cho context đã duyệt; không union hai active intervals như cùng timeline | Trung thực khi khó chứng minh bridge; query/coverage phức tạp và cần tránh multi-match giữa tracks |

**D04 Accepted:** reconciled cutover H-A là direction hiện hành. H-B chỉ giữ evidence tracks riêng cho phần chưa hòa giải, không cho phép publish hai histories conflict thành một verified timeline hoặc ép bridge. Exact generation/window/boundary và procedure chưa chọn. Không lấy pipeline start timestamp làm business effective_from; observed_at chỉ là quan sát, actual change có thể nằm giữa hai observations. Source history retention/restore và concurrency phải được kiểm chứng ở các task extraction sau.

### Cutover validation obligations

1. Dedupe source occurrence và current→archive revisions theo exact evidence, không chỉ timestamp(6) hoặc payload hash; không làm mất zero-duration raw/audit.
2. So sánh approved Type2 vector của source current và forward first observation null-safe; metadata-only/Type1-only differences không tạo Type2 episode. Nếu khác mà không biết thời điểm, ghi unknown transition window, không vẽ interval business giả.
3. Validate overlaps/gaps **trong từng basis và approved combined view**; không dùng precedence arbitrary để che 2 active matches. Conflicting source/backfill phải hold revision để review.
4. Chỉ public một mapping generation nhất quán; SK đang referenced không đổi meaning. Current inventory Product key gắn publication state mới, không latest-at-query.
5. Full reload phải giữ source audit, registry và forward observations đã accepted. Nếu input chỉ còn WWI snapshot gốc, không recreate forward history đã mất; phải restore retained evidence hoặc báo non-equivalent rebuild.

### Reconciliation rules và cutover invariants ở mức thiết kế

| Kiểm tra | Required invariant / output evidence |
| --- | --- |
| Input completeness | Manifest phân biệt archive/current/forward batches, source ranges/observed windows/precision và coverage limitations; zero-duration không mất khỏi Raw/audit |
| Per-NK bridge | Current source approved vector và first forward vector so null-safe dưới cùng tracking-policy generation; khác không biết thời điểm → unverified transition window, không tự timestamp business change |
| Occurrence→episode mapping | Mỗi accepted occurrence/revision có unique mapping hoặc explicit unresolved/conflict reason; một change từ hai streams không cấp hai episodes/SKs. Registry phục hồi được open→closed revisions |
| Intervals/basis | Accepted combined lookup view không gap ẩn/overlap; source/observation/analytical validity và lineage tách; không ép nối khi basis/coverage chưa được phê duyệt |
| Full reload | Retained forward evidence, registry và supersession/lookup-policy maps còn tương thích; reconcile version identities và fact R/U/I theo scope, không chỉ raw row count |
| Consumer publication | Core giữ controlled unresolved, invalid block affected scope; certified mart gates độc lập. Product current SK thuộc cùng published state, không latest-at-query |

Các invariants trên được đòi hỏi bởi D02/D04/D06; exact dedupe/bridge/transaction algorithms, chosen cutover boundary và pass thresholds là technical policies chưa được duyệt. Expected same mapping không được kiểm bằng source row count = analytical episode count, vì hai grain khác nhau.

## Recovery/publication options — chưa triển khai

R-A staged generation + publication pointer: dimension candidate, lookup outcomes, affected facts/marts được validate ở generation mới; chuyển consumer sang generation đã hoàn chỉnh. Ưu điểm rollback về publication cũ rõ ràng; tăng storage và lineage work. R-B transactional bounded updates + durable work/recovery ledger: registry/version updates và dependent rekey trong consistency unit có rollback/retry semantics; hiệu quả scope nhỏ nhưng cross-layer atomicity/checkpoint khó hơn. Không chọn transaction isolation, storage tables, checkpoints hoặc orchestration.

Failure sau SK allocation/trước publish: key reservation không được gán lại cho episode khác nếu có thể đã referenced; registry commit/reservation policy cần thiết kế và tests. Failure sau dimension write/trước fact rekey: publication cũ phải vẫn đọc đúng mappings; retry so current registry và candidate diff trước khi apply. Failure sau fact updates/trước mart refresh: không expose mismatched generation; keep/recover prior published state hoặc gated completion theo option được duyệt. Đây là yêu cầu logic, không khẳng định database đã có atomicity.

Backfill/retry lưu request/attempt/reason, previous/new publication IDs, impacted NK/interval/role/fact IDs, old/new SK mappings và reconciliation outcomes. Không log credentials/PII payload vào repository. Acceptance cần so source event changes và dimension-policy changes riêng, tránh reprocess ledger làm nhân double counts.

## Change Propagation & Restatement Matrix

Theo [DW-01 Change Impact](wwi-change-impact-matrix.md); **version creation ≠ fact rekey ≠ mart restatement ≠ source correction**. Tất cả scopes/actions kỹ thuật dưới đây là đề xuất cần approval trước khi thực thi.

| Change | Dimension action | Fact role keys | Mart/report impact / approval |
| --- | --- | --- | --- |
| Customer Type2 Category/Group | Candidate new episode khi approved vector đổi | Chỉ fact contexts thuộc accepted interval/basis; old facts không tự chuyển về current | Customer segmentation/as-was groups; C03/C04 totals invariant; C01/C02 distinct NK không đổi |
| Product Type2 UnitPackageID/OuterPackageID/QuantityPerOuter | Candidate analytical episode cho approved packaging vector; không source-price substitution | Invoice/order/movement product keys trong scope được duyệt; không rewrite quantity | Product/movement grouping context có thể đổi; totals invariant, no daily inventory balance |
| BillToCustomerID master đổi | Candidate Customer affiliation version theo SCD-01 | **Không sửa Invoices.CustomerID/BillToCustomerID** từ master; buyer/bill-to lookup dùng chính invoice NK riêng | Billing attribution C04 giữ source role; remap dimension version chỉ theo validity policy; không cộng roles |
| Type1 correction của analytical field đã admitted | Không Type2 episode; Product fields ngoài ba packaging columns dùng Type1 direction, nhưng overwrite current/all versions chưa chọn | SK không đổi meaning; không rekey chỉ vì label; technical/excluded không đổi class | Có thể refresh labels/cache hoặc regroup report theo mode được duyệt; historical Type1 impact disclosed, amount/qty/count invariant |
| Late history version/correction | Candidate revised intervals/evidence revision | Resolve affected requests; old/new mapping diff review, không blanket restate | Restate affected old/new date/NK/version groups sau approval; lưu audit/reconciliation |
| Historical lookup policy remapping | Không nhất thiết tạo dimension version; mapping policy revision mới | Fact rekey chỉ sau Owner duyệt date/basis/unknown handling | Reconcile before/after attributed/unknown coverage; all enterprise totals theo cùng population |
| Product current-version refresh | Current pointer theo new validated publication | fact_inventory_current rekey theo same published_state_id | Republish current mart; observed_at nguồn giữ nghĩa, published_at mới; không generate stock history |
| Source fact header/line correction | Không tự là dimension version change | Propagate header-only source changes đúng DW-01; retain source correction lineage | Old/new groups phải recalc nếu source date/role/product đổi; không che dưới label SCD remap |

Không đụng source WWI để thực thi các action; test INSERT/UPDATE/DELETE/replay chỉ sau approval trong môi trường SQL Server độc lập. [Assessment/Test Matrix](wwi-dw-02cd-assessment.md) quy định bằng chứng mong đợi; chưa chạy bất kỳ scenario nào.
