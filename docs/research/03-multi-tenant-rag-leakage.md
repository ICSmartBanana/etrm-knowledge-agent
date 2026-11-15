# 3. Multi-tenant RAG: isolation designs and leakage failure modes

## Known failure modes (and what we do about each)

| Failure mode | What goes wrong | Our control |
|---|---|---|
| Filtering only in the application | One query that forgets `WHERE tenant_id = …` leaks everything. Safety depends on developer discipline. | Postgres RLS as a second layer, plus the mandatory `TenantContext` argument to retrieval |
| The table owner bypasses RLS | RLS doesn't apply to the table owner unless the table has `FORCE ROW LEVEL SECURITY` | `ALTER TABLE … FORCE ROW LEVEL SECURITY`. The app connects as a separate non-owner role without `BYPASSRLS`. |
| `SECURITY DEFINER` functions | They run with the definer's rights, which skips RLS | Ban them on chunk tables. A migration test checks this. |
| Backup or admin roles with `BYPASSRLS` | A dump or an admin script sees every tenant | Only the ingest CLI and backups use such a role, and that role is never available to the API |
| Session variable leaking through connection pooling | The tenant set for one request stays on a pooled connection and is used by the next request | Set the tenant with `SET LOCAL` (or `set_config(..., true)`) **inside a transaction** per request, so it resets at commit or rollback. Test this with two interleaved tenants. |
| Filtering after top-K | Filtering after retrieval cuts the effective K and can bias results | Filter **inside** the vector query (pre-filter). |
| ANN index recall skew | A small tenant's vectors are scattered through a big tenant's HNSW graph, so recall drops | At POC scale (about 100 docs per tenant) use an exact scan with no ANN index. If one is added in M5, test per-tenant partial indexes. |
| Only testing that tenants see their own data | Most teams check that A sees A's data. Few check that A can't see B's. | **Canary test:** plant a unique string in each tenant's corpus, then query for it while logged in as every *other* tenant, in CI. |

## Indirect prompt injection via documents (OWASP LLM01 + LLM08:2025)

- Retrieved text reaches the model as context without going through the user-input path, so input filters never see it. OWASP 2025 added **LLM08 "Vector and Embedding Weaknesses"** for risks at the retrieval layer: poisoned documents, cross-tenant leakage through the vector store, and adversarial embeddings.
- One cited result from USENIX Security 2025 is that **five crafted documents can steer answers to a targeted query with more than 90% success**. **Verify** this in the paper itself. Reported real incidents include Slack AI leaking private channel data and Microsoft Copilot retrieving poisoned SharePoint documents.
- **Mitigations we adopt:** retrieved chunks go into a clearly delimited data block, and the system prompt states that this block never carries instructions. The adversarial set includes the injected document planned for M1. The output guard runs regardless of what the model "decided". Cross-tenant risk under LLM08 is already handled by the controls in the table above.

## Sources

- [pg_trickle: multi-tenant vector search with RLS](https://pgxn.org/dist/pg_trickle/0.36.0/blog/multi-tenant-vector-search-rls.html)
- [Render: multi-tenant RAG with PostgreSQL + pgvector](https://render.com/articles/multi-tenant-rag-postgresql-pgvector)
- [Tian Pan: cross-tenant data leakage in LLM infrastructure](https://tianpan.co/blog/2026/04/10/cross-tenant-data-leakage-llm-infrastructure) · [Tian Pan: vector store access control and RLS](https://tianpan.co/blog/2026/04/17/vector-store-access-control-rag-rls) · [Tian Pan: RAG prompt injection](https://tianpan.co/blog/2026/04/16/rag-prompt-injection-retrieval-pipeline-security)
- [DEV: four pgvector patterns for RAG SaaS](https://dev.to/incultnito_llc/four-pgvector-patterns-that-kept-our-rag-saas-on-one-postgres-230h) · [DEV: one misconfigured vector DB](https://dev.to/arnav_sharma_25c1c7572a20/one-misconfigured-vector-database-every-customers-data-exposed-2jh7)
- [Unified.to: permissions in RAG pipelines](https://unified.to/blog/permissions_security_and_compliance_in_rag_pipelines) · [Twig: RAG data isolation](https://www.twig.so/dev/rag-scenarios-and-solutions/privacy/data-isolation)
- OWASP LLM08: [Indusface](https://www.indusface.com/learning/owasp-llm08-2025-vector-and-embedding-weaknesses/) · [SecureLayer7](https://securelayer7.net/learn/ai-security/vector-and-embedding-weaknesses) · [Aembit overview](https://aembit.io/blog/owasp-top-10-llm-risks-explained/) · [Christian Schneider: RAG security](https://christian-schneider.net/blog/rag-security-forgotten-attack-surface/)
