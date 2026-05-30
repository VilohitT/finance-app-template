# Getting Started

A Claude Code-based personal investment planning system for the Indian context. You run interviews in Claude Code; the system builds a complete picture of your finances; specialist skills then surface recommendations on demand.

---

## What this system does (and doesn't)

**Does:**
- Captures your goals, principles, and portfolio into structured markdown files you own.
- Mirrors every Indian mutual fund's NAV history locally (via AMFI).
- Computes allocation drift against your stated targets; surfaces tax-aware sell/switch opportunities.
- Plans where fresh money should go (SIPs, lumps, surplus) across your sub-portfolio structure.
- Tracks every recommendation in an auditable decisions log.

**Doesn't:**
- Execute trades. You execute via your broker; the system advises.
- Send any data anywhere. Local-first. No telemetry, no cloud calls except AMFI for daily NAVs.
- Sell you anything or take a fee. Open template; your data stays on your machine.

---

## Prerequisites (~5 min)

- **Python 3.10+** in your PATH. Check with `python3 --version`.
  - macOS: `brew install python` (or use the python.org installer)
  - Linux: `sudo apt install python3 python3-pip` (Debian/Ubuntu) or distro equivalent
  - Windows: download from python.org
- **`requests`** package. Install with `pip3 install requests`.
- **Claude Code CLI.** Install per claude.com/claude-code instructions; open this directory.
- **SQLite3** (usually bundled with Python; no separate install needed).

---

## Day 1 setup (~70 minutes total)

### 1. `/setup` (5-10 min)

One-shot installer. Verifies Python prereqs, bootstraps `data/market.db` with today's NAVs (~14,000 schemes), and offers to install a daily NAV refresh cron job (macOS launchd, Linux cron, Windows manual). Confirms all foundation file scaffolds are present.

When it finishes, you'll have a working data layer and a clear "run `/finance-grill` next" pointer.

### 2. `/finance-grill` (~30 min)

