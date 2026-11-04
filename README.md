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

## Try it on another repository

The system holds one index for each repository. Build an index, then serve it.

| Action | Command |
|---|---|
| Index a local folder | `make ingest REPO=~/code/my-project DB=data/my-project.db` |
| Index from GitHub | `make ingest REPO=https://github.com/psf/requests DB=data/requests.db` |
| List the indexes | `make indexes` |
| Serve one index | `make api DB=data/requests.db` |
| Serve one index in the container | `STORE_PATH=data/requests.db docker compose up` |

`DB` has a default of `data/store.db`. Leave it out to use that one index.

A Git URL clones with `--depth 1` into a temporary folder. The folder is removed once
the index is written. Nothing from the repository enters this repository.

The ingest step embeds about 12 chunks each second. A repository of 350 files takes
about three minutes. The index is a file, so you build it one time.

## Work on it

You need `uv`, Node 24, and Python 3.12.

| Command | Action |
|---|---|
| `make setup` | Install the dependencies for both services |
| `make api` | Run the API on port 8000 |
| `make web` | Run the web app on port 3000 |
| `make test` | Run the tests |
| `make ingest REPO=<path>` | Index a repository |
| `make eval` | Measure retrieval. Free, no model call |
| `make eval-answers` | Also ask the model and grade each answer. About $0.70 |
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
| 5 | Web app | Done |
| 6 | Evals and the final document | Done |

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
| [docs/evidence.md](docs/evidence.md) | Every number that we measured. |
| [docs/adr/](docs/adr/) | One Architecture Decision Record for each important decision. |

## Language of the documents

We write the documents in Simplified Technical English (ASD-STE100).
Sentences are short. The voice is active. One word has one meaning.

## Quality

`make eval` asks 15 fixed questions about `psf/requests`. Twelve have an answer in the
repository. Three do not, and the system must refuse those.

| Search | recall@1 | recall@3 | recall@5 | recall@8 |
|---|---|---|---|---|
| Word only | 0.67 | 0.83 | 0.92 | 0.92 |
| Vector only | 0.58 | 0.92 | 0.92 | 0.92 |
| Joined with RRF | 0.67 | **1.00** | **1.00** | **1.00** |

| Answers | Result |
|---|---|
| Faithful to the sources | 12 of 12 |
| Every claim carries a citation | 8 of 12 |
| Refused when it must | 3 of 3 |

[docs/evidence.md](docs/evidence.md) holds every other number.

## Sections that come later

- Screenshots and a short video
- The plan to move the system to a cloud provider
- How we used AI tools, and the rules that we follow
