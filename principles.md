# Investment Principles — Universal Framework

last_updated: 2026-05-30
last_verified_against_budget: 2026
review_due: annually, or after material change to the framework

> **What this file is.** The investment agent's stable prior — the universal framework it reasons *from* when reviewing a portfolio, allocating fresh money, or evaluating any new opportunity. Indian-context aware. Not rules. Principles, with rationale, with named conditions for deviation.
>
> Read alongside three other files:
> - `goals.md` — *your* personal situation (income, dependents, goals, risk profile)
> - `user-principles.md` — *your* structural choices (sub-portfolio targets, glide paths, regime, routing)
> - `laws/` — current Indian tax and scheme rules
>
> **What this file is not.** A market view. A list of recommended schemes. Your personal allocation targets. Anything that goes stale every quarter. If a sentence here would need to change after a Budget speech, it belongs in `laws/`; if it changes based on who you are or what you want, it belongs in `goals.md` or `user-principles.md`.

---

## How to read this document

Each section states a principle, the rationale, and — where useful — when to deviate. The agent applies these principles to *your* situation as captured in `goals.md` and `user-principles.md`, using current rules from `laws/` and live data from `data/market.db`.

When two principles conflict in a specific situation, the agent names the conflict explicitly and explains the trade-off rather than silently picking one.

---

## 1. Foundational philosophy

### 1.1 Time in market beats timing the market
Long-run wealth creation comes from compounding, not from being clever about entry and exit points. Professional managers fail to time markets reliably; retail investors fail systematically. The agent does not recommend "wait for a dip" or "exit before the correction." It allocates available capital to its target home immediately or via short STPs, never holds capital in cash waiting for a better moment.

**Deviate when:** capital is staged for known future deployment (e.g. a property purchase). Park in liquid debt or arbitrage. This is goal alignment, not market timing.

### 1.2 Goal-based bucketing, not aggregate portfolio thinking
Goals at different horizons need different allocation logic — equity-heavy for long, glide-path for medium, capital-preserving for short. The agent reports portfolio status *per bucket*, not as a single aggregate %, because the aggregate hides the picture. Locked emergency funds, for example, distort any aggregate equity % — they show as conservatively allocated when the *investable* bucket may in fact be equity-heavy.

### 1.3 Cost is the most reliable predictor of future returns
Lower expense ratios, lower transaction costs, lower tax drag — all are deterministic positive impacts on net return. Past returns are noisy; cost is signal. The agent prefers Direct plans, prefers index funds where active doesn't reliably beat post-fee, and keeps fund switches rare.

### 1.4 Diversification across uncorrelated assets, not across many similar funds
Holding 12 large-cap funds is one bet, not 12. True diversification is across asset classes (equity / debt / gold), within equity across market caps and geography, and within debt across duration and credit. The agent will not recommend adding a fund that materially overlaps holdings with an existing one.

### 1.5 Discipline > sophistication
Boring works. Regular SIPs, threshold-based rebalancing, no churn. Principles are designed to need *less* attention over time, not more. The agent's job is to reduce decision fatigue, not multiply it.

### 1.6 Tax efficiency is a tailwind, not a strategy
The agent does not optimise primarily for tax — it picks the right investment for the goal, then prefers the more tax-efficient wrapper if the choice is neutral or near-neutral on other dimensions. The agent never sacrifices return, liquidity, or fit for tax savings alone.

**Deviate when:** an LTCG harvesting opportunity is genuinely free (within annual exempt threshold, no other cost). Capture it.

### 1.7 Rationale is mandatory output
Every recommendation comes with: (a) which principle(s) it applies, (b) the alternatives considered, (c) what trade-off was made, (d) what would change the recommendation. This keeps the agent honest *and* educates the user so confidence over time becomes earned rather than borrowed.

### 1.8 Match horizon to actual capital, not entity age
A common error is conflating an investor's age with their capital's effective horizon. A 60-year-old whose pension covers monthly expenses has a 20+ year compounding horizon on the corpus — not a withdrawal window. A 30-year-old saving for a 2-year property goal has a 2-year horizon for *that capital*, not 30. Allocations should reflect the actual time horizon of each pool of capital, not the entity's age.

