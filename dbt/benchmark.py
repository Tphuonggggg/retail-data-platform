"""SELECT-only query-plan benchmark using a frozen successful dbt invocation."""
from pathlib import Path
import argparse,json,time
from acceptance import connect,ROOT

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--invocation',required=True)
    p.add_argument('--execute',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not a.execute:p.print_help();return 0
    try:
        from uuid import UUID
        if str(UUID(a.invocation))!=a.invocation:raise ValueError('Invalid invocation')
        query=(ROOT/'.local/dbt/invocations'/a.invocation/'target/compiled/retail_sales/models/quality/validation_violations.sql').read_text(encoding='utf-8')
        out=[]
        with connect() as db:
            db.execute('set default_transaction_read_only=on');db.execute("set statement_timeout='60s'")
            # Same complete six-source query and data in both sessions/settings; no test fixture benchmark.
            for jit in ('on','off'):
                db.execute('set jit='+jit)
                start=time.perf_counter()
                result=db.execute('explain (analyze,buffers,format json) '+query).fetchone()[0]
                out.append({'jit':jit,'wall_seconds':round(time.perf_counter()-start,3),'plan':result})
        a.output.write_text(json.dumps(out,indent=2,default=str),encoding='utf-8')
        print(json.dumps([{'jit':r['jit'],'execution_ms':r['plan'][0]['Execution Time'],'jit_detail':r['plan'][0].get('JIT')} for r in out]));return 0
    except Exception as error:
        print(json.dumps({'status':'FAIL','error_type':type(error).__name__}));return 1
if __name__=='__main__':raise SystemExit(main())
