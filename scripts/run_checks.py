"""Project-wide offline suites; no ingestion, DB connections, provisioning or dbt execution."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SUITES = (
    ('ingestion/tests', 'full_load_offline.py'),
    ('infrastructure/tests', 'raw_foundation_static.py'),
    ('infrastructure/tests', 'raw_provisioning_readonly.py'),
    ('tests/integration', 'ingest_acceptance_offline.py'),
    ('tests/integration/b9_precision', 'test_poc.py'),
    ('tests', 'source_security_static.py'),
    ('tests', 'staging_acl_static.py'),
)


def main() -> int:
    failed = False
    for directory, pattern in SUITES:
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', directory,
                                 '-p', pattern, '-v'], cwd=ROOT)
        failed |= result.returncode != 0
    result = subprocess.run([sys.executable, 'scripts/validate_repository.py'], cwd=ROOT)
    return int(failed or result.returncode != 0)


if __name__ == '__main__':
    raise SystemExit(main())
