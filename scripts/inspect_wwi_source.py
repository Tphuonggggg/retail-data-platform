"""Explicit, SELECT-only WWI diagnostics; never a loader or DBA fallback.

Default is offline help. --execute opens strict TLS with the current Windows
identity; --samples additionally reads TOP(1) per allowlisted object. No row
values, credentials, files, DDL, grants or target writes are produced.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingestion.common.codecs import admit_row
from ingestion.common.config import SOURCE_DATABASE, SOURCE_ENDPOINT, SOURCE_PRINCIPAL, SOURCE_SID
from ingestion.common.contracts import F2_SQL, catalog, select_objects
from ingestion.common.errors import PipelineError
from ingestion.extractors.sqlserver import windows_principal


COLUMN_SQL = """SELECT c.name,
TYPE_NAME(CASE WHEN c.system_type_id=240 THEN c.user_type_id ELSE c.system_type_id END),
c.max_length,c.precision,c.scale,c.is_nullable
FROM sys.columns c WHERE c.object_id=OBJECT_ID(?,'U') ORDER BY c.column_id"""
KEY_SQL = """SELECT c.name FROM sys.indexes i
JOIN sys.index_columns ic ON ic.object_id=i.object_id AND ic.index_id=i.index_id
JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id
WHERE i.object_id=OBJECT_ID(?) AND i.is_primary_key=1 ORDER BY ic.key_ordinal"""
TEMPORAL_SQL = """SELECT temporal_type_desc,
OBJECT_SCHEMA_NAME(history_table_id)+'.'+OBJECT_NAME(history_table_id)
FROM sys.tables WHERE object_id=OBJECT_ID(?)"""
PERMISSION_SQL = "SELECT " + ",".join(
    f"HAS_PERMS_BY_NAME(?,'OBJECT','{permission}')"
    for permission in ("SELECT", "INSERT", "UPDATE", "DELETE", "ALTER", "CONTROL"))


def column_signature(row: Any) -> tuple[str, str, bool]:
    name, kind, length, precision, scale, nullable = row
    if kind == "nvarchar":
        kind += "(" + ("max" if length == -1 else str(length // 2)) + ")"
    elif kind == "varbinary":
        kind += "(" + ("max" if length == -1 else str(length)) + ")"
    elif kind == "decimal":
        kind += f"({precision},{scale})"
    elif kind == "datetime2":
        kind += f"({scale})"
    return name, kind, bool(nullable)


def inspect(connection: Any, *, samples: bool = False) -> dict[str, Any]:
    with connection.cursor() as cursor:
        identity = cursor.execute("SELECT ORIGINAL_LOGIN(),SUSER_SNAME(),SUSER_SID(),USER_NAME(),DB_NAME(),"
            "CONVERT(varchar(128),SERVERPROPERTY('ProductVersion')),IS_SRVROLEMEMBER('sysadmin')").fetchone()
        if identity[4] != SOURCE_DATABASE:
            raise PipelineError("SOURCE_DATABASE_MISMATCH")
        dedicated = identity[0].casefold() == SOURCE_PRINCIPAL.casefold()
        if dedicated and (identity[1].casefold() != SOURCE_PRINCIPAL.casefold()
                          or bytes(identity[2]) != SOURCE_SID or identity[3] != "wwi_extract" or identity[6] != 0):
            raise PipelineError("SOURCE_IDENTITY_MISMATCH")
        objects = []
        for obj in select_objects():
            actual = [column_signature(r) for r in cursor.execute(COLUMN_SQL, obj.name).fetchall()]
            expected = [(c.name, c.source_type, c.nullable) for c in obj.columns]
            keys = [r[0] for r in cursor.execute(KEY_SQL, obj.name).fetchall()]
            temporal = cursor.execute(TEMPORAL_SQL, obj.name).fetchone()
            rights = list(cursor.execute(PERMISSION_SQL, *([obj.name] * 6)).fetchone())
            result = {"object": obj.name, "column_count": len(actual), "schema_match": actual == expected,
                      "key_match": keys == ([obj.primary_key] if obj.primary_key else []),
                      "actual_primary_key": keys, "temporal_type": temporal[0] if temporal else None,
                      "history_table": temporal[1] if temporal else None,
                      "own_context_rights_select_insert_update_delete_alter_control": rights,
                      "projection_sample": "NOT_RUN"}
            if actual != expected:
                result["expected_schema"] = expected
                result["actual_schema"] = actual
            if samples and actual == expected and result["key_match"]:
                row = cursor.execute(obj.query.replace("SELECT ", "SELECT TOP (1) ", 1)).fetchone()
                if row is not None:
                    admit_row(obj, row)
                result["projection_sample"] = "PASS" if row is not None else "EMPTY_POPULATION"
            objects.append(result)
        return {"status": "READONLY_DIAGNOSTICS_COMPLETE", "strict_tls": True,
                "identity": identity[0], "database_user": identity[3], "version": identity[5],
                "identity_scope": "EXTRACTOR_DIAGNOSTIC_NOT_GATE_PASS" if dedicated else "DBA_METADATA_ONLY",
                "rights_are_current_session_only": True, "objects": objects,
                "full_load_executed": False}


def holdings_profile(connection: Any) -> dict[str, Any]:
    obj = catalog()["Warehouse.StockItemHoldings"]
    nulls = ",".join("SUM(CASE WHEN [" + c.name + "] IS NULL THEN 1 ELSE 0 END)" for c in obj.columns)
    low = F2_SQL.replace("v.source_value", "MIN([LastEditedWhen])")
    high = F2_SQL.replace("v.source_value", "MAX([LastEditedWhen])")
    with connection.cursor() as cursor:
        row = cursor.execute("SELECT COUNT_BIG(*),COUNT_BIG(DISTINCT [StockItemID]),"
            "SUM(CONVERT(bigint,[QuantityOnHand])),SUM(CONVERT(decimal(38,2),[LastCostPrice])),"
            + low + "," + high + "," + nulls + " FROM " + obj.ms_table).fetchone()
    return {"object": obj.name, "rows": row[0], "distinct_keys": row[1],
            "quantity_total": row[2], "last_cost_price_total": str(row[3]) if row[3] is not None else None,
            "last_edited_min": row[4], "last_edited_max": row[5],
            "null_counts": dict(zip((c.name for c in obj.columns), row[6:], strict=True)),
            "basis": "OBSERVATION_ONLY_REMEASURE_IN_SMOKE_WINDOW_NOT_A_SNAPSHOT_PROOF"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Authorize SELECT-only network diagnostics")
    parser.add_argument("--samples", action="store_true", help="TOP(1) codec sample for each approved object")
    parser.add_argument("--holdings-profile", action="store_true", help="Small candidate COUNT/NULL/numeric/time aggregates")
    args = parser.parse_args(argv)
    if not args.execute:
        parser.print_help()
        return 0
    try:
        principal = windows_principal()
        if principal.casefold() not in {SOURCE_PRINCIPAL.casefold(), "desktop-obdfk6b\\pc"}:
            raise PipelineError("DIAGNOSTIC_OPERATOR_NOT_APPROVED")
        import pyodbc
        connection_string = ("DRIVER={ODBC Driver 18 for SQL Server};SERVER=" + SOURCE_ENDPOINT
            + ";DATABASE=" + SOURCE_DATABASE + ";Trusted_Connection=yes;Encrypt=yes;"
              "TrustServerCertificate=no;APP=retail_wwi06b_readonly_review;")
        connection = pyodbc.connect(connection_string, timeout=5, autocommit=True, attrs_before={101: 1})
        try:
            connection.timeout = 30
            output = inspect(connection, samples=args.samples)
            if args.holdings_profile:
                output["holdings_profile"] = holdings_profile(connection)
            print(json.dumps(output))
            return 0 if all(o["schema_match"] and o["key_match"] for o in output["objects"]) else 1
        finally:
            connection.close()
    except Exception as error:
        print(json.dumps({"status": "DIAGNOSTIC_STOP", "error_category": error.code
            if isinstance(error, PipelineError) else "TLS_IDENTITY_OR_DRIVER_FAILURE"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
