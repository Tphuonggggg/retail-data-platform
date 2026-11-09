# WWI Raw Layer Requirements — Phase 1.4

**Trạng thái: Project Owner đã chấp thuận tài liệu Phase 1.4; physical design và policies vẫn Proposed.** Yêu cầu logic để thiết kế ingestion/raw của chín bảng WWI MVP. Không tạo PostgreSQL table, DDL, storage layout, partition, retention policy hay code. SQL Server WWI chỉ đọc. Xem [Source Contracts](../data-models/wwi-source-contracts.md), [Extraction Matrix](../data-models/wwi-extraction-requirements-matrix.md) và [Validation Matrix](wwi-source-validation-matrix.md).

## Ranh giới payload và metadata

**Payload nguồn:** tất cả cột được chọn từ từng bảng WWI với tên, datatype nguồn, NULL, dấu numeric và thời gian được bảo toàn theo [Metadata Dictionary](../data-models/wwi-metadata-dictionary.md). Không sửa payload thành KPI, business status hoặc dữ liệu tổng hợp. `ValidFrom/ValidTo` là **cột nguồn** ở hai bảng temporal, không phải `extracted_at`.

**Metadata kỹ thuật đề xuất** được gắn ngoài payload/record hoặc manifest có liên kết tới record. Tên dưới đây là logical field, chưa chọn physical schema/type:

| Field | Ý nghĩa bắt buộc | Phạm vi / kiểm tra |
| --- | --- | --- |
| `source_system` | Định danh một nguồn WWI SQL Server | Giá trị nhất quán cho chín bảng; không coi schema Sales/Warehouse là nguồn độc lập. |
| `source_schema` | Schema gốc, ví dụ `Sales` | Kết hợp `source_table` để phân biệt object; kiểm với contract. |
| `source_table` | Tên bảng nguồn không gồm schema | Kiểm trong danh sách chín bảng MVP; history archive nếu được duyệt phải nhận diện tách biệt. |
| `extracted_at` | Thời điểm extractor ghi nhận row/batch đã đọc | Technical extraction time, **không** là source update/business time; độ chính xác/timezone cần chốt khi triển khai. |
| `batch_id` | Định danh một đơn vị extraction cụ thể | Dùng đối soát count, retry và trạng thái complete/failed; định nghĩa chunk/window còn mở. |
| `ingestion_run_id` | Định danh lần gọi ingestion bao trùm một hoặc nhiều batch | Cho phép truy vết nhiều bảng trong một run; không chứng minh snapshot nguyên tử. |
| `source_primary_key` | Giá trị PK nguồn được sao chép để đối chiếu | Trùng logic với cột PK trong payload nhưng giữ metadata để truy vết; không tự sinh ID thay thế. Chín bảng current đều PK một cột. |
| `extraction_mode` | Phân biệt loại đọc | Giá trị đề xuất `FULL`, `INCREMENTAL`, `BACKFILL`; chỉ `FULL` là phạm vi thiết kế trực tiếp hiện nay, hai loại sau chưa có policy được duyệt. |

**Batch/run manifest đề xuất** ghi source object, extraction mode, trạng thái `started/partial/validated/failed` (tên trạng thái còn triển khai), start/end time, phạm vi PK hoặc thời gian nếu được phép, source count và raw count cùng cách đo, duplicate count, lỗi, retry association, phiên bản contract/projection và kết quả validation. Đây là yêu cầu traceability, không phải bảng đã tạo.

## Yêu cầu lưu và tái chạy

1. Giữ record nguồn chưa biến đổi về ý nghĩa; phân biệt current row, temporal archive row (nếu được duyệt), và nhiều lần extraction của cùng source PK. Không âm thầm ghi đè phiên bản raw hoặc xóa batch lỗi trước khi có chính sách xử lý.
2. Có thể truy từ raw record tới source object, source PK, batch và run; từ manifest tới tập record raw của batch. Đếm số record trong batch theo cùng source table/window để đối soát `COUNT_BIG(*)` khi điều kiện consistent read được xác minh.
3. Định nghĩa rõ ranh giới batch complete. Batch partial/failed phải được nhận diện và không được công bố như dữ liệu đã kiểm. Retry phải liên kết batch cũ, lưu lý do và kiểm duplicate; yêu cầu idempotency ở serving/validated view cần thiết kế riêng khi triển khai.
4. Giữ NULL và numeric precision gốc đến mức có thể xác minh; đối soát source-to-raw theo PK và các cột trọng yếu. Type mapping, encoding, timezone và serialized representation phải được kiểm thử trước khi chốt physical schema.
5. Hỗ trợ tái kiểm toán count/amount/quantity theo **cùng grain, population và extraction window**. Ghi rõ khi source count là phép đo ở thời điểm khác với raw extraction; không tuyên bố exact reconciliation nếu nguồn thay đổi giữa hai phép đo.
6. Bảo vệ dữ liệu khách hàng và cấu hình kết nối; không commit extract, backup, credential hay raw payload vào repository. Quyền truy cập, retention và quyền phân phối cần Project Owner quyết định trước runtime/publication.

## Điều kiện chưa quyết định

Physical schema PostgreSQL, append/upsert strategy, immutable raw retention, chunk size, batch ID format, thời gian/timezone chuẩn, checksum/hash algorithm, transactional boundary, watermark, delete event representation, nguồn temporal archive có được nạp hay không và xử lý dữ liệu nhạy cảm đều **Pending Approval hoặc Unverified**. Đề xuất metadata trên không chốt các vấn đề này.
