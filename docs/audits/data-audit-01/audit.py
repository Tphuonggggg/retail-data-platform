"""DATA-AUDIT-01. SELECT-only independent audit; no builds, fixtures or repairs."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from contextlib import closing
import csv
from datetime import date,datetime,timezone,timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from uuid import UUID
import psycopg
from psycopg import sql
import yaml

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from ingestion.common.config import settings
from ingestion.common.contracts import select_objects,F2_SQL
from ingestion.extractors.sqlserver import SqlServerSource
from ingestion.loaders.postgres import PostgresTarget

PIN='5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8'
MOD=2**256

def normal(name):
    return re.sub(r'([a-z0-9])([A-Z])',r'\1_\2',re.sub(r'(.)([A-Z][a-z]+)',r'\1_\2',name)).lower()

def canonical(value,kind):
    """Audit-specific typed JSON serialization, independent of ingestion codecs."""
    if value is None:return None
    if kind.startswith('decimal'):
        if not isinstance(value,Decimal):raise ValueError('Non-Decimal exact numeric')
        text=format(value,'f')
        if '.' in text:text=text.rstrip('0').rstrip('.')
        return [kind,'0' if value==0 else text]
    if kind=='int':
        if type(value) is not int:raise ValueError('Integer type mismatch')
        return [kind,str(value)]
    if kind=='bit':
        if type(value) is not bool:raise ValueError('Boolean type mismatch')
        return [kind,value]
    if kind=='date':
        if type(value) is not date:raise ValueError('Date type mismatch')
        return [kind,value.isoformat()]
    if kind=='datetime2(7)':
        if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{7}',value):
            raise ValueError('Exact seven-digit representation missing')
        return [kind,value]
    if kind=='geography' or kind.startswith('varbinary'):
        return [kind,bytes(value).hex()]
    if not isinstance(value,str):raise ValueError('Text type mismatch')
    return [kind,value]

class Stats:
    def __init__(self,obj):
        self.obj=obj;self.count=0;self.total=0;self.xor=0;self.hashes=Counter();self.keys=Counter()
        self.nulls=Counter();self.sums=defaultdict(Decimal);self.periods=Counter()
    def add(self,row):
        payload=[canonical(v,c.source_type) for c,v in zip(self.obj.columns,row,strict=True)]
        encoded=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode('utf-8')
        h=hashlib.sha256(encoded).digest();n=int.from_bytes(h,'big')
        self.count+=1;self.total=(self.total+n)%MOD;self.xor^=n;self.hashes[h]+=1
        names=[c.name for c in self.obj.columns]
        if self.obj.primary_key:self.keys[row[names.index(self.obj.primary_key)]]+=1
        for c,v in zip(self.obj.columns,row):
            if v is None:self.nulls[c.name]+=1
            elif c.source_type=='int' or c.source_type.startswith('decimal'):self.sums[c.name]+=Decimal(v)
        if 'ValidFrom' in names:
            self.periods[(row[0],row[names.index('ValidFrom')],row[names.index('ValidTo')])]+=1
    @property
    def digest(self):
        envelope=f'{self.count}:{self.total:064x}:{self.xor:064x}'
        return hashlib.sha256(envelope.encode()).hexdigest()

class Audit:
    def __init__(self):
        self.cfg=settings(ROOT/'.env');self.rows=[];self.findings=[];self.queries=[];self.details={}
        self.started=datetime.now(timezone.utc);self.pg=None;self.dw=None;self.source=None
    def q(self,db,query,params=(),tag='PG'):
        t=time.perf_counter()
        with db.cursor() as cur:
            cur.execute(query,params or None);result=cur.fetchall()
        self.queries.append({'id':tag,'engine':'PostgreSQL','sql':query,'parameters':list(params),'seconds':round(time.perf_counter()-t,4)})
        return result
    def check(self,section,name,expected,actual,detail='',severity='HIGH',status=None):
        outcome=status or ('PASS' if expected==actual else 'FAIL')
        self.rows.append({'section':section,'check_id':name,'expected':str(expected),'actual':str(actual),
                          'status':outcome,'evidence':detail})
        if outcome in {'FAIL','BLOCKED','DRIFT','WARNING'}:
            self.findings.append({'severity':severity,'check_id':name,'status':outcome,'finding':detail or name,
                                  'expected':str(expected),'actual':str(actual)})
        return outcome
    def connect(self):
        c=self.cfg.target
        options='-c default_transaction_read_only=on -c statement_timeout=120000 -c max_parallel_workers_per_gather=0'
        self.pg=psycopg.connect(host=c.host,port=c.port,dbname=c.database,user=c.user,password=c.password,
                                autocommit=True,connect_timeout=5,options=options)
        secret=json.loads((ROOT/'.local/dbt/connection.json').read_text())['password']
        self.dw=psycopg.connect(host=c.host,port=c.port,dbname=c.database,user='retail_transform',password=secret,
                                autocommit=True,connect_timeout=5,options=options)
        for db,user in [(self.pg,'retail_ingest'),(self.dw,'retail_transform')]:
            self.check('B','IDENTITY_'+user,('retail_raw',user,'on'),self.q(db,"select current_database(),current_user,current_setting('default_transaction_read_only')")[0])
        if not self.q(self.dw,'select pg_try_advisory_lock(941062)')[0][0]:raise RuntimeError('Transformation active; no mixed build audit')
        try:
            self.source=SqlServerSource(self.cfg);self.source.connect()
            self.details['source_identity']={k:self.source.context[k] for k in ['endpoint','instance','database','actual_login','database_user','product_version']}
            self.details['source_security']={'encrypt':True,'development':self.cfg.development,'trust_server_certificate':self.cfg.trust_server_certificate,'admin_opt_in':self.cfg.allow_admin_source}
        except Exception as e:
            self.source=None;self.check('A','SOURCE_CONNECT','reachable',type(e).__name__,'Fresh Source checks unavailable',status='BLOCKED')
    def control(self):
        state={}
        for table in ['runs','object_runs','load_contracts','load_audits','raw_current','raw_publications']:
            data=self.q(self.pg,'select * from ingestion_meta.'+table+' order by 1,2',tag='B_CONTROL_'+table)
            state[table]=hashlib.sha256(json.dumps(data,default=str,sort_keys=True).encode()).hexdigest()
        return state
    def metadata(self):
        run=self.q(self.pg,'select run_id,capture_id,status,consistency_state,extraction_mode,started_at,finished_at from ingestion_meta.runs where run_id=%s',(PIN,),'B_RUN')
        self.check('B','RUN_COUNT',1,len(run));self.check('B','RUN_STATE',('SUCCEEDED','FULL'),(run[0][2],run[0][4]))
        self.details['run']=[str(v) for v in run[0]]
        objs=self.q(self.pg,"select source_schema||'.'||source_table,status,reconciliation_state,source_row_count,extracted_row_count,loaded_row_count from ingestion_meta.object_runs where run_id=%s",(PIN,),'B_OBJECTS')
        expected={o.name for o in select_objects()}
        self.check('B','EXACT_OBJECT_SET',sorted(expected),sorted(r[0] for r in objs))
        self.check('B','OBJECT_RECONCILIATION',0,sum(r[1:3]!=('SUCCEEDED','PASS') or not r[3]==r[4]==r[5] for r in objs))
        audits=self.q(self.pg,'select object_name,row_count,row_digest from ingestion_meta.load_audits where run_id=%s',(PIN,),'B_AUDITS')
        self.check('B','AUDIT_OBJECT_SET',sorted(expected),sorted(r[0] for r in audits))
        self.check('B','PUBLICATION_POINTER',[(None,)],self.q(self.pg,'select publication_id from ingestion_meta.raw_current'))
        self.check('B','PUBLICATION_COUNT',0,self.q(self.pg,'select count(*) from ingestion_meta.raw_publications')[0][0])
        self.details['raw_runs']=self.q(self.pg,'select status,count(*) from ingestion_meta.runs group by 1')
        # Supplementary original capture-audit verification; NOT the source/target independent digest.
        target=PostgresTarget(self.cfg);target.connection=self.pg
        result=target.reconcile(UUID(PIN),select_objects())
        self.check('B','ORIGINAL_INGESTION_AUDIT',0,sum(r['reconciliation']!='PASS' for r in result),
                   'Raw-only legacy digest compared to persisted ingestion audit; Source/Raw uses separate serializer')
    def schema(self,obj):
        all_pg=self.q(self.pg,"select column_name,data_type,is_nullable,numeric_precision,numeric_scale,collation_name from information_schema.columns where table_schema='raw' and table_name=%s order by ordinal_position",(obj.target,),'A_PG_SCHEMA_'+obj.name)
        self.check('B','TECHNICAL_COLUMNS_'+obj.name,[('_run_id','uuid','NO'),('_row_ordinal','bigint','NO')],[tuple(r[:3]) for r in all_pg[:2]])
        pg=all_pg[2:]
        expected=[]
        for c in obj.columns:
            t=c.source_type
            kind='text' if t.startswith(('nvarchar','datetime2')) else 'numeric' if t.startswith('decimal') else 'bytea' if t.startswith('varbinary') or t=='geography' else {'int':'integer','bit':'boolean','date':'date'}[t]
            precision,scale=(tuple(map(int,re.findall(r'\d+',t))) if t.startswith('decimal') else (None,None))
            expected.append((c.name,kind,'YES' if c.nullable else 'NO',precision,scale,'C' if t=='datetime2(7)' else None))
        simplified=[(r[0],r[1],r[2],r[3] if r[1]=='numeric' else None,r[4] if r[1]=='numeric' else None,r[5] if r[0] in [c.name for c in obj.columns if c.source_type=='datetime2(7)'] else None) for r in pg]
        self.check('A','PG_SCHEMA_'+obj.name,expected,simplified,severity='CRITICAL')
        if not self.source:return
        with closing(self.source.connection.cursor()) as cur:
            raw=cur.execute("SELECT c.name,TYPE_NAME(CASE WHEN c.system_type_id=240 THEN c.user_type_id ELSE c.system_type_id END),c.max_length,c.precision,c.scale,c.is_nullable FROM sys.columns c WHERE c.object_id=OBJECT_ID(?, 'U') ORDER BY c.column_id",obj.name).fetchall()
            mapped=[]
            for name,kind,length,p,s,nullable in raw:
                if kind=='nvarchar':kind+='('+('max' if length==-1 else str(length//2))+')'
                elif kind=='varbinary':kind+='('+('max' if length==-1 else str(length))+')'
                elif kind=='decimal':kind+=f'({p},{s})'
                elif kind=='datetime2':kind+=f'({s})'
                mapped.append((name,kind,bool(nullable)))
            expected_source=[(c.name,c.source_type,c.nullable) for c in obj.columns]
            self.check('A','SOURCE_SCHEMA_'+obj.name,expected_source,mapped,severity='HIGH',status='PASS' if expected_source==mapped else 'DRIFT')
            assoc=cur.execute("SELECT t.temporal_type,SCHEMA_NAME(h.schema_id),h.name FROM sys.tables t LEFT JOIN sys.tables h ON h.object_id=t.history_table_id WHERE t.object_id=OBJECT_ID(?)",obj.name).fetchone()
            self.details.setdefault('temporal_associations',{})[obj.name]=list(assoc)
        self.queries.append({'id':'A_SOURCE_SCHEMA_'+obj.name,'engine':'SQL Server','sql':'sys.columns/sys.tables metadata SELECT; see schema()','parameters':[obj.name]})
    def scan(self,obj,source=False,stage=None):
        stats=Stats(obj);t=time.perf_counter()
        if source:
            expressions=[]
            for c in obj.columns:
                operand='['+c.name+']'
                expressions.append(F2_SQL.replace('v.source_value',operand)+' AS '+operand if c.source_type=='datetime2(7)' else 'CONVERT(varbinary(max),'+operand+') AS '+operand if c.source_type=='geography' else operand)
            query='SELECT '+','.join(expressions)+' FROM '+obj.ms_table
            with closing(self.source.connection.cursor()) as cur:
                cur.execute(query)
                while True:
                    rows=cur.fetchmany(1 if any(c.source_type in ('geography','varbinary(max)') for c in obj.columns) else 256)
                    if not rows:break
                    for row in rows:stats.add(row)
        else:
            cols=','.join('"'+(normal(c.name) if stage else c.name)+'"' for c in obj.columns)
            query='SELECT '+cols+' FROM '+('dw_staging.'+stage if stage else obj.pg_table)+('' if stage else ' WHERE _run_id=%s')
            db=self.dw if stage else self.pg
            with db.transaction():
                with db.cursor(name='scan_'+str(time.time_ns())) as cur:
                    cur.execute(query,() if stage else (PIN,))
                    for row in cur:stats.add(row)
        self.queries.append({'id':('C_STAGE_' if stage else 'A_SOURCE_' if source else 'A_RAW_')+obj.name,
                             'engine':'SQL Server' if source else 'PostgreSQL','sql':query,'parameters':[] if source or stage else [PIN],
                             'seconds':round(time.perf_counter()-t,3),'rows':stats.count})
        return stats
    def source_raw_staging(self):
        result=[];self.raw_stats={}
        sales={'Sales.Customers','Sales.Orders','Sales.OrderLines','Sales.Invoices','Sales.InvoiceLines','Warehouse.StockItems'}
        for obj in select_objects():
            self.schema(obj)
            r=self.scan(obj);self.raw_stats[obj.name]=r
            s=self.scan(obj,source=True) if self.source else None
            row={'object':obj.name,'source_now':s.count if s else None,'raw_capture':r.count,'count_difference':s.count-r.count if s else None,
                 'source_digest':s.digest if s else None,'raw_digest':r.digest,'status':'BLOCKED' if s is None else 'PASS' if s.hashes==r.hashes else 'DRIFT'}
            if s:
                self.check('A','SOURCE_RAW_CONTENT_'+obj.name,True,s.hashes==r.hashes,
                           'Independent tagged JSON/SHA256 full-row MULTISET; no ingestion codec. Equality is not point-in-time proof.',
                           status=row['status'],severity='HIGH' if row['status']=='DRIFT' else 'CRITICAL')
                self.check('A','NULL_DISTRIBUTIONS_'+obj.name,dict(s.nulls),dict(r.nulls),status='PASS' if s.nulls==r.nulls else 'DRIFT')
                self.check('A','NUMERIC_SUMS_'+obj.name,{k:str(v) for k,v in s.sums.items()},{k:str(v) for k,v in r.sums.items()},status='PASS' if s.sums==r.sums else 'DRIFT')
                if obj.primary_key:
                    self.check('A','PK_UNIQUENESS_'+obj.name,0,sum(n-1 for n in s.keys.values())+sum(n-1 for n in r.keys.values()),severity='CRITICAL')
                    self.check('A','KEY_PRESERVATION_'+obj.name,True,s.keys==r.keys,severity='HIGH',status='PASS' if s.keys==r.keys else 'DRIFT')
                else:
                    row['history_duplicate_payload_occurrences']=sum(n-1 for n in r.hashes.values())
                    row['history_duplicate_period_keys']=sum(n-1 for n in r.periods.values())
                    self.check('A','HISTORY_OCCURRENCE_MULTISET_'+obj.name,True,s.hashes==r.hashes,severity='HIGH',status='PASS' if s.hashes==r.hashes else 'DRIFT')
                    self.check('A','HISTORY_PK_'+obj.name,'not a current-table PK','not a current-table PK',status='NOT_APPLICABLE')
            base=self.q(self.pg,'select count(*) from '+obj.pg_table,tag='B_BASE_'+obj.name)[0][0]
            row['all_runs_base_rows']=base
            if obj.name in sales:
                stage='stg_'+obj.target
                st=self.scan(obj,stage=stage)
                self.check('C','STAGING_FIDELITY_'+obj.name,True,st.hashes==r.hashes,
                           'All source fields independently serialized; actual view evaluated',severity='CRITICAL')
                self.check('C','STAGING_KEY_SET_'+obj.name,True,st.keys==r.keys,severity='CRITICAL')
                self.check('C','STAGING_CAPTURE_'+obj.name,[(PIN,)],[(str(x[0]),) for x in self.q(self.dw,'select distinct _capture_id from dw_staging.'+stage)],severity='CRITICAL')
            result.append(row);print(obj.name,row['status'],r.count,flush=True)
        self.details['source_raw']=result
        self.check('B','RAW_TOTAL_VS_OBJECT_METADATA',sum(r.count for r in self.raw_stats.values()),
                   self.q(self.pg,'select sum(loaded_row_count) from ingestion_meta.object_runs where run_id=%s',(PIN,))[0][0],severity='CRITICAL')
    def quality(self):
        """Evaluate configured rules in Python on Raw; no production SQL compiler reused."""
        docs={name:yaml.safe_load((ROOT/'dbt/config'/f'{name}.yml').read_text()) for name in ['business_rules','quality_rules','measures','performance']}
        fingerprint=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        version=fingerprint({k:docs[k] for k in ['business_rules','quality_rules']});measure=fingerprint(docs['measures'])
        evaluation=hashlib.md5((PIN+':'+version).encode()).hexdigest()
        self.details['ruleset']=version;self.details['measure_version']=measure
        rules=[r for r in docs['quality_rules']['rules'] if r['enabled']]
        self.check('D','UNIQUE_ENABLED_RULE_IDS',len(rules),len({r['rule_id'] for r in rules}))
        statuses=self.q(self.dw,'select capture_id,source_object,record_identity,source_business_key,_raw_row_ordinal,ruleset_version,evaluation_id,dq_status,is_valid,has_warning,is_quarantined,violation_count from dq.record_status',tag='D_ACTUAL_STATUS')
        actual={r[2]:r for r in statuses};self.check('D','UNIQUE_STATUS',len(statuses),len(actual),severity='HIGH')
        violations=self.q(self.dw,'select capture_id,source_object,record_identity,source_business_key,_raw_row_ordinal,ruleset_version,evaluation_id,rule_id,severity,action,column_name,actual_value from dq.validation_violations',tag='D_ACTUAL_VIOLATIONS')
        expected_v={};expected_status={};byobject=defaultdict(Counter);pools={o.name:set(self.raw_stats[o.name].keys) for o in select_objects() if o.primary_key}
        warnings=[]
        for obj in select_objects():
            rr=[r for r in rules if r['object']==obj.name]
            if not rr:continue
            names=[normal(c.name) for c in obj.columns]
            query='SELECT _row_ordinal,'+','.join('"'+c.name+'"' for c in obj.columns)+' FROM '+obj.pg_table+' WHERE _run_id=%s'
            with self.pg.transaction():
                with self.pg.cursor(name='dq_'+obj.target) as cur:
                    cur.execute(query,(PIN,))
                    for row in cur:
                        ordinal=row[0];values=dict(zip(names,row[1:]));key=values[normal(obj.primary_key)]
                        identity=hashlib.md5(f'{PIN}:{obj.name}:{ordinal}'.encode()).hexdigest();bad=[]
                        for r in rr:
                            v=values[r['column']];e=r['expected'];kind=r['type']
                            if kind=='not_null':failed=v is None
                            elif kind=='unique':failed=self.raw_stats[obj.name].keys[key]>1
                            elif kind=='relationship':failed=v is not None and v not in pools[e['object']]
                            elif kind=='date_order':failed=v is not None and values[e] is not None and v>values[e]
                            elif kind=='min_value':failed=v is not None and v<Decimal(str(e))
                            elif kind=='max_value':failed=v is not None and v>Decimal(str(e))
                            elif kind=='between':failed=v is not None and not Decimal(str(e[0]))<=v<=Decimal(str(e[1]))
                            elif kind=='accepted_values':failed=v is not None and v not in e
                            elif kind=='registered_expression' and e=='credit_note_review':failed=v is True
                            else:raise ValueError('Unsupported independent evaluator rule')
                            if failed:
                                bad.append(r);expected_v[(identity,r['rule_id'])]=(obj.name,str(key),ordinal,r['severity'],r['action'],r['column'])
                                if len(warnings)<3 and r['column']=='line_profit':warnings.append({'record_identity':identity,'source_object':obj.name,'raw_ordinal':ordinal,'line_profit':str(v),'rule_id':r['rule_id']})
                        invalid=any(r['severity']=='ERROR' for r in bad);warning=any(r['severity']=='WARNING' for r in bad);quarantine=any(r['action']=='quarantine' for r in bad)
                        status='INVALID' if invalid else 'WARNING' if warning else 'VALID'
                        expected_status[identity]=(status,not invalid,warning,quarantine,len(bad))
                        byobject[obj.name][status]+=1
                        a=actual.get(identity)
                        correct=a is not None and str(a[0])==PIN and a[1]==obj.name and a[3]==str(key) and a[4]==ordinal and a[5]==version and a[6]==evaluation and tuple(a[7:])==expected_status[identity]
                        if not correct:self.details['dq_status_mismatches']=self.details.get('dq_status_mismatches',0)+1
            self.queries.append({'id':'D_RAW_PYTHON_'+obj.name,'engine':'PostgreSQL','sql':query,'parameters':[PIN]})
        self.check('D','RAW_STATUS_ACCOUNTING',len(expected_status),len(statuses),severity='HIGH')
        self.check('D','INDEPENDENT_RECORD_CLASSIFICATION',0,self.details.get('dq_status_mismatches',0),severity='HIGH')
        observed={(r[2],r[7]):(r[1],r[3],r[4],r[8],r[9],r[10]) for r in violations}
        self.check('D','EXACT_RULE_VIOLATIONS',True,observed==expected_v,'Independent Raw-value Python evaluator vs actual enabled rules, lineage/severity/action',severity='HIGH')
        self.check('D','UNIQUE_VIOLATIONS',len(violations),len(observed))
        self.check('D','VIOLATION_VERSIONS',0,sum(str(v[0])!=PIN or v[5]!=version or v[6]!=evaluation for v in violations))
        quarantine=self.q(self.dw,'select record_identity from dq.quarantine_records',tag='D_QUARANTINE')
        self.check('D','QUARANTINE_MEMBERSHIP',sorted(k for k,v in expected_status.items() if v[3]),sorted(r[0] for r in quarantine),severity='HIGH')
        # Secondary diagnostic representation: observed PG decimal text is hashed in production.
        self.check('D','WARNING_RAW_VALUE_HASH',0,self.q(self.dw,"select count(*) from dq.validation_violations v join raw.sales_invoicelines r on r._run_id=v.capture_id and r._row_ordinal=v._raw_row_ordinal where v.source_object='Sales.InvoiceLines' and v.column_name='line_profit' and (r.\"LineProfit\">=0 or v.actual_value<>('md5:'||md5(r.\"LineProfit\"::text)))",tag='D_WARNING_VALUE')[0][0],severity='MEDIUM')
        self.details['dq_population']={k:dict(v) for k,v in byobject.items()};self.details['warning_samples']=warnings
        self.details['violations_by_rule']=dict(Counter(r[7] for r in violations))
        self.details['dq_counts']={'total':len(statuses),'statuses':dict(Counter(r[7] for r in statuses)),
                                   'violations':len(violations),'violated_records':len({r[2] for r in violations}),'quarantine':len(quarantine)}
        self.expected_status=expected_status
    def dimensions_facts(self):
        for name,key,obj in [('dim_customer','customer_key','Sales.Customers'),('dim_product','product_key','Warehouse.StockItems')]:
            source=self.raw_stats[obj]
            self.check('E','DIM_COUNT_'+name,source.count,self.q(self.dw,'select count(*) from dw_core.'+name)[0][0])
            rawkey='source_customer_id' if 'customer' in name else 'source_stock_item_id';kind='CUSTOMER' if 'customer' in name else 'PRODUCT'
            rows=self.q(self.dw,'select '+key+','+rawkey+',_capture_id,source_valid_from,source_valid_to from dw_core.'+name)
            self.check('E','DIM_UNIQUE_'+name,len(rows),len({r[0] for r in rows}))
            self.check('E','DIM_BUSINESS_KEYS_'+name,0,len(set(source.keys)^{r[1] for r in rows}))
            self.check('E','DIM_NK_UNIQUE_'+name,len(rows),len({r[1] for r in rows}))
            bad=sum(r[0]!=hashlib.md5(f'{kind}:OBSERVED_CAPTURE:{PIN}:{r[1]}'.encode()).hexdigest() or str(r[2])!=PIN for r in rows)
            self.check('E','DETERMINISTIC_OBSERVED_KEY_'+name,0,bad)
        bounds=self.q(self.dw,'select min(d),max(d) from (select "OrderDate" d from raw.sales_orders where _run_id=%s union all select "InvoiceDate" from raw.sales_invoices where _run_id=%s)x',(PIN,PIN),'E_DATE_BOUNDS')[0]
        dates=self.q(self.dw,'select calendar_date,date_key,calendar_year,calendar_month,calendar_day,calendar_quarter,month_start from dw_core.dim_date')
        expected_dates={bounds[0]+timedelta(days=n) for n in range((bounds[1]-bounds[0]).days+1)}
        self.check('E','DATE_COVERAGE',0,len(expected_dates^{r[0] for r in dates}))
        self.check('E','DATE_UNIQUE',len(dates),len({r[1] for r in dates}))
        self.check('E','DATE_ATTRIBUTES',0,sum(r[1]!=int(r[0].strftime('%Y%m%d')) or tuple(r[2:])!=(r[0].year,r[0].month,r[0].day,(r[0].month-1)//3+1,r[0].replace(day=1)) for r in dates))
        self.details['date_range']=[str(x) for x in bounds]
        # All admitted current attributes, not merely dimension keys/row counts.
        for model,table,rawcols,dimcols in [
            ('dim_customer','sales_customers','"CustomerID","CustomerName","CustomerCategoryID","BuyingGroupID","BillToCustomerID","ValidFrom","ValidTo"',
             'source_customer_id,customer_name,customer_category_id,buying_group_id,current_bill_to_customer_id,source_valid_from,source_valid_to'),
            ('dim_product','warehouse_stockitems','"StockItemID","StockItemName","Brand","Size","ColorID","UnitPackageID","OuterPackageID","QuantityPerOuter","IsChillerStock","ValidFrom","ValidTo"',
             'source_stock_item_id,stock_item_name,brand,size,color_id,unit_package_id,outer_package_id,quantity_per_outer,is_chiller_stock,source_valid_from,source_valid_to')]:
            q='with expected as (select '+rawcols+' from raw.'+table+' where _run_id=%s),actual as (select '+dimcols+' from dw_core.'+model+') select count(*) from ((select * from expected except all select * from actual) union all (select * from actual except all select * from expected))x'
            self.check('E','ATTRIBUTE_FIDELITY_'+model,0,self.q(self.dw,q,(PIN,),'E_ATTRIBUTE_'+model)[0][0])
        for model,key,obj,flag in [('fact_invoice_line','source_invoice_line_id','Sales.InvoiceLines','is_sales_eligible'),('fact_order_line','source_order_line_id','Sales.OrderLines','is_order_eligible')]:
            n,distinct=self.q(self.dw,'select count(*),count(distinct '+key+') from dw_core.'+model)[0]
            self.check('F','FACT_COUNT_'+model,self.raw_stats[obj].count,n,severity='CRITICAL');self.check('F','FACT_GRAIN_'+model,n,distinct,severity='CRITICAL')
            parent='Sales.Invoices' if obj=='Sales.InvoiceLines' else 'Sales.Orders'
            rawtable='sales_invoicelines' if obj=='Sales.InvoiceLines' else 'sales_orderlines';parenttable='sales_invoices' if obj=='Sales.InvoiceLines' else 'sales_orders'
            parentkey='InvoiceID' if obj=='Sales.InvoiceLines' else 'OrderID'
            # Derive eligibility from independent statuses via Raw ordinals, not recorded flags.
            raw=self.q(self.dw,'select l._row_ordinal,h._row_ordinal,l."'+parentkey.replace('ID','LineID')+'" from raw.'+rawtable+' l left join raw.'+parenttable+' h on h._run_id=l._run_id and h."'+parentkey+'"=l."'+parentkey+'" where l._run_id=%s',(PIN,),'F_RAW_ELIGIBILITY_'+model)
            expected={pk:(self.expected_status[hashlib.md5(f'{PIN}:{obj}:{ord}'.encode()).hexdigest()][1] and (self.expected_status.get(hashlib.md5(f'{PIN}:{parent}:{pord}'.encode()).hexdigest(),('INVALID',False))[1] if pord else False)) for ord,pord,pk in raw}
            facts=self.q(self.dw,'select '+key+','+flag+',dq_status from dw_core.'+model)
            self.check('F','ELIGIBILITY_'+model,0,sum(expected.get(pk)!=eligible for pk,eligible,status in facts),severity='HIGH')
            flags=self.q(self.dw,'select record_identity,dq_status,is_valid,has_warning,is_quarantined from dw_core.'+model)
            self.check('F','FACT_DQ_FLAGS_'+model,0,sum(tuple(r[1:])!=self.expected_status.get(r[0],())[:4] for r in flags))
            rawkey='InvoiceLineID' if obj=='Sales.InvoiceLines' else 'OrderLineID'
            details=' or f.source_reported_line_profit is distinct from r."LineProfit"' if obj=='Sales.InvoiceLines' else ''
            q='select count(*) from raw.'+rawtable+' r left join dw_core.'+model+' f on f.'+key+'=r."'+rawkey+'" and f._capture_id=r._run_id where r._run_id=%s and (f.source_last_edited_when is distinct from r."LastEditedWhen"'+details+' or f._raw_row_ordinal is distinct from r._row_ordinal or f.source_business_key is distinct from r."'+rawkey+'"::text)'
            self.check('F','EXACT_TEMPORAL_PROFIT_LINEAGE_'+model,0,self.q(self.dw,q,(PIN,),'F_EXACT_'+model)[0][0])
        # Facts and headers are independently checked per field using the read-only dbt SELECTs too.
        self.details['historical_unresolved']=self.q(self.dw,"select count(*) filter(where buyer_lookup_status='U'),count(*) filter(where bill_to_lookup_status='U'),count(*) filter(where product_lookup_status='U') from dw_core.fact_invoice_line")[0]
    def marts(self):
        # Existing independent Raw-based script is a SECONDARY cross-check, never a fixture/build call.
        sys.path.insert(0,str(ROOT/'dbt'))
        import configuration
        import acceptance
        result=acceptance.reconciliation(self.dw,configuration.load())
        self.details['secondary_reconciliation']=result
        for r in result['checks']:
            self.check('G',r['check'],r.get('expected',0),r.get('actual',0),
                       'Fresh independently Raw-derived business formula; ratio threshold from approved YAML',status=r['status'],severity='CRITICAL' if 'amount' in r['check'] else 'HIGH')
        for name,keys in [('mart_sales_daily','sales_date'),('mart_sales_product_daily','invoice_date,source_stock_item_id'),('mart_customer_sales','invoice_date,source_customer_id,customer_role'),('mart_sales_customer_summary','source_customer_id,customer_role'),('mart_sales_monthly','sales_month')]:
            bad=self.q(self.dw,'select count(*) from (select '+keys+' from sales_marts.'+name+' group by '+keys+' having count(*)<>1)x')[0][0]
            self.check('G','MART_GRAIN_'+name,0,bad,severity='CRITICAL')
        role=next(r['value'] for r in yaml.safe_load((ROOT/'dbt/config/business_rules.yml').read_text())['rules'] if r['id']=='BRD-08')
        self.check('G','SINGLE_CUSTOMER_ROLE',[(role,)],self.q(self.dw,'select distinct customer_role from sales_marts.mart_customer_sales'))
        def grouped(name,expected,actual,allow_zero=False):
            a={r[:-1]:r[-1] for r in expected};b={r[:-1]:r[-1] for r in actual}
            bad=sum(a.get(k,0 if allow_zero else None)!=b.get(k,0 if allow_zero else None) for k in set(a)|set(b))
            self.check('G',name,0,bad,'Independent full population grouped comparison')
        for name,rawcol,martcol,table,datecol in [('TAX','TaxAmount','tax_amount','sales_invoicelines','InvoiceDate'),('INCLUDING_TAX','ExtendedPrice','invoice_amount_including_tax','sales_invoicelines','InvoiceDate')]:
            expected=self.q(self.dw,'select i."InvoiceDate",sum(l."'+rawcol+'") from raw.sales_invoicelines l join raw.sales_invoices i on l._run_id=i._run_id and l."InvoiceID"=i."InvoiceID" where l._run_id=%s group by 1',(PIN,),'G_RAW_DAILY_'+name)
            actual=self.q(self.dw,'select sales_date,'+martcol+' from sales_marts.mart_sales_daily')
            grouped('DAILY_'+name,expected,actual,True)
        for name,table,datecol,measure in [('INVOICE','sales_invoices','InvoiceDate','invoice_count'),('ORDER','sales_orders','OrderDate','order_count')]:
            expected=self.q(self.dw,'select "'+datecol+'",count(*) from raw.'+table+' where _run_id=%s group by 1',(PIN,),'G_RAW_DAILY_'+name)
            actual=self.q(self.dw,'select sales_date,'+measure+' from sales_marts.mart_sales_daily')
            grouped('DAILY_'+name+'_COUNT',expected,actual,True)
            if name=='INVOICE':
                expected_month=self.q(self.dw,'select date_trunc(\'month\',"InvoiceDate")::date,count(*) from raw.sales_invoices where _run_id=%s group by 1',(PIN,),'G_RAW_MONTHLY_COUNT')
                grouped('MONTHLY_INVOICE_COUNT',expected_month,self.q(self.dw,'select sales_month,invoice_count from sales_marts.mart_sales_monthly'),True)
        field='CustomerID' if role=='BUYER' else 'BillToCustomerID'
        headers=self.q(self.dw,'select "InvoiceDate","'+field+'",count(*) from raw.sales_invoices where _run_id=%s group by 1,2',(PIN,),'G_RAW_CUSTOMER_HEADERS')
        grouped('CUSTOMER_DAILY_INVOICE_COUNT',headers,self.q(self.dw,'select invoice_date,source_customer_id,invoice_count from sales_marts.mart_customer_sales'))
        summary=self.q(self.dw,'select "'+field+'",min("InvoiceDate"),max("InvoiceDate"),count(*) from raw.sales_invoices where _run_id=%s group by 1',(PIN,),'G_RAW_CUSTOMER_SUMMARY')
        grouped('CUSTOMER_SUMMARY_DATES_COUNTS',summary,self.q(self.dw,'select source_customer_id,first_invoice_date,last_invoice_date,invoice_count from sales_marts.mart_sales_customer_summary'))
        units=self.q(self.dw,'select date_trunc(\'month\',i."InvoiceDate")::date,sum(l."Quantity") from raw.sales_invoicelines l join raw.sales_invoices i on l._run_id=i._run_id and l."InvoiceID"=i."InvoiceID" where l._run_id=%s group by 1',(PIN,),'G_RAW_MONTHLY_UNITS')
        grouped('MONTHLY_UNITS',units,self.q(self.dw,'select sales_month,units_sold from sales_marts.mart_sales_monthly'),True)
        self.details['totals']=self.q(self.dw,'select sum(sales_amount),sum(tax_amount),sum(invoice_amount_including_tax),sum(units_sold),sum(invoice_count),sum(order_count) from sales_marts.mart_sales_daily')[0]
        self.details['model_rows']={}
        for schema,table in self.q(self.dw,"select schemaname,tablename from pg_tables where schemaname in ('dw_core','sales_marts','dq') union all select schemaname,viewname from pg_views where schemaname in ('dw_staging','dw_intermediate')"):
            self.details['model_rows'][schema+'.'+table]=self.q(self.dw,'select count(*) from '+schema+'.'+table)[0][0]
    def storage(self):
        dbsize=self.q(self.dw,'select pg_database_size(current_database())')[0][0]
        self.details['database_bytes']=dbsize
        rows=self.q(self.dw,"select n.nspname,c.relname,c.reltuples::bigint,pg_relation_size(c.oid),pg_indexes_size(c.oid),pg_total_relation_size(c.oid),c.relkind from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname in ('raw','ingestion_meta','dq','dw_core','sales_marts','dbt_sales_test') and c.relkind in ('r','m') order by pg_total_relation_size(c.oid) desc",tag='H_STORAGE')
        output=[]
        for schema,table,estimate,heap,index,total,kind in rows:
            db=self.pg if schema in ('raw','ingestion_meta') else self.dw
            actual=self.q(db,'select count(*) from '+schema+'.'+table,tag='H_ACTUAL_'+schema+'.'+table)[0][0]
            output.append({'schema':schema,'relation':table,'estimated_rows':estimate,'actual_rows_all_captures':actual,
                           'heap_bytes':heap,'index_bytes':index,'total_bytes':total})
        self.details['storage']=output
        self.details['schema_bytes']={schema:sum(r['total_bytes'] for r in output if r['schema']==schema) for schema in sorted({r['schema'] for r in output})}
        self.details['quality_version_storage']=self.q(self.dw,'select sum(pg_column_size(ruleset_version)+pg_column_size(evaluation_id)) from dq.record_status')[0][0]
        self.details['pg_stat_statements']=self.q(self.dw,"select exists(select from pg_extension where extname='pg_stat_statements')")[0][0]
        # No EXPLAIN ANALYZE, ANALYZE, VACUUM or index changes.
        plans=self.q(self.dw,'explain (format json) select sales_date,sales_amount from sales_marts.mart_sales_daily where sales_amount<0',tag='H_SAFE_PLAN')
        self.details['safe_plan']=plans[0][0]
    def model_contracts(self,manifest):
        nodes=[n for n in manifest['nodes'].values() if n['resource_type']=='model']
        expected={(n['schema'],n['alias']) for n in nodes}
        actual=set(self.q(self.dw,"select schemaname,tablename from pg_tables where schemaname in ('dw_core','sales_marts','dq','dw_staging','dw_intermediate') union all select schemaname,viewname from pg_views where schemaname in ('dw_core','sales_marts','dq','dw_staging','dw_intermediate')"))
        self.check('B','EXACT_MODEL_RELATION_SET',expected,actual)
        for n in nodes:
            schema,table=n['schema'],n['alias'];kind='v' if n['config']['materialized']=='view' else 'r'
            actual_kind=self.q(self.dw,'select relkind from pg_class where oid=%s::regclass',(schema+'.'+table,))[0][0]
            self.check('B','MATERIALIZATION_'+table,kind,actual_kind)
            cap='capture_id' if schema=='dq' else '_capture_id'
            invalid=self.q(self.dw,'select count(*) from '+schema+'.'+table+' where '+cap+' is distinct from %s::uuid or ruleset_version is distinct from %s or evaluation_id is distinct from %s',
                           (PIN,self.details['ruleset'],hashlib.md5((PIN+':'+self.details['ruleset']).encode()).hexdigest()),'B_PINS_'+table)[0][0]
            self.check('B','NULL_SAFE_MODEL_PINS_'+table,0,invalid,severity='CRITICAL')
            if schema=='dw_staging':
                definition=self.q(self.dw,'select pg_get_viewdef(%s::regclass,true)',(schema+'.'+table,))[0][0]
                self.check('B','NO_PUBLISHED_VIEW_SOURCE_'+table,False,any(x in definition for x in ['raw.current_','raw_publications','raw_current']))
                self.check('B','EXPLICIT_VIEW_CAPTURE_'+table,True,PIN in definition and '_run_id' in definition)
    def existing_fixtures(self):
        tables=self.q(self.dw,"select c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='dbt_sales_test' and c.relname like 'fixture_%_quarantine' order by c.oid desc")
        if not tables:
            self.check('D','EXISTING_QUARANTINE_FIXTURE','available','missing',status='BLOCKED');return
        prefix=tables[0][0][:-len('_quarantine')]
        if not re.fullmatch(r'fixture_[0-9a-f]{12}',prefix):raise ValueError('Unrecognized fixture identifier')
        expected=self.q(self.dw,'select record_identity from dbt_sales_test.'+prefix+' where tax_amount is null order by 1')
        actual=self.q(self.dw,'select record_identity from dbt_sales_test.'+prefix+'_quarantine order by 1')
        self.check('D','EXISTING_QUARANTINE_FIXTURE',expected,actual,'Existing synthetic records only; audit created no fixture/relations')
        self.details['existing_fixture']={'prefix':prefix,'input_count':self.q(self.dw,'select count(*) from dbt_sales_test.'+prefix)[0][0],
                                         'quarantine_count':len(actual),'states':self.q(self.dw,'select dq_status,count(*) from dbt_sales_test.'+prefix+'_status group by 1')}
    def final_metadata(self):
        counts={r['object']:r['source_now'] for r in self.details['source_raw']}
        for obj in select_objects():
            n=self.q(self.pg,'select count(*),count(distinct _row_ordinal),min(_row_ordinal),max(_row_ordinal) from '+obj.pg_table+' where _run_id=%s',(PIN,),'B_ORDINAL_'+obj.name)[0]
            self.check('B','OCCURRENCE_ORDINAL_'+obj.name,(n[0],n[0],1 if n[0] else None,n[0] if n[0] else None),tuple(n))
            # Failed attempts cannot contribute committed payload records.
            failed=self.q(self.pg,'select count(*) from '+obj.pg_table+" r join ingestion_meta.runs m on m.run_id=r._run_id where m.status='FAILED'",tag='B_FAILED_'+obj.name)[0][0]
            self.check('B','FAILED_ATTEMPT_PAYLOAD_'+obj.name,0,failed,severity='CRITICAL')
            if self.source:
                with closing(self.source.connection.cursor()) as cur:
                    current=cur.execute('SELECT COUNT_BIG(*) FROM '+obj.ms_table).fetchone()[0]
                    pk=[r[0] for r in cur.execute('SELECT c.name FROM sys.indexes i JOIN sys.index_columns ic ON ic.object_id=i.object_id AND ic.index_id=i.index_id JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id WHERE i.object_id=OBJECT_ID(?) AND i.is_primary_key=1 AND ic.key_ordinal>0 ORDER BY ic.key_ordinal',obj.name).fetchall()]
                self.check('A','SOURCE_COUNT_BIG_'+obj.name,counts[obj.name],current,status='PASS' if current==counts[obj.name] else 'DRIFT')
                self.check('A','SOURCE_PK_SCHEMA_'+obj.name,[obj.primary_key] if obj.primary_key else [],pk)
                self.queries.append({'id':'A_SOURCE_COUNT_BIG_'+obj.name,'engine':'SQL Server','sql':'SELECT COUNT_BIG(*) FROM '+obj.ms_table,'parameters':[]})
        # Null-safe measure-contract verification on each model that exposes that column.
        relations=self.q(self.dw,"select table_schema,table_name from information_schema.columns where column_name='measure_version' and table_schema in ('dw_core','dw_intermediate','sales_marts') order by 1,2")
        for schema,table in relations:
            bad=self.q(self.dw,'select count(*) from '+schema+'.'+table+' where measure_version is distinct from %s',(self.details['measure_version'],),'B_MEASURES_'+table)[0][0]
            self.check('B','MEASURE_VERSION_'+table,0,bad)
        if not self.details['pg_stat_statements']:
            self.check('H','HISTORICAL_QUERY_STATISTICS','extension not installed','extension not installed',
                       'pg_stat_statements unavailable; no extension installed by audit',status='NOT_APPLICABLE')
        else:
            self.details['heavy_statement_ids']=self.q(self.dw,'select queryid,calls,total_exec_time,rows from pg_stat_statements order by total_exec_time desc limit 10')
        self.check('H','REPEATED_VERSION_STORAGE','optimization opportunity only',self.details['quality_version_storage'],
                   'Measured ruleset_version + evaluation_id datum bytes in dq.record_status; no migration performed',severity='LOW',status='WARNING')
        self.check('A','POINT_IN_TIME_SOURCE_PROOF','not asserted','not proven',
                   'Current full content equality is not a global source snapshot proof; consistency remains UNVERIFIED',severity='LOW',status='WARNING')
    def compiled_tests(self,project):
        manifest=json.loads((Path(project)/'target/manifest.json').read_text())
        self.model_contracts(manifest)
        results=[]
        for node in manifest['nodes'].values():
            if node['resource_type']!='test':continue
            query=node.get('compiled_code')
            if not query:raise ValueError('Missing compiled test')
            if node.get('config',{}).get('store_failures') or node.get('config',{}).get('store_failures_as'):
                raise ValueError('Mutating test storage configuration: use inspection only')
            text=query.strip().rstrip(';')
            # All executes have a server-side read-only safeguard; compiled SELECT equivalent only.
            n=self.q(self.dw,'select count(*) from ('+text+') audit_failure_rows',tag='I_'+node['name'])[0][0]
            self.check('I','DBT_SELECT_'+node['name'],0,n,'SELECT equivalent of fresh compiled test; no dbt materialization/adapters executed')
            results.append({'test':node['name'],'failures':n})
        self.details['compiled_tests']=results
    def run(self,project):
        try:
            self.connect();before=self.control()
            self.metadata();self.source_raw_staging();self.quality();self.existing_fixtures();self.dimensions_facts();self.marts();self.storage()
            if project:self.compiled_tests(project)
            else:self.check('I','COMPILED_TESTS','available','not provided',status='BLOCKED')
            before_final_metadata=self.control()
            self.final_metadata()
            self.check('B','FINAL_METADATA_UNCHANGED',before_final_metadata,self.control(),severity='CRITICAL')
            self.check('B','METADATA_UNCHANGED',before,self.control(),severity='CRITICAL')
        except Exception as e:
            self.check('RUN','UNEXPECTED_BLOCKER','completed',type(e).__name__,
                       'No repairs performed; inspect failing audit section/query ID',status='BLOCKED')
            # Local diagnostics contain only stack locations; no DB exception/connection strings.
            import traceback
            print('Audit stopped at',[(f.name,f.lineno) for f in traceback.extract_tb(e.__traceback__)],type(e).__name__)
        finally:
            if self.source:self.source.close()
            for db in (self.pg,self.dw):
                if db:db.close()
        return self.save()
    def save(self):
        # Supplemental read-only measurements may repeat an identity check. Keep
        # one identical result; retain differing observations under distinct IDs.
        unique={}
        for row in self.rows:
            key=(row['section'],row['check_id'])
            if key in unique and row==unique[key]:continue
            if key in unique:
                row=dict(row,check_id=row['check_id']+'_repeat')
                key=(row['section'],row['check_id'])
            unique[key]=row
        self.rows=list(unique.values())
        self.details.setdefault('started_at',self.started.isoformat());self.details['finished_at']=datetime.now(timezone.utc).isoformat()
        self.details['baseline_head']='cdfac7f59f6fb4d7fba5e4d27e0c1f6506b8429f'
        self.details['capture_pin']=PIN
        failed=any(r['status'] in ('FAIL','BLOCKED') for r in self.rows)
        drift=any(r['status']=='DRIFT' for r in self.rows)
        self.details['status']='DATA_AUDIT_PARTIAL' if failed or drift else 'DATA_AUDIT_ACCEPTED'
        fields=['section','check_id','expected','actual','status','evidence']
        with (OUT/'reconciliation.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(self.rows)
        with (OUT/'dq_findings.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=['severity','check_id','status','finding','expected','actual']);writer.writeheader();writer.writerows(self.findings)
        storage=self.details.get('storage',[])
        with (OUT/'storage_report.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=['schema','relation','estimated_rows','actual_rows_all_captures','heap_bytes','index_bytes','total_bytes']);writer.writeheader();writer.writerows(storage)
        (OUT/'evidence.json').write_text(json.dumps(self.details,default=str,indent=2),encoding='utf-8')
        (OUT/'queries.json').write_text(json.dumps(self.queries,default=str,indent=2),encoding='utf-8')
        print(self.details['status'],Counter(r['status'] for r in self.rows),flush=True)
        return self.details['status']

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');parser.add_argument('--compiled-project',type=Path)
    args=parser.parse_args()
    if not args.execute:parser.print_help();return 0
    return int(Audit().run(args.compiled_project)!='DATA_AUDIT_ACCEPTED')

if __name__=='__main__':raise SystemExit(main())
