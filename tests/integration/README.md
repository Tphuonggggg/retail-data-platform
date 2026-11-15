# integration

- **Purpose:** Kiểm thử tương tác nguồn WWI chỉ đọc, ingestion và PostgreSQL đích.
- **Owned files / responsibilities:** source contract, batch metadata, quyền đọc, full/incremental trong môi trường phù hợp và reconciliation. Isolated [B9 precision PoC](b9_precision/README.md) chỉ kiểm source F2 → pyodbc str/None; không full/incremental pipeline.
- **Parent module:** [tests](../README.md).
- **Status:** B9 bounded source+PostgreSQL transport/persistence proof Implemented/Tested:12 unit methods,14 parameter cases,15 persisted records via new connection,169 order/14 equality/5 ranges PASS. Production integration suites Not implemented yet; commands/evidence trong README B9.
