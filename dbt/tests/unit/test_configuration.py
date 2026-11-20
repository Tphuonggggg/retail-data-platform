"""Fast deterministic developer tests: no connections, materialization or source data."""
from pathlib import Path
import sys
import unittest
from copy import deepcopy
from decimal import Decimal
import tempfile
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from configuration import load,validate,ContractError,quality_state,safe_ratio,failure_sql,literal,fingerprint,UniqueLoader

class ConfigTests(unittest.TestCase):
    def setUp(self):self.docs=load()['documents']
    def reject(self,change):
        d=deepcopy(self.docs);change(d)
        with self.assertRaises(ContractError):validate(d)
    def test_valid_configuration(self):self.assertEqual(len(load()['objects']),6)
    def test_unknown_type(self):self.reject(lambda d:d['quality_rules']['rules'][0].update(type='raw_sql'))
    def test_duplicate_rule(self):self.reject(lambda d:d['quality_rules']['rules'].append(d['quality_rules']['rules'][0]))
    def test_severity(self):self.reject(lambda d:d['quality_rules']['rules'][0].update(severity='CRITICAL'))
    def test_action(self):self.reject(lambda d:d['quality_rules']['rules'][0].update(action='DELETE'))
    def test_warning_cannot_quarantine(self):self.reject(lambda d:d['quality_rules']['rules'][0].update(severity='WARNING',action='quarantine'))
    def test_unknown_business_rule(self):self.reject(lambda d:d['business_rules']['rules'][0].update(id='INVENTED'))
    def test_unknown_column(self):self.reject(lambda d:d['quality_rules']['rules'][0].update(column='x); drop table raw.x;--'))
    def test_missing_config(self):self.reject(lambda d:d.pop('measures'))
    def test_measure_dependency(self):self.reject(lambda d:next(m for m in d['measures']['measures'] if m['id']=='S06').update(denominator='S01'))
    def test_free_sql_key(self):self.reject(lambda d:d['quality_rules']['rules'][0].update(sql='true'))
    def test_duplicate_yaml_keys(self):
        with self.assertRaises(ContractError):yaml.load('version: 1\nversion: 2',Loader=UniqueLoader)
    def test_valid_state(self):self.assertEqual(quality_state([])['dq_status'],'VALID')
    def test_warning_state(self):
        s=quality_state([{'severity':'WARNING','action':'flag'}]);self.assertTrue(s['is_valid']);self.assertFalse(s['is_quarantined'])
    def test_invalid_multi(self):
        s=quality_state([{'severity':'WARNING','action':'flag'},{'severity':'ERROR','action':'quarantine'}])
        self.assertEqual(s['dq_status'],'INVALID');self.assertTrue(s['has_warning']);self.assertTrue(s['is_quarantined'])
    def test_eligibility_without_quarantine(self):
        s=quality_state([]);parent_valid=False
        self.assertFalse(s['is_valid'] and parent_valid);self.assertFalse(s['is_quarantined'])
    def test_ratio_null_zero_negative_precision(self):
        self.assertIsNone(safe_ratio(100,0));self.assertIsNone(safe_ratio(None,2))
        self.assertEqual(safe_ratio(Decimal('-10.25'),2),Decimal('-5.125'));self.assertEqual(safe_ratio(0,2),0)
    def test_business_amount_and_fanout(self):
        lines=[{'invoice':1,'extended':Decimal('110.00'),'tax':Decimal('10.00')},{'invoice':1,'extended':Decimal('55.00'),'tax':Decimal('5.00')}]
        amount=sum(x['extended']-x['tax'] for x in lines)
        self.assertEqual(amount,150);self.assertEqual(len({x['invoice'] for x in lines}),1)
    def test_roles(self):
        self.reject(lambda d:next(r for r in d['business_rules']['rules'] if r['id']=='BRD-08').update(value='BOTH'))
        d=deepcopy(self.docs);next(r for r in d['business_rules']['rules'] if r['id']=='BRD-08')['value']='BILL_TO';validate(d)
        invoice={'buyer':7,'bill_to':2};self.assertNotEqual(invoice['buyer'],invoice['bill_to'])
    def test_config_change_observable_reproducible(self):
        d=deepcopy(self.docs);a=fingerprint(d);self.assertEqual(a,fingerprint(deepcopy(d)))
        d['quality_rules']['rules'][-1]['enabled']=False;self.assertNotEqual(a,fingerprint(d))
    def test_registered_operations(self):
        base={'column':'quantity','type':'between','expected':[0,10]}
        self.assertEqual(failure_sql(base),'s.quantity NOT BETWEEN 0 AND 10')
        self.assertIn("''",literal("O'Neil"))
        with self.assertRaises(ContractError):failure_sql(base,'raw')
    def test_relationship_requires_parent_pk(self):
        self.reject(lambda d:next(r for r in d['quality_rules']['rules'] if r['type']=='relationship')['expected'].update(column='customer_name'))
    def test_money_tolerance_cannot_hide_errors(self):
        self.reject(lambda d:d['measures']['reconciliation'].update(amount_absolute_tolerance='1'))
    def quality_gate(self,count):
        from jinja2 import Environment
        from types import SimpleNamespace
        class Errors:
            def raise_compiler_error(self,message):raise ContractError(message)
        template=(Path(__file__).resolve().parents[2]/'macros/capture.sql').read_text()
        context={'execute':True,'run_query':lambda query:SimpleNamespace(rows=[[count]]),
                 'env_var':lambda name:'5abc4a32-3eb6-4d17-9a29-37eb26bfc5f8',
                 'modules':SimpleNamespace(re=__import__('re')),'var':lambda name:load(),
                 'return':lambda value:value,'exceptions':Errors()}
        return Environment(extensions=['jinja2.ext.do']).from_string(template).make_module(context).enforce_quality_gate()
    def test_fail_pipeline_macro_blocks(self):
        with self.assertRaises(ContractError):self.quality_gate(1)
    def test_nonfatal_macro_allows(self):self.assertIn('select 1',self.quality_gate(0))
    def test_accepted_domain_null_cannot_silently_pass(self):
        self.reject(lambda d:d['quality_rules']['rules'][0].update(type='accepted_values',expected=[None]))
    def test_unique_on_unregistered_key_fails_clearly(self):
        self.reject(lambda d:d['quality_rules']['rules'][0].update(type='unique',column='customer_name'))

if __name__=='__main__':unittest.main()
