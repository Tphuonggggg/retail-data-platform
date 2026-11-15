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
Phase 0 — Project Initialization: Completed. Phase 1 — WWI Requirements & Source Design: In Progress; Phase 1.1–1.5 đã được chấp thuận ở mức tài liệu, WWI-02/03 `DONE`, Phase 1.6/WWI-04 IN_PROGRESS; DW-01 DONE ở mức thiết kế logic, DW-02 DONE; DW-02A/B DONE; DW-02C/D DONE ở mức thiết kế; DW-02E DONE — B1–B8 Approved — Logical Policy và design acceptance/QA đạt ngày 2026-11-15. Các phase 2–9: Not Started. Chưa có module chức năng được triển khai.


## DW-03A/B9 follow-up — 2026-11-15

DW-03A **DONE — Design** theo conditional Owner final-review authority sau14 design criteria/actual B9 tests/QA đạt. B9 **Approved — Physical Raw Temporal Representation**: F2→Python str/None→bound psycopg→authoritative TEXT/C exact comparator;không whole Raw/index/retention/runtime approval. A01–A06/B1–B8 giữ nguyên; WWI-04/Phase1 IN_PROGRESS,DW-03B/C/DW-04 TODO,Phase2–9 Not Started. Chỉ isolated B9 PoC Implemented/Tested,production modules Not implemented yet. Xem current assessment/work-plan G01–G08; không tự bắt đầu task tiếp.
