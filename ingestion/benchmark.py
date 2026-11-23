"""Repeatable in-memory snapshot-diff fixture benchmark; no database connections."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import platform
import random
import statistics
import time
import tracemalloc

from ingestion.demo import SAMPLE, digest
from ingestion.incremental import compare

ROOT = Path(__file__).resolve().parents[1]


def fixtures(size, percent, seed=20261123):
    if size < 100 or percent not in (0, 1, 10):
        raise ValueError('Use size >= 100 and percent 0, 1 or 10')
    before = [(i, date(2024, 1, 1), 'Sản phẩm ' + str(i % 20), i % 5 + 1,
               Decimal(i % 1000).quantize(Decimal('0.01')), None if i % 2 else '',
               '2024-01-01T00:00:00.0000001') for i in range(1, size + 1)]
    changed = size * percent // 100
    inserts = changed // 2
    updates = changed - inserts
    keys = set(random.Random(seed).sample(range(1, size + 1), updates))
    after = [(*row[:4], row[4] + Decimal('0.01'), *row[5:]) if row[0] in keys else row for row in before]
    after.extend((size+i, date(2024, 1, 2), 'Mới', 1, Decimal('10.00'), None,
                  '2024-01-02T00:00:00.0000001') for i in range(1, inserts+1))
    return before, after, {'INSERT': inserts, 'UPDATE': updates, 'UNCHANGED': size-updates}


def measure(before, source, expected):
    # Fixture generation and parent-state preparation excluded from timed phases.
    loaded = {r[0]: r for r in before}
    tracemalloc.start()
    start = time.perf_counter()
    extracted = [tuple(list(row)) for row in source]
    fetched = time.perf_counter()
    changes = list(compare(SAMPLE, iter(before), iter(extracted)))
    compared = time.perf_counter()
    for change in changes:
        if change.kind in ('INSERT', 'UPDATE'):
            loaded[change.key] = change.after
        elif change.kind == 'DELETE':
            raise AssertionError('Unexpected delete')
    finished = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    counts = Counter(c.kind for c in changes)
    assert {key: counts[key] for key in expected} == expected
    assert digest([loaded[k] for k in sorted(loaded)]) == digest(source)
    elapsed = finished - start
    return {'extraction_seconds': fetched-start, 'comparison_seconds': compared-fetched,
            'load_seconds': finished-compared, 'total_seconds': elapsed,
            'records_examined': len(extracted), 'changes': dict(counts),
            'throughput_rows_per_second': len(extracted)/elapsed, 'peak_traced_bytes': peak}


def run(size=10000, repeats=3, seed=20261123):
    if repeats < 2:
        raise ValueError('At least two measured repetitions required')
    result = {'kind': 'IN_MEMORY_FIXTURE_NOT_DATABASE', 'size': size, 'seed': seed, 'repeats': repeats,
              'timestamp_utc': datetime.now(timezone.utc).isoformat(),
              'environment': {'python': platform.python_version(), 'platform': platform.platform(),
                              'processor': platform.processor(), 'memory': 'tracemalloc; not process RSS'},
              'scenarios': {}}
    for percent in (0, 1, 10):
        before, source, expected = fixtures(size, percent, seed)
        measure(before, source, expected)  # Same instrumented warm-up for each scenario.
        runs = [measure(before, source, expected) for _ in range(repeats)]
        metrics = [k for k, v in runs[0].items() if isinstance(v, (float, int))]
        result['scenarios'][str(percent)] = {'expected': expected, 'runs': runs,
            'summary': {k: {'median': statistics.median(r[k] for r in runs),
                            'min': min(r[k] for r in runs), 'max': max(r[k] for r in runs),
                            'stdev': statistics.stdev(r[k] for r in runs)} for k in metrics}}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rows', type=int, default=10000)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--seed', type=int, default=20261123)
    args = parser.parse_args()
    result = run(args.rows, args.repeats, args.seed)
    destination = ROOT / '.local/portfolio-benchmark/result.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
    for key, scenario in result['scenarios'].items():
        print(key + '%:', json.dumps(scenario['summary']['total_seconds']), scenario['expected'])
    print('IN_MEMORY_FIXTURE_NOT_DATABASE; raw artifact: .local/portfolio-benchmark/result.json')


if __name__ == '__main__':
    main()
