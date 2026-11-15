"""Offline checks that the frozen synthetic corpus matches its specs (no API calls)."""

from __future__ import annotations

import json

import pytest

from datagen.generate import doc_path, split_doc
from datagen.spec import REPO_ROOT, DocSpec, TenantSpec, derived_doc, load_all
from datagen.validate import check_doc

SPECS = load_all()


def _all_docs() -> list[tuple[TenantSpec, DocSpec, bool]]:
    out = []
    for t in SPECS.values():
        out += [(t, d, False) for d in t.docs]
        out += [(t, derived_doc(t, d), True) for d in t.derived]
    return out


ALL_DOCS = _all_docs()


@pytest.mark.parametrize(("tenant", "doc", "derived"), ALL_DOCS, ids=[d.id for _, d, _ in ALL_DOCS])
def test_document_matches_spec(tenant: TenantSpec, doc: DocSpec, derived: bool) -> None:
    path = doc_path(tenant.tenant_id, doc.id)
    assert path.exists(), f"{path} not generated"
    meta, body = split_doc(path.read_text(encoding="utf-8"))
    assert meta["tenant_id"] == tenant.tenant_id
    assert meta["doc_id"] == doc.id
    assert meta["data_class"] == doc.data_class
    assert meta["status"] == doc.status
    assert check_doc(body, doc, tenant, SPECS, derived=derived) == []


def test_no_unexpected_files() -> None:
    expected = {doc_path(t.tenant_id, d.id) for t, d, _ in ALL_DOCS}
    actual = set((REPO_ROOT / "data" / "synthetic").rglob("*.md"))
    assert actual == expected


@pytest.mark.parametrize("tenant", SPECS.values(), ids=list(SPECS))
def test_exactly_one_canary_doc_per_tenant(tenant: TenantSpec) -> None:
    assert sum(d.canary for d in tenant.docs) == 1


def test_registries_match_specs() -> None:
    pii = json.loads((REPO_ROOT / "data" / "pii_registry.json").read_text(encoding="utf-8"))
    canaries = json.loads((REPO_ROOT / "data" / "canaries.json").read_text(encoding="utf-8"))
    for t in SPECS.values():
        assert {p["value"] for p in pii[t.tenant_id]} == {p.value for p in t.pii.values()}
        assert canaries[t.tenant_id] == t.canary


def test_messy_data_present() -> None:
    clients = [SPECS[t] for t in ("clan_a", "clan_b", "clan_c")]
    for t in clients:
        assert any(d.status == "superseded" for d in t.docs), t.tenant_id
        assert any(d.contradicts for d in t.docs), t.tenant_id
        assert t.derived, t.tenant_id
        assert any(d.data_class == "inference_only" for d in t.docs), t.tenant_id
    assert sum(d.injection for t in clients for d in t.docs) >= 1
