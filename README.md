# Retail Data Platform & Analytics Warehouse

**Current local MVP:** [MVP-SIMPLIFICATION-01](docs/architecture/wwi-m1b-owner-decisions.md#mvp-simplification-01--trusted-local-mvp) ưu tiên pipeline/data correctness/runtime evidence; protected staging/ACL work là optional hardening. EX01 DONE, EX02 chưa provision; PostgreSQL Raw [Compose/bootstrap](infrastructure/docker/README.md) và [checker](scripts/check_raw_connection.py) **PREPARED / OFFLINE TESTED**, runtime NOT RUN. [MVP-G01–06](TASKS.md#mvp-operational-milestones) theo dõi access → Raw → Full/Incremental → DW → Analytics/Orchestration; không tự PASS historical gates.

## Project Overview

Dự án portfolio Data Engineering dùng SQL Server WideWorldImporters chỉ đọc làm OLTP, xây warehouse PostgreSQL và phục vụ Power BI. Phase 0 **Completed**; Phase 1 **Completed — Requirements & Source Design**; WWI-02/03 **DONE**, WWI-04 **DONE — Design**. DW-01/02/03A/03B/03C **DONE — Design**; DW-04 **DONE — Design Acceptance**. Phase 2 **IN_PROGRESS — Authorized**, giới hạn WWI-05 **IN_PROGRESS**, M1A **DONE — Verification Checkpoint**; WWI-05 chưa hoàn tất. M2 trở đi và Phase 3–9 **Not Started**. Production modules **Not implemented yet**; chỉ B9 isolated PoC có evidence lịch sử. [Owner closure/authorization](docs/architecture/wwi-phase-1-closure-approval.md). [Scope](PROJECT_SCOPE.md), [Roadmap](ROADMAP.md), [Tasks](TASKS.md).

## Business Problems and MVP

Dữ liệu order, invoice, customer transaction và stock movement có grain/ý nghĩa khác nhau. Báo cáo cần phân biệt đặt hàng, xuất hóa đơn, thu tiền và biến động hàng để tránh đếm trùng và đối soát được. MVP gồm **Sales/Invoicing, Customer Analytics, Inventory Movements**; hoàn thiện Sales end-to-end trước. Purchasing, Finance và BigQuery chỉ là extensions có kiểm soát. BRD-01–BRD-12 đã được duyệt ở mức nghiệp vụ; [KPI Catalog](analytics/kpi-definitions/wwi-kpi-candidate-catalog.md) phân loại KPI MVP và loại trừ. DW-01 grains, DW-02 B1–B8, DW-03A/B/C logical policies và scoped B9 physical temporal representation đã duyệt; concrete physical/runtime choices và numerical quality thresholds còn gates.

## Planned Architecture

`SQL Server WWI (read-only) → Python ingestion → PostgreSQL Raw → dbt Staging → Core DW → Analytics Marts → Power BI`. Airflow điều phối; quality/reconciliation, logging/monitoring và failure recovery xuyên suốt. Kiểm tra cơ bản bắt đầu từ ingestion/warehouse; Phase 6 bổ sung quality gates và failure nâng cao. Xem [system overview](docs/architecture/system-overview.md) và [data flow](docs/architecture/data-flow.md).

## Technology Stack

Python 3.12, SQL Server nguồn, PostgreSQL đích, SQL, dbt Core, Apache Airflow, Docker Compose, pytest, Power BI và GitHub Actions là stack dự kiến theo phase. BigQuery là extension. Chưa cài hoặc cấu hình runtime của dự án trong repository; dịch vụ local tồn tại không chứng minh pipeline đã chạy. Không tự thêm package/framework.

## Module Overview

| Module | Vai trò dự kiến |
| --- | --- |
| `.github` | Cộng tác và CI khi có Git/code |
| `docs` | Requirements, architecture, data models, ADR, runbooks |
| `infrastructure` | Cấu hình local/cloud theo phase |
| `data-sources` | WWI source contract và quyền đọc |
| `ingestion` | Full/incremental extract, load, checkpoint, retry |
| `storage` | Raw, staging, warehouse PostgreSQL |
| `transformation` | dbt/SQL facts, dimensions và SCD2 theo quyết định |
| `orchestration` | Airflow DAGs |
| `data-quality` | Validation, quarantine, reconciliation |
| `analytics` | Marts, KPI, Power BI |
| `monitoring` | Logs, metrics, alerts |
| `tests` | Unit, integration và end-to-end |
| `scripts` | Lệnh hỗ trợ theo task cụ thể |

## Folder Structure and Status

Mỗi module có README điều hướng. Đã có Raw Compose/bootstrap/readonly checker và offline tests; chưa chạy service hoặc tạo PostgreSQL schema thực tế. Chưa có Python ingestion, dbt project, Airflow DAG hoặc Power BI report. Git local hoạt động, chưa push. Đối chiếu [TASKS.md](TASKS.md).

## Getting Started (planned)

Hướng dẫn [EX02 local setup](data-sources/security/README.md#10-local-mvp-setup--pending-runtime-authorization) và [Raw startup](infrastructure/docker/README.md) đã chuẩn bị; runtime cần Owner authorize riêng. Chỉ offline tests được chạy ở task hiện tại. WWI gốc luôn read-only; incremental INSERT/UPDATE tests phải dùng môi trường độc lập, không bịa CDC.

## Documentation Navigation

[Quy tắc AI](AGENTS.md) · [Scope](PROJECT_SCOPE.md) · [Roadmap](ROADMAP.md) · [Tasks](TASKS.md) · [Architecture](docs/architecture/README.md) · [Migration ADR](docs/adr/wwi-source-migration.md) · [Changelog](CHANGELOG.md).

## DW-03B Stage 2 — 2026-11-16

**DW-03B DONE — Design**, INC-01–INC-06 **Approved — Logical Policy** theo conditional design acceptance/QA của Owner. [Specification](docs/data-models/wwi-dw-03b-incremental-design-proposal.md), [Register](docs/data-models/wwi-dw-03b-decision-register.md), [Assessment](docs/data-models/wwi-dw-03b-assessment.md) và [Runtime gates](docs/data-models/wwi-dw-03b-work-plan.md). Mục tiêu Current-State Convergence trên verified consistent source state; không full CDC/intermediate-event guarantee. Full comparison vẫn đọc full source. Numeric/physical/runtime details pending, IT01–IT21 NOT RUN, production pipeline Not implemented yet. DW-03A/B9 approvals giữ nguyên; DW-03C DONE — Design (Stage3 approvals), DW-04 TODO, WWI-04/Phase 1 IN_PROGRESS. Không tự triển khai task tiếp.


## DW-03C Stage 3 — 2026-11-16 (lịch sử trước DW-04)

**DW-03C DONE — Design** sau conditional18/18 criteria/QA. CP-01–CP-06/D1/D2 **Approved — Logical Policy**, D3 **Approved — Governance Policy**, D4 confirmed; [Register](docs/data-models/wwi-dw-03c-decision-register.md), [Final Specification](docs/data-models/wwi-dw-03c-change-propagation-design-proposal.md), [Assessment](docs/data-models/wwi-dw-03c-assessment.md) và [Runtime gates](docs/data-models/wwi-dw-03c-work-plan.md). CP-T01–30 NOT RUN, production modules Not implemented yet; B5 values/physical enforcement/runtime/per-action proof pending. DW-04 TODO/ready-for-Owner-task, WWI-04/Phase1 IN_PROGRESS. Không implementation hoặc tự start DW-04; no push.

## DW-04 — Design Acceptance & Implementation Handoff, 2026-11-16 (lịch sử trước Owner closure)

**DW-04 DONE — Design Acceptance**,20/20 criteria và static/staged QA PASS. [Assessment](docs/data-models/wwi-dw-04-assessment.md), [Implementation Gate Register](docs/data-models/wwi-implementation-gate-register.md) và [Readiness/Handoff](docs/data-models/wwi-implementation-readiness-handoff.md) đối chiếu11 source populations/16 models/22 KPI/12 BRD,31 original gates,18 readiness components và72 planned tests NOT RUN. Approved DW-01/02/03A/03B/03C/B9/INC/CP/D1–D3 giữ nguyên; không thêm business/physical defaults.

Design acceptance khác implementation/operational readiness. WWI-04/Phase1 **IN_PROGRESS**, Phase2–9 **Not Started**; production modules **Not implemented yet**. Không tự bắt đầu task/phase sau; chỉ task tài liệu và một focused commit sau QA theo Owner DW-04 authority, không push/remote/DB/Docker/B9 changes.

## Owner Closure & Phase 2 Authorization — 2026-11-16 (Checkpoint A, trước verification)

Phase 0 **Completed**; Phase 1 **Completed — Requirements & Source Design**; WWI-02/03 **DONE**, WWI-04 **DONE — Design**. DW-01/02/03A/03B/03C **DONE — Design**; DW-04 **DONE — Design Acceptance**. Phase 2 **IN_PROGRESS — Authorized**, giới hạn WWI-05/M1A **IN_PROGRESS — Authorized**; WWI-05 chưa hoàn tất. M2 trở đi và Phase 3–9 **Not Started**. Production modules **Not implemented yet**; chỉ B9 isolated PoC có evidence lịch sử.

[Owner closure/authorization](docs/architecture/wwi-phase-1-closure-approval.md) là authority mới cho APPROVAL-01–05; nguồn là task trực tiếp của Project Owner, không chữ ký điện tử/hệ thống approval bên ngoài. Checkpoint A ghi nhận và commit sau QA, rồi Checkpoint B mới thực hiện M1A chỉ đọc. G01–08/RG01–12/CG01–10/B5 giữ nguyên31 entries;72 runtime scenarios NOT RUN. Approval không cho DML/DDL, infrastructure/identity/config changes, install dependencies, pipeline, M2/M3 hoặc push. Các status/no-start notes của DW-04 phía trên là lịch sử trước approval này.

## WWI-05 / M1A — Verification Report, 2026-11-16 (hiện hành)

M1A **DONE — Verification Checkpoint**, không operational acceptance: secure developer SQL/TLS và11 bounded source reads PASS; tested identity có sysadmin/write permissions nên FAIL suitability, approved extraction profile/consistency/Raw target/reproducibility còn BLOCKED. WWI-05/Phase2 **IN_PROGRESS**; WWI-04 DONE — Design, Phase1 Completed theo Owner approval; M2/M3+ NOT STARTED.

[Environment Report](docs/architecture/wwi-m1a-environment-readiness.md), [Secure Contract](docs/architecture/wwi-secure-connection-contract.md), [26-check Evidence Matrix](docs/architecture/wwi-m1a-gate-evidence.md), [M1A Handoff](docs/architecture/wwi-m1a-handoff.md). Metadata/connectivity là subset, không nghiệm thu IT01 hoặc72 scenarios;31 original gates giữ nguyên. Không source/target writes/infrastructure/identity/dependency changes, B9 sandbox giữ nguyên. Mọi next remediation/provision cần Owner giao task riêng; không tự M2/M3/push.
