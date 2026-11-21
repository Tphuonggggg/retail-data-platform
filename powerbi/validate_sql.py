"""Reader-only SQL evidence for POWERBI-SALES-01; no source extracts or writes."""
from datetime import datetime,timezone
from decimal import Decimal
import json
from pathlib import Path
import re
import sys
import psycopg

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'docs/analytics/sales-discovery-01'))
from analyze import query_suite

PIN='c825b18e-fc62-4cf1-8837-b37b4c9f9668'
QUERIES=('Q01','Q02','Q03','Q04','Q05','Q06','Q07','Q08','Q09','Q11','Q13','Q14','Q15','Q17','Q19','Q22')


def main():
    private=json.loads((ROOT/'.local/powerbi/connection.json').read_text(encoding='utf-8-sig'))
    assert (private['host'],private['port'],private['database'],private['user'])==('127.0.0.1',55434,'retail_raw','retail_bi_reader')
    private['dbname']=private.pop('database')
    result={'checked_at':datetime.now(timezone.utc).isoformat(),'version':PIN,'queries':{}}
    try:
        with psycopg.connect(**private,autocommit=True) as db:
            assert db.execute('SELECT current_user,current_database()').fetchone()==('retail_bi_reader','retail_raw')
            db.execute("SET statement_timeout=120000");db.execute("SET work_mem='64MB'")
            db.execute('SET jit=off');db.execute('SET max_parallel_workers_per_gather=0');db.execute('SET enable_nestloop=off')
            assert db.execute('SELECT pg_try_advisory_lock(941061),pg_try_advisory_lock(941062)').fetchone()==(True,True)
            with db.transaction():
                db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                for key,title,query in query_suite():
                    if key not in QUERIES:continue
                    assert not re.search(r'\b(raw|dq|dw_staging|ingestion_meta|dbt_sales_test)\.',query,re.I)
                    cursor=db.execute(query,{'pin':PIN})
                    columns=[c.name for c in cursor.description]
                    result['queries'][key]={'title':title,'rows':[dict(zip(columns,row)) for row in cursor.fetchall()]}
                assert len(result['queries'])==len(QUERIES)
                contracts={
                    'date_unique_dense': "SELECT count(*),count(DISTINCT calendar_date),max(calendar_date)-min(calendar_date)+1 FROM dw_core.dim_date",
                    'product_key_unique': "SELECT count(*),count(DISTINCT product_key),count(DISTINCT stock_item_name) FROM dw_core.dim_product",
                    'buyer_key_unique': "SELECT count(*),count(DISTINCT customer_key),count(DISTINCT customer_name) FROM dw_core.dim_customer",
                    'invoice_line_key_unique': "SELECT count(*),count(DISTINCT source_invoice_line_id) FROM dw_core.fact_invoice_line",
                    'invoice_header_unique': "SELECT count(*),count(DISTINCT source_invoice_id) FROM dw_intermediate.int_invoice_header",
                    'order_header_unique': "SELECT count(*),count(DISTINCT source_order_id) FROM dw_intermediate.int_order_header",
                    'observed_key_orphans': "SELECT count(*) FILTER(WHERE p.product_key IS NULL),count(*) FILTER(WHERE b.customer_key IS NULL),count(*) FILTER(WHERE t.customer_key IS NULL),count(*) FROM dw_core.fact_invoice_line f LEFT JOIN dw_core.dim_product p ON p.product_key=f.observed_product_key LEFT JOIN dw_core.dim_customer b ON b.customer_key=f.buyer_observed_customer_key LEFT JOIN dw_core.dim_customer t ON t.customer_key=f.bill_to_observed_customer_key",
                }
                result['contracts']={key:db.execute(query).fetchone() for key,query in contracts.items()}
                for key,values in result['contracts'].items():
                    if key=='observed_key_orphans':assert values==(0,0,0,228265)
                    else:assert len(set(values))==1
            result['status']='READER_SQL_VERIFIED'
    except Exception as error:
        result['status']='FAIL';result['error_type']=type(error).__name__
    (ROOT/'powerbi/sql-validation.json').write_text(json.dumps(result,default=str,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'queries':len(result['queries'])}))
    return int(result['status']!='READER_SQL_VERIFIED')


if __name__=='__main__':raise SystemExit(main())
