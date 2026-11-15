# Roadmap

Chủ dự án quyết định nghiệm thu và chuyển phase. Trạng thái tài liệu không chứng minh runtime đã hoạt động. **Phase 0: Completed; Phase 1: In Progress (Phase 1.1–1.5 được chấp thuận ở mức tài liệu; WWI-02/03 DONE; Phase 1.6/WWI-04 IN_PROGRESS; DW-01 DONE ở mức thiết kế logic, DW-02 DONE; DW-02A/B DONE; DW-02C/D DONE ở mức thiết kế; DW-02E DONE — B1–B8 Approved — Logical Policy và design acceptance/QA đạt ngày 2026-11-15); Phase 2–9: Not Started.** Task và bằng chứng ở [TASKS.md](TASKS.md).

## Nguyên tắc triển khai

Nguồn duy nhất của MVP là SQL Server WWI **chỉ đọc**; PostgreSQL là warehouse tự xây. Hoàn thiện Sales/Invoicing **end-to-end** trước Customer Analytics rồi Inventory Movements. Data quality cơ bản được tích hợp ngay tại ingestion/warehouse. Phase 6 tập trung quality gates, monitoring tập trung và failure nâng cao. Purchasing, Finance và BigQuery là phần mở rộng.

Full/incremental load, checkpoint, idempotency, SCD2, reconciliation và recovery là mục tiêu kỹ thuật. Môi trường thử nghiệm độc lập để chứng minh INSERT/UPDATE và incremental end-to-end sẽ được **thiết kế trước**, chỉ tạo/chạy sau task và phê duyệt riêng. Không thay đổi WWI gốc. Không mặc định temporal history là lịch sử đầy đủ của mọi giao dịch.

## Phase 0: Project Initialization

- **Objective:** Cấu trúc repository, quy tắc AI và tài liệu kiến trúc WWI nhất quán.
- **Tasks:** Đồng bộ scope/roadmap/tasks/architecture/README/ADR; loại bỏ file chỉ phục vụ nguồn cũ; kiểm kê file nhạy cảm, file lớn và `.gitignore`; lập task khởi tạo Git.
- **Dependencies:** Quyết định chuyển nguồn của chủ dự án.
- **Deliverables:** Tài liệu hiện hành, cấu trúc module dùng chung, Git readiness checklist và baseline commit đã kiểm tra. PDF đề cương cũ được rà yêu cầu kỹ thuật chung rồi loại khỏi repository.
- **Acceptance Criteria:** Không có link tới file đã xóa, không có task nguồn cũ active, không có code/secret/kết quả giả; Git chỉ được khởi tạo khi task riêng được giao.
- **Status:** Completed.

## Phase 1: WWI Requirements & Source Design

- **Objective:** Chốt source contract, business rules và thiết kế Sales trước.
- **Tasks:** Data dictionary/ERD WWI, PK/FK/timestamps, KPI/revenue/tax/customer role, grain, temporal/SCD2 và incremental proposals; mở contract Customer/Inventory theo thứ tự.
- **Dependencies:** Phase 0 được chủ dự án nghiệm thu và cho phép Phase 1.
- **Deliverables:** Requirements, source contract/mapping, KPI matrix và ADR quyết định.
- **Acceptance Criteria:** Các quyết định ảnh hưởng Sales schema/pipeline được duyệt; giới hạn snapshot/temporal ghi rõ.
- **Status:** In Progress — Phase 1.1–1.5 được chủ dự án chấp thuận ở mức tài liệu; WWI-02 và WWI-03 `DONE`. Phase 1.6/WWI-04 `IN_PROGRESS`, DW-01 DONE, DW-02 DONE; DW-02A/B DONE; DW-02C/D DONE ở mức thiết kế; DW-02E DONE — B1–B8 Approved — Logical Policy và design acceptance/QA đạt ngày 2026-11-15; physical warehouse schema chưa duyệt.

### Phase 1.6 / WWI-04 — kế hoạch thiết kế

