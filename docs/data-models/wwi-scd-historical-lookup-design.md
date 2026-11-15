# WWI Historical Lookup & Unresolved Member Specification — DW-02C

**DW-02C DONE ở mức thiết kế — D03/D06 Accepted Architecture Directions; B3/B4/B5 Approved — Logical Policy (2026-11-15); thresholds/member/algorithm implementation pending.** [ADR-SCD-03](../adr/scd-03-whole-day-analytical-consensus.md) chọn whole-day consensus, [ADR-SCD-06](../adr/scd-06-controlled-unresolved-publication.md) cho phép controlled unresolved trong core và yêu cầu certified mart gates. DW-01/SCD-05/06 invariants giữ nguyên: ≤1 real match mỗi fact/role, integrity multi-match block, không current/earliest hoặc date proxy. [Identity/SK](wwi-scd-identity-key-design.md), [A/B evidence](wwi-scd-temporal-assessment.md) là đầu vào; chưa có implementation.

## Matching contract candidates

Proposed exact-time lookup khi có event timestamp đáng tin và compatible history_basis: NK + accepted positive interval `[from,to)` + policy revision → 0/1 result. Không dùng NK-only join toàn versions. Source periods chỉ system-time; mapping sang DW interval/basis phải được duyệt trước, không chỉ đổi tên source ValidFrom thành effective_from. Full source version và DW analytical episode có thể khác nhau khi tracking set không đổi.

| Fact / role | Source natural key | Event date/time | Candidate intervals và date-only limitation | 0-match / publication / restatement |
| --- | --- | --- | --- | --- |
| fact_invoice_line Buyer | Invoices.CustomerID | Invoices.InvoiceDate | Customer analytical versions theo basis được duyệt; date-only, A/B có 6 header rows chọn source version khác đầu/cuối ngày | Reason code, không lấy master bill-to/current. Resolve lại chỉ affected invoice-line buyer keys sau approval; invoice amounts invariant |
| fact_invoice_line Bill-to | Invoices.BillToCustomerID | InvoiceDate | Customer lookup **riêng**; không đi qua Customers.BillToCustomerID hiện tại; date-only, 6 sensitive header rows | Reason riêng cho role; remapping không sửa source BillToCustomerID; mart BILL_TO chỉ chọn một role |
| fact_invoice_line Product | InvoiceLines.StockItemID | InvoiceDate từ header | Product business-version candidates; source versions khác 284 line rows đầu/cuối ngày nhưng CustomFields/Tags excluded không tự tạo analytical ambiguity | Không đổi line price/tax/qty. Sau policy resolve có thể rekey product grouping, không tự restate tất cả |
| fact_order_line Buyer | Orders.CustomerID | Orders.OrderDate | Customer candidates; date-only. OrderCount/Repeat vẫn lấy header, gồm no-invoice/no-line | Không drop headers/line vì lookup thiếu; publication/quarantine phải có coverage đối soát; distinct customer theo NK |
| fact_order_line Product | OrderLines.StockItemID | OrderDate từ header | Product candidates; 291 sensitive source line rows. Không lấy LastEditedWhen thay order event time | Unresolved reason; affected date/product grouping review. Không invent order value/AOV |
| fact_stock_movement Product | StockItemTransactions.StockItemID | TransactionOccurredWhen timestamp | Có exact timestamp source, A/B 0 no/multi ở khảo sát system-time; vẫn cần basis/timezone/precision contract, không chứng minh business-effective history | Preserve signed quantity/doc refs; rekey theo approved mapping, không dựng daily balance |
| fact_inventory_current Product | StockItemHoldings.StockItemID | Source observation window + target published_state_id | Một Product version gắn **cùng published state**, không latest-at-query; observed_at không phải effective_from; published_at là công bố đích | Thiếu Product/reference hoặc state mismatch phải hold/explicit handling theo policy. Republish state khi current Product refresh; không lịch sử tồn ngày |

Tất cả role dùng cùng multi-match rule: **>1 business-version matches → error, chặn publication của consistency unit liên quan**, không DISTINCT/MAX/first hoặc chuyển thành unknown để che lỗi. Affected scope phải trace được theo B4; exact unit fact/batch/state và dependency closure design còn pending tại DW-03; không tự block toàn platform nếu chỉ một scope ảnh hưởng. Zero-duration không candidate interval dương; raw evidence vẫn giữ.

## Date-only choices đã review — L-B được D03 chọn

