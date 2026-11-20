"""Independent Raw-based acceptance and isolated PostgreSQL synthetic quality tests."""
from __future__ import annotations
import argparse
from collections import defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
from uuid import uuid4
import psycopg
from psycopg import sql
from configuration import load,OBJECTS,failure_sql,literal,quality_state
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from infrastructure.scripts.check_raw_connection import load_config,read_env_file
CAPTURE='5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8'

def connect():
    c=load_config(read_env_file(ROOT/'.env'))
    if c.port!=55434:raise ValueError('Wrong target')
    secret=json.loads((ROOT/'.local/dbt/connection.json').read_text())['password']
    db=psycopg.connect(host=c.host,port=c.port,dbname=c.database,user='retail_transform',password=secret,autocommit=True)
    if db.execute('select current_database(),current_user').fetchone()!=('retail_raw','retail_transform'):raise ValueError('Wrong identity')
    return db

def report_models(db):
    rows=db.execute("select schemaname,tablename from pg_tables where schemaname in ('dq','dw_core','sales_marts') order by 1,2").fetchall()
    result=[]
    for schema,table in rows:
        count,digest=db.execute(sql.SQL("select count(*),md5(string_agg(h,'' order by h)) from (select md5(row_to_json(t)::text) h from {}.{} t) a").format(sql.Identifier(schema),sql.Identifier(table))).fetchone()
        size=db.execute('select pg_total_relation_size(%s::regclass)',(schema+'.'+table,)).fetchone()[0]
        result.append({'schema':schema,'model':table,'rows':count,'content_digest':digest,'size_bytes':size})
    for schema,table in db.execute("select schemaname,viewname from pg_views where schemaname in ('dw_staging','dw_intermediate') order by 1,2"):
        count=db.execute(sql.SQL('select count(*) from {}.{}').format(sql.Identifier(schema),sql.Identifier(table))).fetchone()[0]
        result.append({'schema':schema,'model':table,'rows':count,'materialization':'view'})
    return result