DW-01 Logical Dimensional Modeling đã nghiệm thu theo Kimball/bốn facts/conformed dims và L01–L05 Owner đã duyệt. Bàn giao [logical design](docs/data-models/wwi-logical-dw-design.md) đã qua targeted review. Các task sau cần Owner giao riêng: DW-02 SCD2 & Temporal History; DW-03A Full Load & Raw Layer; DW-03B Incremental; DW-03C Change Propagation & Recovery; DW-04 Final Verification & Acceptance. Dependencies/acceptance ở [TASKS.md](TASKS.md). DW-02A/B đã nghiệm thu; Owner đã nghiệm thu thiết kế C/D, chưa triển khai service/database/pipeline.

DW-02A/B đã nghiệm thu khảo sát và ghi SCD-01–07 trong [assessment A/B](docs/data-models/wwi-dw-02ab-assessment.md). D01 sau đó chốt ba Product Type2 columns; B1–B8 identity/lookup/cutover/recovery/correction logical policies đã duyệt; physical procedures và numerical thresholds vẫn pending. A/B đã commit riêng; C/D đã nghiệm thu tài liệu theo D01–D06, technical details còn Pending Approval; DW-02E/DW-02 DONE ở mức thiết kế sau B1–B8 approval và QA; DW-03A IN_PROGRESS; logical policies đã được Owner duyệt đúng cấp ở milestone bên dưới; concrete/physical/runtime gates còn mở. DW-03B/C chưa bắt đầu, không triển khai runtime.

## Phase 2: Local Source & Destination Readiness

- **Objective:** Chuẩn bị kết nối WWI chỉ đọc và PostgreSQL đích.
- **Tasks:** Xác minh quyền đọc, bảo mật cấu hình, baseline metadata, Docker Compose cho service dự án và kế hoạch test incremental độc lập. Tài liệu tái lập phải nêu điều kiện có WWI hợp lệ bên ngoài repository.
- **Dependencies:** Phase 1 và phê duyệt triển khai.
- **Deliverables:** Hướng dẫn môi trường, connection contract và kết quả kiểm tra quyền.
- **Acceptance Criteria:** Source chỉ đọc; đích sẵn sàng và môi trường local có thể tái lập theo hướng dẫn; không lộ credential, commit backup hoặc sửa WWI gốc.
- **Status:** Not Started.

## Phase 3: Sales Ingestion & Incremental Loading

- **Objective:** Nạp Sales vào raw/staging với khả năng chạy lại an toàn.
- **Tasks:** Full extract, checkpoint/tie-breaker, upsert, retry/backfill, validation/quarantine và đối soát cơ bản. Thử INSERT/UPDATE end-to-end trong môi trường độc lập sau phê duyệt.
- **Dependencies:** Phase 1–2 và source contract Sales.
- **Deliverables:** Python ingestion, raw/staging, unit/integration tests và batch log gồm row count, duration, error type.
- **Acceptance Criteria:** Full load/rerun đối soát được; lỗi không làm checkpoint tiến; incremental chỉ ghi Verified khi có bằng chứng thử nghiệm hợp lệ.
- **Status:** Not Started.

## Phase 4: Sales Warehouse & Transformations

- **Objective:** Xây Sales facts/dimensions theo grain và KPI đã duyệt.
- **Tasks:** dbt/SQL models, mapping invoice/order/transaction, data quality cơ bản (unique, not null, relationships, accepted values, business rules), tests và reconciliation; ghi baseline kế hoạch truy vấn trước tối ưu.
- **Dependencies:** Sales ingestion và quyết định Phase 1.
- **Deliverables:** Warehouse PostgreSQL local, dbt docs/tests và kết quả đối soát Sales.
- **Acceptance Criteria:** Grain đúng, không double count, KPI có công thức được duyệt và tests thực chạy.
- **Status:** Not Started.

## Phase 5: Sales Airflow Orchestration

