# MVP-RESET-01 ? Audit v? migration

Baseline main/cf94d05; b?y dirty WWI-06C paths ?? preserve commit fb8e0f4 tr?n refactor/mvp-simplification. Tr??c refactor48 Full Load +22 Raw tests PASS.

| Ph?n lo?i | Quy?t ??nh |
|---|---|
| KEEP | Full Load/extractors/loaders/common, Raw SQL/Compose resource identities, codecs/transaction/reconciliation, source/DW/KPI/ADR contracts |
| MERGE | Dependency versions v?o root requirements.txt; existing requirements delegates; current management docs r?t g?n |
| ARCHIVE | Windows/security investigations v? prior root/ingestion status; links ???c rewrite theo destination |
| REMOVE kh?i acceptance | Dedicated SID/global all11 permission audit/ACL/manifests/TLS enterprise audits; kh?ng x?a evidence |
| Kh?ng MOVE | Kh?ng gom connectors cosmetic; existing imports/module ownership r?; kh?ng t?o dbt/incremental placeholders |

Imports production gi? nguy?n. Tests obsolete identity/archive assertions ??i sang selected SELECT/projection/schema v? explicit development security contract. Diagnostic history mode gi? opt-in ri?ng, kh?ng CLI gate. Kh?ng th?m dependency/framework.

Rollback: ??i chi?u preserve commit fb8e0f4 v? refactor commits; d?ng targeted revert sau review, kh?ng reset dirty work ho?c rollback database. Kh?ng schema/data/resource changes. Current .venv d?ng PC development account; user kh?c ph?i t?o venv ri?ng t? accessible Python. Runtime ch?a th?c hi?n.

## Validation v? runtime hi?n t?i

Source selected-object preflight Warehouse.StockItemHoldings PASS d??i current PC account v?i APP_ENV=development, trust=yes v? admin opt-in explicit; ch? SELECT metadata/TOP0, kh?ng extract payload. Target preflight/raw checker ConnectionTimeout; Docker desktop-linux engine pipe unavailable. Compose config --quiet PASS; kh?ng start/recreate resources.

107 offline tests PASS (51 Full Load,22 Raw,18 historical SQL security,12 B9,4 Raw verifier). Basic recovery/data fidelity preserved. Current Python3.12 venv ho?t ??ng d??i development account s? h?u installation; kh?ng thay/c?i global packages. User kh?c c?n venv t? interpreter accessible c?a ch?nh h?; kh?ng c?n c?n dedicated-account venv.

Remaining runtime prerequisites: Docker Desktop Linux Engine v? existing Raw container accessible, private .env ??ng target, then combined preflight; Owner giao first smoke. Kh?ng coi target timeout l? runtime PASS. No Full Load/publication/DB changes in reset.

## Placeholder consolidation

- MERGE monitoring/alerts/README.md ? monitoring/README.md
- MERGE monitoring/logging/README.md ? monitoring/README.md
- MERGE monitoring/metrics/README.md ? monitoring/README.md
- MERGE transformation/dbt/README.md ? dbt/README.md
- MERGE transformation/sql/README.md ? dbt/README.md
- MERGE orchestration/dags/README.md ? airflow/README.md
- MERGE orchestration/plugins/README.md ? airflow/README.md
- MERGE data-quality/validations/README.md ? docs/architecture/data-quality-ownership.md
- MERGE data-quality/reconciliation/README.md ? docs/architecture/data-quality-ownership.md
- MERGE infrastructure/cloud/README.md ? infrastructure/README.md
- MERGE infrastructure/local/README.md ? infrastructure/README.md
- MERGE analytics/data-marts/README.md ? powerbi/README.md
- MERGE analytics/powerbi/README.md ? powerbi/README.md
- MERGE storage/staging/README.md ? docs/archive/pre-reset/storage-module.md
- MERGE storage/warehouse/README.md ? docs/archive/pre-reset/storage-module.md
- MERGE tests/e2e/README.md ? tests/README.md
- MERGE ingestion/checkpoints/README.md ? ingestion/README.md

## Final QA

MVP_RESTRUCTURING_COMPLETE: root imports/CLI/offline tests/Compose parser/document links/secret patterns pass. Source selected read-only preflight PASS; target unavailable (Docker pipe missing), no runtime ingestion. No DB/schema/volume/certificate changes. 11 investigations moved,17 future-only READMEs merged, old management documents snapshotted; exact changed paths tracked by Git commits.
