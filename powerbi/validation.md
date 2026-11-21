# POWERBI-SALES-01 — validation và blockers

**POWERBI_SALES_PARTIAL — 2026-11-21. Không đạt Definition of Done của dashboard.**

## Evidence thực tế

| Check | Status / evidence |
|---|---|
| Git baseline | refactor/mvp-simplification, 9ae4f702c18150dc4b7dafe33280984907953d9c; chỉ Owner PBIX mới chưa track |
| Original PBIX và backup SHA256 bằng nhau | PASS; [inspection](original-inspection.json), original 31612480 bytes |
| Desktop | 2.159.1231.0, mở được original working copy và generated PBIP; project reopen/reload thành công |
| Source authentication và version | PASS, retail_bi_reader/retail_raw; all12 đúng c825b18e |
| SQL insight và schema/key checks | PASS; [reader-only results](sql-validation.json), [queries](validation.sql), [runner](validate_sql.py) |
| PBIR metadata | PASS: Microsoft CLI0.5.0, 4 pages,0 errors/0 warnings; không chứng minh data correctness |
| TMSL/TOM | PASS deserialize và Desktop model load; 14 tables/9 relationships/77 measures |
| Offline BI structural tests | 7 PASS: source scope, no embedded rows/secrets, relationship directions/keys, types, measures, bindings/nav destinations |
| Final repository QA | 188 offline tests PASS; Markdown links/Python/PowerShell syntax, secret/scope checks PASS; [artifact summary](artifact-validation.json) |
| Desktop Import/refresh | BLOCKED: external TOM Full refresh không hoàn tất. Initial native identity query chưa được duyệt; đã bỏ query phụ. Navigation-only và private snapshot bootstrap API attempts cũng timeout; không ghi Import PASS |
| Actual DAX baseline | BLOCKED_MODEL_HAS_NO_IMPORTED_DATA; [actual engine result](dax-runtime-results.json) trả BLANK, không khớpSQL; stopped trước14 contexts còn lại |
| SQL-vs-DAX, filtered contexts | NOT RUN / BLOCKED; [15 test queries](dax-validation-queries.json) đã chuẩn bị |
| Four screenshot captures | PASS capture4/4 qua Desktop bridge, nhưng đều PRE_REFRESH / NOT ACCEPTED; xem bên dưới |
| Interactive navigation/slicers | Definitions và page targets hợp lệ; thao tác click/filter chưa VERIFIED |
| Warning fields | VERIFIED có source_reported_line_profit, eligibility và Product/date keys trong approved fact; không cần DQ access |
| Backorder references | BLOCKED: missing BackorderOrderID trong BI allowlist; proposal chưa triển khai |
| Raw/DW/capture/publication preservation | PASS, [44-table audit](warehouse-preservation.json); no ingestion/dbt build/publish |
| Data/model performance | NOT MEASURED ở model có data; không dùng SQL read time làm Desktop refresh performance |

SQL verified headline: Sales172261341.20; Tax25782098.25; IncludingTax198043439.45; Units8950628; Invoices70510; Orders73595. Không đưa các constants này vào report expressions. Source currency chưa xác nhận; không gắn USD/BRL/VND.

## Screenshots — bằng chứng chưa hoàn tất, không là ảnh dashboard đã nghiệm thu

- [01 Sales Performance](qa/01%20_%20Sales%20Performance.png).
- [02 Product Contribution](qa/02%20_%20Product%20Contribution.png).
- [03 Sales Attribution](qa/03%20_%20Sales%20Attribution.png).
- [04 Exceptions & Coverage](qa/04%20_%20Exceptions%20&%20Coverage.png).

Desktop báo thiếu/no data, cards BLANK. Phát hiện qua ảnh và đã sửa trong definitions: button text visibility, duplicate card labels, textbox height, product slicer clipping, friendly matrix labels; cumulative concentration thêm empty-population guard. Chưa kiểm chứng layout đầy đủ khi có data hoặc trục/rank nhiều categories. Banners/auto-recovery đến từ app runtime; không sửa security/privacy settings để che chúng.

Visual cumulative concentration trên trang Attribution vẫn có `Error fetching data` ở lần capture này. Chưa có bằng chứng đủ để khẳng định nguyên nhân chỉ là thiếu data; phải chẩn đoán lại query/visual sau refresh. Đây là một acceptance failure còn mở, không được che bằng ảnh/chart giả. Các slicer defaults cuối (2016 ở Performance, Buyer ở role detail, TopN10) đã ghi vào definitions nhưng chưa capture/kiểm thử lại sau cùng vì Desktop báo unsaved state; không ghi đè state đó.

Truy vấn chỉ đọc riêng trên **cache của bản gốc** xác minh1247 Date/227 Product/663 Customer/228265 InvoiceLines/231412 OrderLines, đúng c825b18e. [Kết quả](original-cache-dax.json) cho Sales172261341.20000011, Tax25782098.250000063, IncludingTax198043439.45000017 do các money columns gốc là double. Chỉ khớp SQL ở mức hiển thị hai chữ số, không phải exact-money PASS và không thay thế kiểm thử model mới. Vì vậy model mới khai báo fixed decimal; hiệu quả runtime của thay đổi này vẫn phải kiểm sau Import.

## Recovery và bảo toàn

Original PBIX không bị overwrite. Chỉ instance generated project do agent mở đã được khởi động lại sau API processing bị treo; chưa có imported data để mất. Original working-copy instance và original file được giữ. Generated on-disk partitions đã khôi phục PostgreSQL navigation, không có embedded source snapshots. Thử bootstrap Import chỉ dùng source SELECT bằng reader; extract/experimental scripts giữ trong ignored `.local`, không commit hoặc dùng như production path.

Private profile ban đầu sai JSON; sửa cú pháp không đổi giá trị mật khẩu. PostgreSQL từ chối giá trị đó; sau **Owner explicit approval**, đồng bộ password riêng retail_bi_reader qua psql password prompt không echo và login PASS. Không đổi grants/roles khác/dữ liệu/schema. Mật khẩu không được đưa vào report, SQL, logs hay Git.

Auditor dùng existing read-only ingestion/transform connections **chỉ để content fingerprints/preservation**, không làm BI data source hoặc bypass BI permissions. Tất cả analytical SQL và source snapshot lấy qua retail_bi_reader. Raw17 + metadata8 + warehouse19 table contents và publication/capture/version records không đổi so với accepted baseline.

## Tiếp tục sau khi Desktop refresh thành công

```powershell
.\.venv\Scripts\python.exe -X utf8 powerbi/validate_sql.py
# Chọn PID của đúng Desktop project, không dùng PID của original working copy:
& powerbi/query_model.ps1 -DesktopPid <actual-project-pid>
```

So exact money/counts theo cùng version/date/customer-role/Product; AIV/growth so ratios với tolerance1e-12 theo contract. So monthly/product/customer groups, không chỉ headline. Khi bất kỳ check sai: giữ task IN_PROGRESS, sửa rồi chạy lại evidence tương ứng. Chỉ báo POWERBI_SALES_DASHBOARD_ACCEPTED sau full runtime/chart/interaction/save-reopen acceptance. SALES-04 và parent phases chưa đóng.