This shapes downstream choices:
- Long-horizon capital tilts equity-dominant regardless of holder's age
- Drawdowns are noise on long timescales, not capital events to react to (reinforces 2.7, 6.4)
- Rebalancing is patient — flow-based where possible (6.3), threshold-based not calendar-based (6.1)
- Goal-bucket glide paths (when used) follow the goal's date, not the holder's birthday

The user captures the actual horizon of each capital pool in `user-principles.md`. The agent reads that, not the holder's age, when setting sleeve targets.

---

## 2. Asset allocation framework

### 2.1 Single portfolio vs sub-portfolios — pick one architecture
Two valid structural choices. The user picks one in `user-principles.md`.

**Option A — Single portfolio.** One investor (or pooled household) with one allocation target. Simplest. All inflows and holdings sit under one roof; one set of sleeve targets; one glide path.

**Option B — Sub-portfolios.** Multi-entity household where capital pools have materially different effective horizons (different ages, different income sources, different goals). Each sub-portfolio gets its own allocation, glide path, and routing rules. The agent reports each sub-portfolio's status separately; aggregate is reported but never optimised against.

Option B is justified only when horizons genuinely differ enough to warrant the operational complexity. A household where everyone shares the same goals and horizons is better served by Option A.

When Option B is used, any locked or constrained capital (e.g. emergency fund tied to family use) typically sits *outside* the sub-portfolios as a separate constraint, with its own allocation rationale.

### 2.2 Sleeve targets per sub-portfolio
**Captured in `user-principles.md`.** Each sub-portfolio (or the single portfolio) carries:
- Equity / debt / gold percentages (other categories — e.g. international, REITs — added if relevant)
- Drift bands (default ±5pp; flag in `user-principles.md` if different)
- Optional waypoints for glide paths (see §2.3)

The agent does not hardcode any specific target. It reads them at run-time and applies the framework to whatever the user has captured.

### 2.3 Glide paths
A glide path is a series of waypoint allocations dated to a specific year. Used when the user wants the equity allocation to shift (typically lower) as a goal date approaches.

Glide paths follow the goal's date, not the holder's age (§1.8). A 2033 property goal at 7-year horizon glides differently from a 2051 retirement goal at 26-year horizon, even for the same holder.

Captured in `user-principles.md` per sub-portfolio (and per goal-bucket if the user has earmarked goals to specific allocations).

### 2.4 Within-equity composition — SAA midpoints with TAA bands
The within-equity composition is typically identical across sub-portfolios (per §1.8 — long-horizon capital has the same diversification needs regardless of holder). Sub-portfolio differences live at the *sleeve* level (equity/debt/gold proportions), not within equity.

**Default Strategic Asset Allocation (SAA) for an equity-heavy long-horizon investor.** Override in `user-principles.md` if your profile differs.

| Slot | SAA midpoint | TAA band | Vehicle | Rationale |
|---|---|---|---|---|
| Nifty 50 (index core) | 48% | 43-53% | Other Scheme - Index Funds (Nifty 50), Direct, low TER | Top 50 by mcap; broad large-cap exposure; lowest-TER passive trackers |
| Nifty Next 50 (core extension) | 12% | 10-15% | Other Scheme - Index Funds (NN50), Direct, low TER | Rank 51-100; structural ~2-3% alpha vs Nifty 50 over long windows from graduation pipeline |
| Flexicap (active satellite) | 22% | 18-26% | Equity Scheme - Flexi Cap Fund, Direct | Style-flex + manager-skill alpha; can substitute international when overseas FoFs closed |
| Passive midcap | 7% | 5-9% | Other Scheme - Index Funds (Midcap 150), Direct | Cap segment 101-250; active midcap AUM-bloat real (SPIVA YE2025: ~82% underperform 10y) |
| Passive smallcap | 4% | 3-6% | Other Scheme - Index Funds (Smallcap 250), Direct | Cap segment 251-500; modest weight reflects ~1.5-1.8× volatility vs large-cap |
| International (broad-passive) | 7% | 5-12% | Other Scheme - FoF Overseas, Direct (S&P 500 / Developed World) | Currency hedge + decorrelation; capacity-dependent |
| **Total** | **100%** | | | |

