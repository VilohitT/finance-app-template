---
name: tax-check
description: Computes the tax implication of a contemplated investment transaction in the Indian context — redemption, switch, Direct-to-Regular conversion, partial sale, LTCG harvesting check. Reads laws/ folder for current rules, goals.md for user's tax regime and bracket, portfolio.md for cost basis and holding dates. Returns structured output (gain type, gain amount, tax owed, net proceeds, holding-period flags, source rule citations). Use whenever the user or another skill asks about the tax cost of selling, switching, or redeeming any investment, or wants to know LTCG harvesting opportunities, or needs to model a hypothetical transaction. Invoke proactively when portfolio-review or fund-allocate is about to recommend any action that triggers a capital gains event. Internal plumbing skill — not chatty, returns data the calling skill folds into recommendations. Indian-context aware (LTCG/STCG framework post-23-Jul-2024, debt MF Section 50AA layered rules, ₹1.25L equity LTCG exemption, regime-dependent treatment).
---

# tax-check

A focused tax-computation skill that turns "what's the tax cost of selling/switching/redeeming this holding?" into a structured, citable answer. Reads the holding from `portfolio.md`, the rules from `laws/`, and the user's tax position from `goals.md`. Returns gain type, gain amount, tax owed, and net proceeds — with rule citations for every fact applied.

Designed to be called **by other skills** (portfolio-review, fund-allocate) and occasionally **by the user directly** for hypothetical modelling.

## When to use

Trigger this skill when:

