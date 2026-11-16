# WWI-05 / M1B — Acceptance & Gate Evidence Assessment

**2026-11-16. M1B review/planning, không source operational readiness.** Authority: task trực tiếp “WWI-05 / M1B — Secure Source Identity & Consistency Readiness”; cho documentation-only commit sau QA, không administrative execution. [Identity proposal](wwi-source-identity-proposal.md), [Consistency proposal](wwi-source-consistency-proposal.md), [Owner/DBA checklist](wwi-source-dba-owner-checklist.md). Không thay approved [A02/Full Load](../data-models/wwi-dw-03a-full-raw-design-proposal.md), [INC](../data-models/wwi-dw-03b-incremental-design-proposal.md) hoặc [B9 ADR](../adr/scd-05-exact-temporal-precision.md).

## 1. Preflight và scope

Expected/actual baseline: branch main,HEAD `69822e2683e40cc0f31a511d9176c03fb743e301`,working tree sạch; root đúng project,133 tracked files baseline hashed. Đã đọc AGENTS/Scope/Roadmap/Tasks,DW-04/gates/handoff,4 M1A docs,Full/Incremental specs và relevant ADRs. Phase1 Completed/WWI-04 DONE Design;Phase2/WWI-05 IN_PROGRESS;M1A DONE Verification. M1B chỉ planning+metadata, M1C/M2/M3 không bắt đầu.

Chỉ4 new docs và6 related tracker/handoff/index files; original gate register/ADR/source/SQL/B9 evidence/code giữ nguyên. Không SQL Server identities/permissions/data/config modifications, PostgreSQL/Docker commands, source writes, package installation hoặc production connector.

## 2. Actual current-security findings

Source observation UTC `2026-11-16T07:29:27.1556321`: machine DESKTOP-OBDFK6B,instance SQLEXPRESS,database WideWorldImporters,server17.0.1000.7. Driver18/Windows Integrated/Encrypt=yes/TrustServerCertificate=no; actual encryptTRUE/TCP/authNTLM. Login/ORIGINAL_LOGIN fingerprint `5eecf0d76c45635cd7b2026ff0ebb098811ebd393fc08164a804c28e9a92f27d`; không raw principal/credential output.

| Observation | Actual result | Interpretation |
| --- | --- | --- |
| Role predicates | sysadmin/securityadmin/db_owner/db_datawriter=1 | Effective context quá rộng; không suy explicit membership/grant path đã audit |
| Broad powers | CONTROL SERVER=1,CONNECT ANY DATABASE=1; own fn_my_permissions có51 server/109 database permission names | Current identity FAIL extraction suitability; không permission changes |
|11 objects | SELECT/VIEW DEFINITION/INSERT/UPDATE/DELETE/ALTER/CONTROL/TAKE OWNERSHIP predicates đều1 | Chỉ metadata rights, không mutation; H engine restrictions khác privileges |
| Temporal links | Customers→Customers_Archive,StockItems→StockItems_Archive;2 physical H có metadata riêng |11-population contract không đổi, H cần own SELECT grant |
| Source flags | is_read_only=false;SNAPSHOT OFF,RCSI/CDC/CT false | Không proof static state; không bật hoặc sửa flags |
| Current tokens |2 Windows-group DENY ONLY,11 Windows-group GRANT OR DENY,2 server-role,1 Windows-login entries | Không xuất group names hoặc claim full Windows/local-admin/role closure đã kiểm |
| Intended extractor config | Không profile supplied; process source-variable names empty,root .env absent | Intended identity chưa verified; không kết luận server không có principal khác |

Cả11 objects metadata visibility/column counts được xác nhận dưới current admin; không rerun data SELECT11 tables hoặc full profiling/extraction trong M1B. Source consistency controls/copy chưa executed; metadata PASS không close G01/G02.

## 3. Acceptance — review completion khác runtime

