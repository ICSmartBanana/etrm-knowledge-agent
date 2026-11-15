"""Unit tests for PII masking and the output guard (no database, no API calls)."""

from __future__ import annotations

from app.guard import WITHHELD, apply_guard
from app.pii import find_pii, mask
from app.retrieval import RetrievedChunk
from app.tenancy import TenantContext, UnknownTenantError


def _chunk(doc_id: str, data_class: str, content: str) -> RetrievedChunk:
    return RetrievedChunk(
        "clan_a", doc_id, "T", "H", data_class, "current", "2025-10-01", content, 0.9, "kb-test"
    )


INTERNAL = _chunk(
    "a-011",
    "inference_only",
    "Credit risk proposes reducing its unsecured limit to GBP 2 million for this counterparty.",
)
PUBLIC = _chunk("a-002", "public", "Nominations are due by 13:00 UK time on D-1.")


def test_mask_registry_and_patterns() -> None:
    text = "Call Harriet Okonjo on +44 20 7946 0412 or x.y@z.example, trader AE-TRD-0412."
    masked = mask(text)
    assert find_pii(masked) == []
    assert "[REDACTED_NAME]" in masked and "[REDACTED_PHONE]" in masked


def test_guard_withholds_verbatim_inference_only_text() -> None:
    answer = "Credit risk proposes reducing its unsecured limit to GBP 2 million soon."
    out = apply_guard(answer, ["a-011"], [INTERNAL, PUBLIC], "system")
    assert out.answer == WITHHELD and "inference_only_overlap" in out.flags


def test_guard_withholds_system_prompt_echo() -> None:
    system = "You are the ETRM knowledge assistant for Clan A and you answer only from documents."
    out = apply_guard(
        "Sure: you are the ETRM knowledge assistant for Clan A and you answer only",
        [],
        [PUBLIC],
        system,
    )
    assert out.answer == WITHHELD


def test_guard_masks_pii_and_drops_bad_citations() -> None:
    out = apply_guard(
        "Ask Harriet Okonjo. Deadline 13:00.",
        ["a-002", "a-011", "b-004"],
        [INTERNAL, PUBLIC],
        "system",
    )
    assert "Harriet" not in out.answer
    assert out.cited_doc_ids == ["a-002"]
    assert {"pii_masked", "citations_dropped"} <= set(out.flags)


def test_clean_answer_passes_unchanged() -> None:
    out = apply_guard("Nominations are due by 13:00 UK time on D-1.", ["a-002"], [PUBLIC], "system")
    assert out.flags == [] and out.cited_doc_ids == ["a-002"]


def test_tenant_context_has_no_text_constructor() -> None:
    assert not any(n.startswith("from_") for n in dir(TenantContext))
    try:
        TenantContext("consultancy")
    except UnknownTenantError:
        pass
    else:
        raise AssertionError("consultancy must not be a login tenant")
