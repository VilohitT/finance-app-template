# Deployment logic — fund-allocate

The exact computation flow the skill walks when generating an allocation plan. This cookbook is what SKILL.md's Workflow section steps you through; refer here when you need the precise computation for a step.

> **Phase 0 must run first.** This file describes Phases 1-7 only. Before any of it kicks in, run `python3 scripts/discover.py` and quote the snapshot (see SKILL.md Phase 0). All current-value figures below come from `discover.py` section 10 or `scripts/render_portfolio.py --json` — never from `portfolio.md` Section 1.5 parsed visually.

---

## Inputs

The skill receives:
- **Source:** salary surplus / business lump / bonus / windfall / mixed
- **Amount (₹X):** total to allocate
- **Cadence:** one-time / monthly recurring / quarterly / mixed
- **Default sub-portfolio routing:** taken from `user-principles.md` §6, with user confirmation if ambiguous
- **User-asserted constraints:** explicit excludes (e.g. "no PPF this round")

It reads from:
- `discover.py` output (Phase 0)
- `goals.md`, `principles.md`, `user-principles.md`, `laws/`, `decisions-log.md`
- `scripts/render_portfolio.py --json` for structured holdings (do not parse `portfolio.md`)

It produces:
- A structured allocation plan per `references/output-format.md`

---

## Phase 1 — Establish current state

Read from `python3 scripts/discover.py` section 10, or for finer detail `python3 scripts/render_portfolio.py --json`.

### Per sub-portfolio (per `user-principles.md` §2)
- Current holdings total (₹)
- Allocation per sleeve (equity/debt/gold/hybrid in ₹ and %)
- Drift vs target (per `user-principles.md` §3 — sleeve targets, with optional overrides; per `user-principles.md` §4 — glide-path waypoint applicable today)

### Per scheme capacity (per `user-principles.md` §8)
For each wrapper the user has declared in use or planned, determine the headroom for the current FY:

**PPF (per holder):**
- Annual cap: ₹1,50,000 (per `laws/ppf.md`)
- YTD used: from `portfolio.md` PPF section
- Headroom: cap - YTD

**VPF (per salaried holder):**
- Tax-free threshold for total employee EPF+VPF: ₹2,50,000/year (per `laws/epf-vpf.md`)
- Mandatory EPF YTD: 12% × (Basic+DA) × months elapsed in FY
- Mandatory EPF projected for full FY: 12% × (Basic+DA) × 12
- VPF headroom (tax-free) = ₹2,50,000 - mandatory EPF projected for FY
- (Above-threshold VPF is allowed but interest becomes taxable; only fill up to threshold by default)

**NPS Tier 1 personal (80CCD(1B)):**
- Annual cap: ₹50,000 above 80C
- **Available only under Old Regime** (per `laws/regime-comparison.md`)
- For users under New Regime: dormant (skip)

**NPS Tier 1 employer (80CCD(2)):**
- Cap: 14% of (Basic + DA) per FY for private sector under New Regime, 10% under Old Regime
- Status: depends on employer offering this route — if unknown per `goals.md`, mark CONDITIONAL

**SCSS (per eligible holder):**
- Age must be ≥ 60
- If currently < 60: dormant (note diary entry)

**SGB:**
- Status: paused per `laws/gold.md`
- Treat as dormant; flag if user wants to consider secondary market

### Per existing SIP
- Active y/n
- Amount/month
- Destination scheme
- Sub-portfolio
- Goal earmark

---

## Phase 2 — Walk the deployment priority

Per `principles.md` §4.1 default, with overrides from `user-principles.md` §9. For each level, compute headroom and apportion.

### Level 1 — PPF (per holder)
- Determine: does each declared PPF holder have an open account? (per `portfolio.md`)
- For each existing or to-be-opened account: fill up to annual headroom this FY
- Cadence option: lump on/before 5 April (full-year accrual) OR monthly ₹X (apportion the annual cap)
- For monthly recurring inputs: split the annual fill across remaining months in FY (e.g. if 6 months left in FY, monthly PPF contribution = headroom / 6)

**Output:** PPF fill per holder, residual = X - sum(PPF fills)