- **Objective:** Điều phối Sales pipeline đã chạy độc lập, không chờ Customer/Inventory.
- **Tasks:** DAG, lịch, dependency, retry, rerun/backfill và thử lỗi cơ bản.
- **Dependencies:** Phase 3–4 cho Sales.
- **Deliverables:** Sales DAG và hướng dẫn vận hành.
- **Acceptance Criteria:** Luồng Sales chạy theo thứ tự; lỗi có thể xác định và rerun an toàn.
- **Status:** Not Started.

## Phase 6: Sales Quality Gates & Centralized Monitoring

- **Objective:** Hoàn thiện Sales end-to-end bằng quality gates và failure recovery nâng cao.
- **Tasks:** Reconciliation gates, logs/metrics/alerts, batch status và failure scenarios; đo thời gian chạy/truy vấn và xem execution plan phù hợp; không trì hoãn kiểm tra cơ bản từ Phase 3–4.
- **Dependencies:** Sales ingestion, warehouse và Airflow.
- **Deliverables:** Quality reports, monitoring và runbook.
- **Acceptance Criteria:** Sai lệch bị phát hiện theo ngưỡng đã duyệt; batch/lỗi truy vết và phục hồi được.
- **Status:** Not Started.

## Phase 7: Customer & Inventory MVP Expansion, Analytics

- **Objective:** Mở rộng tuần tự Customer rồi Inventory Movements sau Sales end-to-end; hoàn thiện marts/Power BI.
- **Tasks:** Customer ingestion/SCD2/mart, sau đó stock movement ingestion/fact/mart; Airflow/DQ cho từng lát cắt; báo cáo Sales/Customer/Inventory.
- **Dependencies:** Sales qua Phase 6; contract/KPI riêng được duyệt.
- **Deliverables:** Ba subject areas MVP, marts, report, test/đối soát.
- **Acceptance Criteria:** Mỗi lát cắt có grain, lineage, data quality và recovery; không tự suy daily inventory balance hoặc lịch sử ngoài bằng chứng.
- **Status:** Not Started.

## Phase 8: Controlled Extensions & BigQuery

- **Objective:** Purchasing, Finance hoặc BigQuery theo task và phê duyệt riêng.
- **Dependencies:** MVP local ổn định và quyết định từng extension.
- **Deliverables:** Chỉ những phần được triển khai và kiểm thử thực tế.
- **Acceptance Criteria:** Có kiểm thử tương đương, giới hạn quota/budget, bảo mật/chi phí và benchmark thực đo nếu triển khai; không chặn MVP local.
- **Status:** Not Started.

## Phase 9: Testing, Documentation & Portfolio

- **Objective:** Kiểm thử toàn luồng và hướng dẫn tái lập.
- **Dependencies:** MVP local Phase 3–7; Phase 8 chỉ khi extension được giao.
- **Deliverables:** Unit/integration/e2e/failure tests, runbooks, CI workflow khi Git/code đã có, demo và tài liệu. Ghi số đo trước/sau nếu có tối ưu PostgreSQL đích.
- **Acceptance Criteria:** Người khác tái lập được MVP local với điều kiện chuẩn bị nguồn WWI được tài liệu hóa; CI kiểm tra đúng khi triển khai; mọi claim/benchmark có bằng chứng.
- **Status:** Not Started.

## Phase 0 checklist

- [x] Cấu trúc module và quy tắc AI đã có.
- [x] Tài liệu kiến trúc được chuyển sang WWI; các file chỉ phục vụ nguồn cũ được loại khỏi repository.
- [x] Không tạo code/schema/Docker service hoặc khẳng định kết quả test.
- [x] Đã kiểm kê file nhạy cảm/lớn và kiểm tra quy tắc `.gitignore` bằng Git local.
- [x] Đã rà PDF đề cương, chuyển các yêu cầu kỹ thuật chung còn phù hợp vào tài liệu WWI và loại PDF cũ.
- [x] WWI-01 được chủ dự án review và phê duyệt; bằng chứng ghi trong TASKS.md.
- [x] Chủ dự án phê duyệt P0-01, P0-02, P0-05, P0-06 và cho phép đóng Phase 0 nếu P0-03/P0-04 đạt; bằng chứng kiểm tra lại ghi trong TASKS.md.
- [x] Khởi tạo Git local và tạo baseline commit theo task P0-06 được chủ dự án giao; không tạo remote/push.
- [x] Chủ dự án chấp thuận nội dung Phase 1.1 và khảo sát Phase 1.2, cho phép Phase 1.3; về sau đã duyệt WWI-03 ở mức tài liệu, WWI-04 chưa bắt đầu.

