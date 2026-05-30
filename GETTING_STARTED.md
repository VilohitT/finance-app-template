# Getting Started

A local-first investment planning system for the Indian context. You run interviews in chat; the agent builds a complete picture of your finances into structured markdown files; specialist skills surface recommendations on demand.

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
- Send any of your data anywhere. Local-first. Only AMFI for daily NAVs, plus public web sources when you explicitly invoke `/fund-research` or `/laws-refresh`.
- Sell you anything or take a fee. Open template; your data stays on your machine.

---

## Prerequisites

- Docker (Docker Desktop on Mac/Windows, `docker` + `docker compose` on Linux).
- An Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com/). Free tier works for evaluating; you'll want a paid plan for routine use.

That's it. No Python install on your machine — everything runs in the container.

---

## Day 1 setup (~70 minutes)

### 1. Start the container (~1 min)

```bash
mkdir -p ~/finance-app-data
docker run -d --name finance-app \
  -p 8000:8000 \
  -v ~/finance-app-data:/app/project \
  ghcr.io/vilohitt/finance-app-template:latest
```

Open http://localhost:8000.

The `-v ~/finance-app-data:/app/project` mount is where your data lives — foundation md files, `data/market.db` with NAV history, transactions ledger, API key, scripts and laws. On first start, the empty directory is seeded from the image with default scaffolds; subsequent restarts preserve everything.

### 2. Paste your Anthropic API key (~1 min)

Click **settings** in the header, paste your key, click Save. Back on the chat page, the welcome card flips step 1 to ✓.

### 3. `/setup` (~5-10 min)

Type `/setup` in the chat (or just `/` and pick from the dropdown), press Enter. The agent:
- Verifies the Python prereqs inside the container
- Bootstraps `data/market.db` with today's NAVs across ~14,000 schemes (first run takes ~30-60s)
- Confirms all foundation file scaffolds are present
- Tells you to run `/finance-grill` next

### 4. `/finance-grill` (~30 min)

