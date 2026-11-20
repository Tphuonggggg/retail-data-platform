"""Read-only independent live-source/current-state and Sales reconciliation."""
from __future__ import annotations
import argparse
from collections import Counter
from decimal import Decimal
from itertools import zip_longest
import json
from pathlib import Path
import sys
import time
from uuid import UUID
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'dbt'))
from acceptance import connect
from configuration import load
from ingestion.common.config import settings
from ingestion.common.contracts import pg_quote
from ingestion.extractors.sqlserver import SqlServerSource
from ingestion.incremental import objects,assert_version


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version-id',type=UUID,required=True);p.add_argument('--execute',action='store_true')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--with-sales',action='store_true')
    args=p.parse_args()
    if not args.execute:p.print_help();return 0
    source=None;db=None;tests=[];details={};began=time.perf_counter()
    def check(name,expected,actual):
        tests.append({'check':name,'expected':expected,'actual':actual,'status':'PASS' if expected==actual else 'FAIL'})
    try:
        source=SqlServerSource(settings(ROOT/'.env'));source.connect();source.preflight(objects())
        db=connect();db.execute('SET default_transaction_read_only=on')
        db.execute("SET work_mem='64MB'");db.execute('SET max_parallel_workers_per_gather=0')
        db.execute('SET jit=off')
        check('target_read_only','on',db.execute('SHOW default_transaction_read_only').fetchone()[0])
        check('validated_input_kind','INCREMENTAL',assert_version(db,args.version_id))
        for obj in objects():
            started=time.perf_counter();columns=','.join(pg_quote(c.name) for c in obj.columns)
            key_index=next(i for i,c in enumerate(obj.columns) if c.name==obj.primary_key)
            null_source=Counter();null_target=Counter();source_rows=0;target_rows=0;mismatches=0
            previous_source=previous_target=None;duplicate_source=duplicate_target=0
            expected_count=source.count(obj)
            def incoming():
                for batch in source.batches(obj):
                    for row in batch:yield tuple(bytes(v) if isinstance(v,(bytearray,memoryview)) else v for v in row)
            with db.transaction():
                with db.cursor(name='independent_source_'+obj.target) as cursor:
                    cursor.execute('SELECT '+columns+' FROM raw.sales_state_'+obj.target+'(%s) ORDER BY '+pg_quote(obj.primary_key),(args.version_id,))
                    def current():
                        while batch:=cursor.fetchmany(obj.page_size(500)):
                            yield from (tuple(row) for row in batch)
                    # Native typed equality, no production hash/merge/admission helper.
                    for a,b in zip_longest(incoming(),current()):
                        if a is not None:
                            source_rows+=1
                            if previous_source is not None and a[key_index]<=previous_source:duplicate_source+=1
                            previous_source=a[key_index]
                            null_source.update({c.name:1 for c,v in zip(obj.columns,a) if v is None})
                        if b is not None:
                            target_rows+=1
                            if previous_target is not None and b[key_index]<=previous_target:duplicate_target+=1
                            previous_target=b[key_index]
                            null_target.update({c.name:1 for c,v in zip(obj.columns,b) if v is None})
                        if a!=b:mismatches+=1
            check(obj.name+'_source_count_before_after',expected_count,source.count(obj))
            check(obj.name+'_source_row_count',expected_count,source_rows)
            check(obj.name+'_target_row_count',source_rows,target_rows)
            check(obj.name+'_exact_typed_row_mismatches',0,mismatches)
            check(obj.name+'_source_duplicate_keys',0,duplicate_source)
            check(obj.name+'_target_duplicate_keys',0,duplicate_target)
            check(obj.name+'_all_null_distributions',dict(null_source),dict(null_target))
            details[obj.name]={'rows_scanned':source_rows,'current_rows':target_rows,
                'seconds':round(time.perf_counter()-started,3),'method':'INDEPENDENT_NATIVE_TYPED_ROW_EQUALITY'}
        if args.with_sales:
            pin="'"+str(args.version_id)+"'::uuid"
            lines='raw.sales_state_sales_invoicelines('+pin+')'
            headers='raw.sales_state_sales_invoices('+pin+')'
            orders='raw.sales_state_sales_orders('+pin+')'
            raw=db.execute('SELECT count(*),sum("ExtendedPrice"-"TaxAmount"),sum("TaxAmount"),sum("ExtendedPrice"),sum("Quantity") FROM '+lines).fetchone()
            facts=db.execute('SELECT count(*),sum(invoiced_sales_before_tax),sum(tax_amount),sum(invoice_amount_including_tax),sum(quantity) FROM dw_core.fact_invoice_line WHERE is_sales_eligible').fetchone()
            for name,e,a in zip(('invoice_lines','sales_before_tax','tax','including_tax','units'),raw,facts):check(name,e,a)
            order_count=db.execute('SELECT count(*) FROM '+orders).fetchone()[0]
            invoice_count=db.execute('SELECT count(*) FROM '+headers).fetchone()[0]
            check('order_header_population',order_count,db.execute('SELECT count(*) FROM dw_intermediate.int_order_header').fetchone()[0])
            check('invoice_header_population',invoice_count,db.execute('SELECT count(*) FROM dw_intermediate.int_invoice_header').fetchone()[0])
            check('fact_unique_grain',0,db.execute('SELECT count(*)-count(distinct source_invoice_line_id) FROM dw_core.fact_invoice_line').fetchone()[0])
            check('dq_record_count',sum(d['rows_scanned'] for d in details.values()),db.execute('SELECT count(*) FROM dq.record_status').fetchone()[0])
            # This live dataset has no invalid records. Do not silently exclude
            # invalid rows to force an all-source business-total equality.
            check('live_invalid_records',0,db.execute("SELECT count(*) FROM dq.record_status WHERE dq_status='INVALID'").fetchone()[0])
            check('live_quarantine',0,db.execute('SELECT count(*) FROM dq.quarantine_records').fetchone()[0])
            for schema in ('dw_staging','dw_intermediate','dw_core','sales_marts','dq'):
                for table, in db.execute('SELECT table_name FROM information_schema.columns WHERE table_schema=%s AND column_name=%s',(schema,'_capture_id')):
                    actual=[str(r[0]) for r in db.execute('SELECT distinct _capture_id FROM '+schema+'.'+pg_quote(table))]
                    check(schema+'.'+table+'_input_pin',[str(args.version_id)],actual)
            for model in ('mart_sales_daily','mart_sales_product_daily','mart_customer_sales','mart_sales_customer_summary','mart_sales_monthly'):
                value=db.execute('SELECT sum(sales_amount),sum(units_sold) FROM sales_marts.'+model).fetchone()
                check(model+'_totals',[raw[1],raw[4]],list(value))
                if model!='mart_sales_product_daily':
                    check(model+'_invoice_count',invoice_count,db.execute('SELECT sum(invoice_count) FROM sales_marts.'+model).fetchone()[0])
            check('mart_daily_order_count',order_count,db.execute('SELECT sum(order_count) FROM sales_marts.mart_sales_daily').fetchone()[0])
            role='CustomerID' if load()['customer_role']=='BUYER' else 'BillToCustomerID'
            for label,group,model,keys in [
                ('daily','i."InvoiceDate"','mart_sales_daily','sales_date'),
                ('product','i."InvoiceDate",l."StockItemID"','mart_sales_product_daily','invoice_date,source_stock_item_id'),
                ('customer','i."InvoiceDate",i."'+role+'"','mart_customer_sales','invoice_date,source_customer_id'),
                ('customer_summary','i."'+role+'"','mart_sales_customer_summary','source_customer_id'),
                ('monthly','date_trunc(\'month\',i."InvoiceDate")::date','mart_sales_monthly','sales_month')]:
                expected='SELECT '+group+',sum(l."ExtendedPrice"-l."TaxAmount"),sum(l."Quantity") FROM '+lines+' l JOIN '+headers+' i ON i."InvoiceID"=l."InvoiceID" GROUP BY '+group
                actual='SELECT '+keys+',sales_amount,units_sold FROM sales_marts.'+model+' WHERE sales_amount<>0 OR units_sold<>0'
                n=db.execute('SELECT count(*) FROM (('+expected+' EXCEPT ALL '+actual+') UNION ALL ('+actual+' EXCEPT ALL '+expected+')) mismatch').fetchone()[0]
                check(label+'_independent_group_values',0,n)
            for label,group,model,keys,measure in [
                ('daily_invoice','i."InvoiceDate"','mart_sales_daily','sales_date','invoice_count'),
                ('customer_invoice','i."InvoiceDate",i."'+role+'"','mart_customer_sales','invoice_date,source_customer_id','invoice_count'),
                ('customer_summary_invoice','i."'+role+'"','mart_sales_customer_summary','source_customer_id','invoice_count'),
                ('monthly_invoice','date_trunc(\'month\',i."InvoiceDate")::date','mart_sales_monthly','sales_month','invoice_count')]:
                expected='SELECT '+group+',count(*) FROM '+headers+' i GROUP BY '+group
                actual='SELECT '+keys+','+measure+' FROM sales_marts.'+model+' WHERE '+measure+'>0'
                n=db.execute('SELECT count(*) FROM (('+expected+' EXCEPT ALL '+actual+') UNION ALL ('+actual+' EXCEPT ALL '+expected+')) mismatch').fetchone()[0]
                check(label+'_independent_group_counts',0,n)
            expected='SELECT i."InvoiceDate",l."StockItemID",count(distinct l."InvoiceID") FROM '+lines+' l JOIN '+headers+' i ON i."InvoiceID"=l."InvoiceID" GROUP BY 1,2'
            actual='SELECT invoice_date,source_stock_item_id,product_filtered_invoice_count FROM sales_marts.mart_sales_product_daily'
            n=db.execute('SELECT count(*) FROM (('+expected+' EXCEPT ALL '+actual+') UNION ALL ('+actual+' EXCEPT ALL '+expected+')) mismatch').fetchone()[0]
            check('product_nonadditive_distinct_invoice_counts',0,n)
            tolerance=Decimal(load()['documents']['measures']['reconciliation']['ratio_absolute_tolerance'])
            n=db.execute('WITH amounts AS (SELECT i."InvoiceDate" d,sum(l."ExtendedPrice"-l."TaxAmount") amount FROM '+lines+' l JOIN '+headers+' i ON i."InvoiceID"=l."InvoiceID" GROUP BY 1), '
                'counts AS (SELECT "InvoiceDate" d,count(*) n FROM '+headers+' GROUP BY 1) '
                'SELECT count(*) FROM sales_marts.mart_sales_daily a LEFT JOIN counts c ON c.d=a.sales_date LEFT JOIN amounts e ON e.d=a.sales_date '
                'WHERE ((coalesce(e.amount,0)::numeric/nullif(c.n,0)) IS NULL)<>(a.average_invoice_value_before_tax IS NULL) '
                'OR abs(coalesce(e.amount,0)::numeric/nullif(c.n,0)-a.average_invoice_value_before_tax)>%s',(tolerance,)).fetchone()[0]
            check('daily_aiv_header_population_and_nulls',0,n)
            details['sales_metrics']={'sales_before_tax':str(raw[1]),'tax':str(raw[2]),'including_tax':str(raw[3]),'units':raw[4],
                                      'order_count':order_count,'invoice_count':invoice_count}
        check('publication_pointer_null',[(True,None)],db.execute('SELECT * FROM ingestion_meta.raw_current').fetchall())
        check('publication_count',0,db.execute('SELECT count(*) FROM ingestion_meta.raw_publications').fetchone()[0])
        check('acknowledged_checkpoint_count',0,db.execute('SELECT count(*) FROM ingestion_meta.incremental_versions WHERE acknowledged_publication_id IS NOT NULL').fetchone()[0])
    except Exception as e:
        import traceback
        tests.append({'check':'UNEXPECTED_BLOCKER','status':'BLOCKED','error_type':type(e).__name__,
                      'locations':[(f.name,f.lineno) for f in traceback.extract_tb(e.__traceback__)]})
    finally:
        if source:source.close()
        if db:db.close()
    status='PASS' if tests and all(t['status']=='PASS' for t in tests) else 'FAIL'
    out={'status':status,'version_id':str(args.version_id),'source_consistency':'UNVERIFIED',
         'seconds':round(time.perf_counter()-began,3),'details':details,'checks':tests}
    args.output.write_text(json.dumps(out,default=str,indent=2),encoding='utf-8')
    print(json.dumps({'status':status,'tests':len(tests),'seconds':out['seconds']}));return int(status!='PASS')


if __name__=='__main__':raise SystemExit(main())
