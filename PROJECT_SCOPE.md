# Project Scope

## Trạng thái

Chủ dự án đã quyết định **WideWorldImporters (WWI) trên SQL Server là nguồn OLTP chính** và **PostgreSQL là Data Warehouse do dự án tự xây dựng**. Đây là phạm vi mục tiêu đã duyệt, không phải bằng chứng pipeline đã triển khai. Phase 0 `Completed`; Phase 1 `In Progress`, Phase 1.1–1.5 được chấp thuận ở mức tài liệu, WWI-02 và WWI-03 `DONE`. Phase 1.6/WWI-04 IN_PROGRESS; DW-01 DONE ở mức thiết kế logic, DW-02 DONE; DW-02A/B DONE; DW-02C/D DONE ở mức thiết kế; DW-02E DONE — B1–B8 Approved — Logical Policy và design acceptance/QA đạt ngày 2026-11-15; Phase 2–9 chưa bắt đầu. Business rules BRD-01–BRD-12 đã duyệt; các quyết định kỹ thuật ở mục Open Decisions còn mở.

## Mục tiêu và kiến trúc

Pipeline dự kiến: SQL Server WWI (**chỉ đọc**) → Python ingestion → PostgreSQL raw/staging → dbt/SQL transformations → PostgreSQL Data Warehouse → analytical data marts → Power BI. Apache Airflow điều phối; data quality, reconciliation và monitoring hoạt động xuyên suốt. Docker Compose phục vụ môi trường local khi được triển khai; BigQuery chỉ là phần mở rộng.

MVP gồm **Sales/Invoicing, Customer Analytics và Inventory Movements**. Hoàn thiện **Sales end-to-end** từ ingestion đến warehouse, Airflow, data quality, monitoring và mart/report trước khi mở rộng Customer rồi Inventory. Purchasing, Finance và BigQuery cần scope/task riêng. Giữ cấu trúc repository và các module Data Engineering dùng chung.

## Functional Requirements dự kiến

Phase 1.6 ghi nhận architecture constraints được Owner phê duyệt: Kimball Star Schema với Conformed Dimensions, bốn logical facts (Invoice Line, Order Line, Stock Movement, Inventory Current); Core DW giữ chi tiết, marts riêng Power BI. L01–L05: initial full + periodic incremental + periodic full reconciliation; transaction watermark candidates, temporal history/snapshot, holdings snapshot comparison; test INSERT/UPDATE/DELETE trên SQL Server độc lập; idempotent upsert + SCD2 theo bằng chứng/forward tracking + rebuild/restate; Sales end-to-end trước. DW-01 đã nghiệm thu [logical design](docs/data-models/wwi-logical-dw-design.md), Customer/Product tracking direction đã duyệt theo SCD principles/D01; B1–B8 validity/registry/recovery/publication/correction logical policies đã duyệt ngày 2026-11-15; physical procedures, incremental algorithm và physical schema còn cần phê duyệt.

| ID | Yêu cầu | Acceptance criteria dự kiến |
| --- | --- | --- |
| FR01 | Đọc WWI bằng quyền chỉ đọc theo source contract | Bảng/cột/khóa và quyền được ghi; không DDL/DML trên WWI gốc. |
| FR02 | Full load vào PostgreSQL raw/staging | Batch ID, source table, extracted_at, row count và đối soát khóa/số dòng. |
| FR03 | Incremental load với watermark/checkpoint | Quy tắc theo bảng và tie-breaker được duyệt; INSERT/UPDATE end-to-end chỉ thử trong môi trường độc lập được phê duyệt; không tuyên bố nguồn gốc đã thay đổi nếu chưa quan sát. |
| FR04 | Idempotent upsert, retry/backfill và recovery | Rerun không tạo duplicate trái quy tắc; checkpoint không tiến khi batch lỗi; backfill khoảng thời gian chọn và test khôi phục có bằng chứng. |
| FR05 | Validation, quarantine và cleaning | Record không hợp lệ có lý do; raw giữ dấu vết; không âm thầm sửa nguồn. |
| FR06 | Warehouse/star schema đúng grain | Fact/dimension và measures theo schema đã duyệt; không double count khi kết hợp order, invoice, transaction và stock movement. |
| FR07 | SCD Type 2 có giới hạn bằng chứng | Chỉ áp dụng cho thuộc tính/history được duyệt; khoảng hiệu lực và lookup as-of được kiểm thử. |
| FR08 | Data quality và reconciliation | Kiểm tra cơ bản từ ingestion/warehouse gồm unique, not null, relationships, accepted values và business rules được duyệt; count/amount/quantity đối soát cùng grain, kỳ và population. |
| FR09 | Airflow orchestration, logging/monitoring | Sales DAG theo dependency, retry và recovery; batch/task được truy vết. |
| FR10 | Data marts và Power BI | Sales rồi Customer rồi Inventory Movements; KPI có định nghĩa, nguồn, test đối soát và cách dùng nhất quán trong semantic/reporting layer. |

