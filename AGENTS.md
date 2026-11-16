# Quy tắc làm việc với AI

Áp dụng cho toàn bộ repository. Chủ dự án quyết định scope, architecture, tính năng, ưu tiên, chuyển phase và nghiệm thu. Tài liệu dùng tiếng Việt; tên thư mục, tệp và định danh code dùng tiếng Anh.

## RULE 01 — SCOPE CONTROL
Chỉ làm đúng task được giao; không tự mở rộng tính năng.

## RULE 02 — NO PREMATURE IMPLEMENTATION
Không viết code cho module chưa được yêu cầu hoặc tự xây toàn bộ pipeline.

## RULE 03 — PLAN BEFORE IMPLEMENTATION
Với mỗi task: đọc tài liệu liên quan, kiểm tra dependencies, trình bày kế hoạch ngắn, xác định file cần tạo/sửa, rồi chỉ thực hiện trong phạm vi đã giao.

## RULE 04 — MODULE ISOLATION
Mỗi module có trách nhiệm riêng; tránh phụ thuộc vòng và trộn logic nghiệp vụ không liên quan.

## RULE 05 — DOCUMENTATION FIRST
Mỗi module có README mô tả purpose, scope, responsibilities, inputs, outputs, dependencies, technology, folder structure, execution, testing, acceptance criteria và status. Chức năng chưa triển khai phải ghi `Not implemented yet`; không mô tả như đã hoạt động khi chưa có bằng chứng kiểm thử.

## RULE 06 — NO UNAUTHORIZED DEPENDENCIES
Không tự cài package, đổi phiên bản hoặc framework khi chưa được chủ dự án phê duyệt.

## RULE 07 — NO DESTRUCTIVE OPERATIONS
Không tự xóa dữ liệu, drop database/table, chạy migration phá hủy, force push, reset Git history, xóa file ngoài task hoặc ghi đè cấu hình hiện có mà chưa kiểm tra. Dừng và hỏi nếu có nguy cơ mất dữ liệu.

## RULE 08 — SECURITY
Không hardcode password, API key, database/cloud credential hoặc access token. Dùng environment variables và `.env.example`; không commit `.env` hay dữ liệu nhạy cảm.

## RULE 09 — CODE QUALITY
Khi được yêu cầu viết code: viết rõ ràng, có type hints và exception handling phù hợp; không dùng bare `except`, không nuốt lỗi vô lý, không hardcode đường dẫn tuyệt đối hay tạo abstraction không cần thiết.

## RULE 10 — TESTING
Mỗi module có test strategy. Khi phát triển tính năng, thêm/cập nhật test phù hợp; nêu chính xác test đã chạy và lý do nếu chưa chạy; không tự khẳng định pass.

## RULE 11 — CHANGE CONTROL
Không tự đổi architecture, database schema, technology stack, business rules hoặc project scope. Nếu cần đổi, trình đề xuất gồm current design, proposed change, reason, impact và alternatives; chờ chủ dự án phê duyệt.

## RULE 12 — PHASE CONTROL
Không tự chuyển phase; chỉ chuyển khi chủ dự án yêu cầu.

## RULE 13 — NO FAKE RESULTS
Không bịa benchmark, cải thiện hiệu năng, kết quả test, quy mô dataset đã xử lý, deployment hoặc thành tích CV. Phân biệt `Planned`, `Implemented`, `Tested`, `Verified`.

## RULE 14 — TASK TRACEABILITY
Mỗi task ghi ID, description, module, dependencies, acceptance criteria và status; xem `TASKS.md`.

## RULE 15 — MINIMAL DIFF
Chỉ chỉnh sửa file cần thiết; không refactor phần không liên quan.

## RULE 16 — STOP ON AMBIGUITY
Hỏi trước khi thiếu thông tin ảnh hưởng architecture, business rules hoặc có nguy cơ mất dữ liệu. Với chi tiết nhỏ, dùng mặc định an toàn và nêu giả định.

## RULE 17 — USER IS PROJECT OWNER
AI hỗ trợ triển khai; chủ dự án quyết định scope, architecture, features, priorities, phase transitions và acceptance.

