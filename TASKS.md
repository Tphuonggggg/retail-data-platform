# Task tracker hi?n h?nh

MVP-RESET-01 supersede operational security gates c?. [Tracker l?ch s?](docs/archive/pre-reset/TASKS.md) gi? acceptance/decisions c?; kh?ng d?ng old security blockers l?m current MVP dependency.

| ID | Module/dependencies | Acceptance | Status |
|---|---|---|---|
| REPO-STRUCTURE-02 | Pipeline-stage ownership, existing uncommitted DW draft | Paths/imports/docs/Compose/offline checks; live capture integrity; no ingestion/dbt runtime | PARTIAL — structural/offline checks PASS; Docker Engine unavailable/TCP55434 timeout, live capture verification BLOCKED |
| INGEST-01 | Existing Docker/Raw + approved local config | Same container/volume, correct identities/dependencies and source/target all11 preflight | DONE ? healthy18.7, all preflights PASS; explicit Owner development config recorded |
| INGEST-02 | INGEST-01 | Real holdings batch64 unpublished smoke; count/distinct/numeric/NULL/digest/meta | DONE ? smoke47b6c909,227 rows, controls/durable reconciliation PASS |
| INGEST-03 | INGEST-02 | All11 load/reconciliation/RI/temporal fidelity/rerun/failure handling; no publication | DONE ? FULL_LOAD_RUNTIME_ACCEPTED, run5abc4a32,939208 rows/11 PASS; rerun/rollback/retry PASS; pointer NULL, consistency UNVERIFIED |
| Phase0/Phase1, WWI-01?04 | Source/design docs | Owner accepted requirements/source/KPI/logical DW/SCD/load designs | DONE ? Design |
| MVP-G02 / Raw provisioning | infrastructure/storage | Foundation +11 payload/4 controls/11 views + target preflight verified | DONE ? Runtime provisioning |
| WWI-06A | ingestion | CLI/types/batch/COPY/count/digest/rerun/rollback offline coverage | DONE ? Implemented / Offline Tested / Full Load Runtime Verified via INGEST-03 |
| WWI-06C | Historical investigation | Permission/TLS evidence retained; no longer a global selected-load gate | DEFERRED ? Historical |
| MVP-RESET-01 | Repository, Owner scope; baseline cf94d05 | Preserve dirty work, simplify selected preflight/config/docs/deps, tests/links/Compose, local commits, no runtime ingestion | DONE ? MVP_RESTRUCTURING_COMPLETE; 107 offline tests/links/Compose PASS; source selected preflight PASS; target runtime blocked by Docker engine unavailable |
| SALES-01 | Reset + private config + runtime authorization | Unpublished selected smoke, durable reconcile and same-run rerun | DONE ? Raw smoke coverage via INGEST-02/03 |
| SALES-02 | SALES-01 | Sales Raw full scope/dependencies and business reconciliation | DONE ? Sales Raw/dependencies and source controls verified via INGEST-03 |
| SALES-03 | SALES-02 + approved DW/KPI | dbt staging/core/Sales Mart/basic DQ | TODO |
| SALES-04 | SALES-03 | Power BI + repeatable Sales demo | TODO |
| NEXT-01 | Sales evidence | Incremental, SCD2, Customer/Inventory, Airflow, advanced recovery per roadmap | TODO |

Current Full Load runtime accepted for unpublished candidates; [counts/evidence](ingestion/README.md#ingest-010203--runtime-acceptance-2026-11-19). WWI-05/06 parent/phase closure remains Owner review; no automatic transition or downstream implementation. Publication remains NOT RUN.
