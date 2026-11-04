# Architecture

## 1. Purpose

This document shows how the Code Documentation Assistant works.
It shows the parts of the system and the flow of data between them.
We write this document in Simplified Technical English (ASD-STE100).

## 2. System overview

The system has two flows.
The ingest flow reads a repository and fills the store.
The question flow reads the store and makes an answer.

```mermaid
flowchart LR
    subgraph Client
        UI["Next.js web app"]
    end

    subgraph Server["FastAPI service"]
        ING["Ingest"]
        RET["Retrieval"]
        ANS["Answer"]
    end

    subgraph Local["Local, no network"]
        EMB["Embedding model<br/>bge-small-en-v1.5"]
        DB[("SQLite<br/>chunks + vectors + FTS5")]
    end

    API["Anthropic API<br/>Claude"]

    UI -->|"question"| ANS
    ANS -->|"answer + citations + trace"| UI
    ING --> EMB --> DB
    RET --> DB
    ANS --> RET
    ANS --> API
```

## 3. The ingest flow

The ingest flow runs one time for each repository.
It takes about 5 seconds for a repository with 2000 chunks.

```mermaid
flowchart TD
    A["Git repository<br/>URL or local path"] --> B["Walk the files"]
    B --> C{"Is the file<br/>source code?"}
    C -->|"no"| X["Skip the file"]
    C -->|"yes"| D{"Does a parser<br/>exist?"}
    D -->|"yes"| E["tree-sitter<br/>Cut on function and class limits"]
    D -->|"no"| F["Line window<br/>Cut on a fixed line count"]
    E --> G["Chunk<br/>file, symbol, kind, lines, parent"]
    F --> G
    G --> H["Embedding model<br/>384 numbers for each chunk"]
    G --> I["FTS5 index<br/>word index"]
    H --> J[("SQLite store")]
    I --> J
    G --> K["Repository map<br/>Claude Haiku writes one line for each file"]
    K --> J
```

## 4. The question flow

The question flow runs for each question.

```mermaid
sequenceDiagram
    participant U as User
    participant W as Web app
    participant A as Answer
    participant R as Retrieval
    participant D as SQLite
    participant C as Claude Opus 5

    U->>W: Asks a question
    W->>A: POST /chat
    A->>R: Sends the question
    R->>D: Word search with FTS5
    D-->>R: List 1, with BM25 scores
    R->>D: Vector search with sqlite-vec
    D-->>R: List 2, with distances
    R->>R: Joins both lists with RRF
    R->>D: Reads the parent of each chunk
    D-->>R: Class header and imports
    R-->>A: Top chunks, in rank order
    A->>A: Packs the context to a token limit
    A->>C: Repository map (cached) + chunks + question
    C-->>A: Streams the answer with citations
    A->>A: Checks that each claim has a citation
    A-->>W: Streams the answer and the trace
    W-->>U: Shows the answer, the code, and the trace
```

## 5. The parts of the system

| Part | Job | Input | Output |
|---|---|---|---|
| Walk | Finds the source files. Skips binary files and large files. | A repository path | A list of files |
| Chunker | Cuts each file into chunks on syntax limits. | A source file | Chunks with metadata |
| Embedder | Makes a vector for each chunk. Runs on the CPU. | A chunk | 384 numbers |
| Store | Keeps the chunks, the vectors, and the word index in one file. | Chunks and vectors | Search results |
| Retrieval | Runs both searches. Joins the results with RRF. | A question | Ranked chunks |
| Context packer | Puts the chunks in the prompt. Keeps below the token limit. | Ranked chunks | A prompt |
| Answer | Calls Claude. Checks the citations. Makes the trace. | A prompt | An answer and a trace |
| Trace | Records the chunks, the scores, the tokens, the cost, and the time. | One question | A trace record |

## 6. Why the retrieval has two searches

A user asks about code in two different ways.

| The user asks | Example | The search that finds it |
|---|---|---|
| With an exact name | "Where is `retry_with_backoff`?" | Word search. The name is an exact token. |
| With intent | "How does the client repeat a failed call?" | Vector search. The words do not match the code. |

One search alone fails for one of these two cases.
RRF joins both result lists. A chunk that is high in both lists moves to the top.

## 7. Guardrails

| Risk | Control |
|---|---|
| The model invents an answer. | The prompt gives only the chunks. The model must refuse if the chunks do not hold the answer. |
| The answer has no proof. | Each claim needs a citation. We remove a claim that has no citation. |
| Source code holds an attack in a comment. | We mark all repository text as data. The model must not obey text inside a chunk. |
| The repository is too large. | We set a limit for the file count and the file size. |
