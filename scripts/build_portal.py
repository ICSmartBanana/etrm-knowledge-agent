"""Build the static demo portal (GitHub Pages) from the repo.

    uv run python scripts/build_portal.py --out build/portal --api-url https://<space>.hf.space

Writes the static app (portal/*.html, *.css, *.js) and its data:
- clients.json: the three client tenants plus the shared consultancy base
- docs.json: every knowledge-base document, with PII masked exactly as at ingestion
- recorded-answers.json, history.json: real eval answers and score history (portal/data/)
- report.md: the iteration-1 eval report
- config.json: the backend URL for live chat (empty means recorded answers only)

Fails if any PII is found in what would be published.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.pii import find_pii, mask  # noqa: E402
from app.tenancy import CLIENT_TENANTS, DISPLAY_NAMES  # noqa: E402
from datagen.spec import CORPUS_DIR, load_all  # noqa: E402

REPO = "https://github.com/ICSmartBanana/etrm-knowledge-agent"
SHARED = "consultancy"


def documents() -> list[dict[str, object]]:
    docs = []
    for path in sorted(CORPUS_DIR.rglob("*.md")):
        _, meta, body = path.read_text("utf-8").split("---\n", 2)
        m = yaml.safe_load(meta)
        docs.append(
            {
                "doc_id": m["doc_id"],
                "tenant_id": m["tenant_id"],
                "title": m["title"],
                "doc_type": m.get("doc_type"),
                "data_class": m["data_class"],
                "status": m["status"],
                "effective_date": str(m.get("effective_date", "")),
                "supersedes": m.get("supersedes"),
                "contradicts": m.get("contradicts"),
                "body": mask(body),
                "source": f"{REPO}/blob/main/{path.relative_to(ROOT).as_posix()}",
            }
        )
    return docs


def clients() -> list[dict[str, str]]:
    specs = load_all()
    out = [
        {
            "id": t,
            "name": DISPLAY_NAMES[t],
            "company": specs[t].company_name,
            "platform": specs[t].platform,
            "profile": specs[t].profile,
        }
        for t in CLIENT_TENANTS
    ]
    s = specs[SHARED]
    out.append(
        {
            "id": SHARED,
            "name": f"Shared ({s.company_name})",
            "company": s.company_name,
            "platform": s.platform,
            "profile": s.profile,
        }
    )
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Build the static demo portal.")
    p.add_argument("--out", type=Path, default=ROOT / "build" / "portal")
    p.add_argument("--api-url", default="", help="live chat backend; empty = recorded only")
    args = p.parse_args()

    out: Path = args.out
    if out.exists():
        shutil.rmtree(out)
    (out / "data").mkdir(parents=True)
    for f in (ROOT / "portal").iterdir():
        if f.is_file():
            shutil.copy(f, out / f.name)

    docs = documents()
    recorded = json.loads((ROOT / "portal" / "data" / "recorded-answers.json").read_text("utf-8"))
    published = {
        "clients.json": clients(),
        "docs.json": docs,
        "recorded-answers.json": recorded,
        "history.json": {
            **json.loads((ROOT / "portal" / "data" / "history.json").read_text("utf-8")),
            "floors": {
                s: v.get("floors") or {}
                for s, v in yaml.safe_load((ROOT / "evals" / "thresholds.yaml").read_text("utf-8"))[
                    "suites"
                ].items()
            },
        },
        "config.json": {"apiUrl": args.api_url.rstrip("/"), "repo": REPO},
    }
    leaks = [(d["doc_id"], hit) for d in docs for hit in find_pii(str(d["body"]))] + [
        (a["id"], hit) for a in recorded["answers"] for hit in find_pii(a["answer"])
    ]
    if leaks:
        print(f"PII found, not publishing: {leaks[:5]}", file=sys.stderr)
        return 1
    for name, data in published.items():
        (out / "data" / name).write_text(json.dumps(data, ensure_ascii=False), "utf-8")
    shutil.copy(ROOT / "docs" / "evals" / "iteration-1-report.md", out / "data" / "report.md")
    print(f"Portal built in {out}: {len(docs)} documents, {len(recorded['answers'])} answers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
