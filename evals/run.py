"""Run eval suites against the real agent (real retrieval, real model) and score them.

    uv run python -m evals.run --suite regression            # PR gate subset
    uv run python -m evals.run --suite all --save-baseline evals/baselines/iteration-1.json

Retrieval is scored separately from generation:
- retrieval: hit@k (an expected doc is among the retrieved chunks) and MRR.
- generation: must_include / must_not_include / expected outcome / expected doc cited.
Hard gates (leakage, PII, inference-only, system prompt or injection) run on every answer, and
any failure makes the run exit non-zero.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.agent import answer_question, system_prompt
from app.config import ANSWER_MODEL, EMBED_MODEL, PROMPT_VERSION, RETRIEVAL
from app.tenancy import TenantContext
from evals.gates import content_checks, hard_gate_failures
from evals.items import EvalItem, select

RESULTS_DIR = Path(__file__).resolve().parent / "results"
GATES = ("leakage", "pii", "inference_only", "system_prompt_or_injection")


def run_item(item: EvalItem) -> dict[str, Any]:
    ans = answer_question(TenantContext(item.tenant_id), item.question, item.history)
    retrieved_docs = [c.doc_id for c in ans.retrieved]
    rank = next((i for i, d in enumerate(retrieved_docs, 1) if d in item.expected_doc_ids), None)
    cited = [c.doc_id for c in ans.citations]
    return {
        "id": item.id,
        "suite": item.suite,
        "tenant_id": item.tenant_id,
        "outcome": ans.outcome,
        "answer": ans.answer,
        "model": ans.model,
        "kb_version": ans.kb_version,
        "guard_flags": ans.guard_flags,
        "retrieved": retrieved_docs,
        "retrieved_tenants": sorted({c.tenant_id for c in ans.retrieved}),
        "cited": cited,
        "hit": rank is not None if item.expected_doc_ids else None,
        "rr": (1 / rank if rank else 0.0) if item.expected_doc_ids else None,
        "cited_expected": bool(set(cited) & set(item.expected_doc_ids))
        if item.expected_doc_ids and item.expect_outcome == ["answered"]
        else None,
        "checks": content_checks(item, ans.answer, ans.outcome),
        "gate_failures": hard_gate_failures(
            item, ans.answer, {c.tenant_id for c in ans.retrieved}, system_prompt(item.tenant_id)
        ),
        "latency_ms": ans.latency_ms,
        "input_tokens": ans.input_tokens,
        "output_tokens": ans.output_tokens,
    }


_PREFIX_TENANT = {"a": "clan_a", "b": "clan_b", "c": "clan_c", "m": "consultancy"}


def rescore(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Re-apply the current checks and gates to saved answers, without calling the model."""
    items = {i.id: i for i in select("all")}
    out = []
    for r in results:
        item = items[r["id"]]
        tenants = set(r.get("retrieved_tenants") or {_PREFIX_TENANT[d[0]] for d in r["retrieved"]})
        out.append(
            {
                **r,
                "retrieved_tenants": sorted(tenants),
                "checks": content_checks(item, r["answer"], r["outcome"]),
                "gate_failures": hard_gate_failures(
                    item, r["answer"], tenants, system_prompt(item.tenant_id)
                ),
            }
        )
    return out


def _mean(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 4) if xs else None


def summarise(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_suite: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in results:
        by_suite[r["suite"]].append(r)

    def metrics(rs: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "n": len(rs),
            "retrieval_hit_at_k": _mean([float(r["hit"]) for r in rs if r["hit"] is not None]),
            "retrieval_mrr": _mean([r["rr"] for r in rs if r["rr"] is not None]),
            "must_include": _mean([float(r["checks"]["must_include"]) for r in rs]),
            "must_not_include": _mean([float(r["checks"]["must_not_include"]) for r in rs]),
            "outcome_correct": _mean([float(r["checks"]["outcome"]) for r in rs]),
            "cited_expected_doc": _mean(
                [float(r["cited_expected"]) for r in rs if r["cited_expected"] is not None]
            ),
        }

    gates = {g: sum(g in r["gate_failures"] for r in results) for g in GATES}
    return {
        "overall": metrics(results),
        "by_suite": {s: metrics(rs) for s, rs in sorted(by_suite.items())},
        "hard_gate_failures": gates,
        "hard_gates_passed": all(v == 0 for v in gates.values()),
        "tokens": {
            "input": sum(r["input_tokens"] for r in results),
            "output": sum(r["output_tokens"] for r in results),
        },
        "p95_latency_ms": sorted(r["latency_ms"] for r in results)[int(0.95 * (len(results) - 1))]
        if results
        else None,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Run eval suites.")
    p.add_argument(
        "--suite",
        default="regression",
        choices=[
            "regression",
            "all",
            "golden",
            "overlap",
            "leakage",
            "pii_inference",
            "adversarial",
        ],
    )
    p.add_argument("--save-baseline", type=Path, help="also write the summary as a baseline file")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument(
        "--rescore", type=Path, help="re-check the answers in a saved results file (no API calls)"
    )
    args = p.parse_args()

    rescored_from = None
    if args.rescore:
        saved = json.loads(args.rescore.read_text("utf-8"))
        results = rescore(saved["results"])
        args.suite = saved["meta"]["suite"]
        rescored_from = {"file": args.rescore.name, "answers_generated": saved["meta"]["timestamp"]}
        print(f"Rescoring {len(results)} saved answers from {args.rescore.name}...")
    else:
        items = select(args.suite)
        print(f"Running {len(items)} items ({args.suite}) against {ANSWER_MODEL}...")
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(run_item, items))

    summary = summarise(results)
    meta = {
        "suite": args.suite,
        "timestamp": datetime.now(UTC).isoformat(),
        "rescored_from": rescored_from,
        "answer_model": ANSWER_MODEL,
        "embed_model": EMBED_MODEL,
        "prompt_version": PROMPT_VERSION,
        "kb_version": next((r["kb_version"] for r in results if r["kb_version"]), None),
        "retrieval": {
            "top_k": RETRIEVAL.top_k,
            "min_score": RETRIEVAL.min_score,
            "chunk_max_chars": RETRIEVAL.chunk_max_chars,
        },
        "judge": "none (deterministic checks only)",
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / f"{datetime.now(UTC):%Y%m%dT%H%M%S}-{args.suite}.json"
    out.write_text(
        json.dumps(
            {"meta": meta, "summary": summary, "results": results}, indent=2, ensure_ascii=False
        ),
        "utf-8",
    )
    if args.save_baseline:
        args.save_baseline.parent.mkdir(parents=True, exist_ok=True)
        args.save_baseline.write_text(
            json.dumps({"meta": meta, "summary": summary}, indent=2) + "\n", "utf-8"
        )

    print(json.dumps(summary, indent=2))
    print(f"Full results: {out}")
    if not summary["hard_gates_passed"]:
        print("HARD GATE FAILURE", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
