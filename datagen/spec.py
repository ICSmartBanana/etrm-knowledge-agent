"""Load and model the YAML knowledge-base specs in data/spec/."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_DIR = REPO_ROOT / "data" / "spec"
CORPUS_DIR = REPO_ROOT / "data" / "synthetic"
TENANTS = ("clan_a", "clan_b", "clan_c", "consultancy")

_KEY_RE = re.compile(r"\[\[(.+?)\]\]")


def key_values(fact: str) -> list[str]:
    """Return the [[bracketed]] key values in a fact."""
    return _KEY_RE.findall(fact)


def strip_brackets(fact: str) -> str:
    return _KEY_RE.sub(r"\1", fact)


@dataclass(frozen=True)
class PiiItem:
    id: str
    kind: str
    value: str
    role: str


@dataclass(frozen=True)
class DocSpec:
    id: str
    title: str
    doc_type: str
    data_class: str
    topic: str
    facts: list[str]
    overlap: str | None = None
    version: int = 1
    status: str = "current"
    effective_date: str = "2025-10-01"
    supersedes: str | None = None
    contradicts: str | None = None
    pii: list[str] = field(default_factory=list)
    canary: bool = False
    injection: bool = False

    @property
    def keys(self) -> list[str]:
        return [k for f in self.facts for k in key_values(f)]


@dataclass(frozen=True)
class DerivedSpec:
    id: str
    kind: str
    source: str


@dataclass(frozen=True)
class TenantSpec:
    tenant_id: str
    company_name: str
    profile: str
    platform: str
    canary: str
    pii: dict[str, PiiItem]
    docs: list[DocSpec]
    derived: list[DerivedSpec]

    def doc(self, doc_id: str) -> DocSpec:
        return next(d for d in self.docs if d.id == doc_id)


def derived_doc(tenant: TenantSpec, d: DerivedSpec) -> DocSpec:
    """Spec for a code-built near-duplicate: same metadata and allowed PII as its source."""
    src = tenant.doc(d.source)
    return DocSpec(
        id=d.id,
        title=f"{src.title} (wiki copy)",
        doc_type=src.doc_type,
        data_class=src.data_class,
        topic=src.topic,
        facts=[],
        overlap=src.overlap,
        effective_date=src.effective_date,
        pii=src.pii,
    )


def _doc(raw: dict[str, Any]) -> DocSpec:
    fields: dict[str, Any] = dict(raw)
    if "effective_date" in fields:
        fields["effective_date"] = str(fields["effective_date"])
    return DocSpec(**fields)


def load_tenant(tenant_id: str) -> TenantSpec:
    raw = yaml.safe_load((SPEC_DIR / f"{tenant_id}.yaml").read_text(encoding="utf-8"))
    company = raw["company"]
    return TenantSpec(
        tenant_id=raw["tenant_id"],
        company_name=company["name"],
        profile=company["profile"].strip(),
        platform=company["platform"],
        canary=raw["canary"],
        pii={p["id"]: PiiItem(**p) for p in raw.get("pii") or []},
        docs=[_doc(d) for d in raw["docs"]],
        derived=[DerivedSpec(**d) for d in raw.get("derived") or []],
    )


def load_all() -> dict[str, TenantSpec]:
    return {t: load_tenant(t) for t in TENANTS}
