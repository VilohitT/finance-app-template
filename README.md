# finance-app — Indian-context personal investment planner

A local-first investment planning system. Captures your goals and structure through guided interviews, mirrors every Indian mutual fund's NAV history locally, and runs specialist "skills" that surface drift, tax opportunities, and fresh-money allocations on demand.

**No cloud. No telemetry. No fee.** Your data stays on your machine — you bring your own Anthropic API key.

## Quick start (Docker)

```bash
# 1. Run the image, mounting a local directory for your data
mkdir -p ~/finance-app-data
docker run -d --name finance-app \
  -p 8000:8000 \
  -v ~/finance-app-data:/app/project \
  ghcr.io/vilohitt/finance-app-template:latest

# 2. Open http://localhost:8000
# 3. Click "settings" → paste your Anthropic API key from console.anthropic.com
# 4. Back on the chat page, type /setup and press Enter
# 5. Follow the welcome card: /finance-grill → /principles-grill → /portfolio-grill
```

That's it. All data persists in `~/finance-app-data`. Stop the container any time; resume by restarting it. On first start, the directory is seeded from the image with foundation files, scripts, laws, and a pre-populated NAV scheme catalogue.

See [`GETTING_STARTED.md`](GETTING_STARTED.md) for the full Day-1 walkthrough.

## Build from source

```bash
git clone https://github.com/VilohitT/finance-app-template
cd finance-app-template
docker compose up --build
# Open http://localhost:8000
```

The compose file mounts `./project` (in the repo) as the user data directory — gitignored, created on first run.

## Local dev (without Docker)

Two terminals:

```bash
# Terminal 1 — backend (FastAPI + agent loop)
cd backend
pip install -r requirements.txt
PROJECT_ROOT=$(pwd)/.. SKILLS_ROOT=$(pwd)/../.claude/skills SCRIPTS_ROOT=$(pwd)/../scripts \
  uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend (Next.js)
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

## Claude Code (alternative client)

The same skills run inside Claude Code if you prefer the CLI:

```bash
pip3 install requests
# Open the directory in Claude Code:
/setup
/finance-grill
/principles-grill
/portfolio-grill
```

Foundation files (`goals.md`, `portfolio.md`, etc.) are identical between the web app and Claude Code modes.

## What lives where

| Layer | What | Where |
|---|---|---|
| Skills | 9 specialist prompts (setup, grills, review, allocate, etc.) | `.claude/skills/*/SKILL.md` |
| Foundation | `goals.md`, `principles.md`, `user-principles.md`, `portfolio.md`, `decisions-log.md` | repo root (web app) or mounted data volume |
| Indian rules | 12 markdown files: capital gains, equity/debt MF, PPF, NPS, etc. | `laws/` |
| Data | ~14k scheme catalogue + NAV history + ledger | `data/market.db`, `data/transactions.json` |
| Scripts | NAV fetcher, allocation helpers, FIFO tax calc | `scripts/` |

## Deep dives

- [`GETTING_STARTED.md`](GETTING_STARTED.md) — Day-1 walkthrough
- [`system-walkthrough.md`](system-walkthrough.md) — architectural deep dive
- [`backend/README.md`](backend/README.md) — backend dev notes
- [`frontend/README.md`](frontend/README.md) — frontend dev notes
