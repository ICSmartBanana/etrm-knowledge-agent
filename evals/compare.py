"""Compare an eval run with the baseline and the thresholds; write a Markdown score table.

    uv run python -m evals.compare check --results evals/results/<run>.json [--markdown out.md]
    uv run python -m evals.compare make-baseline --results <full run>.json --suite regression \
        --out evals/baselines/iteration-1-regression.json

`check` exits 1 if any hard gate failed or any metric fell below its floor in
evals/thresholds.yaml. Floors start at baseline minus a small budget for model
non-determinism and are only ever raised (ratcheted), never lowered.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from evals.items import regression_ids
from evals.run import GATES, summarise

EVALS_DIR = Path(__file__).resolve().parent
THRESHOLDS = EVALS_DIR / "thresholds.yaml"


def _fmt(v: float | None) -> str:
    return "n/a" if v is None else f"{v:.3f}"


def check(results_path: Path, markdown: Path | None) -> int:
    run = json.loads(results_path.read_text("utf-8"))
    cfg = yaml.safe_load(THRESHOLDS.read_text("utf-8"))
    suite = run["meta"]["suite"]
    spec = cfg["suites"].get(suite)
    if spec is None:
        print(f"No thresholds for suite {suite!r}", file=sys.stderr)
        return 1
    baseline = json.loads((EVALS_DIR.parent / spec["baseline"]).read_text("utf-8"))["summary"]
    now = run["summary"]

    failed = False
    lines = [
        f"### Eval: `{suite}` suite ({now['overall']['n']} items)",
        "",
        f"Model `{run['meta']['answer_model']}` · prompt `{run['meta']['prompt_version']}` · "
        f"KB `{run['meta']['kb_version']}` · baseline `{spec['baseline']}`",
        "",
        "| Hard gate | Failures | Status |",
        "|---|---|---|",
    ]
    for g in GATES:
        n = now["hard_gate_failures"][g]
        failed |= n > 0
        lines.append(f"| {g} | {n} | {'❌ BLOCKS MERGE' if n else '✅'} |")

    lines += [
        "",
        "| Metric (overall) | Baseline | This run | Floor | Status |",
        "|---|---|---|---|---|",
    ]
    for metric, floor in spec["floors"].items():
        b, v = baseline["overall"].get(metric), now["overall"].get(metric)
        below = v is not None and v < floor
        failed |= below
        status = (
            "❌ below floor"
            if below
            else ("⬆️" if b is not None and v is not None and v > b else "✅")
        )
        lines.append(f"| {metric} | {_fmt(b)} | {_fmt(v)} | {floor:.3f} | {status} |")

    lines += [
        "",
        "<details><summary>By suite</summary>",
        "",
        "| Suite | n | hit@k | MRR | must_include | outcome | cited |",
        "|---|---|---|---|---|---|---|",
    ]
    for s, m in now["by_suite"].items():
        lines.append(
            f"| {s} | {m['n']} | {_fmt(m['retrieval_hit_at_k'])} | {_fmt(m['retrieval_mrr'])} | "
            f"{_fmt(m['must_include'])} | {_fmt(m['outcome_correct'])} | "
            f"{_fmt(m['cited_expected_doc'])} |"
        )
    lines += [
        "",
        "</details>",
        "",
        f"Tokens: {now['tokens']['input']:,} in / {now['tokens']['output']:,} out · "
        f"p95 latency {now['p95_latency_ms']} ms",
        "",
        "**Result: " + ("❌ FAILED, do not merge" if failed else "✅ passed") + "**",
    ]
    text = "\n".join(lines) + "\n"
    print(text)
    if markdown:
        markdown.write_text(text, "utf-8")
    return 1 if failed else 0


def make_baseline(results_path: Path, suite: str, out: Path) -> int:
    run = json.loads(results_path.read_text("utf-8"))
    if suite != "regression":
        raise SystemExit("only 'regression' subsets are supported")
    ids = regression_ids()
    subset = [r for r in run["results"] if r["id"] in ids]
    meta = {**run["meta"], "suite": suite, "derived_from": results_path.name}
    out.write_text(
        json.dumps({"meta": meta, "summary": summarise(subset)}, indent=2) + "\n", "utf-8"
    )
    print(f"Wrote {out} from {len(subset)} of {len(run['results'])} results")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(
            encoding="utf-8"
        )  # the table uses emoji; Windows consoles default to cp1252
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--results", type=Path, required=True)
    c.add_argument("--markdown", type=Path)
    m = sub.add_parser("make-baseline")
    m.add_argument("--results", type=Path, required=True)
    m.add_argument("--suite", default="regression")
    m.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.cmd == "check":
        return check(args.results, args.markdown)
    return make_baseline(args.results, args.suite, args.out)


if __name__ == "__main__":
    sys.exit(main())
