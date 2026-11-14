# DW-01 Assessment — Logical Dimensional Modeling

**DW-01 DONE ở mức thiết kế logic sau targeted review ngày 2026-11-14, theo quyền nghiệm thu có điều kiện của Project Owner.** WWI-04 IN_PROGRESS; DW-02 và các phần tiếp theo TODO. Phase 1 vẫn In Progress. Đầu vòng xây dựng DW-01 Git sạch tại `411e3eed9cb0b422e0c19fdcd0566b2691a31fd2`; đầu vòng targeted review có đúng 16 Markdown files DW-01 chưa commit, được bảo toàn và hoàn thiện để commit nghiệm thu. Không triển khai database/pipeline.

## Executive summary và deliverables

Đã chuẩn bị thiết kế logical bốn fact dùng bốn conformed dimensions. Order và Invoice header intermediates bảo toàn population counts; không tạo core fact mới. Buyer/bill-to giữ hai role; default measure S05; không đưa Recognized Revenue, official Gross Profit/COGS, AOV, refund allocation, daily balance hay stockout risk vào MVP.

| Deliverable yêu cầu | File chịu trách nhiệm |
| --- | --- |
| Logical DW specification, architecture constraints, BRD/KPI traceability, Kimball Bus Matrix | [Logical DW Design](wwi-logical-dw-design.md) |
| Fact & Dimension Dictionary | [Dictionary đích](wwi-fact-dimension-dictionary.md) |
| Source-to-Target Logical Mapping | [Mapping](wwi-logical-source-to-target.md) |
| Bốn star schemas và consolidated bus | [Mermaid diagrams](wwi-logical-star-schemas.md) |
| Change Impact Matrix | [Change Impact](wwi-change-impact-matrix.md) |
| Sáu Logical Data Mart Specifications | [Marts](wwi-logical-data-marts.md) |
| Acceptance/risks/open decisions | Tài liệu này |

## Evidence và giới hạn kiểm chứng

Verified: baseline Git; metadata/cột/PK/FK/NULL từ Phase 1.1–1.4; KPI arithmetic K01–K13 từ Phase 1.5; BRD do Owner duyệt. Trong DW-01 chỉ chạy thêm SELECT sys.columns/sys.types cho TransactionTypes (evidence/method trong mapping); không chạy benchmark, full load, warehouse query hoặc test DB. Các proposed models, SK/SCD policy, group propagation và mart tests là thiết kế, chưa runtime Verified. Không render Mermaid bằng package mới; đã review thủ công cấu trúc năm diagrams, chưa xác nhận qua renderer tự động.

## Acceptance checklist — nghiệm thu thiết kế logic

| Acceptance criteria | Evidence | Kết quả |
| --- | --- | --- |
| Bốn declared grains đúng | Dictionary: InvoiceLineID, OrderLineID, StockItemTransactionID, current StockItemID | PASS — tài liệu |
| Conformed dimensions rõ, không thêm dimension không có requirement | Bus Matrix, bốn dimensions và role/N/A | PASS — tài liệu |
| Buyer và Bill-to riêng | Hai FKs invoice, C03/C04 riêng role; lấy invoice header roles | PASS — tài liệu |
| Header metrics không nhân dòng | Hai intermediates; header coverage kể cả no-line; natural-key distinct | PASS — tài liệu |
| Mapping không invent source columns | Dictionary nguồn và metadata bổ sung TransactionTypes; technical metadata ghi do đích tạo | PASS — đối chiếu metadata |
| KPI/BRD traceability | Ma trận đủ BRD-01–12; C05 và I05 bổ sung; IDs khớp catalog | PASS — tài liệu |
| Measures tuân thủ KPI duyệt | S03 incl tax/S04 tax/S05 before tax/S06 AIV/S09 source profit | PASS — tài liệu |
| SCD2 không giả định lịch sử đầy đủ | Customer 1 zero-duration, product 0; gap/coverage/date-only limitations; policy DW-02 | PASS — tài liệu |
| Inventory Current không là daily balance | Grain current state, không date FK, I06/I07 ngoài MVP | PASS — tài liệu |
| Header-only changes được bao phủ | Invoice/Order header rows trong Change Impact Matrix, nhóm cũ/mới | PASS — tài liệu |
| Full/incremental requirements, chưa chốt algorithm | L01–05 và từng fact; DW-03A/B/C boundaries | PASS — tài liệu |
| Không code/DDL/pipeline/source changes | Chỉ Markdown; read-only metadata SELECT; runtime Not implemented yet | PASS — phạm vi |
| Secrets/links/diff | 355 local Markdown links/0 broken; 16 file Markdown đúng scope; quét mẫu secret/whitespace/fences không phát hiện; git diff --check sạch; staging rỗng và HEAD không đổi | PASS — QA tài liệu |

