# Roadmap hi?n h?nh

| M?c | Dependency | Outcome/acceptance | Tr?ng th?i |
|---|---|---|---|
| Kh?i t?o v? source/DW design | Owner acceptance | Contracts, profiling, BRD/KPI/grains/SCD designs | DONE ? Design |
| MVP-RESET-01 | Existing code/Raw, Owner reset | Simplified config/preflight/docs; tests/imports/Compose; no data mutation | DONE ? Refactoring; runtime target unavailable |
| First selected smoke | Reset QA, private config, runtime authorization | Holdings batch64, count/distinct/numeric/NULL/digest/reconnect; unpublished | TODO |
| Sales Full Load | Smoke PASS | Selected Sales dependencies, Raw reconciliation, rerun | TODO |
| Sales dbt/DW/Mart | Accepted Raw + approved grains/KPI | Staging/core and one Sales Mart; DQ/measure reconciliation | TODO |
| Power BI / MVP demo | Sales Mart | Dashboard, reproducible execution/basic logs/DQ | TODO |
| Incremental | Full Load evidence | Current-state convergence/checkpoint/failure tests in independent environment | TODO |
| Customer/Inventory + SCD2 | Relevant source/model evidence | Adopt preserved historical designs with scoped runtime proof | TODO |
| Airflow/advanced recovery | Stable executable pipelines | Orchestration, replay/resume/monitoring | TODO |
| Optional cloud | Stable MVP + Owner scope | BigQuery/other controlled extensions | TODO |

Sales-first ?u ti?n tri?n khai; kh?ng lo?i source contracts/accepted DW design. Kh?ng y?u c?u Customer/Inventory/advanced recovery ho?n t?t tr??c demo Sales. Existing all11 publication contract kh?ng t? ??i; selected smoke remains unpublished. [Historical roadmap](docs/archive/pre-reset/ROADMAP.md).