## Trạng thái hiện tại
Phase 0 **Completed**; Phase 1 **Completed — Requirements & Source Design**; WWI-02/03 **DONE**, WWI-04 **DONE — Design**. DW-01/02/03A/03B/03C **DONE — Design**; DW-04 **DONE — Design Acceptance**. Phase 2 **IN_PROGRESS — Authorized**, giới hạn WWI-05 **IN_PROGRESS**, M1A **DONE — Verification Checkpoint**; WWI-05 chưa hoàn tất. M2 trở đi và Phase 3–9 **Not Started**. Production modules **Not implemented yet**; chỉ B9 isolated PoC có evidence lịch sử. [Owner closure/authorization](docs/architecture/wwi-phase-1-closure-approval.md) ghi APPROVAL-01–05 ngày2026-11-16. Chỉ thực hiện M1A sau Checkpoint A commit; không tự bắt đầu M2/M3.


## DW-03A/B9 follow-up — 2026-11-15

DW-03A **DONE — Design** theo conditional Owner final-review authority sau14 design criteria/actual B9 tests/QA đạt. B9 **Approved — Physical Raw Temporal Representation**: F2→Python str/None→bound psycopg→authoritative TEXT/C exact comparator;không whole Raw/index/retention/runtime approval. A01–A06/B1–B8 giữ nguyên; WWI-04/Phase1 IN_PROGRESS, DW-03B DONE — Design theo Stage 2 conditional acceptance ngày 2026-11-16, DW-03C DONE — Design theo Stage3 conditional acceptance ngày 2026-11-16, D1/D2 Logical+D3 Governance Approved, DW-04 TODO, Phase2–9 Not Started. Chỉ isolated B9 PoC Implemented/Tested,production modules Not implemented yet. Xem current assessment/work-plan G01–G08; không tự bắt đầu task tiếp.

## DW-03B Stage 1 — 2026-11-16 (lịch sử trước Stage 2)

Owner chỉ giao Incremental Discovery & Design Proposal. Xem [work plan](docs/data-models/wwi-dw-03b-work-plan.md). INC-01–INC-06 đều PROPOSED — PENDING PROJECT OWNER APPROVAL; không chốt algorithm/window/delete policy hoặc sửa accepted decisions. Chỉ tài liệu, không DB/Docker/B9 sandbox/pipeline changes, stage/commit/push, đóng DW-03B hoặc bắt đầu DW-03C.


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

## DW-04 — Design Acceptance & Implementation Handoff, 2026-11-16 (lịch sử trước Owner closure)

**DW-04 DONE — Design Acceptance**,20/20 criteria và static/staged QA PASS. [Assessment](docs/data-models/wwi-dw-04-assessment.md), [Implementation Gate Register](docs/data-models/wwi-implementation-gate-register.md) và [Readiness/Handoff](docs/data-models/wwi-implementation-readiness-handoff.md) đối chiếu11 source populations/16 models/22 KPI/12 BRD,31 original gates,18 readiness components và72 planned tests NOT RUN. Approved DW-01/02/03A/03B/03C/B9/INC/CP/D1–D3 giữ nguyên; không thêm business/physical defaults.

Design acceptance khác implementation/operational readiness. WWI-04/Phase1 **IN_PROGRESS**, Phase2–9 **Not Started**; production modules **Not implemented yet**. Không tự bắt đầu task/phase sau; chỉ task tài liệu và một focused commit sau QA theo Owner DW-04 authority, không push/remote/DB/Docker/B9 changes.

## Owner Closure & Phase 2 Authorization — 2026-11-16 (Checkpoint A, trước verification)

Phase 0 **Completed**; Phase 1 **Completed — Requirements & Source Design**; WWI-02/03 **DONE**, WWI-04 **DONE — Design**. DW-01/02/03A/03B/03C **DONE — Design**; DW-04 **DONE — Design Acceptance**. Phase 2 **IN_PROGRESS — Authorized**, giới hạn WWI-05/M1A **IN_PROGRESS — Authorized**; WWI-05 chưa hoàn tất. M2 trở đi và Phase 3–9 **Not Started**. Production modules **Not implemented yet**; chỉ B9 isolated PoC có evidence lịch sử.

