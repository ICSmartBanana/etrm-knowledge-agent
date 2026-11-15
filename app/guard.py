"""Output guard: runs on every answer, whatever the model decided (FR4).

1. PII: any seeded or pattern-matched PII is masked, and the answer is flagged.
2. Inference-only: if the answer shares any 8-word run with an inference-only chunk that was in
   context, the whole answer is withheld.
3. System prompt: if the answer shares any 10-word run with the system prompt, it is withheld.
4. Citations: only ids of non-confidential documents that were actually in context survive.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.pii import find_pii, mask
from app.retrieval import RetrievedChunk

WITHHELD = (
    "I can't share that. It draws on internal or restricted information. "
    "Please contact your team lead if you need it."
)
_WORD_RE = re.compile(r"[a-z0-9]+(?:[.,'][a-z0-9]+)*")


def _ngrams(text: str, n: int) -> set[tuple[str, ...]]:
    words = _WORD_RE.findall(text.lower())
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def shares_ngram(a: str, b: str, n: int) -> bool:
    return bool(_ngrams(a, n) & _ngrams(b, n))


@dataclass
class GuardResult:
    answer: str
    cited_doc_ids: list[str]
    flags: list[str] = field(default_factory=list)


def apply_guard(
    answer: str,
    cited_doc_ids: list[str],
    context: list[RetrievedChunk],
    system_prompt: str,
) -> GuardResult:
    flags: list[str] = []
    confidential = [c for c in context if c.data_class in ("inference_only", "pii")]
    if any(shares_ngram(answer, c.content, 8) for c in confidential):
        return GuardResult(WITHHELD, [], ["inference_only_overlap"])
    if shares_ngram(answer, system_prompt, 10):
        return GuardResult(WITHHELD, [], ["system_prompt_overlap"])

    if find_pii(answer):
        answer = mask(answer)
        flags.append("pii_masked")

    citable = {c.doc_id for c in context if c.data_class not in ("inference_only", "pii")}
    kept = [d for d in dict.fromkeys(cited_doc_ids) if d in citable]
    if len(kept) != len(set(cited_doc_ids)):
        flags.append("citations_dropped")
    return GuardResult(answer, kept, flags)
