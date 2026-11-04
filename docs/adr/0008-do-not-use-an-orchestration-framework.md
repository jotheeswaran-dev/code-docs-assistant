# ADR 0008: Do not use an orchestration framework

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-04 |

## Context

Frameworks exist for this kind of system. They give a loader, a chunker, a store
interface, and a chain object.

The assignment asks for the choice of the orchestration framework, and the reason.

Our pipeline has six steps. Each step is small:

1. Walk the files.
2. Cut the files into chunks.
3. Make a vector for each chunk.
4. Search, and join the results.
5. Pack the context.
6. Call the model, and check the citations.

## Decision

We write these six steps ourselves. We use no orchestration framework.

We use a library for a single job only:

| Library | Job |
|---|---|
| `tree-sitter` | Parse a source file |
| `fastembed` | Make a vector |
| `sqlite-vec` | Vector search |
| `anthropic` | Call the model |

## Consequences

### Good

- A reader sees the whole pipeline. Nothing hides inside a framework.
- The chunker is the main design work in this project. A framework chunker would hide it.
- We control the prompt exactly. We can set the cache point where we want it.
- Fewer libraries. Fewer version conflicts.

### Bad

- We write code that a framework gives for free, such as a retry rule.
- A new file type needs our own loader.

### Risk and control

| Risk | Control |
|---|---|
| The pipeline grows and becomes hard to read. | Each step is one module with one job. A test covers each step on its own. |

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| A full framework | Fast to start. But it hides the chunker and the prompt, which are the parts that we want to show. |
| A framework for the store only | Less code. But our store needs a word index and a vector index in one file. A generic interface does not fit. |
