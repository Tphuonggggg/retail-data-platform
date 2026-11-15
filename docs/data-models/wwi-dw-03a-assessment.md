# WWI DW-03A — Proposal & Technical Evidence Assessment

**IN_PROGRESS — Owner Logical Approval Milestone, 2026-11-15.** Section 11 là current assessment: A01/A03/A04/A06 Approved — Logical Policy; A02 Approved — Conditional Logical Policy; A05 Approved — PoC Direction Only. **Sections 1–10 là hồ sơ lịch sử trước approval**, gồm partial SQL evidence và QA ở từng vòng; không dùng các câu “A01–A06 Proposed/chưa approved” cũ làm trạng thái hiện hành. B9 Pending Physical Approval; B1–B8/accepted DW-02 giữ nguyên. Final DW-03A acceptance **NOT PERFORMED**; runtime **Not implemented yet**.

## 1. Stage 1 baseline và tài liệu đã khảo sát

Branch `main`, HEAD **`eeb22c224e767059581c3b10a3bb3f5d1f1cc0fb`**, message `docs: finalize WWI SCD2 design policies`; initial `git status --short` rỗng. Không có pre-existing changes hoặc staged files. SHA-256 snapshot đầu task có 108 tracked files; không lưu source dataset/credentials.

Đã đối chiếu AGENTS/scope/roadmap/tasks/README/changelog, inventory/profiling/dictionary/contracts, extraction/raw/validation matrices, business requirements/KPI, DW-01, Final DW-02/E assessment/handoff và sáu SCD ADRs. Existing ingestion/storage/raw/staging/infrastructure READMEs xác nhận **Not implemented yet**, driver/connector chưa chọn. Đã tìm paths bằng `rg --files`; bốn DW-03A deliverables chưa có, không tài liệu trùng chức năng.

Nguồn hiện hành: [Source Contracts](wwi-source-contracts.md), [Metadata Dictionary](wwi-metadata-dictionary.md), [Profiling](wwi-data-profiling.md), [Extraction Requirements](wwi-extraction-requirements-matrix.md), [Raw Requirements](../requirements/wwi-raw-layer-requirements.md), [Validation Matrix](../requirements/wwi-source-validation-matrix.md), [DW-02](wwi-final-scd2-design-specification.md), [ADR index](../adr/README.md). Verified historical source counts không là immutable load expectations.

## 2. Stage 1 — Completed discovery / Proposed / Missing evidence (lịch sử)

| Loại | Kết quả | Giới hạn |
| --- | --- | --- |
| Completed document discovery | Chín current tables phân loại O/T/S, hai associated physical archives H; kiểu dữ liệu đặc biệt, counts và temporal identity evidence | Dùng source metadata/profiles đã verified 2026-11-07/14, không refresh live counts |
| Completed architecture analysis | Source consistency alternatives, Raw R1–R4, metadata/retry, temporal P1–P5 và publication proposal | Analysis hoàn tất cho Stage 1, không acceptance hoặc implementation |
| Proposed decisions | A01–A06 trong [Decision Register](wwi-dw-03a-decision-register.md) | Tất cả PROPOSED — PENDING PROJECT OWNER APPROVAL |
| Verified mathematical illustration | V1 ticks 639303428961234567; V2 +1 tick; sentinel 3155378975999999999 trong signed bigint range | Local integer/date arithmetic, synthetic example; không SQL cast/driver/PG round-trip |
| Missing source evidence | Current isolation state/RCSI/read-only flags, permissions current/H, writer activity, workload/resource limits | Metadata connection attempt FAILED trước query result |
| Missing implementation evidence | Driver/target versions/config, serialization/type fidelity, chunk/load performance, recovery/atomic visibility | Chưa chọn/triển khai/chạy PoC |
| Final design acceptance | NOT PERFORMED | Chỉ đánh giá completeness/consistency của proposal để Owner review |
| Runtime execution | NOT RUN | Existing CD-T01–21 giữ NOT RUN; không tạo test DB hoặc DML |

## 3. Read-only metadata inspection attempt — FAILED / không có result

Đã phát hiện `SQLCMD.EXE` hiện có và thử integrated-auth connection tới instance/database đã ghi trong inventory. Lệnh:

```powershell
sqlcmd -S '.\SQLEXPRESS' -d WideWorldImporters -E -l 5 -t 15 -b -W -s '|' -Q $metadataQuery
```

