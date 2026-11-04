from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Chunk:
    path: str
    language: str
    kind: str
    start_line: int
    end_line: int
    text: str
    symbol: str | None = None
    parent: str | None = None
    imports: tuple[str, ...] = ()
    part: int = 1
    parts: int = 1

    @property
    def id(self) -> str:
        key = f"{self.path}:{self.start_line}-{self.end_line}:{self.part}"
        return hashlib.sha1(key.encode()).hexdigest()[:16]

    @property
    def label(self) -> str:
        where = f"{self.path}:{self.start_line}-{self.end_line}"
        if self.parts > 1:
            where = f"{where} (part {self.part} of {self.parts})"
        return f"{where} · {self.symbol}" if self.symbol else where

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, **asdict(self), "imports": list(self.imports)}
