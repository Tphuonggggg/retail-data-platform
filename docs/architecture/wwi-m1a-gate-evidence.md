# WWI-05 / M1A — Runtime Gate & Evidence Matrix

**2026-11-16; Checkpoint B sau commit A** `554c5ea3c5eab5f9d3f5ad98f543b3739d0e0d95`. [Approval source](wwi-phase-1-closure-approval.md), [Environment](wwi-m1a-environment-readiness.md), [Contract](wwi-secure-connection-contract.md), [Handoff](wwi-m1a-handoff.md). Evidence dưới đây là actual commands/observations, không runtime suites kế thừa. Không sửa original [31-gate register](../data-models/wwi-implementation-gate-register.md).

## 1. Per-check evidence

| Check ID | Gate / requirement | Preconditions | Verification method | Expected | Observed | Evidence location | Status | Remaining action / owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1A-00 | APPROVAL-01–05 / gate A | A QA+commit | Git HEAD/parent/status | A commit trước B; tree sạch | 554c5ea3c5eab5f9d3f5ad98f543b3739d0e0d95,13 files; sạch trước B | §2 C00 | PASS | Không mở rộng scope; PO |
| M1A-01 | CG08 | Windows tools hiện có | Get-CimInstance Win32_OperatingSystem | Xác định OS/architecture | Windows11 Home Single Language;10.0.26200/build26200/64-bit | §2 C01 | PASS | Không cần thay OS; INF |
| M1A-02 | G03/CG08 | Project .venv | Python sys/platform | Interpreter/venv có sẵn | CPython3.12.10 AMD64; .venv active | §2 C02 | PASS | Chỉ reuse approved venv; IN |
| M1A-03 | G03/G06/CG08 | Không install | importlib.metadata; import drivers | Import và phiên bản xác định | pyodbc5.5.0; psycopg+binary3.3.9;6 packages tổng | §2 C02 | PASS | Production dependency declaration vẫn cần review; IN/PO |
| M1A-04 | G02/G03 | ODBC hiện có | pyodbc.drivers; connection.getinfo | Driver18 sẵn dùng | ODBC Driver18; actual18.06.0002/msodbcsql18.dll | §2 C02; §3 | PASS | Không cài driver; IN |
| M1A-05 | CG08 | Docker đã hoạt động | docker context/version/ps/volume ls | Đọc được engine/resources | desktop-linux; Engine29.8.2 linux/amd64; Desktop4.94.0 | §2 C03 | PASS | Không start/create/reconfigure resources; INF |
| M1A-06 | CG08 | Compose CLI hiện có | docker compose version --short | Xác định availability | 5.5.1; chưa có project Compose definition | §2 C03 | PASS | Có CLI không chứng minh stack tái lập; INF |
| M1A-07 | G02/CG08 | Approved historical developer endpoint | pyodbc.connect; bounded SELECT | Kết nối đúng source bằng cấu hình secure | PASS tại TCP1433,Windows Integrated; developer connection | §3 | PASS | Không dùng kết quả này làm G02 least-privilege PASS; IN/DBA |
| M1A-08 | G02 | Driver18 / Encrypt=yes / TrustServerCertificate=no | Kết nối thành công và session metadata | Encryption/TCP/certificate validation không bypass | encrypt_option TRUE; TCP; NTLM; no bypass | §3 Q_TLS | PASS | Không claim đã audit chain/expiry đầy đủ; IN |
| M1A-09 | G01/G02 | Source allowlist | SERVERPROPERTY/DB_NAME | Đúng machine/instance/database/version | DESKTOP-OBDFK6B/SQLEXPRESS/WideWorldImporters;17.0.1000.7 Express64 | §3 Q_ID | PASS | Không đổi source settings; DBA |
| M1A-10 | G02/RG02 | 11 approved populations | TOP(1) constant và HAS_PERMS_BY_NAME bound params | Đọc được mỗi table, không xuất payload | 11/11 trả1 constant;SELECT=1 cả11 | §3 population results | PASS | Không là full projection/consistency/IT01 nghiệm thu; IN/DQ |
| M1A-11 | G02 | Developer identity đang dùng | sysadmin/effective permissions metadata | Identity extraction không có write/admin | sysadmin=1,CONTROL SERVER=1; INSERT/UPDATE/DELETE=1 cả11;database ALTER=1 | §3 Q_ID/follow-up | FAIL | Tested identity không phù hợp extraction; DBA+PO phê duyệt identity khác, chưa tự thay grants |
| M1A-12 | G02/RG02/CG08 | Cần approved extraction profile | Review template/process env/connector docs | Có identity riêng, trusted profile và effective grants | Không thấy approved extraction profile trong phạm vi repo/process inspected | §2 C02/C04; §3 | BLOCKED | PO/DBA cung cấp profile/approval và least-privilege identity; không kết luận server không có login khác |
| M1A-13 | G01/RG01 | A02 no-writes/copy proof | Read-only config metadata + evidence review | Có defensible consistent source state | DB writable;SNAPSHOT OFF,RCSI/CDC/CT false; không có no-writes window/copy approval proof | §3 Q_DB | BLOCKED | SO/DBA+PO thống nhất method và evidence trước full capture; không activate settings |
| M1A-14 | CG08 / target discovery | Host/container metadata access | Services/listeners/Docker listing | Phân biệt môi trường PG có sẵn | Native postgresql-x64-18 Running,port5432; B9 container exited | §2 C03/C04 | PASS | Service name không chứng minh server version hoặc approved DB/role; INF |
| M1A-15 | G07/RG02/CG08 | Approved Raw target contract | Review repo/process profiles | Có target riêng được Owner duyệt | Chưa tìm thấy approved Raw DB/user/TLS/profile; readiness PENDING | §2 C02/C04; Secure Contract §3 | BLOCKED | PO/INF/DBA duyệt native hay isolated target contract trước provisioning/connection |
| M1A-16 | G04/G07/CG08 | M1A-15 đạt | Không mở PostgreSQL connection | Verify version/encoding/collation/user/TLS trên approved target | NOT RUN; không thử credential B9 hoặc tự dùng host5432 | §2 C04 | NOT RUN | Lặp bounded SELECT khi có approved profile; ST/DBA |
| M1A-17 | B9 / CG08 | B9 ngoài target scope | Restricted Docker inspect + local/protected hashes | Không thay B9 resources/code/evidence/credentials | exited/ExitCode0;127.0.0.1:55433 configured;volume giữ nguyên; không writes/start | §2 C03/C05; final integrity | PASS | Không restart/reuse/test B9; INF/IN |
| M1A-18 | Rule08/G02/G07 | Tracked content + known local B9 secret in memory | Pattern/known-value scans | Không secret/private key/credential URI trong Git | 129 tracked files:0 findings; không in password; principal fingerprint thay tên | §2 C05 | PASS | Không thay thế audit bảo mật đầy đủ; DQ |
| M1A-19 | Rule08 | Existing .gitignore | git check-ignore và .env.example review | Local secrets ignored; template không real secret | .env/.env.local/B9 config+env/credentials pattern ignored; .env.example5keys,4blank/1database identifier | §2 C05 | PASS | Không chỉnh ignore/template trong M1A; IN |
| M1A-20 | G02/G08/INC-06 | Accepted connector boundaries | Review B9 code và lập Secure Contract | Tách checkpoint helper khỏi production connector | B9 source có TLS/closing/params/5s-20s; target path có writes nên không chạy; production Not implemented yet | Secure Contract §4–6 | PASS | Approval future connector config/runtime values riêng; IN/ST/PO |
| M1A-21 | WWI-05 DoD / CG08 | Cần môi trường tái lập | Review requirements/templates/bootstrap/Compose | Có thể tái lập intended runtime từ repo+approved source/profile | Chỉ B9 pinned requirements; không production lockfile/Compose/bootstrap/target/extraction profile | Environment Report §5 | BLOCKED | INF/DBA/IN/PO giải quyết prerequisites trong task riêng; không install/provision |
| M1A-22 | RG10/CG01–10/B5 | Chưa có implementation/test scope | Không chạy suites | Giữ72 full scenarios NOT RUN | CD-T01–21/IT01–21/CP-T01–30 không thực thi; M1A chỉ metadata/connectivity subset | Handoff §3 | NOT RUN | Giữ original runtime acceptance trước use; DQ |
| M1A-23 | CG08 optional client | psycopg available | Get-Command/shutil.which psql | CLI tùy chọn, không cần để dùng psycopg | psql không có trên PATH; CLI SQL tests NOT RUN | §2 C01/C02 | NOT RUN | Không phải blocker độc lập khi driver đủ; không cài chỉ để đủ checklist |
| M1A-24 | B9 scope | Không cho phép B9 writes/retest | Không chạy poc.py/unittest/container exec | Giữ historical proof riêng | Không rerun transport/persistence hoặc source F2 suite | §2 C04 | NOT RUN | B9 lịch sử không production readiness proof |
| M1A-25 | APPROVAL-05 / docs QA | B deliverables đủ | Static links/secret/scope/staged/diff QA | QA PASS trước commit B | Kết quả actual QA ghi tại Environment Report §6 sau kiểm tra | Environment Report §6 | PASS | Chỉ commit sau validation đạt; không push; DQ/PO |

