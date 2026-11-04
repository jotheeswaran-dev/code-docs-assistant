# ADR 0004: Use a local embedding model

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-04 |

## Context

Vector search needs an embedding model.
Anthropic has no embedding model. The Anthropic documents point to a partner service.
That partner needs a second key and a second account. We have neither.

We must also embed every chunk of a repository. A hosted model would cost money for each ingest run.

## Decision

We use `BAAI/bge-small-en-v1.5`. It runs on the local CPU through the `fastembed` library.
The library uses ONNX. It does not need PyTorch.

We tested the model before this decision:

| Measure | Result |
|---|---|
| Vector size | 384 numbers |
| Speed | 450 chunks each second, on the CPU |
| Time for 2000 chunks | About 5 seconds |

## Consequences

### Good

- The reviewer needs one key only. The ingest step needs no key at all.
- The ingest step costs nothing. We can ingest a repository many times during a test.
- The ingest step is fast. A network call for each batch would be slower.
- The container holds the model. The system works without the internet after the build.

### Bad

- The model is small. A large hosted model would give a better match for the meaning.
- The container image grows by about 150 MB.

### Risk and control

| Risk | Control |
|---|---|
| The small model gives a weak match. | Word search runs beside the vector search. For code, the word search does much of the work. |
| The first run downloads the model. | The container build step downloads the model. The run step needs no download. |

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| A hosted embedding service | Better quality. But it needs a second vendor, a second key, and money for each ingest run. |
| `sentence-transformers` | The same models. But it pulls in PyTorch. The image would grow by about 2 GB. |
| No vector search | Word search alone. Simpler. But a question about intent would fail. See ADR 0007. |
