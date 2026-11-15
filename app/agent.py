"""The answering pipeline: retrieve (tenant-filtered) -> abstain check -> LLM -> output guard."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from functools import lru_cache
from html import escape

from app.config import PROMPT_VERSION, REPO_ROOT, RETRIEVAL
from app.guard import apply_guard
from app.llm import LLM, default_llm
from app.retrieval import RetrievedChunk, retrieve
from app.tenancy import DISPLAY_NAMES, TenantContext

NO_INFO = (
    "I don't know. I couldn't find anything about that in your knowledge base. "
    "Try rephrasing, or ask your team lead."
)
MAX_HISTORY_TURNS = 6


@lru_cache(maxsize=4)
def system_prompt(tenant_id: str) -> str:
    template = (REPO_ROOT / "prompts" / f"system_{PROMPT_VERSION}.md").read_text(encoding="utf-8")
    return template.replace("{client_name}", DISPLAY_NAMES[tenant_id])


@dataclass
class Citation:
    doc_id: str
    title: str


@dataclass
class AgentAnswer:
    answer: str
    outcome: str
    citations: list[Citation]
    tenant_id: str
    prompt_version: str
    kb_version: str | None
    model: str | None
    retrieved: list[RetrievedChunk]
    guard_flags: list[str] = field(default_factory=list)
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


def _doc_block(c: RetrievedChunk) -> str:
    return (
        f'<document id="{c.doc_id}" title="{escape(c.title)}" status="{c.status}" '
        f'effective_date="{c.effective_date}" score="{c.score:.2f}">\n{c.content}\n</document>'
    )


def build_user_message(question: str, context: list[RetrievedChunk]) -> str:
    quotable = [c for c in context if c.data_class in ("public", "insight")]
    internal = [c for c in context if c.data_class == "inference_only"]
    parts = ["<documents>", *(_doc_block(c) for c in quotable), "</documents>"]
    if internal:
        parts += ["<internal_context>", *(_doc_block(c) for c in internal), "</internal_context>"]
    parts += ["", f"Question: {question}"]
    return "\n".join(parts)


def answer_question(
    ctx: TenantContext,
    question: str,
    history: list[dict[str, str]] | None = None,
    llm: LLM | None = None,
) -> AgentAnswer:
    start = time.perf_counter()
    hits = retrieve(ctx, question)
    # Contact lists (data_class pii) never reach the model.
    context = [h for h in hits if h.data_class != "pii"]
    kb_version = hits[0].kb_version if hits else None
    base = {"tenant_id": ctx.tenant_id, "prompt_version": PROMPT_VERSION, "kb_version": kb_version}

    if not context or context[0].score < RETRIEVAL.min_score:
        return AgentAnswer(
            NO_INFO,
            "no_information",
            [],
            model=None,
            retrieved=hits,
            latency_ms=int((time.perf_counter() - start) * 1000),
            **base,  # type: ignore[arg-type]
        )

    system = system_prompt(ctx.tenant_id)
    messages = list((history or [])[-2 * MAX_HISTORY_TURNS :])
    messages.append({"role": "user", "content": build_user_message(question, context)})
    result = (llm or default_llm()).answer(system, messages)

    guarded = apply_guard(result.answer, result.cited_doc_ids, context, system)
    titles = {c.doc_id: c.title for c in context}
    return AgentAnswer(
        answer=guarded.answer or NO_INFO,
        outcome=result.outcome if not guarded.flags or guarded.cited_doc_ids else "declined",
        citations=[Citation(d, titles[d]) for d in guarded.cited_doc_ids],
        model=result.model,
        retrieved=hits,
        guard_flags=guarded.flags,
        latency_ms=int((time.perf_counter() - start) * 1000),
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        **base,  # type: ignore[arg-type]
    )
