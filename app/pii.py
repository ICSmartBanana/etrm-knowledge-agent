"""PII detection and masking, used at ingestion, in the output guard and before tracing.

POC approach: regexes for emails, phone numbers and trader IDs, plus exact matches against the
seeded registry (data/pii_registry.json), which is the only way names are caught here. A real
deployment would need an NER-based detector for names; that is a known limitation.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache

from app.config import REPO_ROOT

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_RE = re.compile(r"\+\d[\d ()-]{7,}\d")
TRADER_ID_RE = re.compile(r"\b[A-Z]{2,3}-TRD-\d{4}\b")

_PATTERNS = (("EMAIL", EMAIL_RE), ("PHONE", PHONE_RE), ("TRADER_ID", TRADER_ID_RE))


@lru_cache(maxsize=1)
def registry_values() -> dict[str, str]:
    """Seeded PII value -> kind, across all tenants."""
    data = json.loads((REPO_ROOT / "data" / "pii_registry.json").read_text(encoding="utf-8"))
    return {item["value"]: item["kind"].upper() for items in data.values() for item in items}


def find_pii(text: str) -> list[str]:
    """Every PII string found in text (registry matches and pattern matches)."""
    found = [v for v in registry_values() if v in text]
    for _, rx in _PATTERNS:
        found += rx.findall(text)
    return sorted(set(found))


def mask(text: str) -> str:
    # Longest registry values first, so a full email is masked before a name inside it.
    for value, kind in sorted(registry_values().items(), key=lambda kv: -len(kv[0])):
        text = text.replace(value, f"[REDACTED_{kind}]")
    for kind, rx in _PATTERNS:
        text = rx.sub(f"[REDACTED_{kind}]", text)
    return text
