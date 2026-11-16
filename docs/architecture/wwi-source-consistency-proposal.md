# WWI-05 / M1B — Source Consistency Options & Recommendation

**PROPOSED — PENDING PROJECT OWNER APPROVAL, 2026-11-16.** Chuyên biệt concrete proof/readiness plan cho A02/G01/RG01; không thay [DW-03A §3](../data-models/wwi-dw-03a-full-raw-design-proposal.md#3-a2--a02--source-consistency-options-matrix) hoặc [DW-03B consistent-source boundary](../data-models/wwi-dw-03b-incremental-design-proposal.md#approved-assurance-và-verified-consistent-source-boundary). [Identity](wwi-source-identity-proposal.md), [Owner actions](wwi-source-dba-owner-checklist.md), [assessment/evidence](wwi-m1b-assessment.md).

## 1. Approved boundary và quan sát

Hai candidates trong task là A verified static no-writes window và B separately approved verified consistent copy. Đây là concrete operational choices trong approved A02, không kiến trúc mới; recommendation chưa approve method/window/copy.

M1B metadata: source database writable; SNAPSHOT OFF,RCSI/CDC/CT=false. Source identity hiện tại admin không proof source static. Không inspect mọi writer/session/job hoặc tạo audit/config; không có source-owner attestation/no-writes proof/copy supplied. G01/RG01 vẫn BLOCKED/Pending; không giả có LSN/snapshot token từ SYSUTCDATETIME hoặc local capture ID.

Boundary C phải ghi original/copy identity, restore/generation lineage, declared source scope và projection/contract/canonicalization revisions, capture identity, observation interval và proof references. Source S_C gồm toàn eligible rows trong same verified boundary; current và physical H separate streams, source measures/NULL/100ns/multiplicity giữ nguyên. Metadata-only queries M1B không tạo C đủ để normal publish.

## 2. Candidate evaluation

| Aspect | A — Verified static no-writes window | B — Approved consistent database copy |
| --- | --- | --- |
| Preconditions | SO/DBA kiểm soát được mọi source writers cho entire scope/window; drain in-flight writes trước T0; approved extractor identity | DBA/PO duyệt independent SQL Server copy/restore method, provenance, edition/capability/license/capacity và access; original không bị task sửa |
| Source-owner evidence | Complete writer inventory/controls, actor/time/window attestations và existing corroborating evidence; thiếu coverage giữ blocked | Copy origin/generation, engine-consistent backup/restore/validation records, recovery completion và protection khỏi copy writers |
| Consistent boundary | T0 sau writer drain; controls giữ tới T1 sau source bounds/reads/current+H/counts/key/value/multiset reconciliation cuối cùng | Source-backed recovered committed state của approved copy; reads+source reconciliation trên copy đã cố định; không so copy với live original khác thời điểm |
| Extractor behavior | SELECT-only, bounded/paged theo physical design được duyệt sau; không tự pause services/change source settings | SELECT-only vào exact separately approved copy endpoint/database; least-privilege rights tương ứng, không dùng original admin hoặc B9 |
| Verification | Writer controls primary proof + exact source↔Raw key/value/count/current-H multiset cùng interval; repeated counts/hashes chỉ corroboration | Verify copy provenance/state/role/source metadata/current-H/full fidelity và no-writer controls trên copy; reconcile same copy context |
| Failure cases | Writer/control coverage thiếu, in-flight transaction, late commit, history cleanup/maintenance/restore giữa window, controls release sớm | Logical export nhiều thời điểm, incomplete restore/wrong copy/generation, copy writer vẫn hoạt động, H thiếu/retention changed, old copy bị dùng làm live-current |
| Operational limits | Cần phối hợp source owner; cửa sổ dài qua full scans/reconciliation; không phù hợp khi writers không pause được | Thêm storage/setup/restore cost, copy lag; phải phê duyệt mọi creation/restore/security action riêng |
| Local portfolio suitability | Ưu tiên có điều kiện: ít hạ tầng mới nếu writer control thật sự đủ; không kết luận local restore mặc định static | Fallback khi không chứng minh A; tái lập tốt nếu provenance được tài liệu hóa nhưng không tự chọn method hoặc tạo clone |
| Current status | PROPOSED; actual verified window NOT RUN | PROPOSED alternative; approved copy/proof chưa có, creation NOT RUN |

Không lựa chọn NOLOCK/READ UNCOMMITTED, timestamp-only/static-count proof, per-table independent contexts hoặc temporal AS OF cho cả ordinary tables. Không enable SNAPSHOT/RCSI/CDC/CT, database read-only flag hoặc đổi configuration để “thực hiện A”.

## 3. Preferred method — PROPOSED A, conditional fallback B

**Đề xuất A** cho local portfolio, phù hợp ưu tiên conditional C2 đã ghi trong DW-03A: chỉ bắt đầu full capture sau PO/SO/DBA approve exact writer controls và window proof. M1B không khẳng định mọi writers có thể dừng; nếu không bao phủ được, recommendation chuyển sang **đề xuất B để review**, không automatic failover/copy creation. Nếu cả hai thiếu proof thì hold normal capture/publication claim theo G01, không downgrade guarantee.

A có lợi về phạm vi thay đổi hạ tầng so với chuẩn bị copy mới, **không là benchmark hiệu năng**. Full reconciliation vẫn full-read cost; không cam kết bắt mọi intermediate events hoặc business-effective history. B không được mặc định là database SNAPSHOT feature có trên Express, cũng không là bật SNAPSHOT isolation; concrete supported method cần DBA xác minh ở version/edition thực tế.

## 4. Proposed A proof plan — chưa thực hiện

| Step / test ID | Required proof / expected outcome | Responsible / status |
| --- | --- | --- |
| SW01 | Writer inventory: apps/importers/schedulers/scripts/manual DBA/maintenance/history-retention/restore/automation ở cả declared tables+dependency/H scope; chỉ “không chạy app” không đủ | SO/DBA; NOT RUN |
| SW02 | Approved window/action plan; mọi required writes quiesced bằng existing permitted operator controls, in-flight write transactions drained; no config change do AI | SO/DBA+PO; NOT RUN |
| SW03 | T0/context C ghi sau drain; exact scope/contracts/provenance/proof và actor attestation có revision; không giả native snapshot token | SO/IN/DQ; NOT RUN |
| SW04 | Controls giữ xuyên selecting bounds/extract current+H/count/key/value/multiset reconciliation; lúc nào required dependency reads còn chạy thì chưa release | SO/IN/DQ; NOT RUN |
| SW05 | Corroborate bằng existing evidence và source/current-H exact comparisons; matching counts/min-max timestamps/hashes không thay writer evidence hoặc per-key canonical checks | DQ/SO; NOT RUN |
| SW06 | Bất kỳ writer/control break/unverified interval/mismatch thì candidate không normal publish/ACK; giữ failed evidence, new context cần capture mới khi được phép | IN/DQ; NOT RUN |
| SW07 | T1 và cuối-window attestation sau source reconciliation; release writer controls chỉ theo authorized operator; restart/extension phải có proof mới đúng interval | SO/DBA; NOT RUN |

Đây là plan, không yêu cầu AI dừng writers, thêm tracing/audit hoặc khoá nguồn trong M1B. Catalog flags/read-only extractor, không thấy active writes trong một lần query hoặc grants thấp không chứng minh SW01–07. Missing evidence thì G01 không PASS.

## 5. Proposed B proof plan — chưa thực hiện

| Step / test ID | Required proof / expected outcome | Responsible / status |
| --- | --- | --- |
| CPY01 | PO/DBA duyệt copy method/provenance/license/capacity/security/action scope; chỉ approved SQL Server environment, không B9/PG target | PO/DBA; NOT RUN |
| CPY02 | DBA xác nhận engine-consistent committed restore/copy state và recovery thành công; cross-table logical exports không proven same-state bị từ chối | DBA; NOT RUN |
| CPY03 | Exact copy endpoint/database/profile/identity allowlist; full9 current+2 physical H hoặc approved dependency-complete slice; no extra copy writers | DBA/IN; NOT RUN |
| CPY04 | Origin/source generation/copy generation/cutover/contract scope được pin; backup identifiers/checkpoint/LSN chỉ ghi khi DBA cung cấp verified evidence | DBA/IN; NOT RUN |
| CPY05 | Validate schema/types/NULL/100ns/H multiset/key/value/source reconciliation trên cùng copy boundary, không đối chiếu live original ở lúc khác để claim sameness | IN/DQ; NOT RUN |
| CPY06 | New copy/restore giữa observations phải chứng minh compatible origin lineage hoặc approved rebaseline; không mất registry/forward evidence hay splice generations | IN/DW/DQ+PO; NOT RUN |

Copy actual preparation/restore và write protection là DBA/operator task riêng sau explicit approval. Không tạo copy trong M1B; target names/ports/backup location chưa chọn, backups/PII không vào Git. Copy phục vụ extraction không tự là writable DML sandbox để test INSERT/UPDATE/DELETE; test environment còn RG02 approval riêng.

## 6. Owner decision và acceptance gate

M1B-D03 chọn A hoặc B, M1B-D04 duyệt exact evidence/window/operator responsibilities, và M1B-D05 chỉ khi cần copy setup. Tất cả **PENDING OWNER/DBA APPROVAL**, xem [checklist](wwi-source-dba-owner-checklist.md). G01/RG01 chỉ đủ review PASS khi concrete approved method được thực hiện và có full interval/copy+reconciliation evidence đúng capture context. M1B planning completion không đóng gate, không tạo publication/checkpoint hoặc nhận source consistency operational PASS.
