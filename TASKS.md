# Task tracker hi?n h?nh

MVP-RESET-01 supersede operational security gates c?. [Tracker l?ch s?](docs/archive/pre-reset/TASKS.md) gi? acceptance/decisions c?; kh?ng d?ng old security blockers l?m current MVP dependency.

| ID | Module/dependencies | Acceptance | Status |
|---|---|---|---|
| POWERBI-ACCESS-02 | ACCESS-01 + Owner authorization; accepted version c825b18e | Model-level SELECT đúng 12; compile/manifest/build/tests; reader trước/sau; đối soát counts/KPI/digests/metadata | DONE — POWERBI_PERSISTENT_GRANTS_ACCEPTED; 12 rebuilt, 39 dbt tests/build và standalone PASS, 181 offline tests PASS; [evidence](powerbi/persistent-grants.md). Không đóng SALES-04/parent phases |
| POWERBI-ACCESS-01 | Owner-approved exact SQL; accepted Sales version c825b18e | Password login reader; SELECT đúng 12 objects, không DML/DDL/Raw/meta/test; bảo toàn dữ liệu/version/publication; hướng dẫn BI, proposal grants | DONE — POWERBI_ACCESS_ACCEPTED; runtime reader PASS, 44 table contents không đổi; [evidence và hướng dẫn](powerbi/access.md). dbt grants chưa áp dụng; SALES-04 chưa DONE |
| ANALYTICS-DISCOVERY-01 | Validated Sales version c825b18e + approved KPI/YAML + read-only PostgreSQL | Verify21 model pins/lineage; reproducible Sales exploration,8 evidence-backed candidates, conceptual dashboard/measure mapping; preserve Raw/DW | DONE — SALES_INSIGHT_DISCOVERY_COMPLETE;25 SQL queries/8 cross-checks;19 tables match accepted baseline; Raw/meta and warehouse content unchanged; [report](docs/analytics/sales-discovery-01/README.md). Power BI implementation chưa bắt đầu |
| INGEST-INCR-01 | Accepted Full Load + DBT-SALES-01 + Owner-approved new-only incremental migration | Live snapshot-diff/current-state reconciliation/no-change; isolated persisted I/U/D/recovery; version-pinned dbt/DQ/marts; source/Raw/publication preserved | DONE — INCREMENTAL_RUNTIME_ACCEPTED; 2 live versions604672 unchanged/run; 166 fixture checks; 97 independent checks; 21 models/69 dbt tests; same-version21 counts/19 digests stable; [evidence](docs/audits/ingest-incr-01/evidence.json) |
| DBT-SALES-01 | INGEST-03 + approved Sales DW/KPI + scoped transformation role | Real capture-pinned staging/DQ/core/marts; YAML contracts; independent reconciliation/rerun/performance; Raw preserved | DONE — DBT_SALES_RUNTIME_ACCEPTED; 21 models/69 dbt tests/129 checks; real DQ604672 records; unpublished/UNVERIFIED |
| REPO-STRUCTURE-02 | Pipeline-stage ownership, preserved DW draft | Paths/imports/docs/Compose/offline checks plus live capture integrity | DONE — runtime recovery/bind compatibility and all11 typed digests/control metadata reverified via DBT-SALES-01 |
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
| SALES-03 | SALES-02 + approved DW/KPI | dbt staging/core/Sales Mart/basic DQ | DONE — runtime Sales Warehouse/DQ/marts via DBT-SALES-01; [evidence](dbt/README.md) |
| SALES-04 | SALES-03 | Power BI + repeatable Sales demo | TODO |
| NEXT-01 | Sales evidence | SCD2, Customer/Inventory, Airflow, advanced recovery per roadmap; incremental Sales hoàn tất riêng tại INGEST-INCR-01 | TODO |

Current Full Load runtime accepted for unpublished candidates; [counts/evidence](ingestion/README.md#ingest-010203--runtime-acceptance-2026-11-19). WWI-05/06 parent/phase closure remains Owner review; no automatic transition or downstream implementation. Publication remains NOT RUN.

Nghiệm thu kỹ thuật DBT-SALES-01 chỉ áp dụng local Sales transformations chưa publish; Power BI/Airflow/domain khác/Certified publication và đóng phase vẫn ngoài task.