| Criterion | Requirement | Deliverable / evidence | Result |
| --- | --- | --- | --- |
| M1B-AC01 | Required extraction privileges được ghi | Identity P01–07,11 population rows và current/H grants | PASS — planning |
| M1B-AC02 | Least-privilege acceptance tests có expected/status | LP01–12, safe negatives/no escalation; intended runtime NOT RUN | PASS — specification |
| M1B-AC03 | Evaluate cả2 source consistency candidates | Consistency §2 và SW01–07/CPY01–06 | PASS — analysis |
| M1B-AC04 | Recommend option, chưa tự approve | A có điều kiện, fallback B cần riêng approval; hold nếu thiếu proof | PASS — PROPOSED |
| M1B-AC05 | Owner/DBA decisions và action scope rõ | Checklist D01–D05/DBA01–07; toàn bộ pending approval | PASS — planning |
| M1B-AC06 | Gate status evidence-based | §4; G01/G02 blocked, fresh admin observations riêng;31/72 preserved | PASS — traceability |
| M1B-AC07 | Documentation validation đạt | §6 actual static/staged execution trước commit | PASS — static/staged QA |

Khi AC07 QA đạt, M1B đủ **DONE — Planning Review** theo task acceptance; không Owner approve identity/method recommendation, không operational PASS hoặc WWI-05 DONE.

## 4. Gate evidence / inherited status

| Original gate / scope | Prior evidence | M1B evidence | Current outcome | Required next action |
| --- | --- | --- | --- | --- |
| G02 / existing developer | M1A FAIL; M1B fresh metadata | sysadmin/CONTROL SERVER/CONNECT ANY DATABASE=1; object DML/ALTER/CONTROL1 cả11 | FAIL suitability, unchanged | Không dùng identity này cho extraction; D01/D02+DBA action |
| G02 / intended identity | Approved extractor profile chưa supplied | Chưa có test bằng intended logon; current admin không substitute | BLOCKED / NOT RUN | Approve identity/package và LP tests trước gate review |
| G01/RG01 / concrete method | A02 conditional policy đã approved | A/B evidence plans được chuẩn bị, chưa Owner chọn method hoặc thực hiện controls/copy | BLOCKED; method PROPOSED | D03/D04; actual full interval/copy/recon proof |
| RG02/CG08 / source profile | M1A pending environment/service proof | Metadata visibility/grants proposal có; chưa configure identity hoặc freeze/copy | Pending, không close | DBA/Owner scope và trusted profile proof |
| G03–G08/RG03–12/CG01–10/B5 | Inherited statuses | M1B không runtime Raw/INC/SCD2/Certified, target hoặc thresholds | UNCHANGED/Pending theo original register | Đúng milestone/use gates; no opportunistic PASS |
| CD-T01–21/IT01–21/CP-T01–30 | 72 NOT RUN | Metadata self-review chỉ subset, không toàn IT01 hoặc any suite | NOT RUN — preserved | Execute đúng future approved implementation/test scope |

Original31 gate entries không sửa structure/meaning/status; local M1B-D01–05 không renumber G/RG/CG/B5. LP/SW/CPY tests là readiness specifications mới; mọi intended-identity/window/copy execution vẫn NOT RUN.

## 5. Commands/SQL evidence và verification plan

Executed: git branch/log/status/root checks, read-only file reads/hash inventory; primary Microsoft Learn lookup cho permissions/TLS; one secure source session với5s login/20s query timeout và no automatic retry. Dùng existing project .venv tools, không package change. Python đặt dont_write_bytecode trước driver import; không tạo executable file hoặc evidence JSON mới.

**Đã chạy28 SELECT metadata statements:** Q1/Q2/Q6/Q7 một lần,Q4 SERVER và DATABASE2 lần,Q3/Q5 mỗi11 objects. Column/token COUNT chỉ catalog/token metadata, không source COUNT_BIG. Helper đầy đủ dưới đây là checkpoint evidence, không production connector/intended-identity test.

