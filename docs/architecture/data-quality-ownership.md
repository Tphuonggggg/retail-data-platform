# Data Quality ownership theo pipeline stage

- Ingestion: type fidelity, source/Raw count/digest, capture completeness, rollback/retry; code ở ingestion, offline tests ở ingestion/tests.
- Infrastructure: target identity/schema/privileges và resource configuration; checks ở infrastructure/scripts và infrastructure/tests.
- dbt: staging/core/mart key, nullability, relationships, grain, amount reconciliation; data tests ở dbt/tests. Bản nháp hiện chưa được nghiệm thu.
- tests/integration: kiểm chứng xuyên source→Raw→consumer và end-to-end; không tự mutation khi import/discover.
- Monitoring: cross-pipeline metrics/logs/observability; không lặp transformation logic.

Thay cho README module data-quality chỉ có placeholder. Không thay KPI/business rules hoặc tự chọn thresholds. [KPI](../requirements/kpi-definitions/README.md), [roadmap](../../ROADMAP.md).
