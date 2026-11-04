# ADR 0003: Use Claude models

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-04 |

## Context

We have an Anthropic API key. We have no other model key.
The system makes two kinds of call:

1. One answer call for each question. This call needs strong reading of code.
2. Many small calls. The repository map needs one call for each file. The eval needs one judge call for each test question.

A strong model for the second group costs too much.

## Decision

| Job | Model | Reason |
|---|---|---|
| Answer a question | `claude-opus-5` | Strong reading of code. A context window of 1M tokens. |
| Write a file summary | `claude-haiku-4-5` | Many small calls. Low cost. |
| Judge an eval answer | `claude-haiku-4-5` | The same reason. |

We turn on adaptive thinking for the answer call.
We stream the answer.
We set a cache point after the repository map.

## Consequences

### Good

- The cache holds the system prompt and the repository map. We send these again for each question. The cache cuts the cost.
- The API response reports the token counts. We show these counts in the trace.
- The stream makes the web app feel fast.

### Bad

- The system needs a network call for each question. An offline demo is not possible.
- The cost grows with the size of the repository map.

### Risk and control

| Risk | Control |
|---|---|
| The reviewer has no API key. | The README states the key as a condition. The ingest step and the search step run without a key. |
| A safety rule stops an answer. | We check the stop reason. We turn on the server-side fallback. |

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| One model for all jobs | Simple. But the file summaries would cost about five times more. |
| A local model for the answer | No cost and no key. But the answer quality on code is much lower. |
