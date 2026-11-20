# airflow

Sở hữu DAGs, schedules/dependencies/retries, Airflow configuration, plugins và tests riêng orchestration. DAG gọi entrypoints ingestion/dbt, không sao chép ETL logic.

**Chưa triển khai.** Chỉ có tài liệu trách nhiệm chuyển từ orchestration; không thêm DAG/plugin/config rỗng hoặc cài Airflow. Triển khai sau pipeline độc lập ổn định theo [roadmap](../ROADMAP.md). Cross-pipeline observability thuộc [monitoring](../monitoring/README.md).
