# Output format — tax-check

The exact structure tax-check returns. Both for direct user invocations and when another skill calls it.

The output is a single Markdown block. Whether displayed to user or consumed by another skill, the structure is identical so parsing is predictable.

---

## Structure

```markdown
## Tax-check report
**Generated:** YYYY-MM-DD
**Type:** [full-redemption | partial-redemption | switch | regular-to-direct | ltcg-harvesting-check | hypothetical]
**Calling context:** [direct user call | invoked by portfolio-review | invoked by fund-allocate]

---

### Transaction described
[1-2 sentence description of what's being computed]

### Holding(s) involved
| # | Scheme / Instrument | Plan | Sub-portfolio | Cost basis (₹) | First purchase | Current value (₹) | Holding period |
|---|---|---|---|---|---|---|---|
| 1 | <name> | <D/R> | <user/father/joint> | <cost> | <date> | <value or UNKNOWN> | <X months> |

### User context applied
- **Tax regime:** <Old / New> (per `goals.md` Section 2)
- **Marginal tax bracket:** __% + applicable surcharge __% + cess 4%
- **FY YTD realised equity LTCG used:** ₹<value> of ₹1.25L exempt threshold (only relevant for equity LTCG)
- **Sub-portfolio attribution for the holder:** <user/father/joint> — affects which entity's tax position applies if filings are separate

### Rule path
<For each tax fact applied, one bullet:>
- **<Fact>:** <value> — *Source: laws/<file>.md Section <X.Y>*

Example:
- **Holding period threshold for equity LTCG:** > 12 months — *Source: laws/equity-mf.md Section 1*
- **LTCG rate:** 12.5% no indexation — *Source: laws/capital-gains.md Section 2.2*
- **Annual equity LTCG exemption:** ₹1.25 lakh — *Source: laws/equity-mf.md Section 3*
- **Surcharge cap on equity LTCG/STCG:** 15% maximum — *Source: laws/capital-gains.md Section 3.3*

### Computation

**Sale proceeds:** ₹<value>
**Less: exit load** (<rate>%): ₹<value>
**Net sale proceeds:** ₹<value>

**Cost basis:** ₹<value>
**Gross gain:** ₹<sale - cost> = <type: STCG / LTCG / slab-rate>

**FY YTD exemption already used:** ₹<value>
**Available exemption headroom:** ₹<1.25L - YTD>
**Exemption applied:** min(gain, headroom) = ₹<value>

**Taxable gain:** ₹<gain - exemption>

**Tax:**
- Base rate: <rate>% × ₹<taxable> = ₹<base tax>
- Surcharge (<rate>%): ₹<surcharge>
- Cess (4%): ₹<cess>
- **Total tax: ₹<total>**

**Net proceeds (after exit load and tax):** ₹<sale - exit-load - total-tax>

### Flags

[Each flag is a single line. Examples:]

- **Data limitation:** Holding not in `data/transactions.json` ledger; FIFO precision unavailable for partial redemption. <Normal for non-MF assets (FDs, PPF, real estate, direct equity, physical gold); should not happen for MFs once the ledger is populated by `/portfolio-grill`.>
- **Rule freshness:** laws/equity-mf.md last verified Budget 2026 — current.
- **Holding-period transition opportunity:** This holding crosses 12-month threshold in 23 days; deferring redemption to <date> changes tax from ₹<STCG amount> to ₹<LTCG amount>, saving ₹<diff>.
- **Exit load window:** Holding is <X months> old; exit load of <Y%> applies until <date>.
- **Conservative assumption:** Tax classification of <scheme> is UNKNOWN per portfolio.md; computed under Specified Mutual Fund (slab rate). If equity-oriented (≥65% domestic equity), tax falls to <12.5% LTCG rate> = ₹<lower amount>. Verify from scheme factsheet.
- **Sub-portfolio implication:** Redemption from <father> sub-portfolio; net proceeds reduce that sub-portfolio's allocation by ₹<value>; reinvestment routing is a separate decision (not within tax-check scope).

### Not-for-decision caveat

This report computes the tax cost. Whether to proceed is for the user / calling skill to decide. If the calling skill is `portfolio-review` or `fund-allocate`, that skill will integrate this with allocation, principles, and rebalancing logic before recommending action.
```

---

## Variant: DATA NEEDED output

When portfolio.md doesn't have enough information to compute (most commonly partial-redemption FIFO):