Combined index core (Nifty 50 + NN50) = 60% — at the lower edge of historical 60-75% core. Combined satellite (flexicap + mid + small + intl) = 40% — at the upper edge of 25-40% satellite. Bias toward satellite reflects long-horizon framing (§1.8).

#### International substitution rule (capacity-dependent)

When broad-passive international FoFs are closed for fresh subscriptions (RBI overseas-investment cap binding), the international SAA absorbs into flexicap (Parag Parikh Flexi Cap or equivalent with global sleeve) as the closest available substitute.

When capacity reopens, redeploy from flexicap → broad-passive intl FoF. **Do NOT silently substitute Nasdaq 100 FoFs for the international slot** — Nasdaq 100 is ~50% tech / 40-45% top 7 names, a concentration bet not a diversification leg. Nasdaq 100 deployment requires explicit user opt-in framed as "tech tilt, not international diversification."

#### Avoid list

- **Sectoral / thematic funds** — chase recent performance; chase-the-fad fragility
- **Smart-beta** (single-factor: momentum / low-vol / quality / value) — unless the user understands the specific bet
- **ESG-thematic** — unless the user has stated values pointing there
- **Active large-cap funds** — empirically dominated by Nifty 50 index for retail per SPIVA YE2025 (~73% underperform 10y net of fees). Existing legacy holdings may persist until consolidation window.

#### TAA bands — what they're for, what they're not

The bands are **drift accommodation between annual rebalances**, not active timing budgets.

Acceptable signals at annual review:
- SPIVA refresh (active vs passive underperformance per category)
- AUM-bloat metrics (e.g. median active mid/small fund AUM > ₹15K Cr → tilt away from active)
- Capacity availability (international FoF reopenings)
- Manager continuity changes (trigger re-research, not strategy change)
- TER moves (>10 bps shift) → trigger fund-pick re-evaluation within slot

**Unacceptable signals** (per §1.1, §9.5):
- Macro forecasts (recession / rate-cycle predictions)
- Sectoral rotation calls
- Valuation timing within equity styles (large vs mid vs small relative PE)

If actual sleeve weights drift outside their TAA bands due to market movements, rebalance via new flows first (per §6.3) — do NOT trade existing holdings unless drift exceeds the band by >2pp AND new flows can't correct within 6 months.

### 2.5 Debt sleeve framework — favour sovereign and EEE wrappers in higher brackets

Post Section 50AA (effective 1-Apr-2023; scope refined 1-Apr-2026 to debt-oriented schemes only), debt mutual funds in the 30% bracket are materially less attractive — at slab rate, a 7.5% gross debt MF nets ~5.2%, dominated post-tax by tax-free or equity-tax-treated alternatives.

**Default priority ladder for long-term debt allocation (30% bracket):**

1. **PPF** — ₹1.5L/year per holder cap. Current rate per `laws/ppf.md`. Tax-free under any regime; 80C deduction only under Old Regime. Lock 15 years with partial liquidity from year 7.

2. **VPF (salaried only)** — voluntary EPF top-up; same EEE treatment as EPF up to the ₹2.5L employee-contribution threshold for fully tax-free interest. Lower friction than PPF (auto-deducted). Tracks EPF rate.

3. **SCSS (age 60+ only)** — ₹30L cap at current rate per `laws/scss.md`. Quarterly payout, slab-taxable. Becomes a cornerstone for retiree debt sleeves.

4. **RBI Floating Rate Savings Bonds (FRSB)** — current rate per `laws/` (NSC + 0.35% spread). Slab-taxable. Sovereign credit, 7-year lock with 50% pre-mature withdrawal penalty for under-60. Beats taxable debt MFs on yield AND credit.

5. **Secondary-market tax-free PSU bonds** (NHAI / REC / IRFC / PFC) — no fresh issuance since FY16; secondary YTMs vary. Liquidity thin (30-50 bps bid-ask). Opportunistic.

6. **Direct G-Secs / SDLs via RBI Retail Direct** — slab-taxable; useful after PPF/VPF/SCSS/FRSB are filled, primarily for duration/cash-flow matching.

7. **Short / banking-PSU debt MFs — liquidity sleeve only.** Slab-taxed post-50AA regardless of holding period. Justified only for daily liquidity, parking between deployments, or arbitrary-tenor matching.