## Business và data boundaries

- `Sales.Orders`, `Sales.OrderLines`, `Sales.Invoices`, `Sales.InvoiceLines` và `Sales.CustomerTransactions` có grain/ý nghĩa khác nhau. Order metrics theo `OrderDate`; invoice metrics theo `InvoiceDate`. `Invoiced Sales Before Tax = SUM(InvoiceLines.ExtendedPrice − InvoiceLines.TaxAmount)` là measure mặc định của MVP, cùng với Tax Amount và Invoice Amount Including Tax. Đây là quy ước báo cáo dự án, không là Recognized Revenue hay doanh thu kế toán. Bốn logical fact grains được khai báo trong DW-01 theo yêu cầu Owner; logical mapping đã nghiệm thu; physical schema và các policy được chuyển tiếp vẫn còn mở.
- Customer analytics: buyer `CustomerID` là role mặc định cho Sales; `BillToCustomerID` là góc nhìn billing riêng. Monthly Repeat Order Customer Rate = buyer có ≥2 distinct orders trong tháng / buyer có ≥1 order trong tháng, theo `OrderDate`; quý tính lại trên toàn quý.
- Inventory Movements dùng `Warehouse.StockItemTransactions` theo loại nghiệp vụ; current holdings chỉ là snapshot hiện tại. Daily Inventory Balance và Stockout Risk ngoài MVP.
- Temporal history chỉ hỗ trợ SCD2 ở bảng và khoảng lịch sử đã kiểm chứng, không mặc định bao phủ mọi giao dịch.
- Kiểm tra chất lượng cơ bản bắt đầu ở Phase 3–4. Phase 6 tập trung quality gates, monitoring tập trung và failure scenarios nâng cao.
- WWI gốc luôn chỉ đọc. Không dùng CDC trong phương án hiện hành; chưa bật Change Tracking. Phương án môi trường thử nghiệm độc lập cho incremental chỉ được thiết kế ở WWI-04, chưa tạo clone hoặc DML.

## Out of Scope và extensions

MVP không gồm Recognized Revenue, official Gross Profit/COGS, AOV chưa có policy, Refund/Credit Note KPI, invoice-level payment allocation, Daily Inventory Balance, Stockout Risk, returns/refunds chi tiết, campaign attribution, streaming, Kafka/Flink/Hadoop cluster/Kubernetes, machine learning, payment gateway thật hay frontend web application hoàn chỉnh. `Source-Reported Line Profit` chỉ là optional analytical measure từ `InvoiceLines.LineProfit`. `Average Invoice Value Before Tax` là measure riêng, không là AOV. Purchasing, Finance và BigQuery là phần mở rộng có kiểm soát; chúng không chặn nghiệm thu MVP local. Không tự thêm dependency hoặc thay đổi technology stack.

## Non-functional Requirements và Definition of Done dự kiến

- **Tái lập local:** tài liệu phải nêu cách chuẩn bị WWI làm nguồn read-only và các điều kiện truy cập/restore hợp lệ bên ngoài repository; cấu hình dự án qua `.env.example`, Docker Compose cho các service phù hợp, phiên bản dependency được phê duyệt và runbook. Không commit backup WWI để chứng minh tái lập.
- **Bảo mật:** quyền đọc tối thiểu trên WWI; secret qua environment variables hoặc cơ chế được duyệt; không commit credentials, backup, bản trích xuất chứa dữ liệu nguồn hoặc dữ liệu nhạy cảm. Quyền phân phối/demo dữ liệu được xem xét trước khi công khai repository.
- **Quan sát:** batch ID, row counts, duration, error type và trạng thái task phải truy vết được; cảnh báo và hướng dẫn khôi phục được kiểm thử khi triển khai.
- **Kiểm thử:** unit, integration và end-to-end phù hợp từng phase; kiểm thử rerun, checkpoint, lỗi giữa batch, SCD2 trong phạm vi history có bằng chứng, reconciliation và failure recovery. Không dùng dữ liệu WWI gốc làm nơi tiêm lỗi.
- **Hiệu năng và tối ưu truy vấn:** đo full/incremental load và các truy vấn warehouse; xem execution plan phù hợp từng engine. Chỉ đề xuất/chỉnh index hoặc partition trên PostgreSQL đích sau khi schema được duyệt; không tối ưu bằng cách sửa WWI gốc. Chỉ ghi cải thiện khi có số đo trước/sau cùng điều kiện.
- **CI và portfolio:** sau khi có Git và code, chạy kiểm tra phù hợp bằng GitHub Actions; báo cáo số liệu, dashboard, DAG run và benchmark chỉ khi có bằng chứng. MVP local có thể tái lập và nghiệm thu độc lập với BigQuery.
- **Cloud extension:** nếu BigQuery được duyệt sau này, xác định quota/budget, quyền truy cập và đối soát với local trước khi tuyên bố triển khai.

