# WWI Temporal History, Precision & Lookup Assessment — DW-02B

**DW-02B khảo sát đã nghiệm thu; Verified observations giữ nguyên; SCD-03–07 Approved Principles, technical policies Pending Approval.** Chỉ khảo sát SELECT ngày 2026-11-14; không chọn SCD2 validity, as-of proxy, fallback hay physical datatype. [SQL evidence](wwi-scd-temporal-evidence.md) giữ truy vấn và aggregate output tái kiểm chứng; [classification](wwi-scd-attribute-classification.md) là đề xuất độc lập, không tự phê duyệt từ observed changes. DW-01 và BRD không đổi.

ADR-SCD-01–06 được Owner duyệt sau nghiệm thu A/B, xem [ADR index](../adr/README.md). Các numeric findings/probes dưới đây giữ nguyên evidence; Product tracking nay chỉ ba packaging columns, registry/consensus/reconciled cutover/exact precision/controlled unresolved là accepted directions. Không có truy vấn mới hoặc runtime conversion result trong vòng nghiệm thu C/D.

## Năm loại thời gian/dữ liệu cần phân biệt

| Khái niệm | Ý nghĩa / giới hạn |
| --- | --- |
| Physical archive rows | Dòng thực trong archive; union current+archive giữ cả zero-duration, duplicate start và technical-only versions |
| FOR SYSTEM_TIME ALL | Kết quả temporal query, không đồng nghĩa physical UNION ALL; số Customer rows ít hơn 1 trong snapshot này |
| System-time validity | Khoảng period nguồn do engine theo dõi; không chứng minh business-effective time của customer/product |
| Business-effective validity | Thời điểm thay đổi có hiệu lực nghiệp vụ; chưa có approved source/contract hay rule để suy từ source period |
| Pipeline observation-time validity | Khoảng từ các batches mà pipeline thực sự quan sát giá trị; chưa có extraction batches của dự án; không được backdate thành lịch sử trước quan sát |

Tài liệu [Microsoft temporal overview](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal/overview?view=sql-server-ver17) mô tả engine-managed period. [Temporal querying](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal/query-data?view=sql-server-ver17) diễn giải AS OF theo UTC. Đây là semantics engine; business dates trong WWI chỉ có ngày, không tự cung cấp giờ/timezone giao dịch để map vào source system period. Restore/snapshot không chứng minh toàn bộ quy trình lịch sử nguồn.

## Temporal history coverage — C01/C02, P01/P02

| Metric | Sales.Customers | Warehouse.StockItems |
| --- | ---: | ---: |
| Current rows / distinct current NK | 663 / 663 | 227 / 227 |
| Physical archive rows / NK trong archive | 51 / 46 | 444 / 227 |
| Physical UNION ALL version rows | 714 | 671 |
| FOR SYSTEM_TIME ALL rows | 713 | 671 |
| NK có 1/2/3/4/5 physical versions | 617 / 42 / 3 / 1 / 0 | 0 / 55 / 129 / 41 / 2 |
| Distinct ValidFrom / ValidTo | 65 / 4 | 18 / 14 |
| Open-ended rows (sentinel nguồn) | 663 | 227 |
| Zero-duration / negative-duration | 1 / 0 | 0 / 0 |
| Overlap với prior running max end / internal gaps | 0 / 0 | 0 / 0 |
| Duplicate (NK, ValidFrom, ValidTo) groups | 0 | 0 |
| Duplicate (NK, ValidFrom) groups | **1** | 0 |

| Source scope | Min / max ValidFrom | Min / max ValidTo |
| --- | --- | --- |
| Customers current | 2013-01-01 00:00 / 2016-05-07 00:00 | sentinel / sentinel |
| Customers archive | 2013-01-01 00:00 / 2015-06-12 00:00 | 2013-07-01 16:00 / 2015-07-01 16:00 |
| StockItems current | 2016-05-31 23:00 / 2016-05-31 23:12 | sentinel / sentinel |
| StockItems archive | 2013-01-01 00:00 / 2016-05-31 23:09 | 2016-05-31 23:00 / 2016-05-31 23:12 |

Sentinel = `9999-12-31 23:59:59.9999999`. Range table trình bày các giá trị quan sát tới phút; đầy đủ 7 digits và SQL trong evidence. Không gộp 714 Customer versions thành 714 customers hoặc coi 671 Product source versions là số DW SCD2 versions cần tạo.

Phân phối physical periods theo năm được tái kiểm bằng C05/P04: Customer ValidFrom năm 2013/2014/2015/2016 có 644/31/34/5 rows; finite ValidTo năm 2013/2014/2015 có 18/17/16 rows, còn 663 sentinel. Product ValidFrom năm 2013/2016 có 219/452 rows; finite ValidTo năm 2016 có 444 rows, còn 227 sentinel. Đây là distribution của source versions, không phải số customer/product mới hoặc business events theo năm.