[Owner closure/authorization](docs/architecture/wwi-phase-1-closure-approval.md) là authority mới cho APPROVAL-01–05; nguồn là task trực tiếp của Project Owner, không chữ ký điện tử/hệ thống approval bên ngoài. Checkpoint A ghi nhận và commit sau QA, rồi Checkpoint B mới thực hiện M1A chỉ đọc. G01–08/RG01–12/CG01–10/B5 giữ nguyên31 entries;72 runtime scenarios NOT RUN. Approval không cho DML/DDL, infrastructure/identity/config changes, install dependencies, pipeline, M2/M3 hoặc push. Các status/no-start notes của DW-04 phía trên là lịch sử trước approval này.

## WWI-05 / M1A — Verification Report, 2026-11-16 (hiện hành)

M1A **DONE — Verification Checkpoint**, không operational acceptance: secure developer SQL/TLS và11 bounded source reads PASS; tested identity có sysadmin/write permissions nên FAIL suitability, approved extraction profile/consistency/Raw target/reproducibility còn BLOCKED. WWI-05/Phase2 **IN_PROGRESS**; WWI-04 DONE — Design, Phase1 Completed theo Owner approval; M2/M3+ NOT STARTED.

[Environment Report](docs/architecture/wwi-m1a-environment-readiness.md), [Secure Contract](docs/architecture/wwi-secure-connection-contract.md), [26-check Evidence Matrix](docs/architecture/wwi-m1a-gate-evidence.md), [M1A Handoff](docs/architecture/wwi-m1a-handoff.md). Metadata/connectivity là subset, không nghiệm thu IT01 hoặc72 scenarios;31 original gates giữ nguyên. Không source/target writes/infrastructure/identity/dependency changes, B9 sandbox giữ nguyên. Mọi next remediation/provision cần Owner giao task riêng; không tự M2/M3/push.

## WWI-05 / M1B — Source Identity & Consistency Planning, 2026-11-16 (trước OD01–03)

Task Owner M1B chỉ cho review/metadata SELECT và documentation commit sau QA. M1B **DONE — Planning Review** sau acceptance/QA; không identity/grant/config/source/infrastructure changes. [Assessment](docs/architecture/wwi-m1b-assessment.md), [Identity proposal](docs/architecture/wwi-source-identity-proposal.md), [Consistency proposal](docs/architecture/wwi-source-consistency-proposal.md), [DBA/Owner checklist](docs/architecture/wwi-source-dba-owner-checklist.md).

G01/G02/RG01/RG02/CG08 vẫn Pending/BLOCKED; current developer identity FAIL suitability. Recommended static no-writes window A và identity package **PROPOSED — Pending Owner/DBA Approval**, B consistent copy fallback cần separate approval, không tạo copy. M1B planning không operational PASS, không đóng WWI-05/Phase2; M1A DONE Verification/Phase1 Completed/WWI-04 DONE Design giữ nguyên. Original31 gates/72 NOT RUN scenarios/B9 không đổi; M1C/M2/M3 chưa được giao.

## M1B-Approval — Owner Direction & Execution Preparation,2026-11-16

[M1B-OD01–03](docs/architecture/wwi-m1b-owner-decisions.md): dedicated non-admin Windows/minimum object SELECT direction APPROVED;preferred Option A static no-writes APPROVED;Codex chỉ documentation/scripts/test preparation vàlocal static QA/commit. Actual names/grants/window/operator/execution approval chưa có. [DBA scripts](data-sources/security/README.md) PREPARED,NOT RUN;không auto-execute hoặcsource connection ởtask này.

WWI-04 DONE Design,Phase1 Completed,Phase2/WWI-05 IN_PROGRESS,M1A DONE Verification,M1B DONE Planning Review;**M1B-Approval IN_PROGRESS tớiOwner acceptance**,M1C/M2/M3 NOT STARTED. G01/G02 Pending/BLOCKED,31 original gates/72 NOT RUN scenarios vàB9/INC/CP/D1–D4 unchanged. Không administrative/source/settings/infra/dependency/ingestion changes hoặcpush.
