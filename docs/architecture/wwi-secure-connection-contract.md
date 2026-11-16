# WWI-05 / M1A — Secure Connection Contract

**2026-11-16; documentation contract, production connector Not implemented yet.** [Approval](wwi-phase-1-closure-approval.md), [actual evidence](wwi-m1a-gate-evidence.md), [readiness report](wwi-m1a-environment-readiness.md). Phân biệt Verified checkpoint settings với Proposed future configuration; không tự triển khai adapter/retry/schema hoặc cấp quyền.

## 1. Identity boundaries

| Identity | Trạng thái | Quy tắc |
| --- | --- | --- |
| Developer Windows Integrated | Verified secure connectivity nhưng sysadmin/write permissions | Chỉ bounded SELECT trong M1A; FAIL suitability cho extraction, không dùng làm production default. |
| Extraction service identity | BLOCKED — chưa approved profile trong phạm vi inspected | DBA/PO duyệt identity riêng, effective SELECT/meta current+H đúng scope; không write/admin/DDL; không kế thừa rộng qua roles. Không tạo/grant trong task này. |
| PostgreSQL target writer/control/consumer | PENDING — chưa approved target/profile/roles | Tách source identity và B9 identity; quyền theo scope/schema/control purpose sau physical review. Không tự chọn users/grants hoặc dùng superuser. |
| B9 b9_poc | Historical sandbox only | Không reuse credential/database/container/volume cho Raw, không connect/restart trong M1A. |

## 2. SQL Server source contract

- **Verified endpoint:** tcp:DESKTOP-OBDFK6B,1433; expected instance SQLEXPRESS; database WideWorldImporters. Allowlist phải fail closed khi actual machine/instance/database khác; không fallback local instance/database.
- **Verified transport:** ODBC Driver18, Windows Integrated auth, Encrypt=yes, TrustServerCertificate=no; session TCP/encryptionTRUE/authNTLM. Certificate trust/name validation giữ bật; lỗi TLS phải dừng, không bypass hoặc tự import certificate.
- **Checkpoint timeouts:** login5s/query20s reuse existing B9 source settings; không automatic retry. Đây là bounded verification values, chưa quyết định production connection/retry budget.
- **Source policy:** SELECT/metadata/bounded reads; client access-mode read-only hint chỉ defense-in-depth, không effective permission guarantee. G02 cần DBA metadata proof và approved profile riêng; không test DML để chứng minh deny.
- **Consistency:** G01/RG01 vẫn thiếu method/proof. Không gọi nhiều bounded reads là common snapshot, không activate isolation/CDC/CT hoặc đổi WWI gốc.
- **Scope:**9 current+2 physical H theo accepted contracts; query identifiers chỉ từ trusted allowlist, bind data parameters. Metadata SELECT rights không là full-field adapter/projection correctness.

## 3. PostgreSQL target contract — PENDING APPROVAL

Không có approved Raw target được tìm thấy. Native service/port5432 chỉ được phát hiện; B9 stopped/55433 giữ nguyên. Không tự chọn native service hoặc Docker làm deployment mới.

**Proposal cần PO/INF/DBA phê duyệt trước provision/connect:** xác định target owner, environment marker, host+port+database allowlist, server version cần hỗ trợ/actual verify, dedicated database và role ngoài B9, credential delivery ngoài Git, verified TLS hostname/CA, storage/volume/access/capacity/backup boundaries, expected encoding/collation và quyền theo purpose. Names/ports/users/passwords/physical objects chưa tự chốt.

TLS target đề xuất verify-full với trusted CA/hostname; không dùng sslmode disable/allow/prefer hoặc bypass như production default. Đây là proposed requirement cho target contract, chưa claim current host/B9 đã có TLS hoặc Owner duyệt cách triển khai certificate. Với local non-TLS exception cần explicit Owner security decision; không tự tạo exception.

Khi có profile được duyệt: chỉ metadata SELECT version/current_database/current_user/encoding/pg_database collation và pg_stat_ssl cho own backend trong checkpoint; không CREATE/INSERT/schema/table changes. B9 TEXT/C representation vẫn authoritative cho relevant datetime2(7) ở physical design sau; connection check không approve whole Raw schema/database default collation.

## 4. Configuration và secret loading

| Config | Hiện có / đề xuất | Contract |
| --- | --- | --- |
| WWI_SQLSERVER_HOST | Existing template, blank | Supply approved explicit TCP endpoint; không fallback hostname khác. |
| WWI_SQLSERVER_DATABASE | Existing template | Match approved WideWorldImporters allowlist. |
| WWI_SQLSERVER_AUTH_MODE | Existing template, blank | Checkpoint dùng Windows Integrated; extraction identity/profile phải PO/DBA approved, không hardcode user/password. |
| WAREHOUSE_DATABASE_URL | Existing template, blank | Chưa có approved target; future parse/validate allowlist/TLS, không log URI chứa credential. |
| BIGQUERY_PROJECT_ID | Existing template, blank | Extension, không prerequisite M1A; không set/provision cloud. |
| Driver/TLS/certificate/profile và timeout/retry settings | Proposed logical config requirements, chưa thêm biến hoặc loader | Mapped names/precedence/validation cần review trong connector task, không giả .env.example đã hỗ trợ đầy đủ. |

Source checkpoint dùng đúng endpoint task cho phép và secure flags từ existing B9 source helper; không cần secret source password. Future secrets từ approved environment/local excluded profile hoặc approved secret store; không tự thêm công nghệ. .env không được loader tự hỗ trợ chỉ vì template tồn tại; production loader chưa implement.

Không in passwords/tokens/private keys/DSNs/URLs. Log chỉ check ID, stage, sanitized SQLSTATE/category, version/allowlisted target marker và status; principal name được fingerprint nếu không cần hiển thị. Không dump os.environ/Docker Config.Env hoặc raw exception có credential.

## 5. Error, timeout, retry và cleanup

- Phân biệt configuration/allowlist, authentication/authorization, TLS trust/name, network/timeout, SQL query/metadata permission, fidelity và unknown-outcome. Giữ SQLSTATE khi có, không biến missing profile thành connection PASS.
- M1A không automatic retry hoặc fallback. Future connection retries chỉ transient failures, bounded budget/backoff được review; không retry TLS/auth/allowlist bằng weaker security, không tự chọn numeric production values.
- Dùng connection/cursor cleanup chắc chắn qua context manager/closing cả exception path; query timeout hữu hạn; không idle open transaction. Parameter binding cho values; dynamic identifiers chỉ explicit approved list.
- Read-only checkpoint không tạo writes/checkpoint hoặc ACK. Future G08/INC-06 chỉ ACK sau durable reconciled accepted publication; connection success/task success không là ingestion acceptance.

## 6. Code review và acceptance boundaries

Existing code chỉ tests/integration/b9_precision/poc.py và test_poc.py. Source helper dùng exact B9 F2 path, secure Windows/TLS flags,5/20s,closing và bind parameters. Target helper có opt-in historical writes/test table; **không dùng/không chạy như M1A connector**. M1A inline helper chỉ SELECT và metadata, không production module mới.

Verified: secure developer connection/versions/11 bounded reads và effective privileges; **not verified:** extraction least-privilege identity, Raw target/TLS/permissions, full projection/type codecs/common capture, runtime retry/publication/SCD2. G01–08/RG01–12/CG01–10/B5 và72 scenario statuses giữ nguyên. Contract documentation completion không là approval của proposed target/config hoặc operational readiness.
