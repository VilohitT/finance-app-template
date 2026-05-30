# Findings checklist — portfolio-review

The systematic list of conditions the skill checks for, and the finding it generates if the condition is met. The skill works through this checklist on every run; most checks return "no finding" in steady state.

Each check has:
- The condition checked
- The data source(s) it reads
- The finding type (ACTION / WATCH / INFO) it generates if condition is met
- The principle it applies
- A brief note on what would change the verdict

---

## Group 1 — Goal progress

### 1.1 Retirement goal — corpus vs glide-path
- **Condition:** pessimistic-scenario `pct_of_target` < 0.85 → WATCH; < 0.70 → ACTION
- **Data:** `portfolio.md` goal-earmark for retirement; `goals.md` retirement target (corpus + date); current monthly inflow from `data/recurring.json` + manual entries
- **Helper:** `scripts/lib/projection.goal_progress()` with `DEFAULT_REAL_RETURN_SCENARIOS` (5%/5.5%/4% real per `principles.md` §11). Returns base / optimistic / pessimistic `pct_of_target` and `shortfall_inr` per scenario. Quote all three in the finding; do not collapse to a point estimate.
- **Finding if behind:** WATCH or ACTION per the threshold above
- **Principle:** §1.2 (goal-based bucketing)
- **Computation note:** Do not write prose-arithmetic for the projection. The helper compounds monthly with optional `LumpReceipt` schedule for known lump inflows.

### 1.2 Dated non-retirement goals (property, education, etc.) — corpus vs target
- **Condition:** Per-goal `pct_of_target` against the user's stated goal in `goals.md` and the glide schedule in `user-principles.md` §5
- **Data:** `portfolio.md` goal-earmark + `goals.md` goal-specific targets + `user-principles.md` glide schedule
- **Finding:** WATCH or ACTION per the threshold
- **Principle:** §1.2

### 1.3 Emergency fund — sufficiency check
- **Condition:** Emergency fund < 6× monthly expenses; or > 24× monthly expenses (over-insured drag)
- **Data:** `portfolio.md` emergency holdings; `goals.md` monthly expenses
- **Finding:** WATCH if under-funded; INFO if materially over (opportunity cost)
- **Principle:** §1.2, §10

---

## Group 2 — Sub-portfolio allocation drift

### 2.1 Per-sub-portfolio drift vs target
- **Condition:** For each sub-portfolio in `user-principles.md` §2, any sleeve drifts > the drift band (default 5pp per `user-principles.md` §10) from target (per `user-principles.md` §3)
- **Data:** `discover.py` §10 (sub-portfolio totals — derived from `transactions.current_value_per_scheme()` × `drawdown.classify_sleeve()`); `user-principles.md` §3
- **Finding:** WATCH if correctable through future flows; ACTION only if drift > 3× drift band AND no flow plan exists
- **Principle:** §6.1 (threshold-based) + §6.3 (flow over sales)

### 2.2 Aggregate household drift
- **Condition:** Reported, not optimised against (per `principles.md` §2.1)
- **Finding:** Always INFO at most; never ACTION

### 2.3 Drawdown protection (rebalancing block)
- **Condition:** Aggregate equity drawdown ≥ 20% from trailing peak
- **Finding:** No rebalancing recommended regardless of drift; INFO only with explicit "holding through drawdown per principle §7.1"
- **Principle:** §6.4 + §7.1
- **Helper:** `scripts/lib/drawdown.aggregate_equity_drawdown(sub_portfolio)`. The return dict's `block_at_minus_20pct` field IS the gate flag; do not re-derive it. Per-scheme drawdowns and the value-weighted aggregate are also returned. Phase 0 (`scripts/discover.py`) already runs this for each sub-portfolio — quote §9 of the discovery report rather than calling the helper a second time.

### 2.4 Within-equity composition drift
- **Condition:** Within the equity sleeve, any slot (Nifty 50 / NN50 / Flexicap / Mid / Small / Intl per `principles.md` §2.4) drifts outside its TAA band
- **Data:** `discover.py` §10 with category breakdown; `principles.md` §2.4 (or override in `user-principles.md`)
- **Finding:** WATCH if correctable; ACTION if drift > 2pp beyond band AND no flow correction in 6 months
- **Principle:** §2.4

---

## Group 3 — Fresh-money capacity

### 3.1 PPF accounts not opened or below FY cap
- **Condition:** For each holder of a PPF in `user-principles.md` §8: balance = 0 (account not opened), OR FY contribution < ₹1.5L with > 30 days left in FY
- **Finding:** ACTION
- **Principle:** §4.1 item 1

