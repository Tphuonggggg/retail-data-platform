"""Frozen source schema from accepted metadata/contracts; no runtime invention."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

from .errors import PipelineError

IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CONTRACT_PATH = Path(__file__).with_name("source_contract.json")
# Verbatim verified B9 F2 expression, substituting only the vetted column operand.
F2_SQL = """CASE WHEN v.source_value IS NULL THEN CAST(NULL AS varchar(27))
            ELSE CONVERT(char(19), v.source_value, 126) + '.' +
                 RIGHT('0000000' + CONVERT(varchar(7),
                       DATEPART(NANOSECOND, v.source_value) / 100), 7)
       END"""


def identifier(value: str) -> str:
    if not IDENTIFIER.fullmatch(value):
        raise PipelineError("UNSAFE_IDENTIFIER")
    return value


def ms_quote(value: str) -> str:
    return "[" + identifier(value) + "]"


def pg_quote(value: str) -> str:
    return '"' + identifier(value) + '"'


@dataclass(frozen=True)
class Column:
    name: str
    source_type: str
    nullable: bool

    def __post_init__(self) -> None:
        identifier(self.name)
        if type(self.nullable) is not bool or not re.fullmatch(
            r"int|bit|date|geography|datetime2\(7\)|nvarchar\((?:max|[1-9][0-9]{0,3})\)|varbinary\(max\)|decimal\(([1-9][0-9]?),([0-9]+)\)", self.source_type):
            raise PipelineError("UNSUPPORTED_SOURCE_TYPE")
        if self.source_type.startswith("decimal"):
            p,s=map(int,self.source_type[8:-1].split(","))
            if not 0<=s<=p<=38: raise PipelineError("UNSUPPORTED_SOURCE_TYPE")

    @property
    def pg_type(self) -> str:
        family = self.source_type.split("(")[0]
        if family == "int": return "integer"
        if family == "bit": return "boolean"
        if family == "date": return "date"
        if family == "decimal": return self.source_type.replace("decimal", "numeric")
        if family == "datetime2": return 'text COLLATE "C"'
        if family in {"varbinary", "geography"}: return "bytea"
        if family == "nvarchar": return "text"
        raise PipelineError("UNSUPPORTED_SOURCE_TYPE")

    @property
    def projection(self) -> str:
        operand = ms_quote(self.name)
        if self.source_type == "datetime2(7)":
            return F2_SQL.replace("v.source_value", operand) + " AS " + operand
        if self.source_type == "geography":
            return f"CONVERT(varbinary(max), {operand}) AS {operand}"
        return operand


@dataclass(frozen=True)
class SourceObject:
    schema: str
    table: str
    columns: tuple[Column, ...]
    primary_key: str | None
    order_by: tuple[str, ...]
    origin: str

    @property
    def name(self) -> str: return self.schema + "." + self.table

    @property
    def target(self) -> str: return (self.schema + "_" + self.table).lower()

    @property
    def ms_table(self) -> str: return ms_quote(self.schema) + "." + ms_quote(self.table)

    @property
    def pg_table(self) -> str: return "raw." + pg_quote(self.target)

    def page_size(self, requested: int) -> int:
        if any(c.source_type in {"varbinary(max)","geography"} for c in self.columns): return 1
        if any("max" in c.source_type for c in self.columns): return min(requested,64)
        return requested

    @property
    def query(self) -> str:
        return ("SELECT " + ", ".join(c.projection for c in self.columns) + " FROM " + self.ms_table
                + " ORDER BY " + ", ".join(ms_quote(k) for k in self.order_by))


def catalog() -> dict[str, SourceObject]:
    data = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    result = {}
    for item in data["objects"]:
        obj = SourceObject(item["schema"], item["table"], tuple(Column(**c) for c in item["columns"]),
                           item["primary_key"], tuple(item["order_by"]), item["origin"])
        identifier(obj.schema); identifier(obj.table)
        names = [identifier(c.name) for c in obj.columns]
        if len(names) != len(set(names)) or any(k not in names for k in obj.order_by):
            raise PipelineError("INVALID_SOURCE_CONTRACT")
        result[obj.name] = obj
    if len(result) != 11:
        raise PipelineError("INVALID_ALLOWLIST")
    return result


def select_objects(names: list[str] | None = None) -> tuple[SourceObject, ...]:
    all_objects = catalog()
    chosen = names if names is not None else sorted(all_objects)
    if not chosen or len(chosen) != len(set(chosen)) or any(n not in all_objects for n in chosen):
        raise PipelineError("SOURCE_NOT_ALLOWLISTED")
    return tuple(all_objects[n] for n in sorted(chosen))


def contract_hash() -> str:
    # Git CRLF/LF conversion or JSON indentation must not invalidate an identical contract.
    canonical=json.dumps(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")),
                         sort_keys=True,ensure_ascii=True,separators=(",",":")).encode("ascii")
    return hashlib.sha256(canonical+F2_SQL.encode()+b"wwi06a-codec-1-schema-1").hexdigest()
