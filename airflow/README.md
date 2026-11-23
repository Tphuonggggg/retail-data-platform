# Airflow — Retail Sales orchestration

**AIRFLOW_01_PARTIAL** — implementation/import/services đã kiểm tra; chưa chạy end-to-end vì PostgreSQL timeout/Docker Engine unavailable. Không ghi ingestion/dbt/DQ runtime PASS từ DAG import.

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

Private profile mặc định `allow_pipeline_writes=false`; giữ false trong lúc target đang BLOCKED. Để thực hiện lần supervised run sau này: xác minh source/target identity/TLS/privileges, capture/ledger/checkpoint/pointer baseline, parent validated/contract/depth, không CLI/dbt khác đang chạy, Docker healthy, debug/compile vàlevel1–2 PASS. Xác định write scope: sixRaw delta payloads, incremental events/version ledger vàschemas transform sở hữu dw_staging/dw_intermediate/dw_core/sales_marts/dq; không WWI source, Raw publication hoặc BI.

Sau khi các gates thực tế PASS, operator bật write gate trong profile private vàtrigger:

```bash
~/airflow_env/bin/airflow dags unpause retail_sales_incremental_pipeline
~/airflow_env/bin/airflow dags trigger retail_sales_incremental_pipeline \
  --run-id manual__supervised_01 \
  --conf '{"parent_version":"<validated-parent-uuid>"}'
~/airflow_env/bin/airflow dags list-runs -d retail_sales_incremental_pipeline
```

**Chưa thực thi lệnh trigger này.** Docker Engine hiện unavailable nên target preflight ConnectionTimeout; không đủ baseline/reconciliation/debug/compile để chạy level3. Không create version hoặcbuild một phần khi target chưapass. `allow_pipeline_writes` làoperator interlock, không cơ chếauthorization chống malicious local process; repo vàprivateprofile phải trusted.

## Retry, rerun, failure

Source/target connection tasks retry1; write tasks retry0. Default all_success khiến failure chặn mọi downstream, không markcomplete nếu dbt/mart thất bại. Manual clear cùng Airflow run giữV/parent; dbt retry không tạo ingestion version mới. Existing successfulV đượcreconcile/read-back, khôngreextract. FAILED/RUNNING/unknownCOMMIT: inspectledger trước, không clear ingestion task mù; fresh extraction dùng **new DAG run_id** vàexplicit validated parent. Không tự restartwholeDAG.

Timeout của bridge/worker được báofailure; Windows interopchild có thể còn chạy sau WSLtasktimeout. Không tự kill/retry/createbatch; inspectWindows processes vàdurableversion, đợi/cancel cókiểm soát trước rerun. max_active_runs=1 chỉserializeDAG này; external CLI hoặcDAG khác vẫn cần operator coordination. Existing ingestion/dbt advisory locks vẫn làguard từngengine, khôngglobalatomicpublication. AirflowSQLite sequential chỉ phù hợp localsingleDAG; không HA hoặcdistributedexecutor.

## Kiểm tra và trạng thái

Airflow2.11 runtime import đủ8tasks, DAG discovery, noimporterrors, metadata/db/pipcheck vàUIhealth PASS. N?m bridge tests vàworker receipt/write/version gate tests làmock/offline failure tests, không giảnetworkchaos hoặcmutationproof. Root scripts/run_checks.py bao gồm airflow/tests.

Source read-only preflight từWSL bridge PASS. Target BLOCKED(ConnectionTimeout), Docker daemonpipe missing. dbt debug/compile trêntarget, read-version liveinspection, metadata before/after vàend-to-endDAG **NOT_RUN/BLOCKED**. Không runFullLoad, incrementalexecute, dbtbuild, sourcewrites hoặcpublication trongtask này. No-change/mutation/runtime rerun cases chưa testtrongAirflow; engine regressions hiện hữu vẫnđược giữ.

Troubleshooting: source Windows auth/ODBC/TLS fail thìdừng, khôngfallbackSQLlogin/trust; targettimeout kiểmDocker trước, khôngprunevolume; DAGnotfound kiểmsymlink/resolvedpath; writegatedisabled khôngbật trướclevel2; dbtfailed khôngchọnolderversion; warnings/testskip khôngđượccoi fullbuildPASS. Logs/errors vàrunUUIDs ởAirflowtasklogs, temporaryevidence ởignored.local/airflow-01. PowerBI vẫnmanualImport/Refresh, khôngsửareport.
