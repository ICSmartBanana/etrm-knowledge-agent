# Risk register

| | |
|---|---|
| Status | **Draft, awaiting review** |
| Version | 0.1 (15 Nov 2026, milestone M4) |
| Owner | Parag (POC owner) |
| Review | Monthly (brief §8), and whenever a risk materialises or a covering test changes. Next review: **2026-12-15** |
| Framework | NIST AI RMF 1.0 (*Map* and *Manage*), with the generative-AI risks from NIST AI 600-1. Structured to feed an ISO 42001 risk process later; no conformity claimed. |

Every risk has an owner, a mitigation and the tests that cover it (brief §8). `tests/governance/test_registers.py` checks that each **Covering tests** reference still exists, so a renamed or deleted test fails CI instead of silently leaving a risk uncovered.

**Reference format** in the *Covering tests* column:

- `pytest:<file>::<test>`: a pytest test that runs offline or against the local database on every PR.
- `gate:<name>`: an eval hard gate in `evals/gates.py`, checked on **every** eval answer, with zero tolerance.
- `eval:<suite>`: an eval suite in `evals/sets/`, scored against the floors in `evals/thresholds.yaml`.
- `ci:<job>`: a job in `.github/workflows/ci.yml`.

**Scoring:** likelihood and impact are rated *Low*, *Medium* or *High* for the POC with synthetic data. *Residual* is the rating after the mitigation. The POC has one person in every role, so all owners are the POC owner. Production owners are listed where they would differ.

## Register

