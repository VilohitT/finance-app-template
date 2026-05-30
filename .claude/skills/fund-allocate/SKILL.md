---
name: fund-allocate
description: Designs the routing of fresh money — monthly salary surplus, business lump receipts, windfalls — across the user's portfolio structure, scheme capacities, and goal-bucket allocations. MANDATORY Phase 0 runs scripts/discover.py to enumerate every available helper and surface NAV freshness, ledger health, fund_quality coverage, drawdown gate state, and decisions-log open ACTIONs — the agent quotes this snapshot before any allocation. Then reads goals.md, principles.md, user-principles.md, laws/, and decisions-log.md. Uses scripts/lib/allocation.optimal_sleeve_split() for principle-6.3-compliant per-sleeve flow assignment, scripts/lib/stp_plan.plan_stp() for parking-and-STP planning, scripts/lib/fund_quality.filter_candidates() + scripts/lib/returns.alpha_vs_benchmark() + scripts/lib/returns.tracking_error() for ranked candidate selection, scripts/lib/projection.project_drift() and goal_progress() for forward validation, and scripts/lib/drawdown.aggregate_equity_drawdown() to enforce the §6.4 rebalance-block gate. Invokes /fund-research when fund_quality.json is sparse for a needed category (never invents picks from training-data priors). Use whenever the user has fresh money to deploy, wants to design SIP structure, or asks "where should this money go". Internally invokes /tax-check only if a routing decision involves redirecting from existing holdings (rare; flow-redirect is preferred per principle 6.3). Logs every allocation plan to decisions-log.md alongside portfolio-review entries. Indian-context aware — handles Old vs New regime, scheme-specific limits (PPF ₹1.5L/yr, VPF ₹2.5L threshold, NPS ₹50K 80CCD(1B), SCSS ₹30L), STP-vs-lumpsum thresholds, single-portfolio and multi-entity routing.
---

# fund-allocate

A focused routing skill that turns "I have ₹X to deploy" into a structured allocation plan: which sub-portfolio (per `user-principles.md`), which sleeve, which scheme capacity to fill first, which existing or new SIPs to fund, **and which specific scheme(s) to consider for each SIP** — drawn from the user's researched universe in `fund_quality.json`, ranked by trailing returns, filtered by category/plan/AUM/TER/vintage/manager tenure.

## When to use

Trigger this skill when:

- User has fresh money to deploy (monthly surplus, business lump, salary jump, bonus, windfall, inheritance)
- User says "design my SIPs" / "where should this money go" / "I have ₹X — how should I split it"
- A `/portfolio-review` run produces an ACTION finding to set up SIPs
- User is starting a new financial year and wants to redesign SIP structure
- A material change in income or goals warrants restructuring (per the re-grill triggers in `goals.md`)

## What this skill does NOT do

- **Does not invent fund recommendations from training-data priors.** The skill can only recommend schemes that the user has researched and added to `fund_quality.json`, plus structurally similar candidates from the `schemes` table that have NAV history. If `fund_quality.json` is empty for a category, the skill produces a category-shaped specification (TER cap, AUM floor, AMC tier) and asks the user to research before committing.
- **Does not advise on whether to deploy.** Per principle §1.1, all available capital deploys to its target home; the skill never recommends holding cash for "better entry."
- **Does not redirect existing holdings** without explicit user request. Per principle §6.3, fresh flows go to under-allocated sleeves; existing holdings stay put unless the user is contemplating a switch.
- **Does not invoke `/tax-check`** unless redirecting from existing holdings is involved. Fresh money deployment has no tax events.
- **Does not re-litigate the regime decision.** That's `/portfolio-review`'s job (annual). Fund-allocate uses whatever regime is current per `user-principles.md`.
- **Does not transact.** It produces a plan; the user executes via their broker / AMC platform.
- **Does not modify `fund_quality.json` itself.** When new candidates need to be researched, the skill calls `/fund-research`. Never silent.

## What this skill produces

