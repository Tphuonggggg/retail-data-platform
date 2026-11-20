# loaders

**Status:** WWI-06A Implemented / Offline Tested; Raw DDL provisioning verified; COPY/publication runtime NOT RUN.

Purpose/scope: [postgres.py](postgres.py) ghi immutable Raw captures/metadata/read-back/reconcile/atomic pointer/recovery cho [Full Load](../README.md). Inputs: typed batches/run scope/proof; outputs: candidate hoặc all11 publication. Không business upsert/warehouse/marts/SCD2.

Responsibilities: retail_ingest-only, strict target/schema/type/owner/privilege preflight; advisory lock; typed COPY/server-side named read-back; one capture transaction/no partial publication/inspect unknown ACK. [schema.py](schema.py) chỉ sinh [full_load.sql](../../infrastructure/postgres/full_load.sql), không execute/grant.

Dependencies: psycopg[binary]3.3.9, existing runs/object_runs; bốn control tables/payload proposed chưa provision. Execution qua parent CLI/runbook. [Offline suite](../tests/full_load_offline.py) kiểm driver mocks/transactions/count/digest/failure/retry/pointer; SQL engine/actual privileges cần WWI-06B. Retained sealed-chunk replay/checkpoint Not implemented yet.
