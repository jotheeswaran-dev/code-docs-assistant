# ADR 0012: Cover every line once, with no overlap

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-04 |

## Context

Many retrieval systems cut a document into windows that overlap.
The overlap is a guard. It stops a cut in the middle of an idea from losing the context.

We cut code on syntax limits, so a definition is already complete. See ADR 0006.
Two problems stay:

1. Code outside a definition belongs to no chunk. A script holds much of this code.
2. A class header and its methods must not hold the same lines twice.

## Decision

Every line of every file belongs to exactly one chunk. No chunk overlaps another.

| Rule | Effect |
|---|---|
| A definition becomes one chunk. | The chunk holds the complete function, method, or class. |
| A container keeps a header chunk. | The header stops at the line before the first inner definition. |
| A gap becomes a line window. | Code outside any definition still reaches the index. |
| A line with no meaning is dropped. | A line that holds only `end`, `}`, or a space joins no chunk. |

Two tests hold this rule for every fixture file:

- No chunk overlaps the next chunk.
- Every line that carries meaning belongs to a chunk.

We add context at the time of the answer, not at the time of the index.
A chunk records its parent, so we can add the class header to the prompt. See ADR 0009.

## Consequences

### Good

- The index holds each line one time. The store is smaller.
- A search cannot return the same code twice under two chunk names.
- An embedding is never made for duplicate text.
- The rule is a test. A fault in the chunker fails the build.

### Bad

- A definition that needs its neighbour must read the store a second time.
- The expansion step at answer time is more work than an overlap would be.

### Risk and control

| Risk | Control |
|---|---|
| A cut loses the context of a neighbour. | The chunk records its parent and its line numbers. The answer step reads the neighbours. |
| A very large definition still needs a cut. | We split it into parts. Each part records its number, such as `part 2 of 3`. |

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| A window with an overlap | The common choice. But it stores the same lines twice, embeds them twice, and can return the same code under two names. |
| A chunk for each file | No cut at all. But a large file fills the prompt, and the citation is not exact. |
| Drop the code outside a definition | Simpler. But a shell script or a config script is almost all top-level code, and it would vanish from the index. |
