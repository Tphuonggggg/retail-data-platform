# Quy tắc làm việc

- Đọc README và kiểm tra Git trước khi sửa; tài liệu tiếng Việt, code/định danh tiếng Anh. Chỉ làm task được giao, bảo toàn thay đổi chưa commit, không tự chuyển phase/nghiệm thu hoặc push.
- Source WWI chỉ SELECT. Không tự DML/DDL/GRANT, migration, xóa database/volume, đổi SQL permissions hoặc certificate stores.
- Không commit secrets/.env/source extracts; không log DSN/password hoặc driver exceptions chứa secrets.
- Windows Authentication dùng current development account. Admin source cần explicit development opt-in, không fallback credential. TLS Encrypt=yes, TrustServerCertificate=no mặc định; chỉ APP_ENV=development mới cho explicit trust=yes đã duyệt.
- Preflight chỉ selected objects: SELECT/projection/schema và target identity/schema/privileges. History INSERT không là global blocker.
- Giữ Decimal/NULL/Unicode/datetime2(7), count/digest reconciliation, transaction/idempotency/recovery; không tự sửa business KPI/grain/source contract hoặc accepted DW design.
- Dùng requirements.txt và unittest hiện hữu; không tự thêm package/framework. Phân biệt code/offline/runtime checks; không ghi PASS khi chưa chạy. Routine local/offline commands không cần approval riêng.
- Ingestion sở hữu extract/load/codecs; dbt sở hữu staging/core/marts/DQ; infrastructure sở hữu Compose/provisioning/recovery; powerbi sở hữu reports; airflow sở hữu orchestration tương lai. scripts/tests/docs có source tiện ích hỗ trợ đang được import, không xóa theo tên thư mục.
- Mỗi module cấp cao chỉ một README. Hướng dẫn vận hành: README root và README của ingestion/dbt/infrastructure/powerbi/airflow. AGENTS.md được giữ riêng cho quy tắc cộng tác.

MVP: Sales Full/Incremental snapshot-diff → Raw → dbt/DQ → DW/Sales marts → Power BI. Airflow/historical SCD2 và domain analytics khác chưa hoàn tất. Không chạy ingestion/build hoặc đổi database khi chỉ làm tài liệu.
