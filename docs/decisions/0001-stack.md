# ADR 0001: Stack, isolation design and budget

| | |
|---|---|
| Status | **Proposed, awaiting Parag's approval** (M0 is done once it's approved) |
| Date | 15 Nov 2026 |
| Inputs | [Requirements brief v0.1](../brief/requirements-v0.1.docx), [implementation plan](../brief/implementation-plan.md) §5, [M0 research notes](../research/README.md) |

## Context

The brief asks for a production-minded POC with strict client isolation, an eval-driven workflow and a total budget of $1–2k. The plan in `docs/brief/implementation-plan.md` §5 already proposes a stack. This ADR confirms it and records the changes the M0 research led to.

## Decision: stack

| Layer | Choice | Notes |
|---|---|---|
| Language and dependencies | Python 3.12, `uv` with a committed lockfile | uv installs 3.12 itself. The local system Python (3.13) isn't used. |
| API | FastAPI | |
| UI | Streamlit, with a simulated login dropdown (Clan A/B/C) | It can be swapped for React later. ESLint gets added then. |
| Vector store | Postgres 16 + pgvector (Docker locally; Azure Flexible Server in M6) | The same engine in both places, so nothing is rewritten for M6 |
| Embeddings | `fastembed` with `BAAI/bge-small-en-v1.5`, local CPU, behind an `Embedder` interface | Anthropic has no embeddings API. Azure OpenAI can be swapped in later. |
| LLM | Anthropic API, behind an `LLM` interface. Pinned IDs: `claude-sonnet-5-5` for answers, `claude-haiku-5-5` for data and eval generation and as the Ragas judge | Prompt caching on the system prompt and rubrics |
| Observability | Langfuse Cloud Hobby, EU region | PII redacted before sending |
| Evals | Ragas (quality metrics), Promptfoo (deterministic leakage and PII assertions) | Ragas version and judge model pinned in every baseline |
| CI | GitHub Actions: Ruff, mypy, pytest, Bandit, pip-audit, Gitleaks (CI and pre-commit), Trivy, Semgrep OSS, evals, doc generation | **SonarCloud dropped**: the repo is private and SonarCloud is paid for private repos (plan §3) |
| Local run | `docker compose up` (postgres, api, ui) | Docker capped at about 4 GB RAM |
| Hosting (M6) | Azure Container Apps Consumption (min replicas 0) + Postgres Flexible B1ms with a scheduled stop | See research note 6 |

## Decision: isolation design (refined by research note 3)

1. Retrieval takes a required `TenantContext`, built only from the session. Every SQL query filters `tenant_id IN (:tenant, 'consultancy')` **inside** the vector query (pre-filter, never post-filter).
2. **Postgres RLS** on chunk tables, with `FORCE ROW LEVEL SECURITY`. The API connects as a non-owner role without `BYPASSRLS`. The tenant is set with `SET LOCAL` inside each request's transaction, so it can't leak through pooled connections. No `SECURITY DEFINER` functions on chunk tables.
3. The ingest CLI uses a separate privileged role that the API never has.
4. **No ANN index at POC scale** (exact scan), which avoids per-tenant recall skew. Any index added in M5 must pass the per-tenant recall checks.
5. **Canary tests in CI:** each tenant's corpus contains a unique canary string. Every other tenant queries for it, at both the SQL layer and the full agent. Expected hits: zero.
6. Retrieved chunks go to the model inside a delimited data block that never carries instructions. Inference-only chunks go in a separately tagged block. The output guard (PII registry plus regex, n-gram overlap with inference-only text) runs on every answer.

## Decision: evaluation gates (refined by research note 4)

- **Hard gates, exactly zero failures:** leakage set, PII and inference-only set, and canary tests. These are deterministic string and n-gram checks with no LLM judge, so they're reproducible and free.
- **Quality gates:** a floor per metric (context precision, context recall, faithfulness, answer relevancy) **plus** a maximum drop against the stored baseline. Both get set after the M2 baseline and are only ever raised.
- PRs run the frozen regression subset. The full suite runs weekly.

## Budget

Prices weren't verified in M0, so the budget is set as **caps**, not estimates. Current prices need checking before topping up.

| Item | Cap / target | Control |
|---|---|---|
| Anthropic API, M1–M5 | **$50/month** workspace spend limit; expected well under that | Separate local and CI keys; Haiku for bulk work; PR evals on the regression subset only; generated eval sets frozen in the repo |
| Langfuse, GitHub, all CI tooling | $0 | Free tiers; private-repo Actions limit of 2,000 min/month |
| Azure, M6 only | Target **≤ $30/month**, budget alerts at 50% and 90% | Scale-to-zero apps; B1ms DB with a scheduled stop (Azure restarts a stopped server after 7 days) |
| **Total for the POC** | **< $400** at the caps above over about 3 months, well within the brief's $1–2k | |

## Consequences

- Dropping SonarCloud loses its quality-gate dashboard. Ruff (with complexity rules), Bandit and Semgrep cover most of the same checks. SonarQube Community in Docker is available for an occasional report.
- Branch protection can't be enforced on a free private repo, so "never merge a red PR" is a working rule, not a technical block.
- Langfuse Cloud (EU) and the Anthropic API mean data is processed by third parties. That's fine for synthetic data. It depends on open question 4 (limits on data-processing location) before any real data is used.

## Open items carried forward

1. Check the current Anthropic, Azure Container Apps and B1ms prices, and that pgvector is available on Azure Postgres, before M6.
2. Check Promptfoo's negated case-insensitive assertion (`not-icontains`) before writing the M2 suites.
3. Research the regulatory register for the US states, the UK, Australia and India (M4).
4. Open questions in brief §14: the approved model provider, an Azure subscription, data-processing location, and the standards-pack approver.

## Approval

| Role | Name | Date | Decision |
|---|---|---|---|
| Approver | Parag | | |
