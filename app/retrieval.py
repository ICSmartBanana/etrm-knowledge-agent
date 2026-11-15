"""Tenant-filtered vector retrieval.

Two layers of isolation (ADR 0001):
1. The query filters tenant_id IN (tenant, 'consultancy') inside the vector search (pre-filter).
2. Row-level security: the connection runs as etrm_app, and the tenant is set with SET LOCAL
   inside the request's transaction, so it can never carry over on a pooled connection.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from pgvector.psycopg import register_vector
from psycopg import Connection
from psycopg_pool import ConnectionPool

from app.config import RETRIEVAL, app_dsn
from app.embed import Embedder, default_embedder
from app.tenancy import TenantContext


@dataclass(frozen=True)
class RetrievedChunk:
    tenant_id: str
    doc_id: str
    title: str
    heading: str
    data_class: str
    status: str
    effective_date: str
    content: str
    score: float
    kb_version: str


def _configure(conn: Connection) -> None:
    register_vector(conn)


@lru_cache(maxsize=1)
def app_pool() -> ConnectionPool:
    # autocommit: every query runs in an explicit conn.transaction() block, and a connection
    # handed back to the pool is never left inside an open transaction.
    return ConnectionPool(
        app_dsn(),
        min_size=1,
        max_size=4,
        configure=_configure,
        kwargs={"autocommit": True},
        open=True,
    )


SEARCH_SQL = """
SELECT c.tenant_id, c.doc_id, d.title, c.heading, c.data_class, d.status,
       d.effective_date::text, c.content, 1 - (c.embedding <=> %(q)s) AS score, c.kb_version
FROM chunks c
JOIN documents d ON d.tenant_id = c.tenant_id AND d.doc_id = c.doc_id
WHERE c.tenant_id = ANY(%(tenants)s)
ORDER BY c.embedding <=> %(q)s
LIMIT %(k)s
"""


def search(
    conn: Connection, ctx: TenantContext, vector: list[float], k: int
) -> list[RetrievedChunk]:
    """Run the tenant-scoped search on an open etrm_app connection, in its own transaction."""
    import numpy as np

    with conn.transaction():
        conn.execute("SELECT set_config('app.tenant_id', %s, true)", (ctx.tenant_id,))
        rows = conn.execute(
            SEARCH_SQL,
            {
                "q": np.asarray(vector, dtype=np.float32),
                "tenants": list(ctx.visible_tenants),
                "k": k,
            },
        ).fetchall()
    return [RetrievedChunk(*r) for r in rows]


def retrieve(
    ctx: TenantContext,
    query: str,
    k: int = RETRIEVAL.top_k,
    embedder: Embedder | None = None,
) -> list[RetrievedChunk]:
    vector = (embedder or default_embedder()).embed([query])[0]
    with app_pool().connection() as conn:
        return search(conn, ctx, vector, k)
