#!/bin/bash
# Runs once, on first start of an empty Postgres volume (docker-entrypoint-initdb.d).
# Roles:
#   etrm_owner   - POSTGRES_USER. A SUPERUSER, and superusers bypass RLS even with FORCE, so it
#                  owns nothing and is for admin only. Never give its credentials to the API.
#   etrm_schema  - NOLOGIN, not superuser. Owns the tables; FORCE RLS binds it.
#   etrm_app     - used by the API. No BYPASSRLS; sees only rows the RLS policy allows.
#   etrm_ingest  - used only by the ingest CLI. BYPASSRLS, never given to the API.
# See docs/decisions/0001-stack.md (isolation design) and docs/research/03-multi-tenant-rag-leakage.md.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v app_pw="$ETRM_APP_PASSWORD" -v ingest_pw="$ETRM_INGEST_PASSWORD" <<'SQL'
CREATE EXTENSION IF NOT EXISTS vector;

CREATE ROLE etrm_app LOGIN PASSWORD :'app_pw' NOBYPASSRLS;
CREATE ROLE etrm_ingest LOGIN PASSWORD :'ingest_pw' BYPASSRLS;
CREATE ROLE etrm_schema NOLOGIN NOSUPERUSER NOBYPASSRLS;
GRANT USAGE, CREATE ON SCHEMA public TO etrm_schema;
SET ROLE etrm_schema;

CREATE TABLE kb_versions (
    kb_version   text PRIMARY KEY,
    corpus_hash  text NOT NULL,
    doc_count    integer NOT NULL,
    chunk_count  integer NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE documents (
    tenant_id       text NOT NULL CHECK (tenant_id IN ('clan_a', 'clan_b', 'clan_c', 'consultancy')),
    doc_id          text NOT NULL,
    title           text NOT NULL,
    doc_type        text NOT NULL,
    data_class      text NOT NULL CHECK (data_class IN ('public', 'inference_only', 'insight', 'pii')),
    status          text NOT NULL CHECK (status IN ('current', 'superseded')),
    effective_date  date NOT NULL,
    supersedes      text,
    contradicts     text,
    kb_version      text NOT NULL REFERENCES kb_versions(kb_version),
    PRIMARY KEY (tenant_id, doc_id)
);

-- No ANN index on purpose: exact scan at POC scale avoids per-tenant recall skew (ADR 0001).
CREATE TABLE chunks (
    id           bigserial PRIMARY KEY,
    tenant_id    text NOT NULL,
    doc_id       text NOT NULL,
    chunk_index  integer NOT NULL,
    heading      text NOT NULL,
    data_class   text NOT NULL,
    content      text NOT NULL,          -- PII already masked at ingestion
    embedding    vector(384) NOT NULL,   -- BAAI/bge-small-en-v1.5
    kb_version   text NOT NULL REFERENCES kb_versions(kb_version),
    FOREIGN KEY (tenant_id, doc_id) REFERENCES documents(tenant_id, doc_id) ON DELETE CASCADE,
    UNIQUE (tenant_id, doc_id, chunk_index)
);
CREATE INDEX chunks_tenant_idx ON chunks (tenant_id);

-- Row-level security. FORCE so that even the table owner is subject to it.
-- The tenant comes from a per-transaction setting (SET LOCAL app.tenant_id); with no setting,
-- the policy returns nothing at all, not even consultancy rows.
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents FORCE ROW LEVEL SECURITY;
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_read ON documents FOR SELECT TO etrm_app USING (
    coalesce(current_setting('app.tenant_id', true), '') <> ''
    AND tenant_id IN (current_setting('app.tenant_id', true), 'consultancy')
);
CREATE POLICY tenant_read ON chunks FOR SELECT TO etrm_app USING (
    coalesce(current_setting('app.tenant_id', true), '') <> ''
    AND tenant_id IN (current_setting('app.tenant_id', true), 'consultancy')
);

GRANT SELECT ON documents, chunks, kb_versions TO etrm_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON kb_versions, documents, chunks TO etrm_ingest;
GRANT USAGE ON SEQUENCE chunks_id_seq TO etrm_ingest;
RESET ROLE;
GRANT USAGE ON SCHEMA public TO etrm_app, etrm_ingest;
SQL
