# Decisions

## 1. Purpose

This document records the decisions for the Code Documentation Assistant.
It gives the reason for each decision.
Each important decision also has an Architecture Decision Record in `docs/adr/`.

## 2. Language rules

We write this document in Simplified Technical English (ASD-STE100).
These rules apply:

- One sentence gives one idea.
- Sentences are short.
- We use the active voice.
- We use the same word for the same thing each time.

## 3. What the system does

The system reads a code repository.
A user asks a question about the code.
The system finds the related code.
The system gives an answer. The answer shows the file name and the line numbers.

## 4. Words that we use

| Word | Meaning in this project |
|---|---|
| Chunk | A small part of a source file. One chunk holds one function or one class. |
| Symbol | The name of a function, a class, or a method. |
| Repository map | A short list of all files. Each file has a one-line summary. |
| Retrieval | The step that finds the chunks for a question. |
| Hybrid search | A search that uses word match and meaning match together. |
| RRF | Reciprocal Rank Fusion. A method that joins two result lists into one list. |
| Citation | A link from a sentence in the answer to a file and line numbers. |
| Trace | A record of one question. It holds the chunks, the scores, the time, and the cost. |
| Guardrail | A rule that stops a bad answer. |
| Eval | A test that measures the answer quality with a fixed set of questions. |

## 5. Decisions

| # | Area | Decision | Reason | ADR |
|---|---|---|---|---|
| 1 | Use case | Code Documentation Assistant | Simple search gives bad results on code. The problem is real. | [0001](adr/0001-select-the-code-documentation-assistant.md) |
| 2 | Backend | Python 3.12 and FastAPI | Good support for async work and for streamed answers. | [0002](adr/0002-use-python-fastapi-and-nextjs.md) |
| 3 | Frontend | Next.js | Fast path to a clear user interface. | [0002](adr/0002-use-python-fastapi-and-nextjs.md) |
| 4 | Answer model | Claude Opus 5 | The only model key that we have. It reads code well. | [0003](adr/0003-use-claude-models.md) |
| 5 | Bulk model | Claude Haiku 4.5 | We make many small calls for the repository map and the eval judge. This model is cheap. | [0003](adr/0003-use-claude-models.md) |
| 6 | Embedding model | `bge-small-en-v1.5`, local | Anthropic has no embedding model. A local model needs no second key and costs nothing. | [0004](adr/0004-use-a-local-embedding-model.md) |
| 7 | Storage | SQLite with sqlite-vec and FTS5 | One file holds the chunks, the vectors, and the word index. No database server. | [0005](adr/0005-use-sqlite-for-storage.md) |
| 8 | Chunking | tree-sitter for Python, TypeScript, and Ruby | A chunk holds one complete function or class. A chunk never stops in the middle. | [0006](adr/0006-chunk-code-on-syntax-limits.md) |
| 9 | Retrieval | Word search and vector search, joined with RRF | Users ask with exact symbol names. Word search finds these names. Vector search finds the intent. | [0007](adr/0007-use-hybrid-retrieval-with-rrf.md) |
| 10 | Orchestration | No framework | A short and clear pipeline shows the design better than a framework. | [0008](adr/0008-do-not-use-an-orchestration-framework.md) |
| 11 | Context | Repository map and parent expansion | The model needs a view of the full repository before it reads one chunk. | [0009](adr/0009-add-a-repository-map-to-the-context.md) |
| 12 | Guardrails | Citations, refusal, untrusted source code | Source code can hold an attack in a comment. We treat all code as data. | [0010](adr/0010-enforce-citations-and-treat-code-as-data.md) |
| 13 | Browser path | A proxy route in the web app | One origin, so no CORS rules. The API address is read at request time. | [0011](adr/0011-send-browser-calls-through-a-proxy-route.md) |
| 14 | Chunk coverage | Every line in one chunk, with no overlap | The index holds no duplicate text. A search cannot return the same code twice. | [0012](adr/0012-cover-every-line-once.md) |

## 6. Facts that we measured

We tested each risky part before we made the decision.
The table shows the result of each test.

| Question | Result | Effect |
|---|---|---|
| Can Python load an SQLite extension? | Yes. CPython 3.12.12 and SQLite 3.50.4. | Decision 7 is safe. |
| Does `sqlite-vec` find nearest vectors? | Yes. A KNN query returned the correct order. | Decision 7 is safe. |
| Does FTS5 give a BM25 score? | Yes. FTS5 is part of SQLite. | We need no extra search engine. |
| Does tree-sitter give symbol names and line numbers? | Yes. For Python, TypeScript, TSX, and JavaScript. | Decision 8 is safe. |
| How fast is the local embedding model? | 450 chunks each second on the CPU. 384 numbers for each vector. | A repository with 2000 chunks takes about 5 seconds. |
| Does the stack run in containers? | Yes. `docker compose up` starts both services. The web app reaches the API. | Step 1 is complete. |
| Does the chunker work on a real repository? | 354 files gave 2453 chunks in 0.22 seconds. 731 chunks carry a symbol name. | Step 2 is complete. |
| Does a key reach the index? | No. The walker skips a file that looks like a key, and a test holds that rule. | The risk in ADR 0010 has a control. |
| How fast is the real embedding step? | 12.5 chunks each second. 2453 chunks take about 200 seconds. | The first measure of 450 each second was wrong. ADR 0004 holds the correction. |
| Does the join beat one search alone? | Yes. Each search made a first-place fault that the other corrected. | ADR 0007 holds the three questions and the results. |
| How fast is one search? | 82 milliseconds. That time holds both searches and the question vector. | Fast enough for a chat reply. |

## 7. Points that stay open

| Point | Plan |
|---|---|
| Reranker model | We do not add one. RRF is enough for the first version. The eval step will test this. |
| Index speed | 200 seconds for 2453 chunks. A GPU or a hosted model is the next step for a large repository. |
| More languages | Bash, Lua, and Markdown use a line window now. A parser for each is a short list of node names. |
| Production database | We keep the SQLite interface small. ADR 0005 shows the move to pgvector. |