- A redemption, switch, or sale is being contemplated for any holding (full or partial)
- Direct-to-Regular plan switch is being considered (it's a redemption + new purchase)
- LTCG harvesting check at FY-end (which equity holdings can be sold up to the ₹1.25L exempt threshold)
- Hypothetical: "if I sold X, what would I owe?"
- Pre-redemption reality check before the user actually transacts
- Annual review item: holding-period transitions (something about to flip from STCG to LTCG)
- Cross-checking a calculation a fund platform / broker has shown the user

The skill is also invoked **internally** by:
- `portfolio-review` — before recommending any switch / redemption / Regular-to-Direct conversion
- `fund-allocate` — when a recommendation involves redirecting capital from existing holdings (rare; flow-redirect is preferred)

## What this skill does NOT do

- **Does not advise** whether to do the transaction. It tells the user the tax cost. Whether the cost is worth paying is for the calling skill or the user to decide.
- **Does not give legal opinions** on edge cases. Where the rule is genuinely ambiguous, the skill says so and points at the source.
- **Does not transact** anything. It's a calculator and a citation engine.
- **Does not refresh the rule book.** If `laws/` is stale, the skill flags it and proceeds with a caveat — `laws-refresh` is the skill that updates the rules.
- **Does not capture missing data** from the user mid-call. If portfolio.md has UNKNOWN fields needed for the computation, the skill returns a structured "data needed" output rather than guessing.

## What this skill produces

A **structured tax-check report** for each contemplated transaction. The exact format is in `references/output-format.md`. Conceptually:

```
TRANSACTION: <holding> — <full / partial> — <action>
INPUTS USED:
  Holding: <scheme>, <plan>, <cost basis>, <first purchase date>, <units>
  User context: regime, bracket, surcharge, FY YTD LTCG used
RULE PATH:
  Asset class → tax section → rate
  Holding period: X months → STCG / LTCG
  Citation: laws/<file>.md Section X.Y
COMPUTATION:
  Sale proceeds: ₹X
  Cost basis: ₹Y
  Gross gain: ₹(X-Y)
  Exemption applied: ₹Z (if applicable)
  Taxable gain: ₹W
  Tax (rate × taxable + surcharge + cess): ₹T
  Exit load deducted: ₹E (if applicable)
  Net proceeds: ₹(X - E - T)
FLAGS:
  - [any data limitations, e.g. "per-folio summary used; FIFO precision not available"]
  - [any rule freshness warnings, e.g. "laws/equity-mf.md last verified Budget 2026"]
  - [any optimisation hints, e.g. "holding crosses 12-month threshold in 14 days; deferring saves ₹X"]
NOT-FOR-DECISION CAVEAT:
  - "This computes the tax cost. Whether to proceed is for the user / calling skill."
```

## Operating principles

### Read the rule, cite the rule
Every numeric input to the computation comes from a `laws/` file or a lib helper. The skill does not pull rates from training data or assume current values. If the relevant `laws/` file is stale (per the staleness rules in `laws/index.md` and surfaced in discover.py §7), the skill flags it and proceeds with a caveat. It does not refuse to compute, but it makes clear the result is conditional on the laws being current.

### Verify NAV freshness before quoting prices
Sale proceeds estimation uses `transactions.latest_nav(scheme_code, conn)`. If `db.last_fetch_time('amfi_nav')` is older than 24 hours (surfaced in discover.py §3 as STALE), the underlying NAV may be a day or more out of date. Surface this as a flag in the output rather than silently quoting yesterday's NAV as today's.

### Transaction-level data via the ledger ((ledger-backed))
Holdings live in `data/transactions.json` (append-only ledger). Read this for cost basis and per-lot purchase dates. FIFO is the income-tax default for MF unit accounting; the helper `scripts/lib/transactions.consume_fifo(scheme_code, units, txns)` returns the lots that would be consumed for a sale of `units`, with their purchase dates and cost basis. Use it for partial-redemption gain calculations rather than returning DATA NEEDED.

**Caveat on backfill rows:** transactions whose `source` field is `"backfill"` were seeded from approximate wave dates (typically the 15th of the stated month-of-purchase). For a redemption near a holding-period boundary (≤30 days from STCG→LTCG flip), the FIFO lot date may be ±2 weeks off. In that case, surface the ambiguity ("backfilled lot — exact purchase date approximate") and prompt the user to confirm the precise date from their AMC login before treating the redemption as a clean LTCG.

For holdings not in the ledger (FDs, PPF, EPF, real estate, direct equity, physical gold), continue reading `portfolio.md` and report DATA NEEDED if transaction-level history matters.

### Compute conservatively
Where there's interpretive ambiguity (e.g., a hybrid fund's tax classification is UNKNOWN per portfolio.md), the skill computes under the **less favourable** assumption and flags clearly that a determination of the actual classification could improve the outcome. Reason: the user is making a decision; an over-estimate is recoverable, an under-estimate is not.

### Surcharge and cess are not optional
Many quick tax estimates skip surcharge and cess. This skill includes them. For most cases (income < ₹50L), surcharge is 0% but cess is always 4%. For higher incomes, surcharge applies. Per `laws/capital-gains.md` Section 3, the equity LTCG/STCG surcharge is capped at 15%. The skill applies the correct surcharge tier and the 4% cess on top.

### Holding period transitions get explicit attention
If a holding is currently STCG-eligible but crosses to LTCG within ~30 days, the skill flags this as an optimisation hint — usually meaningful (LTCG rates are 12.5% vs 20% STCG for equity, and the ₹1.25L exemption only applies to LTCG).

### Exit loads are part of net proceeds
For mutual funds, exit loads (typically 1% if redeemed within 1 year for equity) are deducted before the gain is computed (load reduces the redemption value). The skill checks `portfolio.md` for the holding's first purchase date against typical exit-load windows.

### LTCG harvesting check is a recurring use case
At any point in the FY, the skill can be asked: "How much equity LTCG can I harvest within the ₹1.25L exempt threshold?" — the answer factors:
- FY YTD realised LTCG already used
- Available headroom (₹1.25L minus YTD)
- Which holdings have unrealised LTCG that could be harvested
- Per holding: what unit volume sells to capture the headroom

This is a `portfolio-review` use case but lives in `tax-check`.

