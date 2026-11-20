# PostgreSQL Raw — local Compose

## Phase A — MVP-G02 Verified, 2026-11-18

Owner đã apply bootstrap ngoài task code-fix trước. Fresh readonly inspection xác nhận raw/ingestion_meta schemas owner postgres; runs/object_runs đúng22 columns, role retail_ingest không admin, Raw USAGE=true/CREATE=false, metadata SELECT/INSERT/UPDATE=true và DELETE/TRUNCATE=false trên từng bảng. App TCP checker **PASS_READONLY_CONNECTIVITY**: retail_raw/retail_ingest/PostgreSQL18.7/UTF8/C/sslmode disable. Checker dùng `pg_database.datcollate`; `lc_collate` không là runtime GUC phù hợp cho PostgreSQL18.

Sau kiểm0 RUNNING runs và0 other client backends, đã thực hiện **một** Owner-authorized restart riêng retail-raw-postgres-1 bằng immutable container ID. Trở lại healthy; same container/volume/binding127.0.0.1:55434; schema/table owners+OIDs và metadata counts [0,0] giữ nguyên, role/permissions không đổi; fresh app TCP probe PASS. Không sentinel data insertion, payload DDL/grants hoặc Full Load. **MVP-G02 DONE** cho foundation/persistence/connectivity, không whole ingestion readiness. Sections failure/recovery bên dưới giữ historical evidence; không chạy recovery lại trên initialized target.

## WWI-06B — Read-only Docker CLI verification

Latest Owner approval2026-11-18 đã cho exact Raw SQL execution: apply một lần exit0, [RAW_PAYLOAD_PROVISIONING_PASS](../postgres/README.md#wwi-06b--approved-raw-payload-provisioning-2026-11-18), target app preflight và health/TCP PASS. Operator PC/approved per-user Docker CLI/server29.8.2/Linux/context desktop-linux; same healthy container/Compose/loopback55434/retail-raw_pg_data. Không restart/recreate/volume/certificate changes, không ingestion; initializer new-only không rerun. Prior NOT APPLIED inspection giữ historical evidence.

PowerShell preparation/inspection dưới **PC**, không dùng extractor để quản lý Docker. Nếu PATH thiếu chỉ sửa current session; không system-wide PATH hoặc install/reinstall. Không dump container Env/unfiltered Compose config chứa credentials.

~~~powershell
whoami
if ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name -ine 'DESKTOP-OBDFK6B\PC') { throw 'STOP: wrong Docker operator' }
$dockerBin = 'C:\Users\PC\AppData\Local\Programs\DockerDesktop\resources\bin'
$dockerExe = Join-Path $dockerBin 'docker.exe'
if (-not (Test-Path -LiteralPath $dockerExe)) { throw 'STOP: approved Docker CLI absent' }
if (-not (Get-Command docker.exe -ErrorAction SilentlyContinue)) { $env:Path = "$dockerBin;$env:Path" }
& $dockerExe version
& $dockerExe ps -a
& $dockerExe inspect retail-raw-postgres-1 --format '{{.Id}}|{{.Config.Image}}|{{json .Config.Labels}}|{{json .NetworkSettings.Ports}}|{{json .Mounts}}|{{if .State.Health}}{{.State.Health.Status}}{{end}}'
& $dockerExe volume inspect retail-raw_pg_data --format '{{.Name}}|{{json .Labels}}'
~~~

Dùng JSON Mounts để xem cả bind/volume; không truy cập .Name trực tiếp trên mọi mount vì bind mount không có key đó. Commands ở runbooks startup/recovery phía dưới là task lịch sử/future authorization, không quyền thực hiện trong verification hiện tại.

## Purpose, scope và responsibilities

Quản lý PostgreSQL Raw riêng cho MVP, persistent volume và first-start bootstrap. Không quản lý SQL Server, B9, PostgreSQL native, dbt hoặc Airflow trong package này. **Foundation và Owner-approved payload schema đã runtime verified** theo evidence đầu tài liệu/Raw runbook; chưa ingestion. Bootstrap FAILED/recovery preparation bên dưới là historical context, không current failure hoặc quyền rerun.

## Inputs, outputs, dependencies và technology

[compose.raw.yaml](compose.raw.yaml) dùng official `postgres:18`, Docker Compose và biến từ root [.env.example](../../.env.example). Không Dockerfile hoặc package mới. Output tương lai: database `retail_raw`, schemas `raw`/`ingestion_meta`, non-admin role `retail_ingest` và metadata tables tại [bootstrap.sql](../postgres/bootstrap.sql). Credentials thực nằm trong ignored `.env`; không dump `docker compose config` đầy đủ ra logs.

