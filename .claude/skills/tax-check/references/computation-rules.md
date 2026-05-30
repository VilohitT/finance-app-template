# Computation rules — tax-check

Per-asset-class computation flows. This file is the authoritative cookbook the skill follows when computing each transaction type. Read alongside `laws/` (the rules) and `references/output-format.md` (the structure).

The flows assume `goals.md`, `portfolio.md`, and `laws/` have all been read in Step 2 of the workflow, and that Phase 0 (`scripts/discover.py`) has surfaced NAV freshness, ledger health, and laws/ staleness.

## Helpers used (call these; do not re-derive in prose)

- `scripts/lib/transactions.load_transactions()` — load the ledger
- `scripts/lib/transactions.cost_basis_per_scheme(txns)` — net cost basis after FIFO consumption per scheme_code
- `scripts/lib/transactions.consume_fifo(scheme_code, units, txns)` — lot-level cost basis + lot purchase dates for a partial sale
- `scripts/lib/transactions.classify_gain(purchase_date, sale_date, tax_category)` — STCG/LTCG/SpecMF classifier covering the post-23-Jul-2024 boundaries
- `scripts/lib/transactions.latest_nav(scheme_code, conn)` — latest NAV for sale-proceeds estimation
- `scripts/lib/db.last_fetch_time('amfi_nav')` — NAV freshness check
- `scripts/lib/db.get_conn()` — DB connection (context manager)

If you find yourself writing prose-arithmetic for a quantity any of these computes, stop and call the helper.

---

## A. Equity mutual funds

### A.1 Identify gain type
- Look up first purchase date from `portfolio.md`.
- If holding period > 12 months → LTCG (Section 112A).
- If holding period ≤ 12 months → STCG (Section 111A).
- Verify equity-oriented status: scheme should hold ≥ 65% domestic equity. For pure equity-category funds (large/mid/small/multi/flexi/focused/sectoral/index) this is automatic. For aggressive hybrid / equity savings, verify in `laws/sebi-categories.md` Section 5 cheat sheet.

### A.2 Apply rates
- LTCG: 12.5% (Section 112A) — *Source: laws/equity-mf.md Section 3*
- STCG: 20% (Section 111A) — *Source: laws/equity-mf.md Section 2*

### A.3 Apply ₹1.25L exemption (LTCG only)
- Read FY YTD realised equity LTCG from user input or, if tracked, from portfolio.md
- Headroom = ₹1,25,000 - YTD
- Exemption applied to current transaction = min(gross LTCG, headroom)

### A.4 Apply surcharge and cess
- Look up user's total income tier from goals.md Section 2 to determine surcharge tier
- For equity LTCG/STCG specifically: surcharge capped at 15% regardless of income — *Source: laws/capital-gains.md Section 3.3*
- Cess 4% on (tax + surcharge)

### A.5 Compute exit load
- For equity MFs: typical exit load 1% if redeemed within 1 year; else 0%
- Verify against scheme factsheet if user has it; otherwise use category default
- Exit load reduces sale proceeds before gain computation

### A.6 Final
- Net proceeds = sale_proceeds − exit_load_inr − total_tax (each line shown separately in the output)
- For ledger-recorded redemptions, the redemption row's `realised_gain_inr`, `gain_classification`, and `exit_load_inr` (set by `transactions.make_redemption()`) are authoritative and should be quoted directly.

### A.7 Special: ELSS
- Lock-in 3 years per tranche
- Cannot redeem before lock-in expiry; the skill rejects pre-lock-in redemption attempts
- Post-lock-in: same rules as A.1-A.6
- Note: ELSS provides 80C deduction only under Old Regime; the user's regime is in goals.md

---

## B. Debt mutual funds — three-regime layer (most error-prone)