```python
import sys,json,hashlib
sys.dont_write_bytecode=True
from contextlib import closing
import pyodbc
T=["Sales.Customers","Sales.Orders","Sales.OrderLines","Sales.Invoices","Sales.InvoiceLines","Sales.CustomerTransactions","Warehouse.StockItems","Warehouse.StockItemHoldings","Warehouse.StockItemTransactions","Sales.Customers_Archive","Warehouse.StockItems_Archive"]
Q1="""SELECT @@SERVERNAME AS server_name,DB_NAME() AS database_name,
CONVERT(varchar(128),SERVERPROPERTY('MachineName')) AS machine_name,
CONVERT(varchar(128),SERVERPROPERTY('InstanceName')) AS instance_name,
CONVERT(varchar(128),SERVERPROPERTY('ProductVersion')) AS product_version,
ORIGINAL_LOGIN() AS original_login,SUSER_SNAME() AS login_name,USER_NAME() AS db_user,
IS_SRVROLEMEMBER('sysadmin') AS sysadmin,IS_SRVROLEMEMBER('securityadmin') AS securityadmin,
IS_ROLEMEMBER('db_owner') AS db_owner,IS_ROLEMEMBER('db_datawriter') AS db_datawriter,
HAS_PERMS_BY_NAME(NULL,NULL,'CONTROL SERVER') AS control_server,
HAS_PERMS_BY_NAME(NULL,NULL,'CONNECT ANY DATABASE') AS connect_any_database,
CONVERT(varchar(33),SYSUTCDATETIME(),126) AS observed_at_utc"""
Q2="SELECT encrypt_option,net_transport,auth_scheme FROM sys.dm_exec_connections WHERE session_id=@@SPID"
Q3="""SELECT t.object_id,SCHEMA_NAME(t.schema_id)+'.'+t.name AS population,t.temporal_type_desc,
CASE WHEN t.history_table_id IS NULL THEN NULL ELSE OBJECT_SCHEMA_NAME(t.history_table_id)+'.'+OBJECT_NAME(t.history_table_id) END AS history_population,
(SELECT COUNT(*) FROM sys.columns c WHERE c.object_id=t.object_id) AS column_count
FROM sys.tables t WHERE t.object_id=OBJECT_ID(?)"""
Q4="SELECT permission_name FROM sys.fn_my_permissions(NULL,?) ORDER BY permission_name"
Q5="""SELECT HAS_PERMS_BY_NAME(?,'OBJECT','SELECT') AS can_select,
HAS_PERMS_BY_NAME(?,'OBJECT','VIEW DEFINITION') AS view_definition,
HAS_PERMS_BY_NAME(?,'OBJECT','INSERT') AS can_insert,
HAS_PERMS_BY_NAME(?,'OBJECT','UPDATE') AS can_update,
HAS_PERMS_BY_NAME(?,'OBJECT','DELETE') AS can_delete,
HAS_PERMS_BY_NAME(?,'OBJECT','ALTER') AS can_alter,
HAS_PERMS_BY_NAME(?,'OBJECT','CONTROL') AS can_control,
HAS_PERMS_BY_NAME(?,'OBJECT','TAKE OWNERSHIP') AS can_take_ownership"""
Q6="""SELECT is_read_only,snapshot_isolation_state_desc,is_read_committed_snapshot_on,is_cdc_enabled,
CASE WHEN EXISTS(SELECT 1 FROM sys.change_tracking_databases x WHERE x.database_id=d.database_id) THEN 1 ELSE 0 END AS change_tracking_enabled
FROM sys.databases d WHERE d.database_id=DB_ID()"""
Q7="SELECT type,usage,COUNT(*) AS token_entries FROM sys.login_token GROUP BY type,usage"
r={"status":"NOT RUN","scope":"current developer self-context; not intended extractor","login_timeout_seconds":5,"query_timeout_seconds":20,"automatic_retries":0,"queries":{"Q1":Q1,"Q2":Q2,"Q3":Q3,"Q4":Q4,"Q5":Q5,"Q6":Q6,"Q7":Q7}}
def fetch(c,q,p=()):
    c.execute(q,*p);names=[d[0] for d in c.description];return [dict(zip(names,row)) for row in c.fetchall()]
try:
    with closing(pyodbc.connect("DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:DESKTOP-OBDFK6B,1433;DATABASE=WideWorldImporters;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=no;APP=M1B-ReadOnlyReview;",autocommit=True,timeout=5,attrs_before={pyodbc.SQL_ATTR_ACCESS_MODE:1})) as db:
        db.timeout=20
        with closing(db.cursor()) as c:
            x=fetch(c,Q1)[0]
            for k in ("original_login","login_name","db_user"):
                x[k+"_sha256"]=hashlib.sha256(str(x.pop(k)).encode()).hexdigest()
            r["identity"]=x
            if x["database_name"]!="WideWorldImporters" or x["machine_name"].upper()!="DESKTOP-OBDFK6B" or x["instance_name"].upper()!="SQLEXPRESS":raise ValueError("source allowlist mismatch")
            r["tls"]=fetch(c,Q2)[0]
            if r["tls"]["encrypt_option"]!="TRUE" or r["tls"]["net_transport"]!="TCP":raise ValueError("secure transport expectation mismatch")
            r["server_permissions"]=[v["permission_name"] for v in fetch(c,Q4,("SERVER",))]
            r["database_permissions"]=[v["permission_name"] for v in fetch(c,Q4,("DATABASE",))]
            r["populations"]=[]
            for t in T:
                meta=fetch(c,Q3,(t,))
                if len(meta)!=1:raise ValueError("population metadata missing/multiple")
                r["populations"].append({**meta[0],**fetch(c,Q5,tuple(t for _ in range(8)))[0]})
            r["source_flags"]=fetch(c,Q6)[0]
            r["token_summary"]=fetch(c,Q7)
        r["status"]="PASS — metadata inspection only"
except pyodbc.Error as e:
    r["status"]="BLOCKED";r["sqlstate"]=str(e.args[0]) if e.args else None;r["error_category"]="SQL connection/metadata permission; no fallback/escalation"
except ValueError as e:
    r["status"]="FAIL";r["error_category"]=str(e)
print(json.dumps(r,ensure_ascii=False))
```