Definition of Done cho **MVP triển khai** là một người khác có thể chuẩn bị nguồn WWI theo hướng dẫn, cấu hình môi trường hợp lệ, chạy pipeline local, xem kết quả kiểm thử/đối soát và giải thích grain/KPI/SCD2. Điều này không phải tiêu chí hoàn thành Phase 0 tài liệu.

## Open Decisions

SCD-01–07 đã duyệt nguyên tắc: Customer Type 2 direction cho CustomerCategoryID/BuyingGroupID/BillToCustomerID; CreditLimit/IsOnCreditHold optional chưa kích hoạt; hybrid history có evidence, giữ zero-duration Raw/audit, không fallback current/earliest cho unresolved, bảo toàn precision và không blanket restatement. ADR-SCD-01–06 nay chốt Product Type2 ba packaging columns, registry/consensus/reconciled cutover/exact precision/controlled unresolved; B1–B8 đã Approved — Logical Policy; B9 scoped Physical Raw Temporal Representation nay Approved tại DW-03A (F2/str-None/psycopg/TEXT/C);entire Raw schema/index/retention/runtime và numerical thresholds còn separate gates, xem [classification](docs/data-models/wwi-scd-attribute-classification.md). Không thay các BRD/KPI đã duyệt.

| Nhóm | Quyết định chưa chốt | Gate |
| --- | --- | --- |
| KPI triển khai | Population/filter theo kỳ, precision/rounding, credit note tương lai, kiểm thử đối soát các measure đã duyệt; không mở lại revenue recognition ngoài MVP | WWI-04 và trước mart |
| Customer | Logical role/grain/SCD2/lookup/restatement đã duyệt tại DW-01/02/03; physical registry/member/lookup/selected-set implementation và per-request proof còn pending | CG02/CG05/CG09 trước use; không mở lại buyer/bill-to |
| Warehouse | Physical schema và policy từ logical mapping DW-01 đã nghiệm thu; bốn fact/conformed dims theo constraints Owner đã giao; official COGS/Gross Profit deferred | Trước schema |
| SCD2 | D01–D06/B1–B8 approved architecture/logical policies; physical encoding/member/algorithm, concrete day/basis evidence và thresholds còn pending | DW-03 trước conversion/runtime/correction; thresholds trước Certified publication |
| Incremental | INC-01–INC-06 đã Approved — Logical Policy; exact algorithms/U selection, numeric lookback/cadence, delete action procedure và sandbox/runtime proof còn gates | Trước algorithm/scheduling/action/publication use theo DW-03B |
| Inventory | Đối soát movements/current holdings; daily balance và stockout risk ngoài MVP | Trước inventory mart |
| Propagation/publication | CP-01–06 và D1/D2 Logical Approved; D3 Governance Approved. Physical manifests/registry/lookup/consumer/RBAC/transaction/recovery proof, B5 numerical thresholds và per-action authorization vẫn gated | Before relevant normal publication/action use theo DW-03C, không automatic implementation |
| Data quality | B5 tiered logical policy đã duyệt; numeric row/value thresholds theo KPI/view, alert/block values và exception approval còn pending | B5/RG11/CG06 trước Certified publication; basic correctness từ ingestion |
| Git publication | Quyền phân phối dữ liệu, license và chính sách công khai repository trước khi tạo remote/push | Chủ dự án quyết định trước publish |

## Change control

Chỉ chủ dự án phê duyệt business rules, schema, công nghệ, phase và nghiệm thu. Các tài liệu cũ không còn là yêu cầu hiện hành. Không coi tài liệu là bằng chứng database, ingestion, dbt, DAG hoặc dashboard đã hoạt động. Xem [ADR chuyển nguồn](docs/adr/wwi-source-migration.md), [ROADMAP.md](ROADMAP.md) và [TASKS.md](TASKS.md).


