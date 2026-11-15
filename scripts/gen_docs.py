"""Generate the governance docs from the repo and eval outputs (brief §7 "documentation
generation"): model card, data-source register, eval report and changelog.

    uv run python scripts/gen_docs.py --out build/docs

CI uploads the output as an artifact on every PR and push. The hand-written narrative docs in
docs/governance/ stay the source for reasoning and sign-offs; these files are the always-current
facts.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import (  # noqa: E402
    ANSWER_MODEL,
    ANSWER_PRICE_PER_MTOK,
    EMBED_MODEL,
    PROMPT_VERSION,
    RETRIEVAL,
)
from app.tenancy import CLIENT_TENANTS  # noqa: E402

CORPUS = ROOT / "data" / "synthetic"
GATES = ("leakage", "pii", "inference_only", "system_prompt_or_injection")
METRICS = (
    "retrieval_hit_at_k",
    "retrieval_mrr",
    "must_include",
    "must_not_include",
    "outcome_correct",
    "cited_expected_doc",
)

KNOWN_LIMITS = [
    "Knowledge is limited to the synthetic documents ingested; the agent says it doesn't know "
    "when nothing relevant is retrieved (cosine score below the abstain threshold).",
    "PII detection uses regexes plus a seeded registry. Real deployments need NER for names.",
    "The inference-only guard blocks verbatim 8-word overlaps; it can over-trigger when "
    "internal notes repeat public text (see the iteration-1 eval report).",
    "Exact-scan retrieval with fixed heading-based chunks; some values are missed when their "
    "chunk isn't in the top-k.",
    "Quality metrics are deterministic exact-match checks; no LLM-judged faithfulness yet.",
    "Answers can still be wrong. Users are told so by the AI disclosure notice.",
]


def _front_matter(path: Path) -> dict[str, object]:
    _, meta, _ = path.read_text("utf-8").split("---\n", 2)
    data: dict[str, object] = yaml.safe_load(meta)
    return data


def _baseline(name: str) -> dict[str, object]:
    data: dict[str, object] = json.loads((ROOT / "evals" / "baselines" / name).read_text("utf-8"))
    return data


def eval_table(summary: dict[str, dict[str, object]]) -> list[str]:
    gates = summary["hard_gate_failures"]
    overall = summary["overall"]
    lines = ["| Hard gate | Failures |", "|---|---|"]
    lines += [f"| {g} | {gates[g]} |" for g in GATES]
    lines += ["", "| Metric | Value |", "|---|---|"]
    lines += [f"| {m} | {overall.get(m)} |" for m in METRICS]
    return lines


def model_card() -> str:
    full = _baseline("iteration-1.json")
    thresholds = yaml.safe_load((ROOT / "evals" / "thresholds.yaml").read_text("utf-8"))
    changelog = (ROOT / "CHANGELOG.md").read_text("utf-8")
    lines = [
        "# Model card: ETRM knowledge agent (POC)",
        "",
        f"_Generated {datetime.now(UTC):%Y-%m-%d %H:%M} UTC by `scripts/gen_docs.py`._",
        "",
        "## Purpose",
        "",
        "Answers questions from staff of three fictional ETRM clients about their own trading "
        "operations, using only that client's knowledge base plus shared consultancy guidance. "
        "Limited-risk AI system under the EU AI Act (Art. 50 disclosure); see "
        "`docs/governance/use-case-classification.md`. Not for decisions about individuals and "
        "not connected to any operational system.",
        "",
        "## System",
        "",
        "| Component | Version |",
        "|---|---|",
        f"| Answer model | `{ANSWER_MODEL}` (effort `low`, server-side refusal fallback) |",
        f"| Price used for cost reporting | ${ANSWER_PRICE_PER_MTOK[0]} / "
        f"${ANSWER_PRICE_PER_MTOK[1]} per M input / output tokens |",
        f"| System prompt | `prompts/system_{PROMPT_VERSION}.md` |",
        f"| Embedding model | `{EMBED_MODEL}` (local) |",
        f"| Retrieval | top-k {RETRIEVAL.top_k}, abstain below {RETRIEVAL.min_score}, "
        f"chunks up to {RETRIEVAL.chunk_max_chars} chars, exact scan |",
        f"| Clients | {', '.join(CLIENT_TENANTS)} (+ shared `consultancy`) |",
        "",
        "## Evaluation results (baseline, full suite)",
        "",
        f"Baseline `{full['meta']['prompt_version']}` / `{full['meta']['kb_version']}` "  # type: ignore[index]
        f"run {full['meta']['timestamp']}.",  # type: ignore[index]
        "",
        *eval_table(full["summary"]),  # type: ignore[arg-type]
        "",
        "PR gate floors (`evals/thresholds.yaml`, regression suite): "
        + ", ".join(f"{k} ≥ {v}" for k, v in thresholds["suites"]["regression"]["floors"].items())
        + ". Hard gates are zero-tolerance.",
        "",
        "## Known limitations",
        "",
        *[f"- {limit}" for limit in KNOWN_LIMITS],
        "",
        "## Change history",
        "",
        changelog.split("\n", 1)[1].strip(),
        "",
    ]
    return "\n".join(lines)


def data_register() -> str:
    rows = []
    for tenant_dir in sorted(p for p in CORPUS.iterdir() if p.is_dir()):
        metas = [_front_matter(p) for p in sorted(tenant_dir.glob("*.md"))]
        classes = Counter(str(m["data_class"]) for m in metas)
        status = Counter(str(m["status"]) for m in metas)
        rows.append(
            f"| `{tenant_dir.name}` | {len(metas)} | "
            + ", ".join(f"{k} {v}" for k, v in sorted(classes.items()))
            + f" | {status.get('superseded', 0)} | "
            + f"{sum(1 for m in metas if m.get('contradicts'))} | "
            + f"{sum(1 for m in metas if m.get('near_duplicate_of'))} |"
        )
    pii = json.loads((ROOT / "data" / "pii_registry.json").read_text("utf-8"))
    lines = [
        "# Data-source register (generated facts)",
        "",
        f"_Generated {datetime.now(UTC):%Y-%m-%d %H:%M} UTC. Narrative, owners, allowed use and "
        "sign-offs: `docs/governance/data-source-register.md`._",
        "",
        "| Knowledge base | Docs | By data class | Superseded | Contradicting | Near-duplicates |",
        "|---|---|---|---|---|---|",
        *rows,
        "",
        "| Knowledge base | Seeded PII values |",
        "|---|---|",
        *[f"| `{t}` | {len(v)} |" for t, v in sorted(pii.items())],
        "",
    ]
    return "\n".join(lines)


def eval_report() -> str:
    lines = ["# Eval report (baselines)", ""]
    for name in ("iteration-1.json", "iteration-1-regression.json"):
        b = _baseline(name)
        meta = b["meta"]
        lines += [
            f"## `{name}` ({meta['suite']} suite)",  # type: ignore[index]
            "",
            f"Model `{meta['answer_model']}`, prompt `{meta['prompt_version']}`, "  # type: ignore[index]
            f"KB `{meta['kb_version']}`.",  # type: ignore[index]
            "",
            *eval_table(b["summary"]),  # type: ignore[arg-type]
            "",
        ]
    lines.append("Narrative and analysis: `docs/evals/iteration-1-report.md`.")
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description="Generate governance docs.")
    p.add_argument("--out", type=Path, default=ROOT / "build" / "docs")
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "model-card.md").write_text(model_card(), "utf-8")
    (args.out / "data-source-register.md").write_text(data_register(), "utf-8")
    (args.out / "eval-report.md").write_text(eval_report(), "utf-8")
    shutil.copy(ROOT / "CHANGELOG.md", args.out / "CHANGELOG.md")
    print(f"Wrote 4 documents to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
