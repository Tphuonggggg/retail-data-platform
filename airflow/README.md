# Airflow Operations

This module orchestrates the existing Python incremental engine and dbt Sales graph. It does not reimplement extraction, advance publication pointers or refresh Power BI. See the [project overview](../README.md), [ingestion](../ingestion/README.md), [dbt](../dbt/README.md) and [infrastructure](../infrastructure/README.md).

## Runtime Architecture and Setup

The verified local environment uses Ubuntu WSL2, Airflow 2.11.0/Python 3.12 in `~/airflow_env`, SequentialExecutor and SQLite metadata at `~/airflow/airflow.db`. This is a local development configuration, not HA infrastructure. Scheduler and webserver are managed by [start_local.py](start_local.py); the UI binds to `127.0.0.1:8080`.

[bridge.py](bridge.py) invokes the existing Windows `.venv/Scripts/python.exe` and [worker.py](worker.py) using an argument list and explicit working directory. This preserves Windows Authentication/ODBC access to SQL Server. There is no WSL ODBC installation, shell interpolation or password in XCom. XCom carries only small action/status/parent/version metadata.

A new machine needs a separate supported Python 3.12 WSL virtual environment, an initialized Airflow metadata database and an operator UI account. For a genuinely new installation only, follow the [Airflow 2.11 constrained installation](https://airflow.apache.org/docs/apache-airflow/2.11.0/installation/installing-from-pypi.html):

```bash
# First installation only: do not run against the existing environment/metadata.
test ! -e ~/airflow_env && python3.12 -m venv ~/airflow_env
~/airflow_env/bin/python -m pip install 'apache-airflow==2.11.0' \
  --constraint https://raw.githubusercontent.com/apache/airflow/constraints-2.11.0/constraints-3.12.txt
~/airflow_env/bin/python -m pip check
export AIRFLOW_HOME="$HOME/airflow"
export AIRFLOW__CORE__EXECUTOR=SequentialExecutor
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=True
~/airflow_env/bin/airflow db migrate
~/airflow_env/bin/airflow users create --help
```

Create the operator UI account interactively with `airflow users create`, supplying the reviewed username/contact fields and entering its password at the prompt. Preserve the above executor/example settings in the new installation's configuration or startup shell. The launcher does not initialize/migrate/reset metadata or create credentials. Reuse the current environment without reinstalling packages or replacing `airflow.cfg`; this fresh-install sequence was not executed during documentation work.

From the repository in WSL, adapt the four path fields in [config.example.json](config.example.json) to the actual Windows/WSL checkout. Keep `allow_pipeline_writes=false` and `write_scope=null`. Do not put database credentials in this profile.

```bash
cd /mnt/d/Code/Retail_Data_Platform/project1_Retail_Data_platform
mkdir -p ~/.config/retail-airflow ~/airflow/dags
test -e ~/.config/retail-airflow/config.json || cp airflow/config.example.json ~/.config/retail-airflow/config.json
chmod 600 ~/.config/retail-airflow/config.json
# Create only when the link name is unused; inspect a broken/existing link first.
test -e ~/airflow/dags/retail_sales_incremental_pipeline.py || ln -s "$PWD/airflow/dags/retail_sales_incremental_pipeline.py" ~/airflow/dags/retail_sales_incremental_pipeline.py
export RETAIL_AIRFLOW_CONFIG="$HOME/.config/retail-airflow/config.json"
export RETAIL_AIRFLOW_SCHEDULE=manual
unset RETAIL_AIRFLOW_DAILY_TIME RETAIL_AIRFLOW_SCHEDULE_PARENT RETAIL_AIRFLOW_SCHEDULE_NOT_BEFORE
~/airflow_env/bin/airflow version
~/airflow_env/bin/airflow db check
~/airflow_env/bin/airflow dags list-import-errors --output json
```

## DAG and Read-Version Contract

[retail_sales_incremental_pipeline](dags/retail_sales_incremental_pipeline.py) defaults to `schedule=None`, `catchup=False`, `max_active_runs=1`, timezone `Asia/Ho_Chi_Minh`, and paused upon initial creation. Eight tasks run with `all_success` dependencies:

```text
preflight_source → preflight_target → run_incremental_ingestion
→ validate_ingestion_batch → resolve_dbt_read_version → run_dbt_build
→ validate_sales_marts → pipeline_complete
```

| Task | Contract |
|---|---|
| preflight_source | SELECT/projection/security checks for exactly six Sales dependencies |
| preflight_target | Verify target/schema/permissions and explicit parent eligibility |
| run_incremental_ingestion | Existing incremental CLI, deterministic version UUID derived from exact Airflow run ID |
| validate_ingestion_batch | Durable VALIDATED status, parent/contract/algorithm/scope, ACK=NULL and six-object reconciliation |
| resolve_dbt_read_version | Return the same validated UUID; no fallback to parent/latest |
| run_dbt_build | Existing full Sales graph; verify command/input/version receipt and successful model/data-test results |
| validate_sales_marts | Five nonempty, consistently pinned marts; independently reconcile core/header totals |
| pipeline_complete | Recheck version/mart gates; no publication, ACK or BI refresh |

Manual conf must include canonical `parent_version`. Scheduled runs without conf use an explicit environment parent. After preflight, the verified upstream handoff freezes that parent for recovery. No-change extraction still produces a new validated candidate/read version, not a silent reuse of the old BI pin.

## Startup and Health

Windows SQL Server must be running under the approved configuration. Start Docker Desktop Linux Engine, then inspect the existing Raw container before starting it:

```powershell
docker context show
docker info --format '{{.OSType}}'
docker inspect retail-raw-postgres-1 --format '{{.Config.Image}} {{json .Mounts}} {{json .HostConfig.PortBindings}}'
# Only after confirming the dedicated volume and localhost:55434 binding:
docker start retail-raw-postgres-1
docker inspect retail-raw-postgres-1 --format '{{.State.Health.Status}}'
wsl -d Ubuntu
```

In the configured WSL shell:

```bash
~/airflow_env/bin/python airflow/start_local.py --status
~/airflow_env/bin/python airflow/start_local.py --start
curl --fail http://127.0.0.1:8080/health
~/airflow_env/bin/airflow dags list-import-errors --output json
~/airflow_env/bin/airflow dags list-runs -d retail_sales_incremental_pipeline
```

Before startup/restart the DAG must be paused, no run queued/running, and gate/scope closed. If a reboot left an open gate/unpaused DAG, close/pause it before starting; do not bypass the idle guard. `--start` is idempotent only for matching process identity/configuration. The launcher verifies PID command, UID/process group, profile path and inherited schedule environment, and sets `airflow_env/bin` on service/subprocess PATH. This matters because SequentialExecutor invokes the bare `airflow` executable.

Logs/PIDs are under `~/airflow/retail-service-logs`; task logs are under the existing Airflow home and available through the UI. WSL and Windows logon context must remain available. No Windows Task Scheduler job, new systemd unit or automatic Docker restart has been installed.

## Supervised Manual Operation

The following write/trigger examples are **operator actions for a separately authorized run**, not documentation validation commands. First verify source/target identity, TLS, counts/digests, eligible parent/chain depth, no competing CLI/Windows child, Raw metadata baseline and an acceptable DDL scope. Snapshot consistency remains unverified.

Use a new exact run ID and a validated parent. Compute the version through the existing bridge, then authorize only that parent/version/actions in the private profile:

```bash
export PARENT=3a2f011d-f3b3-5683-83a2-a64837720f3d  # Revalidate before using.
export RUN_ID="manual__supervised_$(date -u +%Y%m%dT%H%M%SZ)"
./.venv/Scripts/python.exe -X utf8 -m ingestion.incremental preflight --parent-id "$PARENT"
~/airflow_env/bin/python - <<'PY'
import json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'airflow'))
from bridge import version_for_run
f=Path(os.environ['RETAIL_AIRFLOW_CONFIG']);c=json.loads(f.read_text())
assert c.get('allow_pipeline_writes') is False and c.get('write_scope') is None
v=str(version_for_run(os.environ['RUN_ID']))
c.update(allow_pipeline_writes=True,write_scope={'parent':os.environ['PARENT'],'version':v,'actions':['ingest','build']})
f.write_text(json.dumps(c,indent=2)+'\n')
print('Armed exact run version:',v)
PY
~/airflow_env/bin/airflow dags unpause retail_sales_incremental_pipeline
~/airflow_env/bin/airflow dags trigger retail_sales_incremental_pipeline \
  --run-id "$RUN_ID" --conf "{\"parent_version\":\"$PARENT\"}"
~/airflow_env/bin/airflow dags list-runs -d retail_sales_incremental_pipeline
```

Both bridge and worker enforce exact parent/version/action scope; a true boolean alone is insufficient. Rebuild-only recovery uses `actions=["build"]`. Scope covers existing delta/events/version and Sales transformation writes, never source writes, publication or BI. Pause and close gate/scope after success or failure using the shutdown section.

## Retry and Recovery

| Stage | Automatic retry | Required handling |
|---|---|---|
| Source/target preflight | One retry after 30 seconds for recognized transient transport errors | Authentication, TLS, permissions and contract/configuration errors fail immediately |
| Ingestion | None | Inspect durable version and Windows process; never overwrite FAILED/RUNNING identity |
| dbt build | None | Inspect partial graph, version, artifacts and grants before manual recovery |
| Validation/resolve/marts/complete | None | Fix the cause; clear only the necessary read task if the data remains valid |

Same successful version returns `ALREADY_VALIDATED_NO_REEXTRACTION`; a new run ID creates a different UUID. Unknown COMMIT requires ledger/read-back inspection, not an assumption that rollback occurred. A fresh extraction needs a new run ID and independently eligible parent/scope. Do not reset checkpoints, delete ledger records or clear successful ingestion just to rebuild dbt.

For a dbt-tail recovery: pause, identify the exact run/logical date, inspect native logs and durable P/V, drain Windows children and fix the DDL/dependency cause. Pre-arm build-only scope for that same P/V. Clear only `run_dbt_build`, `validate_sales_marts` and `pipeline_complete`, preserving the first five successful tasks; constrain the clear operation to the exact run, with no upstream/past/future selection. Reconcile all outputs before closing the gate.

Timeouts are CLI 3,300 seconds, bridge 3,600, task 3,900 and DAG five hours. A WSL timeout may leave a Windows child alive. Advisory locks 941061 (ingestion) and 941062 (dbt) protect cooperating runners, not every DBA or an atomic source/serving snapshot.

## Controlled dbt DDL

The approved replacement lifecycle covers the 21 reviewed Sales models, their intermediate/backup relations and the two known dependent header views. CREATE/RENAME/GRANT/COMMIT and backup DROP, including verified CASCADE effects, can be expected dbt behavior. Raw, ingestion metadata, capture/checkpoint/publication state, SQL Server and unrelated schemas remain outside this scope.

[ddl_policy.py](../dbt/ddl_policy.py) runs under the dbt lock before `run`/`build`. It checks project paths/schema/alias, role/ownership, protected permissions, stale artifacts and relation/row-type/function/trigger/RLS dependencies. Unknown consumers or orphan `__dbt_tmp`/`__dbt_backup` objects fail closed. `retail_transform` cannot write/create in Raw or ingestion metadata and has no administrative role flags.

The graph is non-atomic. Replacement can drop the two managed header views and rebuild them later. Isolated tests verified rollback before COMMIT; after successful COMMIT with acknowledgment/cleanup failure, canonical data may be new while backup/dependent views remain old. Inspect canonical/backup versions, ownership, grants and dependencies before any cleanup. Approved isolated recovery rebound the managed header, then used DROP RESTRICT on the verified backup. Unexpected consumers keep the gate closed. Never blanket-clean with CASCADE or assume a client failure undid committed work.

The policy requires reviewed code and no concurrent administrative DDL; it is not a generic SQL firewall. Do not add dependencies or expand permissions to force a build through the gate.

## Daily Schedule Preparation

Manual mode remains the default. [scheduling.py](scheduling.py) reads only these non-secret parse-time settings:

| Variable | Meaning |
|---|---|
| `RETAIL_AIRFLOW_SCHEDULE` | `manual` (default) or `daily` |
| `RETAIL_AIRFLOW_DAILY_TIME` | HH:MM, default 02:00, Asia/Ho_Chi_Minh |
| `RETAIL_AIRFLOW_SCHEDULE_PARENT` | Explicit eligible parent UUID |
| `RETAIL_AIRFLOW_SCHEDULE_NOT_BEFORE` | Future +07:00 timestamp on the chosen daily boundary |

Daily mode uses CronTriggerTimetable, not an extraction date window. `catchup=False` prevents historical backfill; a latest missed interval may still be considered after downtime. Its different UUID remains blocked by the exact write scope. Paused-upon-creation does not pause an existing DAG after reboot.

Only after operator approval, start paused/drained with a closed gate and generate a **single-interval preview**:

```bash
PARENT=3a2f011d-f3b3-5683-83a2-a64837720f3d  # Verify actual parent again.
export RETAIL_OWNER_PLAN=".local/airflow-owner-$(date +%Y%m%dT%H%M%S).json"
ENV_PLAN="${RETAIL_OWNER_PLAN%.json}.env"
~/airflow_env/bin/python airflow/schedule_local.py --parent "$PARENT" --daily-time 02:00 \
  --output "$RETAIL_OWNER_PLAN" --env-output "$ENV_PLAN"
cat "$RETAIL_OWNER_PLAN"
# Review future boundary, exact run ID, version and ingest/build scope.
~/airflow_env/bin/python airflow/start_local.py --stop
source "$ENV_PLAN"
~/airflow_env/bin/python airflow/start_local.py --start
curl --fail http://127.0.0.1:8080/health
~/airflow_env/bin/airflow dags list-import-errors --output json
~/airflow_env/bin/python airflow/start_local.py --status
./.venv/Scripts/python.exe -X utf8 -m ingestion.incremental preflight --parent-id "$PARENT"
```

The planner does not connect to SQL, arm writes or trigger a run. It derives the run ID from actual scheduler UTC normalization; do not construct a different UUID from a local-time string. If any health/import/preflight gate fails, leave the DAG paused and write gate closed.

After reviewing all gates, the operator can arm that exact future interval:

```bash
~/airflow_env/bin/python - <<'PY'
import os,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'airflow'))
from schedule_local import plan
p=json.loads(Path(os.environ['RETAIL_OWNER_PLAN']).read_text());e=p['environment']
v=plan(e['RETAIL_AIRFLOW_DAILY_TIME'],e['RETAIL_AIRFLOW_SCHEDULE_PARENT'],e['RETAIL_AIRFLOW_SCHEDULE_NOT_BEFORE'])
assert p['run_id']==v['run_id'] and p['write_scope']==v['write_scope']
assert all(os.environ.get(k)==value for k,value in e.items())
f=Path(os.environ['RETAIL_AIRFLOW_CONFIG']);c=json.loads(f.read_text())
assert c.get('allow_pipeline_writes') is False and c.get('write_scope') is None
c.update(allow_pipeline_writes=True,write_scope=v['write_scope'])
f.write_text(json.dumps(c,indent=2)+'\n')
PY
~/airflow_env/bin/airflow dags unpause retail_sales_incremental_pipeline
~/airflow_env/bin/airflow dags next-execution retail_sales_incremental_pipeline
```

No automatic parent/scope rotation exists. The next date has a different UUID and requires new preparation. After each run, pause/close the gate, inspect lineage/DQ/KPIs and prepare another interval only if eligible. To recover a run older than daily start_date, switch back to manual through pause/drain/restart before clearing it; retain its run ID/conf/P/V. Do not enable catchup or move the boundary backward.

## Shutdown and Disable Scheduling

Pause prevents new runs, not cancellation of existing tasks. Drain active/queued runs and Windows children before stopping. Closing a gate does not roll back a transaction already started.

```bash
~/airflow_env/bin/airflow dags pause retail_sales_incremental_pipeline
~/airflow_env/bin/airflow dags list-runs -d retail_sales_incremental_pipeline
~/airflow_env/bin/python - <<'PY'
import json,os
from pathlib import Path
f=Path(os.environ['RETAIL_AIRFLOW_CONFIG']);c=json.loads(f.read_text())
c.update(allow_pipeline_writes=False,write_scope=None)
f.write_text(json.dumps(c,indent=2)+'\n')
PY
# Only after idle; launcher verifies identity and sends SIGTERM, not force-kill.
~/airflow_env/bin/python airflow/start_local.py --stop
export RETAIL_AIRFLOW_SCHEDULE=manual
unset RETAIL_AIRFLOW_DAILY_TIME RETAIL_AIRFLOW_SCHEDULE_PARENT RETAIL_AIRFLOW_SCHEDULE_NOT_BEFORE
# Optional restart in manual mode:
~/airflow_env/bin/python airflow/start_local.py --start
~/airflow_env/bin/python airflow/start_local.py --status
```

Stop Raw only when all CLI and BI clients are idle: `docker stop --time 30 retail-raw-postgres-1` from Windows. Retain container/volume for later `docker start`. Do not stop/reconfigure source SQL Server, native PostgreSQL or B9 resources as part of this workflow. Live shutdown/reboot recovery has not been exercised end-to-end; current identity/idle guards and idempotent startup have been checked.

## Power BI Coordination

`pipeline_complete=PASS` means the warehouse gates passed, not that the dashboard refreshed. Do not refresh BI during CREATE/RENAME/GRANT/cleanup or before the complete graph validates. Confirm run SUCCESS, no active writer/child, all 12 serving objects on V, reader SELECT and reconciled KPIs. Pause/drain a pre-armed next run before opening a refresh window.

The existing Power BI pin stays unchanged until separately reviewed. Follow [Power BI version synchronization](../powerbi/README.md), refresh manually, check SQL/DAX/visuals and save. An old imported cache is not the new version; no fallback latest or automatic REST API refresh is implemented.

## Validation and Known Limitations

One accepted supervised run completed all eight tasks, 21 dbt models and 69 data tests. Reliability evidence separates mocked/isolated transport and ingestion failures, isolated DDL rollback/recovery, live same-version read-back and supervised live dbt-tail recovery. It does not claim that every simulated failure occurred on the real source.

Run `.venv\Scripts\python.exe scripts/run_checks.py` from Windows for offline regression. [reliability_runtime.py](tests/reliability_runtime.py) is an explicit isolated Airflow harness, not a production trigger; inspect its `--help` before use. Source/target preflight, dbt compile, DAG discovery, role checks and health checks can be performed without ingestion/build.

Scheduled ingestion and unattended multi-day recovery remain unverified. Windows logon, WSL, Docker and SQL Server must be online; no new autostart service was added. Source consistency is UNVERIFIED, the dbt graph is non-atomic, and publication/BI refresh remain separate controlled operations.

## Portfolio Evidence

Chuỗi tám task và dependencies ở trên là workflow thực; read-version handoff nối `validate_ingestion_batch` → `resolve_dbt_read_version` → `run_dbt_build`, rồi mart gates kiểm tra cùng identity. `max_active_runs=1` hạn chế DAG overlap; locks 941061/941062 bảo vệ các cooperating writers. Preflight transport transient retry một lần; task ghi không tự retry. Downstream default all_success truyền failure và không cho complete giả.

Walkthrough dựa trên **accepted AIRFLOW-01/02/03**, không trigger live trong lượt tài liệu này:

1. AIRFLOW-01 supervised run hoàn tất 8/8 tasks với version đã pin. Không biến kết quả này thành bằng chứng daily unattended.
2. AIRFLOW-02 tách isolated failure/serialization tests với live same-version read-back và dbt-tail recovery. Trong recovery giữ nguyên năm task đầu đã thành công, parent/version không đổi; scope chỉ `actions=["build"]`.
3. Sau khi inspect ledger/process/partial DDL và sửa nguyên nhân, chỉ clear ba task cuối của đúng run: `run_dbt_build`, `validate_sales_marts`, `pipeline_complete`. Ingestion không chạy lại. Xác nhận marts/version/privileges trước khi đóng gate.
4. AIRFLOW-03 chuẩn bị lịch và lifecycle guards; không chứng minh unattended multi-day. Mặc định vẫn manual (`schedule=None`), paused, `catchup=False`, gate=false; không tự cấp quyền cho interval tương lai.

Tái hiện offline: `python -m unittest discover -s airflow/tests -p test_reliability.py -v` và `test_worker.py`; kiểm tra failure propagation, write scope, retry và version validation bằng mocks. Chúng không thay thế live Airflow recovery. Harness isolated Airflow đã có tại [reliability_runtime.py](tests/reliability_runtime.py), chỉ chạy trong scope sandbox riêng; không dừng live database để giả lỗi.

Chưa có ảnh Graph View/task logs thật để đưa vào Git. Chủ dự án có thể mở accepted run ở UI, chụp Graph/Grid thấy đủ tám task và run state, sau đó chụp log resolve read version hoặc recovery tail. Giữ DAG paused/gate closed; không cần trigger/refresh dữ liệu. Che credentials, private hostname/path và thông tin phiên trước khi lưu `docs/assets/airflow-graph.png`; không tạo ảnh từ log giả.
