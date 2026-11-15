"""Shared fixtures. Tests marked `db` need the local Postgres (docker compose up -d db) and an
ingested corpus (uv run python -m ingest.cli); they are skipped when the database is down."""

from __future__ import annotations

import psycopg
import pytest

from app.config import app_dsn


def _db_available() -> bool:
    try:
        with psycopg.connect(app_dsn(), connect_timeout=2):
            return True
    except Exception:
        return False


DB_UP = _db_available()


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    skip = pytest.mark.skip(reason="Postgres not running (docker compose up -d db)")
    for item in items:
        if "db" in item.keywords and not DB_UP:
            item.add_marker(skip)
