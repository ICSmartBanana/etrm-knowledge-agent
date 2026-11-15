"""Governance check for PRs (brief §7): changes to governed areas need matching documentation.

    python scripts/governance_check.py origin/main

Fails (exit 1) when a PR changes a governed area without updating the docs it requires.
Standard library only, so it runs without installing the project.
"""

from __future__ import annotations

import fnmatch
import shutil
import subprocess  # nosec B404
import sys

# (area name, file patterns, documentation that must change alongside)
RULES: list[tuple[str, list[str], list[str]]] = [
    ("system prompt", ["prompts/*"], ["CHANGELOG.md"]),
    (
        "model or retrieval configuration",
        ["app/config.py", "app/retrieval.py", "app/llm.py", "ingest/chunking.py"],
        ["CHANGELOG.md"],
    ),
    (
        "knowledge base",
        ["data/spec/*", "data/synthetic/*"],
        ["CHANGELOG.md", "docs/governance/data-source-register.md"],
    ),
    ("eval sets or baselines", ["evals/sets/*", "evals/baselines/*"], ["CHANGELOG.md"]),
    (
        "guardrails",
        ["app/guard.py", "app/pii.py", "app/tenancy.py", "db/init/*"],
        ["CHANGELOG.md"],
    ),
]


def changed_files(base: str) -> list[str]:
    git = shutil.which("git")
    if git is None:
        raise SystemExit("git not found on PATH")
    out = subprocess.run(  # noqa: S603  # nosec B603
        [git, "diff", "--name-only", f"{base}...HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def violations(files: list[str]) -> list[str]:
    def touched(patterns: list[str]) -> list[str]:
        return [f for f in files if any(fnmatch.fnmatch(f, p) for p in patterns)]

    out = []
    for area, patterns, required in RULES:
        hits = touched(patterns)
        missing = [r for r in required if r not in files]
        if hits and missing:
            out.append(
                f"{area} changed ({', '.join(hits[:3])}{'...' if len(hits) > 3 else ''}) "
                f"but {', '.join(missing)} was not updated"
            )
    return out


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    files = changed_files(base)
    problems = violations(files)
    print(f"{len(files)} changed files checked against {len(RULES)} governance rules.")
    for p in problems:
        print(f"::error title=Governance check::{p}")
    if problems:
        print("Update the listed documents (see CLAUDE.md, 'Evaluation and CI rules').")
        return 1
    print("Governance check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
