# architecture

- **Purpose:** Kiến trúc khái niệm của pipeline WWI → PostgreSQL.
- **Owned files / responsibilities:** [system overview](system-overview.md), [module dependencies](module-dependencies.md) và [data flow](data-flow.md). Chúng ghi architecture constraints và dẫn tới logical DW design; KPI nghiệp vụ đã duyệt, physical schema/implementation còn chờ task sau.
- **Parent module:** [docs](../README.md).
- **Status:** Phase 1.6/DW-01 thiết kế logic đã nghiệm thu; [Logical DW Design](../data-models/wwi-logical-dw-design.md) ghi bus/fact/dimension/marts, không lặp source architecture. Runtime: Not implemented yet.


DW-04 hiện hành: [Assessment](../data-models/wwi-dw-04-assessment.md), [31 original gates](../data-models/wwi-implementation-gate-register.md), [18 components/M1–M9/test handoff](../data-models/wwi-implementation-readiness-handoff.md). DW-04 DONE — Design Acceptance sau20/20 criteria/static/staged QA. Approved DW-01/02/03/B9 scope giữ nguyên; triển khai/operational readiness chưa đạt. WWI-04/Phase1 IN_PROGRESS, Phase2–9 Not Started.
