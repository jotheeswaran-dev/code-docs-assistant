import pytest

from app.ingest.models import Chunk
from app.retrieval import search as search_module
from app.store import EMBEDDING_SIZE, Store


def vector(slot: int) -> list[float]:
    values = [0.0] * EMBEDDING_SIZE
    values[slot % EMBEDDING_SIZE] = 1.0
    return values


def chunk(symbol: str, text: str, line: int) -> Chunk:
    return Chunk(
        path="lib/net.py",
        language="python",
        kind="function",
        start_line=line,
        end_line=line + 2,
        text=text,
        symbol=symbol,
    )


def test_fusion_rewards_a_result_that_both_searches_rank():
    scores = search_module.fuse([[1, 2, 3], [3, 1, 9]])
    assert max(scores, key=scores.get) == 1
    assert scores[9] == pytest.approx(1 / (60 + 3))


def test_fusion_reads_the_rank_and_not_the_score():
    """First place is worth the same, whatever scale the search used."""
    assert search_module.fuse([[7]])[7] == pytest.approx(search_module.fuse([[8]])[8])
    assert search_module.fuse([[1, 2]])[1] > search_module.fuse([[1, 2]])[2]


@pytest.fixture
def store(tmp_path):
    made = Store.open(tmp_path / "store.db", create=True)
    made.write(
        [
            chunk("retry_with_backoff", "sleep and try the call again", 1),
            chunk("parse_header", "read the header fields", 10),
            chunk("open_socket", "connect to the host", 20),
        ],
        [vector(0), vector(1), vector(2)],
    )
    yield made
    made.close()


def test_search_joins_both_searches(store, monkeypatch):
    monkeypatch.setattr(search_module, "embed_query", lambda _: vector(1))
    results = search_module.search(store, "retry_with_backoff", limit=3)

    assert results
    assert results[0].chunk.symbol == "retry_with_backoff"
    assert results[0].lexical_rank == 1
    assert any(r.vector_rank == 1 for r in results)


def test_a_vector_only_match_still_appears(store, monkeypatch):
    """No word of the question matches the code, so only the vector finds it."""
    monkeypatch.setattr(search_module, "embed_query", lambda _: vector(2))
    results = search_module.search(store, "zzzz nothing matches", limit=3)

    assert results[0].chunk.symbol == "open_socket"
    assert results[0].lexical_rank is None
    assert results[0].vector_rank == 1


def test_every_result_reports_where_it_came_from(store, monkeypatch):
    monkeypatch.setattr(search_module, "embed_query", lambda _: vector(0))
    for result in search_module.search(store, "header", limit=3):
        assert result.lexical_rank is not None or result.vector_rank is not None
        assert result.score > 0