Query được chuẩn bị chỉ gồm hai SELECT metadata dưới đây; **kết nối thất bại trước khi trả bất kỳ row nào**:

```sql
SELECT DB_NAME() AS database_name,
       CAST(SERVERPROPERTY('ProductVersion') AS nvarchar(128)) AS product_version,
       CAST(SERVERPROPERTY('Edition') AS nvarchar(128)) AS edition,
       snapshot_isolation_state_desc, is_read_committed_snapshot_on,
       is_read_only, state_desc, SYSUTCDATETIME() AS observed_at_utc
FROM sys.databases WHERE database_id = DB_ID();

SELECT s.name AS schema_name, t.name AS table_name, t.temporal_type_desc,
       HAS_PERMS_BY_NAME(s.name + '.' + t.name, 'OBJECT', 'SELECT') AS can_select
FROM sys.tables AS t JOIN sys.schemas AS s ON s.schema_id = t.schema_id
WHERE (s.name = 'Sales' AND t.name IN
       ('Customers','Customers_Archive','Orders','OrderLines','Invoices','InvoiceLines','CustomerTransactions'))
   OR (s.name = 'Warehouse' AND t.name IN
       ('StockItems','StockItems_Archive','StockItemHoldings','StockItemTransactions'))
ORDER BY s.name, t.name;
```

Observed error: `Microsoft ODBC Driver 18 for SQL Server : SSL Provider: The certificate chain was issued by an authority that is not trusted` và `Client unable to establish connection`. Không có SELECT evidence về flags/permissions, không có database counts mới. Không đổi TLS/trust store/database/isolation, không retry bằng certificate bypass. Driver được nêu trong error không là connector được duyệt cho pipeline hoặc compatibility test. Cần trusted connection configuration/approval phù hợp trước metadata recheck ở task sau; Stage 1 vẫn có thể bàn giao conditional proposal trung thực.

## 4. Proposal completeness review — không final design acceptance

| Requirement | Deliverable/evidence | Stage 1 review |
| --- | --- | --- |
| A1 chín sources + current/history/snapshot | [Proposal](wwi-dw-03a-full-raw-design-proposal.md) section 2, nine-row matrix + two H dependencies | Đã phân tích; archive/projection/type adapter approval pending |
| A2 source consistency alternatives | Proposal section 3, C1–C5 + rejected shortcuts | Đã phân tích; actual flags/permissions Unverified |
| A3 Raw architectures/keys/retention/incremental interface | Proposal section 4, R1–R4 và conceptual objects | Đã đề xuất R1, chưa chọn physical tables hoặc retention |
| A4 batch/lineage/idempotency/failure stages | Proposal section 5, metadata và sáu failure phases + synthetic example | Đã đặc tả proposal; runtime chưa tồn tại |
| A5 B9 comparison/vector/PoC | Proposal section 6, P1–P5; V1/V2/sentinel | Đã đề xuất P1, B9 physical approval pending |
| A6 reconciliation/publication/rollback | Proposal section 7, existing validation I01–I12 mapping | Đã đề xuất gates; RawPublished không Certified mart |
| DW-02 compatibility | Proposal section 8; B1–B8/D05/DW-01 | Không phát hiện conflict architecture/logic; missing physical proofs vẫn có gate |
| Decision register | Six A01–A06 entries: problem/constraints/options/recommendation/rationale/trade-offs/risks/evidence/approval/impact | Đủ nội dung review; không có Accepted decision mới |
| Documentation quality/scope/security | Actual QA record bên dưới: 555 links/0 broken, 104 protected hashes, eight-file allowlist | PASS — document QA, không final design acceptance hoặc runtime PASS |

## 5. Required PoC/Test Plan — NOT RUN

