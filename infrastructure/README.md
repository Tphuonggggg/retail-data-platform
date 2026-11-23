# Infrastructure and PostgreSQL

## Overview

Infrastructure provides the local PostgreSQL service, schema provisioning, role setup and persistence controls. The full environment connects a Windows SQL Server source to a Docker-hosted Raw Layer and Data Warehouse, with Airflow in WSL2 and Power BI Desktop as the analytics client.

Start with the [project overview](../README.md) or use the [isolated demo](#demo-environment) to explore the pipeline without SQL Server.

## System Requirements

- Windows, Python 3.12 and the pinned root [requirements](../requirements.txt).
- Docker Desktop with Linux containers and an available loopback port 55434.
- SQL Server with WideWorldImporters restored separately; ODBC Driver 18 and current-account Windows Authentication.
- Ubuntu WSL2 with a separate Airflow environment for orchestration.
- Power BI Desktop for the Import report.

The full installation includes manual provisioning steps and machine-specific source guards. It is not a one-command installer, and complete clean-machine deployment remains unvalidated.

## Environment Architecture

Windows Python handles SQL Server authentication and extraction. PostgreSQL stores typed payloads, immutable version metadata and analytical models. Airflow calls Windows Python through its WSL bridge rather than installing a second SQL Server extraction stack. Power BI reads serving schemas through a dedicated reader role.

## Docker Services

| Resource | Full environment |
|---|---|
| Compose file | [compose.raw.yaml](docker/compose.raw.yaml) |
| Project / service | `retail-raw` / `postgres` |
| Container / image | `retail-raw-postgres-1` / `postgres:18` |
| Database / endpoint | `retail_raw` / `127.0.0.1:55434` → container 5432 |
| Named volume | `retail-raw_pg_data` at `/var/lib/postgresql` |
| Encoding / locale | UTF8 / C |
| Restart policy | `no` |

Inspect existing resources before starting or provisioning them. The container and volume are independent of native PostgreSQL instances and other sandboxes. Use `config --quiet` to validate Compose without printing resolved credentials.

```powershell
# Run from the repository root; config --quiet does not print resolved secrets.
docker context show
docker info --format '{{.OSType}}'
docker compose --env-file .env -f infrastructure/docker/compose.raw.yaml config --quiet
docker inspect retail-raw-postgres-1 --format '{{.State.Status}} {{.State.Health.Status}}'
.venv\Scripts\python.exe infrastructure/scripts/check_raw_connection.py --check-config
.venv\Scripts\python.exe infrastructure/scripts/check_raw_connection.py
```

## PostgreSQL Setup

Bootstrap runs only against a new database volume. It creates foundation schemas, metadata and a non-admin ingestion role. The health check requires these objects and role properties, not just a listening PostgreSQL socket. Later scripts provision typed payloads, transformation access and incremental state functions.

Source `datetime2(7)` values use exact F2 `TEXT COLLATE "C"`; execution timestamps use timestamptz. Raw identity is run/ordinal, not an archive natural key. Successful ingestion does not automatically update `raw_current` or `raw_publications`.

## Database Schemas

| Schema | Responsibility |
|---|---|
| `raw` | Full Load payloads, incremental deltas and version-resolving state functions |
| `ingestion_meta` | Run, object, audit and version metadata |
| `dw_staging` | Staging Models and Read Version checks |
| `dq` | Data Quality violations, status and quarantine |
| `dw_intermediate` | Order and invoice headers |
| `dw_core` | Dimensions and line-level Facts |
| `sales_marts` | Five Sales Marts |
| `dbt_sales_test` | Controlled transformation test fixtures |

## Database Roles and Permissions

| Role | Access |
|---|---|
| `retail_ingest` | Non-admin payload/metadata access; no schema CREATE, DELETE or TRUNCATE |
| `retail_transform` | Owns transformation schemas; reads approved Raw/metadata inputs; cannot write Raw/publication metadata |
| `retail_bi_reader` | CONNECT, USAGE on serving schemas and SELECT on exactly five core models, two headers and five marts |

The reader has no Raw, staging, DQ, ingestion metadata or test-schema access. Its read-only default supplements object grants. Model-level grants preserve serving access across dbt replacements without broad default grants. The [Power BI guide](../powerbi/README.md#data-sources) lists the 12 serving objects.

## SQL Server Prerequisites

Restore WideWorldImporters independently; the repository distributes neither the source database nor extracted payloads. Source access is SELECT-only, using the current development account with ODBC Driver 18. The implementation checks machine, principal, instance and database identity. A new host requires a deliberate review of those guards in addition to `.env` configuration.

TLS defaults to `Encrypt=yes` and `TrustServerCertificate=no`. Explicit development trust/admin opt-ins require `APP_ENV=development` and separate authorization. Provisioning never changes source permissions or certificate stores and does not fall back to another credential.

## Environment Configuration

Copy [.env.example](../.env.example) to a private `.env` only when no configuration exists. Set distinct, non-placeholder admin and ingestion passwords of at least 16 characters. Random values without `$`, `#` or backslashes avoid Compose/Python parser differences. Keep credentials out of Git, command arguments, SQL literals and logs.

Compose maps `RAW_PG_ADMIN_PASSWORD` to `POSTGRES_PASSWORD` and `RAW_PG_PASSWORD` to `RAW_PG_INGEST_PASSWORD`. Inspect the project/container/volume names and port ownership before using the configuration.

## Initialization

### Provisioning order

Apply this sequence only to a new, reviewed target. Inventory existing databases first; retain their data and metadata.

```powershell
   docker compose --env-file .env -f infrastructure/docker/compose.raw.yaml up -d postgres
   ```

| Order | Step | Result |
|---|---|---|
| 1 | [bootstrap.sql](postgres/bootstrap.sql), normally through first container initialization | Foundation schemas, `runs`, `object_runs` and `retail_ingest` |
| 2 | [full_load.sql](postgres/full_load.sql) | 11 typed payload tables, four control tables, 11 published views and NULL publication pointer |
| 3 | [warehouse/provision.sql](postgres/warehouse/provision.sql) | `retail_transform`, six transform/test schemas and source read grants |
| 4 | [incremental.sql](postgres/incremental.sql) | Six delta tables, two metadata tables, state functions and immutable-state triggers |
| 5 | BI reader identity preparation | Non-login role available for dbt model grants |
| 6 | Authorized Full Load and version-specific dbt build | Initial candidate and analytical objects |
| 7 | BI reader access completion | Connection/schema permissions, read-only settings and private login credential |

For scripts 2–4, inspect the SQL and SHA256, confirm target/operator identity and collision guards, then apply transactionally. `provision.sql` depends on the caller's transaction wrapper. This pattern accepts only a reviewed path from the sequence; bootstrap is not a repeatable migration.

```powershell
$reviewedSql = 'infrastructure/postgres/full_load.sql'
Get-FileHash -Algorithm SHA256 -LiteralPath $reviewedSql
Get-Content -Raw -Encoding UTF8 -LiteralPath $reviewedSql |
  docker exec -i retail-raw-postgres-1 psql -X -U postgres -d retail_raw -v ON_ERROR_STOP=1 --single-transaction
if ($LASTEXITCODE -ne 0) { throw 'Provisioning failed: inspect state before any retry.' }
```

After each step, verify expected objects, types, indexes, grants and preserved metadata as well as the exit code. New-only guards reject collisions. Bootstrap raises SQL exceptions under `ON_ERROR_STOP`; an initialization failure can otherwise leave a started server with incomplete objects.

### Transform credentials

[provision_warehouse.py](scripts/provision_warehouse.py) supports `--help`, `--execute` and `--approved-sha256`. It creates a private `.local/dbt/connection.json` and enables role LOGIN after provisioning. Its container-ID and SQL-hash guards are tied to the original environment. A different installation requires a reviewed guard update or DBA execution of the SQL, not bypassing those guards.

For manual setup, provision the NOLOGIN role transactionally, set its password through interactive `psql` `\password retail_transform`, then enable LOGIN. Store the matching `password` field privately in ignored `.local/dbt/connection.json`. The [dbt runner](../dbt/README.md#running-dbt) generates invocation-specific profiles.

### BI reader bootstrap

[provision_bi_reader.sql](postgres/warehouse/provision_bi_reader.sql) is a new-role, post-model script. Because dbt grants SELECT during model creation, a fresh installation requires a two-stage application: create the non-login identity before the first build, then complete its access after models exist. Running the unchanged new-only script after precreating the identity correctly rejects the collision.

Create only the role, without schema/table grants, before dbt:

```sql
-- Reviewed new-target preparation only; execute as postgres on retail_raw.
BEGIN;
DO $$ BEGIN
  IF current_database() <> 'retail_raw' OR current_user <> 'postgres' THEN
    RAISE EXCEPTION 'Wrong database or operator';
  END IF;
END $$;
CREATE ROLE retail_bi_reader NOLOGIN NOINHERIT
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
COMMIT;
```

After dbt applies model-level SELECT grants on the 12 serving objects, complete the connection/schema/settings package on the same target:

```sql
BEGIN;
GRANT CONNECT ON DATABASE retail_raw TO retail_bi_reader;
GRANT USAGE ON SCHEMA dw_core, dw_intermediate, sales_marts TO retail_bi_reader;
ALTER ROLE retail_bi_reader IN DATABASE retail_raw SET default_transaction_read_only = on;
ALTER ROLE retail_bi_reader IN DATABASE retail_raw
  SET search_path = pg_catalog, dw_core, sales_marts, dw_intermediate;
COMMIT;
-- In an interactive trusted psql session, not a password literal:
\password retail_bi_reader
-- Only after successful password configuration:
ALTER ROLE retail_bi_reader LOGIN;
```

Verify password login, SELECT on all 12 objects and absence of write, DDL or unrelated read access. These steps belong to a new installation, not an existing provisioned environment. This cold-start procedure remains manual and is not validated as a complete clean-machine workflow.

## Demo Environment

[compose.demo.yaml](docker/compose.demo.yaml) defines an independent PostgreSQL 18 service:

| Resource | Demo value |
|---|---|
| Project | `retail-portfolio-demo` |
| Database / user | `retail_portfolio_demo` / `portfolio_demo` |
| Endpoint | `127.0.0.1:55439` |
| Schemas | `demo_raw`, `demo_analytics` |
| Storage | tmpfs at `/var/lib/postgresql`; no named volume |
| Private configuration | `.local/portfolio-demo/demo.env` with a generated independent password |

From the repository root, run `python -m ingestion.demo config`, then `python -m ingestion.demo run`. The entrypoint does not load `.env` or bind source/production configuration. It fixes endpoint/database/user, verifies identity and rejects protected schemas `raw`, `ingestion_meta` and `dw_core`. A port collision fails instead of selecting another target or credential. The bootstrap user has administrative rights only within this demo container; it is not a production least-privilege example.

`python -m ingestion.demo down` stops/removes the demo project without `--volumes` or pruning. Stopping the tmpfs-backed container discards its data. Inspect results first and reserve the project name/port exclusively for the demo. The [sample guide](../ingestion/README.md#sample-demo) describes fixtures and output; this isolated path does not establish full-stack clean-machine reproducibility.

## Troubleshooting

| Problem | Investigation |
|---|---|
| Connection timeout | Check Docker Engine/context, container identity, loopback binding and health |
| Empty inventory or unhealthy bootstrap | Inspect initialization logs and expected foundation objects before changing the target |
| Provisioning collision | Compare actual inventory with the intended new-target script; retain existing objects |
| Source authentication/TLS failure | Review source identity and explicit development configuration; retain grants/certificates |
| Missing BI access after rebuild | Check the 12 model grants, schema usage, role login and consistent Read Version |

## Persistence and Recovery

The named Raw volume retains data across container stops. Restart the existing container explicitly after Docker restarts; never infer that an empty table list makes its volume disposable.

[recover_raw_bootstrap.py](scripts/recover_raw_bootstrap.py) provides guarded inspection/recovery. Read `--help`, verify the exact target and obtain write authorization before applying changes. Preserve credentials and metadata, and investigate partial provisioning before retrying.

A legacy container can bind `storage/raw/bootstrap.sql`. [ensure_raw_bind.ps1](scripts/ensure_raw_bind.ps1) inspects/restores the ignored compatibility junction to `infrastructure/postgres`; the container need not be recreated for this bind. Backup/restore and destructive resets require separate target-specific authorization. Volume deletion or blanket pruning is not a recovery procedure.
