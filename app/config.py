"""Runtime settings, read from the environment (.env in local dev)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

# Pinned versions. Change them only with an eval run and a CHANGELOG entry.
ANSWER_MODEL = "claude-sonnet-5-5"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
PROMPT_VERSION = "v1"
# USD per million (input, output) tokens for ANSWER_MODEL, for the cost-per-query metric.
# Check anthropic.com/pricing when changing the model.
ANSWER_PRICE_PER_MTOK = (2.00, 10.00)


@dataclass(frozen=True)
class RetrievalConfig:
    top_k: int = 6
    # Below this cosine similarity for the best chunk, the agent says it doesn't know.
    min_score: float = 0.60
    chunk_max_chars: int = 1200


RETRIEVAL = RetrievalConfig()


def _dsn(user: str, password_var: str) -> str:
    host = os.environ.get("ETRM_DB_HOST", "127.0.0.1")
    port = os.environ.get("ETRM_DB_PORT", "5433")
    password = os.environ[password_var]
    return f"host={host} port={port} dbname=etrm user={user} password={password}"


def app_dsn() -> str:
    """The API's connection: role etrm_app, subject to row-level security."""
    return _dsn("etrm_app", "ETRM_APP_PASSWORD")


def ingest_dsn() -> str:
    """The ingest CLI's connection: role etrm_ingest (BYPASSRLS). Never used by the API."""
    return _dsn("etrm_ingest", "ETRM_INGEST_PASSWORD")


def admin_dsn() -> str:
    """The superuser (etrm_owner). Tests use it only to SET ROLE etrm_schema, the table owner."""
    return _dsn("etrm_owner", "ETRM_OWNER_PASSWORD")


FASTEMBED_CACHE = REPO_ROOT / ".cache" / "fastembed"
