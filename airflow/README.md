# Airflow — Retail Sales orchestration

**AIRFLOW_01_ACCEPTED — local supervised runtime, 2026-11-23.** Đã chạy một DAG end-to-end, đủ 8 tasks SUCCESS; 21 dbt models, 69 tests và run-start operation PASS. Không đồng nghĩa production readiness hoặc certified/source-consistent publication.

**AIRFLOW_02_ACCEPTED — controlled local recovery.** Owner đã cho phép dbt replacement trong phạm vi Sales được kiểm chứng. Đã phân loại lại toàn bộ DROP log, kiểm tra quyền/dependencies live chỉ đọc và thử lỗi DDL/recovery cô lập; không chạy thêm build live để lặp log cũ. Scheduling vẫn tắt. Phân biệt fixture/mocks, scheduler cô lập và recovery live ở phần dưới; không coi các lỗi mô phỏng là sự cố thật của WWI/PostgreSQL.

**AIRFLOW_03_READY — prepared, not enabled.** Đã chuẩn bị daily timetable có explicit parent/not-before và preview UUID; runtime vẫn manual, gate false, DAG paused. Không tạo scheduled run, không ingestion/build/BI refresh. Daily calendar chưa phải quyền ghi unattended nhiều ngày: mỗi interval vẫn phải được Owner pre-arm đúng parent/version/action.

## Môi trường đã xác minh

Ubuntu WSL2, kernel6.18.58.1; Airflow2.11.0 trong `~/airflow_env`, Python3.12.16. System Python3.14.4 không được dùng chạy Airflow. `airflow version`, `db check`, `pip check` PASS; `typing_extensions==4.13.2` không có Sentinel nhưng Airflow import/CLI thực tế không lỗi. Không nâng cấp hoặc cài lại package.

Executor SequentialExecutor; metadata SQLite `~/airflow/airflow.db`, tách biệt retail_raw. Đây là local development một DAG tuần tự, không production/HA. Giữ metadata hiện có, không migrate/reset. Không có Airflow Connections lúc discovery; không đưa password vào Connection/XCom. Quyền source/target vẫn do CLI và private profiles hiện hữu quản lý.

