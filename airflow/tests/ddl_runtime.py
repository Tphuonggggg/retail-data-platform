"""Explicit PostgreSQL isolated-schema replacement/recovery fixtures, no dbt build.

SQL phases follow the installed dbt table/view materializations: CREATE intermediate,
RENAME old/new, GRANT, COMMIT, then backup cleanup. Not a live rebuild claim.
"""
import argparse
import json
from pathlib import Path
import sys
import re
from contextlib import contextmanager

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'dbt'))
from acceptance import connect
from ddl_policy import inspect_scope,DDLPolicyError


SANDBOX=None


class FixtureConnection:
    def __init__(self,db):self.db=db
    def execute(self,query,params=None):
        query=query.replace('CREATE OR REPLACE TEMP VIEW','CREATE OR REPLACE VIEW').replace('CREATE TEMP TABLE','CREATE TABLE').replace('CREATE TEMP VIEW','CREATE VIEW').replace('pg_temp.',SANDBOX+'.')
        if params:params=tuple(v.replace('pg_temp.',SANDBOX+'.') if isinstance(v,str) else v for v in params)
        return self.db.execute(query,params)
    def transaction(self):return self.db.transaction()


@contextmanager
def fixture():
    with connect() as raw:
        owner=raw.execute('SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname=%s',(SANDBOX,)).fetchone()
        assert owner==('retail_transform',),'Provision the explicit isolated schema first'
        assert not raw.execute('SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=%s',(SANDBOX,)).fetchone()[0],'Sandbox not empty; inspect before rerun'
        raw.execute('SET search_path TO '+SANDBOX+',pg_catalog')
        db=FixtureConnection(raw)
        yield db
        # Exact fixture names only; never DROP SCHEMA CASCADE or touch other schemas.
        db.execute('DROP FUNCTION IF EXISTS pg_temp.af02_unapproved_function() RESTRICT')
        for item in ('af02_unapproved_consumer','af02_old_consumer','af02_header__dbt_tmp','af02_header__dbt_backup','af02_header'):
            db.execute('DROP VIEW IF EXISTS pg_temp.'+item+' RESTRICT')
        for item in ('af02_fact__dbt_tmp','af02_fact__dbt_backup','af02_fact','af02_input'):
            db.execute('DROP TABLE IF EXISTS pg_temp.'+item+' RESTRICT')


def name(db):return SANDBOX
def exists(db,item):return db.execute('SELECT to_regclass(%s)',('pg_temp.'+item,)).fetchone()[0] is not None
def value(db,item):return db.execute('SELECT amount FROM pg_temp.'+item).fetchone()[0]
def granted(db,item):return db.execute("SELECT has_table_privilege('retail_bi_reader',%s,'SELECT')",('pg_temp.'+item,)).fetchone()[0]
def grant(db,item):db.execute('GRANT SELECT ON pg_temp.'+item+' TO retail_bi_reader')
def setup(db):
    db.execute('CREATE TEMP TABLE af02_input(amount integer)');db.execute('INSERT INTO af02_input VALUES(200)')
    db.execute('CREATE TEMP TABLE af02_fact AS SELECT 100::integer amount')
    db.execute('CREATE TEMP VIEW af02_header AS SELECT amount FROM af02_fact')
    grant(db,'af02_fact');grant(db,'af02_header')
def check_scope(db):
    schema=name(db)
    return inspect_scope(db,{(schema,'af02_fact'),(schema,'af02_header')},{(schema,'af02_header')})
def recover(db,kind,target):
    # Commit already succeeded: inspect rather than assume rollback/re-extract.
    assert value(db,target)==200 and value(db,target+'__dbt_backup')==100
    try:check_scope(db)
    except DDLPolicyError as e:assert str(e)=='DDL_STALE_ARTIFACT_INSPECT_BEFORE_RERUN'
    else:raise AssertionError('Orphan artifact admitted')
    if kind=='table':
        db.execute('CREATE OR REPLACE TEMP VIEW af02_header AS SELECT amount FROM af02_fact')
    db.execute('DROP '+kind+' pg_temp.'+target+'__dbt_backup RESTRICT')
    assert granted(db,target) and not exists(db,target+'__dbt_backup')
    check_scope(db)


