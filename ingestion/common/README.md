# common

**Status:** WWI-06A Implemented / Offline Tested; runtime NOT RUN.

Purpose/scope: technical contracts cho [Full Load](../README.md), không KPI logic. Inputs: accepted metadata/config/external proof; outputs: validated objects/typed rows/digest/settings/evidence coverage.

- [contracts.py](contracts.py), [source_contract.json](source_contract.json):11 populations, explicit F2/projections/target names/fingerprint; schema drift STOP.
- [codecs.py](codecs.py): NULL/Decimal/Unicode/binary/date/exact datetime2(7), typed digest; không rounding/truncation.
- [config.py](config.py): reuse Raw checker parser, Windows-integrated strict TLS/local target; no-secret summary.
- [evidence.py](evidence.py), [errors.py](errors.py): window coverage/sanitized categories; parser không chứng minh writer control.

Dependencies/technology: Python3.12 stdlib + pure functions scripts; không I/O database lúc import. Execution qua parent CLI; testing/acceptance qua [offline suite](../tests/full_load_offline.py). Actual engine fidelity cần WWI-06B. Automatic retry/checkpoint Not implemented yet.
