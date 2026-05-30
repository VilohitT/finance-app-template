# Project navigation — read first for any agent session

You are operating in an **Indian-context personal investment planning system** running locally in Claude Code. The user has cloned this template and is building up their own foundation files through guided interviews.

## Foundation files — read in this order when relevant

1. **`goals.md`** — what the user wants (retirement target, dependents, income, surplus, tax bracket, risk tolerance). Populated by `/finance-grill`. If empty, the user hasn't done initial setup yet.
2. **`principles.md`** — the universal Indian-context investing framework (philosophy, vehicles, deployment priority, drift correction, behavioural guardrails). Never user-specific. Static; updated rarely.
3. **`user-principles.md`** — the user's structural choices on top of the framework: sub-portfolio architecture (single or multi-entity), sleeve targets, glide paths, money routing, tax regime, vehicles in use, drift bands, STP threshold. Populated by `/principles-grill`. **Authority for any numeric target or routing rule.**
4. **`portfolio.md`** — what the user owns. Populated by `/portfolio-grill`. Section 1.5 auto-rendered from `data/transactions.json` — never hand-edit.
5. **`decisions-log.md`** — append-only audit trail. Skills (`portfolio-review`, `fund-allocate`) write here; never edit by hand.
6. **`laws/`** — current Indian tax and scheme rules. 12 files covering capital gains, equity/debt MF, PPF, EPF/VPF, NPS, SCSS, gold, SEBI categories, regime comparison, insurance. Updated post-Budget via `/laws-refresh`.

## Skills available

- `/setup` — one-shot first-run installer (Python prereqs, NAV bootstrap, daily cron)
- `/finance-grill` — interviews user → populates `goals.md` (~30 min)
- `/principles-grill` — interviews user → populates `user-principles.md` (~10-15 min)
- `/portfolio-grill` — interviews user → populates `portfolio.md` (~20-40 min)
- `/portfolio-review` — weekly check-in; drift, tax, scheme-level signals; writes to `decisions-log.md`
- `/fund-allocate` — fresh-money routing across sleeves/sub-portfolios; writes to `decisions-log.md`
- `/fund-research` — populates `data/fund_quality.json` for sparse categories
- `/laws-refresh` — refreshes `laws/` post-Budget; never silent writes
- `/tax-check` — internal plumbing; computes tax cost of contemplated transactions

## Data layer

- `data/market.db` — SQLite. `schemes` table has ~14k Indian MFs (catalogue); `nav_history` grows daily; `fetch_log` audit. Populated by `scripts/fetch_nav.py`.
- `data/transactions.json` — append-only MF transaction ledger (source of truth for holdings).
- `data/fund_quality.json` — TER/manager/AUM overlay; populated by `/fund-research`.
- `data/recurring.json` — active SIPs/STPs; consumed by `scripts/recurring_runner.py` monthly.

## Scripts

All scripts in `scripts/`. Key entry points:
- `scripts/discover.py` — Phase 0 mandatory snapshot before any review/allocation run (NAV freshness, ledger health, fund-quality coverage, drawdown gate, open ACTIONs).
- `scripts/fetch_nav.py` — daily AMFI NAV refresh (cron'd via launchd/cron).
- `scripts/recurring_runner.py` — monthly SIP/STP tranche generator (cron'd).
- `scripts/render_portfolio.py --json` — structured holdings snapshot from ledger × NAVs.
- `scripts/log_transaction.py` — append a one-off purchase to the ledger.
- `scripts/resolve_schemes.py` — fuzzy-match scheme names → AMFI scheme codes.

Library modules in `scripts/lib/`: `allocation`, `drawdown`, `freshness`, `fund_quality`, `projection`, `returns`, `stp_plan`, `transactions`, `db`.

## Conventions

- **All amounts in INR.** ₹ symbol everywhere.
- **All dates ISO 8601 (YYYY-MM-DD).**
- **Tax regime:** read `user-principles.md` §7 for committed regime; never assume.
- **Sub-portfolio names:** read from `user-principles.md` §2; never hardcode names like "user" / "father" / "me" / "spouse".
- **Sleeve targets:** read from `user-principles.md` §3; never hardcode percentages.
- **Stable IDs in `decisions-log.md`:** ACTION/WATCH/INFO-YYYY-MM-DD-NNN (portfolio-review), ALLOC-YYYY-MM-DD-NNN (fund-allocate).
- **Mandatory Phase 0** for `/portfolio-review` and `/fund-allocate`: run `scripts/discover.py` first and quote its output before any other work.
- **Never silent writes** to `laws/` or `fund_quality.json` — always propose diff, await user approval.
- **Direct plans only** for new MF investments (per `principles.md` §3.1).

## First-time user flow

If you detect this is a freshly-cloned template (empty `goals.md`, empty `portfolio.md`, etc.), point the user at `GETTING_STARTED.md` and recommend the sequence:
1. `/setup` (5-10 min)
2. `/finance-grill` (~30 min)
3. `/principles-grill` (~10-15 min)
4. `/portfolio-grill` (~20-40 min)
5. Then routine: `/portfolio-review` weekly, `/fund-allocate` on fresh money.
