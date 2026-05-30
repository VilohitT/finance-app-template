---
name: portfolio-review
description: Conducts a structured review of the user's investment portfolio. Reads goals.md, principles.md, user-principles.md, laws/, portfolio.md, and the live-data layer (data/market.db) to assess goal progress, allocation drift using current NAVs, scheme-level signals, fresh-money capacity, and tax-relevant transitions. Produces a structured findings report with severity-tiered recommendations and tax-aware action items. Use whenever the user asks for a portfolio review, weekly check-in, "how is my portfolio doing", or wants to see what changes (if any) to make. Invoke proactively at the user's stated review cadence (per goals.md) or after major events (lump deployment, redemption, life change). Internally invokes tax-check whenever a recommendation involves a sell/switch/redemption. Refreshes NAVs via scripts/fetch_nav.py if last fetch is older than 24 hours. Logs every recommendation and the user's response to decisions-log.md. Indian-context aware — handles single-portfolio and multi-entity sub-portfolio structures (per user-principles.md), scheme-level Direct/Regular, exit-load timing, holding-period transitions, and tax regime decisions.
---

# portfolio-review

A structured review skill that assesses the user's portfolio against goals, principles, current rules, and the user's stated structure. Produces severity-tiered findings, tax-aware recommendations, and an audit log of every decision.

Designed to handle two modes:
- **Backlog mode** (first run, or after long inactivity): many findings; the review is also a strategic catch-up
- **Steady-state mode** (subsequent routine runs): mostly silent, with occasional findings

Both modes use the same workflow.

## When to use

Trigger this skill when:

- The user says "run a portfolio review" or "review my portfolio" or "weekly check-in"
- The user's stated review cadence (per `goals.md`) elapses
- Major event: lump-sum deployed, scheme redeemed/switched, new policy taken, scheme manager changed, tax law update applied via `/laws-refresh`
- The user asks "how is my portfolio doing", "anything to change?", "where do I stand?"
- Open items from previous reviews are coming due

## What this skill does NOT do

- **Does not deploy fresh money.** That's `/fund-allocate`. Portfolio-review surfaces "fresh-money capacity exists" as a finding; deploying it is a separate skill.
- **Does not advise on whether to do a transaction beyond following principles.** It applies the principles in `principles.md` and the user's choices in `user-principles.md` to the current state and surfaces what they imply. Final decision is the user's.
- **Does not refresh rules.** If `laws/` files are stale, the skill flags it and proceeds with caveat — `/laws-refresh` is the skill that updates rules.
- **Does not transact.** Findings recommend; the user (or their broker/AMC platform) executes.
- **Does not relitigate past decisions** in routine review per `principles.md` §7.5. Past actions are past.

## Live data integration

Holdings live in `data/transactions.json` (append-only ledger). Units, current value, cost basis, and FIFO-derived gain are all computable from the ledger × current NAVs in `data/market.db`. `portfolio.md` Section 1.5 is auto-rendered from the ledger; do not hand-edit it.

On every run:

1. **Pull latest auto-tranches first:** run `python scripts/recurring_runner.py` (idempotent) so any SIP/STP tranches scheduled before today are reflected in the ledger before review.
2. **Check NAV freshness:** read `last_fetch_time('amfi_nav')` from the data layer.
3. **Refresh if stale (>24h):** run `python scripts/fetch_nav.py --quiet` to pull the latest AMFI NAVAll.
4. **Read structured snapshot:** run `python scripts/render_portfolio.py --json` — returns per-scheme units, cost basis, latest NAV, current value, and unrealised gain, plus sub-portfolio totals. Use this directly for allocation drift, goal-progress, and signal computations. **Do not** parse portfolio.md unit fields visually.
5. **For holdings beyond MFs** (FDs, PPF, EPF, real estate, gold physical, direct equity) — read from `portfolio.md`. The ledger only covers MF holdings.
6. **Resolve scheme codes:** for any MF holding in `portfolio.md` without a `scheme_code`, run `python scripts/resolve_schemes.py` and surface the report; HIGH-confidence matches are auto-applied for this review session.

If the data layer is unavailable, fall back to cost-basis-as-proxy on `portfolio.md` and flag this in the report header. The fallback is graceful, not blocking.

