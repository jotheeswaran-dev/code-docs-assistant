from __future__ import annotations

import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import __version__
from app.config import Settings, get_settings
from app.retrieval.search import search
from app.store import Store


class Health(BaseModel):
    status: str
    version: str
    answer_model: str
    anthropic_key_set: bool
    indexed_chunks: int | None = None
    indexed_source: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)


class Hit(BaseModel):
    id: str
    path: str
    symbol: str | None
    kind: str
    language: str
    start_line: int
    end_line: int
    label: str
    text: str
    score: float
    lexical_rank: int | None
    vector_rank: int | None


class SearchResponse(BaseModel):
    query: str
    took_ms: float
    hits: list[Hit]


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Code Documentation Assistant", version=__version__)

    @app.get("/health", response_model=Health)
    def health() -> Health:
        chunks, source = None, None
        try:
            store = Store.open(settings.store_path)
        except (FileNotFoundError, OSError):
            pass
        else:
            chunks = store.count()
            source = store.meta().get("source")
            store.close()

        return Health(
            status="ok",
            version=__version__,
            answer_model=settings.answer_model,
            anthropic_key_set=bool(settings.anthropic_api_key),
            indexed_chunks=chunks,
            indexed_source=source,
        )

    @app.post("/search", response_model=SearchResponse)
    def run_search(request: SearchRequest) -> SearchResponse:
        store = _open_index(settings)
        try:
            started = time.perf_counter()
            results = search(store, request.query, limit=request.limit)
            took = (time.perf_counter() - started) * 1000
        finally:
            store.close()

        return SearchResponse(
            query=request.query,
            took_ms=round(took, 1),
            hits=[
                Hit(
                    id=result.chunk.id,
                    path=result.chunk.path,
                    symbol=result.chunk.symbol,
                    kind=result.chunk.kind,
                    language=result.chunk.language,
                    start_line=result.chunk.start_line,
                    end_line=result.chunk.end_line,
                    label=result.chunk.label,
                    text=result.chunk.text,
                    score=round(result.score, 6),
                    lexical_rank=result.lexical_rank,
                    vector_rank=result.vector_rank,
                )
                for result in results
            ],
        )

    return app


def _open_index(settings: Settings) -> Store:
    try:
        return Store.open(settings.store_path)
    except (FileNotFoundError, OSError) as error:
        raise HTTPException(
            status_code=503,
            detail=f"No index at {settings.store_path}. Run: make ingest REPO=<path>",
        ) from error


app = create_app()
