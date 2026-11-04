"""One SQLite file holds the chunks, their vectors, and the word index."""

from __future__ import annotations

import re
import sqlite3
import struct
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import sqlite_vec

from app.ingest.models import Chunk

EMBEDDING_SIZE = 384

# A symbol match counts far more than a mention in the body.
BM25_WEIGHTS = (10.0, 3.0, 1.0)

SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    rowid      INTEGER PRIMARY KEY,
    id         TEXT UNIQUE NOT NULL,
    path       TEXT NOT NULL,
    language   TEXT NOT NULL,
    kind       TEXT NOT NULL,
    symbol     TEXT,
    parent     TEXT,
    start_line INTEGER NOT NULL,
    end_line   INTEGER NOT NULL,
    part       INTEGER NOT NULL,
    parts      INTEGER NOT NULL,
    imports    TEXT NOT NULL,
    text       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS chunks_by_path ON chunks(path, start_line);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
USING fts5(symbol, path, body, content='', tokenize='unicode61');

CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

_WORD = re.compile(r"[^A-Za-z0-9]+")
_CAMEL = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z]+|\d+")


@dataclass(frozen=True, slots=True)
class Hit:
    rowid: int
    score: float


def split_identifier(text: str) -> list[str]:
    """`retry_with_backoff` and `retryWithBackoff` both give retry, with, backoff."""
    words: list[str] = []
    for part in _WORD.split(text):
        if not part:
            continue
        words.append(part)
        words.extend(_CAMEL.findall(part))
    return list(dict.fromkeys(word.lower() for word in words))


class Store:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._db = connection

    @classmethod
    def open(cls, path: Path | str, create: bool = False) -> Store:
        target = Path(path)
        if not create and not target.exists():
            raise FileNotFoundError(target)
        if create:
            target.parent.mkdir(parents=True, exist_ok=True)

        db = sqlite3.connect(target, check_same_thread=False)
        db.row_factory = sqlite3.Row
        db.enable_load_extension(True)
        sqlite_vec.load(db)
        db.enable_load_extension(False)

        if create:
            _create_tables(db)
        return cls(db)

    def close(self) -> None:
        self._db.close()

    def clear(self) -> None:
        """A contentless FTS5 table refuses DELETE once it holds rows, so drop and build again."""
        self._db.executescript(
            "DROP TABLE IF EXISTS chunks;"
            "DROP TABLE IF EXISTS chunks_fts;"
            "DROP TABLE IF EXISTS chunks_vec;"
            "DROP TABLE IF EXISTS meta;"
        )
        _create_tables(self._db)

    def write(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("every chunk needs one vector")

        rows = self._db.execute("SELECT COALESCE(MAX(rowid), 0) FROM chunks").fetchone()[0]
        start = rows + 1

        self._db.executemany(
            "INSERT INTO chunks (rowid, id, path, language, kind, symbol, parent,"
            " start_line, end_line, part, parts, imports, text)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    start + offset,
                    c.id,
                    c.path,
                    c.language,
                    c.kind,
                    c.symbol,
                    c.parent,
                    c.start_line,
                    c.end_line,
                    c.part,
                    c.parts,
                    "\n".join(c.imports),
                    c.text,
                )
                for offset, c in enumerate(chunks)
            ],
        )
        self._db.executemany(
            "INSERT INTO chunks_fts (rowid, symbol, path, body) VALUES (?,?,?,?)",
            [
                (
                    start + offset,
                    " ".join(split_identifier(c.symbol or "")),
                    " ".join(split_identifier(c.path)),
                    c.text,
                )
                for offset, c in enumerate(chunks)
            ],
        )
        self._db.executemany(
            "INSERT INTO chunks_vec (rowid, embedding) VALUES (?,?)",
            [(start + offset, struct.pack(f"{len(v)}f", *v)) for offset, v in enumerate(vectors)],
        )
        self._db.commit()

    def set_meta(self, key: str, value: str) -> None:
        self._db.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?,?)", (key, value))
        self._db.commit()

    def meta(self) -> dict[str, str]:
        return {row["key"]: row["value"] for row in self._db.execute("SELECT key, value FROM meta")}

    def count(self) -> int:
        return self._db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]

    def lexical(self, query: str, limit: int) -> list[Hit]:
        match = _match_expression(query)
        if not match:
            return []
        rows = self._db.execute(
            "SELECT rowid, bm25(chunks_fts, ?, ?, ?) AS score FROM chunks_fts"
            " WHERE chunks_fts MATCH ? ORDER BY score LIMIT ?",
            (*BM25_WEIGHTS, match, limit),
        ).fetchall()
        return [Hit(row["rowid"], row["score"]) for row in rows]

    def vector(self, embedding: Sequence[float], limit: int) -> list[Hit]:
        rows = self._db.execute(
            "SELECT rowid, distance FROM chunks_vec"
            " WHERE embedding MATCH ? AND k = ? ORDER BY distance",
            (struct.pack(f"{len(embedding)}f", *embedding), limit),
        ).fetchall()
        return [Hit(row["rowid"], row["distance"]) for row in rows]

    def fetch(self, rowids: Iterable[int]) -> dict[int, Chunk]:
        wanted = list(rowids)
        if not wanted:
            return {}
        marks = ",".join("?" * len(wanted))
        rows = self._db.execute(f"SELECT * FROM chunks WHERE rowid IN ({marks})", wanted).fetchall()
        return {row["rowid"]: _to_chunk(row) for row in rows}

    def neighbours(self, path: str, start_line: int, end_line: int) -> list[Chunk]:
        """The chunks directly before and after, used to widen the context."""
        rows = self._db.execute(
            "SELECT * FROM chunks WHERE path = ? AND (end_line = ? - 1 OR start_line = ? + 1)"
            " ORDER BY start_line",
            (path, start_line, end_line),
        ).fetchall()
        return [_to_chunk(row) for row in rows]


def _create_tables(db: sqlite3.Connection) -> None:
    db.executescript(SCHEMA)
    db.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec "
        f"USING vec0(embedding float[{EMBEDDING_SIZE}])"
    )
    db.commit()


def _to_chunk(row: sqlite3.Row) -> Chunk:
    return Chunk(
        path=row["path"],
        language=row["language"],
        kind=row["kind"],
        start_line=row["start_line"],
        end_line=row["end_line"],
        text=row["text"],
        symbol=row["symbol"],
        parent=row["parent"],
        imports=tuple(row["imports"].split("\n")) if row["imports"] else (),
        part=row["part"],
        parts=row["parts"],
    )


def _match_expression(query: str, limit: int = 40) -> str:
    """Quote every term, so a character such as ':' cannot break the FTS5 syntax."""
    terms: list[str] = []
    for raw in re.split(r"\s+", query.strip()):
        if raw:
            terms.extend(split_identifier(raw))
    unique = [term for term in dict.fromkeys(terms) if len(term) > 1]
    return " OR ".join(f'"{term}"' for term in unique[:limit])
