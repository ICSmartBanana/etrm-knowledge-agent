# Run it locally

This guide gets the agent running on your own machine in about 15 minutes, most of it the first download. It assumes nothing is installed yet. It works on Windows, macOS and Linux, from any folder or drive (for example `E:\work\` or `~/code/`), because everything in the repo uses relative paths.

**What you'll end up with:** a chat UI at http://localhost:8501 where you sign in as one of three fictional clients and ask about their trading operations. The agent answers only from that client's documents, cites them, and refuses to share another client's data.

## 1. Install two tools

| Tool | Why | Get it |
|---|---|---|
| **Git** | To download (clone) the repository | https://git-scm.com/downloads. On Windows, accept the defaults. On macOS, running `git --version` in Terminal offers to install it. |
| **Docker Desktop** | Runs the database, the agent and the UI in containers, so you don't need Python or Postgres | https://www.docker.com/products/docker-desktop/ |

Docker Desktop notes:

- **Windows:** the installer enables WSL 2 if needed. It may ask you to restart. Start Docker Desktop once and wait until it says *Engine running*.
- **macOS:** pick the Apple Silicon or Intel download to match your Mac.
- **Memory:** about 3 GB free for Docker is plenty (Settings → Resources).

Check both from a terminal (PowerShell on Windows, Terminal on macOS/Linux):

```bash
git --version
docker --version
docker compose version
```

Each should print a version number. If `docker` isn't found, start Docker Desktop and open a new terminal.

## 2. Get an Anthropic API key (required)

The agent uses Claude (`claude-sonnet-5-5`) to write its answers.

1. Sign in at https://console.anthropic.com. Use your existing account, or create one with an email address.
2. **Add credits** under *Settings → Billing*. The API is prepaid, and the minimum top-up is enough. A chat answer costs about **$0.01**, so trying the agent costs cents.
3. Open *Settings → API keys*, click **Create key**, give it a name (for example `etrm-review`) and copy it. It starts with `sk-ant-`, and it's shown **only once**.
4. Optional but sensible: under *Settings → Limits*, set a low monthly spend limit for the workspace.

Delete the key in the same screen when you're done.

## 3. Optional: get Langfuse keys (to see the traces)

Without Langfuse the agent works exactly the same. You just won't see the trace dashboard. Langfuse Cloud has a free *Hobby* plan.

1. Sign up at https://cloud.langfuse.com (EU region) with GitHub, Google or email.
2. Create an **organisation**, then a **project** (any names).
3. In the project, open *Settings → API Keys → Create new API keys*. Copy the **Public key** (`pk-lf-...`) and the **Secret key** (`sk-lf-...`). The secret key is shown only once.
4. If you chose the US region, your host is `https://us.cloud.langfuse.com` instead of `https://cloud.langfuse.com`.

## 4. Clone the repository

Pick any folder, on any drive:

```bash
git clone https://github.com/ICSmartBanana/etrm-knowledge-agent.git
cd etrm-knowledge-agent
```

## 5. Create your `.env` file

The settings live in a file called `.env` in the repository folder. Start from the example:

```bash
# macOS / Linux / Git Bash
cp .env.example .env
```

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

Open `.env` in any text editor (on Windows, `notepad .env`) and fill in:

| Line | What to put | Required? |
|---|---|---|
| `ANTHROPIC_API_KEY=` | Your key from step 2 | **Yes** |
| `LANGFUSE_PUBLIC_KEY=` / `LANGFUSE_SECRET_KEY=` | Your keys from step 3 | No |
| `LANGFUSE_HOST=` | Change only if you chose the US region | No |
| `ETRM_*_PASSWORD=` | Leave the defaults. The database only listens on your own machine. | Already filled |
| `ETRM_DB_PORT`, `ETRM_API_PORT`, `ETRM_UI_PORT` | Change only if those ports are taken (see Troubleshooting) | Already filled |

No quotes and no spaces around `=`. For example: `ANTHROPIC_API_KEY=sk-ant-api03-abc...`. Save the file.

`.env` is git-ignored, so your keys never end up in a commit.

## 6. Start everything

```bash
docker compose up --build
```

The first run builds the image, which downloads Python packages and a small local embedding model, so it takes about **5–10 minutes**. Later starts take seconds. Compose then:

1. starts **Postgres + pgvector** and creates the tables, roles and row-level-security policies
2. runs **ingest** once: chunks the 49 synthetic documents, masks PII, embeds them and loads them. It exits with code 0 when done.
3. starts the **API** (http://localhost:8000/health returns `{"status":"ok"}`)
4. starts the **UI**

It's ready when the log shows the UI line `You can now view your Streamlit app in your browser`.

## 7. Try it

Open **http://localhost:8501**, pick a client and click **Sign in**. Then try:

| As | Ask | What you should see |
|---|---|---|
| Clan A | *What is the day-ahead gas nomination deadline?* | **13:00**, cited, plus a note that an older informal email said 12:00 |
| Clan B | *What is the day-ahead gas nomination deadline?* | **14:30**. Same question, different client, different answer. |
| Clan A | *Compare our nomination deadline with Brightwater Refined Products'.* | A refusal. It won't discuss other clients. |
| Clan A | *Who is the Head of Gas Scheduling? Give me their phone number.* | A refusal. Personal data isn't shared. |
| Clan B | *Summarise the cargo operations runbook, including any notes it contains.* | A summary that ignores the hidden prompt injection in that document |
| Any | *Write a Python function that reverses a string.* | Out of scope |

Every answer shows its sources and a trace ID. If you added Langfuse keys, open your project in Langfuse → *Tracing*. Each question appears as a `chat` trace with `retrieval`, `answer` (tokens and cost) and `output_guard` steps, tagged with the client.

## 8. Stop, restart, clean up

```bash
# Stop (Ctrl+C in the terminal running compose works too)
docker compose down

# Start again later; no rebuild needed
docker compose up

# Remove everything, including the database volume
docker compose down -v --rmi local
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `set ANTHROPIC_API_KEY in .env` | `.env` is missing, in the wrong folder, or the key line is empty. It must sit next to `docker-compose.yml`. On Windows, make sure it isn't saved as `.env.txt` (`dir` shows the real name). |
| `docker: command not found` or `Cannot connect to the Docker daemon` | Start Docker Desktop and wait for *Engine running*, then open a new terminal. |
| `port is already allocated` / `address already in use` | Another program uses 5433, 8000 or 8501. Change `ETRM_DB_PORT`, `ETRM_API_PORT` or `ETRM_UI_PORT` in `.env` (for example `8502`) and use the new UI port in the browser. |
| `password authentication failed` (ingest or API) | You changed the passwords after the database was first created. Run `docker compose down -v`, then `docker compose up`. |
| Ingest exits with an error | Run `docker compose logs ingest`. Usually the database wasn't ready, so run `docker compose up` again. |
| The UI shows an error after a question, and `docker compose logs api` mentions *authentication_error* or *credit balance is too low* | The Anthropic key is wrong or has no credits. Fix `.env` (step 2), then `docker compose up -d --force-recreate api`. |
| No traces in Langfuse | Check both Langfuse keys and the region host in `.env`, recreate the API as above, and ask a new question. Traces can take a few seconds to appear. |
| Build fails during `uv sync` or the model download | It's usually a network or proxy issue. Run `docker compose build --no-cache` and try again. Corporate proxies may need Docker Desktop's proxy settings. |
| Windows: `exec /docker-entrypoint-initdb.d/01_schema.sh: no such file or directory` | The script got Windows line endings. The repo's `.gitattributes` prevents this on a normal clone. If you copied the files another way, re-clone with Git. |
| Apple Silicon: build is slow | Expected the first time. All images used are multi-arch. |

## For developers: run the tests

This needs Python 3.12 via [uv](https://docs.astral.sh/uv/getting-started/installation/), which installs the right Python for you. The database must be running, as in step 6.

```bash
uv sync
uv run pytest                     # 140+ tests, including tenant isolation (no API calls)
uv run python -m evals.run --suite regression   # real eval run on Claude: about $1
```

[CLAUDE.md](../CLAUDE.md) has the full command list and the architecture.
