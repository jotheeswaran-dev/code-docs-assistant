# Evidence

## 1. Purpose

This document holds every number that we measured.
Each decision record points at the measure that supports it.
We write this document in Simplified Technical English (ASD-STE100).

## 2. The machine

| Item | Value |
|---|---|
| Computer | Apple Silicon, 11 cores |
| Python | 3.12.12 |
| SQLite | 3.50.4 |
| Answer model | `claude-opus-5` |
| Bulk model and judge | `claude-haiku-4-5` |
| Embedding model | `BAAI/bge-small-en-v1.5`, 384 numbers, on the CPU |

## 3. Ingest

| Repository | Files | Chunks | From syntax | Time to cut | Time to embed |
|---|---|---|---|---|---|
| A dotfiles repository, mostly Ruby | 354 | 2453 | 731 (30%) | 0.22s | 276s |
| `psf/requests`, mostly Python | 113 | 962 | 716 (74%) | 2.03s | 117s |

The share from syntax follows the language. A repository with a parser for most files
gives more chunks that carry a symbol name.

| Measure | Value |
|---|---|
| Embedding speed, real code chunks | 12.5 chunks each second |
| Embedding speed, one short string many times | 450 chunks each second, which is not a real workload |
| Chunk size, median | 726 characters |
| Chunk size, 90th place | 2806 characters |
| Index size for 2453 chunks | 11 MB |

Two changes to the embedding step were tested. Both were slower.

| Change | Speed |
|---|---|
| Default settings | 12.5 each second |
| Sort the chunks by length | 8.0 each second |
| Worker processes | 3.3 each second |

## 4. Retrieval

Measured over 12 answerable questions about `psf/requests`, 962 chunks.

| Search | recall@1 | recall@3 | recall@5 | recall@8 | MRR |
|---|---|---|---|---|---|
| Word only | 0.67 | 0.83 | 0.92 | 0.92 | 0.77 |
| Vector only | 0.58 | 0.92 | 0.92 | 0.92 | 0.72 |
| Joined with RRF | 0.67 | **1.00** | **1.00** | **1.00** | 0.79 |

The join reaches every target by the third result.
Neither search alone passes 0.92 at any depth.

A search takes 82 milliseconds on the host, and 17 to 30 milliseconds in the container
once the model is warm.

## 5. Answers

| Measure | Result |
|---|---|
| Faithful to the sources, graded by a second model | 12 of 12 |
| Every claim carries a citation | 8 of 12 |
| Refused when the repository holds no answer | 3 of 3 |
| An invented source id, over every run | 0 |

The four answers that are not clean open with a summary line that restates the cited
lines below it. That line carries no citation of its own.

## 6. Cost and the cache

| Measure | Cold | Warm |
|---|---|---|
| Cache tokens | 12701 written | 12701 read |
| Cost for one question | $0.123 | $0.033 to $0.065 |

The cache holds the rules and the repository map. A later question reads them, and the
cost falls by about 60 percent.

A full answer run over 15 questions costs about $0.67.
The retrieval run costs nothing and takes 0.2 seconds.

## 7. Build

| Measure | Value |
|---|---|
| API image | 1.09 GB, which holds the ONNX runtime and the model |
| Web image | 323 MB |
| First-load code for the page | 130 kB, of which 26 kB is the highlighter |
| Tests | 81 |

## 8. What a measurement changed

A measurement is only useful when it changes a decision. These changed.

| Measurement | What changed |
|---|---|
| 12.5 chunks each second, not 450 | ADR 0004 held a wrong number from a test that used one short string. |
| Worker processes ran 4 times slower | We keep the default settings, and we record the test. |
| A real answer flagged 4 false faults | The citation check now reads one line as one claim, and skips a heading and a lead-in. |
| The eval said 1 of 3 refusals | The fault was our grading rule. The answers were correct. The rule now reads a full explanation as a refusal. |
| `DELETE` on an empty word index passed, and failed once it held rows | A second index build would have failed. The store now drops the tables and builds them again. |
| A clone was missing three files | The global ignore file of the machine holds `lib/`. A rule in the repository keeps that folder. |
| A build during a dev run broke the page | The two commands now write to separate folders. |