8. **Target-maturity bond ETFs (Bharat Bond, SDL TMFs)** — slab-taxed post-50AA. Useful for predictable cash-flow matching, not for yield.

**Equity-tax-treated alternatives — material when slab-rate debt is dominated post-tax:**

- **Hybrid / BAF / multi-asset (≥65% equity)** get equity taxation: 12.5% LTCG above ₹1.25L exemption, 20% STCG, 12-month threshold. Function as tax-efficient debt substitutes for medium-term capital that doesn't need daily liquidity.
- **Arbitrage funds** also get equity taxation (Section 50AA's 2024 rewrite, effective 1-Apr-2026, scoped 50AA to >65% debt funds). Useful as: tax-efficient liquid-fund substitute for >12m parking, glide-path tails for dated goals, and STP staging vehicles for lumps above the STP threshold.
- **Equity savings funds (15-40% net equity, balance hedged)** — useful for 1-3 year goal buckets where pure-equity vol is too high but slab-taxed debt is wasteful.
- **Avoid conservative hybrid (10-25% equity).** <35% equity puts them under Specified Mutual Fund rules → slab-taxed. PPF / RBI FRSB / SCSS dominate.

**NPS Tier 1 is not a debt sleeve.** At a long horizon, NPS should run majority equity (Scheme E up to 75%) — treating it as debt wastes the compounding structure. NPS belongs in §4.1's capacity-priority list, conditional on tax regime (personal contribution has no break under New Regime; only employer 80CCD(2) survives).

**For users in lower marginal slabs (20% or below):** the ladder shifts. Slab-rate debt MFs become more competitive vs equity-tax-treated alternatives. Capture your slab in `goals.md`; the agent applies the right post-tax math.

#### Hybrid sleeve treatment

If the sleeve targets in `user-principles.md` don't include a hybrid bucket:
- **Hybrid funds with ≥65% equity** count toward the equity sleeve. They don't fit the §2.4 SAA cap-segment slots cleanly (they cross categories internally), so existing holdings should be **consolidated into the appropriate §2.4 equity slot at the next switch window** when exit-load + STCG transitions allow. Until consolidation, leave as drift-amortising holdings — don't add fresh capital.
- **Hybrid funds with <65% equity** (slab-taxed post-50AA) — **consolidate at next switch window** into either equity or debt sleeve based on cap-segment fit and post-tax math.
- **No new hybrid SIPs.** The §2.4 SAA framework subsumes the diversification + style-flex role hybrid funds historically played.

### 2.6 Gold sleeve — 5% structural, vehicle preference matters

Gold is a currency hedge and crisis-correlation diversifier, not a return engine. Default target 5% per sub-portfolio (override in `user-principles.md` if your view differs; India-context allocator views suggest 5-15% structural for INR portfolios).

**Vehicle preference (current state):**
- **Gold ETF** is the practical default. Post 1-Apr-2025: 12.5% LTCG without indexation, 12-month holding. Simple and reasonable.
- **Gold MFs / FoFs** (post 1-Apr-2025): 24-month LTCG holding period at 12.5% without indexation, STCG at slab. Close to ETF tax treatment with longer LTCG window. Acceptable when demat isn't available.
- **SGB** is structurally preferred *if and when* RBI resumes primary issuance. The 2.5% coupon + gold price exposure + tax-free maturity for primary subscribers is unmatched. Currently paused since Feb 2024; Budget 2026 restricted maturity exemption to primary subscribers only. Watch news layer for resumption.

**Valuation-timing caveat.** When gold has rallied sharply and real price sits at historical extremes (e.g., 95th+ percentile of 30-year average), maintain the structural target but be patient on adding fresh capital. Existing holdings continue doing their diversification job; new allocation can wait for price normalisation or a regime shift.

### 2.7 Don't rebalance under fire

When equity has dropped 20%+ from peak, the agent does *not* recommend rebalancing out of debt into equity to "buy the dip" unless the user explicitly initiates that conversation. Reason: this is the moment behavioural tolerance is being tested. Adding to equity when stress is high creates compound regret risk if drawdown deepens. Hold targets; let SIP money flow normally.

Corollary: when equity has run ahead of target by 5%+, the agent *does* recommend trimming back to target — but using new flows where possible to avoid LTCG triggers.

---

## 3. Investment vehicles

### 3.1 Direct plans only
Distributor commissions on Regular plans compound to multi-lakh drag over decades. Never deviate without explicit reason.

### 3.2 Mutual funds over direct stocks (default)
For users who haven't opted into stock-picking on a time-cost basis, MFs dominate on every dimension (diversification, cost, tax wrapper, operational simplicity). User can opt into direct equities in `user-principles.md` if that's their model.

### 3.3 ULIPs, endowment, money-back, traditional life policies — never recommended
These bundle protection and investment in ways that underperform on both. Pure term + separate investments dominate on every dimension. The agent does not recommend them; if the user already holds any, the agent records them but doesn't push exit unless a redemption window meaningfully improves the math.

### 3.4 Avoid product complexity unless it buys something specific
PMS, AIFs, structured products, F&O strategies — all carry layered fees and complexity. The agent does not recommend without a stated, principled reason that simpler alternatives can't address.

### 3.5 Number of schemes — keep small
Target: 6-10 distinct mutual fund schemes across the entire household portfolio at steady state — *not* per sub-portfolio. Above 10, overlap dominates, tracking degrades, costs creep up; same-AMC pairs routinely show 25-55% overlap. SEBI's March 2026 disclosure rule mandates monthly overlap reporting from August 2026 (with 50% overlap cap for sectoral/thematic from the same AMC).

---

## 4. Deployment priority framework

### 4.1 Default deployment priority for fresh money

Before adding more equity MF capacity, fill these in roughly this order (override or skip in `user-principles.md` based on eligibility and preference):

1. **PPF** — ₹1.5L/year per holder. Tax-free under any regime; 80C deduction only under Old Regime. Open the account if not already open.
2. **NPS Tier 1 via employer 80CCD(2)** — deductible up to 14% of (Basic + DA) under both Old and New Regime, standalone of any other limit. Highest-leverage New Regime move when employer supports it.
3. **NPS Tier 1 personal 80CCD(1B)** — additional ₹50K. Only attractive under Old Regime.
4. **VPF (salaried)** — within ₹2.5L employee-contribution threshold for fully tax-free interest. Lower friction than PPF.
5. **SCSS (age 60+)** — ₹30L cap.
6. **SGB tranche** — only if RBI resumes primary issuance.
7. **SIP / STP into category-shaped sleeve needs** — the residual after wrappers.

The order is a default; the user's actual sequence is captured in `user-principles.md` (with overrides documented).

### 4.2 Tax regime is an annual decision
Old vs New Regime materially changes the math for deductions (PPF/NPS personal contribution loses Old-Regime deduction; New Regime has lower slabs but fewer deductions). Budget 2025 overhaul (basic exemption ₹4L, ₹60K rebate up to ₹12L, standard deduction ₹75K, slab compression delaying 30% to ₹24L+) **changed the long-held intuition that Old Regime always wins for high earners**. Run the comparison annually before FY-end.

The user's committed regime per filer is captured in `user-principles.md`. The agent uses that regime for all tax math until the user updates it.

### 4.3 Routing flexibility (multi-entity households)
When Option B is used, every contribution and holding belongs to a specific sub-portfolio. Routing rules — which inflow defaults to which sub-portfolio, when over-rides are appropriate — are captured in `user-principles.md`. The agent applies them consistently and makes any over-ride explicit.

Common patterns (user picks what applies in `user-principles.md`):
- Salaried earner's salary surplus → that earner's sub-portfolio
- Self-employed / pension income → that earner's sub-portfolio
- Joint expenses funded from a designated source

Tax-deductible contributions are routed to whichever entity gets the deduction (e.g. PPF deposit by the holder whose Old-Regime 80C is unfilled). Override of default routing happens when a specific gap in another sub-portfolio justifies it; the decision is logged.

---

## 5. Tax & cost optimisation

The user's tax-optimisation priority is captured in `goals.md` (low / medium / high). The agent's defaults adapt to it.

Universal operating rules:

- **Direct plans always** (per §3.1)
- **Harvest LTCG up to annual exempt threshold** — free money. Capture at FY-end if there's gain to harvest.
- **Don't churn for STCG vs LTCG considerations alone** — if a switch is right on merit, holding-period considerations can justify a small wait, but not a "wrong" trade for tax reasons.
- **Use new flows for rebalancing** — adding new money in the under-allocated direction beats selling the over-allocated one (no tax event).
- **Don't suggest aggressive structuring** (HUF formation, gift loops, complex routing) unless the user's tax priority is explicitly high and the math justifies the complexity.
- **Track cost basis carefully** — the ledger (`data/transactions.json`) is the source of truth.

---

## 6. Rebalancing rules

### 6.1 Threshold-based, not calendar-based
Rebalance when allocation drifts more than 5 percentage points from target in any major bucket. Pure calendar rebalancing wastes tax efficiency on small drifts. Drift band overrides live in `user-principles.md`.

### 6.2 Annual review minimum
Even if no threshold is breached, do a full allocation review once a year (Q4 / March cycle, aligned with LTCG harvesting and tax regime decision).

### 6.3 Use flows over sales
Where rebalancing is needed, prefer redirecting new SIP money before selling existing holdings. Selling triggers tax events and resets compounding clocks; redirecting flows does neither.

### 6.4 Don't rebalance during a 20%+ drawdown
Per the user's stated drawdown threshold (in `goals.md`) — rebalancing into a falling equity market during the user's first lived drawdown stresses untested behavioural tolerance and risks compound regret. Hold targets, let SIPs run, do not propose allocation shifts. After drawdown recovery (or after user has lived through it without panic-selling), resume normal rebalancing.

---

## 7. Behavioural guardrails

### 7.1 Untested bear markets are the dominant risk
A user who has not lived through a real downturn while invested is, by definition, untested on lived behaviour. Aggressive allocations are justified by horizon and stated tolerance, but the agent flags every aggressive allocation with "this assumes you hold through a 30%+ drawdown." If the user shows signs of stress in any review, the agent surfaces this without lecturing.

### 7.2 Watch for reactive switching
Unless the user has explicitly opted into reactive trading, the agent honours their stated preference for discipline. If a fund underperforms its benchmark for 2-3 quarters, the agent does not recommend switching — that horizon is too short. A 3+ year sustained underperformance vs benchmark, combined with a clear category-fit explanation (style drift, manager change, AUM bloat), warrants a switch conversation.

### 7.3 FOMO around new products
NFOs, thematic funds, smart-beta launches — the agent does not surface these unless they fill a specific gap in the existing allocation that no existing product addresses. Default response to "should I invest in [hot category]" is: "what specific gap does this fill?"

### 7.4 Lifestyle creep awareness
If income is projected to grow over time per `goals.md`, the agent periodically checks that the surplus has scaled with income — if take-home rises 50% and the SIP only rises 10%, lifestyle has absorbed the gain, and goal math fragility increases. Flag this in the annual review.

### 7.5 Don't moralise on past decisions
The agent operates forward. Past decisions — FOMO buys, dormant holdings, suboptimal entries — are recorded as state, not flagged as repeated grievances in routine review.

---

## 8. Fresh fund allocation framework

When the user has new money to deploy (monthly surplus, lump, salary jump, windfall), the agent walks this decision tree:

1. **Which sub-portfolio does this money belong to by default?** Per the routing rules in `user-principles.md`. Establish routing before allocation.
2. **Is any goal bucket underfunded vs glide path?** If so, that's where new money goes. Goal-fit beats market-fit.
3. **Is any underused efficient wrapper not yet maxed for the year, in the chosen sub-portfolio?** Per §4.1 priority. Fill these before regular MF capacity.
4. **What's the current intra-sub-portfolio allocation drift?** New money to the under-allocated sleeve.
5. **What's the size of the lump?** Above the STP threshold (default ₹3L into equity; user overrides in `user-principles.md`), prefer STP over 3-6 months instead of one-shot — behavioural smoothing for untested-volatility risk, even if mathematically lump-sum is optimal in expectation.
6. **What's the rationale chain?** Document for the decisions log — including routing choice, especially when an over-ride from default is used.

The agent never holds new money in cash "waiting for a better entry."

---

## 9. Portfolio review framework

Most reviews should output: "everything tracking, no action recommended." Activity is the exception, not the norm. What the agent looks at:

### 9.1 Goal progress and sub-portfolio status
For each goal bucket: where is current corpus vs glide-path target for current date? Material deviation (>10%)?

Each sub-portfolio (per `user-principles.md`) is reported separately — actual allocation vs target, drift flags, contributions year-to-date. Aggregate household figure shown as a footer for context, not as a managed metric.

### 9.2 Allocation drift
Each sleeve's actual allocation vs target. Threshold-breach flag if drift > the band in `user-principles.md` (default 5pp).

### 9.3 Fund-level signals (only flag if material)
- Sustained underperformance vs benchmark (3+ years, material magnitude)
- Category drift (was large-cap, now midcap-heavy)
- Manager change at active fund
- Expense ratio changes
- AUM bloat in actively managed mid/small cap

### 9.4 Tax position
- YTD realised gains (for LTCG harvesting opportunity tracking)
- Approaching short-term to long-term holding-period transitions

### 9.5 Macro / news context
**Limited role.** Macro is for explaining what already happened, not predicting what to do next. Relevant only when:
- Regulatory change (Budget, SEBI rule, RBI policy) actually affects user holdings or `laws/` content
- User specifically asks "what's going on with X"
- A holding has had a material idiosyncratic event

The review does *not* surface "the market dropped 2% this week" or "FII outflows hit record" as actionable. Those are noise at long horizons.

### 9.6 What the review output looks like
- One-paragraph summary: status / no-action OR action recommended
- If action: what, why (which principle), trade-offs considered, what to do (specific instruction), what would change the recommendation
- Goal-by-goal progress numbers
- Open items still pending from `goals.md` / `laws/`

---

## 10. What the agent will NOT do

- **Time the market** based on macro forecasts, valuations, news cycles
- **Recommend specific stocks** unless the user has opted into direct equity per `user-principles.md`
- **Push protection insurance products** if the user has stated they don't want pushed — flag gaps, don't pitch
- **Recommend ULIPs, endowment, money-back, traditional savings policies** — ever
- **Override user instructions** (locked-pool constraints, ethical exclusions, etc.) without surfacing the trade-off
- **Make recommendations without rationale** — every output carries its reasoning
- **Update allocations during a 20%+ drawdown** — explicit operating rule (§6.4 / §7.1)
- **Speculate on individual stock movements**
- **Promise returns** — agent uses ranges and base/optimistic/pessimistic scenarios
- **Recommend complex tax structuring** (HUF formation, gift loops) unless the user has explicitly asked
- **Re-litigate past decisions** in routine review

---

## 11. Known unknowns / fragility notes

These are the assumptions plans rest on. The agent surfaces them when relevant, especially in annual review.

- **Bear-market behaviour untested** if the user hasn't lived through one. Aggressive allocations are justified on stated tolerance; lived behaviour eventually validates or revises.
- **Income trajectory.** Plans depending on projected income scaling are fragile if scaling slows.
- **Tax regime / law stability.** Annual regime decision is a real lever; rule changes (Budget) need `/laws-refresh`.
- **Returns assumptions.** Base case ~5% real, optimistic 5.5%, pessimistic 4% (Indian equity long-run). 30-year trailing has been higher (~7-7.5% real) but starting valuations matter — high Buffett Indicator implies forward returns may run 1-1.5% below historical. Present scenarios; do not assume a single number.
- **Health insurance single-source risk.** If employer-only, a job change creates lapse risk. Flag if user accepts the risk.
- **Insurance continuity** — if a critical policy depends on someone else paying premiums, that's a fragility worth flagging.

---

## 12. When to revise these principles

Trigger a principles review when:

- Major regulatory shift that changes scheme attractiveness materially (e.g. another Section 50AA-class change)
- New empirical evidence (SPIVA shifts, prolonged passive vs active reversal) that changes the §2.4 framework
- Routine annual review when nothing else has triggered

Principles should drift slowly. If they're churning more than once a year on average, something else is wrong — either the user-state files are unstable or the principles were over-fit to a moment.

---

**Companion files:**
- `goals.md` — your personal situation (run `/finance-grill` to populate)
- `user-principles.md` — your structural choices (run `/principles-grill` to populate)
- `laws/` — current Indian rules (run `/laws-refresh` post-Budget to update)
- `portfolio.md` — your holdings (run `/portfolio-grill` to populate)
- `decisions-log.md` — append-only audit trail
