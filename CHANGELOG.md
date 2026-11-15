# Changelog

Ghi nhận thay đổi đã thực hiện; không ghi tính năng mới chỉ ở mức kế hoạch.

## Unreleased

### Changed
- 2026-11-15 — Áp dụng B1–B8 Approved — Logical Policy trong Final SCD2 Specification/backlog/ADRs/C–D references; chọn Tiered Certification, phân biệt Ambiguous và delete candidate, bỏ unapproved survivor/Type1-all-version/physical-member defaults. B9 Pending — Physical Implementation; numerical row/value thresholds được Owner defer tới DW-03 trước Certified publication. Final documentation QA đạt; DW-02E/DW-02 DONE ở mức thiết kế theo quyền nghiệm thu có điều kiện của Owner; WWI-04/Phase 1 In Progress, DW-03/DW-04 TODO; 21 tests NOT RUN, không database/pipeline/DW-03 hoặc push.
- Thực hiện review DW-02E E1–E5 ở mức tài liệu: Final SCD2 Specification, 32 traceability rows, 14 invariants/14 transitions, registry/split-merge/hybrid/restatement proposals, bảy quality metrics và hai certification options; cập nhật backlog B1–B9 và E Assessment. Khuyến nghị tiered certification cho MVP, mọi technical policy mới Pending Owner Approval. E/DW-02/WWI-04 IN_PROGRESS, DW-03 TODO, 21 runtime tests NOT RUN; không sửa source/ADR/BRD evidence, không stage/commit/push.
- Ghi sáu ADR-SCD-01–06 theo Owner approval D01–D06 (2026-11-14): Product Type2 chỉ ba packaging columns, persistent registry/opaque SK, whole-day analytical consensus, reconciled cutover, exact 100 ns, controlled unresolved core/certified mart gates. Đồng bộ classification/SCD direction notes, sửa draft alternatives chưa được chọn và bổ sung identity ambiguity/boundary/split-merge/registry recovery invariants.
- Hoàn tất targeted document review DW-02C/D; 21 test scenarios đủ preconditions/input/dimension/fact/publication/recovery, tất cả NOT RUN. C/D DONE theo authorization có điều kiện; DW-02/WWI-04 vẫn IN_PROGRESS. Chuẩn bị plan E1–E5/backlog B1–B9, DW-02E TODO, không thực hiện E/DW-03/runtime hoặc đổi source evidence/BRD/KPI.