### Hypothetical modelling is supported
The user can ask "what if I sold X" without actually intending to sell. The skill computes and returns the answer; the user uses the information however they want. No advice, no nagging.

## Workflow

> **Critical:** every step below must be executed in order. Phase 0 establishes
> NAV freshness, ledger health, and laws/ staleness — all prerequisites for an
> honest tax-check output. Skipping it produces numbers without provenance.

### Phase 0 — Mandatory data discovery (cannot skip)

When called by another skill, the calling skill has already run discover.py and
the relevant snapshot is in context — read it from there rather than re-running.
When called directly by the user, run it now:

```bash
python3 scripts/discover.py
```

Quote these sections in the tax-check output's "Inputs used" block:

- **§3 (NAV freshness)** — if STALE, sale-proceeds estimates use yesterday's
  NAV; surface the staleness as a flag. If the data layer is offline entirely,
  the skill computes against user-supplied sale value and flags "NAV layer
  unavailable; using user-stated proceeds."
- **§4 (Ledger health)** — if BLOCKER (empty ledger), full and partial
  redemption math both fall back to portfolio.md cost-basis-per-folio. Surface
  as a "ledger unavailable; precision degraded" flag. For non-MF assets (FDs,
  PPF, EPF, real estate, gold physical, direct equity) this is the normal path
  regardless.
- **§7 (laws/ staleness)** — for every laws file the computation cites, check
  the staleness flag from §7. If any cited file is STALE (older than the most
  recent Budget), prepend the "Rule freshness" caveat per output-format.md.

If the calling skill (portfolio-review or fund-allocate) has already surfaced
this snapshot, do not re-run; reference theirs and avoid duplicate quoting.

### Step 1: Identify the transaction

The caller (user or another skill) describes:
- Which holding(s) — by scheme name, folio if available, or "all my equity LTCG-eligible holdings" for harvesting check
- What action — full redemption / partial redemption (with units or rupee amount) / switch (to which scheme) / Regular-to-Direct conversion / harvesting check
- When — today, or a specific future date for projection

If any of these is unclear, ask once for clarification. Don't run the calculation on guesses.

### Step 2: Read the data

Read in this order:
1. `goals.md` Section 2 — user's tax regime, marginal bracket, applicable surcharge tier
2. `data/transactions.json` (for MF holdings) — load via `scripts/lib/transactions.load_transactions()` and call `consume_fifo(scheme_code, units, txns)` to get the lot-level cost basis. For full redemptions (selling all units), `cost_basis_per_scheme(txns)` gives the total directly.
3. `portfolio.md` — the holding's plan, sub-portfolio, scheme metadata, and (for non-MF assets only) cost basis and purchase dates
4. `laws/index.md` — to identify the right laws files
5. `laws/<asset-class>.md` — the specific tax rules for the asset class (e.g. `laws/equity-mf.md` for an equity MF redemption, `laws/debt-mf.md` for a debt MF, etc.)
6. `laws/capital-gains.md` — the cross-cutting framework, especially for surcharge / cess / set-off
7. Where applicable: `laws/regime-comparison.md` for any regime-dependent piece, `laws/sebi-categories.md` for category verification

Note any staleness flags from `laws/index.md`.

### Step 3: Identify the rule path

Map the transaction to the applicable rules:
- Asset class (equity MF / debt MF / hybrid / SGB / direct equity / etc.)
- Acquisition date — which determines applicable regime (e.g. debt MF Regime A/B/C per `laws/debt-mf.md`)
- Holding period — STCG vs LTCG, or slab rate for Specified Mutual Fund
- Tax section that applies — 111A, 112A, 112, 50AA
- Rate (with surcharge tier and cess)
- Any exemptions (₹1.25L for equity LTCG, transitional rules for pre-cutoff acquisitions, etc.)

Cite each rule by `laws/<file>.md` Section number.

### Step 4: Check for data limitations

