# Changelog

Every change to prompts, models, retrieval settings or knowledge bases gets an entry here (brief §7). The M3 governance check will enforce this.

## [Unreleased]

### Added (hosted demo)
- A portal on GitHub Pages (`portal/`, built by `scripts/build_portal.py`). It has a client switcher, each client's own documents (PII masked as at ingestion), live chat with clickable citations, the 242 recorded eval answers, an agent report with score history and improvements, and links to all docs and repos. The build fails if any PII would be published.
- A live backend on a Hugging Face Space (`deploy/hf-space/`): Postgres + pgvector, ingest and the API in one container, deployed by `.github/workflows/deploy.yml` after an image smoke test (health, limits, CORS, one real answer).
- `ingest` refuses to run when it finds no documents. The Space image was first built without the corpus (the root `.dockerignore` excludes it) and quietly served an empty knowledge base; `deploy/hf-space/Dockerfile.dockerignore` now includes it.
- The backend deploy is switched on by the repo variable `DEMO_BACKEND=hf-space`, since Docker Spaces need Hugging Face PRO. The portal publishes even without it, in recorded-answers mode.
- The API refuses POSTs carrying a foreign `Origin` header. The Hugging Face proxy echoes any origin in its CORS headers, so the browser-level restriction is now enforced in the app, and the smoke test checks it.
- API limits for the public demo, all off by default (`app/api/limits.py`): a shared daily question allowance reset at 00:00 UTC and shown in the UI (`GET /quota`, `quota` in every chat response), a per-visitor rate limit, a question-length cap, CORS limited to the portal origin, and a bounded session store.

### Added (easy local run)
- `docker compose up --build` now does everything: a one-shot `ingest` service loads the knowledge base before the API starts, so reviewers need only Git, Docker Desktop and an Anthropic key.
- `docs/RUN-LOCALLY.md`: a step-by-step guide covering tool installs, Anthropic and Langfuse keys, the `.env` file, what to try, and troubleshooting.
- Host ports are configurable (`ETRM_DB_PORT`, `ETRM_API_PORT`, `ETRM_UI_PORT`), and `.env.example` ships working local database passwords.

### Fixed
- Embedding uses batches of 16 instead of fastembed's default 256. Ingest stalled at the 1 GB container memory limit. The vectors are unchanged.

### Added (M4 governance pack)
- `docs/governance/`: risk register (12 risks, each with an owner, a mitigation and covering tests), model card (narrative; the facts stay generated), human-oversight note, incident process, regulatory register (EU, US federal and states, UK, Australia, India, with review dates), and a README index mapped to the NIST AI RMF functions.
- `tests/governance/test_registers.py`: fails if a risk's covering test, gate, eval suite or CI job no longer exists, if a risk or region that the brief requires is missing, or if a regulatory row's review dates are invalid.
- `tests/api/test_api.py::test_abstains_without_calling_the_model_when_retrieval_is_weak`: the cite-or-abstain path (risk R4) had no direct test.
- The UI shows each answer's trace ID, so users can quote it when they report a problem (incident process).
- `scripts/gen_docs.py` copies `docs/` into the `governance-docs` artifact in the repo layout, so the pack's relative links resolve there too.

### Added (M3 CI/CD)
- GitHub Actions:
  - `ci.yml`: lint, types, tests with Postgres and isolation tests, Bandit, pip-audit, Semgrep, Gitleaks, Trivy, governance check, generated docs
  - `eval.yml`: regression eval gate with a PR score comment
  - `weekly.yml`: full eval suite and image scan
- `evals/thresholds.yaml`: metric floors (baseline minus a small budget, ratchet only) and `evals/compare.py`, which gates a run and writes the score table.
- `evals/baselines/iteration-1-regression.json`: the regression-suite baseline, derived from the iteration-1 full run (same answers, no new model calls).
- `scripts/governance_check.py` and a PR template: governed areas need CHANGELOG (and, for data, data-register) updates.
- `scripts/gen_docs.py`: model card, data-source register, eval report and changelog built from the repo.
- `.pre-commit-config.yaml` with gitleaks and ruff hooks.

### Changed
- The Postgres healthcheck now waits on TCP, so `docker compose up --wait` returns only after `db/init` has finished.
- The UI rejects a non-http(s) `ETRM_API_URL` (Bandit B310).
- The image installs Debian security updates on top of `python:3.12-slim`, which clears two HIGH zlib CVEs (CVE-2026-76844, CVE-2026-85091) that Trivy flagged.

### Fixed
- Golden eval set: regenerated 24 of 131 questions that contained the generator's drafting text (13 also contained the expected answer). Same ids, expected values and source docs. The question generator now uses structured output, and a test rejects malformed golden questions. The iteration-1 baseline was re-run: hard gates still 0, golden exact-value accuracy 0.93 → 0.92.

### Added
- Langfuse Cloud (EU) trace export alongside the local JSONL traces: retrieval, generation (tokens, USD cost) and guard steps, PII-masked, with no document text, and only the app's own spans exported.
- Cost per query (`cost_usd`) in every trace, from pinned prices in `app/config.py`.

## M2 baseline agent (PR #3)

### Added
- Postgres 16 + pgvector schema with row-level security (`db/init/01_schema.sh`). Tables are owned by a non-superuser role (`etrm_schema`) so that FORCE RLS binds the owner too.
- Ingest CLI (`ingest/`): heading-based chunking (max 1200 chars), PII masking, `BAAI/bge-small-en-v1.5` embeddings, a versioned `kb_version`.
- Tenant-filtered retrieval (top-k 6, exact scan, abstain below a cosine score of 0.60).
- System prompt **v1** (`prompts/system_v1.md`).
- Answer model **`claude-sonnet-5-5`** at effort `low`, with structured JSON output and server-side refusal fallback (`fallbacks: "default"`).
- Output guard: PII masking, inference-only and system-prompt n-gram blocks, citation filtering.
- FastAPI service with simulated login, a Streamlit UI with an AI disclosure banner, and local JSONL tracing.
- Eval sets v1: golden (131), overlap (20), leakage (42), PII/inference-only (21), adversarial (28), and a frozen regression subset (105). Deterministic hard gates run on every answer.
- Baseline scores: `evals/baselines/iteration-1.json`.

## M1 - synthetic data (PR #2)
- 49 synthetic documents across four knowledge bases, generated from `data/spec/` with `claude-haiku-5-5`.

## M0 - research and stack (PR #1)
- Research notes, use-case classification, and ADR 0001.
