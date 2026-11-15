# Use-case classification: Multi-Client ETRM Knowledge Agent

| | |
|---|---|
| Status | **Draft, awaiting review** |
| Version | 0.1 (15 Nov 2026) |
| Prepared for review by | Parag (brief §12, M4 approver) |
| Review due | Before M2 starts, then quarterly with the regulatory register |
| Basis | EU AI Act (Reg. (EU) 2024/1689), NIST AI RMF 1.0, NIST AI 600-1. See [research note 2](../research/02-regulation.md). |

> This is an engineering self-assessment written before coding, as the standards pack requires. It is not legal advice. Before any use with real client data, it should be confirmed by someone qualified in EU AI Act compliance.

## 1. System description

A retrieval-augmented chatbot. A logged-in user from one client organisation asks questions about that client's ETRM (energy and commodity trading and risk management) systems: contracts, system configuration, scheduling, settlement and invoicing, and runbooks. The agent answers only from that client's knowledge base plus the consultancy's shared knowledge base, cites its sources, and says it doesn't know when retrieval finds nothing relevant.

- **Users:** client staff (operations, IT, business analysts) and consultancy staff. They are professionals, not consumers.
- **Outputs:** text answers with citations, read by a person.
- **No autonomous actions:** the agent cannot change trades, schedules, configuration or any other system. It has no tools beyond retrieval.
- **Underlying model:** a general-purpose AI model from a third-party provider (Anthropic) used through its API. We don't train or fine-tune it.
- **POC data:** entirely synthetic. No real personal data or client data.

## 2. Role under the EU AI Act

- We are the **provider of an AI system** (we build it and put it into service under our name), built on a third-party general-purpose AI model.
- We are **not** a provider of a general-purpose AI model, so the GPAI obligations in Chapter V fall on the model vendor, not on us.
- A client organisation that runs the agent for its staff would be a **deployer**.

## 3. Risk-tier assessment

| Tier | Assessment | Reasoning |
|---|---|---|
| Prohibited practices (Art. 5) | **No** | No manipulation, social scoring, biometric categorisation, emotion recognition or similar. |
| High risk, Annex I (product safety) | **No** | Not a safety component of a regulated product. |
| High risk, Annex III | **No, with one point to watch (below)** | It's not used for employment decisions, access to essential services, credit, law enforcement, migration, justice or education. |
| ↳ Annex III point 2, critical infrastructure | **No, as designed** | Clan A is a gas and power utility, and Annex III covers AI used as a **safety component** in the management and operation of gas and electricity supply. Our agent is a knowledge-lookup aid. It has no control over operations, its answers go through a person, and it can't act. That keeps it outside point 2. **The classification must be redone if the agent is ever given tools that act on scheduling, nomination or dispatch systems, or if its answers feed automatically into operations.** |
| Limited risk, transparency (Art. 50) | **Yes** | It interacts directly with people, so Art. 50(1) applies: users must be told they are talking to an AI. Applicable since 2 Aug 2026. |
| Minimal risk | n/a | Already covered by the limited-risk tier above. |

**Result: limited risk, with transparency duties.** This matches the expected outcome in brief §8.

## 4. Obligations that follow and how we meet them

| Obligation | How we meet it | Evidence |
|---|---|---|
| Art. 50(1): tell users they are interacting with AI | A persistent disclosure notice in the chat UI, shown before the first message (FR5) | A UI test that checks the notice is present; a screenshot in the model card |
| Art. 50(2): machine-readable marking of generated content | Low relevance, because answers aren't published as content. Re-assess before client-facing use (deferred to 2 Dec 2026 for systems already on the market). | This document, reviewed quarterly |
| GDPR (production only; the POC uses synthetic data) | PII masked at ingestion, an output guard, redaction in traces, deletion per client (brief §8) | PII eval set (hard gate); data-source register |
| Contracts with clients | Client data is never used to train or fine-tune models | Model card; data-source register |

## 5. Voluntary alignment (NIST AI RMF)

Not legally required, but the brief §8 asks for it. The governance pack is organised as **Govern** (this document, the standards pack, review gates), **Map** (data-source register, risk register), **Measure** (the eval sets and CI gates) and **Manage** (incident process, human-oversight note). The NIST AI 600-1 risks most relevant here are confabulation, information security (prompt injection) and data privacy. Each will have an entry in the risk register with the test that covers it.

## 6. Triggers for re-classification

Redo this assessment if any of the following happens:

- the agent gets tools that write to or act on any client system
- its outputs feed automatically into operational, trading or HR decisions
- it is offered to consumers or to the public, not just to client staff
- real personal data goes beyond contact details (for example, decisions about individuals)
- the model provider changes, or the EU AI Act or Commission guidelines are amended (for example, by the Digital Omnibus)

## Sign-off

| Role | Name | Date | Decision |
|---|---|---|---|
| Reviewer | Parag | | |
