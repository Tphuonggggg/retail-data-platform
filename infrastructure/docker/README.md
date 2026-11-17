# PostgreSQL Raw — local Compose

## Purpose, scope và responsibilities

Chuẩn bị PostgreSQL Raw riêng cho MVP; quản lý service, persistent volume và first-start bootstrap. Không quản lý SQL Server, B9, PostgreSQL native, dbt hoặc Airflow trong package này. **PREPARED / OFFLINE TESTED; runtime NOT RUN.** Chỉ chạy sau Owner cho phép runtime riêng.

## Inputs, outputs, dependencies và technology

[compose.raw.yaml](compose.raw.yaml) dùng official `postgres:18`, Docker Compose và biến từ root [.env.example](../../.env.example). Không Dockerfile hoặc package mới. Output tương lai: database `retail_raw`, schemas `raw`/`ingestion_meta`, non-admin role `retail_ingest` và metadata tables tại [bootstrap.sql](../../storage/raw/bootstrap.sql). Credentials thực nằm trong ignored `.env`; không dump `docker compose config` đầy đủ ra logs.

Resource namespace: project `retail-raw`, service `postgres`, expected container `retail-raw-postgres-1`, volume `retail-raw_pg_data`, network `retail-raw_default`; host `127.0.0.1:55434`. Không dùng port5432/native service hoặc55433/B9. Volume PostgreSQL18 mount tại `/var/lib/postgresql` theo [official image](https://hub.docker.com/_/postgres); init script readonly, chỉ chạy khi data directory mới. Ghi actual image version/digest sau lần chạy thực tế; tag major18 chưa là digest pin.

## Folder structure

- [compose.raw.yaml](compose.raw.yaml): một isolated service, loopback binding, persistent volume, healthcheck và `restart: no`.
- [storage/raw](../../storage/raw/README.md): bootstrap SQL/metadata ownership.
- [check_raw_connection.py](../../scripts/check_raw_connection.py): config validation hoặc explicit readonly connectivity probe.

## Execution — lệnh chuẩn bị cho task runtime tiếp theo

Chạy từ repository root. Các lệnh startup/shutdown dưới đây **chưa được chạy hoặc được authorize trong task chuẩn bị**.

1. Owner mở Docker Desktop Linux Engine thủ công. Kiểm tra `docker context show`, `docker ps -a`, `docker volume ls`, `docker network ls` và listener55434. Nếu resource `retail-raw-*` đã tồn tại nhưng không thuộc task dự án này, STOP; không overwrite/adopt/prune. B9 và native PG giữ nguyên.
2. Tự copy `.env.example` thành ignored `.env`, điền hai password khác nhau ≥16 ký tự ngẫu nhiên đơn giản (không `$`, `#`, backslash); không gửi password qua chat. Không sửa `.venv` hoặc global packages. Port có thể đổi sang port trống khác nhưng không5432/55433; host/database/user giữ template.
3. Offline validation, không kết nối hoặc tạo resource:

```powershell
.\.venv\Scripts\python.exe scripts/check_raw_connection.py --env-file .env --check-config
docker compose -p retail-raw --env-file .env -f infrastructure/docker/compose.raw.yaml config --quiet
```

4. Sau explicit Owner runtime authorization cho riêng target này:

```powershell
docker compose -p retail-raw --env-file .env -f infrastructure/docker/compose.raw.yaml up -d postgres
docker compose -p retail-raw --env-file .env -f infrastructure/docker/compose.raw.yaml ps
.\.venv\Scripts\python.exe scripts/check_raw_connection.py --env-file .env
```

Probe dùng role `retail_ingest`, readonly transaction, kiểm database/identity/schema/metadata và no-admin flags; không nạp dữ liệu. `pg_isready` chỉ chứng minh server nhận kết nối, không chứng minh bootstrap/schema/DQ hoàn tất. MVP-G02 cần actual probe và restart/persistence evidence, không chỉ healthy.

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
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'raw_foundation_static.py' -v
```

Tests kiểm config, secret omission, target rejection, SQL contracts và actual Compose parser với synthetic values trong memory; không start service/connect DB. Bootstrap chưa PostgreSQL compile/execute, không runtime PASS.

Observed preparation: Docker CLI29.8.2/Compose5.5.1 có sẵn, context `desktop-linux`, Engine named pipe unavailable. Native5432 đang listening, không listener55433/55434 tại thời điểm inspection; resource names/volumes **chưa xác minh được** do Engine unavailable. Không tự khởi động Docker Desktop. Owner runtime task phải recheck collisions trước `up`.

Acceptance runtime: dedicated target khởi động/khởi động lại ổn định, đúng role/encoding/collation/schema/metadata, connectivity PASS và volume giữ state; source/B9/native không đổi. Current status **PREPARED — runtime NOT RUN**. [MVP milestones](../../TASKS.md#mvp-operational-milestones) là operational checklist; [parent module](../README.md).
