# Retail Data Platform

Portfolio Data Engineering: WWI SQL Server ? Python ? PostgreSQL Raw ? dbt DW/Marts ? Power BI. ?u ti?n Sales end-to-end; incremental/SCD2/Customer/Inventory/Airflow/cloud ? milestones sau.

**Implemented:** Full Load CLI, typed batched SELECT/COPY, run metadata, count/digest reconciliation, rerun/rollback; Raw PostgreSQL18.7 ?? provision. **FULL_LOAD_RUNTIME_ACCEPTED ? 11 objects/939208 rows, unpublished candidates; [runtime evidence](ingestion/README.md#ingest-010203--runtime-acceptance-2026-11-19).** dbt/DW/marts/Power BI/Airflow ch?a tri?n khai.

## Setup local

D?ng Python3.12 c?i cho ch?nh development account (ho?c installation d?ng chung ???c c?p quy?n), kh?ng d?ng venv t?o b?i user kh?c. Kh?ng c?n runas. ODBC Driver18 ph?i c? s?n. Root requirements.txt l? ngu?n phi?n b?n duy nh?t; unittest stdlib, ch?a th?m dbt/Airflow dependencies.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

N?u .venv ?? t?n t?i: ki?m `pyvenv.cfg` v? interpreter tr??c, kh?ng ghi ??/x?a t? ??ng. ?i?n private Raw credentials v?o .env. Windows Auth d?ng current account. Default TLS Encrypt=yes/trust=no; local self-signed c? th? explicit APP_ENV=development + trust=yes. Account admin ch? d?ng khi explicit WWI_ALLOW_ADMIN_SOURCE=yes trong development; summary hi?n th? opt-in.

## L?nh v?n h?nh

```powershell
docker compose --env-file .env -f infrastructure/docker/compose.raw.yaml config --quiet
# Ch? khi c?n kh?i ??ng service; kh?ng reset volume ho?c rerun initialization:
docker compose --env-file .env -f infrastructure/docker/compose.raw.yaml up -d
.venv\Scripts\python.exe -m ingestion.full_load config --env-file .env
.venv\Scripts\python.exe -m ingestion.full_load plan --object Warehouse.StockItemHoldings
.venv\Scripts\python.exe -m ingestion.full_load connectivity --object Warehouse.StockItemHoldings --env-file .env
.venv\Scripts\python.exe -m ingestion.full_load preflight --object Warehouse.StockItemHoldings --env-file .env
```

Compose project retail-raw/volume retail-raw_pg_data/localhost55434 gi? nguy?n. Native PostgreSQL v? B9 kh?ng li?n quan. Existing Raw ?? provision; kh?ng ch?y bootstrap/full_load.sql l?i.

L?nh t??ng lai sau khi Owner giao runtime smoke (reset KH?NG ch?y):

```powershell
$run = [guid]::NewGuid().ToString()
.venv\Scripts\python.exe -m ingestion.full_load load --object Warehouse.StockItemHoldings --batch-size 64 --run-id $run --execute --env-file .env
.venv\Scripts\python.exe -m ingestion.full_load reconcile --object Warehouse.StockItemHoldings --run-id $run --env-file .env
```

Kh?ng --publish cho selected smoke. Unknown commit ? inspect run ID, kh?ng auto retry/delete. [Chi ti?t ingestion](ingestion/README.md).

## Tests

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p '*offline.py'
.venv\Scripts\python.exe -m unittest discover -s tests -p raw_foundation_static.py
```

## ?i?u h??ng

[Scope](PROJECT_SCOPE.md) ? [Roadmap](ROADMAP.md) ? [Tasks](TASKS.md) ? [Source/DW models](docs/data-models/README.md) ? [KPI](analytics/kpi-definitions/wwi-kpi-candidate-catalog.md) ? [Architecture](docs/architecture/system-overview.md) ? [Historical archive](docs/archive/pre-reset/README.md) ? [Reset plan](docs/mvp-reset-plan.md).

Module ownership: ingestion=extract/load; storage=SQL Raw/target definitions; transformation=dbt/SQL t??ng lai; orchestration=DAGs; analytics=marts/KPI/report; scripts=diagnostics; tests=verification. Gi? c?u tr?c hi?n h?u, kh?ng ??i folder ch? ?? gi?ng template.
