# Project-wide utilities

- [validate_repository.py](validate_repository.py): Python syntax, Markdown links/anchors, secret patterns; không runtime connections.
- [run_checks.py](run_checks.py): chạy offline suites theo ownership hiện hành, nonzero exit khi có lỗi.

Source diagnostic thuộc [ingestion](../ingestion/scripts/inspect_wwi_source.py). Raw connection/recovery/provisioning thuộc [infrastructure](../infrastructure/README.md). Không tự cài dependencies, chạy ingestion hoặc cấp quyền.