For holdings where `scheme_code` is unresolved (LOW or NONE confidence), the skill flags them in the report and uses cost basis for those specific holdings only.

## What this skill produces

A **structured review report** with severity-tiered findings, plus an updated `decisions-log.md` capturing every recommendation and the user's response. The exact report format is in `references/output-format.md`.

Conceptually:

```
## Portfolio Review — YYYY-MM-DD
[summary line: green check, or N findings]

### Goal progress
[per-goal progress vs glide-path]

### Sub-portfolio status (or Portfolio status if single-portfolio)
[per-sub-portfolio actual vs target allocation]

### Findings (sorted by severity)
- ACTION-YYYY-MM-DD-001: [headline]
  - Detail
  - Tax-check result (if redemption/switch involved)
  - Trade-offs / what would change the recommendation
- WATCH-...
- INFO-...

### Open items from prior reviews
[checklist of pending items]

### What you can do now
[1-2 line summary of next steps]
```

## Operating principles

### Most routine reviews show no action

Per `principles.md` §9, "activity is the exception, not the norm." A typical review reads the foundation files, checks against goals.md and principles.md, and reports "everything tracking, no action recommended." The user shouldn't expect findings every run. When they appear, they're real.

### Severity tiers

Each finding is tagged with one of three:

- **ACTION**: a concrete thing to do (open an account, redirect a SIP, switch a fund, harvest LTCG). Comes with tax-check output if the action triggers a tax event.
- **WATCH**: a drift or risk to monitor. No action yet, but worth being aware of.
- **INFO**: educational / contextual. Doesn't affect the portfolio but worth knowing.

### Findings carry stable IDs

Each finding gets an ID: `<TIER>-<YYYY-MM-DD>-<seq>`. The user can refer back to specific findings across sessions. Open findings carry forward in subsequent reviews until closed.

### Tax-check is called eagerly

Any ACTION finding that involves a redemption, switch, or sale calls `/tax-check` internally **before** the finding is finalised. The output is folded into the finding so the user sees both the recommendation and the tax cost in one place. No "switch X to Y" recommendations without the rupee cost shown.

### Apply principles.md and user-principles.md at every step

Every finding maps to a principle. The recommendation says which principle it's applying ("per principles.md §6.3 — use flows over sales"). If the finding doesn't trace to a principle, it doesn't belong in the review.

Sub-portfolio names, sleeve targets, glide paths, regime decisions, and routing rules come from `user-principles.md` — never hardcoded.

### Read sub-portfolio architecture from user-principles.md

The user has either a single portfolio or a multi-entity sub-portfolio structure (per `user-principles.md` §1). The skill adapts:
- **Single portfolio:** report one allocation block (actual vs target) and one set of findings.
- **Multi-entity:** report each sub-portfolio separately with its own sleeve targets (from `user-principles.md` §3), drift figures, and findings. Aggregate household figure shown as a footer for context, not as a managed metric.

The skill never assumes specific names like "user" or "spouse" or "father" — it uses whatever the user captured in `user-principles.md`.

### Honest about data limitations

If `portfolio.md` flags any holding as `UNKNOWN` for a field the review needs (cost-basis granularity, tax classification, etc.), the skill is candid about what it can and can't compute. For partial redemption math: tax-check returns DATA NEEDED, and portfolio-review surfaces that as a flag, not a finding.

### Cadence is a default, not a mandate

If the user runs portfolio-review on day 3 after the previous one, the skill runs as normal but notes "this is your last review + 3 days; most findings won't have changed." This protects against reactive checking.

**However: same-day or short-interval re-runs are NOT no-ops.** Even when portfolio.md hasn't changed, the data layer (`data/market.db`) can change between runs. The skill must re-execute Step 2 (refresh live data and resolve scheme codes) and Step 3 (compute review variables) on every invocation. What the skill CAN shortcut on short-interval re-runs:
- Findings list — carry forward from prior decisions-log entries; only generate new findings if the live-data computation surfaces something genuinely new
- Goal progress narrative — note "unchanged from prior run at HH:MM" if true
- The opening one-liner can acknowledge the re-run

