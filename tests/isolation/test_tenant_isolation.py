"""Proves cross-tenant reads are impossible at the data layer (FR2). These are hard gates.

Each tenant's corpus holds a unique canary string (data/canaries.json). Every other tenant must
be unable to read it, through the retrieval function and through raw SQL as etrm_app or even as
the table owner.
"""

from __future__ import annotations

import json
import threading

import psycopg
import pytest
from pgvector.psycopg import register_vector

from app.config import REPO_ROOT, admin_dsn, app_dsn
from app.retrieval import app_pool, retrieve, search
from app.tenancy import CLIENT_TENANTS, TenantContext, UnknownTenantError

pytestmark = pytest.mark.db

CANARIES: dict[str, str] = json.loads(
    (REPO_ROOT / "data" / "canaries.json").read_text(encoding="utf-8")
)
PAIRS = [(a, b) for a in CLIENT_TENANTS for b in CLIENT_TENANTS if a != b]


def _visible_rows(
    dsn: str, tenant: str | None, sql_filter: str = "", role: str | None = None
) -> list[tuple[str, str]]:
    with psycopg.connect(dsn) as conn, conn.transaction():
        if role is not None:
            conn.execute(f"SET LOCAL ROLE {role}")
        if tenant is not None:
            conn.execute("SELECT set_config('app.tenant_id', %s, true)", (tenant,))
        return conn.execute(f"SELECT tenant_id, content FROM chunks {sql_filter}").fetchall()  # noqa: S608


@pytest.mark.parametrize(("asker", "owner"), PAIRS)
def test_canary_not_retrievable_by_other_tenant(asker: str, owner: str) -> None:
    hits = retrieve(TenantContext(asker), f"Internal document reference {CANARIES[owner]}", k=50)
    assert all(CANARIES[owner] not in h.content for h in hits)
    assert {h.tenant_id for h in hits} <= {asker, "consultancy"}


@pytest.mark.parametrize("tenant", CLIENT_TENANTS)
def test_own_canary_is_retrievable(tenant: str) -> None:
    """The positive control: the canary test above is meaningless if retrieval can't find it."""
    hits = retrieve(TenantContext(tenant), f"Internal document reference {CANARIES[tenant]}", k=300)
    assert any(CANARIES[tenant] in h.content for h in hits)


@pytest.mark.parametrize("tenant", CLIENT_TENANTS)
def test_rls_hides_other_tenants_from_app_role_even_without_where(tenant: str) -> None:
    rows = _visible_rows(app_dsn(), tenant)
    assert rows, "expected own + consultancy rows"
    assert {t for t, _ in rows} == {tenant, "consultancy"}


def test_rls_returns_nothing_when_tenant_not_set() -> None:
    assert _visible_rows(app_dsn(), None) == []


@pytest.mark.parametrize("tenant", CLIENT_TENANTS)
def test_rls_binds_the_table_owner_too(tenant: str) -> None:
    """FORCE ROW LEVEL SECURITY: the table owner has no policy, so it sees nothing."""
    assert _visible_rows(admin_dsn(), tenant, role="etrm_schema") == []


def test_app_and_owner_roles_cannot_bypass_rls() -> None:
    with psycopg.connect(app_dsn()) as conn:
        rows = conn.execute(
            "SELECT rolname, rolsuper, rolbypassrls FROM pg_roles"
            " WHERE rolname IN ('etrm_app', 'etrm_schema')"
        ).fetchall()
        owners = conn.execute(
            "SELECT DISTINCT tableowner FROM pg_tables WHERE tablename IN ('chunks', 'documents')"
        ).fetchall()
    assert sorted(rows) == [("etrm_app", False, False), ("etrm_schema", False, False)]
    assert owners == [("etrm_schema",)]


def test_app_role_cannot_write() -> None:
    with psycopg.connect(app_dsn()) as conn, pytest.raises(psycopg.errors.InsufficientPrivilege):
        conn.execute("DELETE FROM chunks")


def test_tenant_setting_does_not_leak_across_pooled_connections() -> None:
    """SET LOCAL ends with the transaction, so a pooled connection carries no tenant forward."""
    with app_pool().connection() as conn:
        search(conn, TenantContext("clan_a"), [0.0] * 384, k=1)
        with conn.transaction():
            setting = conn.execute("SELECT current_setting('app.tenant_id', true)").fetchone()
        assert setting is not None and setting[0] in (None, "")


def test_interleaved_tenants_on_shared_pool_never_mix() -> None:
    errors: list[str] = []

    def worker(tenant: str) -> None:
        for _ in range(20):
            with app_pool().connection() as conn:
                register_vector(conn)
                hits = search(conn, TenantContext(tenant), [0.01] * 384, k=20)
            bad = {h.tenant_id for h in hits} - {tenant, "consultancy"}
            if bad:
                errors.append(f"{tenant} saw {bad}")

    threads = [threading.Thread(target=worker, args=(t,)) for t in CLIENT_TENANTS * 2]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []


@pytest.mark.parametrize("bad", ["consultancy", "", "clan_a' OR '1'='1", "CLAN_A", "clan_d"])
def test_tenant_context_rejects_anything_but_a_client_tenant(bad: str) -> None:
    with pytest.raises(UnknownTenantError):
        TenantContext(bad)


def test_ingested_chunks_contain_no_seeded_pii() -> None:
    from app.pii import find_pii

    rows: list[tuple[str, str]] = []
    for tenant in CLIENT_TENANTS:
        rows += _visible_rows(app_dsn(), tenant)
    leaks = [(t, p) for t, content in rows for p in find_pii(content)]
    assert leaks == []
