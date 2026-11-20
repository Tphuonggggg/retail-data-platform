"""Closed, typed YAML contracts. Configuration selects registered operations, never SQL."""
from __future__ import annotations
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
OBJECTS = {
 'Sales.Customers': ('stg_sales_customers','sales_customers','CustomerID','customer_id'),
 'Sales.Orders': ('stg_sales_orders','sales_orders','OrderID','order_id'),
 'Sales.OrderLines': ('stg_sales_orderlines','sales_orderlines','OrderLineID','order_line_id'),
 'Sales.Invoices': ('stg_sales_invoices','sales_invoices','InvoiceID','invoice_id'),
 'Sales.InvoiceLines': ('stg_sales_invoicelines','sales_invoicelines','InvoiceLineID','invoice_line_id'),
 'Warehouse.StockItems': ('stg_warehouse_stockitems','warehouse_stockitems','StockItemID','stock_item_id'),
}
TYPES={'not_null','unique','accepted_values','min_value','max_value','between','relationship','date_order','registered_expression'}
MEASURES={
 'S01':('int_order_header','OrderID','count','OrderDate'),
 'S02':('int_invoice_header','InvoiceID','count','InvoiceDate'),
 'S03':('fact_invoice_line','InvoiceLineID','sum','InvoiceDate'),
 'S04':('fact_invoice_line','InvoiceLineID','sum','InvoiceDate'),
 'S05':('fact_invoice_line','InvoiceLineID','sum','InvoiceDate'),
 'S06':('fact_invoice_line','InvoiceLineID','ratio','InvoiceDate'),
 'UNITS':('fact_invoice_line','InvoiceLineID','sum','InvoiceDate'),
 'C03':('fact_invoice_line','InvoiceLineID','sum','InvoiceDate'),
 'MOM':('mart_sales_monthly','month','growth','InvoiceDate'),
 'YOY':('mart_sales_monthly','month','growth','InvoiceDate'),
}

class ContractError(ValueError): pass

class UniqueLoader(yaml.SafeLoader): pass
def _mapping(loader,node,deep=False):
    out={}
    for k,v in node.value:
        key=loader.construct_object(k,deep=deep)
        if key in out: raise ContractError('Duplicate YAML key')
        out[key]=loader.construct_object(v,deep=deep)
    return out
UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,_mapping)

def snake(value):
    value=re.sub(r'(.)([A-Z][a-z]+)',r'\1_\2',value)
    return re.sub(r'([a-z0-9])([A-Z])',r'\1_\2',value).lower()

def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def literal(value):
    if value is None:return 'NULL'
    if type(value) is bool:return 'true' if value else 'false'
    if type(value) in (int,float):
        if not Decimal(str(value)).is_finite():raise ContractError('Non-finite boundary')
        return str(value)
    if type(value) is str:return "'"+value.replace("'","''")+"'"
    raise ContractError('Unsupported scalar')

def _keys(obj,allowed,required):
    if type(obj) is not dict or set(obj)-set(allowed) or set(required)-set(obj):
        raise ContractError('Missing/unknown configuration keys')

