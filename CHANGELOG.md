# Changelog

Ghi nhận thay đổi đã thực hiện; không ghi tính năng mới chỉ ở mức kế hoạch.

## Unreleased

### Changed
- Hoàn tất nghiệm thu Phase 0 theo phê duyệt có điều kiện của chủ dự án: P0-01 đến P0-06 ở `DONE`; ADR chuyển nguồn được diễn giải bằng tiếng Việt; liên kết, file tracked và secret được kiểm tra lại. Phase 1 vẫn `Not Started`.
- Đồng bộ scope, roadmap, task tracker, kiến trúc và README theo nguồn WWI SQL Server chỉ đọc và warehouse PostgreSQL.
- Chuyển MVP sang Sales/Invoicing, Customer Analytics và Inventory Movements theo thứ tự; Purchasing, Finance và BigQuery là extensions.
- Ghi ADR chuyển nguồn và giữ các quyết định KPI, grain, SCD2, incremental, inventory và ngưỡng chất lượng ở trạng thái Open.
- Điều chỉnh Phase 3–4 có kiểm tra chất lượng cơ bản; Phase 5–6 hoàn thiện Sales Airflow/monitoring trước khi mở rộng subject areas.
- Đối chiếu đề cương cũ và bổ sung yêu cầu tái lập local, bảo mật nguồn, unit/integration/e2e, CI, quan sát batch, tối ưu truy vấn có số đo và kiểm soát chi phí cloud vào scope/roadmap WWI.
- Bổ sung quy tắc `.gitignore` cho credentials, file database và bản trích xuất nguồn; P0-05 chuyển `REVIEW` sau kiểm tra Git readiness.
- WWI-01 được chủ dự án nghiệm thu; TASKS.md ghi trạng thái `DONE` và bằng chứng tài liệu/cấu trúc.
- Git repository local được khởi tạo trên branch `main`; danh sách file và staged diff được kiểm tra trước baseline commit theo P0-06.

### Removed
- Chín CSV và các tài liệu thiết kế/source contracts dành riêng cho dataset và hệ thống mô phỏng cũ.
- Các thư mục chỉ dành cho thiết kế nguồn trước đây, không chứa chức năng dùng chung.
- PDF đề cương cũ sau khi các yêu cầu kỹ thuật chung còn phù hợp đã được chuyển vào tài liệu hiện hành.

### Status
- Phase 0: Completed ở mức tài liệu và repository. Chưa triển khai hoặc kiểm thử pipeline.
- P0-01 đến P0-06 và WWI-01: `DONE`. Không tạo remote hoặc push; Phase 1 chưa bắt đầu.
