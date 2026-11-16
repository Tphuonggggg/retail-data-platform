# architecture

- **Purpose:** Kiến trúc khái niệm của pipeline WWI → PostgreSQL.
- **Owned files / responsibilities:** [system overview](system-overview.md), [module dependencies](module-dependencies.md) và [data flow](data-flow.md). Chúng ghi architecture constraints và dẫn tới logical DW design; KPI nghiệp vụ đã duyệt, physical schema/implementation còn chờ task sau.
- **Parent module:** [docs](../README.md).
- **Status:** Phase 1.6/DW-01 thiết kế logic đã nghiệm thu; [Logical DW Design](../data-models/wwi-logical-dw-design.md) ghi bus/fact/dimension/marts, không lặp source architecture. Runtime: Not implemented yet.


DW-04 tại mốc design acceptance trước Owner closure: [Assessment](../data-models/wwi-dw-04-assessment.md), [31 original gates](../data-models/wwi-implementation-gate-register.md), [18 components/M1–M9/test handoff](../data-models/wwi-implementation-readiness-handoff.md). DW-04 DONE — Design Acceptance sau20/20 criteria/static/staged QA. Approved DW-01/02/03/B9 scope giữ nguyên; triển khai/operational readiness chưa đạt. WWI-04/Phase1 IN_PROGRESS, Phase2–9 Not Started.

Current governance: [Phase1 closure/Phase2 authorization](wwi-phase-1-closure-approval.md). Phase 0 **Completed**; Phase 1 **Completed — Requirements & Source Design**; WWI-02/03 **DONE**, WWI-04 **DONE — Design**. DW-01/02/03A/03B/03C **DONE — Design**; DW-04 **DONE — Design Acceptance**. Phase 2 **IN_PROGRESS — Authorized**, giới hạn WWI-05 **IN_PROGRESS**, M1A **DONE — Verification Checkpoint**; WWI-05 chưa hoàn tất. M2 trở đi và Phase 3–9 **Not Started**. Production modules **Not implemented yet**; chỉ B9 isolated PoC có evidence lịch sử.


M1A hiện hành: [Local Environment Readiness](wwi-m1a-environment-readiness.md), [Secure Connection Contract](wwi-secure-connection-contract.md), [Gate/Evidence Matrix](wwi-m1a-gate-evidence.md), [Implementation Handoff](wwi-m1a-handoff.md). Checkpoint DONE — Verification, operational readiness BLOCKED; no M2/M3.


M1B planning: [Identity privilege proposal](wwi-source-identity-proposal.md), [Consistency options](wwi-source-consistency-proposal.md), [DBA/Owner checklist](wwi-source-dba-owner-checklist.md), [Assessment/evidence](wwi-m1b-assessment.md). Review DONE sau QA; all concrete identity/method approvals Pending,source operational readiness vẫn BLOCKED. Không thay original policies/gates.


M1B-Approval hiện hành: [Owner decisions](wwi-m1b-owner-decisions.md),[prepared security scripts](../../data-sources/security/README.md),[static-window procedure](wwi-source-consistency-proposal.md#7-static-no-writes-operating-procedure--prepared-not-executed),[execution authorization request](wwi-source-dba-owner-checklist.md#6-compact-execution-authorization-request--ready-for-review-not-authorized). Direction/preferred approach approved,actual package/window execution pending;task IN_PROGRESS,chưa M1C/M2/M3 hoặcG01/G02 PASS.
