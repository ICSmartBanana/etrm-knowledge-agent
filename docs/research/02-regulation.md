# 2. Regulation: EU AI Act transparency, NIST AI RMF and the GenAI profile

## EU AI Act, Article 50 (transparency)

- **In force now.** The Article 50 obligations have applied since **2 August 2026**. Article 50(1) says that providers must design AI systems that interact with people so those people are told they are dealing with an AI, unless that's obvious from context. Commentators say there is no grace period for chatbot disclosure.
- **Machine-readable marking of generated content (Art. 50(2))** was deferred to **2 December 2026** for generative systems already on the market. Our agent produces text answers for a logged-in user, not published content, so 50(2) is low-relevance for the POC. We'll recheck it before any client-facing use.
- **The Commission's final Article 50 guidelines** were published on **20 July 2026**.
- **Digital Omnibus.** Secondary sources say it postpones some AI Act requirements (high-risk obligations) to December 2027. They disagree on whether anything in Art. 50(1) moves. **Verify** against the Official Journal text and the Commission guidelines.
- **Penalties.** Breaching Art. 50 can mean fines of up to €15m or 3% of worldwide annual turnover.

**What this means for the POC:** the disclosure notice (FR5) is a legal duty, not a nicety, so a test should cover it. The banner text and its placement get recorded in the use-case classification.

## NIST AI RMF and the Generative AI Profile (NIST AI 600-1)

- The AI RMF is organised into four functions: **Govern, Map, Measure, Manage**. The governance pack is laid out against these four.
- **NIST AI 600-1** (July 2024) is a companion profile listing **12 risks that are unique to or made worse by generative AI**, with suggested actions for each. The ones that matter most here:
  - **Confabulation** (hallucination). The suggested actions include checking sources and citations in outputs (MS-2.5-003) and monitoring after deployment (MG-4.1-002). Our design answers this with cite-or-abstain (FR3) and the Ragas faithfulness metric.
  - **Information security**, which includes prompt injection against the system. Suggested actions include regularly reviewing guardrails (MS-2.5-006). Our design answers this with the adversarial eval set and the injected-document test data planned for M1.
  - **Data privacy.** Our design answers this with PII masking, the output guard and trace redaction.
- **Status.** The profile was issued under the US executive order on AI that has since been revoked. It remains a voluntary NIST resource. **Verify** on the NIST site that 600-1 is still the current version, and check the control IDs in the primary PDF, since the IDs above come from secondary summaries.

## Still to research (for the regulatory register in M4)

The brief §8 asks for the US states, the UK, Australia and India as well. None of them was researched in M0. They're logged as an open item for M4, when the regulatory register is built.

**Done in M4:** see the [regulatory register](../governance/regulatory-register.md). It also updates the Digital Omnibus point above: it was adopted as Reg. (EU) 2026/1744 and did not move Art. 50(1).

## Sources

- EU AI Act Art. 50 commentary: [Cooley](https://cooley.com/news/insight/2026/2026-08-03-eu-ai-act-transparency-obligations-take-effect-2-august-2026) · [Sidley Data Matters](https://datamatters.sidley.com/2026/06/24/eu-ai-act-transparency-obligations-preparing-for-compliance-by-2-august-2026/) · [McCann FitzGerald](https://www.mccannfitzgerald.com/knowledge/technology-and-innovation/one-month-to-go-eu-ai-act-transparency-compliance) · [Stephenson Harwood on the Commission guidelines](https://perspectives.stephensonharwood.com/post/102nfqh/eu-ai-act-update-european-commission-adopts-guidelines-on-article-50-transparenc) · [CSA research note](https://labs.cloudsecurityalliance.org/research/csa-research-note-eu-ai-act-article-50-transparency-20260729/) · [Chambers / WH Partners](https://chambers.com/articles/eu-ai-act-the-latest-compliance-checkpoint) · [GDPR Local](https://gdprlocal.com/eu-ai-act-article-50/)
- NIST AI 600-1: [NIST primary PDF (initial public draft)](https://airc.nist.gov/docs/NIST.AI.600-1.GenAI-Profile.ipd.pdf) · [Anaconda guide](https://www.anaconda.com/blog/nist-ai-600-1-generative-ai-profile-guide) · [Modulos docs](https://docs.modulos.ai/frameworks/nist-ai-rmf/generative-ai-profile) · [WitnessAI](https://witness.ai/blog/nist-ai-600-1-generative-ai-profile/) · [AI Governance Library](https://www.aigl.blog/artificial-intelligence-risk-management-framework-generative-artificial-intelligence-profile/)