| ID | Proof cần có sau approval | Expected acceptance evidence | Related existing scenarios |
| --- | --- | --- | --- |
| A-P01 | Exact source→carrier→Raw transport và capture completeness | Source/context counts/keysets/multisets/NULL/types, full columns, retained source anomalies và no silent loss | CD-T01/07/13 |
| A-P02 | Chosen consistency method, header/line/current/H concurrent change và context loss | Flags/session evidence, approved guarantee, detect mixed-context attempts; source-only DML không được phép | CD-T09/16, isolated test plan sau approval |
| A-P03 | Retry/extract/load failures, unknown target commit, source reconnect | Same sealed logical content reused once; context mới tạo capture mới; partial invisible | CD-T08/17–19 |
| A-P04 | B9 100 ns end-to-end round-trip/order/range/sentinel/NULL | Exact source digits/bytes và interval predicates, converter versions, no timestamp-only false matches | CD-T10/11/12 |
| A-P05 | Unicode/decimal/blob/geography/computed fields và schema drift | Lossless adapter proof, source metadata retained, original text/value coverage; no silent skip | Source Validation I04, dictionary |
| A-P06 | Atomic Raw membership/pointer, ACK loss, concurrent publication, compatible rollback/restore | Pinned consistent inputs, no duplicate publication, recovery audit; Core/mart certification riêng | CD-T17/18/20/21 |

Chỉ là PoC/test requirements, chưa tạo môi trường, fixtures, scripts hoặc data. Không duplicate toàn bộ C/D test matrix; references giữ test ownership cũ. Performance/driver compatibility và data quality thresholds chưa có kết quả, không claim PASS.

## 6. Stage 1 validation record — actual outputs được giữ nguyên

| Command / check thực hiện | Observed output | Kết quả / giới hạn |
| --- | --- | --- |
| `git status --short`, `git branch --show-current`, `git log -1 --format=...` đầu task | Clean; main; eeb22c224e767059581c3b10a3bb3f5d1f1cc0fb | PASS — expected baseline verified |
| `rg --files` inventory/validator discovery và đọc existing docs | Existing paths đã xác minh; không executable validator/package/test scripts trong repository | NOT APPLICABLE — không có existing validator để chạy |
| `sqlcmd ... -Q $metadataQuery` như section 3 | TLS certificate chain untrusted, client unable to establish connection; không có rows | FAILED — metadata connection; isolation/permissions vẫn Unverified, không là source data test |
| `python -c $summarize` — dictionary type inventory và local integer/date arithmetic | V1=639303428961234567 ticks; V2=639303428961234568; sentinel=3155378975999999999 dưới bigint max | PASS — mathematical illustration, không database/driver round-trip |
| `python -c $stageOneQa` — local link/anchor validation | 555 internal Markdown links, gồm 2 fragments; 0 broken target/anchor | PASS — document QA |
| Cùng Python QA — scope/hash/format/security | Đúng 8 Markdown files; 104 protected files giữ SHA-256; 0 scope/secret-pattern/binary/whitespace/encoding/fence/table errors | PASS — chưa phải comprehensive security audit |
| Cùng Python QA — proposal/status checks | 6 decisions PROPOSED; 9 source matrix rows; only DW-03A task row đổi; B/C/DW-04 TODO; 21 existing tests NOT RUN; 6 PoC plan rows | PASS — specification checks, không runtime PASS |
| `git diff --stat`, `git diff -- TASKS.md ROADMAP.md CHANGELOG.md docs/data-models/README.md` và đọc bốn new files | Chỉ navigation/status và Stage 1 documents; không physical/code artifacts | PASS — diff review |
| `git diff --check` | Exit 0, không whitespace errors | PASS |
| HEAD/staged check qua Python QA | HEAD giữ baseline; staged files rỗng | PASS — không commit/push |

QA dùng Python standard library trong PowerShell session, không tạo code artifact hoặc thêm dependency. Checks bao phủ các Markdown link targets/heading anchors, table widths/fences, UTF-8 replacement/trailing whitespace, credential/token/private-key patterns, source/ADR/scope/KPI/DW hashes và exact status/allowlist. Chỉ source metadata connection attempt thất bại; không có successful live SELECT result. LF→CRLF notices của Git không phải diff-check failures; không đổi Git config.

Không chạy database PoC/concurrency/round-trip, source DML, integration/e2e/pytest, dbt/Airflow hoặc failure injection; implementation/environment chưa được giao. Final design acceptance NOT PERFORMED; QA PASS chỉ xác nhận tài liệu proposal sẵn sàng để Owner review. Không stage/commit/push.

## 7. Files và statuses

