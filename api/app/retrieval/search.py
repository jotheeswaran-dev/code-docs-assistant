"""Word search and vector search, joined with Reciprocal Rank Fusion."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from app.ingest.models import Chunk
from app.retrieval.embedding import embed_query
from app.store import Store

RRF_K = 60
DEFAULT_LIMIT = 10
DEFAULT_POOL = 50


@dataclass(frozen=True, slots=True)
class Result:
    chunk: Chunk
    score: float
    lexical_rank: int | None = None
    vector_rank: int | None = None
    lexical_score: float | None = None
    vector_distance: float | None = None


def fuse(rankings: Sequence[Sequence[int]], k: int = RRF_K) -> dict[int, float]:
    """RRF reads the rank only. A BM25 score and a distance never share a scale."""
    scores: dict[int, float] = defaultdict(float)
    for ranking in rankings:
        for rank, rowid in enumerate(ranking, start=1):
            scores[rowid] += 1.0 / (k + rank)
    return dict(scores)


def search(
    store: Store,
    query: str,
    limit: int = DEFAULT_LIMIT,
    pool: int = DEFAULT_POOL,
) -> list[Result]:
    lexical = store.lexical(query, pool)
    vector = store.vector(embed_query(query), pool)

    lexical_rank = {hit.rowid: rank for rank, hit in enumerate(lexical, start=1)}
    vector_rank = {hit.rowid: rank for rank, hit in enumerate(vector, start=1)}
    lexical_score = {hit.rowid: hit.score for hit in lexical}
    vector_distance = {hit.rowid: hit.score for hit in vector}

    fused = fuse([list(lexical_rank), list(vector_rank)])
    ordered = sorted(fused.items(), key=lambda item: (-item[1], item[0]))[:limit]

    chunks = store.fetch(rowid for rowid, _ in ordered)
    return [
        Result(
            chunk=chunks[rowid],
            score=score,
            lexical_rank=lexical_rank.get(rowid),
            vector_rank=vector_rank.get(rowid),
            lexical_score=lexical_score.get(rowid),
            vector_distance=vector_distance.get(rowid),
        )
        for rowid, score in ordered
        if rowid in chunks
    ]
