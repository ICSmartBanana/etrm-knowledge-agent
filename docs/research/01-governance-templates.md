# 1. Governance templates (model card, risk register, ISO 42001)

## Findings

- **Model cards.** The common starting point is the nine-section structure from Mitchell et al. (2019), "Model Cards for Model Reporting", which the Hugging Face model card template extends. Our model card describes a *system* (an agent built on a third-party model), not a trained model. So we keep the sections that still apply (intended use, out-of-scope use, evaluation data, metrics, limitations, change history) and replace "training data" with "knowledge bases and data classes".
- **Open-source governance starter kits.**
  - The *Regulated AI Starter Kit* is a GitHub template repo with a model card template, a risk register and a risk-assessment template. It maps to NIST AI RMF and EU AI Act concepts but not explicitly to ISO 42001. It's the closest match to the `agent-project-template` we plan to extract in M4. **Verify** its license and how recently it was maintained before borrowing from it.
  - *Northern Cascadia NC-AI-001* is an ISO 42001-aligned risk register with 28 pre-filled risks. It's a public-comment draft and its authorship is unclear, so use it only as a checklist of risks we might have missed, not as a source of truth.
- **Commercial or free-but-proprietary templates.** Aona AI (a model card and risk register mapped to NIST "Map/Measure" and ISO 42001 Annex A), Optro (a model card template covering 17 areas) and Security Scientist (an ISO 42001 risk register in Excel). They're useful for comparing structure. Don't copy them into the repo.
- **ISO 42001 itself** is paywalled. No free official template set exists, so our pack is "structured to feed ISO 42001 later", as the brief says, and makes no claim of conformity.

## Implications for this project

1. Write our own Markdown templates in `docs/governance/`, using Mitchell et al. and the Regulated AI Starter Kit for structure. Markdown keeps them diffable, so CI can check that they're updated.
2. Give every risk-register row an `owner`, a `mitigation` and a `covering_test` (the brief §8 asks for this). The `covering_test` value points to an eval set or pytest ID, which lets CI check that the link is still valid.
3. Cross-check our risk list against NC-AI-001's 28 risks and NIST AI 600-1's 12 risks (note 2) before M4 sign-off.

## Sources

- [Regulated AI Starter Kit](https://simaba.github.io/regulated-ai/) · [How to use it](https://simaba.github.io/regulated-ai/docs/how-to-use-this-template.html)
- [Northern Cascadia AI Governance Standards (draft)](https://esotericshadow.github.io/nc-ai-templates)
- [Aona AI model documentation template](https://aona.ai/templates/model-documentation-template.md) · [Aona AI risk register](https://aona.ai/templates/ai-risk-register.docx)
- [Optro model card template](https://optro.ai/resources/ebook/model-card-template-for-an-ai-developer)
- [Security Scientist ISO 42001 risk register](https://www.securityscientist.net/blog/iso-42001-ai-risk-register-template/)
- [Petronella Tech model card template](https://petronellatech.com/ai/ai-model-card-template/)
- [ThinkTech AI risk register template](https://thinktech.ngo/tools/ai-risk-register-template)
