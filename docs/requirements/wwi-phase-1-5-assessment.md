# Phase 1.5 Assessment — WWI Business Requirements & KPI Definitions

**Trạng thái: Phase 1.5 hoàn tất ở mức tài liệu; WWI-03 `DONE` theo phê duyệt BRD-01–BRD-12 của Project Owner ngày 2026-11-14.** Phase 1 vẫn `In Progress`; Phase 1.6/WWI-04 chưa bắt đầu. K01–K09 là truy vấn `SELECT` read-only trước phê duyệt; K10–K13 chạy ngày 2026-11-14. Không thay đổi SQL Server/PostgreSQL, không tạo schema/pipeline/dbt/Airflow/Power BI. Source arithmetic không xác nhận accounting semantics hoặc runtime KPI.

## Executive summary

**Verified source arithmetic:** 73.595 orders, 70.510 invoices; tổng InvoiceLines.ExtendedPrice 198.043.439,45, TaxAmount 25.782.098,25; 70.510/70.510 invoice đối soát amount với type 1 CustomerTransactions ở `InvoiceID`; type 3 payments có 26.637 `InvoiceID` NULL. 663 buyer có order toàn snapshot; movement/holdings tổng hợp được theo source type/current state. Những con số này **không là KPI đã được phê duyệt**.

**Approved business scope:** 22 KPI IDs giữ nguyên: 12 MVP Core, 5 MVP Optional, 2 Deferred, 3 Not Supported by Current Evidence. BRD-01–BRD-12 được duyệt, gồm quyết định hoãn/loại khỏi MVP. Recognized Revenue, AOV, official Gross Profit/COGS, refund, daily inventory balance, stockout risk và invoice-level payment allocation không là KPI MVP. Purchasing/Finance chuyên sâu ngoài MVP.

**Verified source SQL sau phê duyệt:** K10 S06 = 172.261.341,20 / 70.510 = **2.443,08** tiền nguồn/invoice, 0 invoice thiếu line. K11: 41 tháng có order, 23.871 lượt buyer-tháng, 19.134 lượt repeat buyer-tháng (không là tỷ lệ gộp). K12: tổng trước thuế của invoice, phân bố buyer và bill-to đều 172.261.341,20, tương ứng 663/263 nhóm. K13: 228.265 lines, LineProfit nguồn 85.729.180,90, 4.626 lines âm. SQL là bằng chứng đọc nguồn, không phải warehouse test.

## Deliverables

1. [Business Requirements](wwi-business-requirements.md): mục tiêu, entities, data creation flow, use cases, KPI candidates và giới hạn ba subject areas.
2. [Business Questions & Use Cases](wwi-business-questions-use-cases.md): câu hỏi, grain, candidate và quyết định cần thêm.
3. [KPI Catalog](../../analytics/kpi-definitions/wwi-kpi-candidate-catalog.md): 22 ID, phân loại Core/Optional/Deferred/Unsupported, công thức, source/grain/date/filter/unit/aggregation, DQ/reconciliation và trạng thái duyệt.
4. [KPI Verification SQL](../../analytics/kpi-definitions/wwi-kpi-verification-sql.md): K01–K13, `SELECT` riêng grain và kết quả đã chạy.
5. [Business Rules & Decision Matrix](wwi-business-rules-decision-matrix.md): BRD-01–BRD-12, phương án, evidence, quyết định và trạng thái Approved.

## Acceptance checklist

| Tiêu chí | Bằng chứng | Đánh giá |
| --- | --- | --- |
| Ba subject areas MVP | Business Requirements BR-S/BR-C/BR-I và Business Questions | PASS — tài liệu |
| KPI có định nghĩa/công thức/nguồn/grain/time/filter/unit | 22 mục catalog S01–S10, C01–C05, I01–I07; 12 Core, 5 Optional, 2 Deferred, 3 Unsupported | PASS — business scope approved; runtime pending |
| Kết quả tính toán có SQL evidence | Verification K01–K13 và Phase 1.2/1.3 SQL; K10–K13 chạy 2026-11-14 | PASS — source arithmetic |
| Customer buyer/bill-to tách role | C03/C04, BRD-08, K05: 663 vs 263 groups | PASS — nguồn |
| Revenue/payment không cộng trùng | S03, K03 và BRD-04/10; transaction type 1 chỉ đối soát | PASS — tài liệu |
| Không suy tồn kho lịch sử | I04 current only; I06/I07 Not supported, BRD-11/12 | PASS — tài liệu |
| KPI thiếu hỗ trợ được đánh dấu | S10, I06, I07 Unsupported; S07/S08 Deferred; S09 optional source measure, official Gross Profit deferred | PASS — tài liệu |
| Business decisions được Owner duyệt | 12 BRD ghi rõ approved business rule hoặc approved exclusion/deferment | PASS — owner instruction và matrix |
| Tử/mẫu và role tránh nhầm lẫn | S06 trước thuế không là AOV; C02 theo tháng; C03 buyer/C04 bill-to; S09 không là official Gross Profit | PASS — catalog và K10–K13 |
| Tài liệu nhất quán Source Contracts | Nguồn/grain/FK/nullable đối chiếu WWI-02 | PASS — review tài liệu |
| Links, Git diff và secret | 81 Markdown files, 302 liên kết nội bộ/0 gãy; Git status 16 Markdown files đúng phạm vi, 0 secret pattern/0 trailing whitespace; `git diff --check` sạch | PASS — QA trước commit |

**Giới hạn:** `PASS` là nghiệm thu tài liệu/định nghĩa nghiệp vụ và phép tính nguồn, không chứng minh SQL trong warehouse, fact/mart, pipeline hoặc dashboard đã hoạt động. Công thức được duyệt là quy ước báo cáo dự án, không là xác nhận accounting semantics. WWI-03 có thể `DONE` ở scope tài liệu theo acceptance criteria trong TASKS.md; Phase 1 còn mở.

## Open technical decisions cho WWI-04 và readiness Phase 1.6

WWI-04 cần proposal và approval riêng cho incremental watermark/tie-breaker, delete/replay, môi trường test INSERT/UPDATE độc lập; SCD2 attributes/validity/as-of/độ phủ temporal; quality thresholds và restatement. Trước fact/mart cần duyệt physical grain/schema/source-to-target mapping và kiểm tra precision/rounding, kỳ/filter, credit note tương lai. Phạm vi nghiệp vụ đủ làm đầu vào phân tích Phase 1.6 nhưng **chưa cho phép bắt đầu Phase 1.6**, chưa đủ điều kiện triển khai warehouse hay tuyên bố KPI runtime verified.