FAIL M1A-11 chỉ tested identity suitability, không architecture/TLS failure. BLOCKED approved profile/target khác NOT RUN target connection. PASS inventory không close G02/G07/CG08. M1A-25 chỉ có hiệu lực sau actual QA trước commit.

## 2. Command ledger và outputs

Chạy từ repo root bằng existing tools, không ghi script/runtime JSON mới hoặc sửa .venv/B9. Python snippets truyền vào existing project-local interpreter qua PowerShell here-string; sys.dont_write_bytecode=True khi import drivers, không cài package. Output được rút gọn/sanitize trong các bảng; không lưu credential/PII/source payload.

| Command group | Actual command/method | Significant output / limitation |
| --- | --- | --- |
| C00 — Governance | git branch/log/status/rev-parse; git diff-tree --no-commit-id --name-only -r HEAD | A HEAD khớp,13 paths,tree sạch trước B. Một wrapper PowerShell .Count syntax lỗi trước execution; đã sửa bằng named array rồi verify PASS, không B runtime chạy trước A verification. |
| C01 — Host | Get-CimInstance Win32_OperatingSystem; Get-Command python,py,sqlcmd,psql,docker; Get-Service; Get-NetTCPConnection -State Listen | OS và commands như Environment §2; MSSQL$SQLEXPRESS/postgresql-x64-18 Running; listener1433/5432, không55433. Initial Get-Command group exit1 vì psql thiếu; OS vẫn trả data. Availability wrapper khác có parser error, đã sửa foreach array và kết quả đúng; không system change. |
| C02 — Python/config | existing .venv Python với sys/platform/importlib.metadata.distributions; imports pyodbc/psycopg; pyodbc.drivers; psycopg.pq.version; shutil.which('psql'); inspect selected env names/template/local config markers | Python3.12.10,6 packages/versions trong Environment; no related process env names; root .env absent; B9 config marker only. Không in os.environ hoặc password. |
| C03 — Docker | docker context show; docker version --format '{{json .}}'; docker compose version --short; docker ps -a --format '{{.Names}}\|{{.Image}}\|{{.Status}}\|{{.Ports}}'; docker volume ls --format '{{.Name}}\|{{.Driver}}' | Engine29.8.2 Linux;Compose5.5.1; chỉ retail-b9-pg-poc exited,2 volume names đã ghi. Chỉ inspection. |
| C03a — B9 metadata | docker inspect --format '{{json .State}}' retail-b9-pg-poc; tương tự .HostConfig.PortBindings và .Mounts | exited,ExitCode0; StartedAt2026-11-15T10:28:36.772303443Z/FinishedAt2026-11-15T11:13:16.687223759Z;127.0.0.1:55433;retail-b9-pg-poc-data retained. Không dump .Config.Env. |
| C04 — Project review | git ls-files '*.py' '*.toml' '*requirements*' '*compose*' '.env*'; đọc .gitignore/README/requirements/B9 code; list infrastructure/local,infrastructure/docker,storage | Chỉ B9 Python/requirements; các folder hạ tầng inspected chỉ README, không project Compose/bootstrap. Native PG tồn tại không được mặc định approved target. |
| C05 — Security | Pattern scan129 tracked text files; compare known local secret in memory; git check-ignore -q --no-index cho selected secret paths; scan TLS bypass literals trong Python | 0 pattern/known-value findings; ignored paths đạt;0 explicit bypass hits trong Python. Local B9/evidence/config hashes giữ để compare cuối, không publish credential-file hashes/values. |
| C06 — Docs QA | Git diff/status; static links/anchors/secret/format/table/scope/protected hashes; staged-content/diff checks | Actual summary ghi Environment §6, không coi docs QA là runtime PASS. |

