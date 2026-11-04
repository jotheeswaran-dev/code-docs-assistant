# ADR 0013: Stream the answer over server-sent events

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-04 |

## Context

An answer about code takes several seconds. The model reads the sources, thinks,
and then writes. A reader who sees nothing for eight seconds thinks the page is broken.

The page must also show more than the text:

- The sources, so the reader can open the code at once.
- The trace: the chunks, the ranks, the tokens, the cache reads, the cost, and the time.

The sources are known before the model starts. The trace is known only at the end.

## Decision

`POST /chat` returns a stream of server-sent events. Each event names its type.

| Order | Type | Holds |
|---|---|---|
| 1 | `sources` | Every source, with its id, path, symbol, and lines |
| 2..n | `delta` | One piece of the answer text |
| n+1 | `trace` | The usage, the cost, the times, and the citation report |
| last | `done` | Nothing. It marks the end. |
| any | `error` | A message, with the key removed |

The page shows the sources first. The text then fills in. The trace arrives last.

The proxy route in the web app passes the body through. It does not read the body
first. See ADR 0011.

## Consequences

### Good

- The reader sees the sources within about 100 milliseconds.
- The answer appears word by word, so the wait feels short.
- One request carries the text and the measurements. The page needs no second call.
- An error reaches the page as an event, so a failure mid-answer is visible.

### Bad

- A stream is harder to test than one JSON body.
- A reader who wants the whole answer must wait for the last event.

### Risk and control

| Risk | Control |
|---|---|
| The key appears in an error message. | The server removes the key from every error event. |
| A fault leaves the store open. | The event generator closes the store in a `finally` block. |
| The model writes a claim with no proof. | The trace names each such sentence. See ADR 0010. |

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| One JSON response | Simple to test. But the reader waits in silence for the whole answer. |
| WebSocket | Two-way, and good for a chat. But the answer flows one way only, and SSE needs no extra library. |
| Two calls, one for sources and one for the answer | Clear parts. But it doubles the retrieval work, or it needs a server-side cache between the calls. |
