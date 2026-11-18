# Ingestion

Python3.12 + pyodbc5.5.0 + psycopg3.3.9. Full Load Implemented/Offline Tested; runtime NOT RUN. [Setup/commands](../README.md).

- full_load.py: CLI config/plan/ddl/connectivity/preflight/load/reconcile/abandon.
- common: frozen11-source contracts, config, codecs, exact F2 datetime2(7), digest/evidence.
- extractors: current-account Windows Auth, SELECT-only, selected SELECT/projection/schema checks.
- loaders: non-admin retail_ingest, target schema/grants checks, COPY/read-back, metadata/atomic publication.
- checkpoints: incremental ch?a tri?n khai.

## Contract runtime

SELECT explicit columns/parameterized metadata; no source writes. Encrypt=yes m?c ??nh; development trust=yes v? admin-source opt-in ph?i explicit. Kh?ng permission audit/history INSERT global gate. Selected load check ??ng selected objects; all load check all11. Missing SELECT/schema drift ? STOP.

Source-shaped Raw gi? Decimal/NULL/Unicode/binary/native geography bytes/datetime2(7) text27/C. Batch limits v? ordered typed digest gi? nguy?n; archive duplicates gi? occurrence, kh?ng fake PK. Geography full persistent coverage v?n c?n runtime proof.

Raw provisioning ?? PASS11 payload/4 controls/11 views, foundation2 tables intact. Runtime kh?ng auto DDL/GRANT. M?t capture transaction, known failure rollback; same successful run ID reconcile/no reload; failed run retry d?ng UUID m?i; unknown commit ph?i inspect. Sealed-chunk replay/resume ch?a implement, l? advanced milestone.

Selected candidate kh?ng publish; existing all11 publication c?n consistent source proof v? geography/reconciliation evidence. Read-only extraction/count equality kh?ng t? ch?ng minh source snapshot consistent. Ch?a thay publication semantics ho?c accepted SCD2/business rules.

## First smoke acceptance

Warehouse.StockItemHoldings/batch64/unpublished: fresh source vs Raw count/distinct keys/numeric totals/NULLs, exact F2, typed digest, durable reconnect/reconcile/rerun, run/object metadata, unchanged publication pointer. Ch?a ch?y trong reset.

## Tests v? history

[Offline tests](../tests/full_load_offline.py), [Raw tests](../tests/raw_foundation_static.py), [Raw SQL](../storage/raw/README.md). [Evidence tr??c reset](../docs/archive/pre-reset/ingestion-history.md) l? historical, kh?ng active security requirements.