## DW-03A design acceptance / B9 physical follow-up

Ngày2026-11-15, Owner approve scoped authoritative Raw representation cho relevant datetime2(7): F2 fixed27/seven digits→Python str/None→parameterized psycopg→PostgreSQL TEXT;COLLATE C cho canonical ordering/comparison,NULL/min/max/sentinel/100ns giữ nguyên,derived timestamp/search forms secondary,không business-effective inference. [ADR-SCD-05](docs/adr/scd-05-exact-temporal-precision.md) ghi ten constraints/exclusions. Không approve toàn Raw DDL/index/retention periods/publication/crash/performance.

[DW-03A final assessment](docs/data-models/wwi-dw-03a-assessment.md) nghiệm thu **DONE — Design** theo conditional authority sau14 mandatory design checks/tests/QA. G07 conceptual Raw/evidence/replay/retention protections đủ guide implementation-specific proposal; concrete source consistency/least-privilege/adapters/physical DDL-retention/runtime publication theo [G01–G08](docs/data-models/wwi-dw-03a-work-plan.md),không deferred test PASS. WWI-04/Phase1 **In Progress**, DW-03B DONE — Design theo Stage 2 ngày 2026-11-16, DW-03C DONE — Design, DW-04 TODO; không production pipeline hoặc tự chuyển phase. Existing MVP/BRD/SCD/grains/technology scope không đổi.

## DW-03B Stage 1 — trạng thái thiết kế, 2026-11-16 (lịch sử trước Stage 2)

[Incremental proposal](docs/data-models/wwi-dw-03b-incremental-design-proposal.md) và [INC-01–INC-06](docs/data-models/wwi-dw-03b-decision-register.md) chỉ là PROPOSED — PENDING PROJECT OWNER APPROVAL. Bao phủ 9 current + 2 associated H, không thêm nguồn/subject area. Timestamp/period không mặc định complete CDC; state reconciliation không chứng minh mọi intermediate event. Lookback/cadence/delete confirmation/checkpoint algorithm và writable test environment chưa chốt; không thay các FR/BRD/SCD đã duyệt hoặc triển khai runtime.


## DW-03B Stage 2 — Logical Approval & Design Acceptance, 2026-11-16 (mốc trước DW-03C)

Owner task “DW-03B Stage 2 — Owner Logical Approval & Design Finalization” cấp **INC-01–INC-06 Approved — Logical Policy**. [Specification](docs/data-models/wwi-dw-03b-incremental-design-proposal.md) và [Register](docs/data-models/wwi-dw-03b-decision-register.md) chốt mục tiêu **Current-State Convergence** so với verified consistent source state; candidate windows/temporal history không là complete CDC. Full comparison có full source-read cost dù chỉ ghi changed rows. Exact algorithms/U selection, numeric duration/cadence/quality thresholds và physical/runtime mechanisms chưa tự chốt.

[Assessment](docs/data-models/wwi-dw-03b-assessment.md) sections 9–13 ghi mandatory design criteria/QA và conditional acceptance: **DW-03B DONE — Design**. [RG01–RG12](docs/data-models/wwi-dw-03b-work-plan.md) có reason/owner/target/proof/publication blocker, giữ G01–G08/B5. IT01–IT21 **NOT RUN**, production incremental Not implemented yet. DW-03A/B9/A01–A06/B1–B8 không đổi; **DW-03C/DW-04 TODO, WWI-04/Phase 1 IN_PROGRESS, Phase 2–9 Not Started**. Không bắt đầu task tiếp. Current authorization cho một focused documentation commit sau staged QA; không push hoặc DB/Docker/B9 sandbox changes.


## DW-03C Stage 1 — Discovery & Design Proposal, 2026-11-16 (lịch sử trước Stage 2)

Owner đã giao DW-03C **IN_PROGRESS**. [Work plan](docs/data-models/wwi-dw-03c-work-plan.md), [Change Propagation Proposal](docs/data-models/wwi-dw-03c-change-propagation-design-proposal.md), [CP-01–CP-06](docs/data-models/wwi-dw-03c-decision-register.md) và [Assessment](docs/data-models/wwi-dw-03c-assessment.md) là hồ sơ Stage 1. Tất cả CP decisions **PROPOSED — PENDING PROJECT OWNER APPROVAL**; không thay approved DW-01/02/03A/03B/B9 hoặc business scope. Source/model impact, old/new groups, SCD2/fact/mart/publication/recovery và test scenarios chỉ là design proposals.

