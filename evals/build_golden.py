"""Build the golden set (evals/sets/golden.jsonl) from the specs, with Claude Haiku.

    uv run python -m evals.build_golden          # build from scratch (replaces the frozen set)
    uv run python -m evals.build_golden --fix    # regenerate only questions that fail the checks

Per client: one question per key value in current, quotable docs; one combined question per doc
with two or more key values; questions on the consultancy guidance; and hand-written
unanswerable questions. Generated once, reviewed (20% human spot-check), then frozen.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import anthropic
from dotenv import load_dotenv

from datagen.spec import DocSpec, load_all, strip_brackets
from evals.items import SETS_DIR, question_problems

MODEL = "claude-haiku-5-5"

UNANSWERABLE = {
    "clan_a": [
        "What is the value-at-risk limit for the power desk?",
        "Which bank holds our margin account?",
        "What carbon price is assumed in the 2026 budget?",
        "How many LNG cargoes did we buy last year?",
        "How do I reset my Lumen ETRM password?",
        "What is our capacity market obligation for 2027?",
        "What is the retail tariff for small business customers?",
        "Which weather data vendor feeds the demand forecast?",
    ],
    "clan_b": [
        "What is today's jet fuel inventory at the main terminal?",
        "Which shipbroker do we use for clean tankers?",
        "What is the value-at-risk limit for the gasoline book?",
        "What hedge ratio does our diesel policy require?",
        "What uptime does the Corvane CTRM SaaS contract guarantee?",
        "Which insurer covers cargo losses?",
        "What is the margin call threshold with our clearing broker?",
        "How many staff work on the diesel desk?",
    ],
    "clan_c": [
        "What does our hedge policy say about sugar?",
        "Which Antwerp warehouse stores our cocoa?",
        "Which coffee quality grading scale do we use?",
        "What is the value-at-risk limit for soybeans?",
        "What freight rate do we pay from Santos to Hamburg?",
        "How do we hedge BRL currency exposure?",
        "When is the next Harvest CTRM upgrade scheduled?",
        "Which certifications must our growers hold?",
    ],
}

PROMPT = """Write one question that a staff member at {company} might ask an internal knowledge \
assistant, whose correct answer is given by the fact(s) below. Rules: the question must not \
contain the answer value(s) {keys}; do not mention the company name or the document title; \
ask for all of the values. Output only the question.

Facts:
{facts}"""


QUESTION_SCHEMA = {
    "type": "object",
    "properties": {"question": {"type": "string"}},
    "required": ["question"],
    "additionalProperties": False,
}


def _ask(client: anthropic.Anthropic, prompt: str, keys: list[str]) -> str:
    """Ask for one question as structured JSON (so no drafting text can leak into it),
    then validate it, retrying with feedback up to 3 times."""
    problems: list[str] = []
    for _ in range(3):
        content = prompt
        if problems:
            content += "\n\nYour previous question had these problems: " + "; ".join(problems)
        resp = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            output_config={
                "effort": "low",
                "format": {"type": "json_schema", "schema": QUESTION_SCHEMA},
            },
            messages=[{"role": "user", "content": content}],
        )
        text = next(b.text for b in resp.content if b.type == "text")
        question = str(json.loads(text)["question"]).strip()
        problems = question_problems(question, keys)
        if not problems:
            return question
    raise RuntimeError(f"no valid question after 3 attempts: {problems}")


def _quotable(d: DocSpec) -> bool:
    return d.data_class in ("public", "insight") and d.status == "current" and not d.contradicts


Job = tuple[str, str, list[str], list[str], str]  # tenant, company, keys, facts, doc id


def _jobs() -> list[Job]:
    specs = load_all()
    jobs: list[Job] = []
    for tid in ("clan_a", "clan_b", "clan_c"):
        s = specs[tid]
        for d in filter(_quotable, s.docs):
            for f in d.facts:
                for k in [k for k in d.keys if f"[[{k}]]" in f]:
                    jobs.append((tid, s.company_name, [k], [f], d.id))
            if len(d.keys) >= 2:
                jobs.append((tid, s.company_name, d.keys[:2], d.facts, d.id))
        for d in specs["consultancy"].docs:
            if d.keys:
                jobs.append((tid, s.company_name, d.keys[:1], d.facts, d.id))
    return jobs


def _prompt(job: Job) -> str:
    _, company, keys, facts, _ = job
    return PROMPT.format(
        company=company,
        keys=", ".join(keys),
        facts="\n".join(f"- {strip_brackets(f)}" for f in facts),
    )


def _job_for(item: dict[str, Any]) -> Job:
    """Rebuild the generation job behind an existing golden item (same keys, same doc)."""
    keys = [k for group in item["must_include"] for k in group]
    return next(
        j
        for j in _jobs()
        if j[0] == item["tenant_id"] and j[2] == keys and j[4] == item["expected_doc_ids"][0]
    )


def fix() -> int:
    """Regenerate only the questions that fail question_problems(); keep ids and expectations."""
    load_dotenv()
    client = anthropic.Anthropic()
    path = SETS_DIR / "golden.jsonl"
    items = [json.loads(line) for line in path.read_text("utf-8").splitlines()]
    flawed = [
        i
        for i in items
        if question_problems(i["question"], [k for g in i["must_include"] for k in g])
    ]
    print(f"Regenerating {len(flawed)} flawed questions...")
    with ThreadPoolExecutor(max_workers=4) as pool:
        new = list(pool.map(lambda i: _ask(client, _prompt(_job_for(i)), _keys(i)), flawed))
    for item, question in zip(flawed, new, strict=True):
        item["question"] = question
    path.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items), "utf-8")
    print("Fixed:", ", ".join(i["id"] for i in flawed))
    return 0


def _keys(item: dict[str, Any]) -> list[str]:
    return [k for g in item["must_include"] for k in g]


def build() -> list[dict[str, Any]]:
    load_dotenv()
    client = anthropic.Anthropic()
    jobs = _jobs()

    def make(job: Job) -> dict[str, Any]:
        tid, _, keys, _, doc = job
        q = _ask(client, _prompt(job), keys)
        return {
            "tenant_id": tid,
            "question": q,
            "must_include": [[k] for k in keys],
            "expected_doc_ids": [doc],
            "expect_outcome": ["answered"],
        }

    with ThreadPoolExecutor(max_workers=4) as pool:
        items = list(pool.map(make, jobs))
    for tid, questions in UNANSWERABLE.items():
        items += [
            {
                "tenant_id": tid,
                "question": q,
                "must_include": [],
                "expected_doc_ids": [],
                "expect_outcome": ["no_information", "out_of_scope"],
            }
            for q in questions
        ]
    counters: dict[str, int] = {}
    for it in sorted(items, key=lambda i: i["tenant_id"]):
        counters[it["tenant_id"]] = counters.get(it["tenant_id"], 0) + 1
        it["id"] = f"golden-{it['tenant_id']}-{counters[it['tenant_id']]:03d}"
    return sorted(items, key=lambda i: i["id"])


def main() -> int:
    if "--fix" in sys.argv:
        return fix()
    items = build()
    path = SETS_DIR / "golden.jsonl"
    path.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items), "utf-8")
    counts = {t: sum(i["tenant_id"] == t for i in items) for t in ("clan_a", "clan_b", "clan_c")}
    print(f"Wrote {len(items)} golden items to {path}: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