def validate(documents):
    docs=deepcopy(documents)
    if set(docs)!={'business_rules','measures','quality_rules','performance'}:
        raise ContractError('Missing configuration file')
    b=docs['business_rules']
    _keys(b,{'version','rules'}, {'version','rules'})
    expected={'BRD-01':'SEPARATE_HEADERS','BRD-02':'ORDER_AND_INVOICE_DATE',
              'BRD-03':'EXTENDED_PRICE_MINUS_TAX','BRD-04':'RECOGNIZED_REVENUE_DEFERRED',
              'BRD-06':'AGGREGATE_NUMERATOR_OVER_HEADER_COUNT','BRD-07':'NO_REFUND_INFERENCE',
              'BRD-08':None,'BRD-10':'NO_PAYMENT_ALLOCATION'}
    if {r.get('id') for r in b['rules']}!=set(expected) or len(b['rules'])!=len(expected):
        raise ContractError('Unknown/duplicate/missing business rule ID')
    for r in b['rules']:
        _keys(r,{'id','enabled','version','value','null_behavior','zero_negative_behavior'},
              {'id','enabled','version','value','null_behavior','zero_negative_behavior'})
        if r['enabled'] is not True or r['null_behavior']!='PRESERVE_OPTIONAL_QUARANTINE_REQUIRED' or r['zero_negative_behavior']!='PRESERVE_AND_REVIEW':
            raise ContractError('Unsupported business semantics')
        if r['id']=='BRD-08':
            if r['value'] not in {'BUYER','BILL_TO'}:raise ContractError('Select exactly one customer role')
        elif r['value']!=expected[r['id']]:raise ContractError('Unapproved business rule expression')
    q=docs['quality_rules'];_keys(q,{'version','rules'},{'version','rules'})
    source=json.loads((ROOT/'ingestion/common/source_contract.json').read_text())
    columns={o['schema']+'.'+o['table']:{snake(c['name']):c['source_type'] for c in o['columns']} for o in source['objects']}
    seen=set()
    for r in q['rules']:
        _keys(r,{'rule_id','object','column','type','enabled','severity','action','expected','message'},
              {'rule_id','object','column','type','enabled','severity','action','expected','message'})
        if not re.fullmatch(r'[A-Z][A-Z0-9_]{2,80}',str(r['rule_id'])) or r['rule_id'] in seen:
            raise ContractError('Duplicate/invalid rule ID')
        seen.add(r['rule_id'])
        if r['object'] not in OBJECTS or r['column'] not in columns[r['object']]:raise ContractError('Unknown target')
        if r['type'] not in TYPES or type(r['enabled']) is not bool:raise ContractError('Unknown rule type or switch')
        if r['severity'] not in {'WARNING','ERROR'} or r['action'] not in {'flag','quarantine','fail_pipeline'}:raise ContractError('Invalid severity/action')
        if r['severity']=='WARNING' and r['action']!='flag':raise ContractError('Warning cannot quarantine or abort')
        e=r['expected'];kind=r['type']
        if kind in {'not_null','unique'}:
            if e is not True:raise ContractError('Expected true')
        elif kind=='relationship':
            _keys(e,{'object','column'},{'object','column'})
            if e['object'] not in OBJECTS or e['column'] not in columns[e['object']]:raise ContractError('Unknown relationship')
            if e['column']!=OBJECTS[e['object']][3] or columns[r['object']][r['column']]!=columns[e['object']][e['column']]:
                raise ContractError('Relationship must target a compatible source primary key')
        elif kind=='date_order':
            if e not in columns[r['object']]:raise ContractError('Unknown date endpoint')
            if not all(columns[r['object']][c].startswith(('date','datetime')) for c in (r['column'],e)):
                raise ContractError('Date ordering needs date columns')
        elif kind=='registered_expression':
            if not (e=='credit_note_review' and r['object']=='Sales.Invoices' and r['column']=='is_credit_note'):
                raise ContractError('Unknown registered expression')
        elif kind=='accepted_values':
            if type(e) is not list or not e:raise ContractError('Empty/invalid accepted domain')
            for v in e:literal(v)
        else:
            if not columns[r['object']][r['column']].startswith(('int','decimal')):raise ContractError('Numeric rule needs numeric column')
            values=e if kind=='between' else [e]
            if type(values) is not list or (kind=='between' and len(values)!=2):raise ContractError('Invalid interval')
            for v in values:
                if type(v) not in (int,float):raise ContractError('Boundary must be numeric')
                literal(v)
            if kind=='between' and values[0]>values[1]:raise ContractError('Reversed interval')
    m=docs['measures'];_keys(m,{'version','measures','reconciliation'},{'version','measures','reconciliation'})
    _keys(m['reconciliation'],{'amount_absolute_tolerance','ratio_absolute_tolerance'}, {'amount_absolute_tolerance','ratio_absolute_tolerance'})
    try:
        amount=Decimal(str(m['reconciliation']['amount_absolute_tolerance']))
        ratio=Decimal(str(m['reconciliation']['ratio_absolute_tolerance']))
        if not amount.is_finite() or amount!=0 or not ratio.is_finite() or not Decimal(0)<=ratio<=Decimal('1e-9'):
            raise ContractError('Money must reconcile exactly; ratio tolerance must be tightly bounded')
    except Exception as e:
        raise ContractError('Invalid reconciliation tolerance') from e
    ids=[x.get('id') for x in m['measures']]
    if len(ids)!=len(set(ids)) or set(ids)!=set(MEASURES):raise ContractError('Unknown/duplicate/missing measure')
    for x in m['measures']:
        _keys(x,{'id','name','source_fact','grain','aggregation','numerator','denominator','eligibility','date_basis','null_policy','zero_division','dimensions','version'},
              {'id','name','source_fact','grain','aggregation','numerator','denominator','eligibility','date_basis','null_policy','zero_division','dimensions','version'})
        if (x['source_fact'],x['grain'],x['aggregation'],x['date_basis'])!=MEASURES[x['id']]:raise ContractError('Measure contract changed')
        if x['null_policy']!='PRESERVE_OPTIONAL_EXCLUDE_INVALID' or x['zero_division']!='NULL':raise ContractError('Invalid numeric policy')
        if x['eligibility'] not in {'is_sales_eligible','is_order_eligible'}:raise ContractError('Unknown eligibility')
        dependencies={'S06':('S05','S02'),'MOM':('S05','S05'),'YOY':('S05','S05')}
        if (x['numerator'],x['denominator'])!=dependencies.get(x['id'],(None,None)):raise ContractError('Invalid measure dependency')
        if type(x['dimensions']) is not list or set(x['dimensions'])-{'date','product','buyer','bill_to'}:raise ContractError('Unknown dimensions')
    p=docs['performance'];_keys(p,{'version','threads','materialization','indexes'}, {'version','threads','materialization','indexes'})
    if type(p['threads']) is not int or not 1<=p['threads']<=4 or type(p['indexes']) is not bool:raise ContractError('Unsupported execution parameter')
    if p['materialization']!={'staging':'view','intermediate':'view','dq':'table','core':'table','marts':'table'}:raise ContractError('Unsupported materialization')
    for d in docs.values():
        if not isinstance(d['version'],str) or not d['version']:raise ContractError('Version required')
    for r in b['rules']+m['measures']:
        if type(r['version']) is not str or not r['version']:raise ContractError('Rule/measure version required')
    return docs