C03 command text trong table escape dấu pipe cho Markdown; actual format có pipe literal. Không thực hiện docker start/run/pull/exec/create/remove, pip install, database writes hoặc B9 tests.

## 3. Reproducible bounded SQL verification

**Đã chạy source snippet dưới đây**,2 source sessions tổng gồm follow-up;26 SQL SELECT statements tổng: identity/TLS/database3 +11×(bounded read+permission)22 + follow-up1. Chỉ fetch constant/metadata; không source business payload. No automatic retry. Không chạy lại nếu không có applicable authorization.

```python
import sys,json,hashlib,re
sys.dont_write_bytecode=True
import pyodbc
from contextlib import closing
SOURCE="tcp:DESKTOP-OBDFK6B,1433"
tables=[("Sales","Customers"),("Sales","Orders"),("Sales","OrderLines"),("Sales","Invoices"),("Sales","InvoiceLines"),("Sales","CustomerTransactions"),("Warehouse","StockItems"),("Warehouse","StockItemHoldings"),("Warehouse","StockItemTransactions"),("Sales","Customers_Archive"),("Warehouse","StockItems_Archive")]
Q_ID="""SELECT @@SERVERNAME AS server_name,DB_NAME() AS database_name,
CONVERT(varchar(128),SERVERPROPERTY('MachineName')) AS machine_name,
CONVERT(varchar(128),SERVERPROPERTY('InstanceName')) AS instance_name,
CONVERT(varchar(128),SERVERPROPERTY('ProductVersion')) AS product_version,
CONVERT(varchar(128),SERVERPROPERTY('Edition')) AS edition,
ORIGINAL_LOGIN() AS original_login,SUSER_SNAME() AS login_name,USER_NAME() AS database_user,
IS_SRVROLEMEMBER('sysadmin') AS is_sysadmin,
HAS_PERMS_BY_NAME(NULL,'SERVER','CONTROL SERVER') AS control_server,
HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','INSERT') AS database_insert,
HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','UPDATE') AS database_update,
HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','DELETE') AS database_delete,
HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','ALTER') AS database_alter,
CONVERT(varchar(33),SYSUTCDATETIME(),126) AS observed_utc"""
Q_TLS="""SELECT encrypt_option,net_transport,auth_scheme FROM sys.dm_exec_connections WHERE session_id=@@SPID"""
Q_DB="""SELECT is_read_only,snapshot_isolation_state_desc,is_read_committed_snapshot_on,is_cdc_enabled,
CASE WHEN EXISTS(SELECT 1 FROM sys.change_tracking_databases x WHERE x.database_id=d.database_id) THEN 1 ELSE 0 END AS change_tracking_enabled
FROM sys.databases d WHERE d.database_id=DB_ID()"""
Q_PERM="SELECT HAS_PERMS_BY_NAME(?,'OBJECT','SELECT') AS can_select,HAS_PERMS_BY_NAME(?,'OBJECT','INSERT') AS can_insert,HAS_PERMS_BY_NAME(?,'OBJECT','UPDATE') AS can_update,HAS_PERMS_BY_NAME(?,'OBJECT','DELETE') AS can_delete"
r={"check":"M1A-SQL","server":SOURCE,"requested_database":"WideWorldImporters","auth":"Windows Integrated","encrypt":"yes","trust_server_certificate":"no","login_timeout_seconds":5,"query_timeout_seconds":20,"client_access_mode":"read-only hint","automatic_retries":0,"queries":{"identity":Q_ID,"tls":Q_TLS,"database":Q_DB,"permission":Q_PERM},"status":"NOT RUN"}
stage="connect"
def fetch(c,q,params=()):
    c.execute(q,*params);names=[x[0] for x in c.description];return [dict(zip(names,row)) for row in c.fetchall()]
try:
    dsn="DRIVER={ODBC Driver 18 for SQL Server};SERVER="+SOURCE+";DATABASE=WideWorldImporters;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=no;"
    with closing(pyodbc.connect(dsn,autocommit=True,timeout=5,attrs_before={pyodbc.SQL_ATTR_ACCESS_MODE:1})) as conn:
        conn.timeout=20
        r["driver"]={"name":conn.getinfo(pyodbc.SQL_DRIVER_NAME),"version":conn.getinfo(pyodbc.SQL_DRIVER_VER),"dbms_version":conn.getinfo(pyodbc.SQL_DBMS_VER)}
        with closing(conn.cursor()) as c:
            stage="identity";identity=fetch(c,Q_ID)[0]
            for k in ("original_login","login_name","database_user"):
                value=identity.pop(k);identity[k+"_sha256"]=hashlib.sha256(str(value).encode()).hexdigest()
            r["identity"]=identity
            if identity["database_name"]!="WideWorldImporters" or identity["machine_name"].upper()!="DESKTOP-OBDFK6B" or identity["instance_name"].upper()!="SQLEXPRESS":raise ValueError("source allowlist mismatch")
            stage="tls";r["tls"]=fetch(c,Q_TLS)[0]
            if r["tls"]["encrypt_option"]!="TRUE" or r["tls"]["net_transport"]!="TCP":raise ValueError("TLS/TCP expectation mismatch")
            stage="database";r["database"]=fetch(c,Q_DB)[0]
            r["source_populations"]=[]
            for schema,table in tables:
                stage="bounded_read:"+schema+"."+table
                q="SELECT TOP (1) CAST(1 AS int) AS row_present FROM ["+schema+"].["+table+"]"
                sample=fetch(c,q)
                name=schema+"."+table
                perms=fetch(c,Q_PERM,(name,name,name,name))[0]
                r["source_populations"].append({"table":name,"query":q,"bounded_rows_returned":len(sample),**perms,"status":"PASS"})
        r["status"]="PASS"
        r["least_privilege_extraction"]="BLOCKED" if identity["is_sysadmin"]==1 or identity["control_server"]==1 or identity["database_insert"]==1 else "NOT VERIFIED"
        r["consistency_proof"]="NOT RUN — bounded independent reads are not a consistent full capture"
except pyodbc.Error as e:
    r["status"]="FAIL";r["stage"]=stage;r["sqlstate"]=str(e.args[0]) if e.args else None
    msg=str(e).lower()
    r["failure_class"]="TLS certificate" if any(v in msg for v in ("certificate","ssl provider","certificat")) else "Authentication" if "login failed" in msg else "Connectivity/query"
except ValueError as e:
    r["status"]="FAIL";r["stage"]=stage;r["failure_class"]=str(e)
print(json.dumps(r,ensure_ascii=False))
```