Tạo bốn Markdown files: `wwi-dw-03a-work-plan.md`, `wwi-dw-03a-full-raw-design-proposal.md`, `wwi-dw-03a-decision-register.md`, `wwi-dw-03a-assessment.md`. Cập nhật chỉ `TASKS.md`, `ROADMAP.md`, `CHANGELOG.md`, `docs/data-models/README.md` để điều hướng/trạng thái. Không sửa PROJECT_SCOPE/AGENTS/ADRs hoặc accepted source/DW-01/DW-02 evidence.

DW-03A IN_PROGRESS; DW-03B/C và DW-04 TODO; WWI-04/Phase 1 In Progress; DW-01/DW-02/E giữ DONE ở mức thiết kế. Physical/database/pipeline implementation Not Started. Không stage/commit/push; HEAD phải giữ baseline sau task.

## 8. Owner review và điểm dừng

Owner review sáu recommended answers trong Decision Register. Các trọng tâm là associated archive/full-projection scope, consistency proof/fallback/TLS prerequisites, R1 retention/access, identity/state/retry contract, P1/B9 PoC và Raw publication gates/qualified-use restrictions. Không có yêu cầu tự chốt KPI/warehouse grains, source schema hoặc triển khai subsequent stage. Dừng ở Stage 1; final design acceptance chưa được thực hiện.

## 9. Stage 2 — evidence và approval readiness tại thời điểm review (lịch sử)

Stage 2 bắt đầu với 8 pre-existing Stage 1 changes, không clean working tree; chúng được bảo toàn. [Focused Evidence & Approval Readiness](wwi-dw-03a-evidence-approval-readiness.md) ghi metadata native exit 1/TLS error sau config inspection, nine local temporal check groups PASS/Python 3.12.10, detailed PoC và atomic publication/recovery contract. Các QA counts 555/104 ở section 6 là snapshot Stage 1; current Stage 2 QA nằm ở focused report.

| Readiness | Current conclusion |
| --- | --- |
| Design documented/logically reviewed | Có proposal/refinement, chưa formal acceptance |
| Source capability verified | Chưa; TLS blocker, SNAPSHOT/RCSI/permissions/read-only state Unverified |
| PoC plan | Detailed local/trusted-read-only/sandbox boundaries đã mô tả |
| PoC executed | Local subset 9 groups PASS; SQL formatter/driver/PG/persistence/concurrency NOT RUN |
| Formal A01–A06 approval | Chưa; reviewer recommendation không Owner approval |
| Runtime implementation | Not Started; existing pipeline test plans NOT RUN |
| Final design approval/closure | Chưa đủ evidence; DW-03A IN_PROGRESS, không đóng |

B9 vẫn Pending; exact 100 ns logical invariant không thay đổi. Proposed approval wording và exact implementation gates cho từng quyết định ở register; không inferred approval từ task này. Không stage/commit/push, không đổi source/TLS/config/schema và không bắt đầu B/C.

## 10. Verified SQL Evidence Update — current assessment, 2026-11-15

### 10.1 Baseline và execution boundary

Đầu vòng này: branch main, HEAD eeb22c224e767059581c3b10a3bb3f5d1f1cc0fb, 9 pre-existing dirty files gồm Stages 1–3; không staged. SHA-256 snapshot 113 working files dùng bảo vệ accepted documents và pre-existing root changes. Không reset/overwrite từ HEAD, không stage/commit/push.

[Evidence & Approval Readiness](wwi-dw-03a-evidence-approval-readiness.md) section 10 là single detailed evidence location: exact native sqlcmd argv, 7 SELECT-only queries Q01–Q07, actual results, A02 comparison tám tiêu chí, 14 synthetic fixtures, bounded actual periods, dependency inventory và proposed installation procedure. Không tạo SQL/Python artifact hoặc tài liệu trùng chức năng.

### 10.2 Updated acceptance checklist