What the skill MUST NOT shortcut:
- The data-layer freshness checks
- The current-value computation (re-derive units and current values from latest NAV state)
- Drift figures (these change as NAVs change, even within a single day if fetch_nav.py has run)
- The header-line declaration of which mode the run is using (live-NAV-derived vs cost-basis-as-proxy)

### Don't moralise or relitigate

Per `principles.md` §7.5, past decisions don't get re-aired. Existing suboptimal holdings are recorded as state, not flagged as repeated grievances. The skill operates forward.

### Don't push protection products

If `goals.md` records that the user has opted out of additional protection insurance, the skill records insurance state but doesn't surface "buy more health cover" as a finding unless a triggering event occurs (job change, new dependent, family medical event). Per `principles.md` §10.

### Don't rebalance during 20%+ drawdowns

Per `principles.md` §6.4 / §7.1, during a 20%+ aggregate equity drawdown, the skill specifically does NOT recommend allocation shifts. The gate state is read from `drawdown.aggregate_equity_drawdown(sub_portfolio)["block_at_minus_20pct"]` (and surfaced in `discover.py` §9). When `True`, drift findings for that sub-portfolio downgrade to INFO with the explicit note: "holding targets through this drawdown per principle §7.1; resume normal rebalancing after recovery or after user has lived through it without panic-selling."

## Workflow

> **Critical:** every step below must be executed in order. Phase 0 establishes
> NAV freshness, ledger health, fund-quality coverage, drawdown gate state, and
> open ACTIONs from prior runs. Skipping it produces a review without grounding.

### Phase 0 — Mandatory tool & data discovery (cannot skip)

**Run discover.py first. Quote its output before doing anything else.**

```bash
python3 scripts/recurring_runner.py    # Bring auto-tranches up to date (idempotent)
python3 scripts/fetch_nav.py --quiet   # Refresh NAVs (no-op if <24h old per the daily cron)
python3 scripts/discover.py            # The mandatory Phase 0 entry point
```

`discover.py` emits a 10-section structured report. Portfolio-review reads sections 3, 4, 7, 8, 9, 10 directly and treats them as authoritative inputs:

- **Section 3 (NAV freshness)** — if STALE, the refresh above didn't take. Surface in the report header and proceed with the "live-data unavailable" caveat.
- **Section 4 (Ledger health)** — if BLOCKER (empty ledger), do not produce drift or goal-progress findings; the holdings layer is broken. Surface as a P0 finding asking the user to run `scripts/backfill_units.py` (or to start fresh by capturing holdings via `/portfolio-grill`).
- **Section 7 (laws/ staleness)** — if any file STALE, prepend the report with "⚠️ Some laws files are stale" caveat per the findings checklist.
- **Section 8 (decisions-log open ACTIONs)** — read the count, then read the log in full (the count is just a flag); use it to populate the "Open items from prior reviews" section.
- **Section 9 (Drawdown gate, §6.4)** — if `principle_64_blocked: true` for any sub-portfolio, this review's rebalance recommendations are suppressed (§6.4 / §7.1). All allocation drift findings downgrade to INFO with the explicit note "holding targets through this drawdown per principle §7.1." This is non-negotiable.
- **Section 10 (Sub-portfolio totals)** — authoritative current-value input. Drift figures come from this, not from manually parsing `portfolio.md`.

**Quoting requirement.** The review's report header must include a "Discovery snapshot" block that names:
- NAV freshness status + latest_nav_date
- Ledger txn_count and latest_txn_date (or BLOCKER notice)
- Drawdown gate verdict per sub-portfolio (with weighted_dd numbers)
- Stale laws/ files (if any)
- Open ACTION count from decisions-log

If any of these is missing from the response, the review is incomplete by definition.

### Step 0: Read the foundation files

After discovery, read in order:
1. `goals.md` — user state: regime, bracket, risk tolerance, goals, surplus, dependents
2. `principles.md` — universal framework: especially sub-portfolio architecture options (§2.1), within-equity composition (§2.4), debt sleeve framework (§2.5), gold (§2.6), deployment priority (§4.1), review framework (§9)
3. `user-principles.md` — the user's structural choices: sub-portfolio names, sleeve targets, glide paths, regime committed, routing rules, drift bands, STP threshold. **This is the authority for any numeric target.**
4. `laws/index.md` — check staleness flags (already surfaced via discover.py §7; this read is for which specific files apply)
5. `portfolio.md` — for narrative context (sub-portfolio assignment notes, reconciliation history). **Do NOT** read Section 1.5 unit/value fields for computations — those come from discover.py §10 and from `scripts/render_portfolio.py --json`.
6. `decisions-log.md` (if exists) — full read, to carry forward open findings and check on prior recommendations

