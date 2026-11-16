# WWI-05 / M1A — Local Environment Readiness Report

**2026-11-16. Checkpoint B**, sau governance commit A `554c5ea3c5eab5f9d3f5ad98f543b3739d0e0d95`. Authority: [APPROVAL-01–05](wwi-phase-1-closure-approval.md). [Evidence/commands](wwi-m1a-gate-evidence.md), [Secure Contract](wwi-secure-connection-contract.md), [Handoff](wwi-m1a-handoff.md). Không production ingestion hoặc provisioning.

## 1. Hai kết luận độc lập

- **Verification checkpoint:** hoàn tất phạm vi kiểm tra/tài liệu khi static/staged QA PASS; thiếu prerequisites được ghi FAIL/BLOCKED/NOT RUN có evidence. Đây không là Owner nghiệm thu operational infrastructure.
- **Operational readiness: BLOCKED.** Tested developer identity là sysadmin; thiếu approved extraction profile, concrete source consistency proof và approved Raw PostgreSQL target. WWI-05 giữ IN_PROGRESS; Phase2 In Progress; M2/M3 chưa bắt đầu.
- Parent WWI-04 DONE — Design, Phase1 Completed — Requirements & Source Design theo approval hiện tại, không mở lại vì runtime prerequisites chưa đạt.

## 2. Environment được kiểm chứng

| Thành phần | Actual observed | Kết luận |
| --- | --- | --- |
| Windows | Windows11 Home Single Language;10.0.26200/build26200;64-bit/AMD64 | PASS inventory |
| Python | CPython3.12.10; project-local .venv; base Python312 trên máy | PASS, không install/global changes |
| Packages | pip==25.0.1; psycopg==3.3.9; psycopg-binary==3.3.9; pyodbc==5.5.0; typing_extensions==4.16.0; tzdata==2026.6 | PASS import/inventory; không production dependency approval |
| ODBC | SQL Server legacy; Access/Excel/Text drivers; ODBC17 và18 | Driver18 available; actual loaded18.06.0002/msodbcsql18.dll |
| psycopg | 3.3.9; binary implementation; libpq integer180004 | PASS driver; không PostgreSQL server version |
| Client commands | python/py/sqlcmd/docker có trên PATH; psql không có | Không cài psql; psycopg đủ cho future SELECT checks |
| Docker | context desktop-linux; Client/Server29.8.2; Linux/amd64; Desktop4.94.0; kernel6.18.58.1-microsoft-standard-WSL2 | PASS inspection, không start/reconfigure |
| Compose | 5.5.1 | PASS CLI, chưa có project Compose definition |
| PostgreSQL host | service postgresql-x64-18 Running; listener5432 trên IPv4/IPv6 | Chỉ existence; database/role/version/TLS/approval chưa xác minh |
| B9 | retail-b9-pg-poc / postgres:18, exited ExitCode0; configured127.0.0.1:55433→5432; dedicated volume retained | Không start/reuse/connect/test; không Raw target |
| Docker volumes | retail-b9-pg-poc-data; mage-demo-main_pgdata | Chỉ liệt kê, không dùng/sửa tài nguyên khác |

Không dùng việc host5432 lắng nghe để suy ra có approved warehouse. Docker có engine chạy không chứng minh project stack tái lập được.

## 3. SQL Server actual results

Observed UTC từ source: `2026-11-16T07:09:32.1609379`. Secure connection tới `tcp:DESKTOP-OBDFK6B,1433`; actual machine DESKTOP-OBDFK6B, instance SQLEXPRESS, database WideWorldImporters. Server version17.0.1000.7, Express Edition64-bit; ODBC DBMS string17.00.1000 là driver representation riêng.

Windows Integrated auth, session NTLM/TCP/encrypt_option TRUE; client Encrypt=yes/TrustServerCertificate=no. Kết nối thành công dưới certificate-validation settings, không bypass. Không export certificate chain hoặc claim đã audit expiry toàn hệ thống.

Actual principal được giữ dưới fingerprint SHA-256 `5eecf0d76c45635cd7b2026ff0ebb098811ebd393fc08164a804c28e9a92f27d`; ORIGINAL_LOGIN và SUSER_SNAME khớp fingerprint, không ghi raw principal name/connection string/secret. **sysadmin=1; CONTROL SERVER=1** ở follow-up đúng permission class; database INSERT/UPDATE/DELETE/ALTER=1. TOP(1) constant SELECT và permission checks thành công11/11 populations; không đọc business payload, COUNT_BIG hoặc full extraction.

