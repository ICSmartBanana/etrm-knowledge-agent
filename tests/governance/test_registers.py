"""The governance registers stay wired to the code (brief §8, research note 1).

Every risk must name an owner, a mitigation and covering tests that still exist, so renaming or
deleting a test can't silently leave a risk uncovered. Every regulatory row must carry valid
review dates. Offline: no database or API calls.
"""

from __future__ import annotations

import ast
import re
from datetime import date
from pathlib import Path

import pytest
import yaml

from evals.items import all_items

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "docs" / "governance"
REF = re.compile(r"`(pytest|gate|eval|ci):([^`]+)`")
GATES = {"leakage", "pii", "inference_only", "system_prompt_or_injection"}
# The risks brief §8 requires, matched case-insensitively against the risk column.
REQUIRED_RISKS = (
    "leakage",
    "pii",
    "hallucination",
    "prompt injection",
    "stale",
    "over-reliance",
    "vendor or model change",
)
REGIONS = ("EU", "US", "UK", "Australia", "India")


def _rows(doc: str, first_cell: str) -> list[list[str]]:
    lines = (GOV / doc).read_text("utf-8").splitlines()
    return [
        [c.strip() for c in line.strip().strip("|").split("|")]
        for line in lines
        if re.match(rf"^\|\s*{first_cell}\s*\|", line)
    ]


RISKS = _rows("risk-register.md", r"R\d+")
REGULATIONS = _rows("regulatory-register.md", r"(EU|US|UK|AU|IN)(-[A-Z0-9]+)+")


def _test_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text("utf-8"))
    return {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def _ci_jobs() -> set[str]:
    wf = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text("utf-8"))
    return set(wf["jobs"])


def test_registers_parse() -> None:
    assert len(RISKS) >= len(REQUIRED_RISKS)
    assert all(len(r) == 8 for r in RISKS), "risk rows must have 8 columns"
    assert REGULATIONS and all(len(r) == 10 for r in REGULATIONS), "regulatory rows: 10 columns"


def test_brief_risks_are_all_registered() -> None:
    text = " ".join(r[1].lower() for r in RISKS)
    assert [k for k in REQUIRED_RISKS if k not in text] == []


@pytest.mark.parametrize("row", RISKS, ids=[r[0] for r in RISKS])
def test_risk_has_owner_mitigation_and_live_covering_tests(row: list[str]) -> None:
    rid, _, _, _, owner, mitigation, covering, _ = row
    assert owner and mitigation, f"{rid}: owner and mitigation are required"
    refs = REF.findall(covering)
    assert refs, f"{rid}: no covering tests"
    suites = {i.suite for i in all_items()} | {"regression"}
    for kind, target in refs:
        if kind == "pytest":
            file, _, name = target.partition("::")
            path = ROOT / file
            assert path.is_file(), f"{rid}: {file} not found"
            assert name in _test_names(path), f"{rid}: {target} not found"
        elif kind == "gate":
            assert target in GATES, f"{rid}: unknown gate {target}"
        elif kind == "eval":
            assert target in suites, f"{rid}: unknown eval suite {target}"
        else:
            assert target in _ci_jobs(), f"{rid}: unknown CI job {target}"


def test_every_brief_region_is_in_the_regulatory_register() -> None:
    regions = " ".join(r[1] for r in REGULATIONS)
    assert [r for r in REGIONS if r not in regions] == []


@pytest.mark.parametrize("doc", sorted(GOV.glob("*.md")), ids=lambda p: p.name)
def test_relative_links_in_the_pack_resolve(doc: Path) -> None:
    # gen_docs.py ships docs/ in the repo layout, so links that resolve here resolve in the
    # governance-docs artifact too.
    links = re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", doc.read_text("utf-8"))
    local = [link for link in links if not re.match(r"[a-z]+:", link)]
    assert [link for link in local if not (doc.parent / link).exists()] == []


@pytest.mark.parametrize("row", REGULATIONS, ids=[r[0] for r in REGULATIONS])
def test_regulation_has_valid_review_dates(row: list[str]) -> None:
    last, nxt = date.fromisoformat(row[8]), date.fromisoformat(row[9])
    assert last <= nxt, f"{row[0]}: next review before last review"
    assert (nxt - last).days <= 92, f"{row[0]}: reviews must be at least quarterly"
