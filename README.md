# finance-app — Indian-context personal investment planner

A local-first investment planning system. Captures your goals and structure through guided interviews, mirrors every Indian mutual fund's NAV history locally, and runs specialist "skills" that surface drift, tax opportunities, and fresh-money allocations on demand.

**No cloud. No telemetry. No fee.** Your data stays on your machine — you bring your own Anthropic API key.

Two ways to run it:

## Option A — Standalone web app (recommended for most users)

A Docker image bundles a Python backend (FastAPI + Anthropic SDK) and a Next.js web UI. You run it locally; your data lives in a directory on your machine; you paste your Anthropic API key into the settings page.

```bash
git clone <this-repo>
cd finance-app-template
docker compose up --build
# Open http://localhost:8000
```

In the web UI:
1. Visit `/settings`, paste your Anthropic API key.
2. Run `/setup` to bootstrap the data layer.
3. Run `/finance-grill`, `/principles-grill`, `/portfolio-grill` to populate your foundation files.
4. From then on: `/portfolio-review` weekly, `/fund-allocate` on fresh money.

See [`GETTING_STARTED.md`](GETTING_STARTED.md) for the full Day-1 walkthrough.

> **Phase 1 (current state):** backend agent loop, tool registry, and WebSocket transport are wired; chat UI lands in Phase 2. The `/settings` page works today.

## Option B — Claude Code (CLI users)

If you already use Claude Code, the same skills run there without the web UI:

```bash
pip3 install requests
# Open the directory in Claude Code:
/setup
/finance-grill
/principles-grill
/portfolio-grill
```

The foundation files (`goals.md`, `portfolio.md`, etc.) are identical between modes — switching is just a matter of which client you open.

## Deep dives

- [`GETTING_STARTED.md`](GETTING_STARTED.md) — Day-1 walkthrough
- [`system-walkthrough.md`](system-walkthrough.md) — architectural deep dive
- [`backend/README.md`](backend/README.md) — backend dev notes
- [`frontend/README.md`](frontend/README.md) — frontend dev notes

## What's in this template

- 9 skills (`.claude/skills/`) — interview, review, allocate, research, refresh laws, tax check
- 12 laws files (`laws/`) — Indian tax & scheme rules, current as of Budget 2026
- ~1,500 lines of Python (`scripts/`) — NAV fetcher, ledger helpers, allocation solver, drawdown gate
- Pre-seeded data layer (`data/market.db` with ~14,000 schemes catalogued)
- Empty foundation scaffolds (`goals.md`, `portfolio.md`, etc.) — you populate via the grills

## Requirements

- Python 3.10+
- `requests` package (`pip3 install requests`)
- Claude Code CLI
- macOS / Linux / Windows (daily cron differs per platform; the `/setup` skill handles it)

## Privacy

The only outbound network calls are:
- AMFI (daily NAV refresh, ~5MB)
- mfapi.in (one-off historical NAV backfill for held schemes)
- Public web sources (only when you explicitly invoke `/fund-research` or `/laws-refresh`)

Your `goals.md`, `portfolio.md`, and `decisions-log.md` never leave your machine.

## License

MIT — fork freely, adapt to your situation.