Structured interview capturing your situation:
- Personal context (DOB, dependents, household)
- Income & cash flow (gross, take-home, tax regime, monthly surplus)
- Current assets & corpus
- Insurance
- Goals (retirement, property, education, legacy — Socratic, helps you discover goals you haven't articulated)
- Risk tolerance (with behavioural scenarios)
- Tax preferences
- Knowledge level & review cadence

Produces **`goals.md`** in your data directory.

### 5. `/principles-grill` (~10-15 min)

Captures your investment *structure* on top of the universal framework in `principles.md`:
- Single portfolio vs multi-entity sub-portfolios
- Sleeve targets (equity/debt/gold %)
- Glide paths
- Goal-bucket overlay
- Money routing rules
- Tax regime committed this FY
- Vehicles in use (PPF, EPF/VPF, NPS, SCSS, SSY, SGB)
- Drift policy, STP threshold

Produces **`user-principles.md`**.

### 6. `/portfolio-grill` (~20-40 min)

Captures every holding:
- Mutual funds (scheme, plan, cost basis, purchase month)
- Government schemes (PPF, EPF/VPF, NPS, SCSS, SSY)
- Gold (SGBs, MFs, physical)
- Debt (FDs, bonds)
- Direct equities (if any)
- Real estate, insurance, liabilities

Produces **`portfolio.md`** and seeds `data/transactions.json`.

### 7. (Optional) `/fund-research`

If your portfolio has categories where you don't yet hold a fund, this skill researches candidates from Value Research / Freefincal / AMC factsheets and populates `data/fund_quality.json`. Run when `/fund-allocate` flags sparse-data, or proactively for categories you want to deploy into.

---

## Day 2 onwards

| When | What |
|------|------|
| Daily (auto, inside container) | `scripts/fetch_nav.py` runs at 22:30 IST. ~14k NAVs refreshed nightly. Zero attention from you. Toggleable in /settings. |
| Monthly 6th (auto) | `recurring_runner.py` generates ledger rows for any scheduled SIPs/STPs, then `render_portfolio.py` refreshes Section 1.5 of `portfolio.md`. |
| Weekly (you) | `/portfolio-review` — drift, tax, scheme-level signals. ~5 min; most reviews show no action. |
| On fresh money | `/fund-allocate` — where should this money go? ~15-30 min. |
| After Union Budget (Feb) | `/laws-refresh` — propose diffs to `laws/` from authoritative sources. ~30-60 min. |
| Life event | Re-run `/finance-grill` (income/dependent/job change) or `/portfolio-grill` (large redemption/scheme switch). |

---

## The 4-layer mental model

```
┌─ YOU ────────────────────────────────────────────────────────┐
│  Chat in the web UI. Make decisions. Execute trades at your   │
│  broker.                                                       │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌─ SKILLS ─────────────────▼───────────────────────────────────┐
│  Markdown prompts in .claude/skills/. Each skill is a         │
│  specialist: finance-grill interrogates goals, portfolio-     │
│  review spots drift, fund-allocate routes fresh money.        │
└─────┬────────────────────────────────────┬───────────────────┘
      │ skills invoke scripts               │ skills read/write
┌─ SCRIPTS ─────────────┐         ┌─ FOUNDATION FILES ──────────┐
│  Python in scripts/.   │         │  goals.md, principles.md,    │
│  fetch_nav.py,         │         │  user-principles.md,         │
│  discover.py, etc.     │         │  portfolio.md, laws/,        │
└─────┬─────────────────┘         │  decisions-log.md            │
      │                            └──────────────────────────────┘
┌─ DATA STORE ──────────────────────────────────────────────────┐
│  data/market.db (SQLite — schemes, nav_history, fetch_log)     │
│  data/transactions.json — MF transaction ledger                 │
│  data/fund_quality.json — TER/manager/AUM overlay               │
│  data/recurring.json — active SIPs/STPs                         │
└────────────────────────────────────────────────────────────────┘
```

See [`system-walkthrough.md`](system-walkthrough.md) for the deep dive.

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

**Container won't start**
- Check `docker logs finance-app` — usually a port collision or volume permission issue.
- Make sure nothing else is on `:8000`, or change the port mapping: `-p 8080:8000`.

**Chat says "No Anthropic API key configured"**
- Visit `/settings`, paste your key from console.anthropic.com, save. Come back to `/`.
- The key is stored at `.config/settings.json` inside the container (mode 0600), which maps to `~/finance-app-data/.config/settings.json` on your host.

**Scheduler "Run now" fails with exit code != 0**
- Open the expanded "Show last output" pane to see the script's stderr.
- Usually it's a missing script dependency (re-pull the image to update) or a network blip reaching AMFI.

**Stop / restart**
```bash
docker stop finance-app    # stops the container; data persists
docker start finance-app   # resumes
docker rm finance-app      # removes the container (data still persists in ~/finance-app-data)
```

**Upgrade to a newer image**
```bash
docker pull ghcr.io/vilohitt/finance-app-template:latest
docker stop finance-app && docker rm finance-app
docker run -d --name finance-app -p 8000:8000 \
  -v ~/finance-app-data:/app/project \
  ghcr.io/vilohitt/finance-app-template:latest
```

> **Picking up template updates after upgrade.** The seed step only fills in
> missing files. To pick up changes the new image makes to `laws/`,
> `scripts/`, or the framework `principles.md`, delete the specific file or
> directory under `~/finance-app-data` and restart — the seed will copy the
> new version. Your `goals.md`, `user-principles.md`, `portfolio.md`,
> `decisions-log.md`, and `data/` are user-owned and never touched by upgrade.

---

## Privacy

The only outbound network calls are:
- `scripts/fetch_nav.py` → `https://www.amfiindia.com/spages/NAVAll.txt` (daily, ~5MB)
- `scripts/fetch_nav_history.py` → `https://api.mfapi.in/mf/<scheme_code>` (one-off backfill of held schemes)
- Calls to `https://api.anthropic.com/` for chat (with your API key)
- `/fund-research` → Value Research, Freefincal, AMC factsheet URLs (only when you explicitly invoke this skill)
- `/laws-refresh` → official Indian gov sites and reputable tax publications (only when you explicitly invoke this skill)

No telemetry. No accounts. No remote sync. Your `goals.md`, `portfolio.md`, `decisions-log.md` never leave your machine unless you copy them somewhere yourself.
