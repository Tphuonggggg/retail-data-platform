# WWI DW-03A — Work Plan, Technical Gates & B9 Handoff

**DONE — Design, 2026-11-15.** Nghiệm thu theo conditional authority của Owner sau final design review/B9 physical approval và QA. A01–A06 giữ đúng cấp; **B9 Approved — Physical Raw Temporal Representation**. Section5 là current G01–G08 disposition, section10 là final handoff; prior milestones giữ history. Production runtime Not implemented yet; WWI-04/Phase1 IN_PROGRESS, DW-03B/C/DW-04 TODO.

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

| Gate | Design / runtime disposition | Reason for deferral | Owner chịu trách nhiệm / authority | Target stage | Required evidence | Acceptance gate |
| --- | --- | --- | --- | --- | --- | --- |
| G01 | Design PASS — approved conditional A02; full extraction consistency Unverified/NOT RUN | Chưa có extraction window/no-writer controls hoặc verified source copy, không suy từ read-only client | Source Owner/DBA + ingestion implementer; Project Owner duyệt method/copy | WWI-05 prepare, trước WWI-06 full capture/normal publication | Writer inventory/controls và no-write interval bao trùm extract/reconcile; hoặc approved verified copy/provenance; same-context counts/keys/multisets | Không proof thì hold normal publication; không tự bật SNAPSHOT/RCSI, NOLOCK claim hoặc long SERIALIZABLE |
| G02 | Design security contract PASS; runtime account verification pending | PoC dùng interactive sysadmin, không least-privilege identity | Source DBA cấp account, implementer/DQ verify, Project Owner approve | WWI-05, trước WWI-06 ingestion | Effective role/grant metadata cho required SELECT/current/H/metadata, không write/admin; trusted TLS/profile; không thử DML nguồn | Chưa verified read-only source identity thì không deployment ingestion; PoC permissions không thay production proof |
| G03 | B9 design Approved + bounded SQL→Python PoC PASS; production path deferred | Chưa có actual extractor/full projection/config deployment | Ingestion implementer/DQ reviewer; Project Owner review adapter/config changes | WWI-06, trước full-load publication | Actual mapped datetime2 fields/version/config giữ F2/str-None exact27/NULL và lineage, regression corpus/field metadata | Precision/type/unsupported conversion failure hold; không reconstruct lost digits từ datetime |
| G04 | B9 design Approved + PG parameter/persistence PoC PASS; actual Raw path deferred | Test-only table không là full Raw schema/loader | Storage/ingestion implementer + DQ; Project Owner physical schema approval | WWI-05 schema review rồi WWI-06 trước normal publish | Actual Raw mapping TEXT/C, constraints/NULL/multiplicity và source-to-Raw/replay exactness trong approved environment | Không lấy sandbox15 rows thay full Raw proof; actual schema/transport phải verified trước publish |
| G05 | Exact comparator design Approved + fixture order/equality/range PoC PASS; wider runtime proof pending | Corpus bounded, chưa actual lookup/secondary indexes/full-domain drift tests | DW/ingestion implementer + DQ; Project Owner review secondary design | WWI-06 trước Raw conversion/publish; WWI-08 trước Core lookup | Full relevant fields/version/basis, exact predicates/collisions; secondary representations không thay source TEXT; day-domain/B3 proof riêng | Mismatch/ambiguous basis không thành successful lookup; không timestamp-only predicate hoặc business-time inference |
| G06 | Design full-field fidelity obligations PASS; concrete adapters/test proof deferred | decimal/Unicode/blob/geography/computed paths chưa implement/verify | Ingestion/storage designer + DQ; Project Owner review physical mapping/dependency proposal | WWI-05 physical mapping review trước WWI-06 code/full payload; proof trước publish | Explicit field projection/NULL/source metadata, exact decimal scale/Unicode/bytes/geography/computed outputs, drift/unsupported cases | No silent drop/trim/round/JSONB-only loss; unverified adapter hold complete-fidelity claim/publication |
| G07 | Conceptual Raw/evidence-retention design PASS; physical implementation approval pending | A03 và current B9 explicitly exclude full DDL/index/period/access/capacity approval | Storage designer + source/data custodian; Project Owner approval authority | WWI-05 physical review trước WWI-06 schema/load; retention approval trước purge | DDL/control-keys/access/capacity/backup/layout proposal trace conceptual objects, B9 TEXT/C; retention/reference/restore impact and approved periods | Chưa approved thì không execute schema/purge; không xóa referenced/forward/history/registry/publication evidence; không infinite-retention default claim |
| G08 | Atomic publication/retry/pinning design PASS; runtime/failure tests NOT RUN | Contract tồn tại nhưng runtime/control transactions/consumers chưa implement | Storage/orchestration implementer + DQ reviewer; Project Owner release approval | WWI-06 trước first normal Raw publication; advanced monitoring/failures WWI-10 | Ledger+membership+pointer coherent commit, pinning, durable outcome read-back, seven failure scenarios/retry/race/rollback/no partial visibility | Required runtime cases phải thực chạy PASS trước publish; RawPublished không Certified mart; no silent newer-pointer regression |


