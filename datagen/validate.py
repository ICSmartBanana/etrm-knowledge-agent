"""Checks a generated document against its spec and against every other tenant's spec."""

from __future__ import annotations

import re

from datagen.inserts import INJECTION_MARKER
from datagen.spec import DocSpec, TenantSpec

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_RE = re.compile(r"\+\d[\d ]{8,}\d")
TRADER_ID_RE = re.compile(r"\b[A-Z]{2,3}-TRD-\d{4}\b")


def _forbidden_for(tenant: TenantSpec, specs: dict[str, TenantSpec]) -> list[str]:
    """Strings that identify another tenant and must never appear in this tenant's docs."""
    out: list[str] = []
    for other in specs.values():
        if other.tenant_id == tenant.tenant_id:
            continue
        out += [other.company_name, other.canary, *(p.value for p in other.pii.values())]
        if other.platform.startswith("none"):
            continue
        out.append(other.platform)
    return out


def check_doc(
    body: str,
    doc: DocSpec,
    tenant: TenantSpec,
    specs: dict[str, TenantSpec],
    *,
    derived: bool = False,
) -> list[str]:
    """Return a list of problems; an empty list means the document is valid.

    Derived (near-duplicate) docs may drop content, so their PII is allowed but not required.
    """
    problems: list[str] = []
    if "[[" in body or "]]" in body:
        problems.append("leftover [[ ]] brackets")
    problems += [f"missing key value: {k!r}" for k in doc.keys if k not in body]

    allowed_pii = {tenant.pii[p].value for p in doc.pii}
    if not derived:
        problems += [f"missing PII value: {v!r}" for v in sorted(allowed_pii) if v not in body]
    for rx in (EMAIL_RE, PHONE_RE, TRADER_ID_RE):
        for m in rx.findall(body):
            if m.strip() not in allowed_pii:
                problems.append(f"unexpected PII-like string: {m!r}")

    problems += [
        f"mentions another tenant: {s!r}" for s in _forbidden_for(tenant, specs) if s in body
    ]
    if (tenant.canary in body) != doc.canary:
        problems.append("canary present/absent mismatch")
    if (INJECTION_MARKER in body) != doc.injection:
        problems.append("injection present/absent mismatch")
    return problems