### B.1 Identify regime by purchase date
Look up the earliest in-ledger purchase date for the scheme via `transactions.consume_fifo()` (or just the earliest buy row's `date`). For non-ledger MFs, fall back to portfolio.md. Then:

- **Purchased before 1 April 2023 + sold before 23 July 2024:** Regime A (mostly historical; rare today)
- **Purchased before 1 April 2023 + sold on/after 23 July 2024:** Regime B (transitional)
- **Purchased on/after 1 April 2023:** Regime C (current; almost all of this household's debt MF holdings)

### B.2 Regime A — historical
- LTCG threshold: > 36 months
- LTCG rate: 20% with indexation
- STCG: ≤ 36 months → slab rate
- *Source: laws/debt-mf.md Section 1*

### B.3 Regime B — transitional
- LTCG threshold: > 24 months
- LTCG rate: 12.5% no indexation (Section 112)
- STCG: ≤ 24 months → slab rate
- *Source: laws/debt-mf.md Section 1*
- Indexation NOT available for debt MFs even in transitional period (only for property)

### B.4 Regime C — current (Section 50AA)
- All gains taxed at slab rate, regardless of holding period
- No LTCG concept
- No ₹1.25L exemption (equity-only)
- *Source: laws/debt-mf.md Section 1, Section 50AA*

### B.5 Apply surcharge and cess
- Slab-rate gains use the user's full slab structure including surcharge and cess
- Surcharge cap of 15% does NOT apply (that's equity-only)
- Look up surcharge tier from goals.md based on total income

### B.6 Exit load and final
- Most debt MFs (liquid, ultra-short, money market): no exit load or very small
- Short/medium duration: typically 0% after 7-30 days
- Verify against scheme factsheet
- Net proceeds = sale value - exit load - tax

### B.7 Tax-loss harvesting on debt MFs
- STCL on Regime C debt MF: useful, can offset STCG and LTCG (any source)
- LTCL on Regime B: only against LTCG
- For 30% bracket household, harvesting losses is reasonable but lower-impact than equity (no ₹1.25L threshold to preserve)

---

## C. Hybrid / multi-asset funds (the "verify classification" case)

### C.1 First identify tax classification
A hybrid scheme can fall in three buckets:
- **Equity-oriented** (≥65% domestic equity): Section 111A/112A — equity rates
- **Section 112 hybrid** (35-65% equity): 12.5% no indexation, 24-month LTCG threshold
- **Specified Mutual Fund** (<35% equity, post-Apr-2023): slab rate (Section 50AA)

### C.2 If portfolio.md says UNKNOWN
If `portfolio.md` flags a hybrid / multi-asset holding's tax classification as UNKNOWN (the classification depends on actual equity %, which varies month to month), the skill:
1. Computes under each plausible classification (typically two of the three)
2. Returns all results clearly labelled
3. Flags: "Tax classification UNKNOWN. Verify from scheme factsheet (most recent month's portfolio composition). Conservative computation shown first."

### C.3 Once classification is confirmed
- Equity-oriented → A flow above
- Section 112 hybrid → 12.5% no indexation, 24-month threshold; otherwise like equity LTCG but no ₹1.25L exemption
- Specified MF → slab rate, like B.4

---

## D. Direct equities (listed shares, STT paid)

### D.1 Same as A but for individual stocks
- Buy/sell on exchange = STT paid
- LTCG > 12 months → 12.5% (Section 112A) with ₹1.25L exemption
- STCG ≤ 12 months → 20% (Section 111A)
- Surcharge cap 15% applies

### D.2 Aggregation
- The ₹1.25L LTCG exemption is per FY, per PAN, aggregate across all equity sources (direct stocks + equity MFs)
- The skill aggregates YTD across both when computing harvesting headroom

### D.3 Special: dormant direct equity
If `portfolio.md` records direct equity holdings with UNKNOWN per-stock cost basis (common for dormant legacy holdings), and the user contemplates a redemption:
- The skill returns DATA NEEDED with the fetch source (e.g., broker's capital gains statement / Zerodha Console > Reports > Tax P&L)

---

## E. Sovereign Gold Bonds (SGB)

### E.1 Interest income (recurring)
- 2.5% p.a. on face value, paid semi-annually
- Taxable as "Income from Other Sources" at slab rate
- Same in both regimes
- No TDS
- *Source: laws/gold.md Section 1.3*

### E.2 Capital gains — depends on acquisition route AND exit method
| Acquisition | Exit | Tax |
|---|---|---|
| Primary RBI subscription | Held to 8-yr maturity | **Tax-exempt** (Section 47(viic)) |
| Primary RBI subscription | Pre-mature redemption (5+ yr, RBI window) | Tax-exempt |
| Secondary market | Held to 8-yr maturity | LTCG 12.5% no indexation (Budget 2026 change — *Source: laws/gold.md Section 1.3*) |
| Either | Sold on exchange | LTCG 12.5% (>12 months) or STCG slab rate (≤12 months) |

### E.3 Implication for the user
SGB primary issuance is currently paused (per `laws/gold.md`); only secondary-market acquisitions are possible. If acquiring SGBs, the acquisition-route field becomes critical for maturity tax treatment.

---

## F. Gold (non-SGB)

### F.1 Gold ETFs
- Post 1 April 2025 acquisitions: 12.5% LTCG no indexation, 12-month threshold, STCG slab — *Source: laws/gold.md Section 2.2*
- Pre 1 April 2025 acquisitions: ambiguous in some interpretations; conservative treatment is slab rate

### F.2 Gold MFs (FoF)
- Specified Mutual Fund per Section 50AA → slab rate at all times
- *Source: laws/gold.md Section 3*

### F.3 Digital gold
- Treated like physical gold: 24-month LTCG threshold, 12.5% no indexation, slab STCG
- *Source: laws/gold.md Section 4*

### F.4 Physical gold (jewellery, bullion)
- Section 112: 24-month LTCG threshold, 12.5% no indexation
- *Source: laws/gold.md Section 5.3*
- For sale: making charges sunk; sale at current 24K rate × purity factor; cost basis from purchase records

---

## G. PPF, EPF, VPF, NPS, SCSS

### G.1 PPF
- All withdrawals tax-free (EEE per laws/ppf.md Section 6)
- Loans against PPF are not taxable events (interest paid back to your own account)
- *Source: laws/ppf.md Section 5, Section 6*

### G.2 EPF / VPF
- Withdrawal after 5 yrs continuous service: tax-free
- Withdrawal before 5 yrs: prior 80C deductions reversed + employer contribution + interest become taxable
- *Source: laws/epf-vpf.md Section 3.3*
- Excess over ₹2.5L employee contribution per year: interest portion taxable at slab; *Source: laws/epf-vpf.md Section 3.2*

### G.3 NPS Tier 1
- Withdrawal at 60: 60% tax-free, 40% mandatory annuity (annuity income taxable at slab)
- Premature exit: 80% mandatory annuity; only 20% as lump-sum tax-free
- *Source: laws/nps.md Section 4*

### G.4 SCSS (relevant for holders age 60+)
- Interest fully taxable at slab
- 80TTB ₹50K deduction available for seniors (Old Regime)
- TDS on interest > ₹1L per FY (raised from ₹50K in Budget 2025) for seniors
- *Source: laws/scss.md Section 6*

---

## H. Fixed deposits and savings interest

### H.1 Bank FD interest
- Taxable as "Income from Other Sources" at slab rate
- TDS: 10% if interest > ₹50K/yr from one bank (₹1L for seniors); 20% if no PAN
- Cumulative FD: interest accrues but TDS deducted annually
- *Source: laws/regime-comparison.md Section 1, Section 2*

### H.2 Savings account interest
- 80TTA ₹10K deduction (non-senior) or 80TTB ₹50K (senior) — Old Regime only
- New Regime: no deduction; full interest taxable

### H.3 Large emergency-fund FDs
- For large cumulative FDs (emergency-fund-class), annual interest accrual can be material (e.g. ~₹3.25L on a ₹50L FD at 6.5%)
- Interest is taxable in the FD holder's name at slab in the FY of accrual (for cumulative FDs) or the FY of payout (for payout FDs)
- The skill surfaces this when computing the holder's tax position for any year — even though no cash has been withdrawn yet

---

## I. Crypto / VDA

### I.1 Section 115BBH
- 30% flat tax on all gains
- No setoff against losses
- 1% TDS on transactions > ₹10K
- No 80C, no exemptions, no STCG/LTCG distinction
- Same in both regimes

---

## J. Surcharge tier computation

For any computation requiring surcharge:

### J.1 Identify total income tier
From goals.md Section 2 (gross income, marginal bracket) plus the gain being computed:

| Total income | New regime surcharge | Old regime surcharge |
|---|---|---|
| ≤ ₹50L | 0% | 0% |
| > ₹50L ≤ ₹1Cr | 10% | 10% |
| > ₹1Cr ≤ ₹2Cr | 15% | 15% |
| > ₹2Cr ≤ ₹5Cr | 25% (capped) | 25% |
| > ₹5Cr | 25% (capped under new regime) | 37% |

### J.2 Equity LTCG / STCG cap
For Section 111A and 112A gains: surcharge maxes out at 15% regardless of income tier — *Source: laws/capital-gains.md Section 3.3*

### J.3 Cess
Always 4% on (tax + surcharge). Universal in both regimes.

### J.4 Worked example — equity LTCG (illustrative)
Filer on New Regime, gross income ₹20L:
- Surcharge tier: 0% (income < ₹50L)
- LTCG rate: 12.5%
- Cess: 4%
- Effective tax on ₹X taxable LTCG: 12.5% × (1 + 0%) × (1 + 4%) = 12.5% × 1.04 = 13%

For each filer in a multi-entity household, compute the surcharge tier separately based on that filer's individual income.

---

## K. Loss set-off and carry-forward

### K.1 Capital loss rules
- STCL: offsets STCG and LTCG (both from any source)
- LTCL: offsets only LTCG (any source)
- Carry forward: 8 assessment years; ITR must be filed by due date

### K.2 Within-FY ordering
- LTCL applied to LTCG before the ₹1.25L exemption is computed
- Effectively: LTCL reduces taxable LTCG below ₹1.25L threshold rather than just reducing tax above it

### K.3 Capital loss vs other heads
- Cannot offset capital losses against salary, business, or other income
- Carry-forward losses apply only against future capital gains

---

## L. Special: holding-period transition flag

Always check: how close is the holding to a tax-relevant threshold transition?

### L.1 Equity (12-month STCG → LTCG)
If first purchase is 11+ months ago: flag "X days to LTCG transition." Show both tax computations.

### L.2 Property / debt MF Regime B / gold ETF (24-month threshold, where applicable)
Same logic at 23-month mark.

### L.3 Threshold sensitivity
For any holding within 30 days of a transition, the skill includes a side-by-side STCG vs LTCG computation in the output, so the user can see the optimisation cost of acting now vs waiting.

---

## M. Practical worked example — Regular-to-Direct switch (illustrative)

Inputs (illustrative; all values hypothetical):
- Holding: an active equity MF, Regular plan (scheme_code X, hypothetical)
- First purchase per ledger: 25 days ago (1 lot, ₹1,36,500 cost basis)
- Today: <today>
- Plan: Regular
- Sub-portfolio: <holder's sub-portfolio per user-principles.md>, retirement earmark
- Holder's regime: per `user-principles.md` §7

Switch destination: same scheme, Direct plan

### Computation (helper-based)

```python
import sys; sys.path.insert(0, 'scripts')
from datetime import date
from lib.transactions import (
    load_transactions, cost_basis_per_scheme, units_per_scheme,
    latest_nav, classify_gain,
)
from lib.db import get_conn

txns = load_transactions()
SC = <scheme_code>
basis = cost_basis_per_scheme(txns)
if SC not in basis:                                             # holding not in ledger → DATA NEEDED
    raise SystemExit(f"scheme {SC} not in transactions.json — return DATA NEEDED")
cost = basis[SC]                                                # ₹1,36,500
units = units_per_scheme(txns)[SC]
with get_conn() as conn:
    _, nav = latest_nav(SC, conn)                              # ~₹46.21 (illustrative)
sale_proceeds = round(units * nav, 2)                          # ~₹1,40,000
exit_load = round(sale_proceeds * 0.01, 2)                     # ₹1,400 (1% within 1Y)
net_sale = round(sale_proceeds - exit_load, 2)                 # ₹1,38,600
gross_gain = round(net_sale - cost, 2)                         # ₹2,100

earliest_purchase = min(t["date"] for t in txns
                        if t["scheme_code"] == SC and t["units"] > 0)
gain_type = classify_gain(
    purchase_date=earliest_purchase,
    sale_date=date.today().isoformat(),
    tax_category="equity",
)
# gain_type → "STCG-equity (20%)" — holding period ~25 days
```

Apply rate (laws/equity-mf.md §2: STCG 20%; laws/capital-gains.md §3.3: surcharge cap 15% for §111A; cess 4%):

- Base tax: 20% × ₹2,100 = ₹420
- Surcharge (0% if holder's income < ₹50L; capped at 15% if higher): ₹0
- Cess (4% on tax + surcharge): ₹17
- **Total tax: ₹437**
- **Net proceeds: ₹1,38,600 − ₹437 = ₹1,38,163**

### Flags
- **Exit load window:** 11 months remaining; switching now costs ₹1,400 in load
- **Holding-period transition:** 11 months to LTCG eligibility; switching after the 12-month boundary changes STCG (20%) to LTCG (12.5% with ₹1.25L exemption)
- **Expense ratio savings:** Direct vs Regular typically ~1.0% per year. Over a long retirement horizon, expense ratio savings compound to material amounts; the immediate switch cost (load + tax = ₹1,837) is recovered in approximately 13 months of expense-ratio savings
- **Recommendation timing hint** (informational, for `/portfolio-review` to digest): wait until exit-load window closes AND LTCG eligibility for a much cleaner switch

This is exactly what `/portfolio-review` consumes when it flags a Regular-plan holding for switch consideration. The immediate output is "switching now is expensive; the math says wait." Note that every numeric input traces to a helper or a laws file — no number is invented.
