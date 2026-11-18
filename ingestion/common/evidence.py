"""External no-writes evidence coverage; this file is not proof of writer control."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from .config import SOURCE_ENDPOINT, SOURCE_DATABASE
from .contracts import SourceObject
from .errors import PipelineError


@dataclass(frozen=True)
class SourceEvidence:
    reference: str
    start: datetime
    end: datetime
    scope: frozenset[str]
    geography_reference: str | None = None

    @classmethod
    def read(cls, path: Path) -> SourceEvidence:
        data = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(data, dict) or data.get("kind") != "OWNER_VERIFIED_NO_WRITES_WINDOW" or data.get("reviewed") is not True
                or data.get("endpoint") != SOURCE_ENDPOINT or data.get("database") != SOURCE_DATABASE
                or not isinstance(data.get("reference"), str) or not data["reference"].strip()
                or not isinstance(data.get("scope"), list) or not data["scope"]
                or any(not isinstance(name,str) for name in data["scope"])
                or len(data["scope"])!=len(set(data["scope"]))
                or (data.get("geography_roundtrip_reference") is not None and
                    (not isinstance(data["geography_roundtrip_reference"],str) or not data["geography_roundtrip_reference"].strip()))):
            raise PipelineError("SOURCE_CONSISTENCY_EVIDENCE_INVALID")
        try:
            start = datetime.fromisoformat(data["window_start"])
            end = datetime.fromisoformat(data["window_end"])
            if start.tzinfo is None or end.tzinfo is None or end <= start: raise ValueError("window")
        except (ValueError, KeyError, TypeError):
            raise PipelineError("SOURCE_CONSISTENCY_EVIDENCE_INVALID") from None
        return cls(data["reference"], start.astimezone(timezone.utc), end.astimezone(timezone.utc),
                   frozenset(data["scope"]), data.get("geography_roundtrip_reference"))

    def validate(self, start: datetime, end: datetime, objects: tuple[SourceObject, ...], *, publish: bool) -> None:
        if self.start > start or self.end < end or self.scope != frozenset(o.name for o in objects):
            raise PipelineError("SOURCE_CONSISTENCY_WINDOW_OR_SCOPE")
        if publish and any(c.source_type == "geography" for o in objects for c in o.columns) and not self.geography_reference:
            raise PipelineError("GEOGRAPHY_ROUNDTRIP_UNVERIFIED")