### 3.2 NPS Tier 1 not enrolled
- **Condition:** Per `user-principles.md` §8, the user planned to use NPS but `portfolio.md` shows NPS corpus = 0
- **Finding:** ACTION (with HR check on 80CCD(2) if employer route)
- **Principle:** §4.1 item 2

### 3.3 NPS additional ₹50K (80CCD(1B)) — Old Regime check
- **Condition:** Per `user-principles.md` §7, the filer is on Old Regime AND has not used 80CCD(1B) deduction in current FY
- **Finding:** ACTION
- **Principle:** §4.1 item 3

### 3.4 VPF capacity unused
- **Condition:** Per `user-principles.md` §8, VPF is planned; VPF rate = 0 (per `portfolio.md`) AND headroom under ₹2.5L threshold > ₹50K/year
- **Finding:** ACTION
- **Principle:** §4.1 item 4

### 3.5 SCSS for an eligible holder
- **Condition:** A holder is age ≥ 60 (per `goals.md`) AND no SCSS account
- **Finding:** ACTION (when eligibility opens)
- **Principle:** §4.1 item 5

### 3.6 SGB resumption check
- **Condition:** RBI announces new SGB tranche AND the user's gold sleeve has unfilled allocation
- **Finding:** WATCH (await user direction)
- **Principle:** §4.1 item 6

---

## Group 4 — Scheme-level signals

### 4.1 Regular plan holdings (Direct switch consideration)
- **Condition:** Any holding in `portfolio.md` is a Regular plan
- **Finding:** WATCH or ACTION depending on tax cost timing
  - If exit load window OPEN (within 1 year of purchase): WATCH — switching costs load + STCG; expense ratio savings recovered in N years; switching may not be worth it now
  - If exit load window CLOSED + LTCG eligible: ACTION — switch is now favourable
  - If past exit load but still STCG: WATCH — wait for LTCG transition
- **Principle:** §3.1 (Direct only) + §1.6 (tax efficiency as tailwind)
- **Tax-check call:** Eagerly invoked — fold result into finding

### 4.2 Holding-period transitions (next 30 days)
- **Condition:** Any holding within 30 days of an STCG-LTCG threshold (12 months for equity / equity-oriented hybrid / Gold ETF; 24 months for Gold MF / Specified-MF debt)
- **Finding:** WATCH (with a brief note: deferring redemption to <date> changes tax from STCG to LTCG)
- **Principle:** §1.6 / §1.7

