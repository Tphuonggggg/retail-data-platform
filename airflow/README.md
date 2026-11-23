# Airflow — NOT_IMPLEMENTED

Chưa có DAG, scheduler, plugins hoặc runtime configuration. Không có Airflow orchestration acceptance; không cài hoặc tạo placeholder DAG trong task tài liệu.

Milestone tiếp theo sẽ gọi CLI ingestion/dbt hiện có, không sao chép ETL logic: preflight → explicit run/version → reconcile/DQ → serving/BI steps được cho phép. Dependency/retry phải giữ idempotency, unknown-COMMIT inspection, explicit capture pins và quyền tối thiểu. Observability cần run/version correlation, status/error vàalert; chưa có monitoring runtime độc lập. Không tự publish, restart infrastructure hoặc chạy dữ liệu để chứng minh DAG chưa tồn tại.

Điều kiện bắt đầu: Owner duyệt, pipeline độc lập ổn định, Docker/SQL connectivity, credential injection private, fixture/failure recovery vàquality gates được xác minh. Xem [root](../README.md), [ingestion](../ingestion/README.md), [dbt](../dbt/README.md).
