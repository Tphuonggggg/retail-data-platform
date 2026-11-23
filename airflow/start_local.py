"""Start/stop no services implicitly: explicit WSL local scheduler/webserver start."""
import argparse
import os
from pathlib import Path
import subprocess


def service_environment(executable, config):
    # SequentialExecutor launches the bare `airflow` command in task subprocesses.
    return dict(os.environ, RETAIL_AIRFLOW_CONFIG=str(config),
                AIRFLOW__CORE__LOAD_EXAMPLES='False',
                PATH=str(executable.parent) + os.pathsep + os.environ.get('PATH', ''))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', action='store_true')
    args = parser.parse_args()
    if os.name == 'nt':
        raise SystemExit('Run with the existing WSL airflow_env Python')
    home = Path.home()
    executable = home / 'airflow_env/bin/airflow'
    config = home / '.config/retail-airflow/config.json'
    if not executable.is_file() or not config.is_file():
        raise SystemExit('Configure existing Airflow and private path profile first')
    env = service_environment(executable, config)
    subprocess.run([str(executable), 'db', 'check'], env=env, check=True)
    if not args.start:
        return
    logs = home / 'airflow/retail-service-logs'
    logs.mkdir(exist_ok=True)
    for service in ('scheduler','webserver'):
        pidfile = logs / (service + '.pid')
        if pidfile.exists():
            try:
                pid = int(pidfile.read_text())
                os.kill(pid, 0)
            except (ProcessLookupError, ValueError):
                pass
            else:
                print(service + ': already running; no duplicate started')
                continue
        with (logs / (service + '.log')).open('ab') as log:
            command = [str(executable), service]
            if service == 'webserver':
                command += ['--hostname','127.0.0.1','--port','8080']
            process = subprocess.Popen(command, env=env, stdout=log, stderr=log,
                                       start_new_session=True)
        pidfile.write_text(str(process.pid))
        print(service + ': started PID ' + str(process.pid))


if __name__ == '__main__':
    main()