| Option | Điều kiện/behavior | Trade-off |
| --- | --- | --- |
| L-A conservative unresolved | Nếu thiếu time/basis hoặc trong ngày có nhiều analytical versions có thể phù hợp, mark DATE_ONLY_AMBIGUOUS; giữ otherwise-valid fact U trong Core theo B4, không giữ pending chỉ vì thiếu history | Không invent timestamp; có thể giảm coverage attributed historical segments |
| L-B whole-day analytical consensus | Chỉ khi approved policy chứng minh mọi candidate intervals phủ toàn business day cùng approved Type2 vector/episode semantics, không gap và timezone/day domain đã xác định; có thể resolve grouping consensus | Source versions khác do excluded attributes không cần tạo ambiguity giả; cần định nghĩa business version/interval/key duy nhất, không lấy bất kỳ source row tùy ý |
| L-C operational date proxy | Beginning/end-of-day hoặc proxy nghiệp vụ khác chỉ sau Owner approval và evidence; ghi policy_version, sensitivity và hạn chế | Dễ truy vấn nhưng có thể gán attributes khác; hiện **chưa approved** cho bất kỳ role nào |

**D03 Accepted:** L-B là direction hiện hành. L-A mô tả unresolved outcome khi không đủ proof, không phải alternative để thay decision; L-C operational proxy không được phép dùng. Date-only day domain còn phụ thuộc business timezone/evidence, source AS OF UTC không tự cung cấp business event hour. Bảng A/B đếm source versions, không mặc định bằng số analytical episodes; Product Type2 chỉ ba packaging columns theo D01.

### Whole-day proof obligations — design constraints, chưa chọn algorithm

Gọi D là **toàn bộ khoảng thời gian sự kiện có thể xảy ra** theo event date và day/timezone domain đã được duyệt, biểu diễn half-open `[day_start,next_day_start)`, không chỉ hai endpoint hoặc giờ làm việc tùy chọn. Các boundaries/coverage comparisons phải exact 100 ns hoặc representation tương đương đã kiểm chứng; còn thiếu day domain/analytical-validity basis thì UNRESOLVED, không đoán UTC/local/00:00.

Để trả một episode identity E: mọi thời điểm trong D phải được accepted validity intervals của E bao phủ; không có internal gap hoặc portion trước first coverage, và không có thời điểm trong D thuộc accepted analytical episode khác. Mỗi source occurrence dùng cho proof phải map về E qua registry/evidence continuity. Nhiều source occurrences continuous, cùng approved Type2 state có thể map một E khi hợp lệ; same values nhưng hai noncontiguous episodes không đủ consensus. Đồng nhất Type2 vector chưa đủ để chọn một E/SK.

Thiếu coverage hoặc có hai episodes tuần tự hợp lệ trong ngày → UNRESOLVED (history gap/date-only ambiguity). Hai accepted episodes cùng match một exact time, identity conflict hoặc interval integrity violation → INVALID, block affected publication. Zero-duration không lấp gap và không là positive interval. Checking midnight/end-day đều một match không chứng minh các điều kiện trên. Identity/basis hoặc precision loss chưa giải quyết phải được báo rõ, không lấy MIN/MAX episode làm fallback. Coverage-scan/interval-union implementation và proof artifacts format là technical policies để DW-02E/DW-03 chốt.

## Unresolved/member contract candidates

Proposed lookup result ghi fact source PK, role, source NK, event_value/event_precision, history_basis, candidate_count, lookup_status, reason, matched_business_version_id/SK nếu có, mapping_policy_version, batch/publication và evidence references. Không ghi source NK thành unknown key rồi mất lineage.

| Reason/status candidate | Ý nghĩa | Member/publication options — Pending Approval |
| --- | --- | --- |
| MISSING_REFERENCE | Parent NK chưa có trong validated master extract | Core giữ fact và lý do theo D06; physical unknown/inferred convention pending; phân biệt missing master batch với source integrity error |
| NO_HISTORY_COVERAGE | NK có thật nhưng không có accepted interval phủ event | Core giữ unresolved history reference, không current/earliest, không backdate first version; certified mart qua gate |
| DATE_ONLY_AMBIGUOUS / TIME_BASIS_UNVERIFIED | Không đủ proof whole-day/basis để chọn version | Core giữ unresolved; physical member convention pending; không gọi là successful historical match hoặc dùng operational proxy |
| PRECISION_IDENTITY_UNCERTAINTY | Thiếu precision/identity proof, chưa có proven integrity error | U giữ lineage; không gọi resolved |
| INVALID_KEY_OR_DATE / PRECISION_ERROR | Proven invalid input/parse/conversion/identity conflict | I, giữ audit và block affected scope; không route U để pass |
| MULTI_MATCH_ERROR | Nhiều real versions match cùng context | Bắt buộc chặn publication, điều tra interval/identity; không route unknown để pass gate |
| RESOLVED | Một accepted business version theo approved policy | SK và evidence mapping đầy đủ; không áp cho unknown display member |

