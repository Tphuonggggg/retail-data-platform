# WWI DW-03A — Work Plan, Technical Gates & B9 Handoff

**IN_PROGRESS — Owner Logical Approval Milestone, 2026-11-15.** A01/A03/A04/A06 Approved — Logical Policy; A02 Approved — Conditional Logical Policy; A05 Approved — PoC Direction Only. B9 Pending Physical Approval; chưa final DW-03A acceptance. Sections 1–3 giữ baseline/plans/evidence trước approval; sections 4–6 là backlog và handoff hiện hành. Runtime: **Not implemented yet**; không bắt đầu DW-03B/C.

## 1. Baseline Stage 1 và đầu vào (lịch sử)

Branch `main`; HEAD đã xác minh **`eeb22c224e767059581c3b10a3bb3f5d1f1cc0fb`**, message `docs: finalize WWI SCD2 design policies`; working tree đầu task sạch. Không có pre-existing modifications cần ghép. Snapshot SHA-256 108 tracked files dùng kiểm preservation; không tạo snapshot dữ liệu nguồn.

Dependencies đã có: [Source Contracts](wwi-source-contracts.md), [Extraction Matrix](wwi-extraction-requirements-matrix.md), [Raw Requirements](../requirements/wwi-raw-layer-requirements.md), [Validation Matrix](../requirements/wwi-source-validation-matrix.md), [DW-01](wwi-logical-dw-design.md), [DW-02 Specification](wwi-final-scd2-design-specification.md), [E acceptance/handoff](wwi-dw-02e-assessment.md), [sáu ADR](../adr/README.md). Business definitions theo [KPI Catalog](../../analytics/kpi-definitions/wwi-kpi-candidate-catalog.md); không mở lại BRD/KPI, grains hoặc SCD tracking set.

Đã kiểm inventory/profiling/dictionary và README ingestion/storage/infrastructure. Trong repository chưa có DW-03A deliverables hoặc executable document validator cùng chức năng; không tạo thêm requirements/ADR trùng lặp.

### Work packages của Stage 1

| Package | Việc thực hiện | Output / dependencies | Completion của Stage 1 |
| --- | --- | --- | --- |
| A1 / A01 | Phân loại chín bảng, current/archive/snapshot, full-read và preservation | Matrix trong proposal; dictionary/source profiles | Chín nguồn đủ grain/key/population/method/checks; archive là dependency riêng, không nguồn độc lập |
| A2 / A02 | So sánh source consistency và kiểm metadata nếu truy cập an toàn | Consistency matrix; primary docs; read-only metadata attempt | Guarantees/limitations rõ, không assume SNAPSHOT/RCSI hoặc thay source config |
| A3 / A03 | So sánh Raw storage options và conceptual objects/keys | Raw architecture trong proposal | No SCD2 transform ở Raw, evidence retention và future incremental interface |
| A4 / A04 | Run/batch/capture/snapshot/attempt/lineage, retry transitions | Metadata/state/recovery matrices | Không đồng nhất retry với same source snapshot; preserve legitimate occurrences |
| A5 / A05–B9 | So sánh text/ticks/numeric/native+component | Temporal matrix, synthetic vectors, PoC plan | Exact 100 ns contract, no driver compatibility claim; B9 chưa Approved |
| A6 / A06 | Full-load reconciliation, atomic visibility, rollback | Gate matrix và publication states | RawPublished khác Certified mart; partial/unknown commit recovery có path |
| Assessment | Compatibility, missing evidence, QA và Owner questions | [Assessment](wwi-dw-03a-assessment.md) | Chỉ review completeness của proposal; không final acceptance hoặc runtime PASS |

### Phạm vi file Stage 1

Tạo bốn file hiện hành: tài liệu này, [Full & Raw Proposal](wwi-dw-03a-full-raw-design-proposal.md), [Decision Register](wwi-dw-03a-decision-register.md), [Assessment](wwi-dw-03a-assessment.md). Chỉ đồng bộ `TASKS.md`, `ROADMAP.md`, `CHANGELOG.md` và `docs/data-models/README.md`. Không sửa scope/ADR/evidence nguồn hoặc các module runtime; không DDL/Python ingestion/dbt/DAG/Docker/dependency.

## 2. Discovery và proof boundaries Stage 1 (lịch sử)

Metadata attempt qua sqlcmd/Windows integrated authentication thất bại tại TLS certificate-chain validation; không có SELECT result, không thay cấu hình hoặc bypass certificate. Isolation flags/service-account permissions hiện Unverified. Driver 18 xuất hiện trong error là tool hiện có, không là connector pipeline được chọn. SQL/evidence chi tiết trong assessment; proposal vẫn so sánh các alternatives có điều kiện.

