# Output format — fund-allocate

The exact structure fund-allocate uses for its allocation plan. Use verbatim.

The plan is a structured deployment recipe — wrapper-fill items first, then SIP/STP into category-shaped needs, with rationale citations and selection guidance throughout.

---

## Plan structure

```markdown
# Fund Allocation Plan — YYYY-MM-DD

**Plan ID:** ALLOC-YYYY-MM-DD-<seq>
**Source:** [salary surplus / business lump / windfall / mixed]
**Amount:** ₹X
**Cadence:** [one-time / monthly recurring / quarterly / mixed]
**Default sub-portfolio routing:** per `user-principles.md` §6

---

## Discovery snapshot

From `scripts/discover.py`:
- NAV freshness: [FRESH/STALE], latest_nav_date YYYY-MM-DD
- Ledger: txn_count N, latest_txn_date YYYY-MM-DD
- fund_quality.json coverage for categories this plan needs: [per category]
- Drawdown gate (§6.4) per sub-portfolio: [weighted_dd %, block_at_minus_20pct true/false]
- Sub-portfolio totals (with sleeve breakdown): [from §10]

---

## 1. Current state summary

### Sub-portfolio allocations vs targets

Targets per `user-principles.md` §3 (with glide-path waypoint applicable today per §4).

| Sub-portfolio | Current Eq/Debt/Gold/Hybrid % | Target % (today's waypoint) | Drift |
|---|---|---|---|
| <name 1> | <fill from discover.py §10> | <fill from user-principles.md §3-4> | <diff> |
| <name 2> | ... | ... | ... |

### Wrapper-fill capacity (current FY)

| Wrapper | Holder | Annual cap | YTD used | Remaining |
|---|---|---|---|---|
| PPF | <holder> | ₹1,50,000 (per `laws/ppf.md`) | <from portfolio.md> | <remaining> |
| VPF | <holder> | ₹2,50,000 employee threshold (per `laws/epf-vpf.md`) | <mandatory EPF projected> | <headroom> |
| NPS 80CCD(1B) | <holder> | ₹50,000 | <if Old Regime per user-principles.md §7> | <remaining or N/A> |
| NPS 80CCD(2) | <holder> employer route | 14% × (Basic + DA) | <if confirmed available per user-principles.md §8> | <pending or remaining> |
| SCSS | <holder, if age ≥ 60> | ₹30L lifetime (per `laws/scss.md`) | <existing balance> | <remaining or future> |

---

## 2. Deployment sequence

Walked in priority order per `principles.md` §4.1 with overrides from `user-principles.md` §9.

### Item N — <Wrapper-fill or SIP item>
- **Amount this FY:** ₹X
- **Cadence:** [lump-on-date / monthly ₹Y / quarterly ₹Z]
- **Sub-portfolio:** per `user-principles.md` §6 routing
- **Goal earmark:** per `user-principles.md` §5
- **Rationale:** `principles.md` §X.Y, `user-principles.md` §Z
- **Tax cost:** [₹0 / specifics from `/tax-check`]
- **Action required:** [open account, submit HR rate change, etc.]
- **Confirmation needed:** [conditional / clean wrapper-fill]

[Repeat per item in the sequence]

---

## 3. Residual after wrapper-fill

**Annual wrapper-fill total (Year 1):** ₹<sum>
**Per-month equivalent:** ~₹<avg>

**Monthly surplus / lump amount:** ₹<input>
**Residual:** ₹<remaining for SIPs>

> **Note on routing:** [if wrapper fills route across sub-portfolios, note the implicit routing share here]

---

## 4. SIP / STP allocation (residual ₹Y/month or one-time)

Apply `user-principles.md` §3 (sleeve targets) and §5 (goal-bucket overlay). Drift correction toward target is the dominant signal.

### 4.1 Routing decision

Per `user-principles.md` §6, the default routing for this inflow source goes to <sub-portfolio>. [If over-ride applies, note it here with rationale.]

### 4.2 <Sub-portfolio name> SIP allocation (₹X/month)

Target per `user-principles.md` §3 + §4 waypoint: <equity>%/<debt>%/<gold>% equity/debt/gold within this sub-portfolio.

#### <Sub-portfolio> equity sleeve: ₹X/month
Within equity, distribute per `principles.md` §2.4 SAA midpoints + TAA bands (with overrides from `user-principles.md`).

| Category-shaped need | Amount/month | Sub-portfolio | Goal earmark | Rationale |
|---|---|---|---|---|
| Large-cap index fund (Nifty 50) | ₹X | <name> | <goal> | `principles.md` §2.4 — index core slot |
| Nifty Next 50 index fund | ₹X | <name> | <goal> | §2.4 — core extension |
| Flexi-cap active fund | ₹X | <name> | <goal> | §2.4 — active satellite |
| Passive midcap index | ₹X | <name> | <goal> | §2.4 — passive midcap |
| Passive smallcap index | ₹X | <name> | <goal> | §2.4 — passive smallcap |
| International index FoF | ₹X | <name> | <goal> | §2.4 — broad-passive intl (or absorbed into flexicap if capacity closed) |

> **Selection:** for each row above, run `filter_candidates()` per Step 7 of SKILL.md (with the per-category defaults in SKILL.md's filter table). Present the ranked top-3 to top-5 to the user as a chooseable list. See Section 5 for the table format.

#### <Sub-portfolio> debt sleeve: ₹X/month
| Category-shaped need | Amount/month | Sub-portfolio | Goal earmark | Rationale |
|---|---|---|---|---|
| Short-duration debt fund (Direct) | ₹X | <name> | <goal> | Liquidity within debt sleeve; primary debt is via PPF/VPF wrappers |

#### <Sub-portfolio> gold sleeve: ₹X/month
| Category-shaped need | Amount/month | Sub-portfolio | Goal earmark | Rationale |
|---|---|---|---|---|
| Gold ETF (Direct) [or Gold MF if no demat] | ₹X | <name> | <goal> | `principles.md` §2.6 |

### 4.3 [Repeat per sub-portfolio]

### 4.4 Allocation summary

| Item | Amount/month (or one-time) | Sub-portfolio | Goal earmark |
|---|---|---|---|
| PPF <holder> (apportioned) | ₹X | <name> | <goal> |
| VPF <holder> | ₹X | <name> | <goal> |
| NPS <holder> (conditional) | ₹X | <name> | <goal> |
| <Sub-portfolio> equity SIPs | ₹X | <name> | <goal> |
| <Sub-portfolio> debt SIP | ₹X | <name> | <goal> |
| <Sub-portfolio> gold SIP | ₹X | <name> | <goal> |
| **TOTAL** | **₹X** | | |

---

## 5. Ranked candidates per item

For each SIP/STP row in Section 4, the skill ran `filter_candidates()` (per SKILL.md Step 7) over the researched universe in `data/fund_quality.json`, intersected with the `schemes` table. Where the relative-performance signal is meaningful (active funds → alpha; index funds → tracking error), it also called `alpha_vs_benchmark()` and `tracking_error()` over a 3Y window against the category benchmark from `discover_benchmark_for_category()`.

Each row below cites the **mode** (rich-data / limited-universe / sparse-data — see SKILL.md), the filter parameters that produced the ranking, and the data quality flags.

### 5.1 Item-level table (one block per SIP/STP item in Section 4)

#### Item — <Sub-portfolio> / <Slot> (₹X/month)

**Mode:** rich-data | limited-universe | sparse-data
**Filter spec:** `category="..."`, `plan="Direct"`, `min_aum_crore=...`, `max_ter=...`, `min_vintage_years=...`, `rank_by="..."`, `limit=5`
**Benchmark used:** [scheme_code via `discover_benchmark_for_category` / explicit / None]
**Universe size:** N candidates passed filter

| Rank | scheme_code | Scheme name | TER | AUM (₹Cr) | Manager | Mgr tenure | Vintage | 3Y return | Alpha or TE (3Y) | Quality |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | <code> | <name> | <ter>% | <aum> | <manager> | <years> | <years> | <ret>% | <alpha or te>% | <%> |
| 2 | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 3 | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

**Stale flags:** entries with `last_verified` >90 days are tagged ⚠️.
**Recommended pick (top of rank):** scheme_code X — call out in plan.

**For passive picks:** rationale must include rupee-cost-of-TER over the holding period (not just bps). Use the cost-compounding formula:
```
TER drag (₹) ≈ TER × time_weighted_average_balance × years
```
Quote the rupee figure explicitly.

#### Item — [Sparse-data example]

**Mode:** *sparse-data — pending `/fund-research` run*
**Reason:** `fund_quality.json` has 0 entries in `<category>`.
**Action:** invoke `/fund-research category="<category>" plan="Direct"` before committing this SIP.
**Selection-pending flag:** carries forward to next session.

#### Item — [Repeat per remaining category]

(One block per row in Section 4. Sparse-data items show the `/fund-research` invocation rather than a candidate table.)

### 5.2 Universal filter floors (applied per category)

Per SKILL.md's filter table:

| Category | min_aum_crore | max_ter | min_vintage_years | min_manager_tenure_years | rank_by |
|---|---|---|---|---|---|
| Equity Scheme - Large Cap Fund (active) | 1,000 | 1.20 | 3 | 3 | return_3y |
| Equity Scheme - Mid Cap Fund | 500 | 1.50 | 5 | 3 | return_3y |
| Equity Scheme - Small Cap Fund | 500 | 1.80 | 5 | 3 | return_3y |
| Equity Scheme - Flexi Cap Fund | 1,000 | 1.20 | 5 | 3 | return_3y |
| Other Scheme - Index Funds (any) | 500 | 0.50 | 2 | (n/a) | ter (asc) |
| Debt Scheme (any) | 500 | 0.80 | 3 | 3 | return_3y |
| Hybrid Scheme - Multi Asset | 500 | 1.50 | 3 | 3 | return_3y |
| Other Scheme - Gold ETF / FoF | 500 | 0.40 | 2 | (n/a) | ter (asc) |
| Hybrid Scheme - Arbitrage Fund | 500 | 0.50 | 3 | 3 | ter (asc) + exit-load profile |

**Auto-loosening:** if `filter_candidates()` returns <3 hits at the strict defaults, the skill loosens by 20% on each numeric threshold and re-runs once. Surface the loosening in the row.

### 5.3 Mode-resolution recap

- **Rich-data (≥3 candidates):** present the ranked list above; user picks one (or splits across two for diversification).
- **Limited-universe (1–2 candidates):** present what's there, flag explicitly, recommend `/fund-research` to expand before next allocation cycle.
- **Sparse-data (0 candidates):** invoke `/fund-research` now; defer this row's selection if the user prefers, recording it as `selection-pending` with a follow-up date.

The skill **does not** invent recommendations from training-data priors. If a category is sparse and the user defers research, the row carries a `selection-pending` flag forward.

---

## 6. Conditional and pending items

| Item | Pending on | Follow-up |
|---|---|---|
| <Conditional item> | <condition or user action> | <date or trigger> |

---

## 7. STP schedule for any lump deployments

Not applicable to a monthly-recurring plan. STP applies when a one-time lump (>STP threshold from `user-principles.md` §11; default ₹3L for equity) arrives.

When a lump arrives:
- Walk Items 1-7 of the deployment sequence; top up wrapper-fill to annual caps if not yet done
- Residual: STP into under-allocated equity sleeve over 3-6 months
- Re-run fund-allocate when each lump arrives

---

## 8. Tax implications (mandatory section)

Every plan ends with a tax-implications section. Cover all four buckets even if some are zero — explicit "no tax event" is part of the audit trail.

### 8.1 Entry events (typically all ₹0)

For each leg of the plan, state whether the action triggers a tax event today. Purchases, parking buys, and STP setup are entries → ₹0. Switching from existing holdings or redeeming triggers tax — invoke `/tax-check` for those legs.

### 8.2 Parking-vehicle carry and tax (when STP is used)

For STP plans with arbitrage / liquid / savings parking, compute and surface:
- Average balance over the STP period (declining balance, midpoint approximation)
- Gross yield over period = avg_balance × annualised_yield × period_years
- Tax classification:
  - Arbitrage funds: equity-taxed per Section 50AA's 2024 rewrite. STCG @ 20% if held <12m; LTCG @ 12.5% above ₹1.25L exemption if held >12m.
  - Liquid / overnight / short-duration debt funds: Specified MF per Section 50AA → slab-rate regardless of holding period.
  - Savings account interest: slab-rate; Section 80TTA ₹10K deduction Old-Regime-only.
- Net carry post-tax
- Comparison to the alternative parking vehicle (so the user sees the cost of substitution)

### 8.3 Forward holding-period clocks per leg (for future redemption planning)

For each destination scheme, state:
- Tax classification (equity-oriented MF / Specified MF / hybrid-equity / debt / gold ETF / gold MF)
- LTCG threshold (12 months for equity / equity-hybrid / Gold ETF; 24 months for Gold MF; 24 months for Specified MF debt)
- Effective tax rate (12.5% LTCG above ₹1.25L for equity; slab for Specified MF; etc.)
- The specific date each STP tranche becomes LTCG-eligible

### 8.4 LTCG harvesting calendar (forward-look)

For each FY in which a tranche becomes LTCG-eligible, note the harvesting opportunity. Per `principles.md` §5, harvest up to ₹1.25L LTCG per FY per filer (Q4 timing).

### 8.5 Net household tax footprint

A summary table of total tax during the deployment phase:

| Item | Tax |
|---|---|
| Entry purchases (all) | ₹0 |
| Parking carry STCG (if STP used) | ~₹X |
| Equity destinations (no exits this window) | ₹0 |
| Gold (no exit this window) | ₹0 |
| **Total tax during deployment phase** | **~₹X** |

Compare against the lump-without-parking alternative so the user sees the cost-benefit of the smoothing structure.

---

## 9. Decisions to log

After user response:

| Plan ID | Item | User response | Follow-up |
|---|---|---|---|
| ALLOC-YYYY-MM-DD-001 | <item> | [Acted: <what> on YYYY-MM-DD / Deferred / Rejected] | None / specific date |

All entries appended to `decisions-log.md` with full detail.

---

## 10. Action items summary (what to do this week)

**This week:**
- [Specific action items]

**Next 1-2 weeks:**
- [Selection / setup items]

**Then:**
- Report back chosen schemes via the "Report back when executed" block (Section 11)
- First `/portfolio-review` after SIPs are live: 4-6 weeks out

**Pending:**
- [Conditional items]

---

## 11. Report back when executed (copy-paste template)

=== Report back when executed (paste back to me, edit amount/date if different) ===
Bought ₹<amount> <scheme name> on <YYYY-MM-DD>           # one line per one-off purchase
Registered SIP: ₹<amount>/month <scheme name> from <YYYY-MM-DD>   # one line per SIP
Registered STP: ₹<amount>/month <source> → <dest> from <YYYY-MM-DD>  # one line per STP
PPF deposit ₹<amount> to <holder> PPF on <YYYY-MM-DD>     # govt-scheme line

---

**Re-run fund-allocate when:**
- A new lump arrives (re-walk for that deployment)
- Material income change (>20% up/down)
- Annual review (Q4, alongside regime decision)
- Goals re-grill (any major life event)
- HR/employer response on a conditional item (e.g. NPS 80CCD(2))
```

