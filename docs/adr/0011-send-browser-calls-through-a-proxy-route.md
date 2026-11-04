# ADR 0011: Send browser calls through a proxy route

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-04 |

## Context

The browser must reach the API. The web app and the API run as two containers.
Three ways exist:

1. The browser calls the API address directly. The API needs CORS rules.
2. The Next config holds a rewrite rule. Next forwards the call.
3. The web app holds a route handler. The handler forwards the call.

We chose the rewrite rule first. The container test found a fault.

Next builds the rewrite table at build time. The build step had no API address, so the
fallback address `http://localhost:8000` went into the image. Inside the web container,
that address points at the web container. The call failed with `ECONNREFUSED`.

## Decision

The web app holds a route handler at `/api/[...path]`.
The handler reads the API address for each request. It forwards the call to the API.

## Consequences

### Good

- The API address comes from the environment at request time. One image runs anywhere.
- The browser and the API share one origin. The API needs no CORS rules.
- The handler passes the response body through. It does not read the body first.
  The answer stream reaches the browser token by token.
- The API port does not need to be open to the browser.

### Bad

- Each call takes one more hop.
- The web app holds a small amount of server code.

### Risk and control

| Risk | Control |
|---|---|
| The handler reads a stream into memory. | The handler passes `upstream.body` straight to the response. |
| A build-time value hides a fault again. | The test calls the API through the proxy inside the containers, not only on the host. |

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| A direct call with CORS | Fewer parts. But the API address must go into the browser bundle at build time, which has the same fault. The API also needs CORS rules. |
| A rewrite with a build argument | It works. But the API address stays fixed in the image. A new address needs a new build. |