Do đó **FAIL** least-privilege suitability của identity đang test; approved extraction identity/profile vẫn **BLOCKED**. Client read-only hint không hạn chế server permissions. Database is_read_only=false không là project permission để ghi; task chỉ SELECT. Snapshot isolation OFF, RCSI=false, CDC=false, CT=0 giữ nguyên quan sát; không bật settings. Bounded reads không chứng minh common consistent capture/no-writes interval.

## 4. PostgreSQL và security

Không tìm thấy approved Raw target profile trong repo/process environment inspected: root .env không có; các biến WWI/RAW_PG/PG/POC/SQLSERVER liên quan không được set; WAREHOUSE_DATABASE_URL template trống. Local credential config duy nhất được nhận diện phục vụ B9. Không kết luận không tồn tại DB/login ở nơi khác; cần Owner/DBA cung cấp approved profile.

Raw PostgreSQL readiness **PENDING/BLOCKED**; target connection/version/encoding/collation/user/TLS checks **NOT RUN**. Không kết nối native5432 hoặc B9, không tạo target. [Contract §3](wwi-secure-connection-contract.md#3-postgresql-target-contract--pending-approval) ghi proposal cần duyệt.

Security scan129 tracked files và known sandbox secret value trong memory:0 pattern/value findings; .gitignore bảo vệ .env/.env.local/B9 config/B9 env và credentials pattern. Không in secret. B9 source helper bật certificate validation; target helper là historical write-enabled PoC, không phải production connector và không được chạy trong M1A. Không phát hiện explicit TLS bypass literal trong hai Python files; không coi absence of literal là proof PG TLS đã bật.

## 5. Reproducibility gaps

| Gap | Actual evidence | Remediation đề xuất / owner |
| --- | --- | --- |
| Production dependency declaration | Pinned requirements chỉ dưới tests/integration/b9_precision,6 installed packages; chưa ingestion/dbt/Airflow/pytest runtime | IN/INF trình dependencies trong implementation task riêng, không cài từ task này |
| Environment contract | .env.example có WWI_SQLSERVER_HOST/DATABASE/AUTH_MODE,WAREHOUSE_DATABASE_URL,BIGQUERY_PROJECT_ID;4 trống và1 database identifier; thiếu timeout/TLS/profile details cho production | Dùng Secure Contract làm proposal; PO review trước implement/template update |
| Secure source access | Developer sysadmin; không approved extraction profile | DBA/PO chuẩn bị least-privilege identity, grants/current+H/TLS; không dùng sysadmin làm default |
| Consistent source | Chưa writer-control/window/copy evidence | SO/DBA+PO duyệt concrete A02 proof trước capture |
| Target/bootstrap | Native PG service có nhưng không approved Raw DB/profile; không project Compose/bootstrap | PO/INF/ST duyệt target contract và hướng dẫn tái lập trước provisioning; external WWI prerequisites/license phải được ghi |
| End-to-end setup | README hiện ghi planned/no commands; chỉ B9 có commands lịch sử | M1 chưa đủ operational DoD; bổ sung runbook khi setup được giao, không replay B9 creation/install commands |

## 6. Validation và phạm vi Git

**Static QA PASS ngày2026-11-16:**133 visible text files/127 Markdown;1.034 local links/anchors không lỗi; đúng15 Markdown paths (11 sửa+4 mới),118 protected hashes không đổi,31 gate entries và72 NOT RUN scenario rows giữ nguyên;26 M1A rows =17 PASS/1 FAIL/4 BLOCKED/4 NOT RUN.0 secret pattern/known-value findings; format/table/fence/scope/diff checks đạt.10 local B9 evidence/config hashes và Docker stopped state/resource names không đổi. Chỉ commit sau staged-content/secret/diff verification PASS; không chạy DB integration suites hoặc B9 tests.

Chỉ4 deliverables M1A và related trackers/index/module READMEs được cập nhật. Không Python/SQL code file, .env/example, requirements, Docker definition hoặc schema được sửa. Commit B chỉ sau QA PASS; no push. Governance commit A không bị amend/reset.

Actual staged QA B PASS:15 Markdown blobs khớp working files sau Git line-ending normalization;0 staged secret findings,git diff --cached --check đạt,identity configured/no active hooks/no remote. Current tested-identity FAIL và4 BLOCKED prerequisites vẫn giữ trong báo cáo; local documentation commit không cấp operational approval.