Connection/all metadata queries thành công; data parameters bind object names/classes. Không EXECUTE AS/GRANT/DENY/REVOKE/DML/DDL. SPID-filtered DMV chạy dưới existing developer/admin không là minimum-rights recommendation cho extractor. Cursor/connection đóng qua closing. Profile inspection chỉ names/exists, không secret values.

Future tests LP01–12/SW01–07/CPY01–06 có preconditions/expected/status trong linked proposals, **NOT RUN**. Không destructive negatives/escalation; metadata empty/NULL không tự coi deny. No-unauthorized-modification kết luận trong phạm vi query/code/file evidence, không claim đã audit toàn server/mọi writer.

## 6. Static validation / Git boundary

**Actual static QA PASS,2026-11-16:**137 visible files/131 Markdown,1.075 local links/anchors không lỗi;đúng10 Markdown changes (6 sửa+4 mới),127 protected initial hashes và10 B9 local evidence/config hashes giữ nguyên.31 original gates/72 NOT RUN rows,12 LP+7 SW+6 CPY planned NOT RUN tests và5 Pending decisions được kiểm;0 secret findings,format/table/fence/scope/diff checks đạt. Chỉ commit sau staged-content/secret/diff QA PASS;không remote/push hoặc runtime readiness approval.

Authorized commit: `docs: define WWI source identity and consistency readiness`. Không amend/reset prior commits; SHA báo sau commit.

Actual staged QA PASS:10 Markdown blobs khớp working content sau Git line-ending normalization;0 staged secret findings,diff --cached --check đạt,no active hooks/no remote.7/7 M1B planning criteria đạt;source identity/method operational approvals và runtime proof vẫn pending. Final stage verification được kiểm lại sau dòng evidence này trước commit.

## 7. Readiness và điểm dừng

Operational source readiness **BLOCKED**: G02 approved identity/effective rights chưa verified;G01 concrete method/evidence chưa approved/executed. D01–D05 pending; A preferred có điều kiện,B fallback separately approved. PostgreSQL target/reproducibility blockers của M1A không được giải quyết bởi M1B.

Next recommendation: Owner review proposals,approve exact source identity/grant scope và concrete consistency proof plan,rồi giao DBA action/re-verification task riêng trong WWI-05. Không bắt đầu M1C/M2/M3,copy creation,target setup hoặc ingestion. Planning completion không cấp quyền remediation.
