# dbt — Transformation, Core DW và Data Marts

Sở hữu [project configuration](dbt_project.yml), models staging/intermediate/core/marts, macros và dbt data tests. Seeds/snapshots chỉ thêm khi triển khai thực tế.

**DW-IMPLEMENT-01 draft được bảo toàn từ working tree trước REPO-STRUCTURE-02.** Có 18 SQL models và test nháp; chưa hoàn tất tests/reconciliation, chưa có dbt debug/compile/run/test PASS. Không dùng như warehouse đã nghiệm thu. Refactor chỉ di chuyển và sửa paths; không thẩm định/phê duyệt thêm business/SCD/key policies trong draft.

[run_dbt.py](run_dbt.py) nay dùng project root dbt; profiles/credentials dự kiến ở .local/dbt ngoài Git. Explicit capture ID, không implicit latest/publication views. Historical SCD2/registry theo [thiết kế đã duyệt](../docs/data-models/wwi-final-scd2-design-specification.md), chưa triển khai; key/lookup draft phải review khi tiếp tục DW-IMPLEMENT-01.

[Provisioning SQL nháp](../infrastructure/postgres/warehouse/provision.sql) và [entrypoint](../infrastructure/scripts/provision_warehouse.py) thuộc infrastructure; không tự gọi bởi dbt. Lần thử trước refactor chỉ báo OperationalError, chưa có bằng chứng provision thành công. Task này không chạy lại hoặc sửa logic.

Dependencies ở [root requirements](../requirements.txt). Raw DDL thuộc infrastructure; marts SQL thuộc dbt; report assets thuộc [powerbi](../powerbi/README.md). [KPI definitions](../docs/requirements/kpi-definitions/README.md) giữ nguyên.

REPO-STRUCTURE-02 xác nhận 23 files project nháp (models/macros/tests/config) và provisioning SQL giữ nguyên SHA256 so với trước di chuyển; chỉ runner/provisioning Python đổi import/root/path. Không coi syntax check là dbt compile hoặc business acceptance.
