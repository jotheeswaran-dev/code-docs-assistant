# ADR 0002: Use Python with FastAPI, and Next.js

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-04 |

## Context

We must pick a language for the server and a framework for the web app.
The server must stream an answer token by token.
The web app must look clear and must work well.

## Decision

The server uses Python 3.12 with FastAPI.
The web app uses Next.js.

We pin Python to 3.12. We tested every library on this version.

## Consequences

### Good

- FastAPI streams a response with Server-Sent Events. The code stays short.
- Python has the parser library and the embedding library that we need.
- Next.js gives a good user interface with little code.
- Two services make two small containers.

### Bad

- The project uses two languages. A reader must know both.
- Two package managers. Two lock files.

### Risk and control

| Risk | Control |
|---|---|
| A library has no release for a new Python version. | We pin Python to 3.12 in `.python-version` and in the container. |

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| TypeScript for the server and the web app | One language only. But the parser library and the embedding library are better in Python. |
| Python with a server-rendered page | Fewer parts. But the trace view and the code view need a rich client. |
