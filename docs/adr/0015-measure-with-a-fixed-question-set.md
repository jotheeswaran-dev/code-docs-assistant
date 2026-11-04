# ADR 0015: Measure with a fixed question set

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-04 |

## Context

Every choice in this system is a guess until we measure it.
A change to the chunker, to the weights, or to the prompt can make the answers worse,
and nobody would see it. A demo of three good answers proves nothing.

We need a number that moves when the system changes.

## Decision

We keep a fixed set of questions about one public repository, `psf/requests`.
A reader can build the same index with one command, so the numbers are reproducible.

| Part | Count | Purpose |
|---|---|---|
| Answerable questions | 12 | Each names the file that a reader should reach |
| Unanswerable questions | 3 | The system must refuse, not invent |

The run has two levels:

| Level | Command | Cost | Measures |
|---|---|---|---|
| Retrieval | `make eval` | Free. No model call. | recall@1, 3, 5, 8 and MRR, for each search |
| Answers | `make eval-answers` | About one dollar | Faithful answers, clean citations, correct refusals |

Retrieval runs for each search alone and for the join, so the value of the join is a
number and not a claim.

The three unanswerable questions matter most. Without them, a system that answers
everything would score full marks.

## What we measured

```
corpus   data/requests.db, 962 chunks
asked    12 answerable, 3 unanswerable

  retrieval    recall@1   recall@3   recall@5   recall@8     MRR
  word             0.67       0.83       0.92       0.92    0.77
  vector           0.58       0.92       0.92       0.92    0.72
  fused            0.67       1.00       1.00       1.00    0.79
```

The join reaches every target by the third result. Neither search alone passes 0.92 at
any depth, and the two miss different questions. ADR 0007 argued for the join. This is
the evidence.

The answer level asks the model and grades each answer.

| Measure | First run | After the two corrections below |
|---|---|---|
| Faithful answers | 12 of 12 | 12 of 12 |
| Citations clean | 5 of 12 | 8 of 12 |
| Refused when it must | 1 of 3 | 3 of 3 |
| Cost for one run | $0.695 | $0.673 |

### The set found two faults, and one was in the set itself

The first run said that the system refused only 1 of 3 questions that it must refuse.
We read the answers before we changed any code. The answers were correct:

> This library does not connect to PostgreSQL. It has no database work at all.

> There is no Kubernetes deployment file in the sources.

Each answer then stated what the repository does hold, with a citation.
The fault was in our grading rule, which read a full explanation as "not a refusal".
We corrected the rule, and the score moved to 3 of 3.

The citation score moved from 5 to 8 because a line such as "What the sources show:"
introduces a list and states no fact. The check now skips a line that ends with a colon.

Four answers still hold a line with no citation. That number is honest. It is almost
always the opening summary line, which restates the cited lines below it.

## Consequences

### Good

- A change to retrieval shows up as a number in under a second.
- The free level runs in a build, because it needs no key and no money.
- The question set is small enough to read, so a wrong target is easy to spot.
- The refusal questions guard the guardrail in ADR 0010.

### Bad

- Twelve questions is a small sample. One question moves recall by 0.08.
- The targets are our own opinion of the right file.
- The corpus clones from the default branch, so the code can change under the test.

### Risk and control

| Risk | Control |
|---|---|
| The set is too easy, so every score is full. | We measure at depth 1 and 3, where the searches separate. |
| A question has a wrong target. | A test holds the shape of the set, and the run names each question that the join missed. |
| The answer level costs money on every run. | It is a separate command. The free level is the default. |

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| A judge only, with no retrieval number | One number for the whole pipeline. But a bad answer could come from retrieval or from the prompt, and the number does not say which. |
| The test repository of the author | Already indexed. But a reviewer cannot clone it, so no number could be checked. |
| A large set written by a model | More questions, and less work. But nobody checks the targets, so a wrong target becomes a wrong score that looks right. |
