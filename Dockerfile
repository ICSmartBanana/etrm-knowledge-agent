# One image for the API and the UI (the command differs per compose service).
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1

WORKDIR /srv
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY prompts ./prompts
COPY data/pii_registry.json ./data/pii_registry.json

# Download the embedding model at build time so containers start without network access to HF.
RUN python -c "from app.embed import FastEmbedEmbedder; FastEmbedEmbedder()"

RUN useradd --create-home --uid 10001 appuser && chown -R appuser /srv
USER appuser
EXPOSE 8000 8501
