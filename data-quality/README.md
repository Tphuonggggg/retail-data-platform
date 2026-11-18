# data-quality

## 1. Overview
Module **chất lượng và đối soát WWI → PostgreSQL**. Status: Not Implemented. Not implemented yet.

## 2. Purpose
Kiểm tra validation, business rules và reconciliation nguồn–đích.

## 3. Scope
Sales/Invoicing trước; Customer và Inventory Movements theo thứ tự MVP. Kiểm tra cơ bản bắt đầu từ Phase 3–4; Phase 6 tập trung gates và failure nâng cao.

## 4. Responsibilities
Sở hữu quy tắc kiểm tra, kết quả test/sai lệch và quarantine reason; không sửa dữ liệu WWI nguồn âm thầm.

## 5. Inputs
Source contract, raw/staging/warehouse, KPI và ngưỡng đã duyệt.

## 6. Outputs
Validation results, quarantine reasons, reconciliation và quality gate status.

## 7. Dependencies
data-sources, ingestion, storage, transformation và docs/requirements.

## 8. Technology Stack
pytest, dbt tests, custom SQL validation theo phase được duyệt.

## 9. Directory Structure
- [validations/](README.md)
- [reconciliation/](README.md)

## 10. Planned Workflow
Kiểm tra trong ingestion/staging → kiểm tra dbt/warehouse → đối soát cùng grain/kỳ → Phase 6 gates/monitoring tập trung. Chưa có lệnh chạy.

## 11. Development Tasks
WWI-06/08 cho kiểm tra cơ bản; WWI-10 cho gates và failure nâng cao. Theo dõi [TASKS.md](../TASKS.md).

## 12. Testing Strategy
Khóa, null, relationships, duplicate, lệch count/amount/quantity và sai KPI theo hợp đồng đã duyệt.

## 13. Acceptance Criteria
Sai lệch thử nghiệm được phát hiện và báo lý do rõ; ngưỡng chặn batch do owner duyệt.

## 14. Current Status
Chưa có validation/reconciliation code hoặc kết quả kiểm thử. Not implemented yet.

## MVP-RESET-01 consolidation

Future-only submodule READMEs ?? h?p nh?t v? ??y; ch?a c? implementation trong c?c th? m?c k? ho?ch ??. Xem [roadmap](../ROADMAP.md). Kh?ng t?o placeholder code; t?o module con khi c? task tri?n khai th?c t?.
