# B9 Minimal Precision PoC

## Purpose và scope

Task **DW-03A/B9 PoC** kiểm chứng SQL Server F2 → pyodbc str/None → psycopg TEXT parameters → isolated test-only table → commit/close/reconnect/read-back. Current Resume authorization cho phép một sandbox B9 và bounded test writes; không production ingestion/Raw schema/SCD2. A05 vẫn PoC Direction Only; **B9 Approved — Physical Raw Temporal Representation**, **DW-03A DONE — Design**. Whole Raw schema/index/retention/runtime còn separate gates.

## Responsibilities

Giữ nguyên F2 từ evidence section 5.1; validate exact value/type/27 ASCII characters/seven digits/NULL, SQL typed reverse equality và Python/source ordering. Fail fast khi exactness mismatch; không sửa input hoặc fallback formatter. Tách historical SQL PASS, live DBAPI transport, PostgreSQL parameter và persistence evidence.

## Inputs và outputs

- Input: approved TCP endpoint, 14 synthetic fixture constants và bounded current/history period fields. Không đọc contact/financial payload; không tự gán business-effective time hoặc timezone.
- Output: console summary và raw JSON trong ignored `.venv`, gồm executed SQL/parameters, expected/actual fixture values, 169 comparison rows, 18 sampled cells, driver versions và status. Không log credentials/principal name hoặc xuất source dataset vào Git.
- Mỗi lần chạy chọn output filename mới; script từ chối overwrite. JSON raw chỉ là local evidence, không production storage.

## Technology và dependencies

Existing Windows x64/CPython 3.12.10, ODBC Driver 18; `pyodbc==5.5.0` trong project-local `.venv`. Chỉ dùng standard-library unittest cho offline tests; không thêm pytest/framework. Requirements chỉ cho environment PoC, không pipeline dependency decision.

PostgreSQL current Resume: dedicated `retail-b9-pg-poc`, localhost55433, database `b9_precision_poc`; psycopg/psycopg-binary3.3.9 đã có trong venv. **Target transport/persistence PASS trong tested scope**; credentials ở ignored `.venv/b9-pg-connection.json` và `.venv/b9-pg.env`, không code/logs/Git. Các blocker ở hồ sơ phía dưới là lịch sử trước Resume.

## Folder structure

- `poc.py`: source SELECT experiment và opt-in sandbox-only target path với `--pg-config`; không production pipeline.
- `test_poc.py`: negative controls và F2 document-expression contract.
- `requirements.txt`: exact authorized pyodbc và psycopg binary-extra dependencies, chỉ trong venv.
- `README.md`: scope/execution/acceptance/status.

## Execution

