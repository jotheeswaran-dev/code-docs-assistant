"""Retrieval, the model call, the citation check, and the trace."""

from __future__ import annotations

import re
import time
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from app.answer.prompt import Source, build_messages, build_system, pack
from app.answer.repo_map import render
from app.config import Settings
from app.retrieval.search import search
from app.store import Store

CITATION = re.compile(r"\[(c\d+)\]")
FENCED = re.compile(r"```.*?```", re.S)
INLINE_CODE = re.compile(r"`[^`]*`")
HEADING = re.compile(r"^\s*#{1,6}\s")
LIST_MARKER = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")
MIN_WORDS_FOR_A_CLAIM = 5

NO_SOURCE_ANSWER = (
    "I found nothing in this repository that answers the question. "
    "The index may not hold that code, or the question may name something that is not here."
)


@dataclass(frozen=True, slots=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


@dataclass(frozen=True, slots=True)
class TextDelta:
    text: str


@dataclass(frozen=True, slots=True)
class Completed:
    usage: Usage
    stop_reason: str


Event = TextDelta | Completed


class Answerer(Protocol):
    def stream(
        self, system: list[dict[str, Any]], messages: list[dict[str, Any]]
    ) -> Iterator[Event]: ...


@dataclass(frozen=True, slots=True)
class CitationReport:
    claims: int = 0
    cited: tuple[str, ...] = ()
    unknown: tuple[str, ...] = ()
    uncited: tuple[str, ...] = ()

    @property
    def clean(self) -> bool:
        return not self.unknown and not self.uncited


def validate_citations(text: str, known: set[str]) -> CitationReport:
    """Every claim must name a source. We report a fault. We do not delete the text.

    One line of prose is one claim. We do not cut a line at a full stop, because a
    file name such as `fresh-install.sh` would then become two claims, and the
    citation at the end of the line would belong to only one of them.
    """
    prose = FENCED.sub(" ", text)
    used = tuple(dict.fromkeys(CITATION.findall(prose)))
    unknown = tuple(name for name in used if name not in known)

    uncited: list[str] = []
    claims = 0
    for raw in prose.splitlines():
        if HEADING.match(raw):
            continue  # A heading names a section. It states no fact.
        line = LIST_MARKER.sub("", INLINE_CODE.sub(" code ", raw)).strip()
        if len(line.split()) < MIN_WORDS_FOR_A_CLAIM:
            continue
        claims += 1
        if not CITATION.search(line):
            uncited.append(raw.strip()[:160])

    return CitationReport(claims, used, unknown, tuple(uncited))


def estimate_cost(usage: Usage, settings: Settings) -> float:
    per_token = 1_000_000
    return round(
        usage.input_tokens / per_token * settings.price_input_per_mtok
        + usage.output_tokens / per_token * settings.price_output_per_mtok
        + usage.cache_read_tokens / per_token * settings.price_cache_read_per_mtok
        + usage.cache_write_tokens / per_token * settings.price_cache_write_per_mtok,
        6,
    )


@dataclass
class Trace:
    question: str
    model: str
    sources: list[dict[str, Any]] = field(default_factory=list)
    retrieval_ms: float = 0.0
    answer_ms: float = 0.0
    usage: Usage = field(default_factory=Usage)
    cost_usd: float = 0.0
    citations: CitationReport = field(default_factory=CitationReport)
    stop_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        citations = {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in asdict(self.citations).items()
        }
        return {
            **asdict(self),
            "usage": asdict(self.usage),
            "citations": {**citations, "clean": self.citations.clean},
        }


def answer(
    store: Store,
    settings: Settings,
    question: str,
    answerer: Answerer,
    limit: int = 8,
) -> Iterator[dict[str, Any]]:
    started = time.perf_counter()
    results = search(store, question, limit=limit)
    retrieval_ms = (time.perf_counter() - started) * 1000

    trace = Trace(
        question=question,
        model=settings.answer_model,
        retrieval_ms=round(retrieval_ms, 1),
    )

    if not results:
        yield {"type": "sources", "sources": []}
        yield {"type": "delta", "text": NO_SOURCE_ANSWER}
        trace.stop_reason = "no_sources"
        yield {"type": "trace", "trace": trace.to_dict()}
        return

    sources = pack(results, store, settings.context_budget_chars)
    trace.sources = [_source_row(source) for source in sources]
    yield {"type": "sources", "sources": trace.sources}

    system = build_system(render(store.files()))
    messages = build_messages(sources, question)

    collected: list[str] = []
    answer_started = time.perf_counter()
    for event in answerer.stream(system, messages):
        if isinstance(event, TextDelta):
            collected.append(event.text)
            yield {"type": "delta", "text": event.text}
        else:
            trace.usage = event.usage
            trace.stop_reason = event.stop_reason

    trace.answer_ms = round((time.perf_counter() - answer_started) * 1000, 1)
    trace.cost_usd = estimate_cost(trace.usage, settings)
    trace.citations = validate_citations("".join(collected), {source.id for source in sources})
    yield {"type": "trace", "trace": trace.to_dict()}


def _source_row(source: Source) -> dict[str, Any]:
    chunk = source.chunk
    return {
        "id": source.id,
        "path": chunk.path,
        "symbol": chunk.symbol,
        "kind": chunk.kind,
        "language": chunk.language,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "label": chunk.label,
        "text": chunk.text,
        "enclosing": source.enclosing.text if source.enclosing else None,
    }
