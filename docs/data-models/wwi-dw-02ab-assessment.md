# DW-02A/B Assessment — SCD Classification & Temporal Coverage

**DW-02A/B DONE ở mức khảo sát/phân loại theo phê duyệt SCD-01–07 và quyền nghiệm thu có điều kiện của Owner.** Phase 1 In Progress, WWI-04 và DW-02 IN_PROGRESS. Hồ sơ A/B được commit riêng sau QA; không thay bốn facts/BRD-01–12. Các technical policies chưa được phê duyệt.

**Ghi chú chuyển tiếp:** các câu “Product candidates/technical choices Pending Approval” dưới đây phản ánh snapshot nghiệm thu A/B tại commit `b293fdb`. Sau đó Owner đã duyệt [ADR-SCD-01–06](../adr/README.md), gồm Product set ba packaging columns và các architecture directions. Classification hiện hành đã đồng bộ ADR; numeric findings/SQL evidence của A/B giữ nguyên. Technical implementation details vẫn pending; ghi chú này không sửa nguyên tắc SCD-01–07 hoặc kết quả khảo sát cũ.

## Executive summary

Classification bao phủ đầy đủ 31 Customer và 25 Product source columns; Customer Category/Group/Bill-to có Approved Type 2 direction; CreditLimit/hold optional chưa bật. Product concrete candidates và technical policies vẫn Pending Approval. Physical Customer history có 714 versions so với 713 FOR SYSTEM_TIME ALL, một zero-duration và một duplicate-start identity group; source full period identity hiện unique. Product có 671 versions, không zero-duration/gap/overlap. Customer/Product finite periods trong snapshot không có phần dưới microsecond nhưng sentinel và future 100 ns changes vẫn có rủi ro; chưa test PostgreSQL conversion.

Lookup start/end-of-day đều một match cho source rows khảo sát, nhưng 6 invoice/customer, 284 invoice-product và 291 order-product rows chọn source version khác nhau theo proxy. Không chọn as-of chỉ vì một proxy phủ đủ rows. Product source version khác chủ yếu phản ánh CustomFields/Tags theo profiling cũ, chưa là analytical Type2 change. Current Product availability verified ở nguồn, chưa có DW published state để xác minh.

## Deliverables không trùng chức năng

| Yêu cầu | File |
| --- | --- |
| Customer/Product Attribute Classification Matrix, impacts/dependencies | [Classification](wwi-scd-attribute-classification.md) |
| Temporal Coverage, Precision/Version Identity, Historical Lookup Matrix, forward readiness | [Temporal Assessment](wwi-scd-temporal-assessment.md) |
| SQL tái kiểm chứng và outputs ngày 2026-11-14 | [SQL Evidence](wwi-scd-temporal-evidence.md) |
| Acceptance, Open Decisions, recommendations | Tài liệu này |

Template attribute changes tái dùng Q06/Q08 của Phase 1.2; không nhân bản SQL có cùng chức năng. C01/C02 và P01/P02 bổ sung counts/identity trong classification; full SQL evidence lưu aggregate outputs, không customer records. Counts/proxies chạy bằng Windows integrated auth, SELECT-only, không temp tables/DDL/DML. Không tạo PostgreSQL schema, test SQL Server database hoặc pipeline, không cài dependency.

## Acceptance checklist

