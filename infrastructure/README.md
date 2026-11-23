# Infrastructure and PostgreSQL

This module owns local PostgreSQL infrastructure, reviewed schema provisioning, connection checks and recovery. It does not run extraction or analytical transformations. Start with the [project overview](../README.md), then follow [ingestion](../ingestion/README.md) and [dbt](../dbt/README.md).

## SQL Server Prerequisite

Obtain and restore WideWorldImporters separately; the source database is not distributed in Git. The reviewed local setup uses Windows Authentication, ODBC Driver 18 and `WideWorldImporters` on `DESKTOP-OBDFK6B\SQLEXPRESS` through the configured TCP endpoint. Source access is SELECT-only.

The extractor/configuration contains machine, principal, instance and database guards. A new machine requires a deliberate review of those guards, not just editing `.env`. Strict source TLS is the default. Explicit trust/admin opt-ins are limited to the approved local development configuration; provisioning never changes source permissions or certificates automatically.

## PostgreSQL Target and Persistence

| Setting | Local implementation |
|---|---|
| Compose file | [docker/compose.raw.yaml](docker/compose.raw.yaml) |
| Project / service | `retail-raw` / `postgres` |
| Container / image | `retail-raw-postgres-1` / `postgres:18` (verified server 18.7) |
| Database / endpoint | `retail_raw` / `127.0.0.1:55434` → container 5432 |
| Dedicated volume | `retail-raw_pg_data`, mounted at `/var/lib/postgresql` |
| Encoding / locale | UTF8 / C |
| Restart policy | `no`; explicitly start the existing container after Docker restarts |

Docker Desktop must use the Linux Engine. This is separate from native PostgreSQL and the B9 sandbox. Retain the named volume; an empty table list does not establish that it is disposable.

```powershell
# Run from the repository root; config --quiet does not print resolved secrets.
docker context show
docker info --format '{{.OSType}}'
docker compose --env-file .env -f infrastructure/docker/compose.raw.yaml config --quiet
docker inspect retail-raw-postgres-1 --format '{{.State.Status}} {{.State.Health.Status}}'
.venv\Scripts\python.exe infrastructure/scripts/check_raw_connection.py --check-config
.venv\Scripts\python.exe infrastructure/scripts/check_raw_connection.py
```

## New Environment Initialization

These are operator instructions for a reviewed new target, not commands executed by a documentation check. Existing databases must be inventoried before any migration. Never recreate/reset a working volume to fix connectivity.

1. Copy [.env.example](../.env.example) to private `.env` only if it does not exist. Supply **different**, non-placeholder admin/ingestion passwords, each at least 16 characters. Simple random values without `$`, `#` or backslashes avoid differences between the Compose and Python parsers. Do not commit or print them.
2. Verify port/container/volume names are unused or belong to the intended installation. On a genuinely new target, start Compose:

   ```powershell
   docker compose --env-file .env -f infrastructure/docker/compose.raw.yaml up -d postgres
   ```

   Compose passes `RAW_PG_ADMIN_PASSWORD` as `POSTGRES_PASSWORD` and `RAW_PG_PASSWORD` as `RAW_PG_INGEST_PASSWORD`. The read-only bootstrap bind runs only on a new database volume. Health checks require the foundation objects and a non-admin ingestion role, not merely an accepting PostgreSQL socket.
3. Review and apply the following SQL in order. Check target/operator identity, file SHA256, collision guards and exit status for each step.

| Order | Script | Creates / changes |
|---|---|---|
| 1 | [postgres/bootstrap.sql](postgres/bootstrap.sql) | `raw`, `ingestion_meta`, `runs`, `object_runs`, `retail_ingest`; normally run by first Compose initialization |
| 2 | [postgres/full_load.sql](postgres/full_load.sql) | 11 typed payload tables, four control tables, 11 published views and NULL publication pointer |
| 3 | [postgres/warehouse/provision.sql](postgres/warehouse/provision.sql) | `retail_transform`, six transform/test schemas and source read grants; must precede incremental grants |
| 4 | [postgres/incremental.sql](postgres/incremental.sql) | Six delta tables, two metadata tables, state functions and immutable-state triggers; requires the transform role |
| 5 | BI role preparation, below | Create the reader identity before dbt applies model-level grants |
| 6 | Authorized Full Load, then dbt build | Explicit run/version; see module commands, never infer latest |
| 7 | BI access completion, below | Connection/schema permissions, read-only defaults and private password |

For reviewed scripts 2–4, this PowerShell pattern uses the existing container's local administrative connection. Inspect the transaction first; `provision.sql` relies on the caller to wrap it in a transaction. Substitute only a reviewed path from the table. Do not use this to rerun bootstrap or apply arbitrary scripts.

```powershell
$reviewedSql = 'infrastructure/postgres/full_load.sql'
Get-FileHash -Algorithm SHA256 -LiteralPath $reviewedSql
Get-Content -Raw -Encoding UTF8 -LiteralPath $reviewedSql |
  docker exec -i retail-raw-postgres-1 psql -X -U postgres -d retail_raw -v ON_ERROR_STOP=1 --single-transaction
if ($LASTEXITCODE -ne 0) { throw 'Provisioning failed: inspect state before any retry.' }
```