Resource namespace: project `retail-raw`, service `postgres`, expected container `retail-raw-postgres-1`, volume `retail-raw_pg_data`, network `retail-raw_default`; host `127.0.0.1:55434`. Không dùng port5432/native service hoặc55433/B9. Volume PostgreSQL18 mount tại `/var/lib/postgresql` theo [official image](https://hub.docker.com/_/postgres); init script readonly, chỉ chạy khi data directory mới. Ghi actual image version/digest sau lần chạy thực tế; tag major18 chưa là digest pin.

## Folder structure

- [compose.raw.yaml](compose.raw.yaml): một isolated service, loopback binding, persistent volume, healthcheck và `restart: no`.
- [storage/raw](../postgres/README.md): bootstrap SQL/metadata ownership.
- [check_raw_connection.py](../scripts/check_raw_connection.py): config validation hoặc explicit readonly connectivity probe.

## Execution — lệnh chuẩn bị cho task runtime tiếp theo

Chạy từ repository root. Các lệnh startup/shutdown dưới đây **chưa được chạy hoặc được authorize trong task chuẩn bị**.

1. Owner mở Docker Desktop Linux Engine thủ công. Kiểm tra `docker context show`, `docker ps -a`, `docker volume ls`, `docker network ls` và listener55434. Nếu resource `retail-raw-*` đã tồn tại nhưng không thuộc task dự án này, STOP; không overwrite/adopt/prune. B9 và native PG giữ nguyên.
2. Tự copy `.env.example` thành ignored `.env`, điền hai password khác nhau ≥16 ký tự ngẫu nhiên đơn giản (không `$`, `#`, backslash); không gửi password qua chat. Không sửa `.venv` hoặc global packages. Port có thể đổi sang port trống khác nhưng không5432/55433; host/database/user giữ template.
3. Offline validation, không kết nối hoặc tạo resource:

```powershell
.\.venv\Scripts\python.exe infrastructure/scripts/check_raw_connection.py --env-file .env --check-config
docker compose -p retail-raw --env-file .env -f infrastructure/docker/compose.raw.yaml config --quiet
```

4. Sau explicit Owner runtime authorization cho riêng target này:

```powershell
docker compose -p retail-raw --env-file .env -f infrastructure/docker/compose.raw.yaml up -d postgres
docker compose -p retail-raw --env-file .env -f infrastructure/docker/compose.raw.yaml ps
.\.venv\Scripts\python.exe infrastructure/scripts/check_raw_connection.py --env-file .env
```

Probe dùng role `retail_ingest`, readonly transaction, kiểm database/identity/schema/metadata và no-admin flags; không nạp dữ liệu. Healthcheck sửa mới yêu cầu `pg_isready` **và** Raw/metadata schemas, hai metadata tables, non-admin login role. Existing container chưa nhận health definition mới; không tự recreate để cập nhật nó. Healthy không thay kiểm permissions/constraints/persistence và MVP-G02 evidence.

`--check-config` trước startup kiểm cả bootstrap/app passwords. Normal probe/ingestion chỉ cần app password; không cấp bootstrap `postgres` credential cho extraction runtime. Có thể truyền riêng app environment/config file ở task ingestion, không bắt runtime giữ admin secret.

5. Lệnh shutdown giữ volume, chỉ dùng khi được authorize:

```powershell
docker compose -p retail-raw --env-file .env -f infrastructure/docker/compose.raw.yaml stop postgres
docker compose -p retail-raw --env-file .env -f infrastructure/docker/compose.raw.yaml start postgres
```

Không `down -v`, delete volume, sửa B9/native hoặc tự reset sau lỗi. Bootstrap first-start-only/new identity: không chạy lại SQL mù trên initialized database. Init lỗi có thể để volume initialized nhưng thiếu bootstrap; giữ logs/state, kiểm target và đề xuất repair migration riêng. [Official image docs](https://hub.docker.com/_/postgres) mô tả giới hạn này. Thay password trong `.env` sau first init không tự đổi database role; cần task rotation riêng.

## Connection security

WWI source giữ ODBC18/Windows Integrated/`Encrypt=yes;TrustServerCertificate=no`; không sysadmin runtime. Target PostgreSQL này là **ngoại lệ local có lý do**: chỉ publish IPv4 loopback, dùng SCRAM password và `sslmode=disable` cho dev machine tin cậy; checker từ chối remote host và native/B9 ports. Không áp ngoại lệ này cho SQL Server, LAN/cloud hoặc production. PG TLS cho remote/future hardening cần cấu hình riêng; không dùng `prefer` để âm thầm fallback. Docker/OS users có quyền inspect container env nằm trong trusted local boundary đã được Owner chấp thuận.

## Testing và acceptance

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe -m unittest discover -s infrastructure/tests -p 'raw_foundation_static.py' -v
```

Tests kiểm config, secret omission, target rejection, SQL contracts và actual Compose parser với synthetic values trong memory; không start service/connect DB. Bootstrap chưa PostgreSQL compile/execute, không runtime PASS.

Historical preparation tại38d15a6: Engine unavailable. **Inspection hiện tại,2026-11-17:** container `retail-raw-postgres-1` chạy PostgreSQL18.7, port127.0.0.1:55434, volume `retail-raw_pg_data`, old healthcheck healthy. SELECT trong transaction read-only xác nhận Raw/metadata schemas/tables và `retail_ingest` đều absent. Container ingestion password nonempty nhưng min-length check FALSE; blocked-prefix FALSE. Git `.env` không tồn tại tại inspection, nên nguồn private input ban đầu/host-vs-container value equality chưa xác minh; không suy giá trị password hoặc in credentials.

## Bootstrap failure và recovery A

Root cause có ba phần: input ingestion password dưới16 ký tự bị guard từ chối đúng; bootstrap cũ dùng `\quit 1` dù psql18 không hỗ trợ exit-code argument nên kết thúc bình thường; health cũ chỉ `pg_isready`. [psql18 docs](https://www.postgresql.org/docs/18/app-psql.html) mô tả `\quit` không có argument và SQL error với ON_ERROR_STOP trả exit3. Bản sửa dùng constant `RAISE EXCEPTION`, guard missing env/default rỗng, new-only collision check và giữ transaction DDL. Không hạ password policy hoặc bỏ prefix validation. Compose mapping vẫn `RAW_PG_PASSWORD` → `RAW_PG_INGEST_PASSWORD`; container nhận đúng tên biến, không có bằng chứng lỗi `\getenv`.

**Ưu tiên A: apply corrected bootstrap vào existing database, giữ container/volume.** [recover_raw_bootstrap.py](../scripts/recover_raw_bootstrap.py) mặc định chỉ preflight; kiểm Compose labels/image/loopback/volume, dùng immutable container ID, SELECT read-only để từ chối existing target objects/custom roles. Kiểm này không chứng minh toàn bộ volume trống. `--apply` là mutation cần Owner approve riêng, không chạy trong task fix. Script lấy private app password từ explicit env file, truyền qua child process environment và Docker `--env NAME`, không password argv/logs; stale container password không được dùng lại. Không cần sửa admin password hoặc recreate container.

Exact PowerShell commands từ root cho Owner/future authorized task:

```powershell
Set-Location 'D:\Code\Retail_Data_Platform\project1_Retail_Data_platform'
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
notepad .env
# Owner tự đặt RAW_PG_PASSWORD riêng, >=16 ký tự, không placeholder prefix.
# Không gửi password qua chat; không tự đặt lại admin password của cluster đã init.
.\.venv\Scripts\python.exe infrastructure/scripts/recover_raw_bootstrap.py --env-file .env
if ($LASTEXITCODE -ne 0) { throw 'STOP: private config/target/preflight chưa đạt' }

# CHỈ SAU EXPLICIT OWNER AUTHORIZATION CHO RECOVERY A:
.\.venv\Scripts\python.exe infrastructure/scripts/recover_raw_bootstrap.py --env-file .env --apply
if ($LASTEXITCODE -ne 0) { throw 'STOP: inspect actual state; không retry mù' }

# Chỉ bỏ process-level stale app-password override, không đổi OS/system config.
Remove-Item -LiteralPath Env:RAW_PG_PASSWORD -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe infrastructure/scripts/check_raw_connection.py --env-file .env
if ($LASTEXITCODE -ne 0) { throw 'STOP: app connectivity chưa được verify' }
```

Recovery A không dùng `--check-config` global trước startup vì mode đó yêu cầu cả admin password; recovery chỉ cần private app password để tạo role mới qua existing Docker-local DBA session. Các config host/database/user/port giữ template. Sau apply, Docker Config.Env vẫn có giá trị cũ; thay `.env` hoặc exec env không tự rotate `postgres` password hay cập nhật container definition. Với future Compose recreation cần actual admin credential/config riêng, không đoán hoặc reset password.

Post-recovery permission/ownership verification, chỉ đọc, **chưa chạy để tuyên bố PASS**:

```powershell
@'
BEGIN READ ONLY;
SELECT nspname, pg_get_userbyid(nspowner) AS owner
FROM pg_namespace WHERE nspname IN ('raw','ingestion_meta') ORDER BY nspname;
SELECT tablename, tableowner FROM pg_tables
WHERE schemaname = 'ingestion_meta' ORDER BY tablename;
SELECT rolname, rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls
FROM pg_roles WHERE rolname = 'retail_ingest';
SELECT has_database_privilege('retail_ingest','retail_raw','CONNECT') AS connect_ok,
       has_database_privilege('retail_ingest','retail_raw','CREATE') AS forbidden_db_create,
       has_database_privilege('retail_ingest','retail_raw','TEMP') AS forbidden_temp,
       has_schema_privilege('retail_ingest','raw','USAGE') AS raw_usage_ok,
       has_schema_privilege('retail_ingest','raw','CREATE') AS forbidden_raw_create;
SELECT table_name,
       has_table_privilege('retail_ingest',table_name,'SELECT') AS select_ok,
       has_table_privilege('retail_ingest',table_name,'INSERT') AS insert_ok,
       has_table_privilege('retail_ingest',table_name,'UPDATE') AS update_ok,
       has_table_privilege('retail_ingest',table_name,'DELETE') AS forbidden_delete,
       has_table_privilege('retail_ingest',table_name,'TRUNCATE') AS forbidden_truncate
FROM (VALUES ('ingestion_meta.runs'),('ingestion_meta.object_runs')) AS t(table_name);
ROLLBACK;
'@ | docker exec -i retail-raw-postgres-1 psql -X -h /var/run/postgresql -U postgres -d retail_raw -v ON_ERROR_STOP=1 -f -
if ($LASTEXITCODE -ne 0) { throw 'STOP: permission verification failed' }
```

Expected: schema/table owner postgres; login true và năm administrative role flags false; các `*_ok` true, mọi `forbidden_*` false. Sau đó Owner kiểm restart/persistence khi được authorize riêng. Không coi helper exit0/healthy/count0 là complete Raw hoặc ingestion PASS.

**Failure/rollback:** DDL+role/grants trong một transaction; lỗi trước commit rollback khi session đóng. Sau successful/ambiguous commit không tự DROP/REVOKE/retry: re-inspect role/schema/permissions; helper new-only sẽ từ chối rerun. Existing object/data → review migration riêng, không `IF NOT EXISTS` che drift. Không có automatic postcommit rollback vì chưa biết dependencies/usage.

**Option B — không chọn hiện tại:** chỉ reinitialize exact container `retail-raw-postgres-1` và volume `retail-raw_pg_data` sau separate Owner approval, inventory mọi database/objects và xác nhận không valuable data hoặc có verified backup/restore plan. Empty app table list không chứng minh volume rỗng. Xóa volume sẽ mất toàn cluster (cả postgres DB, roles/settings/objects ngoài Raw); không rollback nếu không có backup hợp lệ. Không broad prune hoặc thao tác B9/native. Task này không cung cấp automatic deletion/recreation runner và chưa tạo backup.

Actual fix validation:22 offline Raw tests +18 SQL regression PASS; Compose parse PASS. Guard-only read-only fixtures empty/short/placeholder trả3, valid synthetic trả0; phần CREATE/GRANT không chạy. New health command đánh giá read-only trên current missing-schema database trả1 đúng; existing container health config không đổi. Full bootstrap/role creation/app authentication/permission verification vẫn **NOT RUN**; MVP-G02 **BLOCKED** tới recovery thực tế.

QA bổ sung: ba negative guard fixtures xác nhận SQLSTATE22023, không chỉ exit code; health probe không stderr lỗi SQL. Python syntax7 files,1.240 local links/anchors và secret scan đạt; đúng11 paths (10 existing+1 recovery helper),148 original files ngoài scope giữ canonical content. Phần DDL/permissions từ BEGIN đến COMMIT trong bootstrap giữ nguyên so với38d15a6; chỉ guard/failure handling đổi. Chưa `.env`/credential/backup artifact nào được tạo trong task; staged scope/blob/secret/diff checks phải đạt trước local commit, không push.

Acceptance runtime: dedicated target khởi động/khởi động lại ổn định, đúng role/encoding/collation/schema/metadata, connectivity PASS và volume giữ state; source/B9/native không đổi. FIX PREPARED/RECOVERY NOT APPLIED là trạng thái lịch sử của section này; current foundation/payload schema PASS theo evidence đầu tài liệu, không rerun recovery/provisioning. [MVP milestones](../../docs/archive/pre-reset/TASKS.md#mvp-operational-milestones) là operational checklist; [parent module](../README.md).