**Zero-duration / start-key identity:** C04 bổ sung xác nhận một duplicate-start group chứa một zero-duration row; nếu chỉ xét positive intervals thì duplicate start groups=0. Vì vậy `(CustomerID, ValidFrom)` không phải unique identity cho toàn physical history **ngay cả trước conversion**. Zero-duration không match bất kỳ điểm nào theo điều kiện khảo sát `from <= t < to`; giữ dấu vết raw/audit, không tự kéo dài period, xóa archive hoặc biến thành business transition có duration. SCD-04 đã duyệt giữ Raw/audit và không coi interval dương; cách map sang DW business versions còn Pending Approval. Attribute LAG counts cũ có zero-duration là physical transition comparisons, không phải số valid intervals hoặc sự kiện nghiệp vụ độc lập.

Không có internal gaps/overlap chỉ chứng minh các intervals hiện có nối tiếp theo NK; không chứng minh coverage trước first version, deleted NK đã mất khỏi phạm vi, source historical completeness hoặc business time. Retention INFINITE ở metadata cũ không chứng minh lịch sử đầy đủ.

## Precision & historical version identity — C03/P03

DW-01 đã xác nhận datetime2(7) 100 ns, PostgreSQL timestamp microsecond và precision 0–6 ([PostgreSQL datetime](https://www.postgresql.org/docs/18/datatype-datetime.html)); capability review không thay phiên bản stack được duyệt. Các probes dưới chạy tại SQL Server, **không phải PostgreSQL round-trip test**.

| Probe | Customer | Product | Diễn giải |
| --- | ---: | ---: | --- |
| ValidFrom có phần dưới microsecond | 0 | 0 | Finite boundaries hiện quan sát nằm trên lưới microsecond |
| Finite ValidTo có phần dưới microsecond | 0 | 0 | Probe loại sentinel trước rounding |
| Sentinel cần conversion riêng | 663 | 227 | Sentinel có chữ số thứ bảy, chưa kiểm driver/PostgreSQL conversion |
| Full identity collisions sau truncate về microsecond | 0 | 0 | So NK+converted from+to, không chứng minh start-only unique |
| Full identity collisions sau SQL Server cast(6), chỉ finite-end rows | 0 | 0 | Không ngoại suy sang converter PostgreSQL chưa được chọn |
| Positive intervals thành zero sau truncation | 0 | 0 | Kết quả snapshot, không đảm bảo future batches |

**Rủi ro vẫn mở:** source versions chỉ khác 100 ns có thể thành cùng microsecond; rounding có thể đẩy boundary/sentinel sang giây/ngày/năm kế tiếp, truncation có thể co duration hoặc đổi match; nếu convert start/end không đồng nhất có thể tạo gap/overlap hoặc nhiều/no match. Ví dụ số học giả định: hai boundaries `.1234561` và `.1234562` khác nhau ở nguồn nhưng truncation đều `.123456`; đây không là dữ liệu WWI đã quan sát. Không tạo test DB/DML để minh họa.

| Phương án identity preservation — đều Pending Approval | Ưu / rủi ro cần xét |
| --- | --- |
| Giữ canonical source period đủ 7 digits + source object/NK/provenance, timestamp query riêng | Dễ audit, không mất source value; cần contract parse/compare/order và typed representation |
| Giữ số ticks 100 ns từ epoch thống nhất + NK/provenance | Ordering/identity exact nếu serialization đúng; phải kiểm range/overflow/timezone semantics |
| Timestamp microsecond + residual 100 ns + source period gốc | Query tiện, có thể reconstruct; tăng composite compare complexity, sentinel test bắt buộc |
| Warehouse surrogate version key + mapping source full identity/payload fingerprint | Tách DW SK khỏi period precision; không tự đảm bảo source uniqueness, hash collision/duplicate physical rows cần kiểm riêng |

Source full tuple hiện unique không là guarantee dài hạn; duplicate identical rows future cần audit discriminator/manifest policy, không tự tạo synthetic temporal ordering. Start-only key đã không đủ với Customer, dù chuyển đổi không gây thêm collisions. Không chọn option, SK algorithm, hash, epoch, PostgreSQL type hoặc unknown version trong DW-02A/B.

## Historical Lookup Feasibility Matrix — L01–L07

Các phép khảo sát dùng positive version membership `[ValidFrom, ValidTo)`, midnight và `23:59:59.9999999` của cùng calendar day. Đây là hai probes để đo độ nhạy, **không phê duyệt start/end-of-day** làm as-of. Count có trọng số theo source fact/header rows, không phải số distinct NK hay business changes. Với date-only event, `event_at` trong SQL cũng là midnight proxy, chưa có giờ thực.

| Lookup population / role | Source rows | No match / multi tại đầu ngày | No match / multi tại cuối ngày | Rows chọn source version khác đầu/cuối ngày | Feasibility / giới hạn |
| --- | ---: | --- | --- | ---: | --- |
| InvoiceDate → Customer buyer | 70.510 headers | 0 / 0 | 0 / 0 | 6 | Full match tại proxies, nhưng ambiguous choice trong ngày |
| InvoiceDate → Customer bill-to | 70.510 headers | 0 / 0 | 0 / 0 | 6 | Lookup role riêng; không suy từ master bill-to current |
| OrderDate → Customer buyer | 73.595 headers | 0 / 0 | 0 / 0 | 6 | Giữ order chưa invoice, không join line để đếm header |
| InvoiceDate → Product | 228.265 lines | 0 / 0 | 0 / 0 | 284 | Source system versions khác trong ngày, không có giờ invoice event |
| OrderDate → Product | 231.412 lines | 0 / 0 | 0 / 0 | 291 | Không dùng order-line timestamps làm business event proxy tự chọn |
| Movement day → Product | 236.667 movements | 0 / 0 | 0 / 0 | 293 | Khi dùng **TransactionOccurredWhen exact**: no-match=0, multi=0; không mặc định timestamp này là business effective của product |
| Current published state → Product | 227 holdings hiện hành | Không áp dụng | Không áp dụng | Không áp dụng | L07: 0 missing current Product, tất cả open-ended; chưa có DW published_state nên chỉ Verified source availability |

Số rows có >1 positive source version giao với cả ngày lần lượt bằng 6/6/6/284/291/293. Không phải nhiều version cùng match một timestamp; mỗi probe trong snapshot đều ≤1. Product source changes đã biết nằm ở CustomFields/Tags (đã được SCD-02 loại khỏi analytical scope), nên khác source version **không tự chứng minh** khác analytical attributes hoặc phải sinh DW version. Customer CreditLimit changes có optional candidate riêng, SCD-01 chưa kích hoạt trong MVP. Muốn so historical business segmentation cần classification và validity rules được duyệt trước.

Current fact Product SK vẫn thuộc **cùng published_state_id** như DW-01 đã nghiệm thu; không latest-at-query, không thay observed_at bằng published_at. Không có batch/publication của dự án để kiểm chứng đây là runtime đúng. Thiếu history/multiple matches/fallback vẫn là Open Decision, không chọn earliest/latest/current/00:00/23:59 để thay dữ liệu thiếu.

## Forward-tracked SCD2 readiness — phân tích sơ bộ

- Source historical reconstruction có thể khảo sát cho CreditLimit và những thuộc tính approved thực sự có source evidence; phần trước observation đầu tiên, history chưa phủ hoặc thuộc tính không có source changes không được invent transitions. Type2 candidate chưa đổi trong snapshot có thể chỉ là một baseline version, không chứng minh bất biến.
- Nếu tracking attributes được duyệt và nguồn history không đủ/không có, batches mới có thể tạo **observation history từ thời điểm theo dõi**, không biết chính xác lúc thay đổi giữa hai batches và có thể bỏ intermediate changes. Pipeline chưa chạy nên chưa có forward history Verified.
- Chuyển từ source history sang forward tracking cần một cutover/evidence boundary, provenance/history_basis và reconciliation current state. Nếu sau này backfill history thì có nguy cơ duplicate versions, overlap, facts rekey hoặc marts restate. Đây là yêu cầu để thiết kế tiếp, chưa xây algorithm.
- Source metadata-only changes hoặc CustomFields/Tags excluded không tự trigger analytical Type2. Bảng current và history có thể thay đổi giữa các SELECT; cần consistency/extraction protocol ở DW-03A, không tuyên bố ảnh chụp nguyên tử.
- Test environment độc lập về sau cần cover two updates trong cùng transaction (zero-duration), 100 ns boundaries, no-op/editor-only updates, Type1/Type2 semantic changes, NK reuse/delete/reinsert, late history/gaps, replay/cutover và batch publication. Chưa tạo môi trường hoặc thực hiện test.

## Kết luận giới hạn

Verified: coverage/identity/proxy results theo SQL trên snapshot hiện có. Proposed: attribute classes và identity preservation options. Unverified: business-effective validity, future update behavior, driver/PostgreSQL precision, cutover/fallback/SK policy và actual forward history. Bốn facts/BRD/KPI không thay đổi. Hồ sơ này nghiệm thu A/B; C/D/E là các task thiết kế tiếp theo chỉ bắt đầu theo Owner authorization.