Toàn bộ database/driver/concurrency/failure PoC tests NOT RUN. Mathematical vector checks chỉ là phép tính local bằng standard library, không chứng minh SQL Server→driver→PostgreSQL round-trip. Existing CD-T01–21 vẫn NOT RUN. Không stage/commit/push. Dừng sau Stage 1 để Owner review A01–A06; DW-03A giữ IN_PROGRESS, B/C/DW-04 TODO, WWI-04/Phase 1 In Progress.

## 3. Stage 2 — Evidence Verification & Owner Approval Package (lịch sử)

Stage 2 bắt đầu tại cùng HEAD eeb22c224e767059581c3b10a3bb3f5d1f1cc0fb, với 8 Stage 1 documents/root-navigation changes chưa commit được bảo toàn; snapshot 112 working files. Chỉ cập nhật bốn DW-03A documents, index và thêm [Evidence & Approval Readiness](wwi-dw-03a-evidence-approval-readiness.md). Root management files của Stage 1 không sửa thêm; accepted DW-02/ADR/source/KPI/scope giữ nguyên.

| Stage 2 package | Deliverable / evidence | Current result |
| --- | --- | --- |
| A01 completeness | Nine current/two H populations, occurrence/null/type và Sales scope checklist trong focused report | Verified historical evidence + reviewed logical coverage; current extraction NOT RUN |
| A02 trusted connectivity/capabilities | Safe config inspection, explicit encryption metadata probe, three-state classification và alternatives | Native exit 1 TLS; source flags/permissions vẫn Unverified, normal publication blocker |
| A03/A04 lifecycle | Distinct IDs/keys, sealed replay vs new capture, failed/superseded/retention và crash sequence | Proposed refinement, không physical objects |
| A05/B9 | F1/F2 source formatter candidates, detailed PoC split local/read-only/sandbox, A05-L01–09 | 9 local groups PASS; source formatter/driver/PG NOT RUN; B9 pending |
| A06 | Scope/manifest/ledger/pointer/pinning và 7 failure scenarios | Proposed atomic contract; source consistency khác target atomicity và Certified output |
| Consolidated review | Per-decision evidence/missing proofs/risks/wording/gates trong register; readiness matrix/QA trong focused report | Reviewer recommendations không Owner approvals; mọi A01–A06 Proposed |

Không đóng DW-03A; chưa final design acceptance. Dừng sau Stage 2; không commit/push, không database config/trust changes hoặc bắt đầu B/C.

## 4. Owner approval milestone và dependencies hiện hành

Nguồn authority: Project Owner instruction **“DW-03A — Record Project Owner Logical Design Approvals”**, 2026-11-15. [Decision Register](wwi-dw-03a-decision-register.md) là nơi ghi sáu approval và giới hạn chính thức; không nâng logical approval thành physical/runtime approval. B1–B8 và accepted DW-02/ADRs không đổi.

Dependencies tài liệu: DW-01/DW-02 DONE ở mức thiết kế; source contracts/dictionary/profiling hiện có; trusted SQL evidence tại [Evidence report](wwi-dw-03a-evidence-approval-readiness.md) section 10. Scope/source consistency/full preservation, immutable manifests, distinct IDs và atomic pinning được duyệt ở đúng mức; concrete method/schema/retention/dependencies/runtime vẫn còn gate. Không phải chờ Owner approve lại A01–A06 directions để ghi nhận milestone này.

| Milestone package | Module / dependencies | Acceptance evidence của vòng hiện tại | Status |
| --- | --- | --- | --- |
| Record Owner approvals | docs/data-models; Owner instruction + accepted DW-02 | Six exact approval levels/limits, authority/date và unchanged B9/B1–B8 | Documented / documentation QA PASS |
| Technical gate backlog | docs/data-models; SQL evidence + approval register | Tám gate có dependencies, proof/approval boundary, không fake runtime results | Documented — chưa execution |
| Narrow B9 handoff | docs/data-models; A05 PoC direction + G02/G03/G04 approval prerequisites | Source F2 → pyodbc string → psycopg text parameter; minimum isolated environment và stop conditions | Planned — chưa chạy |
| Milestone commit | Root/docs; documentation QA + staged review | Chỉ 9 approved Markdown paths, no secrets/source data/code/config, một commit theo Owner | Authorized sau PASS checks; Git outcome báo trong final report |

Đây là milestone documentation checklist, không đổi task tracker statuses hoặc claim toàn DW-03A DONE. Existing CD-T01–21/full pipeline tests vẫn NOT RUN.

## 5. Remaining technical gates — backlog tách khỏi logical approval

