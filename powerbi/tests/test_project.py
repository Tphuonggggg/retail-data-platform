"""Structural BI regression checks. These never imply rendered/DAX acceptance."""
import json
from pathlib import Path
import unittest
import subprocess

ROOT=Path(__file__).resolve().parents[2]
PROJECT=ROOT/'powerbi/RetailSalesAnalytics'
legacy=PROJECT/'RetailSalesAnalytics.SemanticModel/model.bim'
if legacy.exists():
    MODEL=json.loads(legacy.read_text(encoding='utf-8'))['model']
else:
    serialized=subprocess.run(['powershell.exe','-NoProfile','-File',str(ROOT/'powerbi/export_model_metadata.ps1')],capture_output=True,encoding='utf-8-sig',check=True).stdout
    MODEL=json.loads(serialized)
TABLES={t['name']:t for t in MODEL['tables']}
MEASURES={m['name']:m for m in TABLES['Metrics']['measures']}


class ProjectTests(unittest.TestCase):
    def test_six_imports_only_and_no_embedded_source_rows(self):
        imports=[t for t in MODEL['tables'] if t['partitions'][0]['source']['type']=='m']
        self.assertEqual({t['name'] for t in imports},{'Date','Product','Buyer','Invoice Lines','Invoices','Orders'})
        for t in imports:
            m=t['partitions'][0]['source']['expression']
            self.assertIn('PostgreSQL.Database("127.0.0.1:55434", "retail_raw"',m)
            self.assertIn('c825b18e-fc62-4cf1-8837-b37b4c9f9668',m)
            for banned in ('Binary.FromText','File.Contents','Value.NativeQuery','password','Username','dw_staging','ingestion_meta','Schema="raw"','Schema="dq"'):
                self.assertNotIn(banned,m)

    def test_relationships_are_explicit_single_direction_dimension_edges(self):
        self.assertEqual(len(MODEL['relationships']),9)
        for r in MODEL['relationships']:
            # TOM's canonical serializer omits these standard defaults.
            self.assertEqual(r.get('fromCardinality','many'),'many');self.assertEqual(r.get('toCardinality','one'),'one')
            self.assertEqual(r.get('crossFilteringBehavior','oneDirection'),'oneDirection')
            self.assertIn(r['toTable'],{'Date','Product','Buyer','Bill-to'})
            self.assertIn(r['fromTable'],{'Invoice Lines','Invoices','Orders'})
            self.assertNotIn('source_business_key',(r['fromColumn'],r['toColumn']))

    def test_observed_keys_not_unresolved_history_keys(self):
        for r in MODEL['relationships']:
            if r['toTable'] in ('Buyer','Bill-to','Product'):
                self.assertIn('observed',r['fromColumn'])

    def test_financial_precision_calendar_and_technical_hiding(self):
        columns={c['name']:c for c in TABLES['Invoice Lines']['columns']}
        for name in ('invoiced_sales_before_tax','tax_amount','invoice_amount_including_tax','source_reported_line_profit'):
            self.assertEqual(columns[name]['dataType'],'decimal')
        self.assertTrue(columns['_capture_id']['isHidden'])
        date={c['name']:c for c in TABLES['Date']['columns']}
        self.assertTrue(date['calendar_date']['isKey'])
        self.assertEqual(date['Year Month']['sortByColumn'],'Year Month Sort')

    def test_header_counts_and_recomputed_ratio(self):
        self.assertIn('COUNTROWS(Invoices)',MEASURES['Invoice Count']['expression'])
        self.assertIn('TREATAS',MEASURES['Invoice Count']['expression'])
        self.assertIn('COUNTROWS(Orders)',MEASURES['Order Count']['expression'])
        self.assertIn('DIVIDE(',MEASURES['Average Invoice Value']['expression'])
        self.assertIn('CONVERT([Total Sales Before Tax], DOUBLE)',MEASURES['Average Invoice Value']['expression'])
        self.assertIn('[Invoice Count]',MEASURES['Average Invoice Value']['expression'])

    def test_comparisons_and_diagnostic_limit(self):
        self.assertIn('HASONEVALUE',MEASURES['Sales Previous Year Comparable Period']['expression'])
        self.assertIn('ISBLANK',MEASURES['Interaction Contribution']['expression'])
        self.assertIn('BLOCKED',MEASURES['Backorder Diagnostic Status']['expression'])

    def test_real_bindings_and_page_navigation_targets(self):
        pages=json.loads((PROJECT/'RetailSalesAnalytics.Report/definition/pages/pages.json').read_text())['pageOrder']
        self.assertEqual(len(pages),8)
        primary=pages[:4]
        for page in pages:
            directory=PROJECT/'RetailSalesAnalytics.Report/definition/pages'/page
            visuals=[json.loads(p.read_text()) for p in directory.glob('visuals/*/visual.json')]
            links=[]
            for v in visuals:
                self.assertLessEqual(v['position']['x']+v['position']['width'],1920)
                self.assertLessEqual(v['position']['y']+v['position']['height'],1080)
                for state in v['visual'].get('query',{}).get('queryState',{}).values():
                    for projection in state['projections']:
                        field=projection['field'];kind=next(iter(field));item=field[kind]
                        table=item['Expression']['SourceRef']['Entity']
                        self.assertIn(table,TABLES)
                        if kind=='Measure':self.assertIn(item['Property'],MEASURES)
                        else:self.assertIn(item['Property'],{c['name'] for c in TABLES[table]['columns']})
                for link in v['visual'].get('visualContainerObjects',{}).get('visualLink',[]):
                    if 'navigationSection' in link['properties']:
                        value=link['properties']['navigationSection']['expr']['Literal']['Value'].strip("'")
                        links.append(value)
            if page in primary:
                self.assertTrue(set(primary).issubset(links))
                self.assertEqual(len(set(links)),5)
            else:
                self.assertEqual(json.loads((directory/'page.json').read_text(encoding='utf-8'))['visibility'],'HiddenInViewMode')


if __name__=='__main__':unittest.main()
