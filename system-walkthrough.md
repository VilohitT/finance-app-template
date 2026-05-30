# Investment Agent — System Walkthrough

A deep dive into the four architectural layers and how they connect to day-to-day usage. For the quick onboarding, see `GETTING_STARTED.md`.

---

## The mental model: 4 layers

Think of the system as four layers, with mostly one-way information flow:

```
┌─ Layer 1: YOU ────────────────────────────────────────────┐
│  The person making decisions, asking questions, executing │
│  trades at your broker                                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ (chat in Claude Code)
┌─ Layer 2: SKILLS ─────────▼──────────────────────────────────┐
│  Markdown prompts in .claude/skills/. Each skill is a         │
│  "trained specialist" — finance-grill knows how to            │
│  interrogate goals, portfolio-review knows how to spot drift, │
│  fund-allocate knows how to route fresh money.                │
└─────┬───────────────────────────────────────────┬────────────┘
      │ (skills invoke scripts)                    │ (skills read/write)
┌─ Layer 3a: SCRIPTS ──┐                  ┌─ Layer 3b: FOUNDATION FILES ─┐
│  Python in scripts/. │                  │  goals.md, principles.md,     │
│  fetch_nav.py, etc.  │                  │  user-principles.md,          │
│  Do mechanical work. │                  │  portfolio.md, laws/,         │
│                      │                  │  fund_quality.json,           │
│                      │                  │  decisions-log.md             │
└─────┬────────────────┘                  └────────────────────────────────┘
      │ (scripts read/write)
┌─ Layer 4: DATA STORE ───────────────────────────────────────┐
│  data/market.db (SQLite — schemes, nav_history, fetch_log)    │
│  ↑ populated by AMFI NAVAll.txt (daily) and mfapi.in (history) │
└──────────────────────────────────────────────────────────────┘
```

Layer 4 is mechanical (just data). Layer 3a is mechanical (just code). Layer 3b is your knowledge captured in markdown + JSON. Layer 2 is the intelligence — the skills know which Layer 3 things to use for which job. Layer 1 is you, asking questions in chat.

The asymmetry that matters: **skills can call scripts, but scripts never call skills**. Code is dumb infrastructure; skills are the orchestrators.

---

## Layer 4: What's in the data store

Two stores — one SQLite database and three JSON files — sitting at the project root.

**`data/market.db`** has three tables:

`schemes` — one row per Indian mutual fund scheme that AMFI has ever published a NAV for. ~14,000 rows. Columns: `scheme_code` (the ID), `scheme_name`, `amc`, `category` (e.g. "Equity Scheme - Mid Cap Fund"), `plan` ("Direct" / "Regular"), `option_type` ("Growth" / "IDCW"), `isin_growth`, `isin_div_reinv`, `first_seen`, `last_seen`. Nullable: `aum_crore`, `aum_date`.

`nav_history` — one row per (scheme, date). Composite primary key `(scheme_code, nav_date)`. Grows daily — one row per scheme per business day for the daily fetch (~14,000 rows/day). After running `fetch_nav_history.py` for your held schemes, you also have multi-year backfill for those specific schemes.

`fetch_log` — audit trail of every script run. `id`, `source` ("amfi_nav" / "mfapi_history"), `fetch_time`, `status` ("success" / "partial" / "fail"), `record_count`, `error_message`. The skills check this to see when data was last refreshed.

**`data/transactions.json`** — append-only MF transaction ledger. Each row has `txn_id`, `date`, `type` ("purchase" / "redemption" / "stp_in" / "stp_out" / "sip"), `scheme_code`, `scheme_name`, `amount_inr`, `nav`, `units`, `sub_portfolio` (per your `user-principles.md`), `source` ("backfill" / "user" / "sip" / "stp"), and link fields. This is the source of truth for MF holdings; Section 1.5 of `portfolio.md` is auto-rendered from this.

**`data/fund_quality.json`** — slow-moving qualitative data — TER, manager_name, manager_since (ISO date), aum_crore, last_verified, notes. Keyed by scheme_code as string. One entry per scheme you've researched. Populated by `/fund-research`.

