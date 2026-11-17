# Hugging Face Space image: Postgres + pgvector, the ingested synthetic corpus and the API in
# one container. Built from the repo root by .github/workflows/deploy.yml, which copies this
# file to the Space as its Dockerfile. Spaces run the container as uid 1000 and route to 7860.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql postgresql-17-pgvector \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
ENV PATH="/usr/lib/postgresql/17/bin:/opt/venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PYTHONUNBUFFERED=1

WORKDIR /srv
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY ingest ./ingest
COPY prompts ./prompts
COPY data ./data
COPY db ./db
COPY deploy/hf-space/start.sh ./start.sh
RUN python -c "from app.embed import FastEmbedEmbedder; FastEmbedEmbedder()"

RUN useradd --create-home --uid 1000 user && chown -R user /srv && chmod +x /srv/start.sh
USER user
EXPOSE 7860
CMD ["/srv/start.sh"]
