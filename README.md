# etrm-knowledge-agent

**▶ Live demo: https://icsmartbanana.github.io/etrm-knowledge-agent/**: chat as each client, browse their documents, and read the agent's eval report.

**One AI assistant, several clients, zero cross-client leakage, and the receipts to prove it.**

A proof of concept for a multi-tenant RAG chatbot in the ETRM (energy and commodity trading and risk management) consulting domain. One codebase and one agent image serve three fictional clients: a gas and power utility, a refined-products trader and an agricultural trader. A shared consultancy knowledge base is visible to all three. All data is **synthetic**.

The clients' topics overlap on purpose: two of them have gas nomination deadlines, and two have settlement terms, each with *different* facts. That tempts the agent to blend answers. The POC shows that it doesn't, and that every change is measured before it ships.

## What works today

| Area | What's in place |
|---|---|
| **Tenant isolation** | The tenant comes only from the login session, never from the question. Every query filters by tenant, and Postgres FORCE row-level security is a second, independent layer. Canary documents prove one client can't retrieve another's. |
| **Data classes** | Each chunk is `public`, `insight`, `inference_only` (used for reasoning, never quoted) or `pii` (never sent to the model). PII is masked at ingestion and again at output. |
| **Cite or abstain** | Answers cite their source documents. Below a retrieval-score threshold the agent says it doesn't know, without calling the model. It refuses out-of-scope requests, doesn't reveal its system prompt, and always shows an AI disclosure. |
| **Messy data** | Superseded policies, contradictions, near-duplicates and a document with a hidden prompt injection, all deliberate. |
| **Evals** | 242 frozen cases (golden, overlap, leakage, PII/inference-only, adversarial). Four **hard gates** are checked on every answer with zero tolerance. Quality floors only go up. Iteration 1: **0** hard-gate failures, 0.96 exact-value accuracy, 0.98 correct citations. |
| **Observability** | Every request is traced (client, retrieved chunks and scores, model, prompt version, knowledge-base version, tokens, cost) to Langfuse Cloud, with PII masked and no document text sent. |
| **CI/CD** | Ruff, mypy, pytest with a real Postgres, Bandit, pip-audit, Semgrep, Gitleaks, Trivy, a governance check, generated docs, a PR eval job that posts a score table, and a weekly full run. A deliberately leaky change was blocked by the tests, the governance check and the leakage gate (85 failures). |
| **Governance** | EU AI Act use-case classification, risk register (each risk has an owner, a mitigation and live covering tests), model card, data-source register, human-oversight note, incident process, and a regulatory register (EU, US states, UK, Australia, India). |

## Still to do

- LLM-judged faithfulness (Ragas) on top of the deterministic checks
- Better chunking, hybrid search and a reranker. Most golden misses are retrieval misses.
- Langfuse dashboards and alerts on gate failures and score drops
- Deployment to Azure Container Apps (staging, then demo with approval)
- NER-based PII detection for real names, before any real data

## Run it

You need **Git**, **Docker Desktop** and an **Anthropic API key**. No Python required.

```bash
git clone https://github.com/ICSmartBanana/etrm-knowledge-agent.git
cd etrm-knowledge-agent
cp .env.example .env              # then put your ANTHROPIC_API_KEY in .env
docker compose up --build         # db -> ingest -> API (:8000) -> UI (:8501)
```

Open http://localhost:8501. **[docs/RUN-LOCALLY.md](docs/RUN-LOCALLY.md)** has the step-by-step version: installing the tools, creating the Anthropic and (optional) Langfuse keys, the `.env` file, what to try, and troubleshooting.

[CLAUDE.md](CLAUDE.md) has the full command list, the request flow and the architecture invariants. The governance pack is in [docs/governance/](docs/governance/README.md), and the stack decision is in [ADR 0001](docs/decisions/0001-stack.md).

## Related repos

- [agent-standards](https://github.com/ICSmartBanana/agent-standards): principles, review gates, playbooks and Claude Code skills for building agents this way
- [agent-project-template](https://github.com/ICSmartBanana/agent-project-template): a GitHub template that starts a new agent with all of the above already wired in

## Notes

Built with [Claude Code](https://claude.com/claude-code). References to "the brief" (for example "brief §8") point to the private requirements brief this POC was scoped from. It isn't published.

[MIT](LICENSE) licensed.