def replacement(db,kind,fail=None):
    target='af02_fact' if kind=='table' else 'af02_header'
    def fault(phase):
        if fail==phase:db.execute('SELECT 1/0')
    try:
        with db.transaction():
            fault('before_create')
            if kind=='table':db.execute('CREATE TEMP TABLE af02_fact__dbt_tmp AS SELECT amount FROM af02_input')
            else:db.execute('CREATE TEMP VIEW af02_header__dbt_tmp AS SELECT amount+100 AS amount FROM af02_fact')
            fault('after_create')
            db.execute('ALTER '+kind+' pg_temp.'+target+' RENAME TO '+target+'__dbt_backup')
            fault('after_old_rename')
            db.execute('ALTER '+kind+' pg_temp.'+target+'__dbt_tmp RENAME TO '+target)
            fault('after_new_rename')
            grant(db,target);fault('after_grant')
            fault('before_commit')
    except Exception as error:
        assert getattr(error,'sqlstate',None)=='22012'
        assert value(db,target)==100 and granted(db,target)
        assert value(db,'af02_header')==100
        assert not exists(db,target+'__dbt_tmp') and not exists(db,target+'__dbt_backup')
        check_scope(db)
        return {'status':'PASS','expected':'transaction rollback restores old data/grants/names/dependencies','observed_old_value':100,'orphan_artifacts':0}
    assert value(db,target)==200 and granted(db,target)
    if fail in ('unknown_commit','cleanup_failure'):
        if fail=='cleanup_failure':
            if kind=='view':db.execute('CREATE TEMP VIEW af02_old_consumer AS SELECT amount FROM af02_header__dbt_backup')
            try:db.execute('DROP '+kind+' pg_temp.'+target+'__dbt_backup RESTRICT')
            except Exception as error:assert getattr(error,'sqlstate',None)=='2BP01'
            else:raise AssertionError('Missing dependency failure')
            if kind=='view':db.execute('DROP VIEW pg_temp.af02_old_consumer RESTRICT')
        recover(db,kind,target)
        return {'status':'PASS','expected':'committed replacement survives; stale artifact blocks blind rerun; explicit recovery','observed_new_value':200,'backup_removed_after_dependency_rebind':True}
    db.execute('DROP '+kind+' IF EXISTS pg_temp.'+target+'__dbt_backup CASCADE')
    if kind=='table':
        assert not exists(db,'af02_header'),'Expected the old dependent view to be cascaded'
        db.execute('CREATE TEMP VIEW af02_header AS SELECT amount FROM af02_fact');grant(db,'af02_header')
    assert value(db,target)==200 and granted(db,target) and granted(db,'af02_header')
    assert not exists(db,target+'__dbt_backup')
    check_scope(db)
    return {'status':'PASS','expected':'successful replacement, scoped dependent view recreated, grants restored','observed_new_value':200,'orphan_artifacts':0}


def main():
    global SANDBOX
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute-isolated',action='store_true');parser.add_argument('--output',type=Path,required=True);parser.add_argument('--schema',required=True)
    args=parser.parse_args()
    if not args.execute_isolated:parser.print_help();return 0
    if not re.fullmatch(r'af02_ddl_[0-9a-f]{12}',args.schema):raise ValueError('Explicit isolated schema required')
    SANDBOX=args.schema
    results=[]
    for kind in ('table','view'):
        for phase in ('before_create','after_create','after_old_rename','after_new_rename','after_grant','before_commit','unknown_commit','cleanup_failure',None):
            with fixture() as db:
                setup(db);check_scope(db)
                result=replacement(db,kind,phase)
                if phase is not None:
                    # Safe same-input rerun after rollback/manual recovery, no ingestion.
                    if phase in ('unknown_commit','cleanup_failure'):
                        assert value(db,'af02_header')==200
                    else:replacement(db,kind)
                results.append({'kind':kind,'phase':phase or 'success','method':'ISOLATED_SCHEMA',**result})
    with fixture() as db:
        setup(db);schema=name(db)
        db.execute('CREATE TEMP VIEW af02_unapproved_consumer AS SELECT amount FROM af02_fact')
        try:check_scope(db)
        except DDLPolicyError as e:assert str(e)=='DDL_UNAPPROVED_CASCADE_DEPENDENCY'
        else:raise AssertionError('Unapproved consumer admitted')
        # Positive control only in the temporary schema: CASCADE can remove more
        # than its named target. The operational read-only gate blocks this state.
        db.execute('DROP TABLE pg_temp.af02_fact CASCADE')
        assert not exists(db,'af02_unapproved_consumer')
        results.append({'kind':'cascade_guard','phase':'unapproved_view','status':'PASS','method':'ISOLATED_SCHEMA','unsafe_cascade_observed':True,'operational_gate_rejected_before_drop':True})
    with fixture() as db:
        setup(db)
        db.execute('CREATE FUNCTION pg_temp.af02_unapproved_function() RETURNS SETOF pg_temp.af02_fact LANGUAGE sql AS $$ SELECT * FROM pg_temp.af02_fact $$')
        try:check_scope(db)
        except DDLPolicyError as e:assert str(e)=='DDL_UNAPPROVED_CASCADE_DEPENDENCY'
        else:raise AssertionError('Row-type dependent function admitted')
        results.append({'kind':'cascade_guard','phase':'unapproved_row_type_function','status':'PASS','method':'ISOLATED_SCHEMA'})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'status':'PASS','cases':results,'scope':SANDBOX,'production_build_executed':False},indent=2)+'\n')
    print('PASS: '+str(len(results))+' PostgreSQL isolated-schema lifecycle/failure/recovery cases; no live dbt build')
    return 0


if __name__=='__main__':raise SystemExit(main())
