# ADR — WideWorldImporters as Primary OLTP Source

- **Status:** Approved direction by Project Owner on 2026-11-07; implementation and business/schema decisions remain open.
- **Owner:** Project Owner.
- **Context:** [Project Scope](../../PROJECT_SCOPE.md), [Roadmap](../../ROADMAP.md), [Task Tracker](../../TASKS.md).

## Decision

`WideWorldImporters` on SQL Server is the **single primary OLTP source** for the project and is accessed **read-only**. PostgreSQL is the Data Warehouse designed and built by this project. Planned flow: SQL Server → Python ingestion → PostgreSQL raw/staging → dbt/SQL → PostgreSQL warehouse → analytical marts → Power BI. Apache Airflow orchestrates the pipeline.

MVP subject areas are Sales/Invoicing, Customer Analytics and Inventory Movements, in that order. Sales must be completed end-to-end, including ingestion, warehouse, Airflow, basic/central quality, monitoring and reporting, before expanding to Customer and Inventory. Purchasing, Finance and BigQuery are controlled extensions.

The repository keeps reusable Data Engineering modules. Files and requirements serving only the previous source design are removed; the project does not maintain a second active architecture.

## Reason

The WWI database available locally contains connected OLTP tables for orders, invoices, customer transactions and stock item movements, plus temporal history for selected entities. This supports the chosen MVP without building simulated upstream systems. These observations do **not** approve revenue rules, source-to-target mappings or warehouse schema.

## Consequences

- Source contracts, KPI definitions and tests must be rewritten for WWI grain and relationships. Order, invoice, invoice line, ledger and stock movement measures must not be added across fan-out joins.
- The original WWI database is never modified by project work. CDC is outside the current design; Change Tracking is not enabled. WWI-04 must propose a separate test environment for INSERT/UPDATE and incremental end-to-end evidence before it is created or used.
- Temporal history may support selected SCD2 dimensions, but cannot be assumed to represent complete history for all transactions.
- Basic data quality checks begin with ingestion and warehouse work. Phase 6 adds centralized quality gates, monitoring and advanced failure scenarios.
- The project remains at Phase 0 `In Progress`; this ADR does not authorize Phase 1, DDL, ingestion or package installation.
- Các yêu cầu Data Engineering dùng chung từ đề cương ban đầu đã được đối chiếu và diễn giải theo WWI trong scope/roadmap. Đề cương cũ đã được loại khỏi repository; tài liệu hiện hành là nguồn tham chiếu cho dự án.

## Alternatives considered

Continue the previous simulated-source architecture: rejected by the Project Owner. Move all components to a new repository: rejected to preserve reusable modules and task traceability. Use SQL Server as the warehouse: outside the approved architecture; PostgreSQL is the target warehouse.

## Open Decisions

Revenue recognition/tax and invoice-versus-delivery date; `CustomerID` versus `BillToCustomerID`; fact/dimension grain and schema; profit/COGS; SCD2 attributes/validity; incremental extraction/deletes/test environment; inventory daily balance; data quality thresholds. See [Open Decisions](../../PROJECT_SCOPE.md#open-decisions).
