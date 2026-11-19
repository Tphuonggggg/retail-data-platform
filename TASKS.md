# Task tracker hi?n h?nh

MVP-RESET-01 supersede operational security gates c?. [Tracker l?ch s?](docs/archive/pre-reset/TASKS.md) gi? acceptance/decisions c?; kh?ng d?ng old security blockers l?m current MVP dependency.

| ID | Module/dependencies | Acceptance | Status |
|---|---|---|---|
| INGEST-01 | Existing Docker/Raw + environment + explicit local source config | Restore existing container/volume; dependencies and both preflights | IN_PROGRESS — Raw healthy/all11 target PASS; source opt-in pending |
| INGEST-02 | INGEST-01 | Real holdings batch64 unpublished smoke; count/distinct/numeric/NULL/digest/meta | BLOCKED — source local configuration decision pending; NOT RUN |
| INGEST-03 | INGEST-02 | All11 load/reconciliation/RI/temporal fidelity/rerun/failure handling; no publication | TODO — NOT RUN; must not close after smoke only |
| Phase0/Phase1, WWI-01?04 | Source/design docs | Owner accepted requirements/source/KPI/logical DW/SCD/load designs | DONE ? Design |
| MVP-G02 / Raw provisioning | infrastructure/storage | Foundation +11 payload/4 controls/11 views + target preflight verified | DONE ? Runtime provisioning |
| WWI-06A | ingestion | CLI/types/batch/COPY/count/digest/rerun/rollback offline coverage | REVIEW ? Implemented/Offline Tested |
| WWI-06C | Historical investigation | Permission/TLS evidence retained; no longer a global selected-load gate | DEFERRED ? Historical |
| MVP-RESET-01 | Repository, Owner scope; baseline cf94d05 | Preserve dirty work, simplify selected preflight/config/docs/deps, tests/links/Compose, local commits, no runtime ingestion | DONE ? MVP_RESTRUCTURING_COMPLETE; 107 offline tests/links/Compose PASS; source selected preflight PASS; target runtime blocked by Docker engine unavailable |
| SALES-01 | Reset + private config + runtime authorization | Unpublished selected smoke, durable reconcile and same-run rerun | TODO |
| SALES-02 | SALES-01 | Sales Raw full scope/dependencies and business reconciliation | TODO |
| SALES-03 | SALES-02 + approved DW/KPI | dbt staging/core/Sales Mart/basic DQ | TODO |
| SALES-04 | SALES-03 | Power BI + repeatable Sales demo | TODO |
| NEXT-01 | Sales evidence | Incremental, SCD2, Customer/Inventory, Airflow, advanced recovery per roadmap | TODO |

Current runtime ingestion NOT RUN. Parent WWI-05/06 not declared operationally DONE. No source data/permissions or target schema changes in reset.
