# Governance pack

The POC's governance documents (brief §8), aligned to the NIST AI RMF and structured so they can later feed an ISO 42001 management system. No certification is claimed.

| NIST AI RMF function | Document | Review cadence |
|---|---|---|
| Govern | [Use-case classification](use-case-classification.md): EU AI Act tier and re-classification triggers | Quarterly, and on any trigger |
| Govern | [Regulatory register](regulatory-register.md): rules per region, with review dates | Quarterly in full; monthly policy digest |
| Map | [Data-source register](data-source-register.md): knowledge bases, owners, data classes, retention | On every knowledge-base change; monthly |
| Map, Manage | [Risk register](risk-register.md): each risk's owner, mitigation and covering tests | Monthly |
| Measure | [Model card](model-card.md): purpose, limits, evaluation, change history | On every model, prompt, retrieval or knowledge-base change |
| Manage | [Human-oversight note](human-oversight.md): who reviews what, and the escalation path | Monthly; after incidents |
| Manage | [Incident process](incident-process.md): report, contain, notify, review | After every incident; quarterly |

**Generated facts.** `scripts/gen_docs.py` builds the model card facts, data-register counts, eval report and changelog from the repo on every CI run. It ships them, together with this folder, as the `governance-docs` artifact.

**Checks in CI:**

- `scripts/governance_check.py` fails a PR that changes prompts, models, retrieval or data without a CHANGELOG or register update.
- `tests/governance/test_registers.py` fails if a risk's covering test no longer exists, a brief-required risk or region is missing, or a regulatory row's review dates are invalid.

**Sign-off.** The new M4 documents and the use-case classification each end with a sign-off table. The data-source register was signed off through its M1 human spot-check. M4 is done when Parag reviews and signs off (brief §12).
