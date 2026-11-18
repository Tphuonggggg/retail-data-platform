# extractors

**Status:** WWI-06A Implemented / Offline Tested; actual extraction NOT RUN.

Purpose/scope: [sqlserver.py](sqlserver.py) đọc đúng11 objects của [Full Load](../README.md). Inputs: contracts/settings; outputs: source context/COUNT_BIG/batches. Không source writes/business transformations.

Responsibilities: Windows principal/SQL SID/user/instance/database/no-admin guards; ODBC18 Integrated Authentication strict TLS/timeouts; effective SELECT/no-write all11; exact selected schema trước payload. fetchmany/PK order/separate archive occurrences/source-side F2. Metadata nhỏ có fetchall; payload không materialize cả bảng.

Dependencies: common, pyodbc5.5.0/project venv, Windows/ODBC18. Execution qua parent connectivity/preflight/load; không tạo identity/GRANT/DBA fallback. TLS và archive effective INSERT đang BLOCKED. [Offline tests](../../tests/full_load_offline.py) kiểm guards/permissions/schema/batching/identity/timeouts. Actual fidelity/consistency pending; incremental extractor Not implemented yet.
