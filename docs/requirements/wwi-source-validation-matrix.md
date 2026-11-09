# WWI Source Validation & Reconciliation Matrix — Phase 1.4

**Trạng thái: Project Owner đã chấp thuận tài liệu Phase 1.4; các kiểm tra sau ingestion vẫn Proposed.** Chưa chạy ingestion hoặc raw checks; `PASS` trong tài liệu nguồn chỉ là kết quả khảo sát SQL Server ngày 2026-11-07, không phải test pipeline. [Profiling SQL](../data-models/wwi-profiling-queries.md) Q01–Q11 và [Relationship SQL](../data-models/wwi-relationship-validation-sql.md) R01–R06 là evidence tái kiểm chứng. [Source Contracts](../data-models/wwi-source-contracts.md) định nghĩa từng bảng; [Raw Requirements](wwi-raw-layer-requirements.md) định nghĩa dấu vết extraction.

## A. Kiểm tra dữ liệu nguồn (đã khảo sát hoặc cần lặp khi extract)

| ID | Kiểm tra / grain | Evidence hiện có | Kỳ vọng ở thời điểm extract | Trạng thái |
| --- | --- | --- | --- | --- |
| S01 | `COUNT_BIG(*)`, distinct PK cho từng trong 9 bảng current | Phase 1.2 Q01: PK duy nhất, count từng bảng | Đếm lại cùng population/window; không dùng metadata estimate thay exact count | Verified snapshot; repeat proposed |
| S02 | Required columns / NULL distribution theo dictionary | Phase 1.2 Q02/Q07; dictionary nullable | Cột NOT NULL không thiếu; nullable giữ riêng, không ép thành invalid | Verified sample; repeat proposed |
| S03 | FK non-NULL → parent theo từng relationship | Phase 1.2 Q09, Phase 1.3 R03: 0 orphan ưu tiên/bổ sung | Anti-join non-NULL; NULL FK optional báo riêng; xem parent ngoài 9 bảng | Verified snapshot; repeat proposed |
| S04 | Order→Invoice cardinality và line counts | Phase 1.2 Q04; Phase 1.3 R02/R06 | Báo số order không invoice, invoice/order, line/header; không yêu cầu schema 1:1 | Verified snapshot; repeat proposed |
| S05 | Transaction type, `InvoiceID` NULL và customer roles | Phase 1.2 Q05; Phase 1.3 R04 | Phân bố theo type, buyer/bill-to tách role; payment NULL không gắn orphan | Verified snapshot; repeat proposed |
| S06 | Temporal validity của Customers và StockItems current+archive | Phase 1.2 Q06/Q08; một customer zero-duration | Báo overlap, gap, zero/negative duration và coverage; giữ raw archive count riêng `FOR SYSTEM_TIME ALL` | Verified snapshot; repeat proposed |
| S07 | Signed movement / link pattern theo transaction type | Phase 1.2 Q07; Phase 1.3 R05 | Báo issue/receipt/adjustment, negative/zero/positive, nullable invoice/PO; chưa áp threshold | Verified snapshot; repeat proposed |
| S08 | Timestamp NULL, distinct và min/max | Phase 1.2 Q11: trùng nhiều | Quan sát lại trước khi đề xuất incremental; không lấy timestamp đơn làm unique key | Verified snapshot; policy open |

## B. Kiểm tra sau ingestion (chưa triển khai, phải chạy khi có raw)