| Requirement | Evidence / actual result | Assessment | Remaining work / limitation |
| --- | --- | --- | --- |
| Incorporate Owner evidence | Trusted endpoint/flags/V1 ghi rõ Owner-provided và direct SELECT tái kiểm chứng | PASS cho task evidence update | Không tự phê duyệt A01–A06/B9 |
| Trusted encrypted connection | Q01/Q06 native exit 0; TCP/NTLM, encrypt_option TRUE, -E -Nm, không bypass | PASS trên endpoint đã thử | Least-privilege read-only service-account proof chưa có; interactive session sysadmin |
| Current source isolation/protection | SNAPSHOT OFF, RCSI OFF, read-only OFF/READ_WRITE | Verified | Không bật config; không infer active writes hoặc immutable source |
| Nine current / two H mappings và SELECT | Q02 đủ 11 objects, SELECT=1; current temporal masters → respective archives; H không PK | PASS — metadata subset | Full source extraction/completeness chưa chạy |
| Source types/scale/result metadata | Q03/Q06/Q07: 156 current+56 H columns, 19 datetime2(7); quantity int/decimal, special fields, F1/F2 varchar(27) nullable | PASS — metadata | Adapter losslessness/rounding/physical target type chưa chọn |
| A02 reassessment | A=C2 static, B=C5 copy, C=C3 SERIALIZABLE; guarantee/prerequisites/source effect/risk/feasibility/verification/failure/approval đầy đủ | PASS — proposal completeness | Method/control/interval proof + Owner approval thiếu; normal publication hold |
| Owner V1 formatter case | Q04 text 27, ns 123456700 đúng | PASS — SQL synthetic case | Không full B9 PASS |
| F1 canonical fixed width | 4/13 non-NULL fixtures len 19 khi phần lẻ=0 | FAIL — candidate requirement | F1 V1 vẫn PASS; không dùng F1 như fixed-width codec chưa xử lý |
| F2 SQL synthetic/ordering | 14/14 fixtures, 169 ordered pairs/0 mismatch | PASS — source-side SQL subset | Chưa chọn implementation hoặc kiểm target comparator |
| Actual temporal columns | Q05 18/18 sampled cells round-trip equal/len27, sentinel và zero-duration giữ nguyên | PASS — bounded SQL sample | Không full-population/cross-table/driver/PG proof |
| Python/PG inventory | CPython3.12.10 x64; pyodbc/pymssql/psycopg/psycopg2 absent; không active approved PG profile trong inspected scope | Verified inventory | DBAPI/PG tests NOT RUN; không install hoặc đoán connection |
| Isolated dependency proposal | pyodbc==5.5.0; optional psycopg[binary]==3.3.9; existing ODBC18.6.2.1; upstream matching-wheel metadata và venv ngoài repo | PASS — đề xuất để Owner review | Dependency/version/profile approval; local artifact/hash/resolution/compatibility proof chưa có |
| A01–A06 / B9 / accepted policies | Sáu decisions giữ PROPOSED, B9 physical pending; B1–B8 và accepted source/DW/ADR/KPI không đổi | Required status preserved | Owner decisions và physical/runtime evidence còn thiếu |
| Final DW-03A design acceptance | Documented proposal + partial technical evidence | **CHƯA ĐỦ** | Approved extraction consistency, projection/type/100ns end-to-end, manifests/publication gates và A01–A06 approvals |
| DW-03B/C, implementation và databases | Không bắt đầu; không source/target writes/config, install hoặc long SERIALIZABLE transaction | Scope preserved | Không suy dependencies đạt là authorization phase/task sau |

F1 candidate failure là finding hợp lệ của verification; không làm mất kết quả V1 PASS hoặc buộc mở rộng scope để triển khai formatter. Existing CD-T01–21 vẫn NOT RUN; A-P01–06 chưa hoàn tất, chỉ source SQL subset được ghi PASS ở đúng boundary. No successful full capture, Raw load, PostgreSQL persistence, recovery/atomicity hoặc benchmark được tuyên bố.

### 10.3 Files changed so với đầu vòng và rationale

1. `docs/data-models/wwi-dw-03a-evidence-approval-readiness.md`: top current summary, section 10 commands/results, A02 alternatives, precision findings, isolated dependency proposal và gates; giữ nguyên lịch sử lỗi Stages 1–3.
2. `docs/data-models/wwi-dw-03a-decision-register.md`: A02 recommendation theo OFF/OFF; A01/A05/A06 evidence available/missing cập nhật; mọi A01–A06 vẫn Proposed, approval wording vẫn draft.
3. `docs/data-models/wwi-dw-03a-assessment.md`: checklist hiện hành, phân biệt partial SQL PASS với full acceptance, file/Git/QA boundary.
4. `docs/data-models/wwi-dw-03a-full-raw-design-proposal.md`: sửa active recommendation C1/C2 đã lỗi thời, trạng thái source/precision; không đổi Raw architecture hoặc B1–B8.
5. `docs/data-models/README.md`: navigation/current execution status, bỏ claim SQL source tests toàn bộ NOT RUN.

