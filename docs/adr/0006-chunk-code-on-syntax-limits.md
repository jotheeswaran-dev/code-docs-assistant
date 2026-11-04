# ADR 0006: Cut code on syntax limits

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-04 |

## Context

Retrieval returns chunks. The chunk is the unit of the answer.
A chunk of a fixed size cuts code at the wrong place.

An example shows the problem. A 500-token window can cut a function in the middle.
The first half holds the signature. The second half holds the return value.
Neither half answers a question about the function.

## Decision

We cut each file on syntax limits. We use tree-sitter.
One chunk holds one complete function, method, or class.

Each chunk carries this metadata:

| Field | Example |
|---|---|
| File path | `src/requests/sessions.py` |
| Symbol | `Session.send` |
| Kind | `method` |
| First line, last line | 712, 760 |
| Parent | `class Session` |
| Imports | The import lines of the file |

A parser covers Python, TypeScript, TSX, JavaScript, and Ruby.
We added Ruby when we chose the test repository. That repository holds 137 Ruby files.
Without a Ruby parser, every file would fall back, and the main path would never run.

A file with no parser uses a line window. The window has no overlap. See ADR 0012.

We tested this before the decision. tree-sitter gave the correct symbol name and the
correct line numbers for each language. A later run on the test repository gave this result:

| Measure | Result |
|---|---|
| Files | 354 indexed, 4 skipped |
| Chunks | 2453 in 0.22 seconds |
| From syntax | 731 chunks, with a symbol name |
| From a window | 1722 chunks, for the 214 files with no parser |
| Deepest symbol | `ResurrectRepositories.RepositoryConfig.from_hash` |

## Consequences

### Good

- A chunk is always complete. It never stops in the middle.
- The line numbers make an exact citation.
- The symbol name goes into the word index. A search for a name finds the chunk at once.
- The parent field lets us add the class header to the context. See ADR 0009.

### Bad

- A very long function makes a chunk that is too large. We split it, and we mark each part.
- Each language needs its own list of node types.

### Risk and control

| Risk | Control |
|---|---|
| A parser fails on a file. | The chunker catches the error. The file falls back to a line window. |
| A new language costs time. | The language pack holds many grammars. A new language needs a list of node types only. |

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| A fixed token window | Simple. But it cuts functions in the middle, which is the main problem. |
| One chunk for each file | Always complete. But a large file fills the context window, and the citation is not exact. |
| The Python `ast` module | No extra library. But it works for Python only. |
| More languages now | The language pack holds a grammar for each. But each one needs a node list and a fixture, and the time budget is small. |
