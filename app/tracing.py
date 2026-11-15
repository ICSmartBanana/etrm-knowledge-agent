"""Per-request tracing (FR6): client, retrieved chunks with scores, model, prompt and KB versions.

Every trace goes to a local JSONL file (.traces/, git-ignored). When LANGFUSE_PUBLIC_KEY and
LANGFUSE_SECRET_KEY are set, the same trace is also exported to Langfuse Cloud.

What leaves the machine (Langfuse): the PII-masked question and answer, retrieved doc ids,
headings, data classes and scores, model, versions, tokens, cost and guard flags. Document text
is never exported. A Langfuse-side mask function masks PII again as a second layer.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from app.agent import AgentAnswer
from app.config import ANSWER_PRICE_PER_MTOK, REPO_ROOT
from app.pii import mask

TRACE_DIR = REPO_ROOT / ".traces"
log = logging.getLogger(__name__)


def cost_usd(ans: AgentAnswer) -> float:
    price_in, price_out = ANSWER_PRICE_PER_MTOK
    return round((ans.input_tokens * price_in + ans.output_tokens * price_out) / 1e6, 6)


def trace_record(question: str, ans: AgentAnswer, trace_id: str | None = None) -> dict[str, Any]:
    return {
        "trace_id": trace_id or uuid.uuid4().hex,
        "timestamp": datetime.now(UTC).isoformat(),
        "client_id": ans.tenant_id,
        "question": mask(question),
        "answer": mask(ans.answer),
        "outcome": ans.outcome,
        "citations": [c.doc_id for c in ans.citations],
        "retrieved": [
            {
                "tenant_id": c.tenant_id,
                "doc_id": c.doc_id,
                "heading": c.heading,
                "data_class": c.data_class,
                "score": round(c.score, 4),
            }
            for c in ans.retrieved
        ],
        "model": ans.model,
        "prompt_version": ans.prompt_version,
        "kb_version": ans.kb_version,
        "guard_flags": ans.guard_flags,
        "latency_ms": ans.latency_ms,
        "input_tokens": ans.input_tokens,
        "output_tokens": ans.output_tokens,
        "cost_usd": cost_usd(ans),
    }


def _mask_any(*, data: Any, **_: Any) -> Any:
    """Langfuse mask hook: mask PII in every string, recursively."""
    if isinstance(data, str):
        return mask(data)
    if isinstance(data, dict):
        return {k: _mask_any(data=v) for k, v in data.items()}
    if isinstance(data, list | tuple):
        return [_mask_any(data=v) for v in data]
    return data


@lru_cache(maxsize=1)
def langfuse_client() -> Any | None:
    if not (os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY")):
        return None
    from langfuse import Langfuse, is_langfuse_span

    # Export only the spans built below. Other OpenTelemetry spans in the process (for example
    # the Anthropic SDK's own auto-instrumentation) could carry the full prompt, including
    # document text, so they never leave the machine.
    return Langfuse(
        mask=_mask_any,
        environment=os.environ.get("ETRM_ENV", "local"),
        should_export_span=is_langfuse_span,
    )


def export_langfuse(rec: dict[str, Any]) -> str | None:
    """Send one trace to Langfuse. Returns its Langfuse trace id, or None if disabled."""
    lf = langfuse_client()
    if lf is None:
        return None
    from langfuse import propagate_attributes

    tags = [rec["client_id"], rec["outcome"], *rec["guard_flags"]]
    meta = {k: rec[k] for k in ("client_id", "kb_version", "prompt_version", "latency_ms")}
    with (
        lf.start_as_current_observation(name="chat", as_type="span", input=rec["question"]) as root,
        propagate_attributes(
            trace_name="chat",
            tags=tags,
            version=rec["prompt_version"],
            metadata={k: str(v) for k, v in meta.items()},
        ),
    ):
        lf_trace_id = str(lf.get_current_trace_id())
        retr = root.start_observation(
            name="retrieval", as_type="retriever", input=rec["question"], output=rec["retrieved"]
        )
        retr.end()
        if rec["model"]:
            gen = root.start_observation(
                name="answer",
                as_type="generation",
                model=rec["model"],
                output=rec["answer"],
                metadata={"prompt_version": rec["prompt_version"], "citations": rec["citations"]},
                usage_details={"input": rec["input_tokens"], "output": rec["output_tokens"]},
                cost_details={"total": rec["cost_usd"]},
            )
            gen.end()
        guard = root.start_observation(
            name="output_guard",
            as_type="guardrail",
            output={"flags": rec["guard_flags"], "outcome": rec["outcome"]},
            level="WARNING" if rec["guard_flags"] else "DEFAULT",
        )
        guard.end()
        root.update(output=rec["answer"], metadata=meta)
    return lf_trace_id


def record(question: str, ans: AgentAnswer) -> str:
    rec = trace_record(question, ans)
    try:
        lf_id = export_langfuse(rec)
        if lf_id:
            rec["trace_id"] = lf_id
    except Exception:  # tracing must never break an answer
        log.exception("Langfuse export failed; trace kept locally")
    TRACE_DIR.mkdir(exist_ok=True)
    path = TRACE_DIR / f"{datetime.now(UTC):%Y%m%d}.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return str(rec["trace_id"])


def flush() -> None:
    lf = langfuse_client()
    if lf is not None:
        lf.flush()