Structured interview that captures everything an investment planner needs to know about you:
- Personal context (DOB, dependents, household)
- Income & cash flow (gross, take-home, tax regime, monthly surplus)
- Existing assets & corpus
- Insurance & protection
- Goals (retirement, property, education, legacy — Socratic, helps you discover goals you haven't articulated)
- Risk tolerance (with behavioural scenarios, not self-rated)
- Tax priorities & preferences
- Knowledge level & review cadence

Produces **`goals.md`**.

### 3. `/principles-grill` (~10-15 min)

Captures your investment *structure* on top of the universal framework in `principles.md`:
- Single portfolio or multi-entity sub-portfolios? (Option A vs Option B)
- Per sub-portfolio: equity/debt/gold sleeve targets, glide paths
- Goal-bucket overlay (which goals are funded from where)
- Money routing rules (which inflow → which sub-portfolio)
- Tax regime committed this FY (New vs Old)
- Vehicles in use or planned (PPF, EPF/VPF, NPS, SCSS, SSY, SGB)
- Drift correction policy, STP threshold

Produces **`user-principles.md`**.

### 4. `/portfolio-grill` (~20-40 min)

Captures every holding:
- Mutual funds (scheme, plan, cost basis, purchase month, SIP active y/n)
- Government schemes (PPF, EPF/VPF, NPS, SCSS, SSY)
- Gold (SGBs, MFs, physical)
- Debt (FDs, bonds)
- Direct equities (if any)
- Real estate
- Insurance assets
- Liabilities

By default, runs in *minimal-capture mode* for MFs (7 fields per scheme); the ledger backfills units and current values. Opt into heavy mode if you need full precision.

Produces **`portfolio.md`** + appends to `data/transactions.json`.

### 5. Optionally `/fund-research` (~20 min)

If your portfolio has gaps (categories where you don't yet hold a fund and your scheme universe is sparse), this skill researches candidates from Value Research / Freefincal / AMC factsheets and populates `data/fund_quality.json`. Run when `/fund-allocate` flags sparse-data for a category, or proactively for categories you want to deploy into.

---

## Day 2 onwards (recurring)

| When | What |
|------|------|
| Daily (auto) | `scripts/fetch_nav.py` runs at 22:30 IST via cron/launchd installed during `/setup`. ~14,000 NAVs refreshed nightly. Zero attention from you. |
| Weekly (you) | `/portfolio-review` — drift, tax, scheme-level signals. ~5 minutes; most reviews show no action. |
| On fresh money | `/fund-allocate` — where should this money go? ~15-30 minutes including selection and logging. |
| After Union Budget (Feb) | `/laws-refresh` — propose diffs to `laws/` from authoritative sources. ~30-60 min. |
| Life event | Re-run `/finance-grill` (income/dependent/job change) or `/portfolio-grill` (large redemption/scheme switch). |
| Quarterly | Spot-check the daily cron is still running: `launchctl list \| grep financeapp` (macOS) or `crontab -l \| grep financeapp` (Linux). |

---

## The 4-layer mental model

```
┌─ Layer 1: YOU ───────────────────────────────────────────────┐
│  Chat in Claude Code. Make decisions. Execute trades at your  │
│  broker.                                                       │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌─ Layer 2: SKILLS ────────▼───────────────────────────────────┐
│  Markdown prompts in .claude/skills/. Each skill is a         │
│  specialist: finance-grill interrogates goals, portfolio-     │
│  review spots drift, fund-allocate routes fresh money, etc.   │
└─────┬────────────────────────────────────┬───────────────────┘
      │ (skills invoke scripts)             │ (skills read/write)
┌─ Layer 3a: SCRIPTS ──┐         ┌─ Layer 3b: FOUNDATION FILES ┐
│  Python in scripts/. │         │  goals.md, principles.md,    │
│  fetch_nav.py, etc.  │         │  user-principles.md,         │
│  Do mechanical work. │         │  portfolio.md, laws/,        │
└─────┬────────────────┘         │  decisions-log.md            │
      │ (scripts read/write)     └──────────────────────────────┘
┌─ Layer 4: DATA STORE ─────────────────────────────────────────┐
│  data/market.db (SQLite — schemes, nav_history, fetch_log)    │
│  data/transactions.json — MF transaction ledger                │
│  data/fund_quality.json — TER/manager/AUM overlay              │
│  data/recurring.json — active SIPs/STPs                        │
└────────────────────────────────────────────────────────────────┘
```

**Key asymmetry:** skills call scripts; scripts never call skills. Code is dumb infrastructure. Skills are the orchestrators. Foundation files hold *your* state. Data store holds market state.

See `system-walkthrough.md` for the deep dive.

---

## What lives where

| File / dir | Owner | Updated by |
|---|---|---|
| `goals.md` | Yours | `/finance-grill` |
| `principles.md` | Template (universal) | Static; rarely edited |
| `user-principles.md` | Yours | `/principles-grill` |
| `portfolio.md` | Yours | `/portfolio-grill` (manual sections); `render_portfolio.py` (Section 1.5 auto) |
| `decisions-log.md` | Yours | `/portfolio-review`, `/fund-allocate` append |
| `laws/` | Template (current Indian rules) | `/laws-refresh` post-Budget |
| `data/market.db` | Auto | `scripts/fetch_nav.py` daily |
| `data/transactions.json` | Yours | `/portfolio-grill` (initial); `/fund-allocate` + `recurring_runner.py` ongoing |
| `data/fund_quality.json` | Yours | `/fund-research` |
| `data/recurring.json` | Yours | `/fund-allocate` |

---

## Troubleshooting

**"Python is not found" or version too old**
- Run `which python3` and `python3 --version`. Need 3.10+. Use Homebrew/apt to install if needed.

**"requests is not installed"**
- `pip3 install requests` (or `pip3 install --user requests` if you don't have root).

**`/setup` says daily cron didn't install**
- macOS: check `~/Library/LaunchAgents/com.<your-username>.financeapp.fetchnav.plist` exists. Reload with `launchctl unload ... && launchctl load ...`.
- Linux: check `crontab -l` shows the line.
- You can also just run `python3 scripts/fetch_nav.py --quiet` manually whenever you remember.

**`/portfolio-review` says "live data unavailable"**
- Run `python3 scripts/fetch_nav.py` directly and watch the output. If AMFI is unreachable, it's transient — retry later. If the script errors, file an issue with the traceback.

**Tests**
- Run `for t in scripts/tests/test_*.py; do python3 "$t"; done` to confirm the Python layer is intact. All tests use temp DBs; they never touch your real `data/market.db`.

---

## Privacy

Everything runs locally on your machine. The only outbound network calls are:
- `scripts/fetch_nav.py` → `https://www.amfiindia.com/spages/NAVAll.txt` (daily, ~5MB)
- `scripts/fetch_nav_history.py` → `https://api.mfapi.in/mf/<scheme_code>` (one-off backfill of held schemes)
- `/fund-research` → Value Research, Freefincal, AMC factsheet URLs (only when you explicitly invoke this skill)
- `/laws-refresh` → official Indian gov sites and reputable tax publications (only when you explicitly invoke this skill)

No telemetry. No accounts. No remote sync. Your `goals.md`, `portfolio.md`, `decisions-log.md` never leave the machine.
