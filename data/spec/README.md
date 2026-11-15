# Synthetic data specs

One YAML file per knowledge base. These specs are the **ground truth** for the corpus. `datagen` turns each `docs` entry into one Markdown document under `data/synthetic/<tenant_id>/`.

## How the facts work

- Each doc lists `facts`. Text inside `[[double brackets]]` is a **key value**. The generator tells the model to reproduce it verbatim, and `tests/data/test_corpus.py` checks that it appears exactly in the generated document. The brackets themselves are removed.
- PII values come only from the spec. The model is told to copy them exactly and never invent any, and the tests fail on any email, phone number or trader ID that isn't in the doc's spec, so `data/pii_registry.json` is exact. Canaries and the prompt injection are inserted by code, not the model.
- **One deliberate cross-tenant trap:** Clan B's outdated wiki page (`b-010`) says "net 20 days", which is Clan C's *current* payment term (`c-002`). A blended answer looks plausible, and only tenant filtering prevents it.
- Overlap topics (`overlap: gas_scheduling` A↔B, `overlap: settlement` B↔C) deliberately use the same vocabulary with **different values**. That's what the overlap eval set tests.

## Fields

| Field | Meaning |
|---|---|
| `data_class` | `public`, `inference_only` (usable for reasoning, never quotable), `insight` (paraphrasable conclusions) or `pii` (a contact list) |
| `status` | `current` or `superseded` |
| `supersedes` / `contradicts` | Messy-data links used by the evals |
| `pii` | Registry IDs to embed verbatim. Public docs can carry PII too, which tests masking at ingestion. |
| `canary` | `true` means the tenant's canary string goes in this doc (for the cross-tenant leakage tests) |
| `injection` | `true` means the standard injected-instruction block is inserted (for the adversarial set) |
| `derived` | Docs built in code from another doc (near-duplicates), with no LLM call |

All company, system, hub and pipeline names are fictional. Emails use the reserved `.example` TLD. Phone numbers come from the ranges Ofcom reserves for drama (`+44 20 7946 0xxx`) and the US `555-01xx` range.
