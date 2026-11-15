"""FastAPI service.

Simulated login (FR1): POST /login with a client id returns a session token. Every /chat call
must carry that token; the tenant comes only from the session, never from the request body.

    uv run uvicorn app.api.main:app --port 8000
"""

from __future__ import annotations

import secrets
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.agent import answer_question
from app.tenancy import CLIENT_TENANTS, DISPLAY_NAMES, TenantContext
from app.tracing import record

AI_DISCLOSURE = (
    "You are chatting with an AI assistant. Answers are generated from your organisation's "
    "documents and can be wrong; check important details before acting on them."
)

app = FastAPI(title="ETRM knowledge agent (POC)")
_sessions: dict[str, str] = {}  # token -> tenant_id (in memory; POC only)


class LoginRequest(BaseModel):
    client_id: Literal["clan_a", "clan_b", "clan_c"]


class LoginResponse(BaseModel):
    token: str
    client_name: str
    disclosure: str


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=8000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    history: list[Turn] = Field(default_factory=list, max_length=20)


class CitationOut(BaseModel):
    doc_id: str
    title: str


class ChatResponse(BaseModel):
    answer: str
    outcome: str
    citations: list[CitationOut]
    disclosure: str
    trace_id: str
    prompt_version: str
    kb_version: str | None


def tenant_from_session(authorization: Annotated[str | None, Header()] = None) -> TenantContext:
    token = (authorization or "").removeprefix("Bearer ").strip()
    tenant = _sessions.get(token)
    if tenant is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    return TenantContext(tenant)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/clients")
def clients() -> dict[str, str]:
    return {t: DISPLAY_NAMES[t] for t in CLIENT_TENANTS}


@app.post("/login")
def login(req: LoginRequest) -> LoginResponse:
    token = secrets.token_urlsafe(24)
    _sessions[token] = req.client_id
    return LoginResponse(
        token=token, client_name=DISPLAY_NAMES[req.client_id], disclosure=AI_DISCLOSURE
    )


@app.post("/chat")
def chat(
    req: ChatRequest, ctx: Annotated[TenantContext, Depends(tenant_from_session)]
) -> ChatResponse:
    history = [t.model_dump() for t in req.history]
    ans = answer_question(ctx, req.question, history)
    trace_id = record(req.question, ans)
    return ChatResponse(
        answer=ans.answer,
        outcome=ans.outcome,
        citations=[CitationOut(doc_id=c.doc_id, title=c.title) for c in ans.citations],
        disclosure=AI_DISCLOSURE,
        trace_id=trace_id,
        prompt_version=ans.prompt_version,
        kb_version=ans.kb_version,
    )