**`data/recurring.json`** — active SIPs and STPs. Consumed by `scripts/recurring_runner.py` monthly to auto-generate ledger rows.

The whole "data layer" is conceptually small.

---

## Layer 3a: What each Python script does

**`scripts/lib/db.py`** — boring infrastructure. Connection helper (`get_conn`), schema definition for fresh installs, `_migrate_schema()` that idempotently adds columns to existing DBs. Everything else imports `get_conn` from here.

**`scripts/fetch_nav.py`** — fetches `https://www.amfiindia.com/spages/NAVAll.txt` once, parses the pipe-delimited format, upserts into `schemes` and `nav_history` tables. Idempotent (`INSERT OR IGNORE` on the composite key). Logs to `fetch_log`. The daily cron runs this.

**`scripts/fetch_nav_history.py`** — different source: `mfapi.in/api/mf/<scheme_code>` returns 5-15 years of daily NAVs per scheme as JSON. Reads `portfolio.md` to find your scheme codes + first-purchase dates, fetches history from each scheme's purchase date forward to today, upserts to `nav_history`. Conservative pacing. Idempotent. Run once after `/portfolio-grill`; re-run only if you add new holdings.

**`scripts/resolve_schemes.py`** — the bridge between human-readable scheme names ("Quant Mid Cap Fund — Direct G") and AMFI's scheme codes (120841). Fuzzy-matches each name against the `schemes` table, produces a confidence-tiered report (HIGH/MEDIUM/LOW/NONE), and writes resolutions back to `portfolio.md`. Used inline by `/portfolio-grill`.

**`scripts/check_freshness.py`** — parses laws/ and goals.md headers for `last_updated`, `review_due`, and budget-tag fields. Prints a structured staleness report. Used by `/laws-refresh` and `/finance-grill` for Phase 0 staleness scans.

**`scripts/discover.py`** — the mandatory Phase 0 entry point for `/portfolio-review` and `/fund-allocate`. Emits a 10-section structured report covering: helper inventory, script inventory, NAV freshness, ledger health, recurring registry, fund_quality coverage, laws/ staleness, decisions-log open ACTIONs, drawdown gate state per sub-portfolio, sub-portfolio totals. Skills quote its output before doing any work.

**`scripts/log_transaction.py`** — CLI for appending a one-off purchase / redemption / switch to the ledger. NAV resolved automatically from `data/market.db`.

**`scripts/render_portfolio.py`** — reads the ledger × current NAVs and either prints a JSON snapshot (`--json`) or writes Section 1.5 of `portfolio.md` (`--write`). Skills use the JSON output for drift / current-value computations.

**`scripts/backfill_units.py`** — one-shot tool to populate the ledger from a configuration file (used during `/portfolio-grill` to seed the initial ledger from captured cost-basis + purchase-month data).

**`scripts/build_quality_template.py`** — scaffolds empty entries in `fund_quality.json` for any scheme codes not already there. Idempotent. Used inside `/fund-research`.

**`scripts/recurring_runner.py`** — reads `data/recurring.json`, generates ledger entries for active SIPs/STPs whose scheduled date is ≤ today. Idempotent. The monthly cron runs this.

**`scripts/lib/*.py`** — helper modules:
- `allocation.py` — `optimal_sleeve_split()` for principle-§6.3-compliant per-sleeve flow assignment
- `drawdown.py` — `aggregate_equity_drawdown()` for the §6.4 rebalance-block gate; `classify_sleeve()` for grouping schemes
- `freshness.py` — header parsing for laws/ and goals.md
- `fund_quality.py` — query interface: `load_quality()`, `get_quality(scheme_code)`, `filter_candidates(...)` (the headline function `/fund-allocate` calls)
- `projection.py` — `project_drift()`, `project_corpus()`, `goal_progress()` for forward projections
- `returns.py` — `alpha_vs_benchmark()`, `tracking_error()`, `discover_benchmark_for_category()` for performance signals
- `stp_plan.py` — `plan_stp()`, `plan_lump_purchase()`, `should_use_stp()` for STP / lump decision and ledger row emission
- `transactions.py` — ledger I/O: `load_transactions()`, `cost_basis_per_scheme()`, `consume_fifo()`, `classify_gain()`, `current_value_per_scheme()`, etc.

