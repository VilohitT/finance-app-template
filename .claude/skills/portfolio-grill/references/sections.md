# Section playbook — portfolio-grill

The full set of questions per section. Within each, follow the **fast-skip pattern**:
1. First ask a binary question: "Do you have any [category]?"
2. If `No` → write `None.` to the section, move to next
3. If `Yes` → run the per-holding capture loop until user says no more

## Capture mode

Default = **minimal-capture mode**. For MF sections (3, 4, 5, 6, 9.4), capture only the seven fields per scheme:

1. Scheme name (full, AMFI-canonical)
2. Plan (Direct / Regular)
3. Capital invested (cost basis, total ₹)
4. Month-year of first investment (e.g., `2025-03`)
5. SIP active y/n + monthly amount
6. Sub-portfolio (name from `user-principles.md` §2)
7. Goal earmark (name from `user-principles.md` §5; common values: `retirement` / `property` / `education` / `emergency` / `unallocated` / `legacy`)

**Heavy mode** (only if user explicitly opts in): also capture units, current NAV, current value, average purchase NAV, total cost basis (from CAS), folio number, exact first-purchase date, most recent purchase date. The heavy field lists below each MF section are the fold-out — skip them in minimal mode.

Non-MF sections (1, 2, 7, 8, 9.2/9.3/9.5/9.6, 10, 11, 12, 13, 14) keep their full type-specific field lists either way — there's no ledger to backfill them.

---

## Section 1 — Liquid

### 1.1 Open
"Let's start with liquid assets — money you can access in days. Savings accounts, current accounts, sweep-linked FDs, and physical cash."

### 1.2 Per account
For each account:
- Bank name
- Account type (savings / current / sweep-FD / NRE / NRO)
- Approximate current balance (round to nearest ₹100 or ₹1000 is fine)
- Sub-portfolio (per `user-principles.md` §2; if the user has a joint-locked sub-portfolio, household operational accounts often go there)
- Goal earmark (default: `unallocated`)

After capturing all accounts, ask: "Any cash-on-hand you'd like recorded?" — captures small physical cash if any.

### 1.3 Important note
Any emergency-fund FDs go in **Section 3** (Fixed Deposits), not here. Section 1 is for operating cash that turns over month-to-month.

---

## Section 2 — Fixed Deposits

### 2.1 Open
"Now FDs — bank fixed deposits, corporate FDs, NBFC FDs. Include the emergency-fund FD here."

### 2.2 Per FD
- Bank / institution name
- Principal amount
- Deposit date — **important for interest accrual reconciliation**; use the actual deposit date, not the renewal date
- Maturity date
- Interest rate (locked at deposit)
- Interest payout frequency: cumulative / quarterly / monthly / on maturity
- Type: regular / tax-saving (5-yr lock-in 80C) / senior citizen / corporate / NBFC
- Auto-renewal status
- Sub-portfolio
- Goal earmark — emergency FD is `emergency`; others typically `unallocated` or specifically goal-earmarked

### 2.3 Probe specifically
- "What's the maturity date of your emergency fund FD? Or is it laddered?"
- If laddered: capture each block separately
- If single FD: capture single FD with its maturity date

### 2.4 After all FDs captured
Compute and record the maturity ladder summary for Section 3.x:
- Total FDs
- Maturing within 12 months
- Maturing 12-36 months  
- Maturing 36+ months

---

## Section 3 — Debt Mutual Funds

> **Inline scheme-name validation applies here and in Sections 4–6, 9.x (Gold MFs).** As soon as the user dictates a scheme name, run `python3 scripts/resolve_schemes.py --names "<name>" --quiet` and confirm the AMFI canonical name + scheme code with the user before recording. See SKILL.md → "Validate scheme names inline, not after the fact" for the HIGH/MEDIUM/LOW handling.

### 3.1 Open
"Now debt mutual funds — liquid funds, ultra-short, short duration, corporate bond, gilt, banking & PSU, etc."