| Tiêu chí | Evidence | Kết quả mức bàn giao |
| --- | --- | --- |
| Full attribute classification Customer/Product | 31+25 source columns, riêng từng dòng, đủ 9 cột yêu cầu | PASS — SCD-01–07 principles approved; Product/technical policy pending |
| Type2 có historical meaning, không chọn tất cả | Reason/KPI impact, conditional/optional gates; metadata/excluded riêng | PASS — đề xuất |
| 0 observed ≠ immutable; LastEditedBy audit | Quy ước và từng dòng matrix; Q06/Q08 evidence | PASS — tài liệu |
| Natural key/version và temporal counts/distributions | C01/C02/P01/P02, current/archive/ALL tách biệt | PASS — Verified SQL |
| Zero-duration/overlap/gap/identity | Customer 1/0/0, Product 0/0/0; C04 duplicate-start | PASS — Verified SQL, policy chưa chọn |
| Không đồng nhất system/business/observation time | Temporal assessment phân biệt năm khái niệm | PASS — tài liệu |
| Precision risk và preservation options | C03/P03, full tuple/start key, sentinel, no physical type choice | PASS — khảo sát/options |
| Lookup Invoice/Order/Movement/current Product | L01–L07, buyer và bill-to riêng, proxy sensitivity | PASS — Verified SQL/giới hạn rõ |
| Không chọn as-of/fallback hoặc SCD algorithm | Options Pending Approval, invariants DW-01 giữ nguyên | PASS — phạm vi |
| Forward history chưa claim implementation | Requirements/cutover/test scenarios chỉ phân tích | PASS — tài liệu |
| Database/pipeline/business rules không thay đổi | Read-only queries, diff chỉ Markdown; DW-01 files giữ nguyên | PASS — phạm vi |
| Markdown/secret/Git checks | 381 local links/0 broken; source-column coverage 31/31 và 25/25; 11 file Markdown đúng scope; quét mẫu secret/whitespace/fences không phát hiện; git diff --check sạch; staging rỗng, temporal evidence SHA256 không đổi; QA trước commit nghiệm thu A/B | PASS — QA tài liệu |

A/B đạt acceptance criteria ở mức khảo sát/tài liệu theo Owner authorization; không phải nghiệm thu implementation. SCD-01–07 được ghi trong classification, tách Approved Principles khỏi technical policies. Product Type 2 columns chưa tự approved; zero-duration giữ Raw/audit, unresolved không fallback. Temporal SQL evidence giữ SHA256 `45259C87E3543B074786B0655925D2B0A3266403C9BF60FBE9CE805D76694986`. Runtime tests chưa chạy.

## Quyết định chuyển tiếp — principles approved, technical policies pending

| ID | Vấn đề cần Owner duyệt | Đề xuất / lựa chọn để review | Gate |
| --- | --- | --- | --- |
| AB-01 | Thuộc tính analytical và Type1/2 | SCD-01 duyệt Customer Category/Group/Bill-to direction; SCD-02 Product concrete set Pending Approval; Name/AccountOpenedDate còn candidates | Trước DW SCD policy |
| AB-02 | Customer optional scope | CreditLimit/hold optional chưa kích hoạt; bill-to direction Approved, không thay invoice roles hoặc thêm Finance KPI | Trước tracking set |
| AB-03 | Identity và zero-duration | Source NK+full period hiện unique; start-only đã không unique. Giữ audit zero-duration; DW representation/filter policy chưa chọn | Trước SK/identity design |
| AB-04 | Date-only lookup/business-effective validity | Review start/end sensitivity và evidence nghiệp vụ; không chọn proxy/fallback ngay | Trước historical fact dimension lookup |
| AB-05 | Precision representation | Canonical period/ticks/timestamp+residual và SK mapping; kiểm sentinel, rounding, conversion ties | Trước physical types/extraction |
| AB-06 | History reconstruction → forward observation | Cần boundary/history_basis, current reconciliation, late history/restate implications; chưa có batch observation | Trước cutover algorithm |
| AB-07 | Reference labels/history | Contract extension cho category/group/color/package nếu dùng; TransactionTypes vẫn dependency riêng từ DW-01 | Trước ingestion liên quan |

## Recommendations cho DW-02C/D

Owner đã cho phép thiết kế DW-02C/D sau nghiệm thu A/B: identity/SK, lookup/unresolved, forward tracking/cutover/recovery. Các technical options cần Owner review riêng. Commit nghiệm thu A/B không gồm bản C/D; DW-02E và DW-03 chưa bắt đầu.
