# ADR 0007: Use hybrid retrieval with RRF

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-04 |

## Context

A user asks about code in two different ways.

| The user asks | Example | What finds it |
|---|---|---|
| With an exact name | "Where is `retry_with_backoff`?" | Word search. The name is an exact token. |
| With intent | "How does the client repeat a failed call?" | Vector search. No word in the question matches the code. |

Vector search alone fails for the first row. A symbol name is often one rare token.
The embedding model has not seen that name.

Word search alone fails for the second row. The question and the code share no words.

## Decision

We run both searches for every question. We join the two result lists with
Reciprocal Rank Fusion (RRF).

RRF gives a score to each chunk from its rank in each list:

```
score(chunk) = sum over lists of  1 / (k + rank in that list)
```

We set `k` to 60, which is the common value.

RRF uses the rank only. It does not use the raw score.
This matters, because a BM25 score and a vector distance are not on the same scale.

## Consequences

### Good

- A chunk that is high in both lists moves to the top.
- No scale problem. We never need to normalise two different scores.
- The code is short. The rule is easy to explain and easy to test.
- We log both ranks and the final score. The trace view shows them.

### Bad

- RRF ignores how strong a match is. A very strong word match gets no extra weight.
- Two searches cost more time than one.

### Risk and control

| Risk | Control |
|---|---|
| RRF ranks worse than one search alone. | The eval set measures recall for word search, vector search, and RRF. We keep the best. |

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| A cross-encoder reranker | The best quality. But it adds a second model, more memory, and more time. RRF is enough for the first version. |
| A weighted sum of scores | It can use the match strength. But BM25 and vector distance need normalisation, and the weights need tuning. |
| Vector search alone | One search. But it fails on an exact symbol name, which is a common question. |