### Level 2 — NPS Tier 1 via 80CCD(2) employer (CONDITIONAL)
- If `goals.md` or `user-principles.md` flags 80CCD(2) as unknown/pending: mark this level as CONDITIONAL
  - Plan provisionally allocates a placeholder amount (e.g. 14% × user's Basic+DA × remaining months/12)
  - User-action: HR ticket; the plan finalises after response
- If confirmed available: fill up to cap
- If confirmed not available: skip this level

**Output:** NPS 80CCD(2) ₹C (conditional or actual), residual = residual - C

### Level 3 — NPS Tier 1 personal (80CCD(1B))
- Available only under Old Regime
- If user is on New Regime per `user-principles.md` §7: skip; note "dormant under New Regime"
- If Old Regime: fill up to ₹50K cap

### Level 4 — VPF (per salaried holder)
- Compute headroom: ₹2.5L threshold - mandatory EPF FY projected
- For monthly recurring inputs: VPF rate translates to ₹/month
- Suggest a VPF rate that approximately fills headroom
- VPF is set with HR; confirm setup as an action item

**Output:** VPF ₹D, residual = residual - D

### Level 5 — SCSS (per eligible holder)
- If holder age ≥ 60: fill up to ₹30L cap (per `laws/scss.md`)
- Funded by rolling over existing debt holdings, not necessarily from new contributions
- If age < 60: dormant; note diary item

### Level 6 — SGB tranches (when issued)
- Currently dormant (per `laws/gold.md` — issuance paused)
- Note as INFO / monitor item

### Level 7 — SIP / STP into category-shaped needs (the residual)

After Levels 1-6, the residual flows to SIPs/STPs into sub-portfolio sleeves. This is Phase 3.

---

## Phase 3 — Allocate residual across sub-portfolios

### Step 3.1 — Sub-portfolio routing decision

Defaults per `user-principles.md` §6. The skill reads the routing rule for this inflow source and applies it. If the user has named override conditions (e.g., "if entity A's PPF is unfilled and entity B's is maxed, transfer is OK"), apply them when they fire.

**Over-rides allowed when:**
- A specific sub-portfolio is severely under-allocated AND the alternate has scheme capacity unfilled
- The user has named an over-ride condition that applies

Make routing decisions explicit in the plan ("routing this lump to <sub-portfolio> over the default <other> because <reason>").

### Step 3.2 — Within each sub-portfolio, allocate via `optimal_sleeve_split()`

Do NOT compute splits in your head — call the helper:

```python
from scripts.lib.allocation import optimal_sleeve_split

# Targets per user-principles.md §3 for THIS sub-portfolio at TODAY's date
# (use the current glide-path waypoint per §4)
result = optimal_sleeve_split(
    current={"equity": <₹>, "debt": <₹>, "gold": <₹>, "hybrid": <₹>},
    targets={"equity": 0.<target>, "debt": 0.<target>, "gold": 0.<target>},
    new_money=<sub_portfolio_share>,
    exclude_sleeves=set(),                                  # user-asserted excludes
    hybrid_equity_weight=0.65,
    minimum_floor_inr=10000,
)
```

The helper enforces principle §6.3 (zero flow into over-allocated sleeves) automatically. Use `result["flows"]` directly.

For drift projection over the next 12 months:

```python
from scripts.lib.projection import project_drift
drift = project_drift(current, result["flows"], months=12)
# drift["effective_equity_pct"] vs target — quote in plan
```

### Step 3.3 — Within each sleeve, distribute across category-shaped needs

For each sleeve, apply `principles.md` §2.4 (within-equity SAA + TAA bands), §2.5 (debt ladder), §2.6 (gold vehicle preference) — with overrides from `user-principles.md`.

**Equity sleeve (per sub-portfolio):**

Per `principles.md` §1.8 + §2.4, within-equity composition is typically identical across sub-portfolios. Default slot weights (override per `user-principles.md` if applicable):
- Nifty 50 (index core): 48%
- Nifty Next 50 (core extension): 12%
- Flexicap (active satellite): 22% (or higher if international closed)
- Passive midcap: 7%
- Passive smallcap: 4%
- International (broad-passive FoF): 7%

If international FoF capacity is closed (RBI cap binding), the international slot absorbs into flexicap per `principles.md` §2.4. Do NOT silently substitute Nasdaq 100.

**Debt sleeve:**

Primary debt is typically PPF + VPF (Levels 1, 4 of deployment priority). Debt MF SIP here is supplementary, providing intra-debt liquidity. Recommend short-duration debt fund (Direct), modest amount.

**Gold sleeve:**

Per `principles.md` §2.6: Gold ETF preferred if demat is available; Gold MF (Other Scheme - FoF Domestic) if not. SGB if issuance resumes. Recommend small monthly SIP into Gold ETF Direct (or Gold MF if no demat).

### Step 3.4 — STP threshold check via `should_use_stp()` and `plan_stp()`

```python
from scripts.lib.stp_plan import should_use_stp, plan_stp, plan_lump_purchase

# Per user-principles.md §11 STP threshold (default ₹3L for equity)
if should_use_stp(equity_flow):
    stp = plan_stp(
        lump_inr=equity_flow,
        source_scheme_code=<arbitrage code>,
        source_scheme_name=...,
        dest_scheme_code=<destination>,
        dest_scheme_name=...,
        months=6,                         # 3-6; 6 for first lived volatility
        sub_portfolio=<name per user-principles.md>,
        source_tax_category="equity",     # arbitrage = equity-tax-treated
        start_date="YYYY-MM-DD",
        day_of_month=15,
    )
    # stp["parking_purchase"] → append to data/transactions.json
    # stp["recurring_stp"]    → append to data/recurring.json["stps"]
else:
    txn = plan_lump_purchase(...)         # direct buy
```

**STP-source tax flag:** the planner enforces `source_tax_category`. If the STP runs <12 months from a parking buy, redemption legs are STCG. Surface the holding-period implication explicitly in the plan.

---

## Phase 4 — Generate selection criteria per item

For each SIP / STP / lump-deploy item identified in Phase 3, compose:

**Universal criteria** (defaults; override per case):
- Direct plan (`plan="Direct"`)
- AUM floor (₹500 Cr equity, ₹1,000 Cr for active large/large-mid/flexi)
- Vintage ≥ 3y (≥2y for index)
- Manager tenure ≥ 3y (active funds only)

**Selection helpers:**

```python
from scripts.lib.fund_quality import filter_candidates
from scripts.lib.returns import alpha_vs_benchmark, tracking_error, discover_benchmark_for_category

candidates = filter_candidates(
    category="...",  # use canonical SEBI string from data/market.db
    plan="Direct",
    min_aum_crore=500.0,
    max_ter=0.30,
    min_vintage_years=2.0,
    rank_by="return_3y",
    limit=5,
    require_quality_data=False,
)

bench = discover_benchmark_for_category(category)
for c in candidates:
    a = alpha_vs_benchmark(c["scheme_code"], bench, period_days=1095)
    te = tracking_error(c["scheme_code"], bench, period_days=1095)
    # c["alpha"] = a["alpha"], c["tracking_error"] = te["annualised_te"]
```

**Category vocabulary gotchas:**
- Index funds: `"Other Scheme - Index Funds"` (NOT `"Equity Scheme - Index Funds"`)
- Gold ETFs: `"Other Scheme - Gold ETF"`
- Gold FoFs: `"Other Scheme - FoF Domestic"` (filter by name containing "gold")
- International equity FoF: `"Other Scheme - FoF Overseas"`

Run once to verify canonical strings:

```bash
sqlite3 data/market.db "SELECT DISTINCT category FROM schemes ORDER BY category;"
```

**When 0 candidates:** invoke `/fund-research <category>` to populate `fund_quality.json`. Do NOT fall back to invented recommendations from training-data priors.

---

## Phase 5 — Compose the plan

Use `references/output-format.md` for exact structure. Include:

1. Plan header (ID, source, amount, cadence, default routing per `user-principles.md` §6)
2. Current state summary (sub-portfolio drifts, wrapper headroom)
3. Deployment sequence (Levels 1-7 walked above)
4. Residual after wrapper-fill (the ₹ flowing to SIPs/STPs)
5. SIP/STP allocation per sub-portfolio and sleeve
6. Selection guidance per category-shaped need
7. Conditional and pending items
8. STP schedule (if applicable)
9. Tax implications (mandatory)
10. Drift projection
11. Goal progress contribution
12. Action items summary (what to do this week / next 1-2 weeks)

Each line item carries a principle citation.

---

## Phase 6 — Capture user response

Ask the user (per item or batch):
- Confirm Acted / Defer / Reject for each wrapper-fill item
- Confirm Acted / Modify / Defer / Reject for each SIP item
- For each rich-data SIP/STP: confirm scheme pick from the ranked list (typically top-ranked)
- For sparse-data items: confirm whether to (a) commit to top candidate despite limited data, (b) defer pending `/fund-research`, or (c) hand-pick using the spec
- For conditional items: user-action defined (HR ticket, etc.)

---

## Phase 7 — Update decisions-log.md and recurring registry

Append the plan and user response per the format in `output-format.md`. Each item gets a stable ID.

For each SIP/STP the user is registering at their AMC, also append an entry to `data/recurring.json` (per the schema in SKILL.md Step 11).

---

## Variant: lump deployment

When a lump arrives (e.g. bonus, business receipt), the skill:

1. **Re-runs phases 1-2** to check current FY wrapper-fill status
   - Top up any wrappers not yet maxed for FY
2. **Routes residual** through Phase 3 per `user-principles.md` §6
3. **STP threshold:** > the threshold from `user-principles.md` §11 (default ₹3L for equity) → spread over 3-6 months via `plan_stp()`
4. **Output:** lump-specific plan with STP schedule

---

## Variant: salary jump

When the user's salary changes:

1. **Re-walk all phases** with the new monthly surplus
2. **Wrapper-fill is mostly unchanged** (annual caps are independent of salary, but VPF headroom depends on Basic+DA)
3. **Residual increases**, mostly going to under-allocated sleeves first
4. Note re-evaluation of regime decision if income tier crosses a threshold (re-run `principles.md` §4.2 logic)

---

## Variant: re-running after a portfolio-review action

If `/portfolio-review` surfaces "fund-allocate is needed to design SIPs", fund-allocate runs as above. The plan it produces resolves the portfolio-review ACTION finding.

---

## Variant: plan modification after HR confirms NPS 80CCD(2)

When HR responds on NPS 80CCD(2):
- If yes: plan adds NPS Level 2 with the confirmed amount, removes the conditional flag, and adjusts the residual. Re-run fund-allocate.
- If no: plan removes Level 2 entirely, residual increases, allocate to next-priority items.

---

## Edge cases and error handling

### What if portfolio.md hasn't been refreshed?
- The skill uses `portfolio.md` as-of `last_updated`. If stale (>30 days for an active investor), flag this in the plan header: "portfolio.md last refreshed YYYY-MM-DD; if recent transactions occurred, refresh `/portfolio-grill` before relying on this plan."

### What if laws/ are stale?
- Per `laws/index.md`, if any relevant file is stale: flag at top of plan and proceed with caveat. Recommend running `/laws-refresh` before acting on the plan.

### What if goals.md has no surplus computation?
- Default to asking user: "what's your monthly surplus and any lump cadence to plan around?"
- Don't compute against a missing input.

### What if the user wants to override a sub-portfolio routing?
- Honour the override; record reasoning in the plan
- Flag if the override creates material mis-alignment with principles — but proceed with the user's choice and log

### What if the user has a goal not in goals.md?
- Don't allocate against undeclared goals
- Suggest re-grilling `goals.md` (use `/finance-grill`) before continuing
- For a quick goal addition: ask once, capture in `goals.md` as an addendum, then continue

### What if a planned SIP can't be executed because the user's broker doesn't support that AMC?
- Plan-level: the ranked list from `filter_candidates()` is the menu; if the top pick isn't on the broker's platform, fall back to the next-ranked candidate that is, or open a direct folio with the AMC
- If an entire category is missing from the broker: flag as a follow-up; the SIP is deferred but the ranked list stands

---

## Key reminders

- **Walk the priority strictly.** Don't skip Levels 1-2 to "go straight to SIPs" — wrappers come first.
- **`user-principles.md` drives routing and targets.** Don't infer; read.
- **`principles.md` drives within-sleeve allocation framework.** Cite at every step.
- **Selection draws from `fund_quality.json` via `filter_candidates()`.** Produce ranked candidate lists per category-shaped need (not free-form fund names from training-data priors). Sparse-data → invoke `/fund-research` before committing.
- **Conditional items don't block.** Flag them and move on.
- **Drift correction goes through new flows.** Per principle §6.3.
- **Tax-check only if redirecting existing holdings.** Fresh deployment has no tax events.
- **Log everything.** Audit trail in `decisions-log.md`.
