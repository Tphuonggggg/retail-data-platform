# Scripts

- check_raw_connection.py: offline config validation or explicit read-only Raw connectivity.
- recover_raw_bootstrap.py: historical recovery helper; defaults read-only, --apply mutates DB and is outside reset.
- inspect_wwi_source.py: optional metadata/sample diagnostic. --history-permissions is legacy dedicated-user investigation, not a normal load prerequisite.

Use [main CLI/runbook](../README.md) for normal operation. No script auto-installs packages, grants permissions or starts ingestion. [Historical investigation](../docs/archive/pre-reset/ingestion-history.md).