**`scripts/com.template.financeapp.*.plist`** — macOS launchd config templates. Edit `{{PROJECT_ROOT}}` and load via `launchctl`. (Or run `/setup` to do this for you.)

**`scripts/cron-template.txt`** — Linux cron equivalent. Edit `{{PROJECT_ROOT}}` and append to your crontab.

**`scripts/tests/test_*.py`** — ~115 tests across files. Run them with `python3 scripts/tests/test_<name>.py`. They use temporary SQLite databases and synthetic fixtures, never touch your real `data/market.db`. Their job: regression-prove that code changes don't break the data layer's contract.

---

## Layer 3b: What the foundation files contain

These are markdown files at the project root that capture *your* situation and rules. Skills read them every run.

**`goals.md`** — what you want. Retirement target, property goals, current corpus, income & surplus, tax bracket & regime, risk tolerance, dependents, insurance state, preferences. Populated by `/finance-grill`. Re-grill on material life changes.

**`principles.md`** — the universal Indian-context investing framework. Philosophy (time in market, goal-bucketing, cost, diversification, discipline, tax efficiency), asset allocation framework (Option A/B architecture, within-equity SAA + TAA bands, debt sleeve framework, gold framework, drawdown handling), investment vehicles (Direct plans, no ULIPs), deployment priority framework (PPF → NPS → VPF → SIPs), rebalancing rules, behavioural guardrails, fresh fund allocation framework. Static; updated rarely.

**`user-principles.md`** — *your* structural choices on top of the framework: sub-portfolio architecture (single or multi-entity), per-sub-portfolio sleeve targets, glide paths, goal-bucket overlay, money routing rules, tax regime committed, vehicles in use, deployment priority overrides, drift bands, STP threshold. Populated by `/principles-grill`. **This is the authority for any numeric target or routing rule.**