G01–G08 là **gate IDs để trace**, không phải approval decisions hoặc authorization tạo task implementation mới. Mọi gate còn mở; source-side SQL subset PASS được ghi riêng, không dùng để đánh dấu toàn gate đạt.

| Gate ID | Nội dung / module | Dependencies / authority trước execution | Evidence bắt buộc để vượt gate | Current status / next boundary |
| --- | --- | --- | --- | --- |
| G01 | Full-extraction consistency — ingestion/source operations | A02 conditional policy; Owner xác nhận scope/window/writer controls hoặc separate task cung cấp copy | Defensible no-write controls toàn extraction + reconciliation interval; hoặc verified consistent copy/provenance/writer exclusion; full-capture context/coverage và failure handling | OPEN — source SNAPSHOT/RCSI OFF verified, method/interval proof Unverified; hold normal publication |
| G02 | Least-privilege ingestion service account — infrastructure/security | Owner/DBA cấp read-only identity/profile được duyệt; account provisioning ngoài task này | Trusted validated TLS; necessary metadata/SELECT trên required current/H; source write/admin privileges không cấp cho ingestion; effective principal/permissions evidence không lộ secret | OPEN — current interactive sysadmin không đáp ứng service-account proof |
| G03 | Python SQL Server driver transport — ingestion/adapters | Separate approval pyodbc/version + isolated venv; G02 cho service-account claim | F2 fetched thành str/None, exact length/7 digits/NULL/boundaries và result metadata giữ nguyên, không coercion qua datetime/float; actual driver/runtime versions | NOT RUN — pyodbc absent ở interpreter đã kiểm; dependency install chưa authorized |
| G04 | PostgreSQL parameter và persistence round-trip — storage/adapters | Approved target profile/psycopg/version; G03 payload; riêng persistence cần existing sandbox sink + explicit write approval | SELECT parameter echo, byte/character length/equality/NULL; riêng persisted write/read/commit/retrieve evidence khi được giao | NOT RUN — không approved active target profile; SELECT echo không vượt persistence gate; chưa cho tạo tables |
| G05 | Exact temporal ordering/collisions — ingestion/staging contract | G03/G04 read-only paths + approved PoC comparison expressions | 100 ns adjacent values distinct; ordered pairs, half-open predicates, zero-duration, sentinel, duplicate occurrences/NULL; compare source vs target without native microsecond authority | PARTIAL SQL ONLY — 14 fixtures/169 pairs/18 sampled cells PASS; end-to-end predicates/collision proof NOT RUN |
| G06 | Special datatype adapters — ingestion/storage | A01 full preservation; G02; approved projection/adapter design và task phù hợp | Exact decimal scale, Unicode, NULL, varbinary/photo, geography và computed values, source metadata; schema drift/unsupported conversion hold, không silent drop | NOT RUN — metadata verified, adapter fidelity chưa verified; ngoài narrow B9 path |
| G07 | Physical Raw schema và retention — storage/infrastructure | A03 logical capture/manifest; G01–G06 requirements, Owner physical design approval | Reviewed schema/types/keys/access controls/capacity/retention periods; referenced evidence/forward observations/compatible restore được bảo vệ; measures có thực nghiệm khi claim | PENDING IMPLEMENTATION-LEVEL APPROVAL — không DDL/purge/retention defaults ở task này |
| G08 | Publication atomicity/recovery/concurrency — storage/orchestration | A04/A06 logical policies; G01/07, approved runtime sandbox và failure test scope | Coherent ledger/membership/pointer, pinned compatible dependencies; crash/ACK-loss/retry/race/no partial visibility/rollback/recovery proofs và durable-state read-back | NOT RUN — logical contract Approved, physical enforcement chưa triển khai; RawPublished không Certified |

Khi runtime evidence còn thiếu, không ghi “logical approval missing” thay nguyên nhân thật. Design review phải nêu disposition/owner/gate cho physical details; runtime check chỉ PASS khi thực thi đúng môi trường. Certification thresholds/B1–B8 thuộc accepted DW-02 gates tiếp tục giữ, không tự chọn từ bảng này.

## 6. Narrow B9 PoC handoff — Planned, không thực thi trong milestone này

### 6.1 Approved direction và minimum isolated environment

Flow: **SQL Server source-side F2 → Python pyodbc str/None → PostgreSQL psycopg text parameter → exact comparison/round-trip evidence**. A05 chỉ approved F2 preferred candidate; pyodbc/psycopg là components của handoff được yêu cầu, **chưa final adapter selection/installation approval**. B9 PENDING PHYSICAL APPROVAL.

