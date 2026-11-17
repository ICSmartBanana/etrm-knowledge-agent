"""FastAPI service.

Simulated login (FR1): POST /login with a client id returns a session token. Every /chat call
must carry that token; the tenant comes only from the session, never from the request body.

    uv run uvicorn app.api.main:app --port 8000
"""

from __future__ import annotations

import secrets
from collections import OrderedDict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agent import answer_question
from app.api.limits import (
    ALLOWED_ORIGINS,
    DAILY_QUOTA,
    MAX_QUESTION_CHARS,
    RATE_LIMIT,
    QuotaStatus,
)
from app.tenancy import CLIENT_TENANTS, DISPLAY_NAMES, TenantContext
from app.tracing import flush, record

AI_DISCLOSURE = (
    "You are chatting with an AI assistant. Answers are generated from your organisation's "
    "documents and can be wrong; check important details before acting on them."
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    flush()  # send any buffered Langfuse traces before the process exits


app = FastAPI(title="ETRM knowledge agent (POC)", lifespan=lifespan)
# Hosted demo: only the portal's origin may call the API from a browser. Empty (the default)
# adds no CORS headers, which is right for the local Streamlit UI (server-side calls).
if ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )
# token -> tenant_id, in memory (POC only). Bounded so a public demo can't grow it forever.
_sessions: OrderedDict[str, str] = OrderedDict()
MAX_SESSIONS = 5_000


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


class QuotaOut(BaseModel):
    limit: int
    used: int
    remaining: int | None
    resets_at: str

    @classmethod
    def of(cls, q: QuotaStatus) -> QuotaOut:
        return cls(limit=q.limit, used=q.used, remaining=q.remaining, resets_at=q.resets_at)


class ChatResponse(BaseModel):
    answer: str
    outcome: str
    citations: list[CitationOut]
    disclosure: str
    trace_id: str
    prompt_version: str
    kb_version: str | None
    quota: QuotaOut


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


@app.get("/quota")
def quota() -> QuotaOut:
    """Today's shared question allowance (limit 0 = unlimited), for the UI's counter."""
    return QuotaOut.of(DAILY_QUOTA.status())


@app.post("/login")
def login(req: LoginRequest) -> LoginResponse:
    token = secrets.token_urlsafe(24)
    _sessions[token] = req.client_id
    while len(_sessions) > MAX_SESSIONS:
        _sessions.popitem(last=False)
    return LoginResponse(
        token=token, client_name=DISPLAY_NAMES[req.client_id], disclosure=AI_DISCLOSURE
    )


@app.post("/chat")
def chat(
    req: ChatRequest,
    request: Request,
    ctx: Annotated[TenantContext, Depends(tenant_from_session)],
) -> ChatResponse:
    if len(req.question) > MAX_QUESTION_CHARS:
        raise HTTPException(422, f"Questions are limited to {MAX_QUESTION_CHARS} characters.")
    # Behind the host's proxy the first X-Forwarded-For entry is the visitor.
    forwarded = request.headers.get("x-forwarded-for", "")
    visitor = forwarded.split(",")[0].strip() or (request.client.host if request.client else "?")
    if not RATE_LIMIT.allow(visitor):
        raise HTTPException(429, "Too many questions in a minute. Please wait a moment.")
    if not DAILY_QUOTA.try_take():
        q = DAILY_QUOTA.status()
        raise HTTPException(
            429,
            f"Today's demo allowance of {q.limit} questions is used up. "
            f"It resets at 00:00 UTC ({q.resets_at}).",
        )
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
        quota=QuotaOut.of(DAILY_QUOTA.status()),
    )
