# ADR 0001: Select the Code Documentation Assistant

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-04 |

## Context

The assignment gives four options. We must pick one.

Simple retrieval works well on prose. Code is different. Four problems appear:

1. A user asks with an exact symbol name. Meaning search is weak for an exact name.
2. A chunk that stops in the middle of a function has no meaning.
3. A method without its class has no meaning.
4. Many files name a topic. Only one file holds the code for it.

These four problems force real design work. The assignment grades that work.

## Decision

We build Option 2, the Code Documentation Assistant.

## Consequences

### Good

- The problems above are real. Each solution maps to a point that the assignment grades.
- The citation is exact. It points to a file and to line numbers.
- We can test the answers against a known repository.

### Bad

- The ingest step is more work than for plain text.
- A parser for each language costs time.

### Risk and control

| Risk | Control |
|---|---|
| The ingest step takes too much of the time budget. | Only Python and TypeScript get a parser. All other files use a line window. |
| The repository is too large to ingest. | We set a limit for the file count and the file size. |

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| 1. Chat with your documents | The assignment calls it the classic use case. It gives no room to show a design choice. |
| 3. Meeting intelligence | A close second. Transcripts have a good structure. But the retrieval problem is easier than for code. |
| 4. Career intelligence | The best product idea. But the document set is small. Retrieval does little work, so we cannot show the hard part. |
