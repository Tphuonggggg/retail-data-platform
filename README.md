# Retail Data Platform

**DBT_SALES_RUNTIME_ACCEPTED — 2026-11-20:** 21 models (8 views/13 tables), 69 dbt tests, 129 independent reconciliation checks, 153 offline tests. [Runbook, model counts và evidence](dbt/README.md). Raw vẫn unpublished/UNVERIFIED; Power BI/Airflow chưa triển khai.

Đồ án Data Engineering: **SQL Server WWI → Python Full Load → PostgreSQL Raw → dbt DW/Marts → Power BI**. Ưu tiên Sales; incremental/SCD2/Customer/Inventory/Airflow ở milestones sau.

**Full Load đã nghiệm thu ngày 2026-11-19:** 11 objects, 939.208 dòng của run `5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8`, consistency UNVERIFIED, chưa publish. [Runtime evidence](ingestion/README.md#ingest-010203--runtime-acceptance-2026-11-19). Sales dbt Warehouse/Marts đã runtime accepted trong DBT-SALES-01; historical SCD2 và các domain ngoài Sales vẫn chưa triển khai.

## Cấu trúc theo pipeline stage

```text
ingestion/             extractors, loaders, codecs, Full Load CLI
  common/              config, source contract, fidelity/evidence
  extractors/          SQL Server SELECT-only
  loaders/             PostgreSQL COPY, metadata, reconciliation
  scripts/             source diagnostics
  tests/               ingestion unit/offline tests
dbt/                   project, staging/intermediate/core/marts, macros, tests (implemented)
airflow/               orchestration ownership; chưa có DAG/config/plugin
powerbi/               report/dashboard ownership; chưa có report assets
infrastructure/
  docker/              Compose và resource identities
  postgres/            bootstrap, Raw DDL/runbook; warehouse draft riêng
  scripts/             connection, recovery, provisioning utilities
  tests/               infrastructure offline/read-only checks
monitoring/            cross-pipeline logging/metrics/observability
docs/                  architecture, requirements/KPI, data models, ADR, archive
data-sources/          source documentation và historical security artifacts
scripts/               project-wide validation utilities
tests/                 cross-module integration, B9 và historical security tests
```

Marts SQL thuộc dbt; Power BI chỉ sở hữu báo cáo. [DQ ownership](docs/architecture/data-quality-ownership.md): checks đặt gần stage thực thi, không duy trì module rỗng song song.

## Local setup và kiểm tra

Dùng Python 3.12 của development account, ODBC Driver 18, Docker Desktop Linux Engine. Giữ .venv/.env hiện có, không ghi đè/xóa/tạo lại tự động. [requirements.txt](requirements.txt) là nguồn version duy nhất; dbt pins được bảo toàn từ draft trước refactor, không chứng minh runtime PASS. Windows Authentication dùng current development account; development TLS/admin opt-in chỉ theo Owner approval. Không in credentials/DSN.

Chạy từ repository root:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
docker compose --env-file .env -f infrastructure/docker/compose.raw.yaml config --quiet
.venv\Scripts\python.exe -m ingestion.full_load --help
.venv\Scripts\python.exe -m ingestion.full_load plan --object Warehouse.StockItemHoldings
.venv\Scripts\python.exe -m ingestion.full_load preflight --all --env-file .env
.venv\Scripts\python.exe -m ingestion.full_load reconcile --all --run-id 5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8 --env-file .env
.venv\Scripts\python.exe scripts/run_checks.py
```

Preflight/reconcile cần runtime sẵn sàng, không nạp lại/publish. [Runbook](ingestion/README.md). Không chạy lại bootstrap/full_load.sql trên database đã provision.

Compose project `retail-raw`, container `retail-raw-postgres-1`, volume `retail-raw_pg_data`, binding `127.0.0.1:55434` giữ nguyên. Bootstrap bind source nay là `infrastructure/postgres/bootstrap.sql`. Không chạy compose up/recreate chỉ để áp dụng đường dẫn mới trên container hiện có; refactor không yêu cầu restart.

## REPO-STRUCTURE-02 — ngày 2026-11-20

| Đường dẫn cũ | Đường dẫn hiện hành |
|---|---|
| `transformation/dbt/*` | `dbt/*` |
| `transformation/run_dbt.py` | `dbt/run_dbt.py` |
| `transformation/provision.py`, `provision.sql` | `infrastructure/scripts/provision_warehouse.py`, `infrastructure/postgres/warehouse/provision.sql` |
| `storage/raw/*` | `infrastructure/postgres/*` |
| `orchestration/README.md` | `airflow/README.md` |
| `analytics/README.md` | `powerbi/README.md` |
| `analytics/kpi-definitions/*` | `docs/requirements/kpi-definitions/*` |
| `scripts/inspect_wwi_source.py` | `ingestion/scripts/inspect_wwi_source.py` |
| Raw connection/recovery scripts | `infrastructure/scripts/` |
| `tests/full_load_offline.py` | `ingestion/tests/full_load_offline.py` |
| Raw foundation/provisioning tests | `infrastructure/tests/` |
| `tests/ingest_acceptance_offline.py` | `tests/integration/ingest_acceptance_offline.py` |
| `storage/README.md` | `docs/archive/pre-reset/storage-module.md` |
| `data-quality/README.md` | `docs/architecture/data-quality-ownership.md` |

CLI `python -m ingestion.full_load` không đổi. Imports/path discovery, SQL references, Markdown links và Compose bind source được cập nhật; Raw SQL/contracts và business definitions giữ nguyên. Draft DW-IMPLEMENT-01 có sẵn trước task được giữ và di chuyển, không triển khai tiếp; bản sao nguyên trạng ở `.local/repo-structure-02/preserved-dw-draft/` (ignored).

Blocker runtime của REPO-STRUCTURE-02 đã được giải quyết trong DBT-SALES-01: Docker Engine/container cũ khởi động, legacy bind path được khôi phục bằng runtime-only junction; typed digest all11 và metadata/pointer được kiểm lại nguyên vẹn. Không rerun Full Load, recreate container/volume hoặc publish. [Recovery](infrastructure/README.md#dbt-sales-01--khôi-phục-runtime-ngày-2026-11-20).

[Scope](PROJECT_SCOPE.md) · [Roadmap](ROADMAP.md) · [Tasks](TASKS.md) · [Data models](docs/data-models/README.md) · [KPI](docs/requirements/kpi-definitions/wwi-kpi-candidate-catalog.md) · [Archive](docs/archive/pre-reset/README.md).