Chạy từ repository root, chỉ sau khi có task authorization tương ứng. `.venv/` và `__pycache__/` đã được `.gitignore` bảo vệ. Không overwrite venv của việc khác. Các lệnh đầu đã chạy thành công trong task này; không cần lặp install khi môi trường đã có.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: pyodbc==5.5.0
.\.venv\Scripts\python.exe -m unittest discover -s tests/integration/b9_precision -p 'test_*.py' -v
.\.venv\Scripts\python.exe tests/integration/b9_precision/poc.py --server 'tcp:DESKTOP-OBDFK6B,1433' --output '.venv/b9-source-results.json'
```

`tcp,1433` trong task được đối chiếu với verified endpoint ở [evidence](../../../docs/data-models/wwi-dw-03a-evidence-approval-readiness.md); không đoán host mới. Source connection cố định Driver 18, WideWorldImporters, Windows Integrated Authentication, Encrypt=yes, TrustServerCertificate=no; không bypass. Login timeout5s/query timeout20s; autocommit SELECT, ODBC read-only access-mode request. Client read-only hint không thay database-enforced permission; actual interactive principal có sysadmin, không dùng quyền đó để writes hoặc coi G02 đạt.

Không truyền `--pg-config`: chỉ source path, PG NOT RUN. Truyền config: validate localhost/dedicated sandbox/database/account trước writes; parameter/equality/length, commit/reconnect/read-back, ordering/range/NULL/occurrence checks phải đạt mới target PASS. Exit1 khi precision/test FAIL, exit2 khi connectivity/environment BLOCKED; raw phase/status giữ failed evidence. Không lấy exit0 làm B9 approval. Không tự discovery/connect service khác, normalize timestamp hoặc bỏ qua failure.

## Testing và acceptance criteria

1. Offline: F2 phải khớp whitespace-normalized expression trong design; altered seventh digit, dropped digits, bytes/non-string/string NULL/non-ASCII formats và missing/duplicate ordering pairs phải bị phát hiện.
2. Live fixtures: 14/14, gồm 13 strings len27 và None; expected literal phải bằng source F2/Python, nanosecond/source typed reverse phải đúng.
3. Live ordering: 13×13=169 pairs đủ population, Python lexical order = source datetime2 order = source F2 binary-collation order.
4. Actual temporal samples: exact Python value đối chiếu independent source prefix/nanosecond components và typed reverse; giữ sentinel/zero-duration. Mẫu không chứng minh toàn history hoặc common extraction context; selectors có thể lặp source occurrence.
5. Không authoritative datetime/float conversion hoặc source writes; target writes/one test-only TEXT table chỉ trong approved isolated sandbox. Không production Raw schema/B9 approval/DW-03A closure.

## Source-only status trước Resume — 2026-11-15 (lịch sử)

**Implemented and Tested: isolated SQL-to-Python subset only.** 8 unittest methods PASS; 14/14 live fixtures, 169/169 ordering pairs, 18/18 actual temporal cells PASS. Installed packages: pip25.0.1 và pyodbc5.5.0; ODBC getinfo driver18.06.0002, DBMS17.00.1000. PostgreSQL parameters BLOCKED; persistence NOT RUN. Không có exactness FAIL mới. F1 zero-fraction fixed-width FAIL là prior evidence, không bị đổi thành PASS hoặc chạy như F2.

Chi tiết source expected/actual tại [Evidence report section12](../../../docs/data-models/wwi-dw-03a-evidence-approval-readiness.md). Đoạn Actual status trên là vòng source-only trước task PostgreSQL; latest target readiness dưới đây. `.venv/b9-source-results.json` giữ nguyên, không được Git track; không commit/push.

## PostgreSQL preflight — BLOCKED trước Resume, 2026-11-15 (lịch sử)

Owner cho phép reuse venv, install psycopg3.3.9 và dùng approved existing PG sandbox hoặc tạo isolated official postgres:18 Docker sandbox **nếu Docker đã functioning**; test-only TEXT/C-collation table và bounded INSERT/commit/reconnect/read-back nằm trong authorization hiện tại. Không production Raw schema hoặc final B9 approval.

Actual install command:

```powershell
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: 'psycopg[binary]==3.3.9'
```

Installed: psycopg3.3.9, psycopg-binary3.3.9, typing_extensions4.16.0, tzdata2026.6; existing pyodbc5.5.0/pip25.0.1 giữ nguyên. Psycopg import PASS, pq implementation=binary, libpq version integer180004; **không phải PostgreSQL server version**. Global interpreter find_spec('psycopg') vẫn None. Không thêm framework/pip upgrade/global packages.

Preflight: Docker CLI29.8.2/build7fc2dff có trên PATH; `docker info --format '{{.ServerVersion}}|{{.OSType}}'` và `docker ps -a --format '{{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}'` không lấy được server/container state: `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`. Không approved target profile khác trong inspected repo/process scope. Task yêu cầu dừng target-dependent tests khi Docker unavailable và không target khác, nên không start/reconfigure Docker, pull image, tạo container/volume/database/table, INSERT, hoặc remove tài nguyên.

Đã chạy lại eight offline tests PASS và source-only integration PASS: 14/14 fixtures,169/169 ordering pairs,18/18 cells. Command reuse như trên với output mới `.venv/b9-source-pg-preflight-results.json`; previous raw file không overwrite. Source runner sửa blocker message để không nói sai psycopg chưa cài; nó không phải target-test runner.

PG str/NULL/27chars/seven digits/min/max/sentinel/100ns/order/range/collision, commit-close-reconnect/read-back/multiple occurrences: **NOT RUN — BLOCKED by infrastructure**, không executed precision FAIL. Actual PG server version/encoding/collation, unique container/volume/name/port binding: Unverified/Not created; không suy từ client library hoặc planned postgres:18 tag. Target PoC implementation/testing chưa hoàn tất; không claim target transport/persistence verified.

**Exact requirement để tiếp tục:** Docker Desktop Linux engine đã chạy và `docker info` trả Server thành công, hoặc Owner cung cấp approved existing PG sandbox profile qua excluded local config. Với Docker functioning, kiểm lại unique name/port, ưu tiên bind127.0.0.1:55433 nếu available, official postgres:18, credentials excluded; tạo đúng một test-only table/insert synthetic fixtures và giữ resources sau tests theo authorization hiện có. Không cài Docker hoặc sửa existing PG installations. B9 Pending Physical Approval/DW-03A IN_PROGRESS, không commit/push/DW-03B/C. Latest evidence/assessment section13 ghi blocker và QA.

## Resume PostgreSQL PoC trước scoped physical approval — verified evidence (lịch sử)

**B9 target transport and sandbox persistence PoC verified within the tested scope.**

Sandbox: container retail-b9-pg-poc, volume retail-b9-pg-poc-data, bind **127.0.0.1:55433→5432**, database b9_precision_poc, dedicated account b9_poc. Existing mage-demo-main_pgdata không dùng/sửa/xóa. Official image postgres:18, digest sha256:2ea8630df176ad090ec92136dee850397c5af8781e4bcf2e4162593691c61bbc; mount /var/lib/postgresql theo [official image guidance](https://hub.docker.com/_/postgres).

Actual server **PostgreSQL18.7**, UTF8, database lc_collate/lc_ctype **en_US.utf8**, libc provider. Temporal test columns **TEXT COLLATE "C"**; database default và final Raw schema không đổi. Dependencies đã có, không install/upgrade packages ở vòng Resume.

Commands đã thực hiện bằng argv, không passwords trong argv/log:
```powershell
docker pull postgres:18
docker volume create --label project=retail-b9-poc retail-b9-pg-poc-data
docker run -d --name retail-b9-pg-poc --label project=retail-b9-poc --env-file .venv/b9-pg.env --publish 127.0.0.1:55433:5432 --mount type=volume,src=retail-b9-pg-poc-data,dst=/var/lib/postgresql postgres:18
docker exec retail-b9-pg-poc pg_isready -U b9_poc -d b9_precision_poc
.\.venv\Scripts\python.exe -m unittest discover -s tests/integration/b9_precision -p 'test_*.py' -v
.\.venv\Scripts\python.exe tests/integration/b9_precision/poc.py --server 'tcp:DESKTOP-OBDFK6B,1433' --pg-config '.venv/b9-pg-connection.json' --output '.venv/b9-pg-complete-results-v2.json'
```

Credentials random trong new ignored .venv/b9-pg.env và .venv/b9-pg-connection.json; resource audit ở .venv/b9-pg-sandbox-audit.json không secret. Không overwrite credential files hoặc dump Docker Config.Env. Các create commands chỉ dùng khi tên/volume chưa tồn tại; không tự replay để ghi đè resources. Test rerun dùng config đã approved và output filename mới; append UUID batch, không truncate/drop/delete.

Test-only public.b9_temporal_text_poc có fixture_id/canonical_temporal_text/expected_temporal_text/test_batch_id, PK(batch,fixture), không timestamp unique key. Persist original14 synthetic fixtures + synthetic V1_SECOND_OCCURRENCE; không actual Customer data. **12 unit methods PASS**, source14/169/18 PASS, PG14 parameter cases PASS, persisted15 records PASS qua explicit commit/closed writer/new backend92→93; ordering169/equality14/range5/NULL/boundaries/sentinel/100ns/shared occurrences PASS.

First target attempt failed metadata SQLSTATE42704 trước value tests/writes: lc_collate không là configuration parameter. Giữ failed .venv/b9-pg-complete-results.json, sửa query dùng pg_database, không sửa source/value. Successful .venv/b9-pg-complete-results-v2.json giữ commands/parameters/expected/actual/backend/commit proof, SHA-256 52837bd1f0af1b8be0e16229a032577040625b9f77ae31f5fe3a43ee2313d05e. Không precision discrepancy bị normalize/che giấu.

Container/volume/committed rows **giữ lại running**, không cleanup. Test scope không gồm server hard-restart/container-recreation durability, full Raw/production privileges hoặc publication/recovery. G04/G05 có bounded proof; final datatype/adapter/encoding/collation/B9 physical approval và các gates còn lại chưa close. B9 Pending Physical Approval/DW-03A IN_PROGRESS; không commit/push/DW-03B/C. Full evidence/assessment tại section14.


## Current B9 physical approval / DW-03A design acceptance — 2026-11-15

Owner task “DW-03A — B9 Physical Approval & Final Design Acceptance Review” approve **F2→Python str/None→parameterized psycopg→authoritative Raw PostgreSQL TEXT**,COLLATE C khi canonical comparison/order,fixed27/seven digits,NULL/min/max/sentinel/100ns giữ nguyên,source system-time không business-effective. Native datetime/lower precision timestamp không replace authority;derived timestamp/search forms chỉ secondary. [ADR-SCD-05](../../../docs/adr/scd-05-exact-temporal-precision.md) giữ ten rules/exclusions;prior Pending statements phía trên là history.

Actual current rerun12 unit/source14-169-18/PG14 parameters-15 persisted/order169/equality14/ranges5 PASS. Command như Resume nhưng output mới **.venv/b9-design-acceptance-results.json**,SHA25613d1d24790f2b95722b6e2f99369a9a7bb3e60fc31b405a9ce1f47cab40a4188,new backend150→151,batchb25689fc-e7af-4e20-91cd-2f8084120aa3. Original success/failure reports giữ nguyên;sandbox có2 batches×15=30 rows,không overwrite/delete. Environment/image/versions/commands [evidence§15](../../../docs/data-models/wwi-dw-03a-evidence-approval-readiness.md) unchanged from verified Resume.

**DW-03A DONE — Design** sau14 mandatory design checks và QA theo conditional authority. Không whole Raw DDL/index/retention/access/capacity/publication/crash-restart-recreation/performance approval. Gate G01–G08 reason/owner/stage/proof ở work plan;runtime pending,không production ingestion. WWI-04/Phase1 IN_PROGRESS,B/C/DW-04 TODO. Current task cho focused finalization commit sau QA/staged checks,no push;container/volume/credentials/data retained/ignored,không automatic cleanup hoặc task tiếp.
