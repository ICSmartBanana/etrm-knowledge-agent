"""API tests: the tenant comes only from the session, and the AI disclosure is always present.

The model is replaced by a stub, so these tests make no API calls. They need the database.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.agent as agent_mod
from app.api.main import AI_DISCLOSURE, app
from app.llm import LLMResult

pytestmark = pytest.mark.db


class StubLLM:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[dict[str, str]]]] = []

    def answer(self, system: str, messages: list[dict[str, str]]) -> LLMResult:
        self.calls.append((system, messages))
        return LLMResult("stub answer", [], "answered", "stub", 0, 0, 0, "end_turn")


@pytest.fixture
def stub(monkeypatch: pytest.MonkeyPatch) -> StubLLM:
    s = StubLLM()
    monkeypatch.setattr(agent_mod, "default_llm", lambda: s)
    monkeypatch.setattr("app.api.main.record", lambda q, a: "trace-test")
    return s


client = TestClient(app)


def _login(c: str) -> dict[str, str]:
    resp = client.post("/login", json={"client_id": c}).json()
    assert resp["disclosure"] == AI_DISCLOSURE
    return {"Authorization": f"Bearer {resp['token']}"}


def test_chat_requires_login(stub: StubLLM) -> None:
    assert client.post("/chat", json={"question": "hi"}).status_code == 401


def test_cannot_log_in_as_consultancy_or_unknown() -> None:
    for bad in ("consultancy", "clan_d", ""):
        assert client.post("/login", json={"client_id": bad}).status_code == 422


def test_tenant_in_body_is_ignored(stub: StubLLM) -> None:
    body: dict[str, Any] = {"question": "What is the nomination deadline?", "tenant_id": "clan_b"}
    resp = client.post("/chat", json=body, headers=_login("clan_a"))
    assert resp.status_code == 200
    system, messages = stub.calls[-1]
    assert "Clan A" in system and "Clan B" not in system
    assert '<document id="b-' not in messages[-1]["content"]


def test_disclosure_on_every_answer(stub: StubLLM) -> None:
    resp = client.post(
        "/chat", json={"question": "When does the EOD batch start?"}, headers=_login("clan_a")
    )
    assert resp.json()["disclosure"] == AI_DISCLOSURE


def test_contact_lists_never_reach_the_model(stub: StubLLM) -> None:
    client.post(
        "/chat",
        json={"question": "Who are the gas scheduling contacts? contact list"},
        headers=_login("clan_a"),
    )
    _, messages = stub.calls[-1]
    assert 'id="a-013"' not in messages[-1]["content"]


def test_abstains_without_calling_the_model_when_retrieval_is_weak(
    stub: StubLLM, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Cite or abstain (FR3): below the score threshold the agent says it doesn't know and the
    # model is never asked, so it has nothing to confabulate from.
    from dataclasses import replace

    monkeypatch.setattr(agent_mod, "RETRIEVAL", replace(agent_mod.RETRIEVAL, min_score=1.01))
    resp = client.post(
        "/chat", json={"question": "What is the nomination deadline?"}, headers=_login("clan_a")
    ).json()
    assert resp["outcome"] == "no_information"
    assert resp["disclosure"] == AI_DISCLOSURE
    assert stub.calls == []


def test_daily_quota_blocks_after_the_limit_and_is_reported(
    stub: StubLLM, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The hosted demo shares one daily allowance; the UI shows it from /quota.
    from app.api.limits import DailyQuota

    monkeypatch.setattr("app.api.main.DAILY_QUOTA", DailyQuota(1))
    headers = _login("clan_a")
    first = client.post(
        "/chat", json={"question": "When does the EOD batch start?"}, headers=headers
    )
    assert first.status_code == 200 and first.json()["quota"]["remaining"] == 0
    second = client.post("/chat", json={"question": "And on Fridays?"}, headers=headers)
    assert second.status_code == 429 and "resets at 00:00 UTC" in second.json()["detail"]
    assert client.get("/quota").json()["used"] == 1
