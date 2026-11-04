# Architecture Decision Records

Each record holds one decision. It gives the context, the decision, the result,
and the options that we rejected.

We write these records in Simplified Technical English (ASD-STE100).

| # | Decision | Status |
|---|---|---|
| [0001](0001-select-the-code-documentation-assistant.md) | Select the Code Documentation Assistant | Accepted |
| [0002](0002-use-python-fastapi-and-nextjs.md) | Use Python with FastAPI, and Next.js | Accepted |
| [0003](0003-use-claude-models.md) | Use Claude models | Accepted |
| [0004](0004-use-a-local-embedding-model.md) | Use a local embedding model | Accepted |
| [0005](0005-use-sqlite-for-storage.md) | Use SQLite for the store | Accepted |
| [0006](0006-chunk-code-on-syntax-limits.md) | Cut code on syntax limits | Accepted |
| [0007](0007-use-hybrid-retrieval-with-rrf.md) | Use hybrid retrieval with RRF | Accepted |
| [0008](0008-do-not-use-an-orchestration-framework.md) | Do not use an orchestration framework | Accepted |
| [0009](0009-add-a-repository-map-to-the-context.md) | Add a repository map to the context | Accepted |
| [0010](0010-enforce-citations-and-treat-code-as-data.md) | Enforce citations, and treat code as data | Accepted |

## Template

A new record uses this shape:

1. Title, with the number.
2. A table with the status and the date.
3. Context. What forces the decision.
4. Decision. What we do.
5. Consequences. The good result, the bad result, the risk, and the control.
6. Options that we rejected, with the reason.
