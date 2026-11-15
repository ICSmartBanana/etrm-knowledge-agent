"""Unit tests for the corpus validator itself."""

from __future__ import annotations

from datagen.spec import load_all
from datagen.validate import check_doc

SPECS = load_all()
A = SPECS["clan_a"]
DOC = A.doc("a-003")  # public, no PII, keys only
GOOD = "# T\n\n" + " ".join(DOC.keys) + "\n"


def test_valid_document_passes() -> None:
    assert check_doc(GOOD, DOC, A, SPECS) == []


def test_missing_key_value_is_reported() -> None:
    problems = check_doc(GOOD.replace(DOC.keys[0], ""), DOC, A, SPECS)
    assert any("missing key value" in p for p in problems)


def test_other_tenant_name_is_reported() -> None:
    problems = check_doc(GOOD + "Brightwater Refined Products\n", DOC, A, SPECS)
    assert any("another tenant" in p for p in problems)


def test_other_tenant_canary_is_reported() -> None:
    problems = check_doc(GOOD + SPECS["clan_c"].canary, DOC, A, SPECS)
    assert any("another tenant" in p for p in problems)


def test_invented_email_and_phone_are_reported() -> None:
    body = GOOD + "Contact jo@example.com or +44 20 7946 0999.\n"
    problems = check_doc(body, DOC, A, SPECS)
    assert sum("unexpected PII-like" in p for p in problems) == 2