---

## decisions-log.md entry format

Each fund-allocate run appends entries to `decisions-log.md` under the same convention as portfolio-review:

```markdown
### YYYY-MM-DD — Fund Allocation Plan

**Plan ID:** ALLOC-YYYY-MM-DD
**Source:** [salary surplus / business lump / windfall / mixed]
**Amount:** ₹X
**Cadence:** [...]

[Per item, log:]

#### ALLOC-YYYY-MM-DD-001 — <headline>

**Item type:** Wrapper-fill / SIP / STP
**Amount:** ₹X
**Sub-portfolio / Goal earmark:** <name> / <goal>
**Principle applied:** `principles.md` §X.Y, `user-principles.md` §Z
**Tax-check result:** [excerpt or N/A]

**User response:** [Acted: <what> on YYYY-MM-DD / Deferred / Rejected]
**Follow-up:** [date / None]
**Status:** [Open / Closed]

[Repeat per item]

[At the end of the plan entry:]

**Plan summary:**
- Total allocated this plan: ₹X
- Wrapper-fill commitments: [list]
- SIPs designed: [count by sub-portfolio]
- Selection pending: [count]
- Conditional items: [count]
```

---

## Output format conventions

- All currency: ₹ with commas (₹1,50,000)
- Dates: ISO (YYYY-MM-DD)
- Citations: `principles.md §X.Y` / `user-principles.md §X` / `laws/<file>.md §A.B`
- Plan IDs: `ALLOC-YYYY-MM-DD-<seq>`
- Sub-portfolio names: from `user-principles.md` §2 — never hardcoded
- Sleeve targets: from `user-principles.md` §3 — never hardcoded
- Routing decisions: explicit — state the default and any over-ride with reason
- Sub-portfolio table form: equity/debt/gold/hybrid in that order
- Action items at the end: clear, dated, specific
