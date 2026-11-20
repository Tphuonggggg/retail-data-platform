"""Explicit, SELECT-only WWI diagnostics; never a loader or DBA fallback.

Default is offline help. --execute opens strict TLS with the current Windows
identity; --samples additionally reads TOP(1) per allowlisted object. No row
values, credentials, files, DDL, grants or target writes are produced.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ingestion.common.codecs import admit_row
from ingestion.common.config import SOURCE_DATABASE, SOURCE_ENDPOINT, SOURCE_INSTANCE, SOURCE_PRINCIPAL, SOURCE_SID
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


HISTORY_PARENTS = {"Sales.Customers_Archive": "Sales.Customers",
                   "Warehouse.StockItems_Archive": "Warehouse.StockItems"}
HISTORY_RIGHTS = ("SELECT", "INSERT", "UPDATE", "DELETE", "ALTER", "CONTROL", "TAKE OWNERSHIP", "VIEW DEFINITION")


def history_permissions(connection: Any) -> dict[str, Any]:
    """Collect own-context evidence only; never change the production preflight policy."""
    evidence: dict[str, Any] = {}

    def query(label: str, statement: str, *parameters: Any) -> list[dict[str, Any]] | None:
        if not statement.lstrip().startswith(("SELECT ", "WITH ")):
            raise PipelineError("DIAGNOSTIC_QUERY_NOT_SELECT")
        try:
            with connection.cursor() as cursor:
                cursor.execute(statement, *parameters)
                names = [column[0] for column in cursor.description]
                rows = [dict(zip(names, tuple(row), strict=True)) for row in cursor.fetchall()]
            evidence[label] = {"status": "VERIFIED_QUERY_RESULT", "rows": rows,
                               "sql": statement, "parameters": list(parameters)}
            return rows
        except Exception as error:
            # NULL/denied/driver failures must not become an empty successful audit.
            sqlstate = error.args[0] if getattr(error, "args", ()) else None
            if not isinstance(sqlstate, str) or len(sqlstate) != 5 or not sqlstate.isalnum():
                sqlstate = None
            evidence[label] = {"status": "NOT_VERIFIED", "error_type": type(error).__name__,
                               "sqlstate": sqlstate, "sql": statement, "parameters": list(parameters)}
            return None

    identity = query("identity", "SELECT ORIGINAL_LOGIN() AS original_login,SUSER_SNAME() AS effective_login,"
        "CONVERT(varchar(170),SUSER_SID(),1) AS sid,USER_NAME() AS database_user,DB_NAME() AS database_name,"
        "CONVERT(nvarchar(128),SERVERPROPERTY('MachineName')) AS machine,"
        "CONVERT(nvarchar(128),SERVERPROPERTY('InstanceName')) AS instance,"
        "CONVERT(varchar(128),SERVERPROPERTY('ProductVersion')) AS version")
    if not identity or len(identity) != 1:
        raise PipelineError("SOURCE_IDENTITY_UNVERIFIED")
    who = identity[0]
    if (str(who['original_login']).casefold() != SOURCE_PRINCIPAL.casefold()
            or str(who['effective_login']).casefold() != SOURCE_PRINCIPAL.casefold()
            or str(who['sid']).lower() != '0x' + SOURCE_SID.hex()
            or (who['database_user'], who['database_name'], who['machine'], who['instance']) !=
               ('wwi_extract', SOURCE_DATABASE, 'DESKTOP-OBDFK6B', SOURCE_INSTANCE)):
        raise PipelineError("DEDICATED_SOURCE_IDENTITY_REQUIRED")
    matrix = []
    for obj in select_objects():
        statement = "SELECT " + ",".join(
            f"HAS_PERMS_BY_NAME(?,'OBJECT','{right}') AS [{right}]" for right in HISTORY_RIGHTS)
        values = query("object_rights:" + obj.name, statement, *([obj.name] * len(HISTORY_RIGHTS)))
        matrix.append({"object": obj.name, "rights": values[0] if values and len(values) == 1 else None})

    query("role_flags", "SELECT IS_SRVROLEMEMBER('sysadmin') AS sysadmin,"
          "IS_SRVROLEMEMBER('securityadmin') AS securityadmin,IS_ROLEMEMBER('db_owner') AS db_owner,"
          "IS_ROLEMEMBER('db_datareader') AS db_datareader,IS_ROLEMEMBER('db_datawriter') AS db_datawriter,"
          "IS_ROLEMEMBER('db_ddladmin') AS db_ddladmin,IS_ROLEMEMBER('db_securityadmin') AS db_securityadmin")
    query("user_token", "SELECT principal_id,name,[type],[usage] FROM sys.user_token ORDER BY principal_id,name")
    query("login_token", "SELECT principal_id,name,[type],[usage] FROM sys.login_token ORDER BY principal_id,name")
    query("server_effective", "SELECT HAS_PERMS_BY_NAME(NULL,NULL,'CONTROL SERVER') AS control_server,"
          "HAS_PERMS_BY_NAME(NULL,NULL,'SELECT ALL USER SECURABLES') AS select_all_user_securables,"
          "HAS_PERMS_BY_NAME(NULL,NULL,'IMPERSONATE ANY LOGIN') AS impersonate_any_login,"
          "HAS_PERMS_BY_NAME(NULL,NULL,'ALTER ANY LOGIN') AS alter_any_login")
    query("database_effective", "SELECT entity_name,subentity_name,permission_name "
          "FROM sys.fn_my_permissions(NULL,'DATABASE') ORDER BY permission_name")
    # The current user token includes effective database roles and mapped groups.
    # Use that runtime token, rather than reconstructing it from visible edges.
    query("database_role_closure", "SELECT DISTINCT p.name,p.type_desc FROM sys.database_principals p "
          "WHERE p.principal_id IN (SELECT principal_id FROM sys.user_token) ORDER BY p.name")
    query("server_role_membership_visible", "SELECT r.name AS role_name,m.name AS member_name "
          "FROM sys.server_role_members rm JOIN sys.server_principals r ON r.principal_id=rm.role_principal_id "
          "JOIN sys.server_principals m ON m.principal_id=rm.member_principal_id "
          "WHERE rm.member_principal_id IN (SELECT principal_id FROM sys.login_token) ORDER BY r.name,m.name")
    query("server_grants_visible", "SELECT p.class_desc,p.state_desc,p.permission_name,"
          "grantee.name AS grantee,grantor.name AS grantor FROM sys.server_permissions p "
          "LEFT JOIN sys.server_principals grantee ON grantee.principal_id=p.grantee_principal_id "
          "LEFT JOIN sys.server_principals grantor ON grantor.principal_id=p.grantor_principal_id "
          "WHERE p.grantee_principal_id IN (SELECT principal_id FROM sys.login_token) "
          "ORDER BY grantee.name,p.class_desc,p.permission_name")

    for history, parent in HISTORY_PARENTS.items():
        schema = history.split('.')[0]
        query("binding:" + history, "SELECT h.object_id AS history_id,h.temporal_type AS history_type,"
              "h.temporal_type_desc AS history_type_desc,s.name AS history_schema,h.name AS history_name,"
              "USER_NAME(COALESCE(h.principal_id,s.principal_id)) AS history_owner,"
              "p.object_id AS parent_id,OBJECT_SCHEMA_NAME(p.object_id)+'.'+p.name AS parent_name,"
              "p.temporal_type AS parent_type,p.history_table_id AS parent_history_id "
              "FROM sys.tables h JOIN sys.schemas s ON s.schema_id=h.schema_id "
              "LEFT JOIN sys.tables p ON p.history_table_id=h.object_id WHERE h.object_id=OBJECT_ID(?,'U')", history)
        for name in (history, parent):
            query("object_effective:" + name, "SELECT entity_name,subentity_name,permission_name "
                  "FROM sys.fn_my_permissions(?,'OBJECT') ORDER BY subentity_name,permission_name", name)
        query("schema_effective:" + schema, "SELECT entity_name,subentity_name,permission_name "
              "FROM sys.fn_my_permissions(?,'SCHEMA') ORDER BY permission_name", schema)
        query("grants_visible:" + history, "WITH ids AS (SELECT principal_id AS id FROM sys.user_token "
              "UNION SELECT DATABASE_PRINCIPAL_ID('public')) "
              "SELECT USER_NAME(p.grantee_principal_id) AS grantee,USER_NAME(p.grantor_principal_id) AS grantor,"
              "p.class_desc,p.state_desc,p.permission_name,p.minor_id,"
              "CASE p.class WHEN 0 THEN DB_NAME() WHEN 3 THEN SCHEMA_NAME(p.major_id) "
              "WHEN 1 THEN OBJECT_SCHEMA_NAME(p.major_id)+'.'+OBJECT_NAME(p.major_id) END AS securable "
              "FROM sys.database_permissions p JOIN ids i ON i.id=p.grantee_principal_id "
              "WHERE p.class=0 OR (p.class=3 AND p.major_id=SCHEMA_ID(?)) "
              "OR (p.class=1 AND p.major_id IN (OBJECT_ID(?),OBJECT_ID(?))) "
              "ORDER BY grantee,p.class_desc,securable,p.permission_name,p.minor_id",
              schema, history, parent)

    required = ("SELECT", "INSERT", "UPDATE", "DELETE", "ALTER", "CONTROL")
    expected = (1, 0, 0, 0, 0, 0)
    strict_matrix_match = all(r['rights'] is not None and tuple(r['rights'][k] for k in required) == expected for r in matrix)
    ordinary_no_write = all(r['rights'] is not None and all(r['rights'][k] == 0 for k in HISTORY_RIGHTS[1:7])
                            for r in matrix if r['object'] not in HISTORY_PARENTS)
    return {"status": "HISTORY_PERMISSION_DIAGNOSTICS_COMPLETE", "observed_at": datetime.now(timezone.utc).isoformat(),
            "identity": who, "strict_tls": True, "object_permissions": matrix, "evidence": evidence,
            "all11_match_existing_strict_permission_matrix": strict_matrix_match,
            "ordinary_objects_no_dml_alter_control_ownership": ordinary_no_write,
            "unverified_queries": [key for key, value in evidence.items() if value['status'] == 'NOT_VERIFIED'],
            "scope": "CURRENT_REAL_EXTRACTOR_CONTEXT_VISIBLE_METADATA_NOT_GLOBAL_DBA_AUDIT",
            "production_preflight_executed": False, "production_security_policy_changed": False,
            "source_write_probe_executed": False, "full_load_executed": False,
            "root_cause": "UNDETERMINED_REQUIRES_EVIDENCE_REVIEW"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Authorize SELECT-only network diagnostics")
    parser.add_argument("--samples", action="store_true", help="TOP(1) codec sample for each approved object")
    parser.add_argument("--holdings-profile", action="store_true", help="Small candidate COUNT/NULL/numeric/time aggregates")
    parser.add_argument("--history-permissions", action="store_true", help="WWI-06C own-context history metadata/permissions only; wwi_extract required")
    args = parser.parse_args(argv)
    if args.history_permissions and (args.samples or args.holdings_profile):
        parser.error("History investigation cannot sample business payload or profile other source objects")
    if not args.execute:
        parser.print_help()
        return 0
    try:
        principal = windows_principal()
        if args.history_permissions and principal.casefold() != SOURCE_PRINCIPAL.casefold():
            raise PipelineError("DEDICATED_SOURCE_IDENTITY_REQUIRED")
        if principal.casefold() not in {SOURCE_PRINCIPAL.casefold(), "desktop-obdfk6b\\pc"}:
            raise PipelineError("DIAGNOSTIC_OPERATOR_NOT_APPROVED")
        import pyodbc
        connection_string = ("DRIVER={ODBC Driver 18 for SQL Server};SERVER=" + SOURCE_ENDPOINT
            + ";DATABASE=" + SOURCE_DATABASE + ";Trusted_Connection=yes;Encrypt=yes;"
              "TrustServerCertificate=no;APP=retail_wwi06b_readonly_review;")
        connection = pyodbc.connect(connection_string, timeout=5, autocommit=True, attrs_before={101: 1})
        try:
            connection.timeout = 30
            output = history_permissions(connection) if args.history_permissions else inspect(connection, samples=args.samples)
            if args.holdings_profile:
                output["holdings_profile"] = holdings_profile(connection)
            print(json.dumps(output))
            if args.history_permissions:
                return 0 if not output['unverified_queries'] else 2  # Collection success is NOT gate acceptance.
            return 0 if all(o["schema_match"] and o["key_match"] for o in output["objects"]) else 1
        finally:
            connection.close()
    except Exception as error:
        print(json.dumps({"status": "DIAGNOSTIC_STOP", "error_category": error.code
            if isinstance(error, PipelineError) else "TLS_IDENTITY_OR_DRIVER_FAILURE"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