Physical member options: reason-specific shared members tiết kiệm dimension rows nhưng grouping thiếu entity detail; per-NK inferred members giữ identity nhưng **không** chứng minh historical attributes và cần promotion policy. Chưa chọn loại member hoặc reserved SK values. D06 đã cho phép core giữ unresolved có kiểm soát; certified attribution có thể bị hold bởi gates. Missing reference, missing historical coverage và data error phải khác reason, dù sau này dùng một hay nhiều physical unknown members.

## Publication, correction và KPI reconciliation

**D06 Accepted:** core bảo toàn source facts có unresolved historical references một cách có kiểm soát; không drop/inner join mất fact vì thiếu dimension history và không xem unknown là historical match. Pending/quarantine chỉ là candidate xử lý input incomplete hoặc integrity-invalid, không còn là default alternative để loại unresolved khỏi core. Physical unresolved FK/member conventions và exact publication unit/scope chưa được chọn. S01/S02/Repeat dựa complete headers; không trộn header counts complete với line measures partial khi tính S06.

### Resolved / Unresolved / Invalid và certified gate specification

| Lớp logic | Điều kiện | Core / Certified mart behavior theo direction |
| --- | --- | --- |
| RESOLVED | Unique accepted episode theo exact-time/whole-day proof và approved basis | Core giữ matched SK/evidence; mart còn phải qua DQ/reconciliation gates |
| UNRESOLVED | Missing reference/history, valid date-only ambiguity hoặc thiếu time/basis evidence, chưa có integrity violation | Core giữ fact measures, source NK/role/reason và re-resolution lineage; không fallback. Historical grouping mart chưa được claim đầy đủ; certification phụ thuộc approved gates |
| INVALID | Multi-match integrity, conflicting identities/overlap, invalid input hoặc precision conversion gây integrity error | Preserve source/audit, block affected publication; không route thành unknown để pass gate. Nếu chỉ chưa đủ precision proof mà chưa có corruption thì unresolved với lý do riêng, không gộp lỗi thành coverage gap |

Đề xuất gate manifest cho mỗi mart/publication/period/filter: expected source population và grain, input generation/contract, required roles, resolved/unresolved/invalid row counts theo role/reason, completeness, source count/amount/quantity reconciliation, coverage formula, threshold version/approval, blocking scope, certification status và re-resolution request. Đây là logical specification, không tạo schema hoặc tự phê duyệt code names/reserved SK.

Partition input source rows cho scope đầy đủ thành R/U/I không trùng ở grain fact: fact có bất kỳ role invalid thuộc I; còn lại có bất kỳ role unresolved thuộc U; đủ roles resolved thuộc R. Đối soát `expected input rows = R + U + I` cùng validated run; I giữ audit và block scope. Trong scope được phép publish không có invalid chưa xử lý, core totals phải giữ R+U và measures đối soát nguồn; không báo source-complete nếu còn rows đang bị hold. Per-role coverage = số rows role RESOLVED / toàn population role applicable, giữ U trong mẫu; denominator 0 báo not applicable, không mặc định 100%. Measure coverage diagnostic phải tách dấu/zero/NULL để tránh netting che sai lệch; chưa chọn ratio hoặc threshold cho amount coverage.

Certified mart gate cần: complete input/publication compatible, không integrity-invalid trong scope, reconciliation theo policy được duyệt, coverage theo từng role/reason đạt ngưỡng đã được Owner duyệt và disclosure của phần unresolved. Chưa có numeric thresholds hoặc gate policy approval thì **không được gắn nhãn Certified**. All-population totals vẫn tách khỏi historical attribution quality; không chỉ publish resolved rồi báo KPI toàn doanh nghiệp đầy đủ. B5 đã chọn Tiered Certification tại KPI/view theo dependencies, kiểm cả row và value coverage; strict không là policy được chọn. Numerical thresholds được Owner cho phép chuyển DW-03, phải duyệt trước Certified publication. Reason/member encoding, exact dependency closure và re-resolution procedures chuyển DW-03; [Final Specification](wwi-final-scd2-design-specification.md) và [backlog](wwi-dw-02e-work-plan.md) ghi B3/B4/B5/B7 logical approval.

Late dimension/history correction chỉ mở lại matching requests trong NK/role/interval/affected publication scope; tạo mapping revision/audit, so old/new SK và impacted mart groups trước authorization. Customer master BillTo change không sửa Invoice source buyer/bill-to. Source fact correction là loại thay đổi riêng, phải giữ source lineage, không dùng dimension remapping để che source-data update. [Forward/recovery design](wwi-scd-forward-cutover-design.md) tách rõ version creation, fact rekey và restatement; [test matrix](wwi-dw-02cd-assessment.md) chưa được thực thi.
