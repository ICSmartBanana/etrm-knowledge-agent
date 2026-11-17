#!/bin/bash
# Start a private Postgres inside the container, create the schema and roles (with fresh random
# passwords), ingest the synthetic corpus, then serve the API on 7860. Nothing persists between
# restarts, and nothing needs to: the corpus is part of the image.
set -euo pipefail

pw() { python -c "import secrets; print(secrets.token_urlsafe(24))"; }
export ETRM_OWNER_PASSWORD="$(pw)" ETRM_APP_PASSWORD="$(pw)" ETRM_INGEST_PASSWORD="$(pw)"
export ETRM_DB_HOST=127.0.0.1 ETRM_DB_PORT=5432
export PGDATA=/tmp/pgdata PGHOST=127.0.0.1 PGPORT=5432

pwfile=$(mktemp)
printf '%s' "$ETRM_OWNER_PASSWORD" > "$pwfile"
initdb -D "$PGDATA" -U etrm_owner --pwfile="$pwfile" --auth=scram-sha-256 -E UTF8 >/dev/null
rm -f "$pwfile"
pg_ctl -D "$PGDATA" -o "-c listen_addresses=127.0.0.1 -k /tmp" -l /tmp/postgres.log -w start

export PGPASSWORD="$ETRM_OWNER_PASSWORD"
createdb -U etrm_owner etrm
POSTGRES_USER=etrm_owner POSTGRES_DB=etrm bash db/init/01_schema.sh >/dev/null
unset PGPASSWORD ETRM_OWNER_PASSWORD

python -m ingest.cli
exec uvicorn app.api.main:app --host 0.0.0.0 --port 7860 --proxy-headers --forwarded-allow-ips='*'
