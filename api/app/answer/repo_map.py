"""A short map of the whole repository, built from the chunks. It needs no model."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Sequence

from app.ingest.models import Chunk
from app.store import FileEntry

MAX_SYMBOLS = 8
MAX_SUMMARY_CHARS = 110
DEFAULT_BUDGET_CHARS = 24_000

# A heading marker or a comment marker at the start of a line.
_MARKER = re.compile(r'^[\s#/*\-=<>"\']+')
_TRIVIAL_LINE = re.compile(r"^[\s{}()\[\];,.\-=_*#/]*$")


def build(chunks: Sequence[Chunk]) -> list[FileEntry]:
    by_path: dict[str, list[Chunk]] = defaultdict(list)
    for chunk in chunks:
        by_path[chunk.path].append(chunk)

    entries = []
    for path, group in sorted(by_path.items()):
        ordered = sorted(group, key=lambda c: c.start_line)
        entries.append(
            FileEntry(
                path=path,
                language=ordered[0].language,
                lines=max(c.end_line for c in ordered),
                chunks=len(ordered),
                summary=_summarise(ordered),
            )
        )
    return entries


def render(entries: Sequence[FileEntry], budget_chars: int = DEFAULT_BUDGET_CHARS) -> str:
    """The largest files come first, so a cut drops the smallest ones."""
    ranked = sorted(entries, key=lambda e: (-e.chunks, e.path))
    lines: list[str] = []
    used = 0
    for entry in ranked:
        line = f"{entry.path} ({entry.language}, {entry.lines} lines) - {entry.summary}"
        if used + len(line) > budget_chars:
            lines.append(f"... and {len(ranked) - len(lines)} more files, not listed")
            break
        lines.append(line)
        used += len(line) + 1

    lines.sort()
    return "\n".join(lines)


def _summarise(ordered: Sequence[Chunk]) -> str:
    symbols = [c.symbol for c in ordered if c.symbol and c.kind != "file_part"]
    if symbols:
        unique = list(dict.fromkeys(symbols))[:MAX_SYMBOLS]
        text = ", ".join(unique)
        if len(unique) < len({s for s in symbols}):
            text += ", ..."
        return text[:MAX_SUMMARY_CHARS]
    return _headline(ordered[0].text)


def _headline(text: str) -> str:
    """A file with no symbol keeps its first real line, such as a title or a comment."""
    for raw in text.splitlines()[:20]:
        line = _MARKER.sub("", raw).strip()
        if line and not _TRIVIAL_LINE.match(line) and len(line) > 2:
            return line[:MAX_SUMMARY_CHARS]
    return "no summary"
