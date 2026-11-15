# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This is a **pre-code repository** (milestone M0). The only content so far is the brief and plan in `docs/brief/`:

- `docs/brief/requirements-v0.1.docx`: the requirements brief (FR1–FR7, eval sets, CI gates, governance pack). It's the source of truth for scope.
- `docs/brief/implementation-plan.md`: the chosen stack, the proposed repo layout, the milestones M0–M6 with "done when" criteria, and the cost-control rules.

## Commands

The project uses `uv` with Python 3.12 (pinned in `.python-version`). Dependencies are locked in `uv.lock`.

```bash
uv sync                                   # install deps into .venv
uv run pytest                             # all tests (offline, no API calls)
uv run pytest tests/data/test_corpus.py -k a-002   # a single test / single doc
uv run ruff check . && uv run ruff format --check .
uv run mypy datagen
uv run python -m datagen.generate         # generate only missing corpus docs (calls Claude Haiku)
uv run python -m datagen.generate --force --tenant clan_b   # regenerate one tenant (costs API calls)
```

Still to come: Bandit, pip-audit, Gitleaks, Promptfoo (Node), Ragas, and `docker compose up` for Postgres, the API and the UI.

## Synthetic data (M1)

- `data/spec/<tenant>.yaml` is the ground truth. `[[key values]]` in facts must appear verbatim in the generated doc. See `data/spec/README.md`.
- `datagen/` generates `data/synthetic/<tenant>/<doc_id>.md` (YAML front matter carrying `tenant_id`, `data_class`, `status`, and `supersedes`/`contradicts`, then a Markdown body). It also writes `data/pii_registry.json` and `data/canaries.json`.
- The corpus is **committed and frozen**. Don't regenerate it unless the spec changes. After any regeneration, rerun `tests/data/test_corpus.py`, which validates every doc against its spec and checks that no doc names another tenant, carries its canary or PII, or contains invented PII.
- Messy data is deliberate (superseded versions, contradictions, near-duplicates, the injected instruction `INJECTION-TEST-0001` in `b-006`). Don't "fix" it. `docs/governance/data-source-register.md` lists it all.

Scope order: finish M0–M4 (research → synthetic data → baseline agent → CI/CD → governance) before any optimisation. Latency tuning, fine-tuning, and real client data are non-goals for iteration 1.

## What is being built

The project is a multi-tenant RAG chatbot. It's one codebase and one agent image serving three fictional ETRM clients plus a shared consultancy knowledge base. All data is synthetic:

- `clan_a`: gas and power utility (Allegro-style platform)
- `clan_b`: refined products trader. It deliberately overlaps with A on gas scheduling and with C on settlement and invoicing, with *different* facts.
- `clan_c`: agricultural and soft commodities trader
- `consultancy`: playbooks, runbooks, and checklists, visible to every client

The overlapping topics exist on purpose to tempt the agent into blending clients' answers. The main thing the POC proves is that it never does.

## Architecture invariants (must hold in all code)

These come from the brief and the plan. A change that weakens any of them is a defect, even if the tests pass.

1. **Tenant isolation is enforced at the data layer, never by the prompt.** Retrieval requires a `TenantContext` built only from the authenticated (simulated-login) session. No code path may derive a tenant from user text. SQL always filters `tenant_id IN (:tenant, 'consultancy')`. Postgres Row-Level Security, keyed on a per-request session setting, is the second layer of defence.
2. **Every chunk carries `tenant_id` and `data_class`.** `data_class` is one of `public`, `inference_only`, `insight`, or `pii`. Chunks also carry `kb_version`.
3. **PII handling.** PII is masked at ingestion. The output guard blocks PII regex matches and any match from the seeded registry (`data/pii_registry.json`). PII is redacted before anything goes to Langfuse traces or logs.
4. **Inference-only content is never quoted.** It is passed to the model in a separate tagged context block, and the output checker blocks verbatim n-gram overlap with it.
5. **Cite or abstain.** Every answer cites its source documents. If retrieval scores are below the threshold, the agent says it doesn't know. It also refuses out-of-scope topics, never reveals the system prompt, and always shows an AI disclosure notice.
6. **Traceability.** Every request is traced with client_id, the retrieved chunks and their scores, the model, `prompt_version`, and `kb_version`. Prompts are versioned files under `prompts/`.
7. **Swappable providers.** The embedder (local `fastembed` bge-small) and the LLM sit behind interfaces so Azure OpenAI can replace them later.

## Evaluation and CI rules

- Every change to a prompt, model, retrieval setting, or knowledge base must produce an eval score report before it merges.
- **The leakage and PII eval sets are hard gates: zero failures.** Quality thresholds are set from the first baseline (`evals/baselines/iteration-1.json`) and then only ratcheted upward.
- PRs run only the frozen **regression** subset, to save API cost. The full suite runs weekly or on demand. Generated eval sets are generated once, reviewed, and committed, never regenerated on each run.
- A governance check fails if `prompts/`, `data/`, the model config, or the retrieval config changes without a matching docs or CHANGELOG entry.
- Repos are private on a free GitHub plan, so branch protection is not enforced. The working rule is: **never merge a red PR**.

## Models and cost

- Pin model IDs. Use `claude-sonnet-5-5` for agent answers and `claude-haiku-5-5` for bulk work: synthetic-data and eval-set generation, and acting as the Ragas judge.
- Use prompt caching on the system prompt and the eval rubrics.
- Secrets live in `.env` (git-ignored): `ANTHROPIC_API_KEY`, and later `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_HOST`.

## Environment notes

- The machine is Windows with 7.8 GB RAM and Docker capped at about 4 GB. Don't add self-hosted heavy services: use Langfuse Cloud (EU region), not a self-hosted Langfuse.
- The C: drive is nearly full. Keep venvs, caches, and Docker data on D:.
- Azure is deferred until M6.

## Related repos

- `agent-standards`: a separate repo for the Agent Building Standards Pack (principles, review gates, Claude Code skills). It lives outside this repo by design, so don't put standards-pack content here.
- `agent-project-template`: will be extracted from this repo at the end of M4. Don't create it earlier.
