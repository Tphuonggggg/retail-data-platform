"""Read-only pre-build guard for the existing 21-model Sales replacement scope.

This is an operational gate under the dbt advisory lock, not a general SQL firewall.
Concurrent administrative DDL remains prohibited during a supervised build.
"""
from pathlib import Path
import re
import yaml

GROUPS = {
    'staging': ('dw_staging', ('stg_sales_customers','stg_sales_orders','stg_sales_orderlines',
                             'stg_sales_invoices','stg_sales_invoicelines','stg_warehouse_stockitems')),
    'intermediate': ('dw_intermediate', ('int_invoice_header','int_order_header')),
    'quality': ('dq', ('validation_violations','record_status','quarantine_records')),
    'core': ('dw_core', ('dim_date','dim_customer','dim_product','fact_invoice_line','fact_order_line')),
    'marts': ('sales_marts', ('mart_sales_daily','mart_sales_monthly','mart_sales_product_daily',
                           'mart_customer_sales','mart_sales_customer_summary')),
}
MODELS = {(schema,name) for schema,names in GROUPS.values() for name in names}
VIEWS = {('dw_intermediate','int_invoice_header'),('dw_intermediate','int_order_header')}


class DDLPolicyError(ValueError):
    pass


def verify_project(root: Path):
    expected = {root/'models'/group/(name+'.sql') for group,(_,names) in GROUPS.items() for name in names}
    if set((root/'models').rglob('*.sql')) != expected:
        raise DDLPolicyError('DDL_MODEL_SET_REQUIRES_REVIEW')
    config = yaml.safe_load((root/'dbt_project.yml').read_text(encoding='utf-8'))['models']['retail_sales']
    if any(k in config for k in ('+schema','+alias','+database')):
        raise DDLPolicyError('DDL_ROOT_TARGET_OVERRIDE_REQUIRES_REVIEW')
    for path in expected:
        if re.search(r'\b(?:schema|alias|database)\s*=',path.read_text(encoding='utf-8')):
            raise DDLPolicyError('DDL_INLINE_TARGET_OVERRIDE_REQUIRES_REVIEW')
    for group,(schema,names) in GROUPS.items():
        if config[group].get('+schema') != schema or any(k in config[group] for k in ('+alias','+database')):
            raise DDLPolicyError('DDL_SCHEMA_REQUIRES_REVIEW')
        for name in names:
            if any(k in config[group].get(name,{}) for k in ('+schema','+alias','+database')):
                raise DDLPolicyError('DDL_ALIAS_REQUIRES_REVIEW')


def inspect_scope(db, models=None, views=None):
    models = MODELS if models is None else models
    views = VIEWS if views is None else views
    if db.execute('SELECT current_database(),current_user').fetchone() != ('retail_raw','retail_transform'):
        raise DDLPolicyError('DDL_TARGET_IDENTITY_MISMATCH')
    flags = db.execute("SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=current_user").fetchone()
    if flags is None or any(flags):raise DDLPolicyError('DDL_ADMIN_ROLE_NOT_ALLOWED')
    # CREATE/DML/ownership on the protected schemas is never needed for dbt.
    forbidden = db.execute("""SELECT count(*) FROM pg_namespace n WHERE n.nspname IN ('raw','ingestion_meta')
      AND (has_schema_privilege(current_user,n.oid,'CREATE') OR pg_has_role(current_user,n.nspowner,'USAGE'))""").fetchone()[0]
    writable = db.execute("""SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
      WHERE n.nspname IN ('raw','ingestion_meta') AND c.relkind IN ('r','p','v','m')
      AND (pg_has_role(current_user,c.relowner,'USAGE') OR has_table_privilege(current_user,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER'))""").fetchone()[0]
    if forbidden or writable:raise DDLPolicyError('DDL_PROTECTED_SCOPE_WRITABLE')
    rows = db.execute("""SELECT c.oid,n.nspname,c.relname,c.relkind,pg_get_userbyid(c.relowner),c.reltype,t.typarray
      FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
      LEFT JOIN pg_type t ON t.oid=c.reltype WHERE n.nspname=ANY(%s)""",(sorted({s for s,_ in models}),)).fetchall()
    selected=[]
    for row in rows:
        _,schema,name,kind,owner,_,_=row
        if any((schema,name.removesuffix(suffix)) in models for suffix in ('__dbt_tmp','__dbt_backup')) and name.endswith(('__dbt_tmp','__dbt_backup')):
            raise DDLPolicyError('DDL_STALE_ARTIFACT_INSPECT_BEFORE_RERUN')
        if (schema,name) not in models:continue
        if kind not in ('r','v') or owner!='retail_transform':raise DDLPolicyError('DDL_RELATION_OWNER_OR_KIND_MISMATCH')
        selected.append(row)
    oids=[r[0] for r in selected];types=[v for r in selected for v in r[5:7] if v]
    allowed_views={r[0] for r in selected if (r[1],r[2]) in views and r[3]=='v'}
    dependencies=db.execute("""SELECT DISTINCT d.classid::regclass::text,d.objid,r.ev_class
      FROM pg_depend d LEFT JOIN pg_rewrite r ON d.classid='pg_rewrite'::regclass AND r.oid=d.objid
      WHERE d.deptype='n' AND ((d.refclassid='pg_class'::regclass AND d.refobjid=ANY(%s))
       OR (d.refclassid='pg_type'::regclass AND d.refobjid=ANY(%s)))""",(oids,types)).fetchall()
    if any(kind!='pg_rewrite' or view not in allowed_views for kind,_,view in dependencies):
        raise DDLPolicyError('DDL_UNAPPROVED_CASCADE_DEPENDENCY')
    custom=db.execute("SELECT (SELECT count(*) FROM pg_trigger WHERE tgrelid=ANY(%s) AND NOT tgisinternal)+(SELECT count(*) FROM pg_policy WHERE polrelid=ANY(%s))",(oids,oids)).fetchone()[0]
    if custom:raise DDLPolicyError('DDL_CUSTOM_TRIGGER_OR_POLICY_REQUIRES_REVIEW')
    return {'status':'PASS','relations':len(selected),'approved_dependent_views':len({r[2] for r in dependencies})}
