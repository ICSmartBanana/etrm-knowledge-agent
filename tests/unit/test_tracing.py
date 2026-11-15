"""Tracing: records carry the FR6 fields, are PII-masked, and Langfuse is optional."""

from __future__ import annotations

import pytest

import app.tracing as tracing
from app.agent import AgentAnswer, Citation
from app.pii import find_pii
from app.retrieval import RetrievedChunk

ANS = AgentAnswer(
    answer="Ask Harriet Okonjo on +44 20 7946 0412.",
    outcome="answered",
    citations=[Citation("a-002", "Gas nomination")],
    tenant_id="clan_a",
    prompt_version="v1",
    kb_version="kb-test",
    model="claude-sonnet-5-5",
    retrieved=[
        RetrievedChunk(
            "clan_a",
            "a-002",
            "T",
            "H",
            "public",
            "current",
            "2025-10-01",
            "SECRET DOCUMENT TEXT",
            0.81,
            "kb-test",
        )
    ],
    guard_flags=["pii_masked"],
    input_tokens=1_000_000,
    output_tokens=100_000,
)


def test_record_has_fr6_fields_and_no_pii_or_doc_text() -> None:
    rec = tracing.trace_record("Email harriet.okonjo@aldermoor-energy.example please", ANS)
    for field in ("client_id", "retrieved", "model", "prompt_version", "kb_version"):
        assert rec[field]
    assert rec["retrieved"][0]["score"] == 0.81
    blob = str(rec)
    assert find_pii(blob) == []
    assert "SECRET DOCUMENT TEXT" not in blob


def test_cost_uses_pinned_prices() -> None:
    assert tracing.cost_usd(ANS) == pytest.approx(2.0 + 1.0)


def test_langfuse_disabled_without_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    tracing.langfuse_client.cache_clear()
    try:
        assert tracing.export_langfuse(tracing.trace_record("q", ANS)) is None
    finally:
        tracing.langfuse_client.cache_clear()


def test_langfuse_mask_hook_masks_nested_strings() -> None:
    out = tracing._mask_any(data={"a": ["Call +44 20 7946 0412"], "b": 3})
    assert find_pii(str(out)) == [] and out["b"] == 3