> Briefly explain if user is unsure: "Anything you bought through a mutual fund platform that's primarily fixed-income, not equity. If `goals.md` mentions specific debt-MF holdings, start with those."

### 3.2 Per scheme — minimal mode (default)
For each scheme:
- Full scheme name (e.g., "Bandhan Banking & PSU Debt Fund") — resolve inline to AMFI canonical name + scheme code
- Plan: **Direct or Regular**
- Capital invested (total cost basis, ₹)
- Month-year of first investment (e.g., `2026-04`)
- SIP active y/n; if yes, monthly amount
- Sub-portfolio
- Goal earmark
- Tax regime classification (auto: "Specified Mutual Fund — slab rate" for post-Apr-2023 acquisitions; flag in notes only if exceptional)
- Notes (anything special, e.g. pre-2013 legacy code with `-` plan field)

### 3.2-heavy Per scheme — heavy mode (opt-in only)
Add to the above: AMC, SEBI category (per `laws/sebi-categories.md`), folio number, total units (exact), current NAV, current value, average purchase NAV, total cost basis from CAS, first purchase date (exact), most recent purchase date.

### 3.3 Probe
- "Is this a Direct plan or a Regular plan?" — if user is unsure, look up scheme name on AMFI website or AMC site; Direct plans typically named "...Direct Plan - Growth" or have "DIR" in the code
- "When did you first invest?" — important for tax regime classification
- "Are you still SIP-ing into this?" — if yes, capture monthly amount

### 3.4 Common issue
If `goals.md` mentions a meaningful debt MF total but user says "I just have one fund", confirm whether it's actually one scheme or multiple — large round numbers often hide 2-3 schemes the user has consolidated mentally.

---

## Section 4 — Equity Mutual Funds

> **Inline scheme-name validation applies (see Section 3 callout).** Run `python3 scripts/resolve_schemes.py --names "<name>" --quiet` as soon as the user dictates each scheme name; confirm AMFI canonical name + scheme code before recording.

### 4.1 Open
"Now equity mutual funds — large-cap, mid-cap, small-cap, multi-cap, flexi-cap, focused, sectoral, index funds, etc."

