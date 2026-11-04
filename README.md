# Code Documentation Assistant

Ask questions about a code repository. Get an answer with a link to the exact file and line.

The system reads a Git repository. It cuts each source file into chunks on function and
class limits. It finds the related chunks for a question. It sends those chunks to Claude.
Every sentence in the answer points back to the code that proves it.

## Run it

You need Docker. The answer step also needs an Anthropic API key.

1. Copy the example file. Run `cp .env.example .env`.
2. Put your key in `.env`.
3. Index a repository. Run `make ingest REPO=<path or git url>`.
4. Run `make up`.
5. Open `http://localhost:3000`.

The page shows the service status. It states if the key is set, and which repository
the index holds.

The ingest step runs on the host and writes `data/store.db`. The container reads the
same file. A repository of 354 files takes about three minutes, and almost all of that
time is the embedding step.

## Work on it

You need `uv`, Node 24, and Python 3.12.

| Command | Action |
|---|---|
| `make setup` | Install the dependencies for both services |
| `make api` | Run the API on port 8000 |
| `make web` | Run the web app on port 3000 |
| `make test` | Run the tests |
| `make ingest REPO=<path>` | Index a repository |
| `make lint` | Check the style and the types |
| `make help` | Show every command |

## Status

This repository is in progress. The table shows each step.

| Step | Name | State |
|---|---|---|
| 0 | Decisions and architecture | Done |
| 1 | Skeleton and container setup | Done |
| 2 | Ingest and chunk | Done |
| 3 | Index and retrieval | Done |
| 4 | Answer and guardrails | Done |
| 5 | Web app | Next |
| 6 | Evals and final document | Not started |

## Layout

| Path | Content |
|---|---|
| `api/` | The FastAPI service. Ingest, retrieval, and answer. |
| `web/` | The Next.js web app. |
| `docs/` | The decisions, the architecture, and the records. |

## Documents

| Document | Content |
|---|---|
| [docs/decisions.md](docs/decisions.md) | Every decision, the reason, and the facts that we measured. |
| [docs/architecture.md](docs/architecture.md) | The parts of the system and the flow diagrams. |
| [docs/adr/](docs/adr/) | One Architecture Decision Record for each important decision. |

## Language of the documents

We write the documents in Simplified Technical English (ASD-STE100).
Sentences are short. The voice is active. One word has one meaning.

## Sections that come later

- Screenshots
- The approach to RAG, and the quality numbers from the eval run
- The plan to move the system to a cloud provider
- How we used AI tools, and the rules that we follow