Checklist là rà soát tài liệu và filesystem, không phải kết quả kiểm thử pipeline.

## DW-02E / DW-02 — finalization theo logical approval

[Work plan E1–E5 và Technical Backlog](docs/data-models/wwi-dw-02e-work-plan.md): decision traceability, identity/validity/SK invariants, transitions/cutover, publication gates, final handoff. DW-02E/DW-02 DONE ở mức thiết kế: [Final Specification](docs/data-models/wwi-final-scd2-design-specification.md) và [Assessment](docs/data-models/wwi-dw-02e-assessment.md) ghi kết quả E1–E5. B1–B8 Approved — Logical Policy (2026-11-15), B9 Pending — Physical Implementation; design acceptance và QA đã đạt theo quyền Owner ngày 2026-11-15; numerical thresholds chưa tự chọn, gate trước Certified publication; DW-03A nay được giao riêng Stage 1 proposal; physical implementation cần task/approval riêng. DW-02 DONE không đóng WWI-04 hoặc Phase 1; DW-03A IN_PROGRESS, DW-03B/C và DW-04 TODO.

### DW-03A Stage 1 — proposal trước logical approval (lịch sử)

Bàn giao [work plan](docs/data-models/wwi-dw-03a-work-plan.md), [architecture/full-Raw proposal](docs/data-models/wwi-dw-03a-full-raw-design-proposal.md), [A01–A06 register](docs/data-models/wwi-dw-03a-decision-register.md) và [assessment](docs/data-models/wwi-dw-03a-assessment.md). Stage 1 chỉ phân tích source consistency, Raw storage, metadata/retry, B9 precision và publication; mọi quyết định mới PROPOSED — PENDING PROJECT OWNER APPROVAL. Chưa final design acceptance, không chuyển DW-03A DONE, không code/schema/database/Docker hoặc bắt đầu DW-03B/C. Không commit/push.

### DW-03A — logical approval milestone, chưa final acceptance

Ngày 2026-11-15, Project Owner formal approve **A01/A03/A04/A06 — Logical Policy; A02 — Conditional Logical Policy; A05 — PoC Direction Only (F2)** trong [Decision Register](docs/data-models/wwi-dw-03a-decision-register.md). Full-preservation/immutable-capture/identity/atomic-pinning principles được ghi nhận, không chọn final Raw schema/retention/driver/datatype/encoding/collation hoặc certify runtime.

[Work Plan](docs/data-models/wwi-dw-03a-work-plan.md) sections 5–6 giữ backlog G01–G08 và narrow SQL F2 → pyodbc string → psycopg text-parameter handoff. Static window cần no-write evidence toàn extraction interval; nếu không thì separately approved verified copy. SNAPSHOT/RCSI OFF giữ nguyên; không tự long SERIALIZABLE/NOLOCK consistency claim. Driver/PG/persistence/atomicity/recovery tests vẫn chưa chạy; F2 SQL source subset PASS không vượt toàn B9.

**DW-03A IN_PROGRESS; B9 Pending Physical Approval; DW-03B/C/DW-04 TODO; WWI-04/Phase 1 In Progress.** Chưa final DW-03A acceptance hoặc phase transition. Current milestone chỉ cập nhật tài liệu/QA và một documentation-only commit sau kiểm tra theo Owner, không install, database changes, pipeline hoặc push.