| ID | Risk | NIST AI 600-1 | Likelihood / impact (inherent) | Owner | Mitigation | Covering tests | Residual |
|---|---|---|---|---|---|---|---|
| R1 | **Cross-client leakage.** An answer to one client contains another client's content, for example on the overlapping gas-scheduling or settlement topics. | Data privacy; information security | High / High | Parag (production: platform owner) | The tenant comes only from the session (`TenantContext`, no text constructor). SQL pre-filters on `tenant_id`, and Postgres FORCE RLS on a per-transaction setting is a second, independent layer. The API role can't bypass RLS or write. Canary documents and the overlap set detect any blend. | `pytest:tests/isolation/test_tenant_isolation.py::test_canary_not_retrievable_by_other_tenant` · `pytest:tests/isolation/test_tenant_isolation.py::test_rls_hides_other_tenants_from_app_role_even_without_where` · `pytest:tests/isolation/test_tenant_isolation.py::test_interleaved_tenants_on_shared_pool_never_mix` · `pytest:tests/isolation/test_tenant_isolation.py::test_tenant_setting_does_not_leak_across_pooled_connections` · `pytest:tests/api/test_api.py::test_tenant_in_body_is_ignored` · `pytest:tests/unit/test_guard_pii.py::test_tenant_context_has_no_text_constructor` · `gate:leakage` · `eval:leakage` · `eval:overlap` | Low / High. Demonstrated in M3: a change that removed both layers was blocked by the tests, the governance check and the leakage gate (85 failures). |
| R2 | **PII exposure.** An answer, log or trace reveals a person's name, phone number, email or trader ID. | Data privacy | High / High | Parag (production: client data protection lead) | PII is masked at ingestion. Contact-list (`pii`-class) chunks never reach the model. The output guard masks regex matches and every value in the seeded registry. | `pytest:tests/isolation/test_tenant_isolation.py::test_ingested_chunks_contain_no_seeded_pii` · `pytest:tests/api/test_api.py::test_contact_lists_never_reach_the_model` · `pytest:tests/unit/test_guard_pii.py::test_mask_registry_and_patterns` · `pytest:tests/unit/test_guard_pii.py::test_guard_masks_pii_and_drops_bad_citations` · `gate:pii` · `eval:pii_inference` | Low / Medium. Regexes and a registry don't catch unseen names; production needs NER (model card, known limits). |
| R3 | **Inference-only content quoted.** Internal notes (credit observations, margin analysis) appear verbatim in an answer. | Data privacy; intellectual property | Medium / High | Parag | Inference-only chunks go to the model in a separate `<internal_context>` block with instructions not to quote them. The output guard withholds any answer with an 8-word verbatim overlap. | `pytest:tests/unit/test_guard_pii.py::test_guard_withholds_verbatim_inference_only_text` · `gate:inference_only` · `eval:pii_inference` | Low / Medium. Paraphrase is allowed by design; the guard blocks only verbatim quotation. |
| R4 | **Hallucination (confabulation).** The agent states a value that isn't in the client's documents, or cites a document that doesn't support it. | Confabulation | High / Medium | Parag | Cite or abstain: when the best retrieval score is below the threshold, the agent says it doesn't know and the model isn't called. The guard drops citations to documents that weren't retrieved. Golden-set exact-value checks catch wrong values. | `pytest:tests/api/test_api.py::test_abstains_without_calling_the_model_when_retrieval_is_weak` · `pytest:tests/unit/test_guard_pii.py::test_guard_masks_pii_and_drops_bad_citations` · `eval:golden` · `eval:regression` | Medium / Medium. Quality metrics are exact-match, not LLM-judged faithfulness; Ragas is still to come (M3 follow-up). |
| R5 | **Prompt injection and system-prompt extraction.** An instruction hidden in a document (`INJECTION-TEST-0001` in `b-006`) or typed by a user changes the agent's behaviour or reveals its system prompt. | Information security | Medium / Medium | Parag | Documents are passed as escaped, tagged data, and the system prompt says to treat them as data. The output guard withholds answers that echo the system prompt. The agent has no tools, so an injection can't trigger an action. | `pytest:tests/unit/test_guard_pii.py::test_guard_withholds_system_prompt_echo` · `gate:system_prompt_or_injection` · `eval:adversarial` | Low / Low, as long as the agent stays tool-less (see R11). |
| R6 | **Stale or contradictory knowledge.** The agent answers from a superseded policy or an informal document that contradicts the current one. | Confabulation; information integrity | Medium / Medium | Parag (production: each client's knowledge-base owner) | Every document carries `status` and `effective_date`, which are passed to the model. The prompt prefers current, formal documents and asks it to mention the conflict. Every knowledge-base change gets a new `kb_version` and triggers the regression evals. | `eval:adversarial` · `pytest:tests/data/test_corpus.py::test_messy_data_present` | Medium / Medium. Relies partly on the prompt. There is no automatic check that a knowledge base is up to date; that is a process control (data-source register, *last update* column). |
| R7 | **Over-reliance.** Users act on an answer without checking it, for example on a nomination deadline. | Human-AI configuration | Medium / Medium | Parag (production: deploying client) | A disclosure notice on every answer says it's an AI and can be wrong. Every answer cites its source documents so they can be checked. The agent can't act on any system. The human-oversight note sets when a person must check. | `pytest:tests/api/test_api.py::test_disclosure_on_every_answer` · `eval:golden` | Medium / Medium. Human behaviour can't be tested; reviewed through user feedback once traces carry it (M5). |
| R8 | **Vendor or model change.** The provider changes or retires the model, or someone swaps the model or prompt, and answer quality or safety drops unnoticed. | Value chain and component integration | Medium / High | Parag | Model IDs are pinned in `app/config.py`. Prompts are versioned files. Any change to them needs a CHANGELOG entry (governance check) and an eval score report against the frozen regression set before merging. The weekly full run catches drift between changes. | `ci:governance` · `eval:regression` · `gate:leakage` · `gate:pii` | Low / Medium. A retired model forces a change, but the change still goes through the gates. |
| R9 | **Sensitive data in traces.** Document text or PII leaves the machine in Langfuse traces or logs. | Data privacy | Medium / Medium | Parag | Traces carry document IDs and scores, never document text. PII is masked before writing, and a Langfuse `mask` hook masks again. Only the app's own spans are exported. | `pytest:tests/unit/test_tracing.py::test_record_has_fr6_fields_and_no_pii_or_doc_text` · `pytest:tests/unit/test_tracing.py::test_langfuse_mask_hook_masks_nested_strings` | Low / Low |
| R10 | **Security vulnerabilities and leaked secrets.** A vulnerable dependency or base-image package, or an API key committed to the repo. | Information security | Medium / High | Parag | Bandit, pip-audit, Semgrep and Gitleaks (full history) on every PR. Trivy on the image when it changes and weekly. Secrets only in `.env` and GitHub secrets. A pre-commit Gitleaks hook. | `ci:security` · `ci:image-scan` | Low / Medium. Example: two HIGH zlib CVEs were caught and fixed in M3 (CHANGELOG). |
| R11 | **Scope creep beyond the classified use.** The agent gets tools that act on scheduling or trading systems, or its answers feed operations automatically, which could move it into a higher EU AI Act tier. | Human-AI configuration | Low / High | Parag | The use-case classification lists re-classification triggers. The API's database role is read-only. Out-of-scope requests are refused. Any new tool requires a design review gate (standards pack). | `pytest:tests/isolation/test_tenant_isolation.py::test_app_role_cannot_write` · `eval:adversarial` | Low / High. A process control; the test only proves the current design is read-only. |
| R12 | **Cost overrun.** Model spend exceeds the POC budget (US$1–2k), for example from eval runs on every push. | n/a (operational) | Medium / Low | Parag | PRs run only the frozen regression subset (about $1). Prompt caching on the system prompt. Cost per query is computed from pinned prices and sent to Langfuse. | `pytest:tests/unit/test_tracing.py::test_cost_uses_pinned_prices` | Medium / Low. No spend alert yet; add a provider-side budget limit (open action A3). |

## Cross-check against other risk lists

As research note 1 asked, the list was checked against the 12 NIST AI 600-1 risks. *Confabulation*, *data privacy*, *information security*, *information integrity*, *human-AI configuration*, *intellectual property* and *value chain* are covered above. The rest don't apply to a tool-less, text-only, internal knowledge agent on synthetic data: *CBRN information*, *dangerous or violent content*, *obscene or abusive content*, *environmental impacts* (not material at POC scale) and *harmful bias*. Bias is recorded as not applicable because the agent makes no decisions about people. Revisit it if it is ever used for anything that affects individuals (a re-classification trigger).

The NC-AI-001 draft list (28 risks) was not cross-checked, because its authorship is unclear (research note 1). That is open action A1.

## Open actions

| ID | Action | Owner | Due |
|---|---|---|---|
| A1 | Cross-check against a second public risk list (NC-AI-001 or the Regulated AI Starter Kit) | Parag | 2026-12-15 |
| A2 | Add LLM-judged faithfulness (Ragas) to the eval run, to strengthen R4 | Parag | M5 |
| A3 | Set a spend limit and alert on the Anthropic API key used by CI, for R12 | Parag | 2026-12-15 |
| A4 | Add Langfuse alerts on leakage-gate failures and score drops (brief §9), for R1 and R8 | Parag | M5 |

## Review log

| Date | Reviewer | Changes |
|---|---|---|
| 2026-11-15 | Claude Code (draft) | First version, M4 |

## Sign-off

| Role | Name | Date | Decision |
|---|---|---|---|
| Reviewer | Parag | | |