Minimum proposed environment: existing Windows x64/CPython 3.12.10; venv mới ngoài repository; existing ODBC Driver 18 for SQL Server 18.6.2.1; trusted endpoint/profile đã verified, Windows Integrated Authentication/encryption mandatory và validation enabled. Cần approved least-privilege source identity để vượt G02; không mặc định interactive sysadmin là ingestion principal. PostgreSQL dùng **existing approved isolated database/profile** được Owner cấp, không tự tạo server/database/schema/table.

Candidate exact dependencies giữ từ evidence section 10.6: **pyodbc==5.5.0**; optional target **psycopg[binary]==3.3.9** với matching psycopg-binary==3.3.9 và reviewed resolved transitive set. Upstream wheel metadata có sẵn nhưng local download/hash/compatibility chưa verified. Không pip install/upgrade, requirements/lock/venv creation trong task hiện tại; procedure đề xuất có sẵn ở evidence section 10.6, không nhân bản thêm script/config.

### 6.2 Verification steps, evidence và dependencies

| Step | Planned action / dependency | Acceptance evidence của narrow PoC | Stop condition |
| --- | --- | --- | --- |
| B9-P01 | Owner duyệt isolated environment, exact dependency versions/installation, source identity và target read-only profile; G02/G03/G04 prerequisites | Environment/permission inventory không lộ secrets, install/version evidence khi thật sự authorized | Thiếu approval/profile/driver → NOT RUN; không tự install/provision hoặc đoán credentials |
| B9-P02 | Sau authorization, SELECT F2 trên 14 existing fixtures + bounded current/H period samples; reuse Q04/Q05/Q07 | Expected/actual canonical strings, source/result datatype metadata, NULL riêng và exact source digits; không business payload dump | Formatter/type/scale drift hoặc TLS/permission fail → giữ failed evidence, dừng |
| B9-P03 | pyodbc fetch projected F2 trực tiếp thành Python str/None; không fetch native datetime rồi reformat | Every expected digit/27 ASCII characters, UTF-8 bytes/NULL; driver/version/settings; V1/V2 distinct và sentinel đủ digits | Coercion/truncation/type mismatch → FAIL; không pad digit sau loss |
| B9-P04 | psycopg bind Python strings bằng text parameters trong approved read-only SELECT; record target version/encoding và comparison expression | Echo byte-for-byte, character/octet lengths, parameter/result types và NULL; exact equality source→Python→PG→Python | Không approved target hoặc failed binding/TLS/precision → NOT RUN/FAIL; không tạo sink/table |
| B9-P05 | Read-only target comparison trên same-basis fixture values; candidate explicit bytewise comparator như COLLATE C chỉ là PoC expression | 169 ordered-pair comparison checks đối chiếu source; adjacent 100 ns no collision, half-open bounds/zero-duration, duplicate occurrences retained, negative lossy controls | Không default collation/timestamp(6) authority; mismatch → hold, không tự chọn representation |
| B9-P06 | Consolidate expected/actual/version/command/status report và remaining physical proposal để Owner review | Tách SQL source PASS, DBAPI transport, PG parameter/predicate outcomes và persistence NOT RUN; không nâng toàn B9 thành Approved | Không physical schema/adapter/encoding/collation selection từ PoC direction; không mở DW-03B/C |

Các rows trên là kế hoạch có dependencies, **chưa executed tests**. Không khẳng định kết quả mới; source-side control giữ F1 V1 PASS nhưng 4 zero-fraction fixed-width FAIL, F2 14/14/169/18 evidence như đã verified. Zero-duration không tạo positive interval; same timestamp/duplicate payload không thành durable source occurrence key hoặc SK.

### 6.3 Persistence và final approval boundary

Narrow path hiện đề xuất chỉ source/target SELECT và client comparison; text parameter trong SELECT là test carrier/expression, **không chốt physical PostgreSQL storage datatype, adapter, encoding, collation hoặc index**. Persistent round-trip cần riêng existing isolated sink và explicit write/storage-test authorization; **không tạo tables hoặc writes ở task này**, không giả định temporary tables/rollback làm DDL/DML được phép. G04 persistence và G07 physical design vẫn mở sau read-only echo PASS.

B9 chỉ có thể trình physical approval khi appropriate transport/target/predicate/persistence evidence đủ và physical proposal được Owner review; logical 100 ns invariant D05 không bị hoãn. Final DW-03A design acceptance còn cần Owner review closure checklist với disposition của các design/operational gates; implementation tests giữ trạng thái riêng, không vừa thiếu runtime lại nói chưa có logical approval.

**Điểm dừng milestone:** ghi tài liệu, QA, stage đúng documentation allowlist và một commit nếu QA/staged checks đạt theo current Owner instruction. Không install, PoC execution, nguồn/đích changes, push, hoặc DW-03B/C. DW-03A IN_PROGRESS; DW-03B/C/DW-04 TODO; WWI-04/Phase 1 In Progress.