Theo [Airflow2.11 database docs](https://airflow.apache.org/docs/apache-airflow/2.11.0/howto/set-up-database.html), SQLite/SequentialExecutor chỉ dùng development. [Startup docs](https://airflow.apache.org/docs/apache-airflow/2.11.0/start.html) mô tả scheduler và webserver riêng. Không thêm Redis/Celery/Kubernetes.

## Chiến lược thực thi WSL → Windows

Source extractor hiện bắt buộc Windows Authentication/current Windows principal và ODBC18; WSL chưa có ODBC. Đã thử gọi trực tiếp `.venv/Scripts/python.exe` từ WSL bằng argument list/cwd cụ thể, không PowerShell/shell interpolation. Source preflight của sáu Sales objects PASS qua chính bridge này. SQL endpoint theo frozen existing source config, không tự thay named instance/DNS/IP hoặc auth.

Python Windows3.12.10, pyodbc5.5.0, psycopg3.3.9, dbt-core1.11.17/dbt-postgres1.11.0. Ingestion và dbt đều dùng project `.venv`; không cài chúng vào Airflow environment. Target hiện retail_raw/127.0.0.1:55434 từ **Windows worker**, retail_ingest/retail_transform theo nhiệm vụ. Không hiểu localhost WSL là cùng network path; WSL socket trực tiếp55434 thất bại không được che bằng đổi credentials.

`bridge.py` chạy trên WSL; `worker.py` chạy trên Windows. Profile paths tập trung trong `config.example.json`. Private runtime profile ở `~/.config/retail-airflow/config.json`, set `RETAIL_AIRFLOW_CONFIG` trong scheduler/webserver environment. Password không nằm trong profile bridge: worker tái sử dụng `.env` và `.local/dbt/connection.json` đã có ở Windows repository. Không in stdout/stderr tùy ý của drivers/CLI ra task logs; error type vàaction được báo an toàn. CLI error exit được propagate.

## Setup và startup đã thực hiện

Không sửa `airflow.cfg` hoặc xóa metadata. Tạo symlink không ghi đè `~/airflow/dags/retail_sales_incremental_pipeline.py` đến file cùng tên trong repository; symlink resolve về repository để import bridge. Khi setup máy khác, sửa bốn đường dẫn trong profile cho đúng checkout; Windows Python/worker path và WSL mount path là hai dạng riêng.

Chạy trong Ubuntu, từ repository WSL path:

```bash
mkdir -p ~/.config/retail-airflow ~/airflow/dags
# Chỉ copy khi config chưa tồn tại; giữ profile hiện có.
test -e ~/.config/retail-airflow/config.json || cp airflow/config.example.json ~/.config/retail-airflow/config.json
chmod 600 ~/.config/retail-airflow/config.json
# Chỉ tạo khi tên link chưa tồn tại; không dùng ln -sf.
test -e ~/airflow/dags/retail_sales_incremental_pipeline.py || ln -s "$PWD/airflow/dags/retail_sales_incremental_pipeline.py" ~/airflow/dags/retail_sales_incremental_pipeline.py
export RETAIL_AIRFLOW_CONFIG="$HOME/.config/retail-airflow/config.json"
~/airflow_env/bin/airflow version
~/airflow_env/bin/airflow db check
~/airflow_env/bin/airflow dags list-import-errors --output json
~/airflow_env/bin/python airflow/start_local.py --start
```

`start_local.py` kiểm metadata rồi start scheduler/webserver nếu chưa chạy; không tự initialize/reset DB. `--status` kiểm PID command, UID, process group, private config path và inherited schedule environment. PID/config khác thì dừng để inspect, không start duplicate. `--stop` yêu cầu gate/scope đóng, DAG paused, không active/queued runs; chỉ SIGTERM đúng hai PID đã xác minh, không force-kill. Startup cũng yêu cầu trạng thái idle này. Webserver bind127.0.0.1:8080; service logs/PIDs ở `~/airflow/retail-service-logs`. Dùng Airflow user hiện có, không tạo/đổi password UI.

Launcher đặt airflow_env/bin đầu PATH cho service và task subprocesses. SequentialExecutor gọi lệnh `airflow` không có đường dẫn tuyệt đối; thiếu PATH này khiến scheduler dừng lúc task đầu được queued. Đã bổ sung regression cho inherited PATH, không sửa system PATH hoặc cài lại Airflow. Nếu lỗi này xảy ra trước ingestion: kiểm candidate chưa tồn tại, khởi động scheduler với PATH đúng; giữ nguyên run ID và để orphan handling tiếp tục, không tạo batch mới hoặc clear write task mù.

WSL must remain running for these local services. Nếu cài mới trên máy khác cần Airflow release/Python hỗ trợ và official version-specific constraints trong venv riêng; không chạy lệnh reinstall trên environment đang hoạt động. Task này reuse installation đã kiểm chứng, không thêm dependency root.

## DAG và read-version contract

`retail_sales_incremental_pipeline`: mặc định schedule=None, catchup=False, max_active_runs=1, timezone Asia/Ho_Chi_Minh, paused khi tạo. Optional daily dùng CronTriggerTimetable, explicit future not-before; không historical backfill. DAG parse chỉ đọc bốn non-secret environment settings, không đọc private profile/secrets hoặc kết nối DB. Chuỗi tám task:

```text
preflight_source → preflight_target → run_incremental_ingestion
→ validate_ingestion_batch → resolve_dbt_read_version → run_dbt_build
→ validate_sales_marts → pipeline_complete
```

Manual conf bắt buộc `parent_version` canonical UUID. Mỗi Airflow run_id ánh xạ deterministic uuid5 thành version mới; đây chỉ là naming cho UUID của ledger hiện có, không thêm capture table/checkpoint song song. XCom chỉ cóaction/status/parent/version; không records/DataFrame.

Scheduled run không có manual conf thì dùng explicit `RETAIL_AIRFLOW_SCHEDULE_PARENT`. Sau source task, parent được giữ từ verified upstream handoff; thay environment sau đó không âm thầm đổi parent của run đang recovery. Không chọn latest, tự advance parent/checkpoint hoặc đổi read-version pin BI.

- Source: existing SqlServerSource.preflight đúng sáu Sales dependencies, SELECT-only.
- Target: existing IncrementalTarget.preflight vàassert_version(parent), không tự chọn latest.
- Ingestion: `python -m ingestion.incremental run --parent-id P --version-id V --execute`. Chỉ nhận VALIDATED_UNPUBLISHED_CANDIDATE hoặc ALREADY_VALIDATED_NO_REEXTRACTION cho đúngV.
- Validate: kiểm PostgreSQL durable status VALIDATED, parent, contract_hash, algorithm, đủscope vàACK=NULL; chạy existing `incremental reconcile --version-id V`.
- Resolve: lặp durable gate, chỉ trả chínhV, không fallback parent/old capture.
- dbt: `python dbt/run_dbt.py build --input-kind INCREMENTAL --capture-id V`, giữ toàn Sales graph. Kiểm execution receipt đúngV/command/input_kind, đúng private invocation run_results códata tests vàmọi model/test success/pass; không chỉ tin exit0.
- Marts: SELECT-only kiểm năm marts không rỗng, chỉ `_capture_id=V`; Sales/invoice totals đối soát independent core fact totals. dbt data tests giữbusiness/DQ/grain/fidelity gates, không thay bằng count-only.
- Complete: kiểm lại durable version vàmart gate. Không đổi publication pointer/ACK, không refresh Power BI.

Change/no-change đều có candidate version VALIDATED theo engine hiện có. No-change giữevents/payload writes0 nhưngversion mới vẫn làread inputV của dbt. Failed/RUNNING UUID không được tái dùng đểextract lại. Full parent đượcexisting guard admit nhưng **dbt của DAG này chỉ đọc incrementalV**, không tráo run_id/capture metadata.

## Safety preflight và trigger

Private profile mặc định `allow_pipeline_writes=false`, `write_scope=null`; trả về trạng thái đóng sau mỗi lần vận hành. Trước supervised run: xác minh source/target identity/TLS/privileges, capture/ledger/checkpoint/pointer baseline, parent validated/contract/depth, không CLI/dbt khác đang chạy, Docker healthy và các preflight PASS. Xác định write scope: six Raw delta payloads, incremental events/version ledger và schemas transform sở hữu dw_staging/dw_intermediate/dw_core/sales_marts/dq; không WWI source, Raw publication hoặc BI.

Chỉ bật boolean không còn đủ quyền. Scope private phải khớp **parent + version + actions** của lần được phép. Tính version bằng `bridge.version_for_run(run_id)` trước khi trigger, không dùng UUID ngẫu nhiên thay thế. Ví dụ cấu trúc (thay placeholders bằng UUID đã kiểm chứng; không chạy nguyên mẫu):

```json
{
  "allow_pipeline_writes": true,
  "write_scope": {
    "parent": "<validated-parent-uuid>",
    "version": "<uuid-derived-from-exact-run-id>",
    "actions": ["ingest", "build"]
  }
}
```

Recovery chỉ rebuild thì `actions=["build"]`; bridge và worker đều kiểm scope trước gọi CLI. Owner cho phép CREATE/RENAME/GRANT và DROP phục vụ replacement đúng các Sales models ở phần controlled DDL bên dưới. Không cho scope wildcard hoặc áp dụng một scope cho nhiều version. Gate không cấp quyền DROP Raw/metadata hoặc đối tượng ngoài phạm vi, không thay SQL least privilege hoặc bảo vệ private profile/repository.

Sau khi các gates thực tế PASS, operator bật write gate trong profile private vàtrigger:

```bash
~/airflow_env/bin/airflow dags unpause retail_sales_incremental_pipeline
~/airflow_env/bin/airflow dags trigger retail_sales_incremental_pipeline \
  --run-id manual__supervised_01 \
  --conf '{"parent_version":"<validated-parent-uuid>"}'
~/airflow_env/bin/airflow dags list-runs -d retail_sales_incremental_pipeline
```

Đã thực thi một supervised trigger sau khi source/target preflight, dbt debug/compile và baseline checks PASS. Write gate đã trả false và DAG đã pause sau validation. Các lệnh trigger trên chỉ dành cho lần được phép tiếp theo; interlock không thay quyền bảo vệ local profile/repository.

## Retry, rerun, failure

| Task | Retry tự động | Điều kiện và xử lý |
|---|---:|---|
| preflight_source / preflight_target | 1, sau 30 giây | Chỉ lỗi transport được nhận diện, như connection refused/timeout. Auth/certificate, permissions, cấu hình/handoff sai dừng bằng AirflowFailException, không retry. |
| run_incremental_ingestion | 0 | Có durable idempotency nhưng lỗi giữa transaction/unknown COMMIT cần inspect; không tự chạy lại nguồn. |
| run_dbt_build | 0 | Rebuild từng model chưa atomic cho toàn graph; phải xác minh cùng read version và partial output trước manual clear. |
| validate / resolve / marts / complete | 0 | Sai eligibility, digest, grain, test hoặc version cần xử lý nguyên nhân. Nếu chỉ mất kết nối: sau khi kết nối hồi phục, manual clear đúng phần đọc bị lỗi. |

Default `all_success` giữ mọi downstream không thực thi khi upstream fail; leaf không dùng `all_done` để che lỗi. Same run giữ UUID deterministic; một run mới cùng parent tạo UUID mới, không được gọi là retry cùng ingestion identity. Existing VALIDATED V chỉ reconcile/read-back, không re-extract; parent/contract/algorithm/scope phải đúng. FAILED/RUNNING/unknown COMMIT không được ghi đè hoặc reset checkpoint: kiểm ledger và Windows child trước; fresh extraction cần **new DAG run_id**, explicit validated parent và scope riêng.

Quy trình rerun phần dbt:

1. Pause DAG; xem đúng run ID, task states, native logs và ledger. Kiểm tra không còn Windows child, CLI hoặc run khác đang hoạt động. Không suy kết quả COMMIT từ task timeout.
2. Giữ nguyên run ID/conf/parent; xác minh V vẫn VALIDATED, đủ sáu nguồn, contract/algorithm khớp, ACK=NULL. Đối soát baseline Raw/current-state, serving counts/digests/KPI và pin BI.
3. Trong Grid chọn đúng run và ba task `run_dbt_build`, `validate_sales_marts`, `pipeline_complete`; clear cả failed/upstream_failed, không chọn upstream/past/future. Năm upstream đã SUCCESS được giữ nguyên. Không mark success thủ công.
4. Nếu dùng CLI, lấy **logical date chính xác** từ run rồi dùng `airflow tasks clear -s "$LOGICAL_DATE" -e "$LOGICAL_DATE" -t '^(run_dbt_build|validate_sales_marts|pipeline_complete)$' retail_sales_incremental_pipeline`; review danh sách đúng ba task trước xác nhận. Không dùng chỉ ngày khi cùng ngày có nhiều run.
5. Theo phạm vi replacement đã được Owner phê duyệt: mở scope `build` cho đúng P/V rồi unpause DAG manual. Pre-build DDL gate phải PASS; nếu có artifact/dependency ngoài dự kiến thì dừng và inspect, không sửa gate để chạy qua. dbt kiểm eligibility lại trước CLI và dùng đúng V; không clear ingestion. Chỉ hoàn tất sau execution receipt và mọi model/data test PASS, mart reconciliation PASS.
6. Đóng gate, xóa scope hoặc đặt null, pause DAG; so sánh baseline và giữ logs. Không refresh Power BI tự động. Nếu output/receipt/mart mismatch: giữ failure, không fallback capture cũ hoặc tự chạy cả DAG.

Timeout của bridge/worker được báofailure; Windows interopchild có thể còn chạy sau WSLtasktimeout. Không tự kill/retry/createbatch; inspectWindows processes vàdurableversion, đợi/cancel cókiểm soát trước rerun. max_active_runs=1 chỉserializeDAG này; external CLI hoặcDAG khác vẫn cần operator coordination. Existing ingestion/dbt advisory locks vẫn làguard từngengine, khôngglobalatomicpublication. AirflowSQLite sequential chỉ phù hợp localsingleDAG; không HA hoặcdistributedexecutor.

Lock ingestion `941061` chặn writer Full/Incremental khác; lock dbt `941062` chặn transform CLI khác, kể cả ngoài Airflow. Đây là hai locks độc lập, không phải mutex chung cho cả pipeline. Trong recovery live đã giữ ingestion lock trong khi rebuild. Không có atomic publication cho toàn graph, không cho BI refresh trong khoảng rebuild; version guard vẫn bắt mixed/stale versions. Scheduler serialization không thay các locks hoặc chứng minh coherent source snapshot.

## Logs và quan sát

UI Grid/Graph hiển thị run/task/state/attempt/start/end/duration; native task logs ở `~/airflow/logs/dag_id=retail_sales_incremental_pipeline/run_id=<run-id>/task_id=<task-id>/attempt=<n>.log`. Có thể dùng `airflow dags list-runs -d retail_sales_incremental_pipeline` và `airflow tasks states-for-dag-run retail_sales_incremental_pipeline '<run-id>' --output json` để xem states.

Các dòng JSON `retail_stage_start`, `retail_stage_failed`, `retail_stage_success` ghi run_id/task_id/attempt/action/parent/version. Ingestion trả durable status; build thành công thêm dbt_invocation/dbt_command/dbt_exit_code. Đối chiếu invocation với `.local/dbt/invocations/<id>/execution.json` và target/run_results.json; CLI lỗi có command exit code và category được lọc. `READ_VERSION_*`, `DBT_RECEIPT_VERSION_MISMATCH`, `DBT_DATA_TESTS_MISSING`, `MART_*`, unknown COMMIT và timeout không được coi transient để retry ghi. Không relay driver stdout/stderr, exception chứa DSN hoặc credentials; logs không có passwords. XCom chỉ chứa handoff/receipt nhỏ, không chứa dữ liệu nguồn.

## Kiểm tra và trạng thái

Airflow runtime import đủ 8 tasks, discovery, no import errors, metadata/pip checks và UI health PASS. Bộ regression có 17 Airflow tests, ngoài các bộ ingestion/dbt/infrastructure hiện hữu. Failure/receipt/version tests dùng mocks hoặc fixtures, không giả network chaos hoặc source mutation proof.

Source/target preflight từ WSL bridge và dbt debug/compile chỉ đọc PASS. Đã chạy incremental ingestion và dbt build qua supervised DAG; không Full Load/source writes/publication. No-change run và same-ID durable readback đã test thật; INSERT/UPDATE/DELETE/failure cases vẫn là offline/fixture.

Troubleshooting: source Windows auth/ODBC/TLS fail thìdừng, khôngfallbackSQLlogin/trust; targettimeout kiểmDocker trước, khôngprunevolume; DAGnotfound kiểmsymlink/resolvedpath; writegatedisabled khôngbật trướclevel2; dbtfailed khôngchọnolderversion; warnings/testskip khôngđượccoi fullbuildPASS. Logs/errors vàrunUUIDs ởAirflowtasklogs, temporaryevidence ởignored.local/airflow-01. PowerBI vẫnmanualImport/Refresh, khôngsửareport.

## Runtime đã xác minh

- Run `manual__airflow01_20261123T061320Z`; candidate `3a2f011d-f3b3-5683-83a2-a64837720f3d`, parent `c825b18e-fc62-4cf1-8837-b37b4c9f9668`. Candidate VALIDATED, depth 3, ACK=NULL. Tám task SUCCESS; không fallback phiên bản cũ.
- Quét 604672 rows: tất cả UNCHANGED, INSERT/UPDATE/DELETE=0. Không thêm delta payload/events. Chỉ thêm một incremental version; runs/object_runs/load_contracts/load_audits/incremental_events/raw_current/raw_publications giữ nguyên count và content hash so baseline.
- dbt invocation `87a1ee86-1c6b-41c0-874a-794fed249c05`: 21 models, 69 tests, một run-start operation PASS. Cả năm marts chỉ có version mới, row counts giữ nguyên. Sales 172261341.20; Tax 25782098.25; IncludingTax 198043439.45; Units 8950628; Invoices 70510; Orders 73595 giữ nguyên và đối soát PASS.
- Gọi lại CLI cùng V/P trả ALREADY_VALIDATED_NO_REEXTRACTION; metadata toàn bộ không đổi. Đây là engine readback, không phải clear/retry Airflow write task hoặc DAG run thứ hai.
- Container cũ không start do bind `storage/raw/bootstrap.sql` mất sau refactor. Dùng script hiện hữu `infrastructure/scripts/ensure_raw_bind.ps1 -Apply` khôi phục junction đến canonical infrastructure/postgres; start đúng container ID9fd7b79b và volume retail-raw_pg_data, không recreate/reset/migration/bootstrap.
- Scheduler gặp PATH thiếu airflow khi task đầu queued. Sau sửa launcher và restart, scheduler tiếp tục cùng run; không clear task, không tạo batch mới. Regression kiểm inherited PATH đã được bổ sung.
- Gate private false, DAG paused; scheduler/webserver giữ chạy. Temporary evidence ở ignored .local/airflow-01, không commit logs/private profiles.

AIRFLOW-01 không auto-refresh hoặc đổi pin Power BI. Bước POWERBI-VERSION-SYNC-01 sau đó đã xác minh và đồng bộ sáu import guards với serving version 3a2f011d-f3b3-5683-83a2-a64837720f3d; refresh, SQL/DAX reconciliation và render tám trang đã kiểm chứng. Các lần chạy Airflow tiếp theo vẫn cần review/đồng bộ pin riêng trước refresh; không bỏ guard hoặc fallback latest.

## Reliability đã kiểm chứng — AIRFLOW-02

| Scenario | Phương pháp | Kết quả và giới hạn |
|---|---|---|
| 01 SQL Server unavailable | ISOLATED transport + Airflow/mock bridge | ODBC kết nối loopback port đóng thất bại; DAG thử preflight hai lần rồi FAILED, downstream upstream_failed, không ingestion/dbt. Không tắt WWI thật. |
| 02 PostgreSQL unavailable | ISOLATED transport + Airflow/mock bridge | psycopg kết nối loopback port đóng thất bại; target task FAILED, các task ghi không chạy. Không tắt container thật. |
| 03 Ingestion failure | ISOLATED PostgreSQL fixture + Airflow/mock bridge | 69 fixture checks: rollback events/payload, FAILED ledger giữ lại, same failed UUID bị từ chối, recovery UUID mới và no-change đúng. Fixture chỉ dưới prefix riêng trong dbt_sales_test, không production Raw. |
| 04 dbt failure | MOCK CLI/receipt + ISOLATED Airflow | Lỗi dbt chặn marts/complete; receipt sai version hoặc thiếu/failed data tests bị từ chối. Clear ba task cuối không gọi lại ingestion. Recovery live bên dưới dùng gate failure trước CLI, không tuyên bố đã làm dbt thật hỏng. |
| 05 Repeat/retry/clear | ISOLATED + LIVE readback/recovery | Same VALIDATED UUID thực tế trả ALREADY_VALIDATED_NO_REEXTRACTION, đủ sáu reconciliation; clear/rerun tail giữ nguyên P/V và upstream. New run ID khác UUID. |
| 06 No change | REUSE accepted LIVE evidence + ISOLATED fixture | V hiện tại có 604672 UNCHANGED, INSERT/UPDATE/DELETE=0; ledger/reconciliation kiểm lại. Không quét thêm source snapshot chỉ để lặp kết quả AIRFLOW-01. |
| 07 Concurrent runs | ISOLATED real scheduler + LIVE DB locks | Hai run được submit queued cùng lúc; max observed running=1, run sau bắt đầu sau khi run trước kết thúc. Fixture worker không gọi source/target thật, gate đóng nên cả hai dừng ở ingestion. Trên target thật, giữ từng advisory lock khiến CLI ingestion/dbt ngoài Airflow bị từ chối trước ghi. |
| 08 Invalid read version | MOCK + ISOLATED + LIVE SELECT guard | Unknown UUID thật bị READ_VERSION_NOT_ELIGIBLE; unvalidated/failed/missing metadata và version mismatch kiểm bằng doubles. CLI dbt không chạy, không fallback input khác. Không tạo metadata lỗi trong production để thử. |

Recovery live dùng lại `manual__airflow01_20261123T061320Z`, V=`3a2f011d-f3b3-5683-83a2-a64837720f3d`. Clear đúng ba tail tasks khi gate false: build FAILED, hai downstream upstream_failed. Sau đó scope chỉ `build` đúng P/V và ingestion lock được giữ; clear/rerun ba task này thành SUCCESS. dbt invocation `b1d4595c-3f03-4785-8357-af8383db0704`: 21 models, 69 tests, một operation PASS. Build đến attempt 3; năm task upstream giữ nguyên try/start/end/duration. Không tạo DAG run hoặc ingestion candidate mới.

Before/after: count và SHA256 của tám metadata tables giữ nguyên; Raw base/delta/current-state counts và content digests của toàn bộ serving tables giữ nguyên; Sales 172261341.20, Tax 25782098.25, IncludingTax 198043439.45, Units 8950628, Invoices 70510, Orders 73595 giữ nguyên. Hash file Power BI, pin V, publication/checkpoint không đổi. Source chỉ SELECT, không refresh BI. Scope/profile được khôi phục, gate false, DAG paused, schedule=None; scheduler/UI vẫn healthy.

Kết quả đếm DROP trước đây đã được sửa: **42 dòng khớp pattern gồm 21 câu SQL và 21 dòng SQL status**, không phải 42 câu SQL. SQL thực tế có 19 DROP TABLE và 2 DROP VIEW, đều hậu tố `__dbt_backup`, không có TRUNCATE hoặc DROP nhắm canonical name/Raw/metadata. Quyết định Owner mới cho phép replacement có kiểm soát; không xóa lịch sử sai lệch hoặc tự coi mọi tên backup là hợp lệ. Phân loại đầy đủ, số dòng và hash log ở ignored `.local/airflow-02/finalize/drop-classification.json`; mỗi dòng status được liên kết đúng câu SQL, không tính thành lần DROP nữa.

## Controlled dbt DDL

Database duy nhất `retail_raw`; 21 models dưới đây là allowlist. Full target của từng DROP là `retail_raw.<schema>.<model>__dbt_backup`. T = table, V = view. Từng table có bằng chứng old→backup rename, intermediate→canonical rename, COMMIT và DROP acknowledgement. Hai view-backup không được tạo/rename trong trace: no-op được **suy luận từ trace đầy đủ và adapter lifecycle**, không suy từ riêng command tag DROP VIEW.

| Schema | Model | Materialization | Backup tồn tại / bị xóa |
|---|---|---|---|
| dw_staging | stg_sales_customers | T | Có / Có |
| dw_staging | stg_sales_invoicelines | T | Có / Có |
| dw_staging | stg_sales_invoices | T | Có / Có |
| dw_staging | stg_sales_orderlines | T | Có / Có |
| dw_staging | stg_sales_orders | T | Có / Có |
| dw_staging | stg_warehouse_stockitems | T | Có / Có |
| dw_core | dim_date | T | Có / Có |
| dq | validation_violations | T | Có / Có |
| dq | record_status | T | Có / Có |
| dw_core | dim_customer | T | Có / Có |
| dw_core | dim_product | T | Có / Có |
| dw_intermediate | int_invoice_header | V | Không / Không — suy luận |
| dw_intermediate | int_order_header | V | Không / Không — suy luận |
| dq | quarantine_records | T | Có / Có |
| dw_core | fact_invoice_line | T | Có / Có |
| dw_core | fact_order_line | T | Có / Có |
| sales_marts | mart_customer_sales | T | Có / Có |
| sales_marts | mart_sales_daily | T | Có / Có |
| sales_marts | mart_sales_product_daily | T | Có / Có |
| sales_marts | mart_sales_customer_summary | T | Có / Có |
| sales_marts | mart_sales_monthly | T | Có / Có |

Các macro dbt đang cài tạo intermediate, rename old→backup/new→canonical, áp grants và COMMIT, sau đó DROP backup ngoài transaction model. Cả 21 SQL có CASCADE. Khi staging invoices/orders được thay bảng, view headers cũ vẫn trỏ OID của bảng đã rename; CASCADE xóa hai view này. Graph dbt sau đó tạo lại đúng headers và áp SELECT grants. Đây là hai collateral objects thuộc allowlist, không phải bằng chứng CASCADE luôn an toàn. Không có temporary target nào bị DROP trong trace này; intermediate được rename thành canonical.

Cho phép replacement/cleanup đúng model, intermediate và backup tương ứng; giữ materialization table/view đã kiểm chứng. Cấm DROP/DML/DDL lên Raw, ingestion_meta, capture/checkpoint/publication, SQL Server, public hoặc schema/objects ngoài graph Sales. Cấm arbitrary CASCADE và tự cleanup artifact lạ. Quyền `retail_transform` không có superuser/CREATEDB/CREATEROLE/REPLICATION/BYPASSRLS; không sở hữu hoặc có CREATE/DML trên raw/ingestion_meta. Không tăng quyền để khắc phục lỗi.

`dbt/ddl_policy.py` là SELECT-only pre-build check cụ thể cho graph này, chạy trong `execute.py` sau khi giữ lock 941062 và validate read version, trước spawn dbt run/build. Check model paths/schema/alias, owner/kind, quyền bảo vệ Raw/meta, orphan tmp/backup, normal dependencies cả relation/row-type và custom triggers/RLS. Chỉ chấp nhận dependent views là hai headers đã biết; consumer khác, FK/function hay artifact còn sót làm fail closed bằng `DDL_*`. Gate live đã PASS: 21 relations, hai dependent views. Không có privileged GRANT mới hoặc framework security tổng quát.

Quy trình này yêu cầu repository đã review và **không có DDL/admin process khác** trong cửa sổ build. Advisory lock chặn CLI tương ứng, không khóa mọi DBA. Gate không phải SQL firewall chống mã SQL/hook độc hại; thay model, macro, alias/schema, dependency hoặc quyền phải review lại. Không auto-refresh BI trong lúc graph đang rebuild; graph chưa atomic và hai views có thể tạm vắng.

## DDL failure/recovery đã thử

20 cases PostgreSQL cô lập, không phải build live mới: table và view ở before CREATE, sau CREATE, sau rename thứ nhất/thứ hai, sau GRANT, trước COMMIT, lost-COMMIT-ack simulation, cleanup failure và success; thêm unapproved view và row-type function consumers. Bằng chứng `.local/airflow-02/finalize/ddl-fixtures.json`. Schema test riêng được tạo vì transform không có TEMP privilege; không tăng quyền TEMP. Mọi fixture được xóa bằng danh sách tên cụ thể và schema rỗng được DROP RESTRICT; không dùng DROP SCHEMA CASCADE.

- Lỗi trước COMMIT: PostgreSQL rollback khôi phục old names/data/SELECT grants/view dependency; không còn tmp/backup. Same-input rerun sau rollback đã thành công.
- COMMIT đã thành công nhưng ack/cleanup lỗi: canonical mới vẫn tồn tại, backup còn và view có thể vẫn đọc backup cũ. **Không rollback giả định, không re-extract**. Gate chặn blind rerun bằng DDL_STALE_ARTIFACT_INSPECT_BEFORE_RERUN.
- Recovery fixture sau COMMIT: kiểm tra data/version/grants của canonical và backup; rebind đúng managed header view tới canonical, sau đó DROP backup RESTRICT. Kiểm tra không còn artifacts và quyền/giá trị đúng rồi mới cho rerun graph cùng V. Nếu có consumer lạ hoặc chưa xác minh trạng thái thì giữ gate đóng.
- Positive control trong sandbox xác nhận CASCADE thực sự có thể xóa consumer ngoài model; DDL gate đã từ chối trước khi DROP. Row-type function dependency cũng bị chặn. Không thử destructive failure trên Sales đang phục vụ.

Live read-only sau kiểm thử: cả 12 BI objects đúng V, owner retail_transform, retail_bi_reader SELECT thật qua chính login; không DML/admin/schema CREATE hoặc SELECT ngoài allowlist. Hai headers tồn tại đúng row counts; không có orphan tmp/backup. Raw/current-state counts, tám metadata digests, serving data digests, KPI và toàn bộ file Power BI khớp baseline. dbt compile đọc-only PASS; model SQL/dependencies/grants không đổi. Gate vẫn false, DAG paused, schedule=None. Không chạy ingestion, live dbt build hay refresh Power BI trong FINALIZE.

Tái kiểm tra offline từ Windows: `.venv\Scripts\python.exe scripts/run_checks.py`. Trên WSL dùng Python Airflow hiện có:

```bash
~/airflow_env/bin/python airflow/tests/reliability_runtime.py --execute-isolated --output .local/airflow-02/isolated
```

Harness dùng DAG/operators hiện hữu, Airflow home/SQLite tạm riêng và fixture worker, không chạy trên metadata hoặc databases vận hành. Retry delay chỉ được rút xuống 1ms trong test in-process; production vẫn 30 giây. PostgreSQL fixture có thể chạy riêng bằng `.venv\Scripts\python.exe tests/integration/incremental_runtime.py --execute` sau khi kiểm tra target/scope; giữ prefix fixture để inspect, không DROP/TRUNCATE. Runtime evidence tại ignored `.local/airflow-02/`, native Airflow logs và ingestion ledger; không tạo audit database/report hay milestone Markdown mới.

## AIRFLOW-03 — vận hành local

Windows SQL Server SQLEXPRESS đang Running/Auto. Docker Desktop cần Linux Engine desktop-linux; container Raw có restart policy `no`, nên Owner khởi động lại container hiện hữu sau Engine/Windows restart. WSL có systemd=true nhưng hai Airflow processes hiện do launcher thủ công quản lý; không cài thêm Windows Task Scheduler/systemd units hoặc auto-start jobs trong milestone này. Windows logon/current principal phải dùng đúng context Windows Authentication đã duyệt.

PowerShell tại repository:

```powershell
docker context show
docker info --format '{{.OSType}}'
docker inspect retail-raw-postgres-1 --format '{{.Config.Image}} {{json .Mounts}} {{json .HostConfig.PortBindings}}'
# Chỉ sau khi xác minh postgres:18, retail-raw_pg_data và localhost:55434 đúng:
docker start retail-raw-postgres-1
docker inspect retail-raw-postgres-1 --format '{{.State.Health.Status}}'
wsl -d Ubuntu
```

Trong Ubuntu:

```bash
cd /mnt/d/Code/Retail_Data_Platform/project1_Retail_Data_platform
export RETAIL_AIRFLOW_CONFIG="$HOME/.config/retail-airflow/config.json"
export RETAIL_AIRFLOW_SCHEDULE=manual
unset RETAIL_AIRFLOW_DAILY_TIME RETAIL_AIRFLOW_SCHEDULE_PARENT RETAIL_AIRFLOW_SCHEDULE_NOT_BEFORE
~/airflow_env/bin/python airflow/start_local.py --status
~/airflow_env/bin/python airflow/start_local.py --start
curl --fail http://127.0.0.1:8080/health
~/airflow_env/bin/airflow dags list-import-errors --output json
~/airflow_env/bin/airflow dags list-runs -d retail_sales_incremental_pipeline
```

UI: http://localhost:8080, dùng account hiện có. `--start` giữ nguyên PID nếu đúng identity/config; schedule environment chỉ áp dụng khi process khởi động, vì vậy đổi mode cần pause/drain/stop/start. Nếu reboot để lại gate true hoặc DAG unpaused, đóng gate/pause qua CLI trước startup; không ép launcher chạy qua idle guard. Restart thực tế sau reboot và shutdown live **NOT_RUN** trong AIRFLOW-03; đã kiểm proc/config hiện hành, idle/foreign-PID guards bằng regression và idempotent startup live không spawn process mới.

Manual trigger vẫn dùng explicit conf/scope theo phần Safety preflight. Manual run không nhận parent default của daily. Muốn dừng: pause DAG, đợi active runs/Windows children kết thúc, đóng gate/scope rồi `~/airflow_env/bin/python airflow/start_local.py --stop`. Helper không kill Windows interop children; timeout/unknown COMMIT phải inspect durable state trước. Chỉ khi mọi CLI/BI refresh đã idle mới dừng riêng Raw bằng `docker stop --time 30 retail-raw-postgres-1`; giữ container/volume để `docker start` sau này. Không cần dừng SQL Server/native PostgreSQL/B9.

### Chuẩn bị và bật daily — chỉ Owner thực hiện sau milestone

| Environment | Giá trị |
|---|---|
| RETAIL_AIRFLOW_SCHEDULE | manual (default) hoặc daily |
| RETAIL_AIRFLOW_DAILY_TIME | HH:MM, default 02:00, Asia/Ho_Chi_Minh |
| RETAIL_AIRFLOW_SCHEDULE_PARENT | Canonical UUID đã VALIDATED, bắt buộc khi daily |
| RETAIL_AIRFLOW_SCHEDULE_NOT_BEFORE | Future timestamp +07:00 đúng daily boundary, bắt buộc khi daily |

Daily dùng trigger timetable, data interval là một điểm; không đổi thành date filter/extraction window. catchup=False không tạo mọi ngày lịch sử; sau downtime có thể có kỳ gần nhất, scope cũ vẫn chặn UUID khác. Không unpause với plan hết hạn. `is_paused_upon_creation` chỉ áp dụng DAG mới, không tự pause DAG cũ sau reboot.

Not-before cũng là start_date của daily DAG/tasks. Muốn recovery một run cũ hơn boundary này (ví dụ run manual AIRFLOW-01), chuyển về manual theo quy trình pause/drain/restart trước khi clear; giữ nguyên run ID/conf/P/V. Không lùi not-before hoặc bật catchup để ép chạy lịch sử.

**Các lệnh dưới đây chưa được chạy để enable trong AIRFLOW-03.** Trước hết DAG phải paused, không active/queued/Windows child, gate false/scope null, source/target và DDL gates PASS. Planner chỉ tạo preview và file exports, không đọc SQL hoặc mở gate. Thay PARENT bằng version thực tế đã kiểm chứng trước mỗi lần:

```bash
PARENT=3a2f011d-f3b3-5683-83a2-a64837720f3d
export RETAIL_OWNER_PLAN=".local/airflow-03/owner-$(date +%Y%m%dT%H%M%S).json"
ENV_PLAN="${RETAIL_OWNER_PLAN%.json}.env"
~/airflow_env/bin/python airflow/schedule_local.py --parent "$PARENT" --daily-time 02:00 \
  --output "$RETAIL_OWNER_PLAN" --env-output "$ENV_PLAN"
cat "$RETAIL_OWNER_PLAN"
# Review future run_after, parent, run_id, version và đúng actions ingest/build.
~/airflow_env/bin/python airflow/start_local.py --stop
source "$ENV_PLAN"
~/airflow_env/bin/python airflow/start_local.py --start
curl --fail http://127.0.0.1:8080/health
~/airflow_env/bin/airflow dags list-import-errors --output json
~/airflow_env/bin/python airflow/start_local.py --status
./.venv/Scripts/python.exe -X utf8 -m ingestion.incremental preflight --parent-id "$PARENT"
```

Run ID/UUID phải lấy từ planner, không ghép ngày local bằng tay: DAG/scheduler normalize logical date UTC; cùng instant nhưng chuỗi +07 và +00 sẽ cho UUID khác. Planner đã đối chiếu actual DAG và serialization. Nếu bất kỳ preflight/import/health check lỗi, giữ paused/gate false.

Sau review và kiểm tra tất cả gates, Owner pre-arm **một** interval bằng đoạn sau. Đoạn này chỉ sửa đúng boolean/scope trong private profile; không cấp quyền SQL:

```bash
~/airflow_env/bin/python - <<'PY'
import os,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'airflow'))
from schedule_local import plan
p=json.loads(Path(os.environ['RETAIL_OWNER_PLAN']).read_text())
e=p['environment']
v=plan(e['RETAIL_AIRFLOW_DAILY_TIME'],e['RETAIL_AIRFLOW_SCHEDULE_PARENT'],e['RETAIL_AIRFLOW_SCHEDULE_NOT_BEFORE'])
assert p['run_id']==v['run_id'] and p['write_scope']==v['write_scope']
assert all(os.environ.get(k)==value for k,value in e.items())
f=Path.home()/'.config/retail-airflow/config.json';c=json.loads(f.read_text())
assert c.get('allow_pipeline_writes') is False and c.get('write_scope') is None
c.update(allow_pipeline_writes=True,write_scope=v['write_scope'])
f.write_text(json.dumps(c,indent=2)+'\n')
print('Armed one reviewed interval; no SQL executed')
PY
~/airflow_env/bin/airflow dags unpause retail_sales_incremental_pipeline
~/airflow_env/bin/airflow dags next-execution retail_sales_incremental_pipeline
```

Không có tự xoay parent/scope để chạy unattended nhiều ngày. Kỳ kế tiếp có UUID khác sẽ bị write gate chặn nếu Owner chưa pre-arm lại. Parent cũ vẫn phải qua eligibility/depth checks; không reset chain/checkpoint để tiếp tục. Sau mỗi kỳ (PASS/FAIL), pause và đóng gate; kiểm source/Raw metadata, read version, marts/DQ/KPI trước kỳ tiếp theo.

### Đóng gate và tắt daily

Pause chỉ ngăn run mới, không hủy task đang chạy. Đợi/inspect mọi active run và Windows child trước shutdown/restart. Đóng gate không rollback giao dịch đã bắt đầu.

```bash
~/airflow_env/bin/airflow dags pause retail_sales_incremental_pipeline
~/airflow_env/bin/airflow dags list-runs -d retail_sales_incremental_pipeline
~/airflow_env/bin/python - <<'PY'
import json
from pathlib import Path
f=Path.home()/'.config/retail-airflow/config.json';c=json.loads(f.read_text())
c.update(allow_pipeline_writes=False,write_scope=None)
f.write_text(json.dumps(c,indent=2)+'\n')
PY
# Sau khi idle; đổi sang manual và restart để bỏ timetable:
~/airflow_env/bin/python airflow/start_local.py --stop
export RETAIL_AIRFLOW_SCHEDULE=manual
unset RETAIL_AIRFLOW_DAILY_TIME RETAIL_AIRFLOW_SCHEDULE_PARENT RETAIL_AIRFLOW_SCHEDULE_NOT_BEFORE
~/airflow_env/bin/python airflow/start_local.py --start
~/airflow_env/bin/python airflow/start_local.py --status
```

### Phối hợp Power BI

`pipeline_complete=PASS` xác nhận candidate/dbt/DQ/marts, **không phải BI refresh complete**. Trong CREATE/RENAME/GRANT/backup cleanup và khi graph chưa được validate: không refresh Desktop hoặc client BI khác. Chỉ mở cửa sổ refresh khi run SUCCESS, mart validation PASS, không writer/child đang chạy, 12 objects cùng V, ownership/reader SELECT đúng và core KPI đối soát đạt. Nếu run mới đã được pre-arm thì đóng gate/pause và drain trước refresh để tránh đụng lần rebuild kế tiếp.

Pin Power BI giữ nguyên cho đến bước đồng bộ được review riêng; không auto đổi UUID, fallback latest hoặc refresh với guard bị bỏ. Owner xác minh version mới rồi đồng bộ sáu import guards bằng workflow Power BI hiện hữu; Refresh thủ công, kiểm DAX/KPI/visuals và Save cache. Trong thời gian chờ, imported cache cũ không được gọi là dashboard đã cập nhật. Không Power BI REST API hoặc completion flag BI giả trong DAG.

### Kiểm chứng AIRFLOW-03 và giới hạn

Manual/default và daily preview, timezone, future boundary, UTC UUID, serialized timetable, ba daily points, parent handoff và gate block đã test không tạo DagRun. Task graph vẫn tám tasks/all_success; preflight retry 1/30s, ingestion/dbt retry 0; worker CLI timeout 3300s, bridge 3600s, task 3900s, DAG 5h. Timeout có thể để Windows child sống; inspect locks/durable version, không retry ghi mù. max_active_runs=1 và locks 941061/941062 giữ nguyên; không phải coherent source snapshot hoặc mutex cho mọi DBA.

Live read-only: WSL→Windows source/target preflight, parent/read-version/marts/DDL gates, BI reader, Compose config, dbt compile, scheduler/UI health và idempotent startup PASS. Shutdown/reboot và scheduled ingestion/build **NOT_RUN**. Runtime vẫn manual/paused/gate false; không thêm run/capture/version, không thay data/checkpoint/publication hoặc Power BI. Evidence ở ignored .local/airflow-03, không thêm Markdown reports.

Giới hạn: WSL/Windows logon và Docker Engine/container phải online tại giờ chạy; không có autostart/HA/service supervisor mới. SQLite/SequentialExecutor dành cho local; graph dbt chưa atomic, source consistency UNVERIFIED, BI refresh riêng và per-interval write authorization vẫn bắt buộc. Không tự nghiệm thu unattended scheduling nhiều ngày.
