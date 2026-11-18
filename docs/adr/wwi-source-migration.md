# ADR — Chọn WideWorldImporters làm nguồn OLTP chính

- **Trạng thái:** Chủ dự án phê duyệt định hướng ngày 2026-11-07; các quyết định triển khai, nghiệp vụ và schema vẫn còn mở.
- **Người quyết định:** Project Owner.
- **Tài liệu liên quan:** [Project Scope](../../PROJECT_SCOPE.md), [Roadmap](../../ROADMAP.md), [Task Tracker](../../TASKS.md).

## Quyết định

`WideWorldImporters` trên SQL Server là **nguồn OLTP chính duy nhất** của dự án và chỉ được truy cập ở chế độ **chỉ đọc**. PostgreSQL là Data Warehouse do dự án tự thiết kế và xây dựng. Luồng dự kiến: SQL Server → Python ingestion → PostgreSQL raw/staging → dbt/SQL → PostgreSQL warehouse → analytical marts → Power BI. Apache Airflow điều phối pipeline.

MVP gồm Sales/Invoicing, Customer Analytics và Inventory Movements theo thứ tự đó. Cần hoàn thiện Sales end-to-end, bao gồm ingestion, warehouse, Airflow, kiểm tra chất lượng cơ bản và tập trung, monitoring và reporting, trước khi mở rộng sang Customer và Inventory. Purchasing, Finance và BigQuery là các phần mở rộng có kiểm soát.

Repository giữ lại các module Data Engineering có thể tái sử dụng. Các file và yêu cầu chỉ phục vụ thiết kế nguồn trước đây đã được loại bỏ; dự án không duy trì một kiến trúc nguồn thứ hai đang có hiệu lực.

## Lý do

Database WWI có sẵn trên máy chứa các bảng OLTP liên kết với nhau về orders, invoices, customer transactions và stock item movements, cùng temporal history cho một số thực thể. Điều này hỗ trợ MVP đã chọn mà không cần xây các hệ thống nguồn mô phỏng. Những quan sát này **không** đồng nghĩa với việc phê duyệt quy tắc revenue, source-to-target mapping hoặc warehouse schema.

## Hệ quả

- Source contracts, định nghĩa KPI và tests phải được viết lại theo grain và quan hệ của WWI. Không cộng measures từ order, invoice, invoice line, ledger và stock movement qua các JOIN gây nhân bản dòng.
- Dự án không thay đổi database WWI gốc. CDC nằm ngoài thiết kế hiện hành; Change Tracking chưa được bật. WWI-04 phải đề xuất môi trường thử nghiệm độc lập để kiểm chứng INSERT/UPDATE và incremental end-to-end trước khi tạo hoặc sử dụng môi trường đó.
- Temporal history có thể hỗ trợ một số dimension SCD2, nhưng không được mặc định là lịch sử đầy đủ cho mọi giao dịch.
- Kiểm tra data quality cơ bản bắt đầu từ ingestion và warehouse. Phase 6 bổ sung quality gates tập trung, monitoring và các tình huống failure nâng cao.
- ADR này không cho phép tự bắt đầu Phase 1, viết DDL, triển khai ingestion hoặc cài đặt package.
- Các yêu cầu Data Engineering dùng chung từ đề cương ban đầu đã được đối chiếu và diễn giải theo WWI trong scope/roadmap. Đề cương cũ đã được loại khỏi repository; tài liệu hiện hành là nguồn tham chiếu cho dự án.

## Các phương án đã xem xét

Tiếp tục kiến trúc nguồn mô phỏng trước đây: Project Owner không chọn. Chuyển toàn bộ thành phần sang repository mới: không chọn để giữ các module có thể tái sử dụng và khả năng truy vết task. Dùng SQL Server làm warehouse: nằm ngoài kiến trúc đã duyệt; PostgreSQL là warehouse đích.

## Quyết định còn mở

Revenue recognition/tax và ngày invoice so với ngày delivery; `CustomerID` so với `BillToCustomerID`; grain và schema của fact/dimension; profit/COGS; thuộc tính và khoảng hiệu lực SCD2; incremental extraction/deletes/môi trường thử nghiệm; inventory daily balance; ngưỡng data quality. Xem [Open Decisions](../archive/pre-reset/PROJECT_SCOPE.md#open-decisions).
