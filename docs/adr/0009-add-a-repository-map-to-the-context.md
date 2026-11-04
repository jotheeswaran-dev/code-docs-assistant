# ADR 0009: Add a repository map to the context

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-04 |

## Context

Retrieval gives the model five to ten chunks. The model sees nothing else.

This causes two failures:

1. The model cannot say where a chunk sits in the system.
2. The model cannot answer a question about the whole repository, such as
   "Which part handles authentication?" No single chunk holds that answer.

A person reads a repository in a different order. A person looks at the file tree first.

## Decision

We build a repository map during the ingest step.
The map holds the file tree, and one line for each file.
Claude Haiku 4.5 writes each line.

The map goes into the system prompt for every question.
We set the cache point after the map.

We also add the parent of each chunk. A method chunk carries its class header and the imports.

## Consequences

### Good

- The model sees the whole repository before it reads one chunk.
- A question about the structure now has an answer.
- The map does not change between questions. The cache holds it, so the cost stays low.
- The map is small. One line for each file.

### Bad

- The ingest step makes one model call for each file. This costs time and money.
- A very large repository makes a map that is too big for the prompt.

### Risk and control

| Risk | Control |
|---|---|
| The map costs too much for a large repository. | We use the cheap model. We set a file limit. Above the limit, the map holds the tree only. |
| The cache does not work. | We read `cache_read_input_tokens` from the response. The trace view shows this number. |

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| Chunks only | Simple, and cheap. But a question about the structure always fails. |
| The file tree, with no summary | Free. But a file name alone does not say what the file does. |
| A tool call that reads the tree when needed | The model asks only when it needs the map. But it adds a turn, and it makes each answer slower. |