Khi runtime evidence còn thiếu, không ghi “logical approval missing” thay nguyên nhân thật. Design review phải nêu disposition/owner/gate cho physical details; runtime check chỉ PASS khi thực thi đúng môi trường. Certification thresholds/B1–B8 thuộc accepted DW-02 gates tiếp tục giữ, không tự chọn từ bảng này.

## 6. Narrow B9 PoC handoff — kế hoạch trước task Minimal Technical PoC (lịch sử)

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

## 7. Minimal Technical PoC — executed SQL→Python subset, 2026-11-15

Owner task mới authorize **project-local .venv + pyodbc==5.5.0** cho isolated PoC; override venv-location/install/“không thực thi” restrictions của prior planning milestone ở đúng scope này. Không authorize commit/push, PostgreSQL provisioning/writes/schema hoặc production pipeline. Section6 giữ kế hoạch lịch sử; không tự đánh dấu toàn B9-P01–06 hoặc G01–G08 DONE.

[PoC README](../../tests/integration/b9_precision/README.md) và [evidence section12](wwi-dw-03a-evidence-approval-readiness.md) ghi actual environment/commands/fixtures/results. CPython3.12.10, pyodbc5.5.0 trong ignored .venv, actual ODBC getinfo18.06.0002. Tám unit methods PASS; F2 giữ exact str/None cho 14 fixtures, 169 ordering pairs và 18 actual period cells. Không authoritative Python datetime, global package changes hoặc source writes.

B9-P01–03 chỉ **partial/scoped evidence** trên interactive sysadmin identity; G02 service account chưa verified. B9-P04 PG parameters BLOCKED vì chưa approved profile, không cài psycopg; persistence NOT RUN. B9-P05 Python/source ordering subset PASS, target/end-to-end predicates chưa test; B9-P06 bàn giao bounded report, không physical approval. Source consistency/full extraction G01, special adapters G06, physical Raw/retention G07 và atomicity/recovery G08 còn gate; G04/G05 chưa close.

Narrow PoC code đã Implemented/Tested, production ingestion/SCD2/Raw/pipeline vẫn **Not implemented yet**. A01–A06 approval levels không đổi; B9 Pending Physical Approval, DW-03A IN_PROGRESS, B/C/DW-04 TODO, WWI-04/Phase1 In Progress. Current task **không commit/push** hoặc bắt đầu DW-03B/C.

## 8. PostgreSQL task — installed dependencies, infrastructure stop

Current Owner **B9 PostgreSQL Transport & Persistence PoC** authorize reuse venv/install psycopg[binary]==3.3.9 và isolated official postgres:18 Docker sandbox/test-only TEXT table/bounded writes nếu Docker functioning; không cần xin lại sandbox-write approval đã cấp. Source code/fixtures/F2/architecture giữ nguyên; prior section7 “không authorize provisioning/writes” chỉ áp cho task source-only trước đây.

Actual psycopg3.3.9/psycopg-binary3.3.9 + required typing_extensions4.16.0/tzdata2026.6 cài/import thành công trong .venv; global Python không đổi. Docker CLI29.8.2 tồn tại nhưng info/ps không connect được `dockerDesktopLinuxEngine` named pipe. Không approved PG profile khác trong inspected scope. Theo explicit stop condition, **target tests BLOCKED/NOT RUN**, không tự start/reconfigure Docker hoặc pull/create/write/cleanup target.