def reconciliation(db,contract):
    role=contract['customer_role'];role_field='CustomerID' if role=='BUYER' else 'BillToCustomerID'
    tests=[]
    def check(name,expected,actual):
        delta=(actual-expected) if expected is not None and actual is not None else None
        tests.append({'check':name,'expected':expected,'actual':actual,'absolute_difference':abs(delta) if delta is not None else None,
                      'relative_difference':(abs(delta)/abs(expected) if expected else None) if delta is not None else None,
                      'status':'PASS' if expected==actual else 'FAIL'})
    # Independent formulas on Raw, not dbt metric macros or facts.
    expected=db.execute('select count(*),sum("ExtendedPrice"-"TaxAmount"),sum("TaxAmount"),sum("ExtendedPrice"),sum("Quantity") from raw.sales_invoicelines where _run_id=%s',(CAPTURE,)).fetchone()
    actual=db.execute('select count(*),sum(invoiced_sales_before_tax),sum(tax_amount),sum(invoice_amount_including_tax),sum(quantity) from dw_core.fact_invoice_line').fetchone()
    for name,e,a in zip(('invoice_line_count','sales_amount','tax','including_tax','units'),expected,actual):check(name,e,a)
    for table,key,model in [('sales_orders','OrderID','dw_intermediate.int_order_header'),('sales_orderlines','OrderLineID','dw_core.fact_order_line'),('sales_invoices','InvoiceID','dw_intermediate.int_invoice_header')]:
        e=db.execute(sql.SQL('select count(*),count(distinct {}) from raw.{} where _run_id=%s').format(sql.Identifier(key),sql.Identifier(table)),(CAPTURE,)).fetchone()
        a=db.execute(sql.SQL('select count(*) from {}').format(sql.SQL(model))).fetchone()[0];check(table+'_count',e[0],a);check(table+'_distinct',e[1],a)
    for model in ('mart_sales_daily','mart_sales_product_daily','mart_customer_sales','mart_sales_customer_summary','mart_sales_monthly'):
        a=db.execute(sql.SQL('select sum(sales_amount),sum(units_sold) from sales_marts.{}').format(sql.Identifier(model))).fetchone()
        check(model+'_amount',expected[1],a[0]);check(model+'_units',expected[4],a[1])
    count=db.execute('select count(*) from raw.sales_invoices where _run_id=%s',(CAPTURE,)).fetchone()[0]
    for model in ('mart_sales_daily','mart_customer_sales','mart_sales_customer_summary','mart_sales_monthly'):
        a=db.execute(sql.SQL('select sum(invoice_count) from sales_marts.{}').format(sql.Identifier(model))).fetchone()[0];check(model+'_invoice_count',count,a)
    # Grouped full outer comparisons; exact amounts, no tolerances on money.
    for label,raw_group,model,mart_group in [
      ('date','i."InvoiceDate"','mart_sales_daily','sales_date'),
      ('product','i."InvoiceDate",l."StockItemID"','mart_sales_product_daily','invoice_date,source_stock_item_id'),
      ('customer','i."InvoiceDate",i."'+role_field+'"','mart_customer_sales','invoice_date,source_customer_id')]:
        raw=db.execute('select '+raw_group+',sum(l."ExtendedPrice"-l."TaxAmount"),sum(l."Quantity") from raw.sales_invoicelines l join raw.sales_invoices i on i._run_id=l._run_id and i."InvoiceID"=l."InvoiceID" where l._run_id=%s group by '+raw_group,(CAPTURE,)).fetchall()
        actuals=db.execute('select '+mart_group+',sales_amount,units_sold from sales_marts.'+model).fetchall()
        exp={r[:-2]:(r[-2],r[-1]) for r in raw};act={r[:-2]:(r[-2],r[-1]) for r in actuals}
        bad=sum(exp.get(k,(0,0))!=act.get(k,(0,0)) for k in set(exp)|set(act))
        check('grouped_'+label+'_mismatch_groups',0,bad)
    product_counts=db.execute('select i."InvoiceDate",l."StockItemID",count(distinct l."InvoiceID") from raw.sales_invoicelines l join raw.sales_invoices i on i._run_id=l._run_id and i."InvoiceID"=l."InvoiceID" where l._run_id=%s group by 1,2',(CAPTURE,)).fetchall()
    actual_product_counts=db.execute('select invoice_date,source_stock_item_id,product_filtered_invoice_count from sales_marts.mart_sales_product_daily').fetchall()
    expected_counts={r[:2]:r[2] for r in product_counts};observed_counts={r[:2]:r[2] for r in actual_product_counts}
    check('product_distinct_invoice_mismatch_groups',0,
          sum(expected_counts.get(k)!=observed_counts.get(k) for k in set(expected_counts)|set(observed_counts)))
    # Additive accounting explicitly reports excluded records and contributions.
    included=db.execute('select count(*),coalesce(sum(invoiced_sales_before_tax),0) from dw_core.fact_invoice_line where is_sales_eligible').fetchone()
    excluded=db.execute('select count(*),coalesce(sum(invoiced_sales_before_tax),0) from dw_core.fact_invoice_line where not is_sales_eligible').fetchone()
    check('included_plus_excluded_rows',expected[0],included[0]+excluded[0]);check('included_plus_excluded_amount',expected[1],included[1]+excluded[1])
    check('unexplained_exclusions',0,excluded[0])
    unresolved=db.execute("select count(*) filter(where buyer_lookup_status='U'),count(*) filter(where bill_to_lookup_status='U'),count(*) filter(where product_lookup_status='U') from dw_core.fact_invoice_line").fetchone()
    # Independent Raw header/line populations and Decimal division; ratio-only tolerance
    # covers PostgreSQL numeric division scale, never monetary reconciliation.
    tolerance=Decimal(str(contract['documents']['measures']['reconciliation']['ratio_absolute_tolerance']))
    raw_daily=dict(db.execute('select "InvoiceDate",count(*) from raw.sales_invoices where _run_id=%s group by 1',(CAPTURE,)))
    amounts=dict(db.execute('select i."InvoiceDate",sum(l."ExtendedPrice"-l."TaxAmount") from raw.sales_invoicelines l join raw.sales_invoices i on i._run_id=l._run_id and i."InvoiceID"=l."InvoiceID" where l._run_id=%s group by 1',(CAPTURE,)))
    ratio_checks=[]
    def ratio_check(name,e,a):
        difference=abs(e-a) if e is not None and a is not None else None
        ratio_checks.append({'check':name,'absolute_difference':difference,
            'status':'PASS' if (e is None and a is None) or (difference is not None and difference<=tolerance) else 'FAIL'})
    for day,actual_ratio in db.execute('select sales_date,average_invoice_value_before_tax from sales_marts.mart_sales_daily'):
        expected_ratio=amounts.get(day,Decimal(0))/raw_daily[day] if raw_daily.get(day) else None
        ratio_check('AIV_'+str(day),expected_ratio,actual_ratio)
    raw_months=dict(db.execute('select date_trunc(\'month\',i."InvoiceDate")::date,sum(l."ExtendedPrice"-l."TaxAmount") from raw.sales_invoicelines l join raw.sales_invoices i on i._run_id=l._run_id and i."InvoiceID"=l."InvoiceID" where l._run_id=%s group by 1',(CAPTURE,)))
    month_rows=db.execute('select sales_month,sales_amount,full_calendar_month,mom_sales_growth,yoy_sales_growth from sales_marts.mart_sales_monthly order by sales_month').fetchall()
    lo,hi=db.execute('select min("InvoiceDate"),max("InvoiceDate") from raw.sales_invoices where _run_id=%s',(CAPTURE,)).fetchone()
    import calendar
    for n,(month,amount,complete,mom,yoy) in enumerate(month_rows):
        check('month_amount_'+str(month),raw_months.get(month,Decimal(0)),amount)
        expected_complete=month>=lo and month.replace(day=calendar.monthrange(month.year,month.month)[1])<=hi
        check('month_coverage_'+str(month),expected_complete,complete)
        for offset,value,label in ((1,mom,'MOM'),(12,yoy,'YOY')):
            comparator=month_rows[n-offset] if n>=offset else None
            old=raw_months.get(comparator[0],Decimal(0)) if comparator else None
            old_complete=(comparator[0]>=lo and comparator[0].replace(day=calendar.monthrange(comparator[0].year,comparator[0].month)[1])<=hi) if comparator else False
            expected_ratio=(raw_months.get(month,Decimal(0))-old)/old if old and expected_complete and old_complete else None
            ratio_check(label+'_'+str(month),expected_ratio,value)
    tests.append({'check':'independent_ratios','comparisons':len(ratio_checks),'tolerance':tolerance,
                  'max_absolute_difference':max((t['absolute_difference'] or Decimal(0) for t in ratio_checks),default=Decimal(0)),
                  'status':'PASS' if all(t['status']=='PASS' for t in ratio_checks) else 'FAIL'})
    # Exact configured capture and one ruleset/measure version in every output.
    for schema,table in db.execute("select schemaname,tablename from pg_tables where schemaname in ('dq','dw_core','sales_marts')"):
        cap='capture_id' if schema=='dq' else '_capture_id'
        n=db.execute(sql.SQL('select count(*) from {}.{} where {}<>%s or ruleset_version<>%s').format(sql.Identifier(schema),sql.Identifier(table),sql.Identifier(cap)),(CAPTURE,contract['ruleset_version'])).fetchone()[0]
        check(schema+'.'+table+'_pin_and_ruleset',0,n)
    return {'checks':tests,'included':included,'excluded':excluded,'unresolved_historical_roles':unresolved,
            'role':role,'status':'PASS' if all(t['status']=='PASS' for t in tests) else 'FAIL'}