DW-01/DW-02/DW-03A/DW-03B DONE Design; DW-04 TODO; WWI-04/Phase 1 IN_PROGRESS; Phase 2–9 Not Started. Inherited G01–G08/RG01–RG12/B5 vẫn pending; CP runtime tests NOT RUN, production modules Not implemented yet. Không SQL/DB/Docker/B9 sandbox/code/dependency changes; **không stage/commit/push, không đóng DW-03C hoặc bắt đầu DW-04**.


## DW-03C Stage 2 — Owner Logical Approval & Final Design Review, 2026-11-16 (lịch sử trước Stage 3)

Owner đã approve **CP-01–CP-06 — Logical Policy** tại [Register](docs/data-models/wwi-dw-03c-decision-register.md). [Specification](docs/data-models/wwi-dw-03c-change-propagation-design-proposal.md) section10 ghi D1–D4: **D1 Type1 selection reference/mode, D2 analytical publication unit/shared consumer compatibility, D3 revocation/rollback authority còn PENDING OWNER APPROVAL**; D4 full affected-mart rebuild baseline CONFIRMED theo CP-04, không cần approve lại. Six logical approvals không tự resolve D1–D3.

[Assessment](docs/data-models/wwi-dw-03c-assessment.md) sections9–13: design acceptance **PARTIAL**, DW-03C **IN_PROGRESS**; no finalization commit/staging/push. AP01–AP06 logical evidence contracts reviewed, CP-R01–12 và CP-T01–30 được rà; runtime tests **NOT RUN**. G01–G08/RG01–RG12/CG01–10/B5 vẫn gated, không numeric/physical defaults. DW-04 TODO/chưa bắt đầu; WWI-04/Phase1 IN_PROGRESS, Phase2–9 Not Started. Approved DW-01/02/03A/03B/B9/business scope không đổi; không DB/Docker/B9 sandbox/code changes.


## DW-03C Stage 3 — Final Design Acceptance, 2026-11-16 (lịch sử trước DW-04)

Owner task “DW-03C Stage 3 — Owner D1–D3 Approvals & Final Design Acceptance” cấp **D1/D2 Approved — Logical Policy, D3 Approved — Governance Policy; D4 Confirmed**. [Register](docs/data-models/wwi-dw-03c-decision-register.md) ghi exact scope/authority; [Specification](docs/data-models/wwi-dw-03c-change-propagation-design-proposal.md) tích hợp explicit frozen four-anchor selected set, dependency-complete subject/view+joint consumer manifest và DQ/Owner/Operator lifecycle governance. Không phát hiện conflict với accepted DW-02; no Type2/source-measure/history-meaning changes.

[Final Assessment](docs/data-models/wwi-dw-03c-assessment.md) sections14–18 ghi **18/18 mandatory design criteria PASS → DW-03C DONE — Design** theo conditional authority sau actual QA, không runtime approval. Stage1/2/Pending/15PASS+3PARTIAL evidence giữ history. CP-01–06 vẫn Approved — Logical Policy; CP-T01–30 NOT RUN; G01–08/RG01–12/CG01–10/B5 và per-action evidence còn gates trước relevant normal publication/use. Không tự revoke/reinstate/rollback hoặc implement. DW-04 TODO/ready-for-Owner-task, WWI-04/Phase1 IN_PROGRESS,Phase2–9 Not Started. Current authority cho one focused docs commit sau staged checks, no push/remote/DB/Docker/B9 changes; không bắt đầu DW-04.

## DW-04 — Design Acceptance & Implementation Handoff, 2026-11-16 (hiện hành)

**DW-04 DONE — Design Acceptance**,20/20 criteria và static/staged QA PASS. [Assessment](docs/data-models/wwi-dw-04-assessment.md), [Implementation Gate Register](docs/data-models/wwi-implementation-gate-register.md) và [Readiness/Handoff](docs/data-models/wwi-implementation-readiness-handoff.md) đối chiếu11 source populations/16 models/22 KPI/12 BRD,31 original gates,18 readiness components và72 planned tests NOT RUN. Approved DW-01/02/03A/03B/03C/B9/INC/CP/D1–D3 giữ nguyên; không thêm business/physical defaults.

Design acceptance khác implementation/operational readiness. WWI-04/Phase1 **IN_PROGRESS**, Phase2–9 **Not Started**; production modules **Not implemented yet**. Không tự bắt đầu task/phase sau; chỉ task tài liệu và một focused commit sau QA theo Owner DW-04 authority, không push/remote/DB/Docker/B9 changes.