`TASKS.md`, `ROADMAP.md`, `CHANGELOG.md` và work plan có changes từ trước được giữ nguyên trong vòng này; không sửa AGENTS/PROJECT_SCOPE/source contracts/KPI/ADRs/DW-01/DW-02. Tổng Git dirty vẫn gồm 9 pre-existing paths; danh sách 5 ở trên là **incremental diff của task hiện tại**, không đánh đồng với toàn working tree.

### 10.4 Documentation QA / Git verification

Đã chạy `python -c $dw03EvidenceQa` bằng standard library, final exit **0 / PASS**: đúng 5 Markdown files trong allowlist thay đổi so với đầu vòng; **108 protected initial files giữ SHA-256**, gồm ba root management changes và work plan từ trước. Kiểm tra **580 local Markdown links, 2 fragments**, 0 broken targets/anchors; 0 secret-pattern hits, control/UTF-8/whitespace/fence/table errors, SQL write-statement blocks, binary hoặc files >5 MiB. Sáu overview decisions đúng PROPOSED; task statuses unchanged. `git diff --check` exit **0**; index rỗng, branch **main**, HEAD giữ **eeb22c224e767059581c3b10a3bb3f5d1f1cc0fb**. Tổng 9 dirty paths giữ từ Stages 1–3, không file mới ngoài scope; không stage/commit/push.

QA chỉ kiểm nội dung tài liệu/scope/secret patterns; không comprehensive secret guarantee hoặc source/driver/target runtime PASS. Không tạo remote, commit/push hoặc thay đổi history.

### 10.5 Remaining Owner gates và stop

- **A02:** duyệt proposed static window và yêu cầu writer-control evidence; nếu không bảo đảm, giao task verified consistent copy riêng. SERIALIZABLE chỉ sau separate operational approval, chưa execute.
- **A01/A03/A04/A06:** review logical wording/gates trước implementation; full projection/special-type fidelity, retention/lineage/state/atomic target enforcement còn evidence gaps.
- **A05/B9:** duyệt F2 next-PoC direction và pinned isolated dependencies/read-only identities/profiles nếu muốn tiếp tục; chưa duyệt physical datatype/collation/codec chỉ từ SQL subset.
- **Không đủ để đóng DW-03A:** A01–A06 còn Proposed; source common full-extraction consistency, Python/PG/end-to-end precision, target persistence/publication/concurrency/recovery chưa verified. B9 vẫn Pending Physical Approval.
- **Điểm dừng:** bàn giao technical evidence update để Owner review; DW-03A IN_PROGRESS, WWI-04/Phase 1 In Progress; DW-03B/C/DW-04 TODO. Không triển khai hoặc tự bắt đầu task tiếp.

## 11. Owner Logical Approval Milestone — current assessment

### 11.1 Authority, baseline và thay đổi được phép

Project Owner instruction **“DW-03A — Record Project Owner Logical Design Approvals”**, 2026-11-15 formal approve đúng sáu mức trong [Decision Register](wwi-dw-03a-decision-register.md). Đây không là inferred approval từ SQL PASS hoặc reviewer recommendations. Đã đọc AGENTS, project management, năm DW-03A documents và sáu accepted DW-02 ADRs; không cần khảo sát lại Phase 1 hoặc kết nối database trong task ghi nhận này.

Trước chỉnh sửa: branch main, HEAD eeb22c224e767059581c3b10a3bb3f5d1f1cc0fb; 9 dirty Markdown paths của Stages 1–3/SQL evidence, index rỗng. Initial SHA-256 113 files bảo vệ existing work; không reset/revert. Current Owner cho phép cập nhật năm DW-03A documents, related navigation/management khi cần, và **một documentation-only commit sau QA/staged review**; lịch sử “không commit” ở sections trước giữ đúng thời điểm của nó.

### 11.2 Design/documentation milestone checklist — không final DW-03A acceptance

