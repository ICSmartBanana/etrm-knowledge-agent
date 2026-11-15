# Model card: ETRM knowledge agent (POC)

| | |
|---|---|
| Status | **Draft, awaiting review** |
| Version | 0.1 (15 Nov 2026, milestone M4) |
| Owner | Parag (POC owner) |
| Review | On every change to the model, prompt, retrieval settings or knowledge bases (enforced by the governance check), and monthly with the risk register |

This card describes a **system**: an agent built on a third-party model, not a model we trained. It follows the structure of Mitchell et al. (2019), with "training data" replaced by "knowledge bases" (research note 1).

It has two parts:

- **This file:** purpose, intended use, limits and reasoning. It changes only when someone decides something.
- **The generated card**, `model-card.md` in the `governance-docs` CI artifact (`uv run python scripts/gen_docs.py`). It holds the facts that change with the code: model IDs, prompt version, retrieval settings, baseline eval scores, thresholds and the full change history. It is rebuilt on every PR, so it can't go stale.

Where the two disagree, the generated card is right about the facts, and this file should be updated.

## Purpose and intended use

Answers questions from staff of three fictional ETRM clients about their own trading operations: contracts, system configuration, gas and power scheduling, settlement and invoicing, and runbooks. It uses only that client's knowledge base plus the consultancy's shared guidance, and cites the documents it used.

- **Intended users:** client operations, IT and business-analyst staff, and consultancy staff. Professionals, logged in, using it as a lookup aid.
- **Intended setting:** a proof of concept on synthetic data, to prove that one shared agent can serve several clients without mixing their information.
- **EU AI Act tier:** limited risk, with the Art. 50(1) disclosure duty ([use-case classification](use-case-classification.md)).

## Out of scope

- Decisions about individuals (employment, credit, access to services).
- Acting on any system. The agent has no tools and can't change trades, nominations, schedules or configuration. Giving it tools is a re-classification trigger.
- Real client or personal data. That needs the open questions in brief §14 answered first: approved provider, data-processing location, ISO 27001 owner.
- General-purpose chat, coding help, or questions about other companies. These are refused.

## System overview

| Component | Choice | Notes |
|---|---|---|
| Answer model | Anthropic Claude Sonnet, pinned ID in `app/config.py` | Third-party general-purpose model through the API. Not trained or fine-tuned on any client data. |
| Bulk model | Anthropic Claude Haiku, pinned ID in `datagen/generate.py` and `evals/build_golden.py` | Synthetic-data and eval-set generation only. Never answers users. |
| Embeddings | `fastembed` bge-small, run locally | No document text leaves the machine for embedding. |
| Retrieval | Postgres + pgvector, tenant pre-filter plus FORCE row-level security | See the isolation design in [ADR 0001](../decisions/0001-stack.md). |
| Output guard | PII masking, inference-only and system-prompt n-gram blocks, citation filter | `app/guard.py` |
| Tracing | Local JSONL plus Langfuse Cloud (EU) | IDs and scores only, never document text; PII masked twice. |

## Knowledge bases

Four synthetic knowledge bases (Clan A, B, C and the shared consultancy base) with four data classes: `public` and `insight` (may be quoted), `inference_only` (may inform an answer, never quoted), and `pii` (contact lists, never sent to the model). Sources, owners, sensitivity, retention and the deliberate messiness (superseded versions, contradictions, near-duplicates, one injected instruction) are in the [data-source register](data-source-register.md).

## Evaluation

The agent is scored on five frozen sets: golden (exact values), overlap (same question, different correct answer per client), leakage, PII and inference-only, and adversarial. Four **hard gates** are checked on every answer with zero tolerance: leakage, PII, inference-only quotation, and system prompt or injection. Quality metrics have floors that only ever go up.

- Baseline and analysis: [iteration-1 report](../evals/iteration-1-report.md). Iteration 1 had **zero** hard-gate failures.
- Current numbers: the generated card and the score table that the `eval` workflow posts on every PR that can change answers.

## Known limitations

These are the limitations that matter most when relying on an answer. The generated card lists the technical ones.

- **It can be wrong.** Quality metrics are exact-match checks against expected values; there is no LLM-judged faithfulness metric yet (risk R4). Users are told this on every answer.
- **It doesn't know what isn't in the documents.** When retrieval finds nothing relevant it says so, but a relevant-looking chunk with the wrong value can still produce a confident wrong answer.
- **PII detection is pattern-based.** Regexes plus a seeded registry catch the synthetic PII. Real names in real documents would need NER (risk R2).
- **Stale documents.** It prefers current over superseded documents, but only as well as the documents' `status` field is maintained (risk R6).
- **One language.** English only; not evaluated on other languages.

## Data handling

- Client data is never used to train or fine-tune any model (brief §8).
- PII is masked at ingestion, blocked at output and redacted from traces.
- Each client's data can be deleted without touching the others: remove its folder and its rows, then re-ingest.

## Human oversight and incidents

See the [human-oversight note](human-oversight.md) and the [incident process](incident-process.md).

## Change history

The full, authoritative history is [`CHANGELOG.md`](../../CHANGELOG.md), copied into the generated card. Milestones so far: M0 research and ADR, M1 synthetic data, M2 baseline agent with Langfuse tracing, M3 CI/CD gates, M4 governance pack (this card).

## Sign-off

| Role | Name | Date | Decision |
|---|---|---|---|
| Reviewer | Parag | | |
