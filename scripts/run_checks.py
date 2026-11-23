"""Project-wide offline suites; no ingestion, DB connections, provisioning or dbt execution."""
from pathlib import Path
import argparse
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SUITES = (
    ('airflow/tests', 'test_*.py'),
    ('powerbi/tests', 'test_*.py'),
    ('dbt/tests/unit', 'test_*.py'),
    ('ingestion/tests', 'full_load_offline.py'),
    ('ingestion/tests', 'incremental_offline.py'),
    ('infrastructure/tests', 'raw_foundation_static.py'),
    ('infrastructure/tests', 'raw_provisioning_readonly.py'),
    ('tests/integration', 'ingest_acceptance_offline.py'),
    ('ingestion/tests', 'portfolio_offline.py'),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--portable', action='store_true',
                        help='Exclude Desktop TOM-dependent Power BI tests; retain all default local suites.')
    args = parser.parse_args()
    failed = False
    for directory, pattern in SUITES:
        if args.portable and directory == 'powerbi/tests':
            print('NOT_RUN: Power BI structural suite requires Windows and Desktop TOM', flush=True)
            continue
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', directory,
                                 '-p', pattern, '-v'], cwd=ROOT)
        failed |= result.returncode != 0
    result = subprocess.run([sys.executable, 'scripts/validate_repository.py'], cwd=ROOT)
    return int(failed or result.returncode != 0)


if __name__ == '__main__':
    raise SystemExit(main())
