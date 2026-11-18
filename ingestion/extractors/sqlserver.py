"""Dedicated Windows identity, metadata fences, SELECT-only streamed extraction."""
from __future__ import annotations

import ctypes
import os
from typing import Iterator, Any

from ingestion.common.config import Settings, SOURCE_PRINCIPAL, SOURCE_SID
from ingestion.common.contracts import SourceObject, catalog
from ingestion.common.errors import PipelineError


def windows_principal() -> str:
    if os.name != "nt": raise PipelineError("WINDOWS_EXTRACTION_IDENTITY_REQUIRED")
    size = ctypes.c_ulong(0)
    api = ctypes.WinDLL("secur32", use_last_error=True).GetUserNameExW
    api.argtypes = [ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]
    api.restype = ctypes.c_int
    api(2, None, ctypes.byref(size))
    if not size.value: raise PipelineError("WINDOWS_IDENTITY_UNVERIFIED")
    buffer = ctypes.create_unicode_buffer(size.value)
    if not api(2, buffer, ctypes.byref(size)): raise PipelineError("WINDOWS_IDENTITY_UNVERIFIED")
    return buffer.value


class SqlServerSource:
    def __init__(self, config: Settings):
        self.config = config
        self.connection: Any = None
        self.context: dict[str, Any] = {}

    def connect(self) -> None:
        if windows_principal().casefold() != SOURCE_PRINCIPAL.casefold():
            raise PipelineError("DEDICATED_SOURCE_IDENTITY_REQUIRED")
        import pyodbc
        self.connection = pyodbc.connect(self.config.source_connection_string,
            timeout=self.config.login_timeout, autocommit=True, attrs_before={101: 1})
        self.connection.timeout = self.config.query_timeout
        with self.connection.cursor() as cursor:
            row = cursor.execute("SELECT ORIGINAL_LOGIN(), SUSER_SNAME(), SUSER_SID(), DB_NAME(), "
                "CONVERT(nvarchar(128), SERVERPROPERTY('MachineName')), "
                "CONVERT(nvarchar(128), SERVERPROPERTY('InstanceName')), "
                "IS_SRVROLEMEMBER('sysadmin'), IS_SRVROLEMEMBER('securityadmin'), "
                "IS_ROLEMEMBER('db_owner'), IS_ROLEMEMBER('db_datareader'), IS_ROLEMEMBER('db_datawriter'), USER_NAME()").fetchone()
            if (row[0].casefold() != SOURCE_PRINCIPAL.casefold() or row[1].casefold() != SOURCE_PRINCIPAL.casefold()
                    or bytes(row[2]) != SOURCE_SID or tuple(row[3:6]) != ("WideWorldImporters", "DESKTOP-OBDFK6B", "SQLEXPRESS")
                    or any(value != 0 for value in row[6:11]) or row[11]!="wwi_extract"):
                raise PipelineError("SOURCE_IDENTITY_OR_ADMIN_PRIVILEGE")
            version,collation=cursor.execute("SELECT CONVERT(varchar(128),SERVERPROPERTY('ProductVersion')), "
                                              "CONVERT(varchar(128),SERVERPROPERTY('Collation'))").fetchone()
            self.context={"endpoint":"tcp:DESKTOP-OBDFK6B,1433","instance":"SQLEXPRESS","database":"WideWorldImporters",
                          "product_version":version,"collation":collation,"source_snapshot_id":None,
                          "geography_encoding":"SQL_SERVER_NATIVE_VARBINARY_NOT_WKB",
                          "pyodbc_version":pyodbc.version,"ingestion_settings":self.config.summary()}

    def preflight(self, objects: tuple[SourceObject, ...]) -> None:
        # Always check the complete identity allowlist, including known archive INSERT exceptions.
        with self.connection.cursor() as cursor:
            for obj in catalog().values():
                row = cursor.execute("SELECT HAS_PERMS_BY_NAME(?, 'OBJECT', 'SELECT'), "
                    "HAS_PERMS_BY_NAME(?, 'OBJECT', 'INSERT'), HAS_PERMS_BY_NAME(?, 'OBJECT', 'UPDATE'), "
                    "HAS_PERMS_BY_NAME(?, 'OBJECT', 'DELETE'), HAS_PERMS_BY_NAME(?, 'OBJECT', 'ALTER'), "
                    "HAS_PERMS_BY_NAME(?, 'OBJECT', 'CONTROL')", *([obj.name] * 6)).fetchone()
                if tuple(row) != (1, 0, 0, 0, 0, 0):
                    raise PipelineError("SOURCE_EFFECTIVE_PERMISSIONS_UNRESOLVED")
            powers = cursor.execute("SELECT HAS_PERMS_BY_NAME(NULL,NULL,'CONTROL SERVER'), "
                                    "HAS_PERMS_BY_NAME(NULL,NULL,'SELECT ALL USER SECURABLES')").fetchone()
            if tuple(powers) != (0, 0): raise PipelineError("SOURCE_BROAD_PERMISSION")
            for obj in objects:
                rows = cursor.execute("SELECT c.name, TYPE_NAME(CASE WHEN c.system_type_id=240 THEN c.user_type_id "
                    "ELSE c.system_type_id END), c.max_length,c.precision,c.scale,c.is_nullable "
                    "FROM sys.columns c WHERE c.object_id=OBJECT_ID(?, 'U') ORDER BY c.column_id", obj.name).fetchall()
                actual = []
                for name, kind, length, precision, scale, nullable in rows:
                    if kind == "nvarchar": kind += "(" + ("max" if length == -1 else str(length // 2)) + ")"
                    elif kind == "varbinary": kind += "(" + ("max" if length == -1 else str(length)) + ")"
                    elif kind == "decimal": kind += f"({precision},{scale})"
                    elif kind == "datetime2": kind += f"({scale})"
                    actual.append((name, kind, bool(nullable)))
                expected = [(c.name, c.source_type, c.nullable) for c in obj.columns]
                if actual != expected: raise PipelineError("SOURCE_SCHEMA_MISMATCH")

    def count(self, obj: SourceObject) -> int:
        if catalog().get(obj.name)!=obj: raise PipelineError("SOURCE_NOT_ALLOWLISTED")
        with self.connection.cursor() as cursor:
            return int(cursor.execute("SELECT COUNT_BIG(*) FROM " + obj.ms_table).fetchone()[0])

    def batches(self, obj: SourceObject) -> Iterator[list[Any]]:
        if catalog().get(obj.name)!=obj: raise PipelineError("SOURCE_NOT_ALLOWLISTED")
        with self.connection.cursor() as cursor:
            page_size = obj.page_size(self.config.batch_size)
            cursor.arraysize = page_size
            cursor.execute(obj.query)
            while True:
                batch = cursor.fetchmany(page_size)
                if not batch: break
                yield batch

    def close(self) -> None:
        if self.connection is not None: self.connection.close()