| Design/documentation criterion | Evidence | Milestone result | Remaining approval / verification boundary |
| --- | --- | --- | --- |
| Record A01/A03/A04/A06 | Register ghi APPROVED — Logical Policy, authority/date, scope và limits theo instruction | PASS — recorded approval | Full preservation/state/recovery/publication runtime proof chưa có |
| Record A02 conditional policy | Static window cần no-write evidence; fallback separately approved verified copy; OFF/OFF giữ nguyên, no NOLOCK/auto SERIALIZABLE | PASS — recorded conditional approval | Concrete method/interval evidence chưa verified, normal publication hold |
| Record A05 đúng cấp | F2 preferred candidate, APPROVED — PoC Direction Only; B9 Pending Physical Approval | PASS — direction recorded | Không final PG datatype/adapter/encoding/collation hoặc install authorization |
| Preserve verified/unfavorable evidence | Evidence section 10/Q01–Q07 và fixture/sample results giữ nguyên | PASS — prior SQL evidence preserved | Không test DB mới; F1 fixed-width FAIL không bị nâng thành PASS |
| Preserve accepted decisions/scope | B1–B8, six accepted ADRs/source/KPI/DW-01/DW-02 không thay; 104 protected files giữ initial hashes | PASS — hash QA | Không business/architecture/phase expansion |
| Explicit remaining backlog | Work plan section 5: G01–G08, dependencies/evidence/status/approval boundary | PASS — documented gates | Tám gate còn mở; partial SQL subset không close G05 |
| Narrow B9 handoff | Work plan section 6: B9-P01–06, minimal isolated environment, pending pinned dependencies/profiles, read-only vs persistence boundary | PASS — plan documented | Chưa authorized install/PoC execution/writes/tables |
| Management/navigation consistency | README/TASKS/ROADMAP/CHANGELOG có latest logical approval note; task statuses không đổi | PASS — documentation QA | DW-03A IN_PROGRESS; B/C/DW-04 TODO; WWI-04/Phase 1 In Progress |
| Documentation/security checks | Actual QA record ở 11.5; staged verification là điều kiện trước commit | PASS — pre-stage QA | Không secret/data/code/config ngoài allowlist; chưa runtime proof |
| Final DW-03A acceptance | Owner chỉ approve logical-decision milestone và giữ task IN_PROGRESS | **NOT PERFORMED** | Final review/acceptance chưa được giao hoặc ban hành |

Tách hai loại điều kiện: **design closure** cần review/disposition hợp lệ của concrete extraction method/operational evidence, physical design/B9 questions và final acceptance theo Owner; **runtime readiness** cần các tests ở 11.3 khi implementation được giao. Không đặt thêm yêu cầu phải triển khai toàn pipeline để ghi nhận logical approval, không đổi implementation tests thành design PASS hoặc tự sửa acceptance criteria trong TASKS.md.

### 11.3 Runtime/physical verification — giữ trạng thái riêng

| Runtime/physical criterion | Actual evidence hiện có | Status / future gate |
| --- | --- | --- |
| Consistent full extraction và least-privilege ingestion identity | Trusted interactive metadata/TLS; OFF/OFF/READ_WRITE; interactive sysadmin | Full capture Unverified / service-account proof chưa có — G01/G02 |
| Exact F2 SQL source formatting | 14/14 fixtures PASS; 169 comparisons/0 mismatch; 18/18 actual sampled cells PASS | Verified SQL subset — không full B9 |
| F1 fixed-width negative finding | ZERO/NEXT_SECOND/MIN/LEAP_DAY trả len19; V1 len27/ns123456700 PASS | FAIL canonical fixed width ở bốn cases — giữ nguyên evidence |
| Source→Python DBAPI string transport | Prior inventory thiếu approved installed Python drivers | NOT RUN — G03; subprocess CLI parsing không DBAPI |
| PostgreSQL parameter SELECT / persisted round-trip | Không approved active target profile/driver test trong prior scoped inspection | NOT RUN — G04; SELECT echo không storage proof, không tạo tables |
| End-to-end ordering/collision/predicate/boundary | SQL-side subset và local math, chưa driver/PG path | NOT RUN end-to-end — G05 |
| Full special datatype preservation | Source metadata verified, chưa adapters | NOT RUN — G06 |
| Physical Raw schema/retention/access/capacity | Logical A03 approved; chưa physical proposal acceptance/implementation | Pending implementation-level approval — G07 |
| Atomicity/retry/concurrency/rollback/recovery | Logical A04/A06 approved; không runtime implementation | NOT RUN — G08 |
| Existing pipeline/CD-T01–21 | Existing design scenarios chưa execution | NOT RUN — không chạy trong documentation milestone |

