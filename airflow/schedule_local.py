"""Preview one future daily interval and its existing bounded write scope. Never arm."""
import argparse
import importlib.util
import json
from pathlib import Path
import shlex

ROOT=Path(__file__).resolve().parent


def load(name):
    spec=importlib.util.spec_from_file_location('retail_'+name,ROOT/(name+'.py'))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def plan(clock,parent,not_before=None):
    import pendulum
    from airflow.timetables.trigger import CronTriggerTimetable
    from airflow.timetables.base import TimeRestriction
    from airflow.utils.types import DagRunType
    scheduling=load('scheduling');parent=scheduling.canonical(parent)
    # Validate format before converting, even when choosing the next future day.
    if not_before is None:
        now=pendulum.now(scheduling.TIMEZONE)
        import re
        if not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]',clock):raise ValueError('Daily time must be HH:MM')
        hour,minute=map(int,clock.split(':'))
        boundary=now.replace(hour=hour,minute=minute,second=0,microsecond=0)
        if boundary<=now.add(minutes=5):boundary=boundary.add(days=1)
        not_before=boundary.isoformat()
    environment=dict(zip(scheduling.KEYS,('daily',clock,parent,not_before)))
    cfg=scheduling.settings(environment)
    start=pendulum.instance(cfg['not_before'])
    if start<=pendulum.now(scheduling.TIMEZONE).add(minutes=1):raise ValueError('Plan must be at least one minute in the future')
    timetable=CronTriggerTimetable(cfg['cron'],timezone=scheduling.TIMEZONE)
    # DAG normalizes start_date/TimeRestriction to UTC before scheduler run-id
    # generation. Equal instants with +07 vs +00 strings produce different UUIDs.
    info=timetable.next_dagrun_info(last_automated_data_interval=None,restriction=TimeRestriction(earliest=start.in_timezone('UTC'),latest=None,catchup=False))
    if info.run_after!=start:raise ValueError('Unexpected first interval; inspect timetable')
    run_id=timetable.generate_run_id(run_type=DagRunType.SCHEDULED,logical_date=info.logical_date,data_interval=info.data_interval)
    version=load('bridge').version_for_run(run_id)
    return {'mode':'daily','timezone':scheduling.TIMEZONE,'cron':cfg['cron'],'environment':environment,
            'logical_date':info.logical_date.isoformat(),'run_after':info.run_after.isoformat(),'run_id':run_id,'version':version,
            'write_scope':{'parent':parent,'version':version,'actions':['ingest','build']},
            'armed':False,'note':'Preview only. Explicit parent, one exact run; later dates require new scope. No BI refresh.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--daily-time',default='02:00');parser.add_argument('--parent',required=True)
    parser.add_argument('--not-before');parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--env-output',type=Path,required=True)
    args=parser.parse_args();result=plan(args.daily_time,args.parent,args.not_before)
    for path in (args.output,args.env_output):
        if path.exists():raise ValueError('Plan output exists; inspect or choose a new filename')
        path.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    args.env_output.write_text('\n'.join('export '+key+'='+shlex.quote(value) for key,value in result['environment'].items())+'\n')
    print(json.dumps(result));return 0


if __name__=='__main__':raise SystemExit(main())
