"""Ingest the synthetic corpus into Postgres, as a new knowledge-base version.

    uv run python -m ingest.cli                  # ingest all tenants
    uv run python -m ingest.cli --run-evals      # ...then run the regression evals (FR7)

Each run computes kb_version from a hash of the corpus files, masks PII, embeds every chunk and
replaces all rows in one transaction. Uses the etrm_ingest role, never the API's role.
"""

from __future__ import annotations

import argparse
import hashlib

# subprocess runs only our own eval module with a fixed argv (see main()).
import subprocess  # nosec B404
import sys
from datetime import date
from pathlib import Path

import psycopg
import yaml
from pgvector.psycopg import register_vector

from app.config import REPO_ROOT, RETRIEVAL, ingest_dsn
from app.embed import default_embedder
from app.pii import mask
from ingest.chunking import chunk_markdown

CORPUS = REPO_ROOT / "data" / "synthetic"


def corpus_files() -> list[Path]:
    return sorted(CORPUS.rglob("*.md"))


def kb_version(files: list[Path]) -> tuple[str, str]:
    h = hashlib.sha256()
    for f in files:
        h.update(f.relative_to(CORPUS).as_posix().encode())
        h.update(f.read_bytes())
    digest = h.hexdigest()
    return f"kb-{date.today():%Y%m%d}-{digest[:8]}", digest


def parse(path: Path) -> tuple[dict[str, object], str]:
    _, meta, body = path.read_text(encoding="utf-8").split("---\n", 2)
    return yaml.safe_load(meta), body


def ingest() -> str:
    files = corpus_files()
    if not files:
        raise SystemExit(f"No documents under {CORPUS}; refusing to load an empty KB.")
    version, digest = kb_version(files)
    embedder = default_embedder()
    docs, rows = [], []
    for f in files:
        meta, body = parse(f)
        docs.append(meta)
        for c in chunk_markdown(str(meta["title"]), mask(body), RETRIEVAL.chunk_max_chars):
            rows.append((meta, c))
    print(f"{len(docs)} documents, {len(rows)} chunks; embedding with {embedder.model_name}...")
    vectors = embedder.embed([c.text for _, c in rows])

    with psycopg.connect(ingest_dsn()) as conn:
        register_vector(conn)
        with conn.transaction():
            conn.execute("DELETE FROM chunks")
            conn.execute("DELETE FROM documents")
            conn.execute(
                "INSERT INTO kb_versions (kb_version, corpus_hash, doc_count, chunk_count) "
                "VALUES (%s, %s, %s, %s) ON CONFLICT (kb_version) DO NOTHING",
                (version, digest, len(docs), len(rows)),
            )
            for m in docs:
                conn.execute(
                    "INSERT INTO documents (tenant_id, doc_id, title, doc_type, data_class, status,"
                    " effective_date, supersedes, contradicts, kb_version)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        m["tenant_id"],
                        m["doc_id"],
                        m["title"],
                        m["doc_type"],
                        m["data_class"],
                        m["status"],
                        m["effective_date"],
                        m.get("supersedes"),
                        m.get("contradicts"),
                        version,
                    ),
                )
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO chunks (tenant_id, doc_id, chunk_index, heading, data_class,"
                    " content, embedding, kb_version) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    [
                        (
                            m["tenant_id"],
                            m["doc_id"],
                            c.index,
                            c.heading,
                            m["data_class"],
                            c.text,
                            vec,
                            version,
                        )
                        for (m, c), vec in zip(rows, vectors, strict=True)
                    ],
                )
    print(f"Ingested as {version}")
    return version


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest the knowledge bases.")
    parser.add_argument("--run-evals", action="store_true", help="run regression evals after")
    args = parser.parse_args()
    ingest()
    if args.run_evals:
        cmd = [sys.executable, "-m", "evals.run", "--suite", "regression"]
        # Fixed argv, no shell.
        return subprocess.call(cmd)  # noqa: S603  # nosec B603
    return 0


if __name__ == "__main__":
    sys.exit(main())