Full original principal values chỉ dùng trong memory để fingerprint; expected source identity kiểm bằng machine/instance/database allowlist. Actual result:
- identity/TLS/source reads **PASS**; SQL version17.0.1000.7,Express64,driver18.06.0002; encryptTRUE/TCP/NTLM.
- Login fingerprint `5eecf0d76c45635cd7b2026ff0ebb098811ebd393fc08164a804c28e9a92f27d`; sysadmin1; DB write/ALTER1. Initial permission probe dùng class SERVER trả control_server=NULL, **không được hiểu là deny**. Đã verify lại đúng server-level invocation:

```sql
SELECT HAS_PERMS_BY_NAME(NULL,NULL,'CONTROL SERVER') AS control_server,
       IS_SRVROLEMEMBER('sysadmin') AS is_sysadmin;
```

Follow-up vẫn dùng secure source connection/read-only hint/5s login/20s query timeout; actual control_server=1 và is_sysadmin=1. Không sửa identity/grants để “làm PASS”.

| Source population | TOP(1) constant rows | SELECT | INSERT / UPDATE / DELETE metadata | Read status |
| --- | --- | --- | --- | --- |
| Sales.Customers | 1 | 1 | 1 / 1 / 1 | PASS |
| Sales.Orders | 1 | 1 | 1 / 1 / 1 | PASS |
| Sales.OrderLines | 1 | 1 | 1 / 1 / 1 | PASS |
| Sales.Invoices | 1 | 1 | 1 / 1 / 1 | PASS |
| Sales.InvoiceLines | 1 | 1 | 1 / 1 / 1 | PASS |
| Sales.CustomerTransactions | 1 | 1 | 1 / 1 / 1 | PASS |
| Warehouse.StockItems | 1 | 1 | 1 / 1 / 1 | PASS |
| Warehouse.StockItemHoldings | 1 | 1 | 1 / 1 / 1 | PASS |
| Warehouse.StockItemTransactions | 1 | 1 | 1 / 1 / 1 | PASS |
| Sales.Customers_Archive | 1 | 1 | 1 / 1 / 1 | PASS |
| Warehouse.StockItems_Archive | 1 | 1 | 1 / 1 / 1 | PASS |

Q_DB actual: is_read_only=false,snapshot_isolation_state_desc=OFF,is_read_committed_snapshot_on=false,is_cdc_enabled=false,change_tracking_enabled0. Metadata observations không no-writes guarantee; không thay settings.

## 4. Không thực thi / giới hạn

- Không PostgreSQL connection/metadata/persistence/encoding/collation/TLS check vì chưa approved target/profile; native5432 và B9 không được tự sử dụng. Không actual PG server version claim.
- Không full population/COUNT_BIG/extraction, common source snapshot, adapter/temporal fidelity rerun, injection/retry/recovery, DML/DDL hoặc permission-negative write attempts.
- Không chạy B9 poc.py/unittest;72 inherited scenarios giữ NOT RUN, kể cả IT01 vì M1A chỉ subset metadata/access, chưa toàn Q11/profile/history requirements.
- Không database/container/service/config/dependency modification. Temporary source connections tự đóng; báo cáo metadata không chứng minh database-wide source immutability.