def failure_sql(rule,schema='dw_staging'):
    if schema not in {'dw_staging','dbt_sales_test'}:raise ContractError('Unapproved relation namespace')
    c='s.'+rule['column'];e=rule['expected'];t=rule['type']
    if t=='not_null':return c+' IS NULL'
    if t=='unique':return 's._key_count > 1'
    if t=='accepted_values':return c+' IS NOT NULL AND '+c+' NOT IN ('+','.join(literal(x) for x in e)+')'
    if t in {'min_value','max_value'}:return c+(' < ' if t=='min_value' else ' > ')+literal(e)
    if t=='between':return c+' NOT BETWEEN '+literal(e[0])+' AND '+literal(e[1])
    if t=='relationship':
        # Parent staging views are explicitly pinned to the same capture by the runner.
        # A NULL-free membership set avoids correlated probes and cannot fan out on duplicates.
        parent='p.'+e['column']
        return c+' IS NOT NULL AND '+c+' NOT IN (SELECT '+parent+' FROM '+schema+'.'+OBJECTS[e['object']][0]+' p WHERE '+parent+' IS NOT NULL)'
    if t=='date_order':return c+' > s.'+e
    if t=='registered_expression':return c+' IS TRUE'
    raise ContractError('Unregistered operation')

def load(path=None):
    path=Path(path or Path(__file__).parent/'config')
    docs=validate({n:yaml.load((path/(n+'.yml')).read_text(encoding='utf-8'),Loader=UniqueLoader)
                   for n in ('business_rules','measures','quality_rules','performance')})
    result={'ruleset_version':fingerprint({k:docs[k] for k in ('business_rules','quality_rules')}),
            'measure_version':fingerprint(docs['measures']), 'documents':docs}
    result['customer_role']=next(r['value'] for r in docs['business_rules']['rules'] if r['id']=='BRD-08')
    result['rules']=[]
    for r in docs['quality_rules']['rules']:
        if not r['enabled']:continue
        alias='rel_'+hashlib.sha256(r['rule_id'].encode()).hexdigest()[:12]
        condition=('s.'+r['column']+' IS NOT NULL AND '+alias+'._parent_key IS NULL') if r['type']=='relationship' else failure_sql(r)
        result['rules'].append(dict(r,failure_sql=condition,join_alias=alias))
    result['objects']=[]
    for k,v in OBJECTS.items():
        joins=[]
        for r in result['rules']:
            if r['object']!=k or r['type']!='relationship':continue
            e=r['expected'];alias=r['join_alias']
            # A distinct parent-key membership set is boolean evidence, not deduplication of source facts.
            joins.append('LEFT JOIN (SELECT DISTINCT '+e['column']+' AS _parent_key,_capture_id FROM dw_staging.'+
                         OBJECTS[e['object']][0]+' WHERE '+e['column']+' IS NOT NULL) '+alias+
                         ' ON '+alias+'._parent_key=s.'+r['column']+' AND '+alias+'._capture_id=s._capture_id')
        result['objects'].append(dict(source_object=k,model=v[0],table=v[1],raw_key=v[2],key=v[3],joins_sql='\n'.join(joins)))
    return result

def quality_state(violations):
    """Small independent fixture oracle; warnings do not become invalid."""
    invalid=any(v['severity']=='ERROR' for v in violations)
    return {'dq_status':'INVALID' if invalid else 'WARNING' if violations else 'VALID',
            'is_valid':not invalid,'has_warning':any(v['severity']=='WARNING' for v in violations),
            'is_quarantined':any(v['action']=='quarantine' for v in violations)}

def safe_ratio(numerator,denominator):
    return None if denominator in (None,0) or numerator is None else Decimal(numerator)/Decimal(denominator)
