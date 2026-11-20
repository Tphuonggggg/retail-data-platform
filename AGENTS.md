# Quy t?c l?m vi?c

MVP-RESET-01 (Owner, 2026-11-19) supersede c?c security/runtime acceptance c?; l?ch s? ? [archive](docs/archive/pre-reset/README.md).

- T?i li?u ti?ng Vi?t, code/??nh danh ti?ng Anh; ch? l?m task ???c giao, ??c t?i li?u v? ki?m tra Git tr??c khi s?a.
- B?o to?n thay ??i ch?a commit; kh?ng t? chuy?n phase/nghi?m thu ho?c push.
- Gi? source SELECT-only, kh?ng t? DML/DDL/GRANT, kh?ng x?a database/volume, kh?ng auto migration.
- Kh?ng commit secrets/.env/source extracts. Kh?ng log DSN/password/driver exceptions ch?a secrets.
- Windows Authentication d?ng current development account. Admin source ph?i explicit development opt-in, kh?ng fallback credential.
- TLS Encrypt=yes; TrustServerCertificate=no m?c ??nh. APP_ENV=development m?i cho explicit trust=yes. Kh?ng s?a machine certificate stores.
- Preflight ch? selected objects: SELECT, projection/schema; target identity/schema/privileges. History INSERT kh?ng global blocker.
- Gi? Decimal/NULL/Unicode/datetime2(7) fidelity, count/digest reconciliation, transactions/idempotency v? recovery ?? c?.
- Kh?ng thay BRD/KPI/grain/source contracts ho?c accepted DW design n?u ch?a Owner duy?t; history design ???c gi? cho milestones sau.
- D?ng requirements.txt ? root; unittest hi?n h?u; kh?ng t? th?m framework/package kh?ng c?n thi?t.
- Ph?n bi?t code/offline test/runtime verification. Kh?ng ghi runtime PASS khi ch?a ch?y.
- Refactor nh?, tests ph? h?p, c?p nh?t README/status ??ng th?c t?. Routine local/offline commands kh?ng c?n chu?i approval ri?ng.

MVP hi?n t?i: Sales extraction ? Raw ? dbt ? DW ? Sales Mart ? Power BI, basic DQ/logging/repeatability. Incremental, Customer/Inventory, SCD2, Airflow v? advanced recovery ? milestones ti?p theo. Kh?ng ch?y ingestion trong task reset.
# Ownership hiện hành — REPO-STRUCTURE-02, 2026-11-20

`ingestion` sở hữu extract/load/codecs và tests riêng; `dbt` sở hữu staging/core/marts/data tests; `airflow` sở hữu orchestration; `powerbi` sở hữu reports. `infrastructure` sở hữu Compose/PostgreSQL provisioning và utilities/tests riêng. `docs` giữ business/KPI/models/ADRs/history. `scripts` chỉ project-wide utilities; `tests` giữ cross-module integration. Refactor không phê duyệt runtime hay business policies trong draft DW-IMPLEMENT-01. Xem [migration map](README.md#repo-structure-02--ngày-2026-11-20).