A **structured allocation plan** with deployment sequence, ranked candidate scheme list per item (where data exists), and selection guidance (where it doesn't). The exact format is in `references/output-format.md`. Conceptually:

```
ALLOCATION PLAN — YYYY-MM-DD
Source: <salary surplus / business lump / windfall>
Amount: ₹X
Default sub-portfolio routing: <per user-principles.md §6 routing rules>

DEPLOYMENT SEQUENCE (priority-ordered per principles.md §4.1
                     with overrides from user-principles.md §9):
1. Wrapper-fill items (PPF, VPF, NPS where untapped)
2. SIP / STP into category-shaped needs across sub-portfolios

For each item:
- Amount
- Sub-portfolio tag (per user-principles.md)
- Goal earmark
- Rationale (citing principles.md and user-principles.md)
- Category-shaped specification (TER cap, AUM floor, plan)
- Ranked candidate list (from filter_candidates(), if data available)
  OR Selection-pending flag with research guidance

LOG: every plan logged to decisions-log.md with user response and selection.
```

## Tool inventory (consult discover.py for the live list)

The agent MUST run `python3 scripts/discover.py` at the start of every invocation (see Workflow → Phase 0). The report is the authoritative inventory of helpers, scripts, data freshness, and gates.

The recurring helpers used by every fund-allocate run live in `scripts/lib/`:

- **`fund_quality.filter_candidates(...)`** — rank candidate schemes by trailing returns from the researched universe.
- **`fund_quality.get_quality(scheme_code)`** — single-scheme merged metadata (TER, AUM, manager, vintage, returns, completeness).
- **`returns.alpha_vs_benchmark(fund, benchmark, period_days)`** — fund return minus benchmark return; differentiates active funds.
- **`returns.tracking_error(fund, benchmark, period_days)`** — annualised stdev of daily return diffs; differentiates index trackers.
- **`returns.discover_benchmark_for_category(category)`** — pick a sensible default index fund per SEBI category.
- **`drawdown.aggregate_equity_drawdown(sub_portfolio)`** — value-weighted equity drawdown; feeds the §6.4 gate.
- **`allocation.optimal_sleeve_split(current, targets, new_money, ...)`** — solver for per-sleeve flow assignment honouring principle §6.3.
- **`stp_plan.plan_stp(...)` / `plan_lump_purchase(...)`** — emit the parking purchase + recurring.json STP entry, or a one-shot purchase txn.
- **`projection.project_drift(...)` / `project_corpus(...)` / `goal_progress(...)`** — forward projections for plan validation.

Scripts (CLI entry points):

- **`scripts/discover.py`** — Phase 0 mandatory snapshot.
- **`scripts/fetch_nav.py`** — refresh AMFI NAVs.
- **`scripts/recurring_runner.py`** — process scheduled SIP/STP tranches.
- **`scripts/render_portfolio.py --json`** — structured holdings snapshot for current values.
- **`scripts/log_transaction.py`** — append a one-off purchase to the ledger.

Skills (slash commands):

- **`/fund-research`** — populate `fund_quality.json` for sparse categories via web research before committing scheme picks.
- **`/tax-check`** — invoke for any plan item that would redirect existing holdings.

## Operating principles

### Routing is principles + state; selection is data + filtering

The skill confidently does routing. Selection now also has structure: it draws from the user's researched universe in `fund_quality.json` via `filter_candidates()`, ranks by 3Y trailing return (computable from `nav_history`), and respects user-set thresholds for TER, AUM, vintage, and manager tenure. The skill does NOT invent recommendations from training-data priors.

### Walk the deployment priority strictly

Default ladder per `principles.md` §4.1; overrides per `user-principles.md` §9. Common ladder for an Indian-context investor:

1. PPF (per holder)
2. NPS Tier 1 via employer 80CCD(2) — only if employer supports the route
3. NPS Tier 1 personal 80CCD(1B) — only attractive under Old Regime
4. VPF (salaried, within ₹2.5L threshold)
5. SCSS (age 60+)
6. SGB tranches — only if RBI resumes primary issuance
7. SIP / STP into category-shaped needs

The skill processes a fresh-money input by walking the user's actual priority order. Capacity at each level reduces the residual; whatever's left flows to the next level.

### Sub-portfolio assignment is the first decision

Before any allocation, route money to a sub-portfolio per the rules in `user-principles.md` §6 (Money routing). Defaults are user-specific — the skill reads them, does not hardcode.

Routing flexibility lets the agent recommend over-rides (e.g. "this lump goes to entity A even though source is entity B, because A's PPF is unfilled and B's is maxed"). When over-riding, the rationale is explicit.

### Glide paths are honoured

Sleeve targets and glide-path waypoints come from `user-principles.md` §3 and §4. The skill reads the current waypoint applicable to today's date and treats that as the target. New money goes preferentially to the under-allocated sleeve in each sub-portfolio. Goal-bucket earmarks (per `user-principles.md` §5) follow their own glide schedules where defined.

### STP vs lump-sum threshold

Default: lumps above ₹3L into equity go via STP over 3-6 months; lumps below ₹3L deploy directly. The user can override the threshold in `user-principles.md` §11. Behavioural smoothing for untested-volatility risk, even though mathematically lump-sum is optimal in expectation. Per `principles.md` §8 step 5.

### Rationale chain is mandatory

Every allocation decision in the plan has a rationale citing `principles.md` and/or `user-principles.md`. Every scheme recommendation in the plan has a rationale citing the filter parameters that produced it (e.g. "ranked #1 of 4 candidates by 3Y return after filtering for TER ≤ 0.50%, AUM ≥ ₹500cr, vintage ≥ 3y"). If the rationale doesn't trace, the line doesn't belong in the plan.

### Selection draws from a researched universe; gracefully degrades when sparse

`filter_candidates()` operates over the intersection of (a) `schemes` table category/plan filter and (b) `fund_quality.json` quality filters. Two operating modes:

**Rich-data mode** — for categories where the user has researched 3+ candidates into `fund_quality.json` matching the requested category and plan: produce a ranked top-3 to top-5 list with TER, AUM, manager, manager tenure, vintage, 3Y return. User picks one (or splits across two for diversification — typically only when 5+ candidates exist).

**Sparse-data mode** — for categories where `fund_quality.json` has 0-2 entries matching: produce the top result (if any) with a "limited universe" caveat, plus a category-shaped specification (TER cap, AUM floor, AMC tier). Flag this category for the user to research. Invoke `/fund-research` to populate the universe before committing.

The skill does NOT silently fall back to invented recommendations. If `fund_quality.json` is empty for a category, the skill says so explicitly.

### Default filter parameters by category

The skill applies per-category filter defaults when calling `filter_candidates()`. These can be overridden if the user specifies tighter or looser thresholds, but the defaults reflect the framework's structural quality bar:

| Category | min_aum_crore | max_ter | min_vintage_years | min_manager_tenure_years | **rank_by** |
|---|---|---|---|---|---|
| Equity Scheme - Large Cap Fund (active) | 1,000 | 1.20 | 3 | 3 | return_3y |
| Equity Scheme - Large & Mid Cap Fund | 1,000 | 1.50 | 3 | 3 | return_3y |
| Equity Scheme - Mid Cap Fund | 500 | 1.50 | 5 | 3 | return_3y |
| Equity Scheme - Small Cap Fund | 500 | 1.80 | 5 | 3 | return_3y |
| Equity Scheme - Flexi Cap Fund | 1,000 | 1.20 | 5 | 3 | return_3y |
| Other Scheme - Index Funds (any) | 500 | 0.50 | 2 | (n/a — passive) | **ter (asc)** |
| Other Scheme - Gold ETF | 500 | 0.40 | 2 | (n/a — passive) | **ter (asc)** |
| Other Scheme - FoF Domestic (Gold MF) | 500 | 0.40 | 2 | (n/a — passive) | **ter (asc)** |
| Hybrid Scheme - Arbitrage Fund | 500 | 0.50 | 3 | 3 | **ter (asc)** + **exit-load profile** |
| Debt Scheme (any) | 500 | 0.80 | 3 | 3 | return_3y |
| Hybrid Scheme - Multi Asset Allocation | 500 | 1.50 | 3 | 3 | return_3y |

**Why rank_by differs:** passive categories have no manager-skill premium — the manager's job is to minimise tracking error, not pick stocks — so cost (TER) is the primary signal. Active categories have a manager-skill premium that warrants ranking on risk-adjusted returns first, with TER as a constraint. See Step 7 for the full passive-vs-active rationale convention.

**For arbitrage funds specifically:** rank by TER first, but **always also surface the exit-load profile** in the recommendation. Many arbitrage funds have 30-day exit loads that destroy the carry edge for monthly STP staging. A fund with TER 0.31% and `exit_load: <15 days` beats a fund with TER 0.37% and `exit_load: <30 days` for STP-source duty even when the higher-TER fund has higher AUM.

For new SIPs going into Direct plans (the default per `principles.md` §3.1), pass `plan="Direct"` to `filter_candidates()`. The skill confirms with the user when ambiguity exists.

If filtering returns fewer than 3 candidates with the strict defaults, the skill loosens by 20% on each numeric threshold and re-runs once. If still fewer than 3, it falls back to sparse-data mode.

### Don't hold cash for "better entry"

Per principle §1.1. If money cannot be deployed today (e.g. lump exceeds STP threshold), the plan is "STP over 3-6 months starting this week" — not "wait for a dip then decide."

### Pragmatism substitution requires explicit user opt-in

When the principle-aligned vehicle for a slot is missing from `fund_quality.json`, the **only** acceptable default response is to invoke `/fund-research` for that category. The skill does NOT silently fall back to a less-aligned but operationally simpler alternative — that is a user decision, not an agent decision.

Examples of pragmatism substitutions the skill must NOT make without asking:
- **Arbitrage parking → savings account / liquid fund.** Principle §2.5 designates arbitrage as the STP staging vehicle (equity-tax-treated, ~5.7% net). Substituting savings (slab-taxed, ~2.4% net) violates the principle. If `fund_quality.json` has 0 arbitrage entries, run `/fund-research` for arbitrage funds — don't default to savings.
- **Gold ETF → Gold MF.** Principle §2.6 prefers Gold ETF (12m LTCG window) over Gold MF (24m LTCG window). Substituting Gold MF because "user might not have demat" is wrong unless the user has actually been asked. Confirm demat in Step 2.
- **Direct plan → Regular plan.** Principle §3.1 mandates Direct only for new investments. Never substitute Regular without explicit user instruction.
- **Active fund → Index fund** (or vice versa) without the user being aware of the swap. Style-tilt changes are user decisions, not agent decisions.

The correct framing when a substitution might be reasonable: "The principle-aligned pick is X. If you'd rather use Y for [stated operational reason], it costs ~₹Z over the holding period and deviates from principle [§A.B]. Your call."

### Honest about what's deferred

Some items in the plan may be conditional (e.g. NPS 80CCD(2) capacity depends on employer support per `goals.md`). The skill flags these as conditional and provides the user-action to resolve them, without blocking the rest of the plan.

## Workflow

> **Critical:** every step below must be executed in order. Skipping the discovery
> phase (Phase 0) was how prior runs missed half the available tools and bypassed
> the §6.4 drawdown gate. The checklist exists to make that mistake structurally
> hard to repeat.

### Phase 0 — Mandatory tool & data discovery (cannot skip)

**Run discover.py first. Quote its output before doing anything else.**

```bash
python3 scripts/recurring_runner.py    # Bring auto-tranches up to date (idempotent)
python3 scripts/fetch_nav.py --quiet   # Refresh NAVs (no-op if <24h old per the daily cron, but cheap to retry)
python3 scripts/discover.py            # The mandatory Phase 0 entry point
```

`discover.py` emits a 10-section structured report covering:
1. **Helper inventory** — every public function in `scripts/lib/`. *Cite the helpers you intend to use.*
2. **Script inventory** — every executable in `scripts/`.
3. **NAV freshness** — fetch age, latest NAV date, schemes with history. *If STALE, refresh before quoting prices.*
4. **Ledger health** — txn count, date range, schemes held. *If BLOCKER, run `scripts/backfill_units.py` first.*
5. **Recurring registry** — active SIPs/STPs and monthly outflow.
6. **fund_quality.json coverage** — entries, completeness, by-category breakdown. *Categories with 0 entries → invoke `/fund-research` before committing a scheme pick.*
7. **laws/ staleness** — per file vs latest Budget. *If STALE, surface caveat in the plan.*
8. **decisions-log open ACTIONs** — count of unresolved items. *Read the log in full and honour prior commitments.*
9. **Drawdown gate (§6.4)** — per-sub-portfolio aggregate equity drawdown. **If `principle_64_blocked: true`, do not propose any equity-additive recommendation. Stop and tell the user.**
10. **Sub-portfolio totals** — current value per sleeve, derived from the ledger × current NAVs. *This is your authoritative current-state input — do NOT parse `portfolio.md` Section 1.5 visually.*

**Quoting requirement.** Before producing any allocation plan, the agent's response must include a "Discovery snapshot" block that quotes (paraphrasing the key fields):
- NAV freshness status + latest_nav_date
- Ledger txn_count and latest_txn_date
- fund_quality coverage for each category the plan needs
- Drawdown gate status per sub-portfolio (with the actual weighted_dd numbers)
- Sub-portfolio totals (with sleeve breakdown)

If any of these is missing from the response, the plan is incomplete by definition.

### Step 1 — Read the foundation files

After discovery, read in order:
1. `goals.md` — surplus, regime, bracket, goals, income sources
2. `principles.md` — universal framework: especially sub-portfolio architecture (§2.1), within-equity composition (§2.4), debt sleeve framework (§2.5), gold (§2.6), deployment priority (§4.1), fresh-fund framework (§8)
3. `user-principles.md` — the user's structural choices: sub-portfolio names + sleeve targets (§3), glide paths (§4), goal-bucket overlay (§5), money routing (§6), regime (§7), vehicles in use (§8), deployment priority overrides (§9), drift policy (§10), STP threshold (§11). **This is the authority for any numeric target or routing rule.**
4. `laws/index.md` — and any specific files relevant to wrapper-fill items the user is contemplating
5. `decisions-log.md` — fully read; the discover.py count is just a flag

`portfolio.md` is read for narrative context (sub-portfolio assignment notes, reconciliation history) but NOT for current values — those come from `discover.py` section 10 and, when more detail is needed, `python3 scripts/render_portfolio.py --json`.

### Step 2 — Establish the input

Capture from the user (one batch if not already supplied). **Ask the full checklist before drafting the plan** — partial input drives wrong defaults.

- Source of money (salary surplus / business lump / bonus / windfall)
- Amount (₹)
- Cadence (one-time / recurring monthly / recurring quarterly / etc.)
- Default sub-portfolio routing (or take the user-principles.md §6 default and confirm)
- Goal earmark intent (retirement / property / education / specific other goal)
- **User-asserted constraints** (e.g. "no PPF this round", "no NPS")
- **Sequential-lumps context:** any *additional* lumps expected in the next 3-6 months? This calibrates STP duration. Sequential ₹X lumps each on a 6-month STP create overlapping schedules; a 3-month STP per lump cleanly stacks. Default: 6-month STP for isolated lumps; 3-month STP per lump when ≥2 are sequenced within 3 months.
- **Demat availability:** does the holder of the receiving sub-portfolio have an active demat account? This gates Gold ETF / direct-equity ETF eligibility. Without demat, gold flows go to Gold MF (Other Scheme - FoF Domestic) — a real principle-§2.6 deviation that needs explicit user opt-in.
- **AMC consolidation preferences:** any AMCs the user wants to keep / consolidate / avoid? Without this, the skill optimises purely on TER + AUM + manager metrics and may push concentration the user dislikes.

### Step 2.5 — Within-equity completeness audit + front-load research for sparse categories

**Before drafting the plan, walk the within-equity completeness checklist explicitly.** The sleeve-level view (equity/debt/gold) hides gaps INSIDE equity. Running checks only at the sleeve level was how prior runs missed Nifty Next 50, passive smallcap, and international leg simultaneously. The completeness audit prevents that recurrence.

**Required within-equity slots for any equity-heavy lump deployment** — read `principles.md` §2.4 for the authoritative SAA midpoints + TAA bands. Default summary (override per user-principles.md if your profile differs):

| # | Slot | Default SAA midpoint | TAA band | Category vocabulary |
|---|---|---|---|---|
| 1 | Nifty 50 (index core) | 48% | 43-53% | Other Scheme - Index Funds (Nifty 50 subset) |
| 2 | Nifty Next 50 (core extension) | 12% | 10-15% | Other Scheme - Index Funds (NN50 subset) |
| 3 | Flexicap (active satellite) | 22% (or higher if intl closed) | 18-26% (25-33% intl-closed) | Equity Scheme - Flexi Cap Fund |
| 4 | Passive midcap | 7% | 5-9% | Other Scheme - Index Funds (Midcap 150 subset) |
| 5 | Passive smallcap | 4% | 3-6% | Other Scheme - Index Funds (Smallcap 250 subset) |
| 6 | International (broad-passive) | 7% | 5-12% (capacity-dependent) | Other Scheme - FoF Overseas |

**SAA + TAA framework rules:**
- Within-equity composition is typically identical across sub-portfolios per `principles.md` §1.8 + §2.4 (long-horizon capital has the same diversification needs regardless of holder).
- The bands are **drift accommodation between annual rebalances**, NOT active timing budgets. Do not adjust within bands based on macro forecasts, sectoral rotation calls, or style-PE timing — all of these violate §1.1 and §9.5.
- Acceptable signals for adjusting within bands at annual review: SPIVA refresh, AUM-bloat metrics, capacity availability, manager continuity, TER moves.
- **International substitution rule** (per `principles.md` §2.4): when broad-passive intl FoFs are closed (RBI cap binding), the international slot absorbs into flexicap. When capacity reopens, redeploy. Do NOT silently substitute Nasdaq 100 — explicit user opt-in required (Nasdaq 100 is tech-concentration, not broad international).

For each slot, the plan must explicitly state **"covered by [fund]"** OR **"deferred because [reason]"**. Silent omissions are structural misses.

**Plus the non-equity slots that complete the plan:**
- Gold vehicle — Other Scheme - Gold ETF if demat available, else Other Scheme - FoF Domestic (Gold MF). Confirm demat in Step 2.
- Arbitrage parking — Hybrid Scheme - Arbitrage Fund, only if equity flow > the STP threshold from `user-principles.md` §11 (default ₹3L).

**For each slot the plan needs, count entries in `fund_quality.json` matching the (category, plan) filter. If any needed slot has <3 candidates, invoke `/fund-research` for it BEFORE drafting the plan**, not after a thin plan provokes user pushback. Bundle research requests as a single up-front message listing all sparse slots:

```
Bundled invocation message to the user (one batch, not per-category):
"I'll need to research these N categories first to give you a rich-data plan:
  - <category 1>: 0 candidates currently → ~10 min research
  - <category 2>: 1 candidate currently (limited universe) → ~10 min research
  - <category 3>: 4 candidates currently (rich-data, no research needed)
Total: ~N×10 min. I'll present consolidated diffs at the end. Anything to skip?"
```

This avoids the failure mode where the agent delivers a thin "limited-universe" plan, then spends 3-4 turns expanding research while the user pushes back.

**Skip this step only when:** the user's request is itself a "research X" call (in which case `/fund-research` IS the workflow), or when all needed categories already have ≥3 entries in `fund_quality.json`.

### Step 3 — Drawdown gate (principle §6.4)

`discover.py` already computed this in Phase 0. Re-state the verdict explicitly:

- If `principle_64_blocked: true` for the chosen sub-portfolio AND the plan would
  add to its equity sleeve → **STOP**. Do not produce equity-additive
  recommendations. Tell the user the gate is triggered, cite the weighted
  drawdown percentage from discover.py section 9, and offer alternatives
  (debt-only deployment, parking in arbitrage until rebound, deferring).
- If `principle_64_blocked: false` → proceed.

This step is non-negotiable. It must appear in the response.

### Step 4 — Walk the deployment priority

Per `principles.md` §4.1 default with overrides from `user-principles.md` §9. For each level, compute the FY headroom against the relevant `laws/<file>.md` cap and apportion annual ₹ vs monthly equivalent. Skip levels the user has excluded.

### Step 5 — Allocate residual using `optimal_sleeve_split()`

Do NOT compute sleeve splits in your head. Use the helper:

```python
from scripts.lib.allocation import optimal_sleeve_split

# Read current sub-portfolio sleeve totals from discover.py section 10
current = {"equity": <from discover.py>, "debt": <...>, "gold": <...>}
# Targets per user-principles.md §3 for THIS sub-portfolio at TODAY's date
targets = {"equity": 0.<target>, "debt": 0.<target>, "gold": 0.<target>}

result = optimal_sleeve_split(
    current=current,
    targets=targets,
    new_money=<residual_after_wrappers>,
    exclude_sleeves=set(),               # user-asserted excludes go here
    hybrid_equity_weight=0.65,           # SEBI ≥65% equity → equity tax treatment
    minimum_floor_inr=10000,             # ensure at least token flow to under-funded sleeves
)
# result["flows"] is per-sleeve ₹ to deploy
# result["post_deployment"] shows where sleeves land
# result["remaining_gap_to_target"] shows what's still under-funded after this round
```

Quote the `flows` and `post_deployment` blocks in the plan.

### Step 6 — STP planning using `plan_stp()` and `plan_lump_purchase()`

For each sleeve flow, decide STP vs lump (per `user-principles.md` §11 threshold, default ₹3L):

```python
from scripts.lib.stp_plan import should_use_stp, plan_stp, plan_lump_purchase

# Per user-principles.md §11 STP threshold
if should_use_stp(equity_flow):
    stp = plan_stp(
        lump_inr=equity_flow,
        source_scheme_code=<arbitrage code chosen via Step 7>,
        source_scheme_name=...,
        dest_scheme_code=<destination code chosen via Step 7>,
        dest_scheme_name=...,
        months=6,                        # 3-6; 6 for first lived volatility
        sub_portfolio=<sub-portfolio name per user-principles.md>,
        source_tax_category="equity",   # arbitrage is equity-tax-treated
        start_date="YYYY-MM-DD",
        day_of_month=15,
    )
    # stp["parking_purchase"] → append to data/transactions.json
    # stp["recurring_stp"]    → append to data/recurring.json["stps"]
else:
    # Sub-threshold or non-equity flow → direct buy
    txn = plan_lump_purchase(
        amount_inr=flow, scheme_code=<code>, scheme_name=...,
        sub_portfolio=<sub-portfolio name>, purchase_date=...,
    )
```

**STP-source tax flag:** the planner enforces that you specify `source_tax_category` explicitly. Arbitrage funds are equity-tax-treated (`equity`). This matters because the redemption legs of a 3-6 month STP held <12 months are STCG. Surface this as a flag in the plan.

### Step 7 — Selection: pick destination schemes (and benchmarks)

**Critical: use the actual SEBI category vocabulary.** Run this once to confirm the canonical strings in `data/market.db`:

```bash
sqlite3 data/market.db "SELECT DISTINCT category FROM schemes WHERE category LIKE 'Equity%' OR category LIKE 'Hybrid%' OR category LIKE 'Other%' OR category LIKE 'Debt%' ORDER BY category;"
```

Common gotchas:
- Index funds: `"Other Scheme - Index Funds"` — **NOT** `"Equity Scheme - Index Funds"` (which doesn't exist)
- Gold ETFs: `"Other Scheme - Gold ETF"`
- Gold FoFs: `"Other Scheme - FoF Domestic"` (with "Gold" in the scheme name)
- International equity FoFs: `"Other Scheme - FoF Overseas"`

For each SIP/STP item, run the rich-data filter:

```python
from scripts.lib.fund_quality import filter_candidates
from scripts.lib.returns import alpha_vs_benchmark, tracking_error, discover_benchmark_for_category

candidates = filter_candidates(
    category="Other Scheme - Index Funds",   # use the canonical category string
    plan="Direct",
    min_aum_crore=500.0,
    max_ter=0.30,
    min_vintage_years=2.0,
    rank_by="return_3y",
    limit=5,
    require_quality_data=False,
)
```

For each candidate, also compute relative-performance signals:

```python
benchmark = discover_benchmark_for_category(category)  # auto-pick or user-specify
for c in candidates:
    a = alpha_vs_benchmark(c["scheme_code"], benchmark, period_days=1095)  # 3Y
    te = tracking_error(c["scheme_code"], benchmark, period_days=1095)
    # Append a["alpha"] and te["annualised_te"] to the candidate row
```

**Why both?** Trailing return alone collapses to noise within a category — index trackers cluster within ~12 bps on 3Y. Tracking error differentiates them; alpha differentiates active funds.

**Per-category ranking convention (passive vs active):**

Passive funds (index, gold ETF, arbitrage) have **no manager-skill premium** to pay for — the manager's job is to minimise tracking error, not to pick stocks. Active funds do have a manager-skill premium that justifies higher TER when the alpha is real and durable. The ranking convention encodes this:

| Type | Categories | Primary rank | Secondary filters | Rationale language |
|---|---|---|---|---|
| **Passive** | Other Scheme - Index Funds, Other Scheme - Gold ETF, Hybrid Scheme - Arbitrage Fund | **TER (ascending)** | AUM ≥ floor, vintage ≥ floor, tracking error <1% (index/gold ETF only) | Lead with TER + cost-compounding math. **Do NOT use manager tenure as primary rationale.** Manager-tenure is irrelevant for passive trackers. |
| **Active** | Equity Scheme - Flexi Cap, Large Cap, Large & Mid Cap, Mid Cap, Small Cap; Hybrid Scheme - Multi Asset; Debt Scheme - * | **return_3y or return_5y (descending)** | TER ≤ ceiling, AUM ≥ floor, vintage ≥ floor, manager tenure ≥ floor | Lead with risk-adjusted return + manager tenure + style fit. TER is a constraint not a tiebreaker (within ~30 bps spread). |

**Cost-compounding rationale for passive picks (mandatory):**

When recommending a passive fund, the rationale must include the rupee-cost-of-TER over the holding period, not just basis-point comparisons. Default formula:

```
TER drag (₹) ≈ TER × time_weighted_average_balance × years
```

For ₹X invested today at ~10% nominal CAGR over Y years, TWA balance ≈ X × ((1+r)^Y - 1) / (Y × r) ≈ ~3-4× the initial principal for 25-year horizons. So a 15 bps TER difference on ₹3L over 25 years = 0.0015 × ~₹10L × 25 ≈ **~₹40K terminal-value loss** — this is the real "expensive" picture.

Quote this number explicitly in the recommendation.

**For active picks, the cost-compounding math is also useful** but is secondary to manager-skill rationale (alpha-vs-benchmark, style fit).

**Mode resolution:**

- **≥3 candidates returned**: rich-data mode. Present top 3-5 with TER, AUM, manager, manager_tenure_years, vintage_years, return_1y/3y/5y, alpha (active funds), tracking_error (index funds), `quality_completeness` (flag if <0.75), `last_verified` (flag if >90 days old).
- **1-2 candidates returned**: limited-universe mode. Present available, flag explicitly, recommend `/fund-research` to expand.
- **0 candidates returned (sparse)**: invoke the **`/fund-research`** skill to populate `fund_quality.json` for this category. Once populated, re-run filter_candidates(). If the user prefers to defer research, present the category-shaped specification with a "selection-pending" flag.

**Fallback when filters are too strict:** if 0 candidates but JSON has entries in the category, auto-loosen filters by 20% and re-run once. Surface the loosening explicitly.

### Step 8 — Project drift and goal progress

Before finalising, project where the plan lands:

```python
from scripts.lib.projection import project_drift, goal_progress, DEFAULT_REAL_RETURN_SCENARIOS

# Where do sleeves land in 12 months given the chosen flows?
drift = project_drift(
    current_holdings=current,
    flows=result["flows"],
    months=12,
)
# drift["effective_equity_pct"] → quote in plan; compare against target

# How does this contribute to the relevant goal?
progress = goal_progress(
    current_corpus_inr=<household corpus or sub-portfolio earmarked corpus>,
    target_corpus_inr=<from goals.md>,
    target_date=<from goals.md>,
    monthly_flow_inr=<post-this-plan monthly>,
    real_return_pct=DEFAULT_REAL_RETURN_SCENARIOS,
)
# progress["scenarios"]["base"]["pct_of_target"] → quote
```

Surface base / optimistic / pessimistic in the plan summary so the user sees the scenario range, not a point estimate.

### Step 9 — Generate the plan

Use `references/output-format.md` for exact structure. Required sections:

1. **Discovery snapshot** (quoting Phase 0 fields — see Phase 0 quoting requirement)
2. **Drawdown gate verdict** (per principle §6.4)
3. Source / amount / cadence / sub-portfolio routing (per user-principles.md §6)
4. Wrapper-fill items in priority order
5. Per-sub-portfolio sleeve contributions (from `optimal_sleeve_split()`)
6. Per item: category-shaped spec + ranked candidate list (with alpha / TE) OR `/fund-research` invocation
7. STP schedule (from `plan_stp()`)
8. **Tax implications (mandatory)** — entry events / parking carry & tax / forward holding-period clocks per leg / LTCG harvesting calendar / net household tax footprint. See `references/output-format.md` Section 8.
9. Drift projection (from `project_drift()`)
10. Goal progress contribution (from `goal_progress()`)
11. Rationale citations to `principles.md` and `user-principles.md` throughout. **For passive picks: rationale must include rupee-cost-of-TER over the holding period (not just bps).** **For passive picks: do NOT use manager-tenure as primary rationale.**
12. Conditional items flagged
13. Data quality summary: rich-data vs limited-universe vs sparse-data per item

### Step 10 — Capture user response and selection

For each plan-item, ask the user (per item or batch):
- For each wrapper-fill item: confirm proceeding (Acted) or defer with reason
- For each SIP/STP in **rich-data mode**: confirm scheme pick from the ranked list (typically the top-ranked unless the user has a reason). Record the chosen `scheme_code` against the plan-item.
- For each SIP/STP in **limited-universe or sparse-data mode**: confirm whether to (a) commit to the top candidate despite limited data, (b) defer this SIP until research is done, or (c) hand-pick using the category specification and report the chosen scheme_code at next session.
- Selection deferrals are recorded with a follow-up date.

### Step 11 — Update decisions-log.md and recurring registry

Append the plan and user response to `decisions-log.md` under the format described in portfolio-review's `output-format.md`. Each plan-item gets a stable ID (e.g. `ALLOC-YYYY-MM-DD-001`). For rich-data mode picks, also record which `scheme_code` was chosen and the filter parameters that produced the ranked list (so future re-runs can audit consistency).

**For each SIP or STP the user commits to registering at their AMC**, also append an entry to `data/recurring.json` (under `sips` or `stps`). Required fields:
- For SIPs: `sip_id`, `destination_scheme_code`, `destination_scheme_name`, `amount_inr`, `frequency: "monthly"`, `day_of_month`, `start_date`, `end_date` (null unless time-bound), `sub_portfolio` (per user-principles.md), `status: "active"`.
- For STPs: `stp_id`, `source_scheme_code`, `source_scheme_name`, `source_tax_category` (one of: `equity`, `specified-mf`, `hybrid-equity-oriented`, `hybrid-debt-oriented`, `non-equity-pre-Apr-2023`), `destination_scheme_code`, `destination_scheme_name`, **`amount_inr_per_tranche`** (NOT `amount_inr` — `recurring_runner.py` reads this key), `frequency: "monthly"`, `day_of_month`, `start_date`, `end_date`, `sub_portfolio`, `status: "active"`, `stop_when_source_exhausted: true|false`, `exit_load: null` or `{"days": int, "pct": float}`.

`scripts/recurring_runner.py` (scheduled monthly) reads this file and auto-generates the corresponding ledger rows on each tranche date.

### Step 12 — Closing

Tell the user:
- Total plan: how much was allocated, where, what's next
- Action items: which scheme accounts to open this week, which SIPs to set up, which selection research to do (where deferred)
- Pending items: the gating event and follow-up date
- The expected timeline to get the SIPs live (typically 2-4 weeks for a full first design)
- A reminder that any new candidate funds researched should be added to `fund_quality.json` so future runs benefit

**Then emit the "Report back when executed" block** — a copy-pasteable confirmation template the user edits and pastes back once they've executed at the AMC. Format:

```
=== Report back when executed (paste back to me, edit amount/date if different) ===
Bought ₹<amount> <scheme name> on <YYYY-MM-DD>           # one line per one-off purchase
Registered SIP: ₹<amount>/month <scheme name> from <YYYY-MM-DD>   # one line per SIP
Registered STP: ₹<amount>/month <source> → <dest> from <YYYY-MM-DD>  # one line per STP
PPF deposit ₹<amount> to <holder> PPF on <YYYY-MM-DD>     # govt-scheme line
```

When the user pastes back, append each one-off purchase to `data/transactions.json` via `python scripts/log_transaction.py purchase --date ... --scheme-code ... --amount ... --sub-portfolio ...` (NAV resolved automatically from market.db). Append each registered SIP/STP to `data/recurring.json`. Then run `python scripts/render_portfolio.py --write` to refresh portfolio.md Section 1.5.

End with: re-run fund-allocate when:
- A material change in income occurs
- A new lump arrives
- Annual review (typically during the regime decision in Q4)
- After major life events (re-grill goals.md first, then re-run fund-allocate)
- After significantly expanding `fund_quality.json` for categories where the previous run was sparse-data

## Common scenarios (templates)

### Scenario A — Salary surplus SIP design

**Input:** ₹X/month recurring surplus.
**Default routing:** per `user-principles.md` §6.

Walk Steps 4-9 with the surplus as input. Typical pattern:
- Wrapper-fill (PPF/VPF/NPS depending on user's vehicles and regime) consumes a portion
- Residual flows into SIPs across the user's sub-portfolio sleeves
- Each sleeve flow goes to category-shaped destinations per Step 7

### Scenario B — One-time lump (bonus / windfall / business receipt)

Treat as a single lump. Walk the priority sequence; deploy residual via STP if > the STP threshold (per `user-principles.md` §11) into equity. Selection via `filter_candidates()` for each STP destination.

### Scenario C — Salary jump / income revision

Same flow as Scenario A with updated input. New surplus → re-walk priority sequence. Wrapper-fill caps unchanged unless the user is now eligible for new vehicles (e.g., crossed a threshold). Residual SIPs scale up.

## Key reminders

- **Routing is the value; selection now also has structure.** With Phase 3 data, the skill ranks candidates from the user's researched universe. Without it (sparse `fund_quality.json`), the skill degrades gracefully to category-shaped specification + selection deferral. Never invents recommendations.
- **Front-load research (Step 2.5).** If any needed category has <3 candidates in `fund_quality.json`, run `/fund-research` BEFORE drafting the plan.
- **Capture full Step 2 input before drafting.** Sequential lumps + demat status + AMC preferences are not optional — they change the structure of the plan.
- **Passive funds: rank by TER. Active funds: rank by return.** Manager-tenure is irrelevant for passive trackers.
- **Cost-compounding math is mandatory for passive picks.** Quote the rupee-cost-of-TER over the holding period.
- **Pragmatism substitution requires explicit user opt-in.** When the principle-aligned vehicle is missing from `fund_quality.json`, invoke `/fund-research` — don't silently fall back.
- **Tax implications section is mandatory.** Every plan ends with the four tax buckets (entry events / parking carry / forward holding-period clocks / LTCG harvesting calendar).
- **Wrapper-fill before SIPs.** Per `principles.md` §4.1.
- **Sub-portfolio routing, sleeve targets, glide paths, regime, vehicles come from `user-principles.md` — never hardcoded.**
- **Drift correction goes through new flows, not sales.** Per principle §6.3.
- **STP over lump-sum for ≥ the threshold from `user-principles.md` §11 into equity.**
- **Every allocation cites a principle.** Every scheme recommendation cites the filter parameters that produced its ranking.
- **Don't hold cash for entry.** Per principle §1.1.
- **No tax-check unless redirecting existing holdings.** Fresh deployment has no tax events.
- **Conditional items flagged, not blocking.** NPS 80CCD(2) availability is a common example.
- **Log every plan to decisions-log.md.** Audit trail for learning.
- **Surface stale `fund_quality.json` entries** (`last_verified` >90 days) but proceed with the data; flag for refresh.
- **Never silently fall back to invented recommendations.** If a category has 0 candidates in `fund_quality.json`, say so and run `/fund-research`.