If `decisions-log.md` doesn't exist (first run), the skill creates it.

### Step 1: Acknowledge mode and date

Open with a one-liner:

> "Running portfolio review for YYYY-MM-DD. Last review was [date / first run]."

If first run: note that the review will likely surface a backlog (set expectations). If steady-state: proceed.

### Step 2: Pull holdings snapshot and resolve scheme codes

**Freshness and ledger health are already in hand from Phase 0** (discover.py §3 and §4). Do NOT re-derive them with ad-hoc SQL — quote the discover.py output. If §3 said STALE, the Phase 0 `fetch_nav.py` retry should have cleared it; if not, set the "live-data unavailable" flag in the report header and continue.

**Scheme code resolution.** Read `portfolio.md` and check whether each MF holding has a `scheme_code` field. If any are missing:

```bash
python scripts/resolve_schemes.py --file portfolio.md --quiet
```

Apply HIGH-confidence matches to the in-memory portfolio for this review. Surface MEDIUM matches in the report so the user can confirm, then write back to portfolio.md only with explicit user approval. LOW or NONE matches stay unresolved; affected MF holdings are reported as "scheme_code unresolved" rather than included in drift math.

**Pull the structured holdings snapshot.** Use `transactions.current_value_per_scheme()` directly (or the `render_portfolio.py --json` wrapper, which calls the same helper). This is the single source of truth for units, cost basis, latest NAV, current value, and unrealised gain per scheme.

```python
import sys; sys.path.insert(0, 'scripts')
from lib.transactions import load_transactions, current_value_per_scheme
from lib.db import get_conn

txns = load_transactions()
with get_conn() as conn:
    snapshot = current_value_per_scheme(txns, conn)
# snapshot[scheme_code] = {units, cost_basis_inr, latest_nav, latest_nav_date,
#                          current_value_inr, unrealised_gain_inr}
```

Or via the CLI wrapper:

```bash
python scripts/render_portfolio.py --json
```

Both paths produce the same numbers. Use them — do not parse portfolio.md Section 1.5 visually, do not write SQL by hand to look up purchase-date NAVs, do not invent a "units = cost_basis / purchase_nav" anchor (the ledger has actual unit counts per lot).

**For non-MF holdings** (FDs, PPF, EPF, real estate, gold physical, direct equity) — read from `portfolio.md`.

**Per-scheme fallback** (rare): if `latest_nav` is `None` for a scheme in the snapshot, the scheme is not in `nav_history`. Report current_value as "cost basis (no NAV)" for that holding only and flag it inline.

**Global fallback** (very rare, only if the ledger is empty or NAV layer is offline — discover.py §3 and §4 will already have flagged this): set the header to:
> "Live data layer unavailable — drift figures are computed against cost basis only and are directionally correct but magnitude-underestimated for older holdings."

### Step 3: Compute review variables

Do NOT compute these by hand. Each variable below maps to a specific helper in `scripts/lib/`. If you find yourself writing prose-arithmetic, you are reinventing a helper that already exists — stop and call it.

**Sub-portfolio sleeve totals (drift inputs).** Already in discover.py §10. Quote it. The numbers come from `transactions.current_value_per_scheme()` × `drawdown.classify_sleeve()` — the same classifier the §6.4 gate uses, so drift and drawdown views cannot disagree.

For each sub-portfolio defined in `user-principles.md`:
- Target sleeve allocation (from `user-principles.md` §3)
- Actual sleeve allocation (from discover.py §10)
- Drift per sleeve = actual - target
- Drift band (from `user-principles.md` §10; default 5pp)
- Flag any sleeve where |drift| > band

Aggregate household: report only (not optimised against).

**Drawdown gate (§6.4).** Already in discover.py §9. Re-state the verdict per sub-portfolio. The helper is `drawdown.aggregate_equity_drawdown(sub_portfolio)`; do not write peak-NAV arithmetic in prose.

