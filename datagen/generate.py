"""Generate the synthetic corpus from data/spec/*.yaml with Claude Haiku.

Usage:
    uv run python -m datagen.generate            # generate missing docs only
    uv run python -m datagen.generate --force    # regenerate everything (costs API calls)
    uv run python -m datagen.generate --tenant clan_a

The generated corpus is committed and frozen; regenerate only on purpose.
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import anthropic
import yaml
from dotenv import load_dotenv

from datagen import inserts
from datagen.spec import (
    CORPUS_DIR,
    REPO_ROOT,
    DocSpec,
    TenantSpec,
    derived_doc,
    load_all,
    strip_brackets,
)
from datagen.validate import check_doc

MODEL = "claude-haiku-5-5"
MAX_ATTEMPTS = 3

SYSTEM_PROMPT = """\
You write realistic internal business documents for a fictional company. The documents form a \
synthetic test corpus for a retrieval-augmented chatbot, so precision matters more than style.

Rules:
- Output only the document body in Markdown. Start with a level-1 heading that is the title.
- Use at least two level-2 headings.
- Include every listed fact. Reproduce each value marked as a key value exactly as given, \
character for character.
- Mention people, email addresses, phone numbers or trader IDs only when they are given to you, \
and copy them exactly. Never invent any.
- Name no company, platform, hub, pipeline or product other than those given to you.
- Do not add facts that contradict the ones given. You may add plausible, generic procedural \
detail that has no numbers, dates or deadlines.
- Length: 300 to 550 words (a contact list can be shorter).
"""

CLASS_GUIDANCE = {
    "public": "An ordinary internal document that staff may quote.",
    "inference_only": (
        "A confidential internal analysis. Label it 'Internal - not for distribution' at the top."
    ),
    "insight": "A short lessons-learned summary with conclusions and recommendations.",
    "pii": "A contact list: a Markdown table with name, role, email, phone and trader ID columns.",
}


def build_prompt(tenant: TenantSpec, doc: DocSpec) -> str:
    facts = "\n".join(f"- {strip_brackets(f)}" for f in doc.facts)
    keys = "\n".join(f"- {k}" for k in doc.keys) or "- (none)"
    people = "\n".join(
        f"- {tenant.pii[p].kind}: {tenant.pii[p].value} ({tenant.pii[p].role})" for p in doc.pii
    )
    notes = []
    if doc.status == "superseded":
        notes.append("This is an old policy version. Write it as it was when it applied.")
    if doc.contradicts:
        notes.append(
            "This is an older informal document. Keep its values even though they are dated."
        )
    return f"""Company: {tenant.company_name}
Company profile: {tenant.profile}

Document title: {doc.title}
Document type: {doc.doc_type}
Effective date: {doc.effective_date}
Kind of document: {CLASS_GUIDANCE[doc.data_class]}
{chr(10).join(notes)}

Facts to include:
{facts}

Key values to reproduce exactly:
{keys}

People and contact details to include exactly (and no others):
{people or "- none: mention no people by name"}
"""


def front_matter(tenant: TenantSpec, doc: DocSpec, **extra: object) -> str:
    meta = {
        "doc_id": doc.id,
        "tenant_id": tenant.tenant_id,
        "title": doc.title,
        "doc_type": doc.doc_type,
        "data_class": doc.data_class,
        "topic": doc.topic,
        "overlap": doc.overlap,
        "version": doc.version,
        "status": doc.status,
        "effective_date": doc.effective_date,
        "supersedes": doc.supersedes,
        "contradicts": doc.contradicts,
        "generated_by": MODEL,
        **extra,
    }
    meta = {k: v for k, v in meta.items() if v is not None}
    return "---\n" + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True) + "---\n\n"


def _call(client: anthropic.Anthropic, prompt: str) -> str:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        output_config={"effort": "low"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    if resp.stop_reason != "end_turn":
        raise RuntimeError(f"unexpected stop_reason {resp.stop_reason}")
    return "".join(b.text for b in resp.content if b.type == "text").strip() + "\n"


def generate_doc(
    client: anthropic.Anthropic, tenant: TenantSpec, doc: DocSpec, specs: dict[str, TenantSpec]
) -> str:
    prompt = build_prompt(tenant, doc)
    problems: list[str] = []
    for _ in range(MAX_ATTEMPTS):
        attempt_prompt = prompt
        if problems:
            attempt_prompt += "\nYour previous draft had these problems; fix them:\n" + "\n".join(
                f"- {p}" for p in problems
            )
        body = _call(client, attempt_prompt)
        if doc.injection:
            body = inserts.insert_after_first_section(body, inserts.INJECTION_BLOCK)
        if doc.canary:
            body += inserts.canary_line(tenant.canary)
        problems = check_doc(body, doc, tenant, specs)
        if not problems:
            return front_matter(tenant, doc) + body
    raise RuntimeError(f"{doc.id}: still invalid after {MAX_ATTEMPTS} attempts: {problems}")


def doc_path(tenant_id: str, doc_id: str) -> Path:
    return CORPUS_DIR / tenant_id / f"{doc_id}.md"


def split_doc(text: str) -> tuple[dict[str, object], str]:
    """Split a corpus file into (front matter, body)."""
    _, meta, body = text.split("---\n", 2)
    return yaml.safe_load(meta), body.lstrip("\n")


def build_derived(tenant: TenantSpec) -> None:
    for d in tenant.derived:
        src_text = doc_path(tenant.tenant_id, d.source).read_text(encoding="utf-8")
        _, src_body = split_doc(src_text)
        spec = derived_doc(tenant, d)
        body = inserts.near_duplicate(src_body, spec.title)
        out = front_matter(tenant, spec, near_duplicate_of=d.source, generated_by="code")
        doc_path(tenant.tenant_id, d.id).write_text(out + body, encoding="utf-8")


def write_registries(specs: dict[str, TenantSpec]) -> None:
    pii = {
        t.tenant_id: [{"id": p.id, "kind": p.kind, "value": p.value} for p in t.pii.values()]
        for t in specs.values()
    }
    canaries = {t.tenant_id: t.canary for t in specs.values()}
    data = REPO_ROOT / "data"
    (data / "pii_registry.json").write_text(
        json.dumps(pii, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (data / "canaries.json").write_text(json.dumps(canaries, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the synthetic corpus.")
    parser.add_argument("--force", action="store_true", help="regenerate existing documents")
    parser.add_argument("--tenant", choices=list(load_all()), help="only this tenant")
    args = parser.parse_args()

    load_dotenv()
    client = anthropic.Anthropic()
    specs = load_all()
    tenants = [specs[args.tenant]] if args.tenant else list(specs.values())

    jobs = []
    for t in tenants:
        (CORPUS_DIR / t.tenant_id).mkdir(parents=True, exist_ok=True)
        jobs += [(t, d) for d in t.docs if args.force or not doc_path(t.tenant_id, d.id).exists()]
    print(f"Generating {len(jobs)} documents with {MODEL}...")

    def run(job: tuple[TenantSpec, DocSpec]) -> str:
        t, d = job
        doc_path(t.tenant_id, d.id).write_text(generate_doc(client, t, d, specs), encoding="utf-8")
        return d.id

    failures = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(run, j) for j in jobs]
        for f in futures:
            try:
                print("  ok", f.result())
            except Exception as e:  # report every failure, keep the rest
                failures += 1
                print("  FAILED", e, file=sys.stderr)

    for t in tenants:
        build_derived(t)
    write_registries(specs)
    print(f"Done. {len(jobs) - failures} generated, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
