## Summary

<!-- What changed and why. -->

## Governance checklist (brief §7)

Tick each one that this PR changes. CI fails if a governed area changes without its docs.

- [ ] **Knowledge base** (`data/`): CHANGELOG and `docs/governance/data-source-register.md` updated
- [ ] **System prompt** (`prompts/`): new prompt version, CHANGELOG updated
- [ ] **Model** (`app/config.py`, `app/llm.py`): model card notes the change, CHANGELOG updated, prices checked
- [ ] **Retrieval settings** (`app/retrieval.py`, `ingest/chunking.py`, `RETRIEVAL`): CHANGELOG updated
- [ ] **Guardrails or isolation** (`app/guard.py`, `app/pii.py`, `app/tenancy.py`, `db/init/`): CHANGELOG updated, isolation tests pass
- [ ] **Eval sets or baselines** (`evals/sets/`, `evals/baselines/`): CHANGELOG updated, reason stated
- [ ] None of the above

## Evidence

- [ ] CI is green. **Never merge a red PR**: the leakage and PII eval gates are hard gates.
- [ ] Eval score table (posted by the `eval` workflow) reviewed against the baseline