```python
from lib.drawdown import aggregate_equity_drawdown
for sub_port in user_principles_sub_portfolios:
    dd = aggregate_equity_drawdown(sub_portfolio=sub_port)
    # dd["block_at_minus_20pct"] is the rebalance-block flag — use it as-is.
    # dd["weighted_drawdown"] is the value-weighted percentage — quote it in findings.
```

If `block_at_minus_20pct: true` for a sub-portfolio, every drift finding for that sub-portfolio downgrades to INFO with the principle §7.1 hold-through note.

**Goal progress.** Use `projection.goal_progress()`; do not describe the math in prose.

```python
from lib.projection import goal_progress, DEFAULT_REAL_RETURN_SCENARIOS

# Per goal in goals.md §5
for goal in goals_md_goals:
    prog = goal_progress(
        current_corpus_inr=<earmarked corpus from snapshot + user-principles.md §5>,
        target_corpus_inr=goal["target_inr"],
        target_date=goal["target_date"],
        monthly_flow_inr=<post-current-plan monthly inflow>,
        real_return_pct=DEFAULT_REAL_RETURN_SCENARIOS,
    )
    # prog["scenarios"] has base / optimistic / pessimistic, each with
    # pct_of_target and shortfall_inr. Quote all three; do not collapse to a point estimate.
```

Material deviation flag: pessimistic scenario `pct_of_target < 0.85`.

**Active fund underperformance.** Use `returns.alpha_vs_benchmark()` and `returns.discover_benchmark_for_category()`; do not describe rolling-return math in prose.

```python
from lib.returns import alpha_vs_benchmark, discover_benchmark_for_category

for scheme_code, info in held_funds.items():
    # Only fires for active funds held >= 3 years
    if holding_age_years(scheme_code, txns) < 3:
        continue
    bench = discover_benchmark_for_category(info["category"])
    if not bench:
        # Flexi/Multi/Value/ELSS/Focused/Sectoral — no clean default benchmark.
        # Skip or ask user to specify. Don't fabricate one.
        continue
    a = alpha_vs_benchmark(scheme_code, bench, period_days=1095)  # 3Y
    if a and a["alpha"] < -0.02:
        # 2pp annual underperformance over 3Y → ACTION (consider switch)
        ...
```

For index funds use `returns.tracking_error()` instead — alpha collapses to noise within the category.

**Manager-change watch.** `fund_quality.json` (populated by `/fund-research`) carries `manager_name` and `manager_since`. The mechanism is snapshot-on-write: when this review reads `fund_quality.json`, capture the (scheme_code, manager_name) pairs and persist them to `decisions-log.md` under a "Manager snapshot YYYY-MM-DD" block. On the next review, diff against the prior snapshot:

```python
from lib.fund_quality import load_quality
quality = load_quality()
current_managers = {sc: q.get("manager_name") for sc, q in quality.items() if q.get("manager_name")}
# Compare against prior snapshot stored in decisions-log.md.
# A change → WATCH finding with research recommendation per principle §7.2.
```

If no prior snapshot exists (first run with this rule live), this review writes the baseline and produces no finding.

**Fresh-money capacity.** No prose-arithmetic; read state from `portfolio.md` (account balances) and `laws/<scheme>.md` for current caps. Per `principles.md` §4.1 and any overrides in `user-principles.md` §9, list unused capacity in priority order: PPF, VPF (if salaried), NPS additional ₹50K (Old Regime only), SGB (if RBI issuance open), SCSS (when eligible).

**Holding-period status, exit-load window, Direct vs Regular flag.** Read from the ledger's per-lot purchase dates — `transactions.consume_fifo()` returns lot dates if you need precision; otherwise `transactions.cost_basis_per_scheme()` and the earliest purchase date per scheme are sufficient. The `transactions.classify_gain()` helper resolves STCG vs LTCG vs Specified-MF given (purchase_date, sale_date, tax_category).

