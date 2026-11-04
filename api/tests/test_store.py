import pytest

from app.ingest.models import Chunk
from app.store import EMBEDDING_SIZE, IndexVersionError, Store, split_identifier


def vector(slot: int) -> list[float]:
    """A unit vector, so a test needs no embedding model."""
    values = [0.0] * EMBEDDING_SIZE
    values[slot % EMBEDDING_SIZE] = 1.0
    return values


def chunk(symbol: str, path: str = "lib/session.py", text: str = "body", line: int = 1) -> Chunk:
    return Chunk(
        path=path,
        language="python",
        kind="method",
        start_line=line,
        end_line=line + 2,
        text=text,
        symbol=symbol,
        parent="Session",
        imports=("import os",),
    )


@pytest.fixture
def store(tmp_path):
    made = Store.open(tmp_path / "store.db", create=True)
    yield made
    made.close()


def test_it_writes_and_counts(store):
    store.write([chunk("Session.send"), chunk("Session.close", line=10)], [vector(0), vector(1)])
    assert store.count() == 2


def test_word_search_finds_a_symbol(store):
    store.write(
        [chunk("Session.retry_with_backoff"), chunk("Session.close", line=20)],
        [vector(0), vector(1)],
    )
    hits = store.lexical("retry_with_backoff", 5)
    assert hits
    assert store.fetch([hits[0].rowid])[hits[0].rowid].symbol == "Session.retry_with_backoff"


def test_word_search_splits_a_camel_case_name(store):
    store.write([chunk("Session.retryWithBackoff")], [vector(0)])
    assert store.lexical("retry backoff", 5)


def test_word_search_survives_punctuation(store):
    store.write([chunk("Session.send")], [vector(0)])
    assert store.lexical('what does Session.send() do? "quoted" OR NOT', 5) is not None


def test_word_search_returns_nothing_for_an_empty_query(store):
    store.write([chunk("Session.send")], [vector(0)])
    assert store.lexical("   ", 5) == []


def test_vector_search_returns_the_nearest(store):
    store.write(
        [chunk("a", line=1), chunk("b", line=10), chunk("c", line=20)],
        [vector(0), vector(1), vector(2)],
    )
    hits = store.vector(vector(1), 2)
    assert store.fetch([hits[0].rowid])[hits[0].rowid].symbol == "b"


def test_a_chunk_survives_the_round_trip(store):
    original = chunk("Session.send", text="def send(self):\n    return 1")
    store.write([original], [vector(0)])
    restored = next(iter(store.fetch([1]).values()))
    assert restored == original


def test_it_finds_the_neighbours_of_a_chunk(store):
    store.write(
        [chunk("a", line=1), chunk("b", line=4), chunk("c", line=7)],
        [vector(0), vector(1), vector(2)],
    )
    found = {c.symbol for c in store.neighbours("lib/session.py", 4, 6)}
    assert found == {"a", "c"}


def test_clear_empties_every_table(store):
    store.write([chunk("Session.send")], [vector(0)])
    store.clear()
    assert store.count() == 0
    assert store.lexical("send", 5) == []
    assert store.vector(vector(0), 5) == []


def test_a_mismatched_vector_count_is_refused(store):
    with pytest.raises(ValueError):
        store.write([chunk("a"), chunk("b")], [vector(0)])


def test_a_missing_index_is_an_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        Store.open(tmp_path / "absent.db")


def test_it_splits_an_identifier():
    assert split_identifier("retry_with_backoff") == ["retry", "with", "backoff"]
    assert split_identifier("retryWithBackoff") == ["retrywithbackoff", "retry", "with", "backoff"]
    assert split_identifier("HTTPServer") == ["httpserver", "http", "server"]


def test_an_old_index_fails_with_a_clear_message(tmp_path):
    path = tmp_path / "old.db"
    made = Store.open(path, create=True)
    made._db.execute("UPDATE meta SET value = '0' WHERE key = 'schema_version'")
    made._db.commit()
    made.close()

    with pytest.raises(IndexVersionError, match="make ingest"):
        Store.open(path)
