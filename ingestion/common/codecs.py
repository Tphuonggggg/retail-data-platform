"""Lossless scalar admission and streaming source-to-target content checks."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import re
from typing import Any

from .contracts import Column, SourceObject
from .errors import PipelineError

TEMPORAL = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$", re.ASCII)


def admit(column: Column, value: Any) -> Any:
    if value is None:
        if not column.nullable: raise PipelineError("REQUIRED_NULL")
        return None
    kind = column.source_type
    if kind == "datetime2(7)":
        if not isinstance(value, str) or not TEMPORAL.fullmatch(value):
            raise PipelineError("TEMPORAL_PRECISION_LOSS")
        try:
            date.fromisoformat(value[:10])
            if int(value[11:13]) > 23 or int(value[14:16]) > 59 or int(value[17:19]) > 59:
                raise ValueError("range")
        except ValueError:
            raise PipelineError("INVALID_TEMPORAL") from None
        return value
    if kind == "int":
        if type(value) is not int or not -(2**31) <= value < 2**31:
            raise PipelineError("INTEGER_FIDELITY")
        return value
    if kind == "bit":
        if type(value) not in {int, bool} or value not in (0, 1):
            raise PipelineError("BOOLEAN_FIDELITY")
        return bool(value)
    if kind == "date":
        if not isinstance(value, date) or isinstance(value, datetime):
            raise PipelineError("DATE_FIDELITY")
        return value
    if kind.startswith("decimal("):
        if not isinstance(value, Decimal) or not value.is_finite():
            raise PipelineError("DECIMAL_FIDELITY")
        precision, scale = map(int, kind[8:-1].split(","))
        try:
            with localcontext() as context:
                context.prec = 40
                fixed = value.quantize(Decimal(1).scaleb(-scale))
                if fixed != value or abs(value) >= Decimal(10) ** (precision - scale):
                    raise InvalidOperation
        except InvalidOperation:
            raise PipelineError("DECIMAL_PRECISION_LOSS") from None
        return fixed
    if kind.startswith("nvarchar("):
        if not isinstance(value, str) or "\x00" in value:
            raise PipelineError("TEXT_FIDELITY")
        try:
            value.encode("utf-8", errors="strict")
            length = len(value.encode("utf-16-le", errors="strict")) // 2
        except UnicodeError:
            raise PipelineError("UNICODE_FIDELITY") from None
        limit = kind[9:-1]
        if limit != "max" and length > int(limit):
            raise PipelineError("TEXT_LENGTH")
        return value
    if kind in {"varbinary(max)", "geography"}:
        if not isinstance(value, (bytes, bytearray, memoryview)):
            raise PipelineError("BINARY_FIDELITY")
        return bytes(value)
    raise PipelineError("UNSUPPORTED_SOURCE_TYPE")


def admit_row(obj: SourceObject, row: Any) -> tuple[Any, ...]:
    if len(row) != len(obj.columns): raise PipelineError("ROW_SHAPE_MISMATCH")
    return tuple(admit(c, v) for c, v in zip(obj.columns, row, strict=True))


class RowDigest:
    """Length-framed ordered multiset digest. Ordinals never identify source history episodes."""
    def __init__(self) -> None:
        self._hash = hashlib.sha256()
        self.count = 0

    def add(self, row: tuple[Any, ...]) -> None:
        self._hash.update(b"R")
        for value in row:
            if value is None: tag, data = b"N", b""
            elif isinstance(value, bytes): tag, data = b"B", value
            elif isinstance(value, Decimal): tag, data = b"D", format(value, "f").encode("ascii")
            elif isinstance(value, bool): tag, data = b"L", str(int(value)).encode("ascii")
            elif isinstance(value, int): tag, data = b"I", str(value).encode("ascii")
            elif isinstance(value, date): tag, data = b"A", value.isoformat().encode("ascii")
            elif isinstance(value, str): tag, data = b"S", value.encode("utf-8")
            else: raise PipelineError("UNSUPPORTED_DIGEST_TYPE")
            self._hash.update(tag + len(data).to_bytes(8, "big")); self._hash.update(data)
        self._hash.update(b"E"); self.count += 1

    @property
    def hexdigest(self) -> str: return self._hash.hexdigest()