**Tax position.**
- Regime decision: read `user-principles.md` §7 for the committed regime; if open item flag in `goals.md`, surface as a finding.
- LTCG harvesting headroom: `/tax-check` skill computes it; portfolio-review just calls it for any equity LTCG-eligible holdings near FY-end.
- Holding-period transitions in next 30 days: scan ledger lots per `transactions.consume_fifo()` lot dates and flag any within 11-12 months for equity / 23-24 months for non-equity.

### Step 4: Translate variables into findings

Each variable that breaches a threshold becomes a finding. Map:

- Allocation drift > band → potentially ACTION (redirect SIP) or INFO (drift accepted; await flow correction)
- New scheme capacity unused → ACTION
- Goal earmark glide-path deviation > 10% → WATCH or ACTION
- Regular plan holding past exit load + crossed LTCG threshold → ACTION (switch is now favourable)
- Regular plan holding still in exit load + STCG → INFO (keep waiting)
- Holding within 30 days of LTCG transition → WATCH (timing-relevant if user is contemplating action)
- Regime decision not done in current FY → ACTION
- LTCG harvesting headroom available + FY-end approaching → ACTION (or INFO if user's tax priority is low and harvesting cost > benefit)
- Tax classification UNKNOWN on any holding → INFO (low-cost research item)
- Stale `laws/` file → INFO
- Multiple findings with the same root cause → consolidate into one finding

For each ACTION finding involving a redemption / switch / sale:
- Call `/tax-check` skill internally with the proposed transaction
- Fold the tax-check output into the finding's "trade-offs / cost" subsection
- If tax-check returns DATA NEEDED, surface that as part of the finding (often shifts a finding from ACTION to WATCH pending data)

### Step 5: Sort and assign IDs

Sort findings: ACTION first (in order of impact), then WATCH, then INFO.

Assign IDs: `<TIER>-<YYYY-MM-DD>-<seq>` per the convention. seq is per-tier, per-day.

### Step 6: Carry forward open items

Read `decisions-log.md` for the list of open findings from prior reviews. For each:
- Check if the underlying condition still holds
- If yes: include in this review's "Open items from prior reviews" section, with status (e.g., "still pending; condition unchanged")
- If no: mark as resolved in `decisions-log.md` and don't include in current review

### Step 7: Generate the report

Use `references/output-format.md` for exact structure. Include:
- One-line summary at top
- Goal progress section
- Sub-portfolio status section (or single portfolio status if Option A)
- Findings (sorted)
- Open items from prior reviews
- 1-2 line "what you can do now" closer

### Step 8: Capture user response per finding

After presenting findings, ask the user (one batch):

> "For each ACTION finding, tell me:
> - **Acted**: did the action; tell me when
> - **Deferred**: not now, follow up later (give a reason)
> - **Rejected**: not doing this; explain why
> Or: 'all deferred to next review' / 'all acted' for batch processing."

The user can also acknowledge WATCH and INFO findings ("noted") without action.

### Step 9: Update decisions-log.md

For each finding presented:
- Append an entry to `decisions-log.md` with: ID, date, severity, headline, full detail, tax-check excerpt if applicable, user response, follow-up date if deferred
- Mark resolved findings as closed
- Findings still open (deferred) carry forward to next review

### Step 10: Closing

Tell the user:
- Summary of what they acted on, deferred, rejected
- Follow-up dates for deferred items
- Next review due date (typically +1 cadence-period, or sooner if the user requests)

End cleanly. Don't add a recap of every principle the agent applied — that's in the report itself.

## Key reminders

- **Most reviews show no action.** This is a feature, not a bug.
- **Severity tiers, stable IDs.** Findings carry forward across sessions.
- **Tax-check is called eagerly** for any sell/switch/redemption.
- **Every finding cites a principle.** If it doesn't, it doesn't belong.
- **decisions-log.md is mandatory** — every recommendation logged with user response.
- **Sub-portfolio targets, names, glide paths, regime, routing come from `user-principles.md` — never hardcoded.**
- **Don't push protection products** if the user has opted out per `goals.md`.
- **Don't rebalance during 20%+ drawdowns.** Per `principles.md` §6.4 / §7.1.
- **Don't relitigate past decisions** in routine review.
- **Honest about data limitations.** Live NAVs are read from `data/market.db` when available; falls back to cost-basis-as-proxy when the data layer is offline, and flags clearly in the report header which mode the run is using.
