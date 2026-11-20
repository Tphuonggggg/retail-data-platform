# ingestion — WWI-06A Full Load

**WWI-06C hiện hành2026-11-18:** [history permission investigation](ingestion-history.md#wwi-06c--history-permission-investigation-2026-11-18) vẫn **BLOCKED**. Đã có SELECT-only evidence dưới actual wwi_extract qua PowerShell/ODBC18:9 current tables không quyền ghi được kiểm, hai bound histories cùng effective INSERT=1. Chưa xác định được nguyên nhân; Python preflight chưa chạy được do base interpreter nằm trong profile PC. Một kết nối strict TLS thành công, kết nối mới thất bại; không suy current source readiness PASS. Production guard giữ nguyên, chưa smoke/ingestion/publication.

**WWI-06B current2026-11-18:** [approved Raw provisioning/runtime evidence](../../../infrastructure/postgres/README.md#wwi-06b--approved-raw-payload-provisioning-2026-11-18) = **RAW_PAYLOAD_PROVISIONING_PASS**. Owner duyệt exact SHA256/target/postgres; initializer chạy nguyên bản một lần exit0.11 payload+4 controls+11 views/248 columns/constraints/indexes/grants verified; target-only preflight(all11) PASS, foundation unchanged. Chưa Full Load/smoke/publication. Archive permission exception vẫn pending; không source guard bypass hoặc tự load. NOT APPLIED/TARGET_DDL_REQUIRED và TLS trust-remediation notes phía dưới là prior states/proposals.

## Trạng thái và phạm vi

2026-11-18: **Implemented / Offline Tested / REVIEW**. Full Load cho đúng11 populations đã có code/test; **runtime Full Load NOT RUN**, MVP-G03 chưa nghiệm thu. MVP-G02 foundation và Owner-authorized Raw schema provisioning verified; source strict TLS PASS theo Owner, archive effective INSERT decision vẫn pending. Quyền mới nhất chỉ đã cho exact Raw initializer và readonly verification, không Full Load/smoke hoặc rerun provisioning.

Module đọc SQL Server WWI → PostgreSQL Raw, quản lý run/capture, fidelity/count/digest và publication. Không tính KPI, không dbt/DW/SCD2/Airflow hoặc incremental; các phần đó **Not implemented yet**. Sales → Customer → Inventory giữ thứ tự nghiệp vụ; nạp11 source populations chỉ chuẩn bị Raw.

## Trách nhiệm, cấu trúc và dependencies

| Thành phần | Trách nhiệm / input → output |
| --- | --- |
| [full_load.py](../../../ingestion/full_load.py) | CLI và orchestration trong một process; contracts/config → candidate hoặc publication |
| [common/](../../../ingestion/common/README.md) | Frozen source schema, F2, codecs/digest, config, external evidence coverage |
| [extractors/](../../../ingestion/extractors/README.md) | Dedicated Windows identity; SELECT-only metadata/count/batched reads |
| [loaders/](../../../ingestion/loaders/README.md) | COPY/read-back/metadata/atomic pointer/recovery; không auto DDL/GRANT |
| [checkpoints/](../../../ingestion/README.md) | Incremental checkpoint Not implemented yet |
| [requirements.txt](../../../ingestion/requirements.txt) | pyodbc5.5.0, psycopg[binary]3.3.9 đã có trong project-local .venv; task này không cài package |

Python3.12, ODBC18, PostgreSQL18, unittest stdlib. Inputs: [source contracts](../../data-models/wwi-source-contracts.md), [metadata dictionary](../../data-models/wwi-metadata-dictionary.md), [accepted Full/Raw design](../../data-models/wwi-dw-03a-full-raw-design-proposal.md), [Raw foundation](../../../infrastructure/postgres/README.md), private ignored .env. Outputs: typed Raw candidates/published membership và metadata. Không sửa accepted mappings/KPI/temporal policies. Config tái sử dụng pure functions của [Raw checker](../../../infrastructure/scripts/check_raw_connection.py).

## Hợp đồng dữ liệu và kiểu

[source_contract.json](../../../ingestion/common/source_contract.json) đóng băng9 current tables/156 columns từ metadata dictionary: Sales.Customers, Orders, OrderLines, Invoices, InvoiceLines, CustomerTransactions; Warehouse.StockItems, StockItemHoldings, StockItemTransactions. Hai populations riêng Sales.Customers_Archive và Warehouse.StockItems_Archive giữ đủ columns/duplicate multiplicity; không unique natural key archive. Runtime so tên/thứ tự/type/nullability với sys.columns; khác biệt → STOP. WWI-06B đã đối chiếu archive schema thực tế dưới DBA: khớp; dedicated runtime permissions còn pending.

| SQL Server | Python / Raw | Kiểm soát |
| --- | --- | --- |
| int, bit, date | int/bool/date → integer/boolean/date | Type/range/NULL theo source contract |
| decimal(p,s) | Decimal → numeric(p,s) | Không float hoặc âm thầm rounding; reject scale/range loss |
| nvarchar | str → text | Giữ Unicode/whitespace/case; reject NUL/unpaired surrogate không thể lưu lossless |
| varbinary(max) | bytes → bytea | Giữ nguyên bytes kể cả byte0 |
| geography | SQL native varbinary → bytes/bytea | Không gọi WKB; lưu engine/version/encoding context; actual round-trip proof pending |
| datetime2(7) | source F2 → str/None → text COLLATE "C" | Canonical27 ký tự YYYY-MM-DDTHH:MM:SS.fffffff; exact100ns/min/max/sentinel; không Python datetime |

F2 expression nguyên văn [B9 PoC](../../../tests/integration/b9_precision/poc.py), chỉ thay vetted operand. Technical run times dùng timestamptz, không biến system-time thành business-effective time. Geography dùng CONVERT(varbinary(max), geography) theo [SQL Server serialization](https://learn.microsoft.com/en-us/sql/t-sql/spatial-geography/spatial-types-geography-transact-sql?view=sql-server-ver17); cần actual adapter round-trip proof trước publication.

Current ORDER BY PK/strictly increasing key. Archive ORDER BY natural ID/ValidFrom/ValidTo; tied ordinal chỉ là occurrence trong capture, không stable cross-capture identity. Không collapse duplicates/zero-duration rows.

Source fetchmany, target COPY từng batch, read-back bằng **server-side named cursor**. Batch1–10000 mặc định500; binary/geography cap1; max-text cap64. Memory tỷ lệ batch × largest row; một LOB/driver buffer vẫn lớn. Chưa đo RSS/throughput hoặc hard memory ceiling. COPY dùng typed write_row, không CSV interpolation; transaction behavior theo [psycopg COPY](https://www.psycopg.org/psycopg3/docs/basic/copy.html).

## Target initialization và quyền

[full_load.sql](../../../infrastructure/postgres/full_load.sql) là **artifact đã Owner-authorized execution/runtime verified**, sinh từ [schema.py](../../../ingestion/loaders/schema.py):11 typed payload tables,11 views, bốn control tables. DDL new-only transaction trên retail_raw; Owner dùng postgres chỉ khi cấp quyền provisioning riêng. Collision → rollback; không DROP/TRUNCATE/IF-NOT-EXISTS che drift. Runtime luôn retail_ingest, không auto CREATE/GRANT/escalation.

Actual role có raw USAGE, không CREATE; payload/control/views và exact grants đã provision. Target-only preflight(all11) PASS. Grants chỉ SELECT/INSERT payload; controls SELECT/INSERT hoặc pointer SELECT/UPDATE; views SELECT. Metadata nền runs/object_runs giữ SELECT/INSERT/UPDATE; app không DELETE/TRUNCATE. Không nới quyền để đạt PASS.

**Historical reviewed command — đã execute theo Owner approval, không rerun trên target hiện tại:**

~~~powershell
if ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name -ine 'DESKTOP-OBDFK6B\PC') { throw 'STOP: Docker requires PC operator' }
$dockerExe = 'C:\Users\PC\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe'
Get-Content -LiteralPath infrastructure/postgres/full_load.sql -Raw -Encoding UTF8 | & $dockerExe exec -i retail-raw-postgres-1 psql -X -U postgres -d retail_raw -v ON_ERROR_STOP=1
~~~

Actual execution dùng exact bytes qua approved Docker-local psql, không rerun command ví dụ này; không áp dụng native PostgreSQL/B9 hoặc đổi bootstrap. CLI load không tự provisioning.

## Transaction, metadata và publication

runs lưu run_id/capture_id riêng, retry link, start/end/status/error/consistency. object_runs lưu scope/status/timestamps/source/extracted/loaded counts/reconciliation. Duration tính finished_at−started_at và tổng trên CLI; unknown count NULL, known rollback mới loaded=0. Columns dựa [bootstrap thực tế](../../../infrastructure/postgres/bootstrap.sql).

Bốn bảng mới: load_contracts(scope/contract fingerprint/source engine context), load_audits(count/SHA256 typed-row digest), raw_publications(immutable run/previous publication), raw_current(singleton pointer). Fingerprint là data replay contract, không approval manifest; source snapshot ID NULL khi không proof.

Sau preflight/session advisory lock: transaction nhỏ ghi RUNNING/PENDING, rồi **một transaction cho toàn selected scope** gồm COPY/read-back/count/digest/final status. Lỗi rollback toàn payload capture; không per-batch commit/partial publication. Long transaction/WAL cost cần đo. Source count trước/sau bằng nhau không chứng minh snapshot consistency.

Selected/all không proof → VALIDATED_UNPUBLISHED_CANDIDATE, consistency UNVERIFIED. Publication chỉ all11, external verified no-writes window + geography proof/count/content PASS; pointer/payload commit cùng transaction. Current views chỉ committed publication; downstream nhiều statements phải pin publication/run hoặc dùng consistent transaction. Base tables có candidate rows; consumers không tự MAX(run time) mỗi bảng. Raw publication không phải Certified DW/mart approval.

**Persisted chunk ledger/sealed-chunk resume, retained failed-content replay và toàn bộ attempt registry chưa triển khai**. WWI-06A có atomic capture và safe new-capture retry; không gọi source reread là retained replay. Accepted design giữ nguyên, remaining recovery requirements phải đối chiếu/bổ sung WWI-06B trước operational acceptance; không WWI-06/MVP-G03 DONE.

## CLI offline và cấu hình

Chạy tại root bằng .venv có sẵn. Private .env/environment, không password argv/in file tracked. Summary chỉ allowlisted fields. Fixed source tcp:DESKTOP-OBDFK6B,1433 / SQLEXPRESS / WideWorldImporters, kiểm Windows principal/SQL SID/user. Encrypt=yes/TrustServerCertificate=no không fallback. [.env.example](../../../.env.example): batch500/login5s/query60s có configurable bounds.

~~~powershell
.venv\Scripts\python.exe -m ingestion.full_load config --env-file .env
.venv\Scripts\python.exe -m ingestion.full_load plan --all
.venv\Scripts\python.exe -m ingestion.full_load ddl
~~~

plan là dry-run offline chỉ SELECT projections; ddl chỉ in SQL; config không kết nối. Các lệnh offline này đã chạy. load/abandon thiếu --execute dừng trước connect.

## Runbook runtime tương lai — NOT RUN

Prerequisites: Owner authorize WWI-06B runtime load; source TLS hợp lệ/least privilege all11; target DDL/grants + actual schema/type adapter proof. Chạy Python trong Windows DESKTOP-OBDFK6B\wwi_extract session, nhập password tương tác ngoài repository, không PC/DBA fallback. Private config/env phải đọc được bởi extractor; task này không thay ACL/logon rights.

~~~powershell
# SELECT-only; connectivity kiểm source rights/schema, preflight thêm target payload.
.venv\Scripts\python.exe -m ingestion.full_load connectivity --all --env-file .env
.venv\Scripts\python.exe -m ingestion.full_load preflight --all --env-file .env

# Chỉ sau runtime authorization: selected candidate trước.
$candidateRun = [guid]::NewGuid().ToString()
.venv\Scripts\python.exe -m ingestion.full_load load --object Sales.Orders --run-id $candidateRun --execute --env-file .env
.venv\Scripts\python.exe -m ingestion.full_load reconcile --object Sales.Orders --run-id $candidateRun --env-file .env

# All11 candidate, vẫn UNVERIFIED nếu không proof.
$fullRun = [guid]::NewGuid().ToString()
.venv\Scripts\python.exe -m ingestion.full_load load --all --run-id $fullRun --execute --env-file .env
~~~

Source preflight luôn effective-rights all11, cả selected-object; archive INSERT phải resolve. Readonly ODBC hint không thay quyền thực tế. Không command nào bypass TLS/auto grant.

Publication cần **capture mới** trong actual verified window phủ toàn thời gian/scope. External JSON ở ignored .local; template sau **chưa valid**, không runtime proof:

~~~json
{
  "kind": "OWNER_VERIFIED_NO_WRITES_WINDOW",
  "reviewed": false,
  "endpoint": "tcp:DESKTOP-OBDFK6B,1433",
  "database": "WideWorldImporters",
  "reference": "REPLACE_WITH_REVIEWED_ACTUAL_SOURCE_WINDOW_EVIDENCE",
  "window_start": "REPLACE_WITH_ACTUAL_AWARE_ISO8601_START",
  "window_end": "REPLACE_WITH_ACTUAL_AWARE_ISO8601_END",
  "scope": ["Sales.Customers", "Sales.Customers_Archive", "Sales.CustomerTransactions", "Sales.InvoiceLines", "Sales.Invoices", "Sales.OrderLines", "Sales.Orders", "Warehouse.StockItemHoldings", "Warehouse.StockItemTransactions", "Warehouse.StockItems", "Warehouse.StockItems_Archive"],
  "geography_roundtrip_reference": "REPLACE_WITH_ACTUAL_ENGINE_ADAPTER_ROUNDTRIP_EVIDENCE"
}
~~~

Operator chịu proof writer inventory/control/window; parser chỉ kiểm review flag/shape/endpoint/coverage, không chứng minh authenticity/writer control. Không source timestamp nào tự thành business-effective time. Lệnh tương lai: load --all --run-id <new-uuid> --consistency-evidence .local/source-window.json --publish --execute --env-file .env. Không promote UNVERIFIED capture cũ bằng sửa metadata.

## Rerun và recovery

- Cùng run_id SUCCEEDED: durable count/digest read-back, không source reread/duplicate load/reset current pointer. Scope/contract phải khớp. reconcile không sửa metadata.
- Known batch failure: rollback toàn scope, metadata FAILED/category/progress, previous publication giữ nguyên. New UUID + --retry-of <failed-uuid> cùng scope/contract: source reread/new capture.
- Mất COMMIT ACK: COMMIT_OUTCOME_UNKNOWN_INSPECT_RUN_ID; không rewrite FAILED/auto retry. Fresh connection inspect runs/contracts/audits/payload/publication. SUCCEEDED → reconcile sameID; ambiguity → STOP.
- Crash để RUNNING: operator xác nhận process dừng; abandon đúng --all/--object + --run-id + --execute phải lấy lock và không payload/audit/publication rồi mới mark FAILED. Không delete. Broken connection không giả vờ rollback/loaded=0.
- Logs chỉ IDs/status/category/count/duration, không driver text/row values/password. Close failure trả non-zero và inspect-before-retry. Không auto database retry/backoff để che lỗi.

## Testing, acceptance và WWI-06B

~~~powershell
.venv\Scripts\python.exe -m unittest discover -s ingestion/tests -p full_load_offline.py -v
.venv\Scripts\python.exe -m unittest discover -s infrastructure/tests -p raw_foundation_static.py -v
.venv\Scripts\python.exe -m unittest discover -s tests -p source_security_static.py -v
~~~

[Offline suite](../../../ingestion/tests/full_load_offline.py): synthetic fixtures/mock drivers; F2/NULL/Decimal/Unicode/binary, frozen contracts156 current columns, batching/empty/history duplicates, rollback/count/content mismatch/retry/idempotency/unknown ACK, atomic full-scope publication, identity/schema/TLS/permission blockers, named cursor/no-secret CLI. Offline PASS không chứng minh SQL compilation/geography fidelity/performance hoặc runtime ingestion.

Kết quả WWI-06A2026-11-18 (trước readiness review dưới đây): Python3.12.10, pyodbc5.5.0, psycopg/psycopg-binary3.3.9 và ODBC Driver18 có sẵn; không install. **38 Full Load +22 Raw foundation +18 source security +12 B9 offline tests PASS**. CLI plan/config/ddl PASS offline; load thiếu execute trả exit1 trước connection. Final readonly Raw inspection: PostgreSQL18.7,0 payload tables, chỉ runs/object_runs, counts[0,0], app Raw CREATE=false. Task chỉ restart Raw một lần ở Phase A và chạy metadata/TCP reads; không source query/extraction, payload DDL/grants/COPY/publication, source permission change, native PostgreSQL/B9 resource change hoặc real Full Load.

WWI-06A acceptance: runnable CLI/code/type contracts + reproducible offline tests + safe failure/recovery/privilege boundaries; Owner review pending. WWI-06B: resolve source TLS/archive INSERT; actual full projection/archive metadata/geography proof; review/provision target artifact; dedicated runtime preflight; selected smoke/full candidate trong verified window; actual COPY/rollback/reconnect/idempotency/count+value/atomic views và remaining chunk/attempt recovery requirements. WWI-06B readiness review được giao ở phần dưới; actual load và các milestone sau chưa bắt đầu.

## WWI-06B — Runtime readiness review, 2026-11-18

**Historical review trước approved Raw provisioning.** Target schema/grants đã PASS theo latest linked evidence; các blockers TARGET_DDL_REQUIRED/NOT APPLIED phía dưới giữ historical context. Source/archive gate và runtime load authorization chưa được thay đổi.

**Kết luận: NOT READY FOR SELECTED-OBJECT LOAD.** Đây là review/read-only diagnostics + bounded offline fixes, không runtime authorization. WWI-06A vẫn REVIEW; WWI-06/MVP-G03 chưa nghiệm thu. Git đầu task: main / 36d5ab05b4d4b17cbf041e2c1daf2637bcc05b36, clean.

### Kết quả review implementation

| Hạng mục | Kết quả / giới hạn |
| --- | --- |
| Source projection/allowlist | Explicit columns cho9 current +2 physical archives; không SELECT-star/filter business; metadata11/11 và PK9 current/no PK2 history verified thực tế |
| Type/adapter | decimal18,2/3→exact Decimal/numeric; int/bit/date/Unicode/binary/NULL; computed fields được đọc như source output. TOP(1) projection+codec11/11 PASS dưới PC, không chứng minh toàn dataset/dedicated permissions |
| datetime2(7) | F2 nguyên văn B9; Python str/None,27 chars, TEXT/C. Không giảm xuống microsecond, không gán business time |
| Geography | Hai non-NULL samples Customers/current và archive: native22 bytes, SQL→Python→parameter SQL→native bytes exact PASS. Đây không WKB; chưa PostgreSQL persistent round-trip/full geometry coverage |
| Streaming/memory | fetchmany/COPY batches; named server cursor read-back; cap1 binary/geography,64 max-text. Không full payload fetchall; driver/large single LOB/RSS chưa benchmark |
| Transactions/publication | RUNNING registration riêng; một transaction cả selected capture; count+typed digest/read-back trước SUCCEEDED; all11+external proof mới đổi pointer; selected candidate không publication |
| Metadata/reconciliation | Existing runs/object_runs definitions giữ; bốn control tables đề xuất. Counts/NULL/decimal/temporal/PK và ordered digest; count stability không chứng minh consistent snapshot |
| Idempotency/recovery | Same validated runId chỉ read-back, không source reread/duplicate publish. Known failure rollback; retry UUID/capture mới. Unknown ACK không auto retry hoặc tự FAILED |
| Lỗi đã sửa | CLI trước đây tự sinh runId nhưng lỗi không trả ID; nay cấp ID trước connect và ghi ID trong sanitized failure/close output, để tra unknown COMMIT. Regression tests không dùng live DB |
| Schema generator | File thực tế là loaders/schema.py, không ingestion/schema.py. Prepared full_load.sql khớp generator; chưa engine compilation/provisioning |

### TLS — actual evidence và bước xử lý tối thiểu

2026-11-18: **ODBC18 Encrypt=yes/TrustServerCertificate=no/Windows Auth PASS dưới DESKTOP-OBDFK6B\PC**, SQL17.0.1000.7, TCP/NTLM/encrypt_option TRUE. Đây là DBA metadata diagnostic, **không extractor TLS hoặc least-privilege PASS**.

Configured certificate và startup error log cùng thumbprint **BAB7BCF8CEEFD64DB354180B5D2A92439BFDB7EB**; log2026-11-15 15:18:07.490 xác nhận đã loaded for encryption. Subject/issuer cùng CN=DESKTOP-OBDFK6B; SAN DESKTOP-OBDFK6B,localhost; Server Authentication EKU; validity UTC2026-11-15T08:01:27 →2028-11-15T08:11:27. Public DER SHA256 **BF957C2D7D78A5A613BB9EFCEC4C6E273694FAC0F9E924647D1E152F93067726**. Không export private key.

PC CurrentUser/Root có certificate này; LocalMachine/Root không có cùng thumbprint. Chain Build dưới PC thành công với revocation checking tắt cho bước inspection này; **không chứng minh revocation đã checked**. Hive SID-1007 chưa loaded; registry path không tồn tại **không chứng minh extractor không trust**. Fresh extractor handshake còn NOT VERIFIED. Không cần thay server certificate/name/service chỉ để sửa client-specific trust nếu cùng certificate đang được phục vụ. Requirements hostname/SAN/trust/validity theo [Microsoft certificate requirements](https://learn.microsoft.com/en-us/sql/database-engine/configure-windows/certificate-requirements?view=sql-server-ver17).

Read-only PowerShell inspections (PC; không load hive/đọc private key):

~~~powershell
$instanceId = (Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL').SQLEXPRESS
$network = Get-ItemProperty -LiteralPath ('HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\' + $instanceId + '\MSSQLServer\SuperSocketNetLib')
$network | Select-Object Certificate,ForceEncryption
$cert = Get-Item -LiteralPath ('Cert:\LocalMachine\My\' + $network.Certificate)
$cert | Select-Object Thumbprint,Subject,Issuer,NotBefore,NotAfter,HasPrivateKey,DnsNameList,EnhancedKeyUsageList
$cert.Extensions | Where-Object {$_.Oid.Value -eq '2.5.29.17'} | ForEach-Object {$_.Format($false)}
Test-Path -LiteralPath ('Cert:\CurrentUser\Root\' + $cert.Thumbprint)
Test-Path -LiteralPath ('Cert:\LocalMachine\Root\' + $cert.Thumbprint)
$chain = New-Object System.Security.Cryptography.X509Certificates.X509Chain
# Inspection only: records trust-chain result separately from revocation evidence.
$chain.ChainPolicy.RevocationMode = [System.Security.Cryptography.X509Certificates.X509RevocationMode]::NoCheck
$chain.Build($cert)
$chain.ChainStatus
~~~

Optional read-only DBA corroboration qua trusted SQL client: EXEC master.sys.sp_readerrorlog 0,1,N'certificate'. Đã chạy read-only log reader; access registry Parameters bị OS từ chối, không nâng quyền để vượt qua. Chỉ đọc SuperSocketNetLib đủ cùng startup log.

**Bước tiếp theo trước mutation:** mở fresh extractor PowerShell (Owner nhập password tương tác), chạy diagnostic nguồn không cần Raw password:

~~~powershell
runas /user:DESKTOP-OBDFK6B\wwi_extract "powershell.exe -NoProfile -NoExit"
# Trong cửa sổ wwi_extract:
Set-Location -LiteralPath 'D:\Code\Retail_Data_Platform\project1_Retail_Data_platform'
whoami /user
.venv\Scripts\python.exe ingestion/scripts/inspect_wwi_source.py --execute
~~~

Diagnostic không bypass TLS, không nạp dữ liệu, không gọi production loader bằng PC. --samples thêm TOP(1) mỗi object, --holdings-profile thêm small-table aggregates; output không row values. Exit0 chỉ hoàn tất metadata check, không G01/least-privilege PASS; rights output thuộc current session.

**Remediation PROPOSED, cần Owner authorization, NOT RUN:** nếu fresh extractor strict handshake còn fail chain và trust check đúng user thiếu cert, trust chính public certificate đã xác minh trong CurrentUser/Root của wwi_extract. Không import certificate không rõ nguồn; không machine-wide trust/service restart/ForceEncryption change. Nếu lỗi name/validity khác, STOP và review lại.

~~~powershell
# PC: chỉ export PUBLIC cert vào ignored .local sau Owner cho phép.
$thumb = 'BAB7BCF8CEEFD64DB354180B5D2A92439BFDB7EB'
$publicFile = Join-Path (Get-Location) '.local\wwi-sqlserver-public.cer'
New-Item -ItemType Directory -Path '.local' -Force | Out-Null
if (Test-Path -LiteralPath $publicFile) { throw 'STOP: existing artifact; inspect first' }
Export-Certificate -Cert (Get-Item -LiteralPath ('Cert:\LocalMachine\My\'+$thumb)) -FilePath $publicFile | Out-Null
Get-FileHash -LiteralPath $publicFile -Algorithm SHA256

# Chỉ trong fresh wwi_extract session, sau explicit trust authorization:
if ([System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value -ne 'S-1-5-21-2164258108-3044412014-540060861-1007') { throw 'STOP: wrong Windows identity' }
$publicFile = Join-Path (Get-Location) '.local\wwi-sqlserver-public.cer'
$expectedSha256 = 'BF957C2D7D78A5A613BB9EFCEC4C6E273694FAC0F9E924647D1E152F93067726'
$publicCert = Get-PfxCertificate -FilePath $publicFile
if ($publicCert.Thumbprint -ne 'BAB7BCF8CEEFD64DB354180B5D2A92439BFDB7EB' -or
    (Get-FileHash -LiteralPath $publicFile -Algorithm SHA256).Hash -ne $expectedSha256) { throw 'STOP: certificate mismatch' }
if ((Get-Date) -lt $publicCert.NotBefore -or (Get-Date) -ge $publicCert.NotAfter) { throw 'STOP: invalid certificate validity' }
if (Test-Path -LiteralPath ('Cert:\CurrentUser\Root\'+$publicCert.Thumbprint)) { throw 'STOP: already trusted; inspect the remaining TLS cause' }
Import-Certificate -FilePath $publicFile -CertStoreLocation Cert:\CurrentUser\Root
.venv\Scripts\python.exe ingestion/scripts/inspect_wwi_source.py --execute
~~~

[Import-Certificate](https://learn.microsoft.com/en-us/powershell/module/pki/import-certificate?view=windowsserver2025-ps) thao tác certificate store của đúng session. Proposed rollback chỉ sau Owner review: gỡ đúng thumbprint mới import nếu trước đó absent và không có dependency khác; không xóa wholesale root store. Trust action trên **chưa được thực hiện**. Private config/venv phải đọc được dưới extractor; không sửa ACL ở task này.

### Archive effective INSERT — không suy permission bit thành executable DML

Actual metadata: hai parent Customers/StockItems là SYSTEM_VERSIONED_TEMPORAL_TABLE, history_table_id trỏ đúng archives HISTORY_TABLE; cả hai history không PK. DBA grant/role closure đọc được: dedicated login/user SID khớp1007, không direct server/db role; đúng11 object SELECT +database CONNECT, không thấy INSERT/schema broad grants cho target/public/db-role closure. Audit này không mô phỏng đầy đủ Windows target token/ownership/module paths.

INSERT=1 trên hai archives là **Owner-provided evidence**, chưa independently rerun dưới fresh extractor trong task này. PC là sysadmin nên permission results trong PC session không đại diện wwi_extract. [HAS_PERMS_BY_NAME](https://learn.microsoft.com/en-us/sql/t-sql/functions/has-perms-by-name-transact-sql?view=sql-server-ver17) kiểm effective permission theo caller; không tự chứng minh một operation vượt qua mọi engine/table restriction. [Temporal limitations](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal/considerations-limitations?view=sql-server-ver17) cấm direct history data modification khi system-versioning đang hoạt động.

**Inference có giới hạn:** INSERT bit không đủ chứng minh extractor có thể insert vào bound history; chưa đủ evidence để gọi đây là harmless bug/đã least privilege PASS. Không thử DML, không DENY/REVOKE hoặc tắt versioning để test. Fresh diagnostic ghi raw rights + metadata; Owner cần quyết định sau evidence về permission paths/temporal restrictions. Production preflight hiện đòi INSERT=0 cho cả11; **vẫn BLOCKED ngay cả selected holdings**. Không tự thêm exception hoặc skip archives. Nếu muốn conditional temporal exception, phải có explicit recorded decision và guard/test riêng, không chỉ sửa test để xanh.

Phương án để Owner review, **PROPOSED/NOT IMPLEMENTED**: chỉ cho metadata INSERT=1 ở đúng hai named archives khi fresh extractor identity/token/permission paths đã kiểm, mọi current-table write và archive UPDATE/DELETE/ALTER/CONTROL đều0, và mỗi archive vẫn HISTORY_TABLE trỏ từ đúng parent SYSTEM_VERSIONED_TEMPORAL_TABLE. Guard phải fail nếu mất binding/parent versioning hoặc rights drift. Đây là điều chỉnh cách đánh giá security evidence cần explicit decision, không thêm quyền hoặc suy full least-privilege PASS; hiện code vẫn giữ strict-zero rule.

### Schema/type và Raw provisioning review

Actual11/11 exact name/order/type/NULLability match frozen contract, current156 columns +history31/25;9 PK đúng,2 archives không PK. Đối chiếu thêm51 FK column mappings với accepted dictionary: tất cả khớp,0 disabled/untrusted; history không FK. Có thể tái kiểm bằng [metadata FK SQL hiện có](../../data-models/wwi-metadata-queries.md). Computed fields IsFinalized/ConfirmedDeliveryTime/ConfirmedReceivedBy/Tags/SearchDetails được explicit projected và bounded sample đọc thành công. Không có actual mismatch cần đổi contract. Native geography22-byte samples round-trip qua parameter SELECT trong SQL17 PASS; không persistent PostgreSQL proof. SQL/read codecs không crash trên11 TOP(1), không khẳng định mọi possible value đã được khảo sát.

Raw actual: postgres:18 container retail-raw-postgres-1 healthy,127.0.0.1:55434, dedicated retail-raw_pg_data tại /var/lib/postgresql; app retail_ingest/retail_raw18.7/C.0 payload tables;2 metadata tables runs/object_runs, counts0/0; raw CREATE=false. SELECT-only target preflight → **TARGET_DDL_REQUIRED**. Không restart, DDL hoặc grants trong WWI-06B readiness.

Prepared SQL:11 Raw tables,2 technical identity columns mỗi table + source columns; current UNIQUE(run_id,sourcePK), history chỉ occurrence PK; precise numeric/text-C/bytea;11 serving views;4 control tables. PK prefix hỗ trợ run read-back; không thêm unsupported source FK/identity/default/computed business logic. Existing runs/object_runs không ALTER; explicit context guard retail_raw/postgres và BEGIN/COMMIT; runtime role không superuser/CREATE.

**Setup không phải no-op idempotent installer:** new-only. Chạy lần hai hoặc gặp collision sẽ fail/rollback transaction, không overwrite existing objects, không auto reset/resume initialization. Vì thế Owner phải kiểm actual namespace trước apply; không dùng IF NOT EXISTS để che drift. Static review không bằng SQL engine compilation.

**Provisioning command cần Owner authorization riêng, NOT RUN** (PC/local DBA; inspect đúng Docker context/target và existing state trước):

~~~powershell
if ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name -ine 'DESKTOP-OBDFK6B\PC') { throw 'STOP: Docker requires PC operator' }
$dockerExe = 'C:\Users\PC\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe'
if (-not (Test-Path -LiteralPath $dockerExe)) { throw 'STOP: approved Docker CLI absent' }
& $dockerExe inspect retail-raw-postgres-1 --format '{{.Config.Image}}|{{json .NetworkSettings.Ports}}|{{json .Mounts}}'
if ($LASTEXITCODE -ne 0) { throw 'STOP: Docker target inspection failed' }
# Future separately authorized apply only; NOT RUN in provisioning verification task.
Get-Content -LiteralPath infrastructure/postgres/full_load.sql -Raw -Encoding UTF8 |
    & $dockerExe exec -i retail-raw-postgres-1 psql -X -U postgres -d retail_raw -v ON_ERROR_STOP=1
if ($LASTEXITCODE -ne 0) { throw 'STOP: provisioning failed; inspect, do not reset/retry blindly' }
~~~

Scope authorization: CREATE11 payload tables/11 views/4 controls, initial raw_current(NULL), exact proposed grants cho existing retail_ingest. Không source changes, new roles, ALTER existing metadata, broad grants hoặc other database. Runtime app chỉ SELECT/INSERT payload; controls SELECT/INSERT hoặc SELECT/UPDATE pointer; views SELECT; existing metadata SELECT/INSERT/UPDATE. Sau apply kiểm owners/schema/types/constraints/grants bằng preflight; chưa cấp quyền auto-run load. Không drop objects để rollback sau khi có payload; failed initialization transaction phải rollback toàn phần, unknown ACK → inspect.

### Selected-object smoke procedure — PREPARED, NOT RUN

Chọn **Warehouse.StockItemHoldings**, chỉ227 current rows/9 columns ở observation này, integer PK, decimal(18,2), Unicode BinLocation và datetime2(7), không geography/BLOB/history payload. Không bắt đầu inventory mart/daily balance. Archive gate vẫn phải resolve; chọn bảng này không bypass all11 security check.

Observation source dưới PC, không fixed acceptance constants: rows227/distinct StockItemID227; SUM(bigint QuantityOnHand)=30343296; SUM(decimal38,2 LastCostPrice)=5107.92; NULL counts cả9 columns=0; F2 min2016-05-31T07:00:00.0000000/max2016-05-31T12:00:00.0000000. Đây là field controls, **không KPI/COGS definition**. Fresh smoke phải remeasure, không hardcode snapshot cũ.

Trình tự sau khi Owner cho phép **riêng selected-object load**, dưới wwi_extract. Target đã provision/PASS ở WWI-06B; hiện phải STOP vì source gate chưa resolve. WWI-06C bổ sung Python execution/TLS prerequisites ở cuối tài liệu; các lệnh load dưới đây vẫn PREPARED, NOT RUN:

~~~powershell
Set-Location -LiteralPath 'D:\Code\Retail_Data_Platform\project1_Retail_Data_platform'
whoami /user
.venv\Scripts\python.exe ingestion/scripts/inspect_wwi_source.py --execute --holdings-profile
if ($LASTEXITCODE -ne 0) { throw 'STOP: source metadata/TLS check' }
.venv\Scripts\python.exe -m ingestion.full_load preflight --object Warehouse.StockItemHoldings --env-file .env
if ($LASTEXITCODE -ne 0) { throw 'STOP: unresolved source rights or target schema/grants' }
$candidateRun = [guid]::NewGuid().ToString()
$candidateRun
.venv\Scripts\python.exe -m ingestion.full_load load --object Warehouse.StockItemHoldings --batch-size 64 --run-id $candidateRun --execute --env-file .env
if ($LASTEXITCODE -ne 0) { throw ('STOP: inspect run '+$candidateRun+'; no automatic retry') }
.venv\Scripts\python.exe -m ingestion.full_load reconcile --object Warehouse.StockItemHoldings --run-id $candidateRun --env-file .env
if ($LASTEXITCODE -ne 0) { throw 'STOP: durable reconciliation failed' }
.venv\Scripts\python.exe ingestion/scripts/inspect_wwi_source.py --execute --holdings-profile
~~~

Không --publish. Với batch64 và227 rows mong đợi4 batches64/64/64/35 nếu source không đổi. Expected: one new run/capture, runs RUNNING→SUCCEEDED; object PENDING→RUNNING→SUCCEEDED/reconciliation PASS, source/extracted/loaded counts bằng fresh count; load_audits count/digest; duration nonnegative; raw_current/publication không đổi, serving views không nhận candidate. Technical SUCCESS không chứng minh consistent source; khi chưa actual no-writes proof vẫn UNVERIFIED/unpublished.

Post-load read-only control query dưới app (không có command load bên trong; cần các proposed objects đã provision và run đã có):

~~~powershell
@'
import json,sys
from pathlib import Path
from uuid import UUID
from ingestion.common.config import settings
from ingestion.common.contracts import select_objects
from ingestion.loaders.postgres import PostgresTarget
rid=UUID(sys.argv[1]); target=PostgresTarget(settings(Path('.env')))
try:
    target.connect()
    print(json.dumps(target.reconcile(rid,select_objects(['Warehouse.StockItemHoldings']))))
    with target.transaction():
        target.connection.execute('SET TRANSACTION READ ONLY')
        row=target.connection.execute("""SELECT COUNT(*),COUNT(DISTINCT "StockItemID"),
            SUM("QuantityOnHand"::bigint),SUM("LastCostPrice"),MIN("LastEditedWhen"),MAX("LastEditedWhen"),
            COUNT(*) FILTER(WHERE "LastEditedWhen" IS NULL),
            COUNT(*) FILTER(WHERE length("LastEditedWhen")<>27)
            FROM raw.warehouse_stockitemholdings WHERE _run_id=%s""",(rid,)).fetchone()
        meta=target.connection.execute("""SELECT r.status,r.consistency_state,o.source_row_count,
            o.extracted_row_count,o.loaded_row_count,o.reconciliation_state,
            r.finished_at-r.started_at
            FROM ingestion_meta.runs r JOIN ingestion_meta.object_runs o USING(run_id)
            WHERE r.run_id=%s""",(rid,)).fetchone()
        pointer=target.connection.execute('SELECT publication_id FROM ingestion_meta.raw_current WHERE singleton').fetchone()
        print(json.dumps({'raw_counts_sums_min_max_null_length':[str(v) if v is not None else None for v in row],
                          'metadata':[str(v) if v is not None else None for v in meta],
                          'publication_pointer':str(pointer[0]) if pointer and pointer[0] else None}))
finally:
    target.close()
'@ | .venv\Scripts\python.exe - $candidateRun
~~~

Evidence PASS smoke: saved runId/CLI exit0, dedicated identity/strict TLS/no broad rights, exact target preflight, before/after source controls vs Raw controls, loaded PK set/count + typed source-read/Raw digest equality, required NULLs và temporal27 chars, fresh-session durable reconcile, complete metadata và unchanged publication pointer. Nếu cần certify source-consistent dataset phải có independent window proof; merely matching before/after counts không đủ. Nên ghi pointer trước smoke bằng same SELECT để so after.

Known failure: rollback toàn capture, no payload/audit/publication for failed run, metadata FAILED/loaded0 chỉ sau acknowledged rollback; previous published state giữ. Unknown COMMIT/registration outcome: dùng runId có trong output để inspect bằng fresh session; không tự mark FAILED, delete hoặc retry. Offline failure tests không thay fault-injection runtime acceptance.

### Recovery limitations theo mức nghiệm thu

| Mục tiêu | Sealed-chunk/attempt replay thiếu có chặn không? |
| --- | --- |
| A. Selected-object smoke, unpublished | Không tự nó chặn controlled smoke: transaction rollback/new-capture retry đủ kiểm basic path. Target provisioning đã PASS; source rights/TLS/execution context vẫn chưa đủ điều kiện |
| B. Full all11 candidate, unpublished | Không tự nó cấm disposable candidate nếu Owner chấp nhận full restart cost; chưa được giao/executed. Không gọi đây exact resume/replay hoặc operationally accepted full load |
| C. MVP-G03/WWI-06 final acceptance | Có: accepted persisted chunk/attempt/retained-content replay requirements còn thiếu, cần implementation + tests hoặc explicit Owner scope decision; không tự giảm criteria |

Source READ_WRITE, RCSI OFF, SNAPSHOT isolation OFF đã được quan sát ở review này. Không tự bật isolation options hoặc dùng snapshot semantics chưa có. Full candidate publication còn cần external verified consistency/full-scope geography adapter/persistence proof và actual runtime reconciliation/recovery. **Current blockers cho first selected load:** executable Python environment dưới extractor, repeatable strict TLS/least privilege (archive anomaly decision), và Owner selected-load authorization. Target DDL/grants đã PASS ở WWI-06B. Không thêm governance/staging/ACL gates mới.

Validation:44 Full Load/readiness +22 Raw foundation +18 source security +12 B9 offline tests; kết quả actual được xác minh trước commit. Diagnostics/code test không phải privileged SQL execution. Không commit source rows, private config/password hoặc certificate private key.

## WWI-06C — History permission investigation, 2026-11-18

**BLOCKED — chưa đủ điều kiện selected-object smoke.** Bắt đầu main/cf94d05247ba9ac0d3fe7f440c2e73156076cfaf, working tree clean. Chỉ bổ sung diagnostics/tests và cập nhật runbook/tracker; không sửa production extractor, permission contract hoặc accepted temporal semantics. Không source/target writes, grants, certificate/ACL changes, dependency installation, Full Load hoặc publication.

### Runtime evidence và giới hạn

Project-local .venv trỏ base Python3.12.10 tại `C:\Users\PC\AppData\Local\Programs\Python\Python312\python.exe`. Launch bằng credential riêng trả Win32 access error5 và stderr `No Python at ...Python312...`; ACL đọc được của base executable/directory chỉ có SYSTEM/Administrators/PC. **Python production preflight dưới wwi_extract = NOT RUN**, không gán cho nó một SQL runtime error chưa quan sát. Không dùng PC/DBA hoặc EXECUTE AS thay extractor, không copy Python/install package/sửa ACL để vượt prerequisite.

Để thu thập subset độc lập, đã chạy Windows PowerShell System.Data.Odbc với Driver18/Integrated Auth/Encrypt=yes/TrustServerCertificate=no dưới actual Windows SID đã duyệt. Adapter dùng SELECT queries/parameters từ [collector](../../../ingestion/scripts/inspect_wwi_source.py), không chạy loader. Lượt đầu verified27/30 queries;3 queries role/grant closure NOT_VERIFIED, không coi là empty grants. Collector sau đó dùng active `sys.user_token` cho effective role/grant scope; các query sửa này chưa được live-verify do kết nối mới fail TLS.

| Kiểm tra | Bằng chứng actual / kết quả |
| --- | --- |
| Windows identity | DESKTOP-OBDFK6B\wwi_extract; SID S-1-5-21-2164258108-3044412014-540060861-1007 |
| SQL identity/target | ORIGINAL_LOGIN() = SUSER_SNAME() = cùng Windows principal; SQL SID khớp; USER_NAME()=wwi_extract; WideWorldImporters / DESKTOP-OBDFK6B / SQLEXPRESS; ProductVersion17.0.1000.7 |
| 9 current objects | HAS_PERMS: SELECT=1; INSERT/UPDATE/DELETE/ALTER/CONTROL/TAKE OWNERSHIP=0 trên từng object, VIEW DEFINITION=0 |
| Sales.Customers_Archive | SELECT/INSERT=1; UPDATE/DELETE/ALTER/CONTROL/TAKE OWNERSHIP=0; fn_my_permissions OBJECT-level trả SELECT và INSERT |
| Warehouse.StockItems_Archive | Cùng effective rights và fn_my_permissions OBJECT-level như Customers_Archive |
| Temporal bindings | Customers_Archive object1010102639/type1 ← Customers802101898/type2; StockItems_Archive1458104235/type1 ← StockItems1314103722/type2; mỗi parent_history_id khớp, history owner dbo |
| Roles/token | sysadmin/securityadmin/db_owner/db_datareader/db_datawriter/db_ddladmin/db_securityadmin=0; database token chỉ wwi_extract/public; visible server role edges rỗng; không admin role trong captured SQL token |
| Broad rights | CONTROL SERVER/SELECT ALL USER SECURABLES/IMPERSONATE ANY LOGIN/ALTER ANY LOGIN=0 |
| Database/schema | DATABASE effective CONNECT và hai VIEW ANY COLUMN ... KEY DEFINITION; SCHEMA Sales/Warehouse fn_my_permissions rỗng. Không coi metadata visibility rights là write grant |
| Visible server grants | CONNECT SQL cho wwi_extract và BUILTIN\Users; public endpoint CONNECT và VIEW ANY DATABASE. Không phải full global grant audit |
| Object grant/inheritance audit | NOT_VERIFIED cho hai object-grant queries và role-closure query đầu tiên; chưa có current extractor evidence đủ để kết luận không tồn tại grant path |
| Strict TLS | Một fresh connection PASS với msodbcsql18.dll; fresh connection kế tiếp FAIL SQLSTATE08001/native -2146893019. Giữ cả hai kết quả, chưa repeatable PASS; không fallback trust bypass |

Local sanitized evidence được giữ trong ignored `.local`, không chứa password/payload: `wwi06c-odbc-first-pass.json` SHA256 `0936d6a761c5922605c0051709020dd70139e06283573d2d0bdef7f27944247f`; `wwi06c-odbc-tls-failed.json` SHA256 `2ff82ac29f0c970716405bf05fddfe3484f89dc66a03ad9a2a4058db6b358cc6`. Đây là traceability của local results, không tạo lại mandatory execution manifest. Không coi temporary adapter là supported production preflight hoặc thay TLS/role acceptance bằng offline test.

**Owner-run follow-up:** Owner xác nhận đã chạy collector trong interactive wwi_extract session. File observed_at `2026-11-18T16:39:46.0755421+00:00` xác nhận Windows principal/SID-1007; ODBC fail trước metadata,0 queries với SQLSTATE08001/native -2146893019. `certutil -error 0x80090325` xác nhận SEC_E_UNTRUSTED_ROOT / certificate chain not trusted; đây là TLS observation, không kết luận về SQL permissions. Preserved `wwi06c-owner-tls-failed.json` SHA256 `2c753ccc1cc5c127e728e3f7ee1b103f73e1734805ea6b45435b33c16d0ef006` trong ignored .local.

Read-only PC corroboration vẫn thấy configured thumbprint BAB7BCF8CEEFD64DB354180B5D2A92439BFDB7EB, LocalMachine/My public DER SHA256 BF957C2D7D78A5A613BB9EFCEC4C6E273694FAC0F9E924647D1E152F93067726 và còn validity; LocalMachine/Root không có. Hive SID-1007 hiện visible và Root registry entry cùng thumbprint **có tồn tại**. Registry presence không chứng minh current-user logical store/chain tin cậy chứng chỉ; không tự import lặp hoặc kết luận certificate absent. Không xác nhận live server-presented certificate chỉ từ configured store entry.

Temporary `.local/wwi06c-odbc-runtime.ps1` đã bổ sung read-only exact-certificate store/hash/chain diagnostics, PowerShell parser PASS; **runtime phần bổ sung NOT RUN**, Owner hiện chưa thể chạy thêm. Diagnostic chain dùng NoCheck riêng cho revocation inspection, không sửa strict ODBC TLS và không chứng minh revocation PASS. Chỉ đọc public certificate, không export private key/import/remove/trust mutation. Khi Owner chạy lại, dùng absolute script path vì .NET ReadAllText relative path theo process working directory, có thể khác PowerShell Set-Location. Source blocker và production policy giữ nguyên.

### Kết luận permission và remediation

**Verified:** anomaly effective INSERT ở đúng hai linked history objects tồn tại trong actual extractor context, không phải kết quả PC/sysadmin hoặc chỉ một hàm. **Unverified:** cơ chế tạo effective INSERT; có grant path ngoài phần visibility đã thu hay không; executable DML capability chưa thử và không được phép thử. Mức tin cậy cao cho observation, chưa đủ cho root-cause classification hoặc exception approval.

[HAS_PERMS_BY_NAME](https://learn.microsoft.com/en-us/sql/t-sql/functions/has-perms-by-name-transact-sql?view=sql-server-ver17) kiểm effective permission của caller. [Temporal limitations](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal/considerations-limitations?view=sql-server-ver17) cấm sửa trực tiếp history data khi bound versioning hoạt động; quy tắc engine đó không giải thích riêng nguồn gốc permission bit. Không gọi đây harmless bug, không suy đã chứng minh no-write capability hoặc least-privilege gate PASS.

**Khuyến nghị hiện tại:** giữ blocker và strict-zero production guard. Trước tiên cần Python environment đọc/chạy được bởi approved identity và strict TLS lặp lại ổn định trong chính context đó; không tự sửa OS trust/ACL. Sau đó chạy collector/preflight bằng commands dưới đây để hoàn tất own-token object grants/role evidence. Nếu tìm được unintended grant cụ thể: trình exact REVOKE delta cho Owner trước thao tác. Chỉ khi evidence đủ chứng minh temporal-specific behavior mới trình exception cho đúng hai named histories, verified type1/type2 binding, mọi ordinary-table DML và archive UPDATE/DELETE/ALTER/CONTROL vẫn0, NULL/missing/drift phải fail closed. Đây vẫn là **PROPOSED, NOT IMPLEMENTED** và cần Owner duyệt material security-contract change; không cần thêm quyền để chẩn đoán.

~~~powershell
# Trong actual wwi_extract session, sau khi Python execution prerequisite được resolve.
# Collector exit0 = collection complete; exit2 = metadata query NOT_VERIFIED; không gate approval.
.venv\Scripts\python.exe -X utf8 ingestion/scripts/inspect_wwi_source.py --execute --history-permissions
# Chỉ SELECT/preflight, không load; unchanged guard vẫn reject archive INSERT=1.
.venv\Scripts\python.exe -X utf8 -m ingestion.full_load preflight --object Warehouse.StockItemHoldings --env-file .env
~~~

Existing [smoke procedure](ingestion-history.md#selected-object-smoke-procedure--prepared-not-run) giữ target Warehouse.StockItemHoldings/batch64/new run ID/retail_ingest/unpublished. Chạy sau riêng Owner load authorization và source gate PASS; so fresh source/Raw count, distinct PK, numeric totals, NULL distribution, F2/digest, durable audit/metadata, unchanged publication pointer. Snapshot227 rows/totals cũ chỉ tham khảo, không acceptance constants. Smoke **NOT RUN**; target provisioning PASS giữ evidence WWI-06B, không re-provision.

Offline regressions:48 Full Load/readiness,22 Raw foundation,18 source security,12 B9 và4 Raw readonly-verifier tests PASS. Bốn tests mới kiểm real-identity fence, preserved all11 matrix/no invented cause, SQL SID/user mapping và denied metadata/no-secret handling. Existing archive-INSERT blocker/TLS-no-bypass tests giữ nguyên; không nâng MVP-G01, WWI-06B hoặc WWI-06C thành DONE từ offline PASS.
