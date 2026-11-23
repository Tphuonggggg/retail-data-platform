import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

spec=importlib.util.spec_from_file_location('retail_schedule',Path(__file__).resolve().parents[1]/'scheduling.py')
schedule=importlib.util.module_from_spec(spec);spec.loader.exec_module(schedule)
P='3a2f011d-f3b3-5683-83a2-a64837720f3d'


class SchedulingTests(unittest.TestCase):
    def daily(self):return dict(zip(schedule.KEYS,('daily','02:00',P,'2026-11-24T02:00:00+07:00')))
    def test_default_manual_even_with_unused_daily_values(self):
        self.assertIsNone(schedule.settings({})['cron'])
        self.assertIsNone(schedule.settings({schedule.KEYS[2]:'latest'})['parent'])
    def test_daily_is_explicit_bounded_timezone_boundary(self):
        cfg=schedule.settings(self.daily());self.assertEqual(cfg['cron'],'0 2 * * *');self.assertEqual(cfg['parent'],P)
        for key,bad in ((schedule.KEYS[0],'@daily'),(schedule.KEYS[1],'24:00'),(schedule.KEYS[2],'latest'),(schedule.KEYS[3],'2026-11-24T02:00:00'),(schedule.KEYS[3],'2026-11-24T03:00:00+07:00')):
            env=self.daily();env[key]=bad
            with self.subTest(key=key),self.assertRaises((ValueError,TypeError)):schedule.settings(env)
    def test_manual_requires_conf_and_scheduled_requires_explicit_parent(self):
        with self.assertRaises(ValueError):schedule.parent_for_run(SimpleNamespace(conf={},run_type='manual'),P)
        with self.assertRaises(ValueError):schedule.parent_for_run(SimpleNamespace(conf={},run_type='scheduled'),None)
        self.assertEqual(schedule.parent_for_run(SimpleNamespace(conf={},run_type='scheduled'),P),P)
    def test_scheduled_handoff_preserves_original_parent_after_config_change(self):
        run=SimpleNamespace(conf={},run_type='scheduled')
        self.assertEqual(schedule.parent_for_run(run,None,{'parent':P}),P)
        run.conf={'parent_version':P};self.assertEqual(schedule.parent_for_run(run,None),P)