**`portfolio.md`** — what you own. Every holding across asset classes (MFs, government schemes, gold, debt, real estate, insurance, alternatives, liabilities). Section 1.5 auto-rendered from `data/transactions.json`; never hand-edit unit counts. Populated by `/portfolio-grill`. Updated whenever you transact (either via `/fund-allocate`'s report-back block or manually via `scripts/log_transaction.py`).

**`laws/`** folder — 12 files capturing current Indian rules: capital gains, equity MF tax, debt MF tax, PPF, EPF/VPF, NPS, SCSS, gold tax, regime comparison, SEBI categories, insurance, plus an index. Each has `last_updated` and `last_verified_against_budget` front matter. The `/laws-refresh` skill updates these after Budget changes.

**`decisions-log.md`** — audit trail. Every recommendation a skill makes, with stable ID (ACTION/WATCH/INFO/ALLOC + date + sequence), severity tier, principle citation, and your response (acted/will-do/defer/reject/ack with date). Skills append; nothing else writes here.

---

## Layer 2: What each skill does

Each skill is a markdown file at `.claude/skills/<name>/SKILL.md`. The frontmatter has a `description` field Claude Code uses to decide which skill applies to a given user message. The body is the prompt that loads when the skill activates.

**`/setup`** — one-shot first-run installer. Verifies Python prereqs, bootstraps the NAV layer, optionally installs the daily cron, confirms scaffolds. Run once at project start. Re-run if you want to revisit the cron install.

**`/finance-grill`** — interrogator. Asks ~50 questions about your situation, writes `goals.md`. Re-run after major life changes.

**`/principles-grill`** — captures your investment structure (sub-portfolios, sleeve targets, glide paths, routing, regime, vehicles). Writes `user-principles.md`. Re-run when household composition changes or after a lived bear market reshapes risk tolerance.

**`/portfolio-grill`** — captures every holding into `portfolio.md` + seeds `data/transactions.json`. Re-run after big changes.

**`/laws-refresh`** — manual trigger. After every Union Budget (Feb), run this. It web-searches authoritative Indian sources, proposes diffs to `laws/` files, you review and approve.

**`/tax-check`** — internal plumbing. Not invoked directly. Other skills (`portfolio-review`, `fund-allocate`) call it when a transaction has tax implications.

**`/portfolio-review`** — your routine check-in. Reads foundation files + refreshes NAVs if stale + computes drift vs targets + walks a structured findings checklist + outputs tiered findings. Internally invokes `/tax-check` on any sell/switch finding. Logs everything to `decisions-log.md`.

**`/fund-allocate`** — fresh-money router. Reads foundation files + walks deployment priority + computes per-sleeve target ₹ + generates category-shaped specs + calls `filter_candidates()` for ranked candidates + presents the plan. Logs to `decisions-log.md` and `data/recurring.json`.

**`/fund-research`** — populates `data/fund_quality.json` for sparse categories. WebFetches Value Research / Freefincal / AMC factsheets, presents a structured diff, writes on approval.

The **dependency graph** between skills:

```
setup            ──► (data layer ready)
finance-grill    ──► goals.md
principles-grill ──► user-principles.md
portfolio-grill  ──► portfolio.md, data/transactions.json
laws-refresh     ──► laws/
fund-research    ──► data/fund_quality.json

(produces inputs for the routine skills)
                                    ↓
                portfolio-review ─┬─► tax-check (called internally)
                fund-allocate ────┘
                                    ↓
                              decisions-log.md
```

---

## End-to-end: walking through a `/portfolio-review` run

This is the most useful flow to understand because it touches every layer.

You type `/portfolio-review` in Claude Code. Claude Code loads `.claude/skills/portfolio-review/SKILL.md`. The skill's prompt instructs Claude to do roughly the following sequence:

**Phase 0 — discovery.** Claude runs:
```bash
python3 scripts/recurring_runner.py
python3 scripts/fetch_nav.py --quiet
python3 scripts/discover.py
```
`discover.py` emits a 10-section structured report covering NAV freshness, ledger health, fund-quality coverage, laws/ staleness, open ACTIONs from prior runs, and the §6.4 drawdown gate state per sub-portfolio. Claude quotes the relevant sections in the review header.

**Step 0 — read foundation files.** Claude reads `goals.md`, `principles.md`, `user-principles.md`, `laws/index.md`, `portfolio.md`, `decisions-log.md`. All in markdown.

**Step 2 — compute current values.** For each holding in the ledger, Claude uses `transactions.current_value_per_scheme()` (or the `render_portfolio.py --json` wrapper) — this returns per-scheme units, cost basis, latest NAV, current value, and unrealised gain. **Not** by hand-querying SQL.

**Step 3 — compute review variables.** Each variable maps to a helper:
- Sleeve drift → `discover.py` §10 (already computed)
- Drawdown gate → `discover.py` §9 (already computed)
- Goal progress → `projection.goal_progress(...)`
- Active fund underperformance → `returns.alpha_vs_benchmark(...)`
- Holding-period transitions → `transactions.classify_gain(...)`

No prose-arithmetic; the helpers are authoritative.

**Step 4 — translate variables into findings.** Group by group. For each rule that fires, Claude assembles the context (which rule, which holding, which principle citation, what action).

**Step 5 — invoke `/tax-check` on transactional findings.** For any sell/switch/redemption recommendation, Claude internally calls `/tax-check`, which reads `laws/equity-mf.md` (or relevant file) and applies the rules to the specific holding. Result gets folded into the finding.

**Step 6 — render report.** All findings rendered in tiered order (ACTION first, then WATCH, then INFO), each with stable ID, principle citation, tax math (where relevant), recommended action.

**Step 7 — capture your response.** You respond per item: "acted" / "will-do by Friday" / "defer to next week" / "reject with reason" / "ack only". Claude writes each finding + your response to `decisions-log.md` with the stable ID.

That's one full run. Typically 30-90 seconds end-to-end. Five files read (markdown), one DB queried, one external HTTP call (to AMFI, only if NAV is stale), markdown append at the end.

---

## End-to-end: walking through a `/fund-allocate` run

Same pattern, different specifics:

**Phase 0** — `scripts/discover.py` for the freshness/health/gate snapshot.

**Step 1** — read foundation files (`goals.md`, `principles.md`, `user-principles.md`, `laws/`, `decisions-log.md`). User-principles.md is the authority for sub-portfolio names, sleeve targets, routing, regime, vehicles, STP threshold.

**Step 2** — capture inputs from you: source ("salary surplus" / "lump"), amount, cadence, routing override (or use `user-principles.md` default), sequential-lumps context, demat availability, AMC preferences.

**Step 2.5** — within-equity completeness audit. For each slot in `principles.md` §2.4 (Nifty 50, NN50, Flexicap, Mid, Small, Intl), check that `fund_quality.json` has ≥3 candidates. If not, invoke `/fund-research` for the sparse slots — bundled as a single up-front message.

**Step 3** — drawdown gate verdict per sub-portfolio.

**Step 4** — walk deployment priority (PPF → NPS → VPF → SCSS → SGB → SIPs, with `user-principles.md` overrides).

**Step 5** — `allocation.optimal_sleeve_split(...)` for the per-sleeve flow assignment.

**Step 6** — `stp_plan.plan_stp(...)` (above STP threshold) or `plan_lump_purchase(...)` (below) per sleeve flow.

**Step 7** — `fund_quality.filter_candidates(...)` for each SIP/STP destination, ranked by TER (passive) or 3Y return (active), with `returns.alpha_vs_benchmark()` and `tracking_error()` overlaid.

**Step 8** — `projection.project_drift(...)` and `projection.goal_progress(...)` for forward validation.

**Step 9** — render the plan with tax-implications section, drift projection, scenario-based goal contribution.

**Step 10** — capture user picks per item. Selection deferrals tracked.

**Step 11** — append plan + picks to `decisions-log.md` with `ALLOC-YYYY-MM-DD-NNN` IDs; append SIPs/STPs the user is registering at the AMC to `data/recurring.json`.

**Step 12** — emit a "Report back when executed" block the user pastes back after they've actually transacted at their AMC.

---

## The lifecycle: how this lives over time

**Daily (automatic):** the cron/launchd job runs `fetch_nav.py` at 22:30 local time. ~14,000 schemes refreshed. `nav_history` grows by one row per scheme per business day. Zero attention required.

**Monthly (automatic, if you've registered SIPs/STPs):** `recurring_runner.py` runs on the 6th, generating ledger rows for any scheduled tranches.

**Weekly (you):** `/portfolio-review` — ~5-10 minutes including reading findings + responding. Decisions appended to `decisions-log.md`.

**Quarterly (you):** spot-check cron is running. One-line shell command.

**Quarterly (you, optional):** refresh `fund_quality.json` for AMCs you hold or are considering. ~30 minutes via `/fund-research`.

**On fresh money (you):** `/fund-allocate` — ~15-30 minutes including selection and logging.

**Annually (Feb, you):** `/laws-refresh` after the Union Budget. Review and approve diffs. ~30-60 minutes.

**On life events (you):** re-run `/finance-grill` (income/dependent change) or `/portfolio-grill` (large redemption/scheme switch).

**On code changes (rare):** re-run the test suite. `for t in scripts/tests/test_*.py; do python3 "$t"; done`. ~3 seconds total.

---

## What you've actually got, in one sentence each

A daily-refreshed local mirror of every Indian mutual fund's NAV history, joined against your own portfolio cost-basis and a manually-curated quality overlay, queried by skills that apply your stated principles (universal + personal) to surface findings and produce allocation plans, with every recommendation auditable in `decisions-log.md`.

The Python is mechanical (~1,500 lines of code, ~600 lines of tests). The intelligence lives in the markdown — your `goals.md`, `principles.md`, `user-principles.md`, and the skill prompts. Everything else is plumbing to feed those prompts the right data at the right time.

If a piece breaks or feels unclear, the question to ask is: which layer is the problem in? Data layer (run `sqlite3 data/market.db "SELECT COUNT(*) FROM nav_history"` to sanity check)? Script layer (run the relevant test file)? Markdown layer (re-read `goals.md` and `user-principles.md` to check they still reflect your situation)? Skill layer (re-read the SKILL.md to see what the prompt actually says)? The 4-layer model gives you a triage path.
