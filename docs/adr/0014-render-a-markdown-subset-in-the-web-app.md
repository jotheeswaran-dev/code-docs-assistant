# ADR 0014: Render a markdown subset in the web app

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-04 |

## Context

The model writes the answer in markdown. The page must show headings, lists, bold text,
inline code, and fenced code.

Two needs make a general library awkward:

1. A citation such as `[c1]` must become a button inside the prose. A click opens the
   source. A library treats that text as plain text.
2. The text arrives as a stream. A fenced code block is open for a moment, and a parser
   that needs a complete document fails or flickers.

The code inside a source block also needs colour, and it needs the real line numbers of
the file so that a reader can find the lines.

## Decision

We write the markdown reader ourselves. It covers the subset that the model uses:
heading, paragraph, list, bold, inline code, and fenced code.
It treats `[c1]` as a button, and a half-written fence renders as code.

We use `highlight.js` for colour, with twelve languages registered, not the whole set.
The colours live in our own stylesheet, so one palette serves the light view and the
dark view.

Line numbers sit in their own column beside the code. The column holds its place when
the code scrolls sideways.

## What we measured

| Measure | Result |
|---|---|
| The reader | About 130 lines, with no new dependency |
| `highlight.js`, 12 languages | The page grows from 104 kB to 130 kB of first-load code |
| Languages checked | Ruby, Python, Bash, and YAML each return the token classes that our stylesheet sets |

## Consequences

### Good

- A citation is a real button. A click opens the exact source.
- A stream never breaks the page, because the reader accepts a part of a document.
- The colours match the rest of the page in both views.
- The bundle holds twelve languages, not two hundred.

### Bad

- The reader covers a subset. A table or an image in an answer would not render.
- We own that code, so a new markdown need means a change here.

### Risk and control

| Risk | Control |
|---|---|
| The model writes markdown that we do not cover. | The rules ask for a short answer and a list. Any text that we do not read still renders as a paragraph, so nothing is lost. |
| Highlighted code is HTML, so it could carry a script. | `highlight.js` escapes the code that it reads, and we escape the text when no language matches. |
| A new language has no colour. | The file name picks the language. A file with no match renders as plain text, which stays readable. |

## Options that we rejected

| Option | Why we rejected it |
|---|---|
| A markdown library such as react-markdown | Well tested, and it covers everything. But a citation button inside the text needs a custom node for every text run, and a partial document during a stream is the normal case here, not an edge case. |
| No colour at all | Fewer parts, and the line numbers carry most of the value. But a tool about code that shows plain grey code reads as unfinished. |
| The full `highlight.js` bundle | One import. But it holds about two hundred languages, and a repository needs a few. |
