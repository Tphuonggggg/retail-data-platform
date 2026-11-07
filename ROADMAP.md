# Roadmap

Chủ dự án quyết định nghiệm thu và chuyển phase. Trạng thái tài liệu không chứng minh runtime đã hoạt động. **Phase 0: Completed; Phase 1: In Progress (Phase 1.1 và khảo sát Phase 1.2 đã được chấp thuận; Phase 1.3 được phép thực hiện); Phase 2–9: Not Started.** Task và bằng chứng ở [TASKS.md](TASKS.md).

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
- **Status:** In Progress — Phase 1.2 đã được nghiệm thu về mặt khảo sát; Phase 1.3 được phép thực hiện; WWI-02 vẫn `IN_PROGRESS`, WWI-03 chưa bắt đầu.

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
- [x] Chủ dự án chấp thuận nội dung Phase 1.1 và khảo sát Phase 1.2, cho phép Phase 1.3; chưa phê duyệt WWI-03/04.

Checklist là rà soát tài liệu và filesystem, không phải kết quả kiểm thử pipeline.
