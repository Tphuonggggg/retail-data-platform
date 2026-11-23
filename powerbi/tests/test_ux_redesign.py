"""Contract and geometry regressions for the existing Sales report."""
import hashlib
import json
from pathlib import Path
import unittest
from powerbi.tests.test_project import MEASURES, MODEL

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'powerbi/tests/fixtures'
PAGES=ROOT/'powerbi/RetailSalesAnalytics/RetailSalesAnalytics.Report/definition/pages'


class UxRedesignTests(unittest.TestCase):
    def test_approved_base_kpis_unchanged(self):
        previous=json.loads((HERE/'approved-sales.json').read_text(encoding='utf-8-sig'))
        before={m['name']:m['expression'].strip() for m in previous['measures']}
        for name in ('Total Sales Before Tax','Total Tax','Total Amount Including Tax','Invoice Count','Order Count','Units Sold','Buyer Sales','Bill-to Sales','Sales Previous Year Comparable Period'):
            self.assertEqual(MEASURES[name]['expression'].strip(),before[name],name)

    def test_original_and_brand_assets_preserved(self):
        before=json.loads((HERE/'approved-sales.json').read_text(encoding='utf-8'))['hashes']
        for name,digest in before.items():
            if name=='powerbi/Sales_Dashboard.pbix' or '/StaticResources/' in name:
                self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest,name)

    def test_four_primary_pages_have_a_hero_and_bounded_chart_count(self):
        for pid in json.loads((PAGES/'pages.json').read_text(encoding='utf-8'))['pageOrder'][:4]:
            visuals=[json.loads(p.read_text(encoding='utf-8')) for p in (PAGES/pid/'visuals').glob('*/visual.json')]
            charts=[v for v in visuals if v['visual']['visualType'] in ('lineChart','barChart','clusteredColumnChart','lineClusteredColumnComboChart')]
            self.assertLessEqual(len(charts),3)
            self.assertEqual(len([v for v in charts if v['position']['width']>=1500 and v['position']['height']>=400]),1)
            self.assertFalse(any(v['visual']['visualType']=='pivotTable' for v in visuals))
            for i,a in enumerate(visuals):
                for b in visuals[i+1:]:
                    x,y=a['position'],b['position']
                    overlap=min(x['x']+x['width'],y['x']+y['width'])-max(x['x'],y['x'])>0 and min(x['y']+x['height'],y['y']+y['height'])-max(x['y'],y['y'])>0
                    self.assertFalse(overlap,(pid,a['name'],b['name']))

    def test_dates_synced_and_details_keep_context(self):
        groups={}
        for path in PAGES.glob('*/visuals/*/visual.json'):
            v=json.loads(path.read_text(encoding='utf-8'))['visual']
            group=v.get('syncGroup',{}).get('groupName')
            if group:groups[group]=groups.get(group,0)+1
        self.assertEqual(groups['retail_year'],8)
        self.assertEqual(groups['retail_date'],8)
        self.assertEqual(groups['retail_product'],2)
        self.assertEqual(groups['retail_topn'],2)

    def test_derived_helpers_do_not_replace_base_metrics(self):
        self.assertIn('CONVERT',MEASURES['Average Invoice Value']['expression'])
        self.assertIn('COALESCE(COUNTROWS(INTERSECT',MEASURES['Top N Ranking Overlap']['expression'])
        for name in ('Buyer Rank','Bill-to Rank','Selected Role Rank'):
            self.assertIn('NOT ISBLANK',MEASURES[name]['expression'])
            self.assertIn('<>0',MEASURES[name]['expression'])
        for name in ('Weekday Invoice Activity','Weekday Order Activity'):
            self.assertIn('[Data Coverage Days]>0',MEASURES[name]['expression'])


if __name__=='__main__':unittest.main()
