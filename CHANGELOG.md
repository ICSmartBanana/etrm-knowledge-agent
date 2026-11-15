# Changelog

Every change to prompts, models, retrieval settings or knowledge bases gets an entry here (brief §7). The M3 governance check will enforce this.

## [Unreleased] - M2 baseline agent

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
