# Airflow — Retail Sales orchestration

**AIRFLOW_01_ACCEPTED — local supervised runtime, 2026-11-23.** Đã chạy một DAG end-to-end, đủ 8 tasks SUCCESS; 21 dbt models, 69 tests và run-start operation PASS. Không đồng nghĩa production readiness hoặc certified/source-consistent publication.

**AIRFLOW_02_PARTIAL.** Các kiểm thử reliability/recovery trên DAG hiện hữu đã chạy, scheduling vẫn tắt. Recovery live đã rebuild bằng dbt table materialization và DROP các backup tables; điều này vi phạm ràng buộc không DROP bất kỳ PostgreSQL table của AIRFLOW-02, dù dữ liệu trước/sau khớp nhau. Chưa đủ điều kiện nghiệm thu. Phân biệt fixture/mocks, scheduler cô lập và recovery live ở phần dưới; không coi các lỗi mô phỏng là sự cố thật của WWI/PostgreSQL.

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

`start_local.py` kiểm metadata rồi start scheduler/webserver nếu PID chưa active; không tự initialize/reset DB. Webserver bind127.0.0.1:8080; health endpoint đã HTTP200/metadatabase healthy/scheduler healthy. Service logs/PIDs trong `~/airflow/retail-service-logs`. PID existence check không thay full service supervisor; nếu stale/reused PID hoặc một service được start ngoài script, operator phải inspect trước, không start duplicate. Không tạo/đổi user hoặc mật khẩu UI. Dùng user Airflow đã có; nếu chưa có, owner cần provision riêng.

Launcher đặt airflow_env/bin đầu PATH cho service và task subprocesses. SequentialExecutor gọi lệnh `airflow` không có đường dẫn tuyệt đối; thiếu PATH này khiến scheduler dừng lúc task đầu được queued. Đã bổ sung regression cho inherited PATH, không sửa system PATH hoặc cài lại Airflow. Nếu lỗi này xảy ra trước ingestion: kiểm candidate chưa tồn tại, khởi động scheduler với PATH đúng; giữ nguyên run ID và để orphan handling tiếp tục, không tạo batch mới hoặc clear write task mù.

WSL must remain running for these local services. Nếu cài mới trên máy khác cần Airflow release/Python hỗ trợ và official version-specific constraints trong venv riêng; không chạy lệnh reinstall trên environment đang hoạt động. Task này reuse installation đã kiểm chứng, không thêm dependency root.

## DAG và read-version contract

`retail_sales_incremental_pipeline`: schedule=None, catchup=False, max_active_runs=1, timezone Asia/Ho_Chi_Minh, paused khi tạo; không backfill. DAG parse không đọc secrets hoặc kết nối DB. Chuỗi tám task:

```text
preflight_source → preflight_target → run_incremental_ingestion
→ validate_ingestion_batch → resolve_dbt_read_version → run_dbt_build
→ validate_sales_marts → pipeline_complete
```

Manual conf bắt buộc `parent_version` canonical UUID. Mỗi Airflow run_id ánh xạ deterministic uuid5 thành version mới; đây chỉ là naming cho UUID của ledger hiện có, không thêm capture table/checkpoint song song. XCom chỉ cóaction/status/parent/version; không records/DataFrame.

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

Recovery chỉ rebuild thì `actions=["build"]`; bridge và worker đều kiểm scope trước gọi CLI. **dbt table rebuild có DROP backup relations**: scope này không phù hợp với một yêu cầu cấm DROP tuyệt đối. Khi chưa có chấp thuận cho table replacement, giữ gate đóng và chỉ kiểm thử cô lập/đọc. Không cho scope wildcard, không cho một scope áp dụng nhiều version. Gate là interlock local, không thay SQL least privilege hoặc bảo vệ private profile/repository.

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
5. Chỉ khi Owner cho phép DDL table replacement của dbt: mở scope `build` cho đúng P/V rồi unpause DAG manual. Nếu vẫn cấm DROP tuyệt đối thì dừng trước bước này, dùng fixtures để chứng minh recovery. dbt kiểm eligibility lại trước CLI và dùng đúng V; không clear ingestion. Chỉ hoàn tất sau execution receipt và mọi model/data test PASS, mart reconciliation PASS.
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

**Sai lệch safety cần Owner review:** SQL log của recovery invocation có 42 câu DROP IF EXISTS cho dbt temporary/backup relations, trong đó 21 câu dành cho `__dbt_backup`; không có TRUNCATE. Các bảng phục vụ đã được thay thế theo cơ chế materialization của dbt; data digests/KPI khớp hoàn toàn, nhưng không thể tuyên bố đã tuân thủ lệnh cấm DROP bất kỳ bảng PostgreSQL. Đã dừng mọi thao tác ghi tiếp theo, không tự coi normal dbt rebuild là ngoại lệ được duyệt. Cần Owner quyết định liệu cho phép table replacement có kiểm soát trong recovery tương lai hay giữ cấm DROP và chỉ demo bằng môi trường cô lập. Không mở scheduling hoặc đánh dấu AIRFLOW-02 accepted khi chưa xử lý sai lệch này.

Tái kiểm tra offline từ Windows: `.venv\Scripts\python.exe scripts/run_checks.py`. Trên WSL dùng Python Airflow hiện có:

```bash
~/airflow_env/bin/python airflow/tests/reliability_runtime.py --execute-isolated --output .local/airflow-02/isolated
```

Harness dùng DAG/operators hiện hữu, Airflow home/SQLite tạm riêng và fixture worker, không chạy trên metadata hoặc databases vận hành. Retry delay chỉ được rút xuống 1ms trong test in-process; production vẫn 30 giây. PostgreSQL fixture có thể chạy riêng bằng `.venv\Scripts\python.exe tests/integration/incremental_runtime.py --execute` sau khi kiểm tra target/scope; giữ prefix fixture để inspect, không DROP/TRUNCATE. Runtime evidence tại ignored `.local/airflow-02/`, native Airflow logs và ingestion ledger; không tạo audit database/report hay milestone Markdown mới.

Giới hạn còn lại: local SQLite/SequentialExecutor, chưa HA; timeout Windows child cần operator inspect; dbt graph chưa atomic; locks không chặn source business writers; source consistency vẫn UNVERIFIED; chưa nghiệm thu automated scheduling hoặc sự cố thật bằng cách tắt services.