```markdown
## Tax-check report — DATA NEEDED
**Generated:** YYYY-MM-DD
**Type:** <type>

### Transaction described
[1-2 sentence description]

### Why this can't be computed yet
[Explanation of the data gap.]

Example: "Partial redemption requires FIFO lot-level cost basis. Holding is not in `data/transactions.json` (e.g., a non-MF asset like physical gold or a direct-equity lot, which the ledger does not cover). The per-folio summary in portfolio.md is sufficient for full redemption but not for partial."

### What data is needed
1. **<specific data item>** — fetch from <specific source>
   - For an MF holding missing from the ledger: fetch the CAS (CAMS or KFintech) transaction-level history and append rows to `data/transactions.json` via `python scripts/log_transaction.py` (or `scripts/backfill_units.py` for a wave). Once in the ledger, `transactions.consume_fifo()` makes the partial-redemption computation precise.
   - For direct equity / physical gold / real estate: fetch from broker (Zerodha Console > Reports > Tax P&L) or purchase records.
2. **<another item>** if applicable

### Workaround (deterministic rule)
If full transaction history is unavailable but the user wants to proceed with a rule-based partial redemption, here's the deterministic option:
- **"Sell oldest <X%> of units"** — uses the per-folio first-purchase date as a proxy. Conservative; may overstate STCG portion if the SIP has been running for a while. Acceptable for ballpark; not for precise tax planning.

### What you can do with current data
- **Full redemption** — can be computed accurately with current portfolio.md.
- **Hypothetical estimates** — can be computed under stated assumptions (e.g. "assume 50/50 STCG/LTCG split"). Skill flags as estimate, not exact.
```

---

## Variant: LTCG harvesting check output

Specific format for the LTCG harvesting use case:

```markdown
## Tax-check report — LTCG harvesting check
**Generated:** YYYY-MM-DD
**FY:** <FY YYYY-YY>

### Available headroom
- **Annual equity LTCG exemption:** ₹1,25,000
- **FY YTD realised equity LTCG:** ₹<value>
- **Headroom remaining:** ₹<value>

### Eligible holdings
[For each equity holding with > 12 months holding period and unrealised LTCG:]

| # | Scheme | Plan | Sub-portfolio | Cost basis | Current value | Unrealised LTCG | Sell amount to use exact ₹<headroom> |
|---|---|---|---|---|---|---|---|

### Suggested harvesting plan
[Pick the holding(s) where harvesting is cleanest — usually the one with lowest exit load risk, no SIP currently active, etc.]

[Per holding: sell ₹<X> worth (≈ <Y> units), realises ₹<gain>, tax = ₹0 (within exemption), rebuy at current NAV resets cost basis upward by ₹<gain>.]

### Flags
- **Rebuy considerations:** Rebuy must be at market price (no fictitious price). Indian tax law does not have a 30-day wash-sale rule, but bona fide trades are required.
- **Switch is also a redemption:** If using the switch facility (intra-AMC), the same FIFO mechanics apply.
- **Bid-ask / settlement:** For ETFs, brief market exposure during T+1; for MFs, NAV exposure between sale and rebuy.
- **Data limitation:** [As applicable, e.g. cost basis for harvested portion is computed using weighted-average; transaction-level FIFO would give precise figures]
- **Goals.md context:** User's tax priority is <X>/10 per goals.md Section 7. <If 3 or below, add: "User has indicated low tax priority; harvesting is recommended only when it's genuinely free (no exit load, no churn cost). Harvesting may not be worth the operational effort.">

### Net effect of executing
- Tax owed: ₹0 (within exemption)
- Future LTCG liability reduced by: ₹<rebuy reset>
- Operational steps: <number> redemptions + <number> repurchases
```

---

## Variant: Regular-to-Direct switch output

For the recurring "should I switch this Regular plan holding to Direct?" question:

```markdown
## Tax-check report — Regular-to-Direct switch
**Generated:** YYYY-MM-DD

### Transaction described
Switch from <Regular plan scheme> to <equivalent Direct plan scheme>.

[Same redemption + new purchase output as full redemption, with the holding-period reset noted explicitly.]

### Specific to plan switch
- **Mechanically:** Redemption of Regular + fresh purchase of Direct. No "switch facility" treats this as tax-neutral. It is a tax event.
- **Holding-period reset:** Direct plan starts a new 12-month / 24-month clock. Cost basis is the redemption-day NAV.
- **Expense ratio savings:** Estimated ~<value>% per year, compounding. For a <holding-period> horizon: ~₹<approx benefit>.
- **Break-even time:** Tax cost ₹<X> recovered by expense ratio savings in approximately <Y> years.

### Flags
- **Exit load:** Equity MF held <X months>; exit load of <Y%> applies until <date>. Switching now costs an additional ₹<value>.
- **Holding-period transition:** Currently STCG (20%); switching now realises STCG. Waiting until <date> would shift to LTCG (12.5%, with ₹1.25L exemption potentially available).
- **Recommendation timing hint** (informational, not advice): Wait for exit-load window to close AND LTCG eligibility AND ideally use within FY's ₹1.25L exemption for a cleaner switch.
```

---

## When the calling skill consumes the output

Both `portfolio-review` and `fund-allocate` will:
1. Receive the tax-check report as a structured block
2. Extract: net proceeds, total tax, flags
3. Fold into their recommendation: e.g. "Switch X to Y will cost ₹T in tax now; principle 1.7 requires this be acknowledged. Trade-off: ₹X annual savings vs ₹T one-time cost; break-even <years>."
4. Display the recommendation to the user with the underlying tax-check report available on request

The user-facing recommendation thus has the math underneath it traceable. This serves the goals.md preference for math/probability-based reasoning.
