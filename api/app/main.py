from __future__ import annotations

import json
import time
from collections.abc import Iterator
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app import __version__
from app.answer.claude import ClaudeAnswerer
from app.answer.pipeline import answer
from app.config import Settings, get_settings
from app.retrieval.search import search
from app.store import IndexVersionError, Store


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


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=8, ge=1, le=20)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Code Documentation Assistant", version=__version__)

    @app.get("/health", response_model=Health)
    def health() -> Health:
        chunks, source = None, None
        try:
            store = Store.open(settings.store_path)
        except (FileNotFoundError, OSError, IndexVersionError):
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

    @app.post("/chat")
    def chat(request: ChatRequest) -> StreamingResponse:
        if not settings.anthropic_api_key:
            raise HTTPException(
                status_code=503,
                detail="No ANTHROPIC_API_KEY. The answer step needs a key. Search still works.",
            )
        store = _open_index(settings)
        answerer = ClaudeAnswerer(settings)

        def events() -> Iterator[str]:
            try:
                for event in answer(
                    store, settings, request.question, answerer, limit=request.limit
                ):
                    yield _sse(event)
                yield _sse({"type": "done"})
            except Exception as error:  # noqa: BLE001 - the stream must report, not crash
                yield _sse({"type": "error", "message": _redact(str(error), settings)})
            finally:
                store.close()

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"cache-control": "no-cache", "x-accel-buffering": "no"},
        )

    return app


def _sse(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event)}\n\n"


def _redact(message: str, settings: Settings) -> str:
    key = settings.anthropic_api_key
    return message.replace(key, "***") if key else message


def _open_index(settings: Settings) -> Store:
    try:
        return Store.open(settings.store_path)
    except IndexVersionError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (FileNotFoundError, OSError) as error:
        raise HTTPException(
            status_code=503,
            detail=f"No index at {settings.store_path}. Run: make ingest REPO=<path>",
        ) from error


app = create_app()
