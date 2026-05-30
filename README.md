# finance-app — Indian-context personal investment planner

A local-first Claude Code template for personal investment planning in the Indian context. Captures your goals and structure through guided interviews, mirrors every Indian mutual fund's NAV history locally, and runs specialist "skills" that surface drift, tax opportunities, and fresh-money allocations on demand.

**No cloud. No telemetry. No fee.** Your data stays on your machine.

## Quick start

```bash
# 1. Clone this template
git clone <this-repo>  # or copy the directory
cd finance-app-template

# 2. Install Python deps
pip3 install requests

# 3. Open in Claude Code and run:
/setup            # one-shot installer (~5-10 min)
/finance-grill    # interview → goals.md (~30 min)
/principles-grill # interview → user-principles.md (~10-15 min)
/portfolio-grill  # interview → portfolio.md (~20-40 min)

# Then routine:
/portfolio-review # weekly check-in
/fund-allocate    # when fresh money arrives
```

See [`GETTING_STARTED.md`](GETTING_STARTED.md) for the full Day-1 walkthrough.
See [`system-walkthrough.md`](system-walkthrough.md) for the deep architectural dive.

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
