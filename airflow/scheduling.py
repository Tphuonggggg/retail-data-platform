"""Non-secret schedule configuration. No files, database calls or write authority."""
from datetime import datetime,timedelta
import re
from uuid import UUID

TIMEZONE='Asia/Ho_Chi_Minh'
KEYS=('RETAIL_AIRFLOW_SCHEDULE','RETAIL_AIRFLOW_DAILY_TIME',
      'RETAIL_AIRFLOW_SCHEDULE_PARENT','RETAIL_AIRFLOW_SCHEDULE_NOT_BEFORE')


def canonical(value):
    if not isinstance(value,str) or str(UUID(value))!=value:raise ValueError('Canonical explicit parent UUID required')
    return value


def settings(environment):
    mode=environment.get(KEYS[0],'manual')
    if mode not in ('manual','daily'):raise ValueError('Schedule must be manual or daily')
    if mode=='manual':return {'mode':mode,'cron':None,'parent':None,'not_before':None}
    clock=environment.get(KEYS[1],'02:00')
    if not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]',clock):raise ValueError('Daily time must be HH:MM')
    parent=canonical(environment.get(KEYS[2]))
    start=datetime.fromisoformat(environment.get(KEYS[3],''))
    if start.utcoffset()!=timedelta(hours=7):raise ValueError('Explicit not-before timestamp with +07:00 required')
    hour,minute=map(int,clock.split(':'))
    if (start.hour,start.minute,start.second,start.microsecond)!=(hour,minute,0,0):raise ValueError('Not-before must match daily boundary')
    return {'mode':mode,'cron':f'{minute} {hour} * * *','parent':parent,'not_before':start}


def parent_for_run(run,scheduled_parent,previous=None):
    supplied=(run.conf or {}).get('parent_version')
    if supplied is not None:return canonical(supplied)
    if run.run_type!='scheduled':raise ValueError('Manual run requires parent_version')
    # Preserve the run's first verified handoff across later configuration changes.
    return canonical(previous['parent'] if previous else scheduled_parent)
