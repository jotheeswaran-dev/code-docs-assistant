"""The embedding model runs on the local CPU. It needs no key and no network."""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache

from fastembed import TextEmbedding

from app.config import get_settings
from app.ingest.models import Chunk


@lru_cache(maxsize=2)
def _model(name: str, cache: str) -> TextEmbedding:
    return TextEmbedding(name, cache_dir=cache)


def model_name() -> str:
    return get_settings().embedding_model


def _loaded() -> TextEmbedding:
    settings = get_settings()
    return _model(settings.embedding_model, settings.embedding_cache)


def embed_documents(texts: Sequence[str]) -> list[list[float]]:
    return [vector.tolist() for vector in _loaded().embed(list(texts))]


def embed_query(text: str) -> list[float]:
    """A BGE model needs a prefix on a question. The library adds the correct one."""
    return next(iter(_loaded().query_embed([text]))).tolist()


def document_text(chunk: Chunk) -> str:
    """The path and the symbol join the body, so a vector match sees the context."""
    header = chunk.path if chunk.symbol is None else f"{chunk.path} · {chunk.symbol}"
    return f"{header}\n{chunk.text}"
