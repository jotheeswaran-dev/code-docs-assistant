FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.6 /uv /usr/local/bin/uv

WORKDIR /srv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/srv/.venv \
    PATH="/srv/.venv/bin:$PATH"

# The lock file installs before the source code, so a code change keeps the cached layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app

# The build downloads the embedding model, so the container needs no network at run time.
ENV EMBEDDING_CACHE=/srv/.models \
    HF_HUB_OFFLINE=1
RUN HF_HUB_OFFLINE=0 python -c \
    "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5', cache_dir='/srv/.models')"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
