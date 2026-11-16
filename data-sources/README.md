# data-sources

## 1. Overview

Module **WWI OLTP source contract**. Database `WideWorldImporters` trên SQL Server local là nguồn chính, truy cập **chỉ đọc**. Status của module trong repository: Not Implemented. Not implemented yet.

## 2. Purpose

Xác định ranh giới nguồn, quyền truy cập, bảng/cột/khóa và metadata cần cho ingestion. Không sở hữu business transformation hoặc warehouse.

## 3. Scope

MVP theo thứ tự Sales/Invoicing, Customer Analytics, Inventory Movements. Purchasing và Finance là extensions chỉ khi được phê duyệt.

## 4. Responsibilities

WWI-02 tạo source contract và data dictionary có bằng chứng metadata. Phase 1.1 đã khảo sát trực tiếp chín bảng MVP, gồm `Sales.Orders`, `Sales.OrderLines`, `Sales.Invoices`, `Sales.InvoiceLines`, `Sales.Customers`, `Sales.CustomerTransactions`, `Warehouse.StockItems`, `Warehouse.StockItemHoldings` và `Warehouse.StockItemTransactions`. Phase 1.2 đã kiểm tra dữ liệu hiện hành và hai archive temporal; Phase 1.3 đã ghi quan hệ nguồn. Xem [metadata dictionary](../docs/data-models/wwi-metadata-dictionary.md), [relationship contract](../docs/data-models/wwi-source-relationships.md) và [Phase 1.4 source contracts](../docs/data-models/wwi-source-contracts.md). Phase 1.4 và WWI-02 đã được nghiệm thu ở mức source design; hợp đồng triển khai và runtime: Not implemented yet.

## 5. Inputs

Database WWI local và quyền đọc được cấp riêng; không lưu credentials trong repository.

## 6. Outputs

Source contracts cho ingestion: grain, PK/FK, timestamps, nullable fields, temporal coverage, exception rules và phạm vi full/incremental được duyệt.

## 7. Dependencies

[Scope](../PROJECT_SCOPE.md), WWI-02/03/04, infrastructure cho kết nối an toàn. Không có source generator dependency.

## 8. Technology Stack

SQL Server là nguồn OLTP; Python/SQL sẽ đọc theo contract khi triển khai. PostgreSQL là đích của ingestion/warehouse, không phải nguồn WWI.

## 9. Directory Structure

README điều hướng và[security/](security/README.md) chứa prepared DBA setup/read-only verify scripts;không migration/auto-run. WWI data vẫn ngoàiGit trongSQLServer,không CSV/backup/extract mới.

## 10. Planned Workflow

Xác minh metadata bằng truy vấn chỉ đọc → đề xuất contract → owner review → ingestion ở phase được cho phép. Không có lệnh chạy module trong repository.

## 11. Development Tasks

WWI-02 source contract, WWI-05 kết nối, WWI-06/07 ingestion. Theo dõi [TASKS.md](../TASKS.md).

## 12. Testing Strategy

Kiểm tra schema/keys/quan hệ và quyền đọc; về sau kiểm tra extraction count, watermark và reconciliation. Không sửa dữ liệu WWI gốc.

## 13. Acceptance Criteria

Contract đúng bảng/cột/grain đã kiểm chứng; quyền đọc tối thiểu và không đưa dữ liệu/secret nguồn vào repository.

## 14. Current Status

Source contracts/WWI-02 đã nghiệm thu ở mức tài liệu. M1A secure developer SQL connection/11 bounded reads PASS, nhưng current identity sysadmin không phù hợp extraction; approved least-privilege profile và source consistency proof còn blocked. [Secure Contract](../docs/architecture/wwi-secure-connection-contract.md), [Evidence](../docs/architecture/wwi-m1a-gate-evidence.md), [Handoff](../docs/architecture/wwi-m1a-handoff.md). Không source write/config/identity changes; production adapter/pipeline Not implemented yet.


## M1B — Source identity và consistency proposals

[Identity](../docs/architecture/wwi-source-identity-proposal.md), [Consistency](../docs/architecture/wwi-source-consistency-proposal.md), [DBA/Owner actions](../docs/architecture/wwi-source-dba-owner-checklist.md), [Assessment](../docs/architecture/wwi-m1b-assessment.md) ghi required per-object privileges/current+H,metadata/TLS limits,safe negative tests và A/B proof plans. Chỉ review/metadata,không tạo/sửa identities/grants. M1B planning DONE sau QA,method/identity PROPOSED và G01/G02 vẫn BLOCKED; production adapter Not implemented yet.


## M1B-Approval — prepared source-security artifacts

[OD01–03](../docs/architecture/wwi-m1b-owner-decisions.md) approve direction/preferredA vàpreparation only. [Setup/verify README](security/README.md) mô tảguards/placeholder inputs/no automation/manual future authorization;[EX01–04](../docs/architecture/wwi-source-dba-owner-checklist.md#6-compact-execution-authorization-request--ready-for-review-not-authorized) cầnOwner/DBA review trướcWindows/SQL/window/runtime actions. Scripts NOT RUN,production adapter Not implemented yet,G01/G02 Pending/BLOCKED.