- Chuẩn bị DW-02C/D: identity/SK stability và precision options, historical lookup/unresolved bảy roles, forward state transitions, hybrid cutover/recovery và scoped restatement; test matrix CD-T01–21 chỉ Planned. Technical policies Pending Approval; C/D IN_PROGRESS, chưa commit, không bắt đầu E/DW-03.
- Nghiệm thu DW-02A/B theo SCD-01–07: Customer Category/Group/Bill-to approved tracking direction; CreditLimit/hold optional chưa bật; Product concrete candidates có metadata và KPI impact nhưng chưa approved. Giữ nguyên temporal SQL evidence; identity/lookup/precision/cutover implementation chưa chốt. Commit A/B riêng, DW-02/WWI-04 vẫn IN_PROGRESS.
- Thực hiện DW-02A/B theo Owner authorization: đề xuất classification đủ 31 Customer/25 Product columns; tái kiểm temporal counts/identity, precision probes và lookup theo hai date proxies bằng SELECT. Ghi nhận Customer duplicate-start identity và date-only sensitivity; mọi SCD/identity/fallback options Pending Approval. DW-02/A/B IN_PROGRESS, không commit hoặc triển khai C/D/E/runtime.
- Nghiệm thu DW-01 sau targeted review theo yêu cầu Owner: làm rõ lookup 0..1 version và unresolved ở DW-02; distinct header population/Product filters; single-role customer totals; observed_at/published_at và Product SK theo published state; reference contract/controlled mapping cùng precision requirements. DW-01 DONE, WWI-04 IN_PROGRESS, Phase 1 In Progress; DW-02 chưa bắt đầu. Commit tài liệu nghiệm thu theo task riêng.
- Bắt đầu Phase 1.6 chỉ trong DW-01 theo Owner authorization: logical Kimball/bus, bốn fact/four conformed dimensions, source-to-target mapping, năm Mermaid, change impact và sáu logical marts. Ghi nhận architecture constraints L01–L05; WWI-04/DW-01 IN_PROGRESS, DW-02 chưa bắt đầu. Chỉ tài liệu, không commit hoặc triển khai runtime ở bước này.
- Project Owner phê duyệt BRD-01–BRD-12; chuẩn hóa 22 KPI IDs thành 12 MVP Core, 5 MVP Optional, 2 Deferred, 3 Not Supported by Current Evidence. K10–K13 kiểm chứng read-only công thức AIV trước thuế, repeat theo tháng, attribution hai customer roles và LineProfit nguồn. Phase 1.5/WWI-03 `DONE` ở mức tài liệu; Phase 1 vẫn `In Progress`, không tạo warehouse/pipeline.
- Phase 1.4 source contracts cho chín bảng MVP, extraction matrix, raw requirements, validation matrix và assessment đã được Project Owner nghiệm thu ở mức tài liệu; WWI-02 `DONE` ở phạm vi source design, không tạo code/schema hoặc chốt incremental/KPI.
- Phase 1.3 source relationships, Mermaid ERD, business data flow, SQL kiểm chứng và assessment được Project Owner chấp thuận ở mức tài liệu/khảo sát; chưa chốt KPI hoặc warehouse design, WWI-02 vẫn `IN_PROGRESS`.
- Chủ dự án chấp thuận nội dung Phase 1.1 và nghiệm thu khảo sát Phase 1.2. Bổ sung profiling chỉ đọc cho Sales/Invoicing, Customer temporal và Inventory/integrity cùng truy vấn SQL tái kiểm chứng; cho phép Phase 1.3, WWI-02 vẫn `IN_PROGRESS`.
- Bắt đầu Phase 1 theo phê duyệt của chủ dự án nhưng chỉ khảo sát Phase 1.1 của WWI-02: truy vấn metadata SQL Server WWI chỉ đọc và ghi inventory, dictionary, classification/dependencies, temporal/index, truy vấn kiểm chứng và assessment. WWI-02 vẫn `IN_PROGRESS`, chưa có source contract cuối cùng.
- Hoàn tất nghiệm thu Phase 0 theo phê duyệt có điều kiện của chủ dự án: P0-01 đến P0-06 ở `DONE`; ADR chuyển nguồn được diễn giải bằng tiếng Việt; liên kết, file tracked và secret được kiểm tra lại. Tại thời điểm nghiệm thu Phase 0, Phase 1 vẫn `Not Started`.
- Đồng bộ scope, roadmap, task tracker, kiến trúc và README theo nguồn WWI SQL Server chỉ đọc và warehouse PostgreSQL.
- Chuyển MVP sang Sales/Invoicing, Customer Analytics và Inventory Movements theo thứ tự; Purchasing, Finance và BigQuery là extensions.
- Ghi ADR chuyển nguồn và giữ các quyết định KPI, grain, SCD2, incremental, inventory và ngưỡng chất lượng ở trạng thái Open.
- Điều chỉnh Phase 3–4 có kiểm tra chất lượng cơ bản; Phase 5–6 hoàn thiện Sales Airflow/monitoring trước khi mở rộng subject areas.
- Đối chiếu đề cương cũ và bổ sung yêu cầu tái lập local, bảo mật nguồn, unit/integration/e2e, CI, quan sát batch, tối ưu truy vấn có số đo và kiểm soát chi phí cloud vào scope/roadmap WWI.
- Bổ sung quy tắc `.gitignore` cho credentials, file database và bản trích xuất nguồn; P0-05 chuyển `REVIEW` sau kiểm tra Git readiness.
- WWI-01 được chủ dự án nghiệm thu; TASKS.md ghi trạng thái `DONE` và bằng chứng tài liệu/cấu trúc.
- Git repository local được khởi tạo trên branch `main`; danh sách file và staged diff được kiểm tra trước baseline commit theo P0-06.

### Removed
- Chín CSV và các tài liệu thiết kế/source contracts dành riêng cho dataset và hệ thống mô phỏng cũ.
- Các thư mục chỉ dành cho thiết kế nguồn trước đây, không chứa chức năng dùng chung.
- PDF đề cương cũ sau khi các yêu cầu kỹ thuật chung còn phù hợp đã được chuyển vào tài liệu hiện hành.

### Status
- Phase 0: Completed ở mức tài liệu và repository. Chưa triển khai hoặc kiểm thử pipeline.
- P0-01 đến P0-06 và WWI-01: `DONE`. Không tạo remote hoặc push; Phase 1.1 và khảo sát Phase 1.2 được chấp thuận, WWI-02 ở `IN_PROGRESS`.