| ID | Kiểm tra / grain | Yêu cầu đối soát | Evidence nền | Trạng thái |
| --- | --- | --- | --- | --- |
| I01 | Source→raw row count theo table, batch, extraction window | So source count với số raw record của **cùng population**; ghi thời điểm hai phép đo, batch complete/partial | Q01 baseline; [raw metadata](wwi-raw-layer-requirements.md) | Proposed; Not implemented yet |
| I02 | PK coverage / missing source records | Anti-join source PK set ↔ raw PK set trong cùng window; phân biệt source-only, raw-only, duplicate extraction và source thay đổi giữa lúc đọc | Q01/R03 PK; snapshot không nguyên tử | Proposed; Not implemented yet |
| I03 | Duplicate extraction | Trong một batch complete, source PK xuất hiện quá số lần theo extraction mode/temporal grain đã duyệt; giữa retry gắn cùng run/batch lineage | Q01 source PK; raw metadata | Proposed; Not implemented yet |
| I04 | Required field, datatype, NULL và numeric precision | So raw payload với source projection, giữ NULL/precision và `LastEditedWhen`/period; ghi lỗi type conversion, không sửa nguồn | Dictionary; Q02/Q07 | Proposed; Not implemented yet |
| I05 | FK raw non-NULL / missing parent | Kiểm theo dependency và cùng snapshot logic; orphan raw do partial/inconsistent extraction phân biệt orphan nguồn; optional FK NULL giữ nguyên | Q09/R03 | Proposed; Not implemented yet |
| I06 | Amount source→raw ở **InvoiceLineID** và **CustomerTransactionID** | Đối soát `TaxAmount`, `ExtendedPrice`, `LineProfit`, `TransactionAmount` riêng theo bảng/PK và cùng batch; tổng theo grain riêng, không định nghĩa KPI | Phase 1.2 Q05 | Proposed; Not implemented yet |
| I07 | Invoice lines↔invoice transaction ở **InvoiceID** | Tổng `InvoiceLines.ExtendedPrice` so với transaction type `Customer Invoice` của cùng invoice sau khi hai tập complete; không cộng hai tập thành revenue | Phase 1.2 Q05: 70.510 invoice khớp snapshot | Proposed; Not implemented yet |
| I08 | Quantity source→raw ở **OrderLineID**, **InvoiceLineID**, **StockItemTransactionID** | So từng source row/PK và tổng theo cùng table/window; giữ dấu movement | Q05/Q07 | Proposed; Not implemented yet |
| I09 | Stock issue↔invoice line ở **(InvoiceID, StockItemID)** | Tổng quantity issue type 10 đổi dấu so với invoice lines khi cả hai tập complete; không khẳng định FK line-level | Phase 1.2 Q10: 228.265 cặp khớp | Proposed; Not implemented yet |
| I10 | Stock receipt↔PO line ở **(PurchaseOrderID, StockItemID)** | Chỉ kiểm khi dependency Purchasing được đọc hợp lệ; đối chiếu unit theo công thức đã quan sát, báo cặp chưa receipt riêng | Phase 1.2 Q10: 8.358 cặp khớp, 9 PO-line-only | Proposed dependency; Not implemented yet |
| I11 | Temporal raw version validity và current/archive coverage | Nếu archive được duyệt nạp, đối soát version key/period, zero-duration, overlap/gap và raw archive count; không lấy `FOR SYSTEM_TIME ALL` bằng raw archive | Q06/Q08 | Proposed; Not implemented yet |
| I12 | Retry/partial batch | Batch partial không vào tập được công bố; rerun không tạo duplicate trái policy; ghi count lỗi, PK lỗi và run lineage | Raw requirements | Proposed; Not implemented yet |

## C. Kiểm tra nghiệp vụ cần quyết định bổ sung

| ID | Quyết định cần phê duyệt | Vì sao chưa thành quality gate | Owner/task |
| --- | --- | --- | --- |
| B01 | Order chưa có invoice | 3.085 order trong snapshot; không có business status được duyệt để coi là lỗi | WWI-03 |
| B02 | `InvoiceLines.LineProfit < 0` | 4.626 rows; profit/COGS semantics và ngưỡng chưa duyệt | WWI-03 |
| B03 | Movement `Quantity = 0` | 4 rows, cần quy tắc stocktake/type | Trước inventory mart |
| B04 | Customer buyer so với bill-to; payment allocation | 44.245 invoice khác role, 26.637 payment `InvoiceID` NULL; không thể phân bổ bằng FK | WWI-03 |
| B05 | Daily inventory balance/current holdings | 227/227 holdings khác tổng movement thô; thiếu opening balance/stocktake rule | Trước inventory mart |
| B06 | SCD2/business-effective as-of và delete | Temporal system-time, một zero-duration; chưa chứng minh lịch sử nghiệp vụ hay delete policy | WWI-04 |
| B07 | Error thresholds/gate severity | Không có ngưỡng warn/block/quarantine được owner duyệt | WWI-03/04 và phase DQ |

## Nguyên tắc đối soát

Đối soát phải ghi `source_schema`, `source_table`, batch/run, extraction window, grain, population, công thức tổng, thời điểm đo, số nguồn/raw và chênh lệch. Khi nguồn thay đổi giữa các phép đọc, chỉ báo chênh lệch quan sát, không tự kết luận extraction lỗi. Không join trực tiếp nhiều fact-like bảng khác grain để cộng amount/quantity. Không trừ refund hoặc tính revenue/COGS trong Phase 1.4.
