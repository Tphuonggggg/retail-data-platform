# POWERBI-ACCESS-02 — dbt grants bền vững

**POWERBI_PERSISTENT_GRANTS_ACCEPTED — 2026-11-21.** Owner cho phép cấu hình grants và một lần controlled rebuild đúng 12 models. Kết quả runtime không đồng nghĩa nghiệm thu report Power BI hoặc Certified publication.

## Cấu hình và quyền thực thi

Đã thêm `+grants: {select: [retail_bi_reader]}` vào từng tên model trong [dbt_project.yml](../dbt/dbt_project.yml): 5 core, 2 intermediate headers, 5 marts đúng [allowlist kết nối](access.md#objects-power-bi-được-đọc). Không grants ở project/folder level, không default privileges, không đổi SQL, measures, business rules, grain, schema hoặc materialization.

Trước và sau: cả 12 objects do `retail_transform` sở hữu. dbt chạy bằng role này trên đúng `127.0.0.1:55434/retail_raw`, container `retail-raw-postgres-1`; không dùng `postgres`, không cần GRANT/DDL admin bổ sung. Quyền CONNECT/schema USAGE và role settings đã có từ ACCESS-01 được giữ nguyên. Dependencies: dbt-core **1.11.17**, dbt-postgres **1.11.0**, psycopg **3.3.9**.

Cú pháp model-level theo [dbt grants documentation](https://docs.getdbt.com/reference/resource-configs/grants); installed table/view materializations gọi `apply_grants` sau khi thay relation và trước commit. Runtime OID thay đổi trên cả 12 objects nhưng SELECT vẫn hoạt động là bằng chứng grants được áp dụng lại, không chỉ đọc cấu hình.

## Kết quả kiểm chứng

[Evidence đầy đủ](persistent-grants-verification.json) chứa commands, invocation IDs, manifest grants, từng dbt result, metrics, counts/digests, reader privileges và catalog fingerprints trước/sau.

| Tiêu chí | Kết quả |
|---|---|
| Compile trên explicit INCREMENTAL version `c825b18e-fc62-4cf1-8837-b37b4c9f9668` | PASS; 17,741s runner wall |
| Manifest 21 models, chỉ đúng 12 configs SELECT cho retail_bi_reader | PASS |
| Controlled build: đúng 10 tables + 2 views, không chọn dependency expansion | PASS; 21,798s runner wall |
| Tests trong build | 39 PASS + 12 model results + 1 hook = 52 successful results |
| Chạy riêng các tests liên quan, indirect selection cautious | 39 PASS + 1 hook = 40 successful results; 13,342s runner wall |
| Login/SELECT bằng reader mới, trước và sau | 12/12 PASS, đúng version; không quyền DML/DDL |
| Không SELECT/USAGE trên Raw, staging, DQ, metadata/test | PASS |
| Counts và content digests 19 warehouse tables + 2 header views | Không đổi |
| 17 Raw + 8 metadata tables, gồm checkpoint/capture/version/publication state | Không đổi |
| OID đổi đúng 12 objects; owner và loại table/view giữ nguyên | PASS |
| Catalog ngoài phạm vi (1.880 objects), bao gồm test fixtures | Count và SHA256 không đổi |
| Offline regression | 181 tests PASS; có 4 tests mới bảo vệ grants/selector scope |

Các tests đòi parent ngoài 12 models không được chọn gián tiếp bởi `cautious`; không tuyên bố chạy lại toàn bộ 69 dbt tests. Dữ liệu staging/DQ và source inputs được đọc làm dependencies, không được rebuild. Tests không lưu failures thành bảng.

| KPI | Trước = sau |
|---|---:|
| Invoiced Sales Before Tax | 172261341.20 |
| Invoice Tax Amount | 25782098.25 |
| Invoice Amount Including Tax | 198043439.45 |
| Source Units Sold | 8950628 |
| Invoice Count | 70510 |
| Order Count | 73595 |
| AIV before tax | 2443.0767437242944263 |

Headline được tính từ facts/header populations theo approved Q01, đối chiếu Sales/Units với daily, monthly, product và customer marts riêng từng grain. Không join fact-to-fact, không cộng hai customer roles. Ruleset/measure hashes và toàn bộ model/config/macro file hashes không đổi. Khoảng InvoiceDate: 2013-01-01 đến 2016-05-31.

## Tái lập và phạm vi

[Acceptance runner](../dbt/bi_grants_acceptance.py) tự snapshot chỉ đọc → compile → kiểm manifest → build đúng 12 → test → snapshot và đối soát. Lệnh sau **có rebuild 12 models**, chỉ dùng khi có authorization tương ứng:

```powershell
.\.venv\Scripts\python.exe -X utf8 dbt/bi_grants_acceptance.py --execute
```

Runner giữ ingestion advisory lock `941061` suốt phép thử; dbt runner giữ transformation lock `941062` mỗi invocation. `--select` chỉ nhận 12 tên tường minh, không `+`, wildcard hoặc model ngoài allowlist; default CLI cũ không đổi. Version truyền explicit, không dùng latest hoặc publication pointer. Logs/manifest/compiled artifacts giữ private trong `.local`; tracked evidence chỉ gồm aggregates/metadata, không credentials.

Một lượt preflight ban đầu của acceptance harness đã dừng trước mọi dbt command vì kiểm tra nhầm cột Tax trên marts không cung cấp Tax. Đã sửa harness chỉ đối soát Sales/Units ở các marts đó; Tax/Including Tax kiểm tại headline và content digests. Failure record giữ private; không có DDL nào từ lượt dừng này. Không sửa model để chiều test.

Giữ hạn chế development/unpublished, source consistency UNVERIFIED; không atomic multi-model serving publication. Role có read-only default, nhưng effective grants mới là giới hạn ghi. Không thay SQL Server, không chạy ingestion/checkpoint advance/publish, không dựng Power BI report, không đóng parent phases. Future model ngoài allowlist không tự nhận grants. Nếu future thay ownership hoặc schema/role, cần review quyền riêng.

Commit local của task này bao gồm prerequisite ACCESS-01 đã kiểm chứng nhưng còn uncommitted khi bắt đầu, cùng cấu hình/QA/evidence ACCESS-02; không discard thay đổi cũ và không push/merge.

Sau khi runtime acceptance hoàn tất, Owner xác nhận đang chỉnh private profile `.local/powerbi/connection.json`; file tại lần QA cuối không còn JSON hợp lệ. Không tự ghi đè profile hoặc đặt lại mật khẩu database. Chỉ sửa file không thay PostgreSQL password; Owner cần hoàn tất JSON hợp lệ và dùng đúng mật khẩu đã provision trước lần kết nối tiếp theo. Evidence phản ánh kết nối reader thật trước/sau rebuild tại thời điểm thử nghiệm, không khẳng định private profile đang được chỉnh đã sẵn sàng dùng. Private profile không thuộc commit.
