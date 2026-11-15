"""Per-request tracing (FR6): client, retrieved chunks with scores, model, prompt and KB versions.

Every trace goes to a local JSONL file (.traces/, git-ignored). Text is PII-masked before it is
written. Langfuse Cloud export is added once its keys are configured (see CLAUDE.md).
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from app.agent import AgentAnswer
from app.config import REPO_ROOT
from app.pii import mask

TRACE_DIR = REPO_ROOT / ".traces"


def trace_record(question: str, ans: AgentAnswer) -> dict[str, Any]:
    return {
        "trace_id": str(uuid.uuid4()),
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
    }


def record(question: str, ans: AgentAnswer) -> str:
    rec = trace_record(question, ans)
    TRACE_DIR.mkdir(exist_ok=True)
    path = TRACE_DIR / f"{datetime.now(UTC):%Y%m%d}.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return str(rec["trace_id"])