def fixtures(db,contract):
    """Real PostgreSQL rule engine in a separately approved schema; no Raw writes."""
    missing_capture_rejected=False
    try:
        with db.transaction():db.execute('select dw_staging.assert_capture(%s)',(uuid4(),))
    except psycopg.errors.RaiseException:
        missing_capture_rejected=True
    if not missing_capture_rejected:raise ValueError('Missing capture was not rejected')
    ident='fixture_'+uuid4().hex[:12]
    source=next(o for o in json.loads((ROOT/'ingestion/common/source_contract.json').read_text())['objects'] if o['table']=='InvoiceLines')
    from configuration import snake
    cols=[];defaults={}
    for c in source['columns']:
        n=snake(c['name']);t=c['source_type'];typ='integer' if t=='int' else 'numeric' if t.startswith('decimal') else 'text'
        cols.append(sql.SQL('{} {}').format(sql.Identifier(n),sql.SQL(typ)))
        defaults[n]=1 if t=='int' else Decimal('5.00') if t.startswith('decimal') else '2020-01-01T00:00:00.1234567' if t.startswith('datetime') else 'SYNTHETIC EXAMPLE'
    invoice=db.execute('select min(invoice_id) from dw_staging.stg_sales_invoices').fetchone()[0]
    product=db.execute('select min(stock_item_id) from dw_staging.stg_warehouse_stockitems').fetchone()[0]
    base=dict(defaults,invoice_id=invoice,stock_item_id=product,extended_price=Decimal('110.00'),tax_amount=Decimal('10.00'),line_profit=Decimal('5.00'),quantity=2)
    chosen=[r for r in contract['rules'] if r['object']=='Sales.InvoiceLines']
    with db.transaction():
        db.execute(sql.SQL('create table dbt_sales_test.{} (_capture_id uuid,record_identity text,parent_is_valid boolean,{}, _key_count bigint)').format(sql.Identifier(ident),sql.SQL(',').join(cols)))
        fields=['_capture_id','record_identity','parent_is_valid']+list(base)+['_key_count']
        for i in range(1,6):
            row=dict(base,invoice_line_id=i)
            if i==2:row['line_profit']=Decimal('-1')
            if i in (3,4):row['tax_amount']=None
            if i==4:row['invoice_id']=-99999
            values=[CAPTURE,'SYNTHETIC_'+str(i),i!=5]+list(row.values())+[1]
            db.execute(sql.SQL('insert into dbt_sales_test.{} ({}) values ({})').format(sql.Identifier(ident),sql.SQL(',').join(map(sql.Identifier,fields)),sql.SQL(',').join(sql.Placeholder() for _ in fields)),values)
        union=[]
        joins=next(o['joins_sql'] for o in contract['objects'] if o['source_object']=='Sales.InvoiceLines')
        for r in chosen:
            union.append('select s.record_identity,'+literal(r['rule_id'])+' as rule_id,'+literal(r['severity'])+' as severity,'+literal(r['action'])+' as action from dbt_sales_test.'+ident+' s '+joins+' where '+r['failure_sql'])
        db.execute('create table dbt_sales_test.'+ident+'_violations as '+' union all '.join(union))
        db.execute('create table dbt_sales_test.'+ident+"_status as select s.record_identity,s.parent_is_valid,case when bool_or(v.severity='ERROR') then 'INVALID' when bool_or(v.severity='WARNING') then 'WARNING' else 'VALID' end as dq_status,coalesce(bool_or(v.action='quarantine'),false) as is_quarantined,count(v.rule_id) as violation_count from dbt_sales_test."+ident+' s left join dbt_sales_test.'+ident+'_violations v using(record_identity) group by 1,2')
        db.execute('create table dbt_sales_test.'+ident+'_quarantine as select * from dbt_sales_test.'+ident+'_status where is_quarantined')
    observed=db.execute('select record_identity,dq_status,is_quarantined,violation_count from dbt_sales_test.'+ident+'_status order by record_identity').fetchall()
    expected=[('SYNTHETIC_1','VALID',False,0),('SYNTHETIC_2','WARNING',False,1),('SYNTHETIC_3','INVALID',True,1),('SYNTHETIC_4','INVALID',True,2),('SYNTHETIC_5','VALID',False,0)]
    gate=db.execute("select count(*) from dbt_sales_test."+ident+"_status where dq_status='VALID' and not parent_is_valid and not is_quarantined").fetchone()[0]
    duplicate=db.execute('select count(*) from (select count(*) over(partition by id) as _key_count from (values(1),(1))x(id))s where s._key_count>1').fetchone()[0]
    return {'status':'PASS' if observed==expected and gate==1 and duplicate==2 else 'FAIL','schema':'dbt_sales_test','table_prefix':ident,
            'ruleset_version':contract['ruleset_version'],
            'origin':'SYNTHETIC_EXAMPLE_ONLY','observed':observed,'expected':expected,'eligibility_exclusion_without_quarantine':gate,
            'duplicate_occurrences_flagged':duplicate,
            'missing_capture_rejected':missing_capture_rejected,
            'quarantine_rows':db.execute('select count(*) from dbt_sales_test.'+ident+'_quarantine').fetchone()[0]}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['snapshot','reconcile','fixtures']);p.add_argument('--execute',action='store_true');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if not a.execute:p.print_help();return 0
    try:
        with connect() as db:
            if a.mode!='fixtures':db.execute('set default_transaction_read_only=on')
            db.execute('select dw_staging.assert_capture(%s)',(CAPTURE,))
            contract=load()
            result=({'models':report_models(db)} if a.mode=='snapshot' else reconciliation(db,contract) if a.mode=='reconcile' else fixtures(db,contract))
            result['publication_count']=db.execute('select count(*) from ingestion_meta.raw_publications').fetchone()[0]
            result['publication_pointer']=db.execute('select publication_id from ingestion_meta.raw_current').fetchone()[0]
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,default=str,indent=2),encoding='utf-8')
        print(json.dumps({'status':result.get('status','PASS'),'evidence':str(a.output)}));return int(result.get('status','PASS')!='PASS')
    except Exception as error:
        print(json.dumps({'status':'FAIL','error_type':type(error).__name__,'message':'Inspect acceptance evidence and query contracts; no secrets logged'}));return 1

if __name__=='__main__':raise SystemExit(main())
