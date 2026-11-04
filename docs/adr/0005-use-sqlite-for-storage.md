# ADR 0005: Use SQLite for the store

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-04 |

## Context

The store must hold three things:

1. The chunks and their metadata.
2. A vector for each chunk, for the meaning search.
3. A word index, for the exact name search.

The document set is one repository. The set is bounded. It does not grow during use.

## Decision

We use one SQLite file. It holds all three things.

| Need | Part |
|---|---|
| Chunks and metadata | A normal table |
| Vectors | The `sqlite-vec` extension, a `vec0` virtual table |
| Word index | FTS5, which is part of SQLite |

We tested this before the decision:

| Question | Result |
|---|---|
| Can Python load an SQLite extension? | Yes. CPython 3.12.12 and SQLite 3.50.4. |
| Does the vector search return the correct order? | Yes. |
| Does FTS5 give a BM25 score? | Yes. |

## Consequences

### Good

- No database server. The container set stays small.
- One file holds one repository. We can ship a ready file for a fast demo.
- A test makes a store in memory. The test is fast and needs no setup.
- FTS5 gives BM25 with no extra library.

### Bad

- One writer at a time. The system cannot ingest two repositories at the same time.
- The vector search reads all rows. This is fine for a bounded set. It is not fine for millions of rows.

### Risk and control

| Risk | Control |
|---|---|
| A reader thinks that SQLite is not serious. | The README names the exact move to a server database. See the table below. |
| The store must grow later. | All store calls go through one small interface. A second class can use pgvector. |
| The tables change and an old index stays on disk. | The store writes a version number. An old index fails with the exact command to build it again. |
| A rebuild fails on the word index. | An FTS5 table with no stored content refuses `DELETE` once it holds rows. The store drops the tables and builds them again. A test holds this rule. |

## The move to a server database

| Now | Later | Change |
|---|---|---|
| SQLite table | PostgreSQL table | The same columns |
| `sqlite-vec` `vec0` | `pgvector` | The same vector size, 384 |
| FTS5 BM25 | `tsvector` and `ts_rank` | The same word search |
| One file | Amazon RDS | One connection string |

The RRF step and the retrieval step do not change.

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| PostgreSQL with pgvector | It looks like production. But it costs about 1.5 hours for the driver, the migrations, and the test setup. That is 15 percent of the time budget. |
| A hosted vector database | No setup. But it needs a third account. It also splits the vectors from the metadata. |
| Qdrant or Chroma | Good vector search. But we would need a second store for the word index. |