**MF holdings (ledger-backed) ledger backfill:** partial redemption is no longer
DATA NEEDED. `transactions.consume_fifo(scheme_code, units, txns)` returns the
exact lots consumed with their cost basis and purchase dates. Use it.

**Non-MF holdings** (FDs, PPF, EPF, direct equity, physical gold, real estate)
are not in the ledger. For these, read cost basis and purchase dates from
portfolio.md. If portfolio.md flags `cost_basis_granularity: per-folio summary`
on a holding AND the user is asking about a partial sale, return DATA NEEDED
with the specific fetch source (CAS for MFs that aren't in the ledger,
Zerodha Console > Reports > Tax P&L for direct equity, etc.).

**Backfilled MF lots:** transactions whose `source` field is `"backfill"` were
seeded from approximate wave dates (typically the 15th of the stated
month-of-purchase). For a redemption ≤30 days from a holding-period boundary,
flag the lot date as approximate and prompt the user to confirm from their AMC
login before treating the redemption as a clean LTCG.

**UNKNOWN tax classifications** (e.g. the household's two multi-asset funds):
compute under each plausible classification per `references/computation-rules.md`
Section C and flag — do not silently pick one.

**Exit load.** For STP-derived units, the source's STP entry in
`data/recurring.json` carries the `exit_load` field set by `stp_plan.plan_stp()`
— use that. For ledger-recorded redemptions, `transactions.classify_gain()` /
the redemption row's `exit_load_inr` is authoritative. For one-off contemplated
redemptions where the holding is in the ledger, look up the source scheme's
factsheet exit-load schedule; if unavailable, default to category convention
(1% equity within 1 year, typically 0% for debt) and flag.

### Step 5: Compute

Use the lib helpers; do not write prose-arithmetic for any quantity a helper
already computes.

**Full redemption (MF in ledger):**

```python
import sys; sys.path.insert(0, 'scripts')
from lib.transactions import (
    load_transactions, cost_basis_per_scheme, units_per_scheme,
    latest_nav, classify_gain,
)
from lib.db import get_conn

txns = load_transactions()
cost = cost_basis_per_scheme(txns)[scheme_code]
units = units_per_scheme(txns)[scheme_code]
with get_conn() as conn:
    nav_date, nav = latest_nav(scheme_code, conn)
sale_proceeds = round(units * nav, 2)

# Earliest purchase date for the holding (drives STCG/LTCG)
earliest_purchase = min(
    t["date"] for t in txns
    if t["scheme_code"] == scheme_code and t["units"] > 0
)
gain_type = classify_gain(
    purchase_date=earliest_purchase,
    sale_date=date.today().isoformat(),
    tax_category=<one of VALID_TAX_CATEGORIES per portfolio.md>,
)
# gain_type is e.g. "LTCG-equity (12.5% over ₹1.25L)" — apply the rate from
# laws/equity-mf.md or laws/debt-mf.md based on which classification fired.
```

**Partial redemption (MF in ledger):**

```python
from lib.transactions import consume_fifo

cost_basis_consumed, lots = consume_fifo(scheme_code, units_to_sell, txns)
# lots = [(units, source_txn_id, source_purchase_date), ...] in FIFO order.
# Apply classify_gain per-lot and aggregate; surface STCG vs LTCG split.
```

This is the **default partial-redemption path** (ledger-backed). It is no longer
DATA NEEDED. (If `lots[0]` has a backfilled source date and the redemption is
near a holding-period boundary, flag per Step 4.)

**Apply rates and exemption.**

After classifying the gain, look up the rate in the cited `laws/` file
(equity-mf, debt-mf, gold, capital-gains for the cross-cutting surcharge/cess).
The skill does NOT pull rates from training data — the rate comes from the
file, the citation goes in the output.

For equity LTCG: apply the ₹1.25L FY exemption against the gain (after
subtracting FY YTD realised LTCG already used per goals.md or user input).
Surcharge cap of 15% applies for §111A and §112A gains; cess is 4% on
(tax + surcharge). All three line items appear in the output.

**LTCG harvesting:**

Available headroom = ₹1.25L − FY YTD realised equity LTCG. For each
LTCG-eligible equity holding (purchase date > 12 months ago), compute how many
units sell to consume the headroom. `cost_basis_per_scheme` and
`current_value_per_scheme` give the inputs; `consume_fifo` gives the lot-level
basis when slicing partial harvests.

**Direct-to-Regular switch (or vice-versa):**

It's a redemption + a fresh purchase. Compute the redemption as above; the
fresh purchase has no tax event but starts a new holding-period clock with cost
basis = redemption-day NAV. Flag the reset.

**Net proceeds:**

`net_proceeds = sale_proceeds − exit_load_inr − total_tax`. The output shows
each line item separately; do not collapse to a single number without the
breakdown.

### Step 6: Format output

Use the structure in `references/output-format.md`. Include:
- All inputs used (so the user can verify)
- Rule path with citations
- Computation step-by-step
- Flags (data limitations, freshness warnings, optimisation hints)
- Net proceeds
- The "not-for-decision" caveat

Do not add advice on whether to do the transaction. The output is data.

### Step 7: Return

If called by another skill: return the structured report as a single block. The calling skill folds it into its recommendation.

If called by the user directly: present the report. Optionally, the user can ask follow-up questions (e.g. "what if I waited 3 weeks for LTCG?" — re-run with adjusted holding period).

## Common scenarios

### Scenario 1: Full redemption of an equity MF
Inputs: scheme, plan, cost basis, first purchase date, current value.
Output: STCG or LTCG, tax, net proceeds, citation to `laws/equity-mf.md`.

### Scenario 2: Direct-to-Regular conversion (or vice versa) of one of father's holdings
Inputs: scheme A details (current Regular plan), proposed scheme B (Direct equivalent).
Output: tax cost on the redemption of A, holding-period reset for B, recommendation hint flag (typically: wait for exit load window to close + LTCG eligibility before switching to minimise tax).

### Scenario 3: Partial redemption of a debt MF (Regime C, slab rate)
Inputs: scheme, units to redeem.
Output: call `transactions.consume_fifo(scheme_code, units, txns)` to get the lot-level cost basis and purchase dates. Apply slab rate per `laws/debt-mf.md` Section 50AA — every Regime C debt MF lot is slab-rate regardless of holding period. (Before the ledger was populated this was DATA NEEDED on a per-folio summary; the ledger makes it computable.)

### Scenario 4: LTCG harvesting check at FY-end
Inputs: all equity holdings, FY YTD realised LTCG.
Output: available headroom, per-holding sell schedule to use it.

### Scenario 5: Multi-asset fund redemption (tax classification UNKNOWN)
Inputs: scheme, cost basis, first purchase date.
Output: computation under each plausible classification (equity-oriented vs Section 112 hybrid vs Specified MF), flagged "actual classification needs verification — fetch from scheme factsheet."

## Key reminders

- **Cite, cite, cite.** Every numeric input traces to a laws file section.
- **Use the helpers.** `transactions.cost_basis_per_scheme`, `transactions.consume_fifo`, `transactions.classify_gain`, `transactions.latest_nav`, `db.last_fetch_time`. If you find yourself writing prose-arithmetic for a quantity these helpers compute, stop and call the helper.
- **Conservative on ambiguity.** Compute under less favourable assumption when uncertain; flag clearly.
- **Don't advise.** Tax cost is the output; whether to act on it is downstream.
- **Don't refuse computation when data is missing.** Return DATA NEEDED with the specific fetch requirement — but only when the data genuinely isn't in the ledger. For MFs in the ledger, partial redemptions are FIFO-computable, not DATA NEEDED.
- **Surcharge and cess always.** Default-omitting these gives wrong tax estimates.
- **Holding-period transitions are worth flagging.** A 14-day wait can save material tax.
- **No interpretation of whether the user should transact.** That's for the calling skill or the user.