### 4.3 Active fund underperformance check
- **Condition:** Active fund has 3+ years sustained underperformance vs benchmark
- **Finding:** ACTION (consider switch)
- **Principle:** §7.2 (don't react to short-term)
- **Helpers:** `scripts/lib/returns.alpha_vs_benchmark(fund, benchmark, period_days=1095)` and `scripts/lib/returns.discover_benchmark_for_category(category)`. Threshold: `alpha < -0.02` (2pp annual underperformance over the 3Y window). Skip categories where `discover_benchmark_for_category` returns None (Flexi/Multi/Value/ELSS/Focused/Sectoral) — picking Nifty 50 there silently misleads alpha. Do not write rolling-return arithmetic in prose.
- **Index-fund variant:** Use `scripts/lib/returns.tracking_error(fund, benchmark, period_days=1095)` instead. Within an index category, alpha collapses to noise (~12 bps); tracking error differentiates trackers.

### 4.4 Manager change at active fund
- **Condition:** A held active fund's `manager_name` differs from the prior review's snapshot
- **Finding:** WATCH with research recommendation
- **Principle:** §7.2
- **Helpers:** `scripts/lib/fund_quality.load_quality()` returns the current `manager_name` per scheme. Persist a "Manager snapshot YYYY-MM-DD" block to `decisions-log.md` on every review; the next review diffs against the prior snapshot. First run with this rule live writes the baseline and produces no finding.

### 4.5 Fund category drift
- **Condition:** A held fund's actual market-cap composition has drifted out of stated category
- **Finding:** WATCH
- **Principle:** §7.2
- **Note:** Requires factsheet portfolio composition data (not in default data layer). Dormant unless the data layer is extended.

### 4.6 Tax classification UNKNOWN
- **Condition:** Holding's tax classification is UNKNOWN per `portfolio.md` (e.g. multi-asset funds requiring factsheet verification of equity %)
- **Finding:** INFO with research item
- **Principle:** §1.7

---

## Group 5 — Tax position

### 5.1 Tax regime decision overdue
- **Condition:** Current FY tax regime decision has not been documented in `user-principles.md` §7, or `goals.md` flags it as pending
- **Finding:** ACTION
- **Principle:** §4.2

### 5.2 LTCG harvesting opportunity
- **Condition:** FY YTD realised equity LTCG + unrealised LTCG > ₹1.25L threshold AND there are LTCG-eligible holdings AND FY-end is approaching
- **Finding:** Depends on user's tax priority (per `goals.md`):
  - Priority ≥ 5/10: ACTION
  - Priority 3-4/10: WATCH (only if very clean — no exit load, no churn cost)
  - Priority < 3/10: INFO (may not be worth operational effort)
- **Tax-check call:** Eager (LTCG harvesting variant)
- **Principle:** §5 (tax & cost optimisation operating rules) + §1.6

### 5.3 STCL/LTCL set-off opportunity
- **Condition:** Realised loss in current FY available for set-off against gains
- **Finding:** ACTION before FY-end if material
- **Principle:** §5

---

## Group 6 — Income trajectory (sensitivity)

### 6.1 Income tracking vs projection
- **Condition:** Actual annual income materially below projected trajectory in `goals.md`
- **Finding:** WATCH (informational; affects retirement-math fragility)
- **Principle:** §11 (known unknowns) + §7.4 (lifestyle creep awareness)
- **Note:** Annual review item; not weekly. Report as "tracking" or "behind" against `goals.md` projection.

### 6.2 Lifestyle creep
- **Condition:** Take-home rises, but SIP amount doesn't proportionally
- **Finding:** WATCH at annual review
- **Principle:** §7.4

---

## Group 7 — Insurance and protection (light touch)

### 7.1 Term insurance lapse risk
- **Condition:** Term policy premium has not been paid in current cycle
- **Finding:** ACTION (immediate — prevents lapse)
- **Note:** Especially relevant if `goals.md` flags continuity risk (e.g., premium paid by a third party).

### 7.2 Health insurance gap (do NOT push if user opted out)
- **Condition:** No personal (non-employer) health cover
- **Finding:** Suppressed if `goals.md` records the user has accepted this risk; INFO/WATCH if not
- **Principle:** `principles.md` §10 — agent does not push protection products when user has opted out

### 7.3 ULIPs / endowment / money-back / traditional
- **Condition:** Any such policy held
- **Finding:** WATCH (with surrender vs hold computation)
- **Principle:** §3.3

---

## Group 8 — Operational hygiene

### 8.1 EPF UAN consolidation
- **Condition:** Multiple member IDs across employers not consolidated
- **Finding:** ACTION

### 8.2 Open data fetches (UNKNOWN fields in `portfolio.md`)
- **Condition:** Open items checklist non-empty
- **Finding:** INFO each, or consolidated reminder

### 8.3 Stale review (no review in > 14 days)
- **Condition:** Last portfolio-review > 14 days ago
- **Finding:** None — the act of running this review resolves it. Just acknowledge the gap.

---

## Group 9 — Skills and rule layer

### 9.1 Stale laws files
- **Condition:** Any `laws/` file's `last_verified_against_budget` < most recent Budget
- **Finding:** INFO at top of report ("⚠️ Some laws files are stale...")

### 9.2 Major Budget / Notification triggered
- **Condition:** Recent Budget passed; `/laws-refresh` not yet run
- **Finding:** INFO recommendation to run `/laws-refresh`

### 9.3 New SEBI MF categorisation
- **Condition:** Major SEBI categorisation update
- **Finding:** INFO recommendation to run `/laws-refresh` + portfolio re-classification

---

## How the checklist is applied

For each run, the skill walks Groups 1-9, checking each condition. Most checks return "no finding" in steady state. The findings that fire become the report.

**Default suppression rules:**
- A finding is not generated if it duplicates a prior finding still open in `decisions-log.md`
- A finding is not generated if the user has Rejected a similar finding within the last 90 days (unless underlying conditions have materially changed)

**Default consolidation rules:**
- Multiple findings sharing a root cause (e.g., "no SIPs running" causing allocation drift + fresh-money capacity unused + glide-path deviation) consolidate into one finding with sub-points
- Multiple Regular-plan holdings consolidate into one finding (don't generate N separate ones)
- Multiple UNKNOWN data items consolidate into one INFO

**Severity escalation rules:**
- An ACTION finding stays ACTION
- A WATCH finding becomes ACTION if the underlying threshold tightens (e.g., exit-load window closes)
- An INFO finding becomes WATCH if the underlying issue starts materially affecting goals
