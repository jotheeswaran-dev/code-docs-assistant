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

We tested the model before this decision. That first test was wrong.
It sent one short string many times, and it gave 450 chunks each second.

A later test used real chunks from the test repository. A chunk holds 2221 characters
on average. A chunk of that size fills the 512 token limit of the model.

| Measure | Result |
|---|---|
| Vector size | 384 numbers |
| Speed, one short string | 450 chunks each second (not a real workload) |
| Speed, real code chunks | 12.5 chunks each second, on a machine with 11 cores |
| Time for 2453 chunks | About 200 seconds |

We tried two ways to make it faster. We measured both. Both were slower.

| Change | Result | Reason |
|---|---|---|
| Worker processes | 3.3 chunks each second | ONNX already uses many threads. Each worker loads the model again. |
| Sort the chunks by length | 8.0 chunks each second | The library already groups a batch well. The sort only moved work. |

We keep the default settings of the library.

## Consequences

### Good

- The reviewer needs one key only. The ingest step needs no key at all.
- The ingest step costs nothing. We can ingest a repository many times during a test.
- The container holds the model. The system works without the internet after the build.
- The ingest step runs one time. It writes a file, and every later question reads that file.

### Bad

- The model is small. A large hosted model would give a better match for the meaning.
- The container image grows by about 150 MB.
- The ingest step takes about 200 seconds for 2453 chunks. A hosted model with a GPU would be faster.

### Risk and control

| Risk | Control |
|---|---|
| The small model gives a weak match. | Word search runs beside the vector search. For code, the word search does much of the work. |
| The first run downloads the model. | The container build step downloads the model. The run step needs no download. |
| A large repository takes too long to index. | The index is a file. It is built one time and then read many times. A GPU or a hosted model is the next step. |

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| A hosted embedding service | Better quality. But it needs a second vendor, a second key, and money for each ingest run. |
| `sentence-transformers` | The same models. But it pulls in PyTorch. The image would grow by about 2 GB. |
| No vector search | Word search alone. Simpler. But a question about intent would fail. See ADR 0007. |