PASS trong bảng là nghiệm thu thiết kế logic, không phải runtime verification. Project Owner đã chấp thuận tổng thể và cho phép DONE sau targeted review đạt; năm vấn đề dưới đây đều đạt, không có blocker trọng yếu cho DW-01. Physical schema, dimension lookup policy, SCD2, incremental/recovery và approval reference ingestion vẫn là gates của task sau, không bị coi đã chốt.

## Targeted review A–E và những chỗ đã sửa

| Vấn đề | Kết luận / sửa tài liệu | Evidence / acceptance |
| --- | --- | --- |
| A — SCD2 lookup | Bổ sung invariant 0..1 real match mỗi fact/role; >1 chặn publication; cấm NK-only JOIN tất cả versions. Unresolved/fallback/business-effective time giữ ở DW-02; diagrams chỉ mô tả resolved state | Dictionary, Mapping H/C, Star Schemas; PASS — logical |
| B — Header population | Xác nhận S01 từ Orders, S02 từ Invoices, C01/C02 từ order header. Bổ sung distinct document membership/semi-join khi filter Product; không cộng distinct từng product; C02 Product chưa có policy nên không công bố biến thể | Specification, Marts; K01/K10/K11 hiện có; PASS — logical |
| C — Customer roles | Siết customer_role trong mart_customer_sales: đúng một BUYER/BILL_TO; thiếu/multi-role không trả enterprise SUM. Enterprise tổng chỉ tính một lần từ invoice fact/sales daily hoặc BUYER branch | Marts, BRD-08, K12; PASS — logical |
| D — Current Inventory | Tách observed_at (observation) và published_at (target publication). Product SK thuộc cùng published_state_id, không latest-at-query; republish/rekey theo policy sau; không daily history | Dictionary, Mapping, Diagram, Marts, Change Impact; PASS — logical |
| E — Dependencies/precision | Bổ sung hai phương án contract extension/controlled mapping cho TransactionTypes; cả hai Pending Approval. Xác nhận 100ns vs microsecond từ tài liệu engine, mô tả loss/ties/sentinel và decimal scale/rounding tests; không chốt physical types | Mapping có nguồn chính thức và metadata evidence cũ; PASS — design requirement |

Không khảo sát lại Phase 1.1–1.5, không truy vấn database trong vòng targeted review. Đã đối chiếu KPI Catalog/BRD/Source Contracts và SQL evidence hiện có; chỉ bổ sung kiểm chứng capability từ tài liệu engine chính thức. Chưa chạy conversion/runtime tests hoặc render Mermaid bằng công cụ mới. Sửa làm rõ contract, không đổi bốn facts/dimensions, hai headers, sáu marts hoặc business scope.

## Rủi ro và Open Decisions chuyển các task sau

| ID / vấn đề | Phương án/khuyến nghị để review | Gate / tác động |
| --- | --- | --- |
| OD-DW-01 — validity/source history | Giữ system-time riêng; chỉ map business validity khi có evidence; forward tracking từ observation đã kiểm | DW-02; rekey/historical grouping |
| OD-DW-02 — SCD attributes/SK stability | Chọn thuộc tính thực sự phục vụ analytics; stable NK, version SK strategy, rebuild mapping; không copy mọi archive row thành version DW | DW-02; versions/count/reproducibility |
| OD-DW-03 — Unknown/gap/date-only lookup | So sánh unknown chung, inferred NK, pending publication; không chọn earliest/latest tùy ý; giữ lookup status | DW-02; late dimensions/history coverage |
| OD-DW-04 — references ngoài chín bảng | TransactionTypes tối thiểu cho movement type; labels category/package/colors optional; cần contract/approval riêng | Trước ingestion liên quan; không tự mở source scope |
| OD-DW-05 — full extraction/physical representation | Multi-table consistency, datetime2(7), decimal quantity/amount, calendar range/currency metadata | DW-03A; tránh mất precision và false reconciliation |
| OD-DW-06 — watermark/delete | Timestamp+PK/window chỉ candidates; prove update/delete trên test độc lập, source gốc read-only | DW-03B; không bỏ sót/nhầm missing key |
| OD-DW-07 — publication/recovery | Affected key/group cũ+mới, complete state, same-run ratio, restatement/rebuild equivalence | DW-03C; tránh stale marts/double apply |
| OD-DW-08 — semantic grain/filter | Hai role tách; product invoice counts non-additive; quarterly repeat tính từ header; chốt physical marts và report filters sau review | DW-04 và trước mart |

Tất cả OD trên **Pending Approval**; DW-01 không thực hiện các thiết kế DW-02/DW-03 chi tiết. Header intermediates, mart grain/NK-version distinction và reference boundaries đã qua targeted review. Đầu vào đủ để Owner giao DW-02; DW-02 vẫn TODO và chưa được thực hiện. WWI-04 chỉ đóng sau DW-04 được nghiệm thu; không tự chuyển phase.
