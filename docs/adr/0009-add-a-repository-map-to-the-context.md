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
The map holds one line for each file. The chunker supplies that line, not a model.

    scripts/utilities/brew_bundle.rb (ruby, 230 lines) - BrewBundle, BrewBundle.run, ...
    docs/fresh-install.md (text, 520 lines) - Fresh install guide

A file with a parser lists its symbols. A file with no parser keeps its first real
line, such as a title or a comment.

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

- A symbol list states what a file holds. It does not state why the file exists.
- A very large repository makes a map that is too big for the prompt.

### Risk and control

| Risk | Control |
|---|---|
| The map is too large for the prompt. | The render step takes a character budget. The largest files stay, and the line states how many files it dropped. |
| The cache does not work. | We read `cache_read_input_tokens` from each response, and the trace shows it. A measured run wrote 12701 tokens for the first question, then read the same 12701 for every later question. |

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| Chunks only | Simple, and cheap. But a question about the structure always fails. |
| The file tree, with no summary | Free. But a file name alone does not say what the file holds. |
| One Claude Haiku call for each file | A better line, in plain words. But see the update below. |
| A tool call that reads the tree when needed | The model asks only when it needs the map. But it adds a turn, and it makes each answer slower. |

## Update, 2026-11-04

The first version of this record said that Claude Haiku 4.5 writes each line.
We built it without a model call. Three reasons made the change:

1. ADR 0003 states that the ingest step runs with no key. A model call would end that rule.
2. The chunker already holds every symbol in every file. That list is most of the map.
3. A call for each file costs money, and it adds about two minutes for 354 files.

The map is now free, instant, and the same on every run.
A model call can enrich it later. The first version does not need one.
