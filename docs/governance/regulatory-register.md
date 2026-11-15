# Regulatory register

| | |
|---|---|
| Status | **Draft, awaiting review** |
| Version | 0.1 (15 Nov 2026, milestone M4) |
| Owner | Parag (POC owner) |
| Review | Quarterly in full (brief §8): next full review **2027-02-15**. Rows with an earlier date are reviewed on that date. A monthly policy digest flags changes in between. |

A living table of the AI and data rules in the regions the brief lists (EU, US states, UK, Australia, India), what they mean for this agent, and when each row is next reviewed. `tests/governance/test_registers.py` checks that every row has valid review dates.

> **Not legal advice.** This is an engineering register built from secondary sources (law-firm and compliance commentary) on 15 Nov 2026. Rows marked **verify** have conflicting or unconfirmed secondary sources, or none checked against the primary text. Before using real client data, someone qualified should confirm each applicable row against the primary law.

**Applies to the POC?** answers for the POC as built: synthetic data, internal professional users, no tools, no decisions about individuals. **Applies in production?** is for a deployment to real clients.

## Register

| ID | Region | Instrument | Status and key dates | Applies to POC? | Applies in production? | What we do | Verify | Last reviewed | Next review |
|---|---|---|---|---|---|---|---|---|---|
| EU-1 | EU | AI Act (Reg. (EU) 2024/1689), Art. 50(1): tell people they are interacting with AI | Applies since 2 Aug 2026. Not postponed by the Digital Omnibus. Fines up to €15m or 3 % of turnover. | Yes | Yes | Disclosure notice on every answer and at login (FR5). Covered by `tests/api/test_api.py::test_disclosure_on_every_answer`. | No | 2026-11-15 | 2027-02-15 |
| EU-2 | EU | AI Act Art. 50(2): machine-readable marking of AI-generated content | 2 Dec 2026 for generative systems already on the market on 2 Aug 2026; from launch for systems placed on the market later. | Low relevance: answers go to one logged-in user and aren't published. | Re-assess before client launch. | Use-case classification records the reasoning. If needed, add answer metadata marking it as AI-generated. | Yes: scope for text answers in a closed tool | 2026-11-15 | 2026-12-01 |
| EU-3 | EU | AI Act high-risk rules (Annex III) and the Digital Omnibus (Reg. (EU) 2026/1744) | Omnibus in force 27 Jul 2026. Annex III high-risk duties moved to 2 Dec 2027, Annex I to Aug 2028. | No (not high-risk) | Only if a re-classification trigger fires, for example tools acting on gas or power operations (Annex III point 2). | Re-classification triggers in the use-case classification; risk R11. | Yes: confirm dates in the OJ text | 2026-11-15 | 2027-02-15 |
| EU-4 | EU | GDPR | In force. Art. 33: breach notice to the authority within 72 hours. | No (synthetic data) | Yes, for any personal data in client documents | PII masked at ingestion, blocked at output, redacted in traces. Per-client deletion. Incident process covers the 72-hour notice. | No | 2026-11-15 | 2027-02-15 |
| US-1 | US (federal) | No federal AI statute. NIST AI RMF and AI 600-1 are voluntary. | The executive order behind NIST AI 600-1 was revoked; the profile remains a voluntary NIST resource. | Voluntary alignment | Voluntary alignment | The governance pack is organised on Govern / Map / Measure / Manage. | Yes: check NIST for a newer 600-1 version | 2026-11-15 | 2027-02-15 |
| US-CO | US: Colorado | SB 24-205 (Colorado AI Act), repealed and replaced by SB 26-189 (automated decision-making technology) | SB 24-205 was delayed to 30 Jun 2026, its enforcement stayed by a court on 27 Apr 2026, then repealed and re-enacted more narrowly by SB 26-189 (signed 14 May 2026), **effective 1 Jan 2027**. | No | Unlikely: it targets consequential decisions about individuals, which the agent doesn't make. | Keep decisions about individuals out of scope (model card). Re-check if the use changes. | Yes: sources disagree on whether SB 24-205 ever took effect; read SB 26-189 | 2026-11-15 | 2026-12-15 |
| US-CA-1 | US: California | SB 243 (companion chatbots) | Core duties since 1 Jan 2026; reporting from 1 Jul 2027. An amendment (SB 1119) reportedly changes the minor-specific duties from 1 Jan 2027. | No | Unlikely: aimed at companion chatbots for consumers, not a workplace knowledge tool. | Record the reasoning; re-check if the agent is ever offered to consumers. | Yes: SB 1119 detail is from one aggregator | 2026-11-15 | 2027-02-15 |
| US-CA-2 | US: California | SB 942 (AI Transparency Act), as amended by AB 853 and SB 1000 | Operative since 2 Aug 2026 (AB 853 moved it from 1 Jan 2026); SB 1000 amended it from 30 Sep 2026. Enforced by the Attorney General. | No | Unlikely: applies to "covered providers" of public generative AI systems with over 1 million monthly users. | None needed at current scale. | Yes: check the amended thresholds on leginfo | 2026-11-15 | 2027-02-15 |
| US-UT | US: Utah | Artificial Intelligence Policy Act (as amended by SB 226 and SB 332, 2025) | In force; sunset extended to 1 Jul 2027. Disclosure when a person asks if they are talking to AI, and up front in regulated occupations. A 2026 bill (HB 320) was not reviewed. | No | Possibly, if Utah users ask whether they're talking to AI | The disclosure notice is always shown, which exceeds an on-request duty. | Yes: 2026 amendments unchecked | 2026-11-15 | 2027-02-15 |
| US-TX | US: Texas | TRAIGA (HB 149) | Effective 1 Jan 2026. AI-interaction disclosure duties fall mainly on government agencies (and healthcare); bans certain intentional harmful uses. | No | Unlikely for a private B2B tool | The disclosure notice is always shown. | Yes: scope of the private-sector duties | 2026-11-15 | 2027-02-15 |
| UK-1 | UK | No AI statute. UK GDPR, Data Protection Act 2018, Equality Act 2010, sector regulators (FCA, Ofgem for energy). | No government AI bill as of Nov 2026; none in the 13 May 2026 King's Speech, which announced a Regulating for Growth Bill with sandbox powers. The ICO's statutory code on AI and automated decision-making is still pending. | No (synthetic data) | Yes: UK GDPR for personal data. Clan A-style utilities are Ofgem-regulated. | Same data controls as EU-4. Watch for the ICO code. | Yes: track the ICO code | 2026-11-15 | 2027-02-15 |
| AU-1 | Australia | Privacy Act 1988 as amended by the Privacy and Other Legislation Amendment Act 2024: APP 1.7 automated-decision transparency | **Applies from 10 Dec 2026.** Privacy policies must describe computer-made decisions that could significantly affect individuals. | No | Unlikely: the agent makes no decisions about individuals. | Keep it that way; record the reasoning. | No | 2026-11-15 | 2026-12-10 |
| AU-2 | Australia | AI policy: National AI Plan (2 Dec 2025) and voluntary guidance | Mandatory guardrails for high-risk AI were dropped for voluntary guidance in Dec 2025. Reports from Jul–Aug 2026 of new mandatory national AI standards, with legislation planned for early 2027; scope unclear. | No | Watch | Follow the voluntary practices the pack already covers (testing, transparency, human oversight). | Yes: sources conflict on the 2026 announcements | 2026-11-15 | 2027-02-15 |
| IN-1 | India | Digital Personal Data Protection Act 2023 and DPDP Rules 2025 | Rules notified 13/14 Nov 2025 in phases: the Data Protection Board immediately; consent managers from **13/14 Nov 2026**; most data-fiduciary duties (notice, security safeguards, breach notification, children's data) from **13/14 May 2027**. | No (synthetic data) | Yes, for personal data of people in India | PII masking and per-client deletion already in place. Add DPDP breach-notice steps to the incident process before May 2027. | Yes: exact day differs by source | 2026-11-15 | 2027-02-15 |
| IN-2 | India | India AI Governance Guidelines (MeitY, 5 Nov 2025) | Non-binding policy guidance; relies on existing law and sector regulators. | Voluntary | Voluntary | The pack's principles already align. | No | 2026-11-15 | 2027-02-15 |

## Monthly policy digest

The brief §8 asks for a monthly digest to keep this register current. Until the standards-pack skill for it exists (M4, `agent-standards` repo), the digest is a manual task on the monthly review date:

1. Search for changes since the last digest for each region above, and for new US state AI laws.
2. For each change, update the row (status, dates, applies?, what we do), set *Last reviewed*, and add a review-log line.
3. If a row now applies where it didn't, add a risk-register entry and, if needed, re-run the use-case classification.

## Sources

Secondary sources, checked 15 Nov 2026:

- EU: [Cooley on the Digital Omnibus](https://cdp.cooley.com/digital-ai-omnibus-delays-key-deadlines-introduces-new-rules/) · [nicfab on Reg. (EU) 2026/1744 in the OJ](https://www.nicfab.eu/en/posts/digital-omnibus-ai-official-journal/) · [Technology.org on deadlines after the Omnibus](https://www.technology.org/2026/10/13/eu-ai-act-deadlines-after-the-digital-omnibus-what-applies-from-december-2026-to-august-2028/) · Art. 50 sources in [research note 2](../research/02-regulation.md)
- Colorado: [AI Compliance Atlas](https://aicomplianceatlas.com/law/colorado-ai-act) · [imiel.dev](https://imiel.dev/explore/us-ai-legislation-2026/colorado/) · [aigovernance.com](https://aigovernance.com/policy/colorado-ai-act-sb205)
- California: [Jones Walker on SB 243](https://www.joneswalker.com/en/insights/blogs/ai-law-blog/ai-regulatory-update-californias-sb-243-mandates-companion-ai-safety-and-accoun.html) · [AI Compliance Atlas on SB 243](https://aicomplianceatlas.com/law/california-sb-243) · [CASRAI on SB 942](https://casrai.org/news/california-sb-942-ai-transparency-act-effective-august-2026) · [Kolmogorov Law on SB 942](https://www.kolmogorovlaw.com/california-ai-transparency-act-sb-942)
- Utah and Texas: [Venable](https://www.venable.com/insights/publications/2025/11/state-ai-laws-continue-evolving-in-2025) · [Greenberg Traurig on TRAIGA](https://gtlaw.com/en/insights/2025/6/traiga-key-provisions-of-texas-new-artificial-intelligence-governance-act) · [Cooley: state AI laws, Apr 2026](https://www.cooley.com/news/insight/2026/2026-04-24-state-ai-laws-where-are-they-now) · [Utah SB 226 enrolled text](https://le.utah.gov/Session/2025/bills/enrolled/SB0226.pdf)
- UK: [Bratby Law](https://bratby.law/uk-ai-regulation-what-the-law-says/) · [Osborne Clarke](https://www.osborneclarke.com/insights/regulatory-outlook-january-2026-artificial-intelligence) · [regulations.ai UK overview](https://regulations.ai/regulations/RAI-GB-NA-SUMMARY-2026)
- Australia: [CoterieLabs](https://coterielabs.com.au/field-notes/ai-compliance-australia-guide) · [Shiv Odean, Q2 2026](https://shivodean.com/state-of-ai-regulations-australia/) · [Aivy on the Privacy Act](https://aivy.com.au/resources/privacy-act-1988-ai-compliance-playbook-australia/)
- India: [DPDP Rules 2025 (Wikipedia)](https://en.wikipedia.org/wiki/Digital_Personal_Data_Protection_Rules,_2025) · [Responsible AI Labs](https://responsibleailabs.ai/knowledge-hub/articles/india-dpdp-act-2026-2027) · [AI Risk Aware](https://airiskaware.com/insights/india-ai-governance-dpdp-2026)

## Review log

| Date | Reviewer | Changes |
|---|---|---|
| 2026-11-15 | Claude Code (draft) | First version, M4. Closes the M0 open item "US states, UK, Australia, India not researched". |

## Sign-off

| Role | Name | Date | Decision |
|---|---|---|---|
| Reviewer | Parag | | |
