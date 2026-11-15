"""The answering model, behind a small interface so Azure OpenAI could replace it later."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol

import anthropic

from app.config import ANSWER_MODEL

OUTCOMES = ("answered", "no_information", "out_of_scope", "declined")

ANSWER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "cited_doc_ids": {"type": "array", "items": {"type": "string"}},
        "outcome": {"type": "string", "enum": list(OUTCOMES)},
    },
    "required": ["answer", "cited_doc_ids", "outcome"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class LLMResult:
    answer: str
    cited_doc_ids: list[str]
    outcome: str
    model: str  # the model that actually served the request (may differ after a fallback)
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    stop_reason: str


class LLM(Protocol):
    def answer(self, system: str, messages: list[dict[str, str]]) -> LLMResult: ...


class AnthropicLLM:
    def __init__(self, model: str = ANSWER_MODEL) -> None:
        self.model = model
        self._client = anthropic.Anthropic()

    def answer(self, system: str, messages: list[dict[str, str]]) -> LLMResult:
        request: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4000,
            # Server-side fallback on a safety-classifier refusal; the served model is traced.
            "betas": ["server-side-fallback-2026-07-01"],
            "fallbacks": "default",
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            "messages": messages,
            "output_config": {
                "effort": "low",
                "format": {"type": "json_schema", "schema": ANSWER_SCHEMA},
            },
        }
        resp = self._client.beta.messages.create(**request)
        usage = resp.usage
        model = str(resp.model)
        cache_read = usage.cache_read_input_tokens or 0
        stop = str(resp.stop_reason)
        data = {"answer": "", "cited_doc_ids": [], "outcome": "declined"}
        if resp.stop_reason == "end_turn":
            data = json.loads(next(b.text for b in resp.content if b.type == "text"))
        return LLMResult(
            answer=str(data["answer"]),
            cited_doc_ids=[str(d) for d in data["cited_doc_ids"]],
            outcome=str(data["outcome"]),
            model=model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_read_tokens=cache_read,
            stop_reason=stop,
        )


@lru_cache(maxsize=1)
def default_llm() -> LLM:
    return AnthropicLLM()