[Evidence section13](wwi-dw-03a-evidence-approval-readiness.md) và [assessment section13](wwi-dw-03a-assessment.md) ghi actual commands/versions/blocker. Existing 8 unit tests và source regression14/169/18 PASS. PG server version/encoding/collation, parameter/persistence/order/range/occurrence/collision proof Unverified/NOT RUN, không lấy libpq version làm server evidence.

Để tiếp tục cần functioning Docker Linux Server hoặc approved PG sandbox profile; khi ready verify unique resource names/localhost-only port (prefer55433), secrets excluded, test-only TEXT/C-collation không là Raw schema, preserve resources sau tests theo current authorization. Target runner/target execution còn chưa hoàn tất. B9 Pending Physical Approval, DW-03A IN_PROGRESS, B/C/DW-04 TODO, WWI-04/Phase1 In Progress; không stage/commit/push.

## 9. Resume PostgreSQL PoC — bounded evidence verified

Docker engine29.8.2/linux và unique resources/port reverified trước create retail-b9-pg-poc/retail-b9-pg-poc-data tại127.0.0.1:55433. Existing unrelated volume không tác động. [Evidence section14](wwi-dw-03a-evidence-approval-readiness.md)/[assessment section14](wwi-dw-03a-assessment.md) ghi setup, metadata failure và successful retry.

F2/original fixtures không đổi.12 unit methods PASS; source14/169/18,PG parameters14/persisted15/new backend92→93,ordering169/equality14/range5/NULL/boundary/sentinel/shared occurrence PASS. PG18.7/UTF8/default en_US.utf8,test-only TEXT/C table; candidate không final Raw schema. Previous PG BLOCKED statements là history, current G04/G05 có bounded proof.

G01/G02/G06/G07/G08 còn gates; final datatype/adapter/encoding/collation/index/B9 approval và production acceptance chưa có. Restart/recreation/crash/production pipeline NOT RUN. Container/volume/rows retained,credentials/results ignored. B9 Pending Physical Approval,DW-03A/WWI-04/Phase1 IN_PROGRESS,B/C/DW-04 TODO; không stage/commit/push hoặc task tiếp.

## 10. Final design acceptance và DW-03B handoff

Owner instruction “DW-03A — B9 Physical Approval & Final Design Acceptance Review”,2026-11-15 cấp scoped B9 physical approval và quyền nghiệm thu có điều kiện nếu mandatory design criteria đủ. [Final assessment](wwi-dw-03a-assessment.md) section15 ghi14 design criteria PASS và G07 eight-point coverage; current table G01–G08 tách approved/verified design/PoC khỏi pending runtime, mỗi deferral có reason/owner/stage/evidence/gate.

**DW-03A DONE — Design.** Existing A03 storage objects/keys/manifests/lineage/replay/retention protection đủ để hướng dẫn implementation-specific physical proposal; không cần phát minh additional architectural approval. Không approve entire Raw DDL/index/access/capacity/retention periods hoặc claim runtime PASS. Khi chưa có retention/purge authorization và dependency/restore proof, không xóa evidence; đây là existing A03/Rule07 constraint, không đặt retention days.

B9 authoritative temporal contract tại [ADR-SCD-05](../adr/scd-05-exact-temporal-precision.md): F2→str/None→bound psycopg→TEXT, C comparison, exact27/seven digits/NULL/boundaries/sentinel/100ns; derived representations secondary. Source system-time không business-effective. B1–B8/A01–A06 giữ nguyên cấp.

DW-03B nhận approved full capture/base manifests/current-H/source origins/exact temporal field contract, consistency hold rule, replay identities và no-loss retention constraints. DW-03B vẫn cần Owner giao task riêng để chọn watermark/tie-breaker/delete/late/change scenarios; không tự bắt đầu vì dependency DW-03A DONE. DW-03C/DW-04 TODO; WWI-04/Phase1 IN_PROGRESS. Chỉ focused finalization commit sau actual tests/QA/staged checks PASS; không push hoặc production implementation.