Không install thư viện, tạo source code/dependencies/config, tạo schema/table, đọc/chỉnh SQL Server/PostgreSQL hoặc bắt đầu B9 PoC trong task này. Remaining gate backlog authoritative tại work plan; không tự đóng gate vì đã ghi approval.

### 11.4 Files changed và preservation

**9 existing Markdown paths** được cập nhật/đưa vào milestone commit theo instruction, gồm cả pre-existing Stage 1–3 work:

1. `docs/data-models/wwi-dw-03a-decision-register.md`: sáu formal levels, authority/date, recorded text và remaining gates; loại current “all Proposed” claim.
2. `docs/data-models/wwi-dw-03a-full-raw-design-proposal.md`: logical-approved scope tách physical options; F2 PoC-only, A02 condition và current approval boundary.
3. `docs/data-models/wwi-dw-03a-evidence-approval-readiness.md`: latest approval section 11; nguyên trạng historical SQL/failed/successful evidence sections 1–10.
4. `docs/data-models/wwi-dw-03a-assessment.md`: milestone checklist, runtime checklist, preservation/QA/final acceptance limits.
5. `docs/data-models/wwi-dw-03a-work-plan.md`: current approval milestone, G01–G08 backlog và narrow B9-P01–06 handoff.
6. `docs/data-models/README.md`: latest approval/navigation và B9/runtime limitations.
7. `TASKS.md`: ghi milestone approval/evidence/backlog, không đổi task statuses/acceptance criteria.
8. `ROADMAP.md`: latest logical milestone/remaining gates, không phase transition.
9. `CHANGELOG.md`: ghi nhận logical approvals/F2 direction và explicit no-final-acceptance boundary.

AGENTS/PROJECT_SCOPE, accepted DW-02/ADR/source/KPI và các modules runtime ngoài phạm vi giữ nguyên. Không file mới, xóa file hoặc code/config/binary/dataset artifacts.

### 11.5 Actual documentation QA và Git checks

Đã chạy `python -c $approvalQa`, final exit **0 / PASS**: đúng 9 existing Markdown paths trong scope, 104 protected initial files giữ SHA-256; **597 local Markdown links, 2 fragments**, 0 broken targets/anchors; 0 secret-pattern/control/encoding/whitespace/fence/table errors, SQL write-statement blocks, binary hoặc files >5 MiB. Sáu Approved overview rows đúng từng cấp, sáu Recorded Owner decisions, tám G01–G08 và sáu B9-P01–06 plan steps; task statuses giữ nguyên. Evidence sections 1–10 và tám SQL code blocks giữ nguyên nội dung trước approval. `git diff --check` exit **0**; pre-stage index rỗng, branch main, parent HEAD eeb22c224e767059581c3b10a3bb3f5d1f1cc0fb. Không database tests mới hoặc dependency install.

Staging/commit được Owner cho phép với **exact 9 Markdown paths** đã liệt kê; kiểm tra staged path allowlist, blob/content diff, secret patterns, size và `git diff --cached --check` trước commit. Message: `docs: approve DW-03A logical design policies`. Kết quả staged verification và Git commit thực tế được báo sau khi thực hiện; chỉ commit khi mọi checks đạt, không push.

QA chỉ đánh giá documentation/scope/pattern security; không comprehensive secret assurance hoặc driver/database/runtime PASS. Hash của milestone commit được xác minh bằng `git log -1 --format=%H` sau commit và báo trong final report; không thay history hoặc push.

### 11.6 Acceptance readiness và stop

**Logical approval recording milestone đã được Owner cho phép; DW-03A final acceptance chưa thực hiện, giữ IN_PROGRESS.** Các unresolved items là technical/physical/evidence gates ở đúng cấp, không còn “chờ Owner phê duyệt A01–A06 logical directions”. Concrete full-extraction method/proof và B9 physical/target evidence chưa đủ; Raw implementation/publication chưa được phép coi ready.

Owner review tiếp narrow handoff/environment/dependency installation và connection authority trước khi execution; persistence/physical design cần scope riêng. DW-03B/C/DW-04 TODO, WWI-04/Phase 1 In Progress; B1–B8 và DW-02 design DONE giữ nguyên. Chỉ một documentation-only commit nếu QA/staged checks đạt; không push, database changes, install hoặc bắt đầu task tiếp.