Do not claim a migration passed from exit status alone: verify expected objects, types, indexes, grants and preserved metadata. New-only guards deliberately refuse collisions. Bootstrap errors raise a SQL exception under `ON_ERROR_STOP`; PostgreSQL initialization can otherwise leave a started server after an init failure.

### Transform Credentials and Local Wrapper

[provision_warehouse.py](scripts/provision_warehouse.py) supports `--help`, `--execute` and `--approved-sha256`. It creates a separate transform password/private `.local/dbt/connection.json` and enables LOGIN after provisioning. It is pinned to the original reviewed container ID and SQL hash: **it is not a portable first-install wrapper**. A new container needs a reviewed guard update or DBA execution of the SQL, not a bypass of the guard.

For manual setup, provision the NOLOGIN role transactionally, set its password via interactive `psql` `\password retail_transform`, then enable LOGIN only after password setup. The runner requires an ignored `.local/dbt/connection.json` object with a `password` field matching that role. Prepare it privately without echoing the value; do not place passwords in SQL, command arguments or shell history. The generated dbt profile is described in [dbt setup](../dbt/README.md).

### BI Role Bootstrap Ordering

The checked-in [provision_bi_reader.sql](postgres/warehouse/provision_bi_reader.sql) is a **new-role, post-model** script. Current dbt configuration already grants SELECT to that role, so running the script unchanged only after a first build creates a bootstrap ordering conflict on a clean machine.

Use a DBA-reviewed two-stage application of the same permission package for a fresh installation: create only the non-login identity before dbt, then apply the connection/schema/settings portion after models exist. Do not run the new-only full script after precreating the role; its guard will correctly reject it. The pre-build identity has no table/schema grants:

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

After the build has applied model-level SELECT grants on exactly the approved 12 objects, the DBA completes this package on the same verified target:

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

Verify actual password login, SELECT on all 12 objects and absence of write/DDL/out-of-scope read access. The existing environment is already provisioned; do not apply this preparation there. This manual cold-start path is documented, not newly runtime-tested or automated in this task.

## Permissions and Storage Contracts

- `retail_ingest`: non-admin payload/metadata access, no schema CREATE, DELETE or TRUNCATE.
- `retail_transform`: owns transformation schemas, reads approved Raw/metadata inputs, cannot write Raw/publication metadata; ordinary dbt build uses this role.
- `retail_bi_reader`: CONNECT, USAGE on three serving schemas, SELECT on exactly five core models, two headers and five marts. No Raw, staging, DQ, metadata or test access; read-only default is additional defense, not a substitute for grants.

See the [12-object list](../powerbi/README.md). Model-level grants preserve access across dbt replacements; no broad default/project-level grants are required.

Source `datetime2(7)` values use F2 `TEXT COLLATE "C"`; execution timestamps use timestamptz. Raw identity is run/ordinal, not archive natural-key uniqueness. A successful candidate is not automatically published through `raw_current` or `raw_publications`.

## Recovery

Inspect Engine/context, exact container identity, port, health and inventory first. [recover_raw_bootstrap.py](scripts/recover_raw_bootstrap.py) provides guarded inspection/recovery; read `--help` and obtain the required write approval before applying. Preserve credentials and existing metadata.

A legacy existing container may still bind `storage/raw/bootstrap.sql`. [ensure_raw_bind.ps1](scripts/ensure_raw_bind.ps1) can inspect/restore the ignored compatibility junction to canonical `infrastructure/postgres`; do not recreate the container just to change that historical bind.

After any failed provisioning, investigate partial state before another attempt. Prefer a reviewed manual correction to deleting a volume. Backup/restore and destructive reset need separate target-specific authorization; there is no broad volume-prune recovery procedure. Existing scripts do not constitute a tested one-command cold deployment on another machine.

## Isolated Portfolio Demo

[compose.demo.yaml](docker/compose.demo.yaml) dùng project `retail-portfolio-demo`, PostgreSQL 18, database `retail_portfolio_demo`, user `portfolio_demo`, loopback port **55439**, schemas `demo_raw`/`demo_analytics`. Không đọc `.env`, không bind source/config production, không dùng named volume; PGDATA ở tmpfs `/var/lib/postgresql`. User khởi tạo có quyền admin **chỉ trong container demo riêng**, không chứng minh production least privilege. Credential ngẫu nhiên độc lập ở ignored `.local/portfolio-demo/demo.env`.

Từ root chạy `python -m ingestion.demo config`, sau đó `python -m ingestion.demo run`. Lệnh `up --wait` chỉ khởi động service demo; cổng đang bị chiếm sẽ fail thay vì chuyển sang target khác. Python cố định endpoint/database/user, kiểm tra identity và từ chối nếu có schema `raw`, `ingestion_meta` hoặc `dw_core`. Không fallback credential. dbt profile demo được tạo từ template riêng và không tham chiếu Raw/metadata live. Không chạy Compose Raw trong quá trình demo.

`python -m ingestion.demo down` dừng/xóa resource của riêng project demo, không gọi `--volumes`, `prune` hay xóa database hiện hữu. Vì tmpfs, dừng container làm mất fixture; chạy lại tạo fresh demo. Nếu cần inspect output, thực hiện trước khi down. Không dùng cùng project name/cổng cho dịch vụ cá nhân khác. Lượt này đã kiểm chứng startup/build/no-change/rollback/recovery/output và teardown trên Docker Linux local; chưa kiểm chứng full stack trên máy sạch.