### 4.2 Per scheme — minimal mode (default)
- Full scheme name — resolve inline to AMFI canonical + scheme code
- Plan: Direct or Regular
- Capital invested (total cost basis, ₹)
- Month-year of first investment
- SIP active y/n; monthly amount
- Sub-portfolio (per `user-principles.md` §6 routing — equity from salary-source income typically routes to the earner's sub-portfolio)
- Goal earmark (most equity typically `retirement`; near-term goals like property may earmark a subset)
- Notes

### 4.2-heavy Per scheme — heavy mode (opt-in only)
Add to the above: AMC, SEBI category, active or passive (index / ETF), benchmark, folio number, total units, current NAV, current value, average purchase NAV, total cost basis, first purchase date (exact), most recent purchase date.

### 4.3 Cross-check against goals.md
If `goals.md` records a total equity MF corpus figure, reconcile during the grilling — confirm the captured schemes sum to the stated total; flag any gap.

---

## Section 5 — ELSS

> **Inline scheme-name validation applies (see Section 3 callout).** Run `python3 scripts/resolve_schemes.py --names "<name>" --quiet` per scheme as it's dictated.

### 5.1 Open
"Any ELSS — Equity Linked Savings Scheme — funds? These are equity funds with a 3-year lock-in, used for 80C deductions under Old Regime."

### 5.2 Per ELSS scheme — minimal mode (default)
Same seven fields as equity MF (Section 4.2). For ELSS specifically, also capture:
- **Lock-in summary** — single line, e.g. "Lump 2025-03, lock-in expires 2028-03" or "SIP since 2025-03 — earliest installment unlocks 2028-03". Per-installment tranche detail is heavy mode only.
- **80C claim history** — concise: which FYs claimed under Old Regime; ₹ total per FY. Skip entirely if user has been on New Regime throughout (note in Notes).

### 5.2-heavy Per ELSS scheme — heavy mode (opt-in only)
Add to the above: full equity-MF heavy fields (Section 4.2-heavy), plus a per-installment lock-in tranche table (purchase date, lock-in expiry, ₹ invested for each SIP installment).

### 5.3 Note
If user has been on New Regime, ELSS provides no tax benefit at deposit — flag this in notes for portfolio-review consideration.

---

## Section 6 — Hybrid / Multi-Asset / Balanced Advantage Funds (non-equity-oriented)

> **Inline scheme-name validation applies (see Section 3 callout).** Run `python3 scripts/resolve_schemes.py --names "<name>" --quiet` per scheme as it's dictated.

### 6.1 Open
"Any hybrid, multi-asset, balanced-advantage, or arbitrage funds? These mix equity and debt; some are taxed as equity, others as debt depending on actual allocation."

### 6.2 Per scheme — minimal mode (default)
Same seven fields as equity MF (Section 4.2). Also capture:
- **Tax classification:** equity-oriented (≥65% equity) / Section 112 hybrid (35-65%) / Specified Mutual Fund — slab rate (<35% or post-Apr-2023 with low equity)

> If unsure, the agent can refer to `laws/sebi-categories.md` Section 5 cheat sheet to classify.

### 6.2-heavy Per scheme — heavy mode (opt-in only)
Add the full equity-MF heavy fields (Section 4.2-heavy).

### 6.3 Note about multi-asset classification
For any multi-asset / hybrid fund the user holds, check the actual current equity allocation (from the latest AMC factsheet) to determine tax classification. Aggressive-hybrid funds with 65%+ equity should be in Section 5; multi-asset funds that drop below 65% domestic equity belong here as Specified MFs.

---

## Section 7 — Government Schemes

This section has multiple sub-sections. Open with: "Now government schemes — PPF, EPF, NPS, etc. I'll go through each."

### 7.1 PPF
Ask: "Any PPF accounts? For yourself, father, or any other family member you operate?"

If yes, for each account:
- Account holder
- Bank or post office where opened
- Account number
- Account opening date — **critical for maturity date**
- Maturity date (calculated: 15 years from end of FY of opening)
- Current balance
- FY contributions to date (current FY)
- Annual contribution (typical / target)
- Extension status: initial 15-yr block / extended with contribution / extended without contribution
- 80C claim history for Old Regime FYs
- Sub-portfolio (each PPF holder's account belongs to that holder's sub-portfolio per `user-principles.md` §6)
- Goal earmark — typically `retirement`
- Notes

> If `goals.md` records the user as not having a PPF account despite being eligible, write `None — flagged for action per principles.md §4.1` after confirming with user.

### 7.2 EPF / VPF
Ask: "Any salaried members of the household — do they have an active UAN?"

For each EPF holder:
- UAN
- Current employer establishment ID
- Current EPF balance (member portion = employee contributions + interest)
- Current EPF balance (employer portion = employer contributions + interest)
- Current Basic + DA monthly (needed to compute mandatory and VPF capacity)
- Mandatory employee contribution = 12% of (Basic + DA) — record this rate
- VPF rate / amount if any
- YTD employee contribution (current FY)
- Tax-free interest threshold check: is YTD < ₹2.5L?
- Prior employer EPF balances: consolidated y/n; UAN-linked y/n
- Sub-portfolio: holder's sub-portfolio per `user-principles.md`
- Goal earmark: `retirement`

### 7.3 NPS Tier 1
Ask: "Any NPS Tier 1 accounts in the household? If yes, share PRAN."

> If the user identified NPS as a planned vehicle in `user-principles.md` §8 but doesn't have an account yet, write `None — flagged for action per principles.md §4.1` after confirming.

If yes, for each account holder:
- PRAN
- Pension Fund Manager
- Allocation choice: Active or Auto (LC25 / LC50 / LC75)
- If Active: % E / % C / % G / % A
- Current corpus
- Annual contribution (typical)
- 80CCD(1) claim history (Old Regime years)
- 80CCD(1B) claim history (Old Regime years)
- Employer 80CCD(2) contribution: y/n, amount/month
- Sub-portfolio: holder's sub-portfolio per `user-principles.md`
- Goal earmark: `retirement`

### 7.4 NPS Tier 2
"Any NPS Tier 2 account? (Tax benefits don't apply for private sector — generally not used.)"

### 7.5 SSY
Skip unless the household has a daughter under 10 (per `goals.md`).

### 7.6 SCSS
Skip unless a holder is age ≥ 60 (per `goals.md`). Note diary entry if a holder will become eligible within the next 5 years.

### 7.7 Post Office schemes
Ask: "Any post office schemes — POMIS, NSC, KVP, post office RD?"

For each: scheme, holder, deposit, dates, rate, sub-portfolio, goal earmark.

---

## Section 8 — Bonds

### 8.1 Open
"Any bonds — RBI Floating Rate Bonds, tax-free bonds, government securities, corporate bonds?"

### 8.2 If yes, capture per bond/issue
- RBI FRB: holder, amount, dates, current rate (resets half-yearly)
- Tax-free bonds: issuer (NHAI, IRFC, REC, etc.), amount, coupon, maturity
- G-Sec / SDL: issuer, face value, coupon, maturity
- Corporate bonds: issuer, rating, face value, coupon, maturity

---

## Section 9 — Gold

### 9.1 Open
"Now gold — let's go through each form. SGBs first, then ETFs, MFs, digital gold, and physical."

### 9.2 SGB tranches
For each tranche held:
- Tranche ID (e.g., "2020-21 Series VII")
- Issue date
- Maturity date (8 years from issue)
- Holder
- Units in grams
- Issue price per gram (the original allotment price)
- Current value (units × current gold price ~ ₹/g)
- **Acquisition route: primary subscription or secondary market** — important per current Budget rules for maturity tax exemption (per `laws/gold.md`)
- Interest payment dates (half-yearly anniversaries from issue)
- Premature redemption eligibility (5 years from issue)
- Sub-portfolio
- Goal earmark — typically `retirement`
- Notes

### 9.3 Gold ETFs
For each:
- ETF name
- Issuer (AMC)
- Demat account / folio
- Units
- Current NAV
- Current value
- Average purchase price
- First purchase date
- Sub-portfolio
- Goal earmark

### 9.4 Gold Mutual Funds (FoF)

> **Inline scheme-name validation applies (see Section 3 callout).** Run `python3 scripts/resolve_schemes.py --names "<name>" --quiet` per Gold MF as it's dictated.

#### 9.4 Minimal mode (default)
Same seven fields as equity MF (Section 4.2). Also flag:
- Tax: "Specified Mutual Fund — slab rate"

#### 9.4-heavy Heavy mode (opt-in only)
Add the full equity-MF heavy fields (Section 4.2-heavy).

### 9.5 Digital gold
Platform, holder, grams, average purchase price, current value, sub-portfolio, goal earmark.

### 9.6 Physical gold
- Jewellery: total approximate value (single number; not investment-grade)
- Investment-grade bullion / coins: per piece — purity (22K / 24K / 99.9%), weight, current value, purchase date, holder, sub-portfolio, goal earmark

> If `goals.md` records a combined physical-gold figure, resolve into separate jewellery and bullion values during the grill.

---

## Section 10 — Direct Equities

### 10.1 Open
"Any direct stocks held in a demat account?"

### 10.2 Per stock
- Company name
- Exchange (NSE / BSE)
- Holder
- Demat account
- Quantity
- Current price (today's)
- Current value
- Average purchase price
- Total cost basis
- First purchase date
- Sector
- Sub-portfolio
- Goal earmark — often `legacy` for dormant holdings; `retirement` or `unallocated` for actively managed
- Notes — capture "dormant" status for old holdings

> Capture all holdings with as much precision as the user has; flag UNKNOWN for any prices/dates not at hand and note "fetch from broker capital gains statement" as the source.

---

## Section 11 — Real Estate

### 11.1 Primary residence
- Location
- Approximate market value (today's, rough)
- Year acquired
- Holder(s) — joint or single name
- Home loan: balance, rate, EMI, tenure remaining (or N/A if no loan per `goals.md`)
- Sub-portfolio: typically a joint-locked sub-portfolio if defined in `user-principles.md`, since the primary home is not investable

### 11.2 Investment property
"Any investment property currently?"

### 11.3 Plots / Agricultural land
"Any plots or agricultural land?"

---

## Section 12 — Insurance Assets

### 12.1 Term life
For each:
- Insurer
- Policy number
- Sum assured
- Annual premium
- **Premium-paying party** (self / spouse / parent / grandparent — important for continuity risk if a third party pays)
- Policy start date
- Policy end date / tenure
- Riders
- Notes

### 12.2 Health
For each:
- Insurer
- Policy type (employer floater / individual / family floater / senior citizen / top-up / super top-up)
- Sum assured
- Annual premium
- Premium-paying party
- Insureds covered
- Policy date
- Riders / add-ons
- Notes

### 12.3 ULIPs / Endowment / Money-back / Traditional
If any, capture per policy. If none, confirm and write None.

### 12.4 Critical illness / Disability standalone
If any, capture per policy.

---

## Section 13 — Alternatives

### 13.1 Crypto / VDA
"Any cryptocurrency holdings — Bitcoin, Ethereum, others on Indian or foreign exchanges?"

### 13.2 PMS / AIF
"Any Portfolio Management Service or Alternative Investment Fund holdings?"

### 13.3 REITs / INVITs
"Any Real Estate Investment Trusts or Infrastructure Investment Trusts?"

### 13.4 Foreign assets (LRS)
"Any holdings outside India under the Liberalised Remittance Scheme — US stocks, foreign bank accounts, ESOPs in a foreign company?"

### 13.5 Anything else
"Anything else of value not yet captured? Loans given to friends/family, business interests, intellectual property, etc.?"

---

## Section 14 — Liabilities

### 14.1 Loans
For each:
- Loan type (home / car / personal / education / credit-card-rollover / other)
- Lender
- Original loan amount
- Current balance
- Interest rate
- EMI
- Tenure remaining
- Holder

### 14.2 Credit card revolving balance
"Any credit card outstanding that's revolving (i.e., not paid in full each cycle)?"

### 14.3 Other
"Any other money owed — family loans, deferred payments, anything?"

---

## After Section 14 — Reconciliation pass

Don't write portfolio.md yet. First, run the reconciliation described in SKILL.md Step 5:

1. **Compute totals** and surface to the user:
   - Total household corpus (investable, ex-real-estate, ex-emergency-FD)
   - Total household net worth (incl. real estate, ex-loans)
   - Sub-portfolio split percentages
   - Asset-class split per sub-portfolio and aggregate

2. **Cross-check against goals.md Section 3** if known:
   - Does the captured total reconcile with goals.md's stated total investable corpus?
   - Any material gap (>5%) → surface to user, ask for explanation/correction

3. **Sub-portfolio sanity check:**
   - For each sub-portfolio in `user-principles.md` §2, compare current sleeve mix to the target in `user-principles.md` §3
   - Surface any clear mismatch ("Sub-portfolio X is currently <actual> vs target <target> — does this reflect reality, or should some holdings reassign?")

4. **Goal earmark sanity check:**
   - What % is `unallocated`? If > 50%, that's likely fine for now — the agent will refine over time.
   - Any goal with 0% earmarked despite being active? Flag.

5. **Plan check:**
   - Any Regular plans? List them for follow-up consideration in portfolio-review.

6. **Open items count:**
   - How many fields are UNKNOWN? List the top fetches by source.

Surface 2-5 of these tensions/observations. For each, ask user to confirm, correct, or note as accepted.

Only then write `portfolio.md`.
