"""Protect the reader allowlist and bounded rebuild selection, without a DB."""
from pathlib import Path
import sys
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'dbt'))
from execute import SALES_BI_MODELS, selection_arguments


class BiGrantsTests(unittest.TestCase):
    def test_exact_model_grants_no_folder_defaults(self):
        config = yaml.safe_load((ROOT/'dbt/dbt_project.yml').read_text())['models']['retail_sales']
        found = {}
        def walk(node, path=()):
            if not isinstance(node, dict):
                return
            for key, value in node.items():
                if key == '+grants':
                    found[path] = value
                else:
                    walk(value, path+(key,))
        walk(config)
        self.assertEqual(len(found), 12)
        self.assertEqual({p[-1] for p in found}, set(SALES_BI_MODELS))
        self.assertTrue(all(len(p) == 2 and p[0] in {'core','intermediate','marts'} for p in found))
        self.assertTrue(all(v == {'select':['retail_bi_reader']} for v in found.values()))

    def test_no_selection_keeps_existing_cli(self):
        self.assertEqual(selection_arguments(None), [])

    def test_explicit_selection_never_expands_graph(self):
        self.assertEqual(selection_arguments(['dim_date']),
                         ['--select','dim_date','--indirect-selection','cautious'])

    def test_reject_expansion_unrelated_and_duplicate_names(self):
        for names in ([], ['+dim_date'], ['dim_date+'], ['raw.*'], ['record_status'],
                      ['dim_date','dim_date'], ['*'], ['--full-refresh']):
            with self.subTest(names=names), self.assertRaises(ValueError):
                selection_arguments(names)


if __name__ == '__main__':
    unittest.main()
