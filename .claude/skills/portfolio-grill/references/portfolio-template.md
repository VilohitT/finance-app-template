# Portfolio.md template — portfolio-grill

This is the **exact** structure for the output file. Use it verbatim.

## Capture mode (read first)

Default = **minimal-capture mode** for MF sections (4 Debt MF, 5 Equity MF, 6 ELSS, 7 Hybrid, 10.3 Gold MF). The ledger backfills units and current values from cost basis + purchase month; collecting more upfront makes the interview longer without improving downstream accuracy. Each MF holding carries only seven fields:

1. Scheme name (full, AMFI-canonical)
2. Plan (Direct / Regular)
3. Capital invested (cost basis, ₹)
4. Month-year of first investment
5. SIP active y/n + monthly amount
6. Sub-portfolio
7. Goal earmark

Section 1.5 of the produced `portfolio.md` is auto-rendered from `data/transactions.json` + live NAVs in `data/market.db` — it supplies units, current NAVs, and current values without the user needing to dictate them.

The MF sections below show the **minimal-mode block first** (use this by default). A `### N.x-heavy` fold-out follows each one for the opt-in heavy-mode field list. Skip the heavy block unless the user has explicitly asked for full precision.

Non-MF sections (FDs, PPF, EPF, NPS, SGB, real estate, insurance, etc.) keep their full type-specific field lists either way — no ledger backfills them.

## Field-level conventions

- **`UNKNOWN — fetch from <source>`** for missing data; `<source>` should be specific (e.g., "CAS from CAMS", "UAN portal", "ICICI Pru policy document", "SBI passbook")
- **`N/A`** when a category genuinely doesn't apply
- Round currency to the nearest ₹ or ₹100 as natural
- Dates: ISO format `YYYY-MM-DD` for full dates; `YYYY-MM` for the minimal-mode "month of first investment" field
- Sub-portfolio values: per `user-principles.md` §2 (single portfolio name, or one of the multi-entity sub-portfolio names)
- Goal earmark values: per `user-principles.md` §5 (common: `retirement` / `property` / `education` / `emergency` / `unallocated` / `legacy`)
- All numeric values are at-the-time-of-grilling snapshots — values change daily

---

## TEMPLATE BEGINS BELOW THIS LINE — copy from here downward

```markdown
# Portfolio Holdings

last_updated: YYYY-MM-DD
last_grilled_by: portfolio-grill v1
cost_basis_granularity: minimal-capture
transactions_csv_present: false
review_due: YYYY-MM-DD (3 months from last_updated)

> **Cost basis note:** This file uses **minimal-capture** granularity. For each MF holding, captured fields are: scheme name, plan (Direct/Regular), capital invested (cost basis), month-year of first investment, SIP active y/n, sub-portfolio, and goal earmark. Folio numbers, exact units, current NAV, current value, and average purchase NAV are not separately captured — flagged `UNKNOWN — fetch from CAS` and resolved when a tax/redemption decision requires precision. All ₹ figures in MF sections below are **cost basis**, not current market value. Section 1.5 auto-renders units / NAVs / current values from `data/transactions.json` + `data/market.db`.

> **Sub-portfolio framework:** Per `user-principles.md` §2, holdings are tagged with the user's sub-portfolio names (single portfolio under Option A; multiple sub-portfolios under Option B). Goal earmarks (per `user-principles.md` §5) are informational; they don't constrain allocation logic.

---

## 1. Household Summary

- **Total household corpus (investable, ex-real-estate, ex-emergency-FD):** ₹
- **Total household net worth (incl. real estate, ex-loans):** ₹
- **Sub-portfolio split (investable):** (per `user-principles.md` §2)
  - <Sub-portfolio name 1>: ₹ ( __% )
  - <Sub-portfolio name 2>: ₹ ( __% )
  - <Sub-portfolio name 3>: ₹ ( __% )  (if applicable)
- **Asset-class split (investable, household aggregate):**
  - Equity: __%
  - Debt: __%
  - Gold: __%
- **Asset-class split (per sub-portfolio):**
  - [Repeat per sub-portfolio defined in `user-principles.md` §2]
- **Goal earmark coverage:** (per `user-principles.md` §5)
  - <Goal 1>: ₹ ( __% )
  - <Goal 2>: ₹ ( __% )
  - Unallocated: ₹ ( __% )

---

## 2. Liquid

### 2.1 Savings & Current Accounts
For each:
- **Bank:**
- **Account type:** (savings / current / sweep-FD / NRE / NRO)
- **Current balance:** ₹
- **Sub-portfolio:**
- **Goal earmark:**
- **Notes:**

### 2.2 Cash on hand
- **Approximate amount:** ₹
- **Notes:**

---

## 3. Fixed Deposits

For each FD or FD ladder block:
- **Bank / institution:**
- **Deposit amount (principal):** ₹
- **Deposit date:** YYYY-MM-DD
- **Maturity date:** YYYY-MM-DD
- **Interest rate:** __%
- **Interest payout frequency:** (cumulative / quarterly / monthly / on maturity)
- **Type:** (regular / tax-saving / senior citizen / corporate / NBFC)
- **Auto-renewal:** (yes/no)
- **Sub-portfolio:**
- **Goal earmark:**
- **Notes:**

### 3.x FD ladder summary
- Total FDs: ₹
- Maturing within 12 months: ₹
- Maturing 12-36 months: ₹
- Maturing 36+ months: ₹

---

## 4. Debt Mutual Funds

### 4.x Per scheme — minimal mode (default)

Use the table form below — one row per scheme.

| # | Scheme name | AMC | Plan | Scheme code | Capital ₹ | Month | SIP | Sub-portfolio | Earmark |
|---|---|---|---|---|---|---|---|---|---|

For each row, also note as a sub-bullet:
- **Tax regime:** Specified Mutual Fund — slab rate (post-Apr-2023 acquisition) / pre-Apr-2023 transitional
- **Notes:** (anything special — pre-2013 legacy code, AMFI plan field shows `-`, naming reconciliations, etc.)

### 4.x-heavy Per scheme — heavy mode (opt-in only)
Use this expanded layout only if the user explicitly opted into heavy mode at Step 1:
- **Scheme name (full):**
- **AMC:**
- **Plan:** Direct / Regular
- **Category (SEBI):** (liquid / ultra-short / low-duration / money-market / short-duration / corporate-bond / banking-PSU / gilt / dynamic-bond / credit-risk / other)
- **Folio number:**
- **Total units:**
- **Current NAV:** ₹
- **Current value:** ₹
- **Average purchase NAV:** ₹
- **Total cost basis:** ₹
- **First purchase date:** YYYY-MM-DD
- **Most recent purchase date (if SIP active):** YYYY-MM-DD
- **SIP active:** (yes/no — amount/month if yes)
- **Tax regime applicable:** (Specified Mutual Fund — slab rate, post-Apr-2023 acquisition / pre-Apr-2023 transitional)
- **Sub-portfolio:**
- **Goal earmark:**
- **Notes:**

### 4.x Debt MF summary
- Total debt MF corpus (cost basis): ₹
- Schemes count:
- Direct vs Regular split:

---

## 5. Equity Mutual Funds

### 5.x Per scheme — minimal mode (default)

Use the table form below — one row per scheme.

| # | Scheme name | AMC | Plan | Scheme code | Capital ₹ | Month | SIP | Sub-portfolio | Earmark |
|---|---|---|---|---|---|---|---|---|---|

Notes per row (sub-bullets):
- **Index / active flag** if it's a passive scheme (so portfolio-review's tracking-error gate fires correctly)
- **Notes:** anything special

### 5.x-heavy Per scheme — heavy mode (opt-in only)
Use this expanded layout only if the user explicitly opted into heavy mode at Step 1:
- **Scheme name (full):**
- **AMC:**
- **Plan:** Direct / Regular
- **Category (SEBI):** (large-cap / mid-cap / small-cap / multi-cap / flexi-cap / large-and-mid-cap / focused / sectoral-thematic / value-contra / dividend-yield / index / international)
- **Active or passive:** (active / index / ETF)
- **Benchmark:**
- **Folio number:**
- **Total units:**
- **Current NAV:** ₹
- **Current value:** ₹
- **Average purchase NAV:** ₹
- **Total cost basis:** ₹
- **First purchase date:** YYYY-MM-DD
- **Most recent purchase date:** YYYY-MM-DD
- **SIP active:** (yes/no — amount/month if yes)
- **Sub-portfolio:**
- **Goal earmark:**
- **Notes:**

### 5.x Equity MF summary
- Total equity MF corpus (cost basis): ₹
- Schemes count:
- Direct vs Regular split:
- Active vs index/ETF split:
- Cap-allocation split (cost-basis weighted): large __% / mid __% / small __% / international __%

---

## 6. ELSS

### 6.x Per scheme — minimal mode (default)

Same seven-field row as equity MF (Section 5) — use the same table format. Add per-row sub-bullets:
- **Lock-in summary:** one line, e.g. `Lump 2025-03 → unlock 2028-03` or `SIP since 2025-03 — earliest tranche unlocks 2028-03`
- **80C claim history (Old Regime FYs only):** concise, e.g. `FY24 ₹1.5L Old; FY25 onwards New (no 80C claim)`. Skip entirely if user has been on New Regime throughout.
- **Notes:** anything special

### 6.x-heavy Per scheme — heavy mode (opt-in only)
Use this expanded layout only if the user explicitly opted into heavy mode at Step 1:
- **Scheme name (full):**
- **AMC:**
- **Plan:** Direct / Regular
- **Folio number:**
- **Total units:**
- **Current NAV:** ₹
- **Current value:** ₹
- **Lock-in tranche detail:** (list each tranche with purchase date and lock-in expiry date — required for ELSS specifically because each SIP installment has its own 3-yr clock)
  - YYYY-MM-DD purchase, lock-in expires YYYY-MM-DD, ₹X invested
  - (repeat per tranche)
- **Average purchase NAV:** ₹
- **Total cost basis:** ₹
- **80C claim history:** (FY-by-FY contribution amount, regime under which claimed if applicable)
- **Sub-portfolio:**
- **Goal earmark:**
- **Notes:**

---

## 7. Hybrid / Multi-Asset / Balanced Advantage Funds (non-equity-oriented)

### 7.x Per scheme — minimal mode (default)

Same seven-field row as equity MF (Section 5) — use the same table format. Add per-row sub-bullets:
- **Tax classification:** equity-oriented / Section 112 hybrid / Specified Mutual Fund — slab rate
- **Notes:** anything special

> Aggressive-hybrid and equity-savings funds that meet the equity-oriented test belong in Section 5. Conservative-hybrid and similar that fall below the threshold belong here.

### 7.x-heavy Per scheme — heavy mode (opt-in only)
Use this expanded layout only if the user explicitly opted into heavy mode at Step 1:
- **Scheme name (full):**
- **AMC:**
- **Plan:** Direct / Regular
- **Category (SEBI):** (aggressive-hybrid / balanced-hybrid / conservative-hybrid / equity-savings / multi-asset-allocation / balanced-advantage / arbitrage)
- **Tax classification:** (equity-oriented / Section 112 hybrid / Specified Mutual Fund — slab rate)
- **Folio number:**
- **Total units:**
- **Current NAV / value / cost basis / purchase dates / SIP details / sub-portfolio / goal earmark:**

---

## 8. Government Schemes

### 8.1 PPF
For each PPF account in the household:
- **Account holder:** (user / father / mother / minor name)
- **Bank or post office:**
- **Account number:**
- **Account opening date:** YYYY-MM-DD
- **Maturity date (current 15-yr block):** YYYY-MM-DD
- **Current balance:** ₹
- **FY contributions to date (current FY):** ₹
- **Annual contribution (typical):** ₹
- **Extension status:** (initial 15-yr block / extended with contribution / extended without contribution)
- **80C claim FY-by-FY (Old Regime years):**
- **Sub-portfolio:**
- **Goal earmark:**
- **Notes:**

### 8.2 EPF / VPF
For the user (and any household member with EPF):
- **UAN:**
- **Current employer establishment ID:**
- **Current EPF balance (member portion):** ₹
- **Current EPF balance (employer portion):** ₹
- **Mandatory employee contribution rate:** 12% of (Basic + DA)
- **Current Basic + DA monthly:** ₹
- **VPF contribution rate (if any):** __% of (Basic + DA) — or ₹/month
- **YTD employee contribution (current FY):** ₹
- **Tax-free interest threshold:** ₹2.5L employee contribution per FY (verify YTD against threshold)
- **Prior employer EPF balances:** (consolidated y/n; UAN-linked y/n)
- **Sub-portfolio:**
- **Goal earmark:**
- **Notes:**

### 8.3 NPS Tier 1
For each PRAN holder:
- **Account holder:**
- **PRAN:**
- **Pension Fund Manager:**
- **Allocation choice:** (Active / Auto / Auto LC25/LC50/LC75)
- **If Active:** % E (equity), % C (corporate bonds), % G (govt securities), % A (alternative)
- **Current corpus:** ₹
- **Annual contribution (typical):** ₹
- **80CCD(1) claim history:**
- **80CCD(1B) claim history:**
- **Employer 80CCD(2) contribution:** (yes/no — amount/month)
- **Sub-portfolio:**
- **Goal earmark:**
- **Notes:**

### 8.4 NPS Tier 2 (if any)
- Similar structure to 8.3
- Tax benefits not available for private sector — generally not used by this household

### 8.5 Sukanya Samriddhi Account (SSY)
- **N/A** unless household has a daughter under 10
- If applicable: account holder (daughter), opening date, balance, annual contribution, maturity year

### 8.6 SCSS
- **N/A** until father becomes eligible at 60 (~2028)
- When applicable: account holder, deposit amount, deposit date, maturity date, interest rate at deposit, payout frequency

### 8.7 Post Office schemes
For each POMIS / NSC / KVP / Post Office RD / etc.:
- **Scheme:**
- **Account holder:**
- **Deposit amount:** ₹
- **Deposit date:** YYYY-MM-DD
- **Maturity date:** YYYY-MM-DD
- **Rate at deposit:** __%
- **Sub-portfolio:**
- **Goal earmark:**

---

## 9. Bonds

### 9.1 RBI Floating Rate Bonds
- **Holder:**
- **Investment amount:** ₹
- **Investment date:** YYYY-MM-DD
- **Maturity date:** YYYY-MM-DD (typically 7 years from issue)
- **Current rate:** __% (resets half-yearly, NSC + 35 bps)
- **Interest payout frequency:** half-yearly
- **Sub-portfolio / goal earmark / notes:**

### 9.2 Tax-free bonds
- **Issuer:**
- **Holder:**
- **Investment amount:** ₹
- **Coupon rate:** __%
- **Maturity date:**
- **Sub-portfolio / goal earmark / notes:**

### 9.3 Government securities (G-Sec) / SDLs / Corporate bonds
- For each: issuer, holder, face value, coupon, maturity, sub-portfolio, goal earmark

---

## 10. Gold

### 10.1 Sovereign Gold Bonds
For each tranche:
- **Tranche identifier:** (e.g., 2020-21 Series VII)
- **Issue date:** YYYY-MM-DD
- **Maturity date:** YYYY-MM-DD (8 years from issue)
- **Holder:**
- **Units (grams):**
- **Issue price per gram:** ₹
- **Current value:** ₹
- **Acquisition route:** (primary subscription / secondary market)
  > Note: tax exemption at maturity applies only to primary subscribers per current Budget rules (see `laws/gold.md`)
- **Interest payment dates:** (half-yearly from issue anniversary)
- **Premature redemption eligibility:** (5+ years from issue)
- **Sub-portfolio:**
- **Goal earmark:**
- **Notes:**

### 10.2 Gold ETFs
For each:
- **ETF name:**
- **Issuer (AMC):**
- **Folio / demat account:**
- **Units:**
- **Current NAV:** ₹
- **Current value:** ₹
- **Average purchase price:** ₹
- **First purchase date:** YYYY-MM-DD
- **Sub-portfolio / goal earmark / notes:**

### 10.3 Gold Mutual Funds (FoF)

#### Minimal mode (default)
Same seven-field row as equity MF (Section 5) — use the same table format. Add per-row sub-bullet:
- **Tax flag:** Specified Mutual Fund — slab rate

#### Heavy mode (opt-in only)
Add the full equity-MF heavy fields (Section 5.x-heavy): folio, total units, NAV, current value, average purchase NAV, total cost basis, first purchase date, most recent purchase date.

### 10.4 Digital gold
- **Platform:** (MMTC-PAMP / Augmont / SafeGold / etc.)
- **Holder:**
- **Quantity (grams):**
- **Average purchase price:** ₹/g
- **Current value:** ₹
- **Sub-portfolio / goal earmark:**

### 10.5 Physical gold
- **Jewellery total approximate value:** ₹ (held for utility/sentiment, not portfolio purposes per principles)
- **Investment-grade bullion / coins:** holder, purity, weight, current value, purchase date, sub-portfolio, goal earmark

---

## 11. Direct Equities

For each holding (per stock):
- **Company name:**
- **Listed exchange:** NSE / BSE
- **Holder:**
- **Demat account:**
- **Quantity:**
- **Current price:** ₹
- **Current value:** ₹
- **Average purchase price:** ₹
- **Total cost basis:** ₹
- **First purchase date:** YYYY-MM-DD
- **Sector:**
- **Sub-portfolio:**
- **Goal earmark:** (often `legacy` for dormant holdings)
- **Notes:** (e.g., "dormant since 2024", "received as IPO allotment", etc.)

### 11.x Direct equities summary
- Total value: ₹
- Number of stocks:
- Concentration: top 3 stocks = __%

---

## 12. Real Estate

### 12.1 Primary residence
- **Location:**
- **Approximate market value:** ₹
- **Year acquired:**
- **Holder(s):** (user / father / joint)
- **Home loan balance:** ₹ (or N/A)
- **Home loan rate:** __% (or N/A)
- **EMI:** ₹/month (or N/A)
- **Tenure remaining:** years
- **Sub-portfolio:** (typically a joint-locked sub-portfolio if defined in `user-principles.md`)

### 12.2 Investment property
- **Location:**
- **Type:** apartment / villa / commercial / plot
- **Year acquired:**
- **Holder(s):**
- **Approximate market value:** ₹
- **Annual rental income:** ₹ (gross)
- **Loan if any:** balance / rate / EMI / tenure
- **Sub-portfolio:**
- **Goal earmark:**

### 12.3 Plots / Agricultural land
- For each: location, area, holder, approximate value, year acquired, sub-portfolio, goal earmark

---

## 13. Insurance Assets

### 13.1 Term life insurance
For each policy:
- **Insurer:**
- **Policy number:**
- **Sum assured:** ₹
- **Annual premium:** ₹
- **Premium-paying party:** (self / spouse / parent / grandparent — important for 80C eligibility and continuity risk)
- **Policy start date:** YYYY-MM-DD
- **Policy end date / tenure:**
- **Riders:** (accidental death / critical illness / disability — list separately)
- **Notes:**

### 13.2 Health insurance
For each policy:
- **Insurer:**
- **Policy type:** (employer floater / individual / family floater / senior citizen / top-up / super top-up)
- **Sum assured:** ₹
- **Annual premium:** ₹
- **Premium-paying party:**
- **Insureds covered:**
- **Policy date:**
- **Riders / add-ons:** (critical illness / room rent waiver / no claim bonus etc.)
- **Notes:**

### 13.3 ULIPs / Endowment / Money-back / Traditional life
For each policy, if any:
- Policy details, surrender value, premium remaining, etc.

### 13.4 Critical illness / Disability standalone policies
For each, if any:
- Policy details

---

## 14. Liabilities (for net-worth completeness)

### 14.1 Loans
For each loan:
- **Loan type:** home / car / personal / education / credit-card-rollover / other
- **Lender:**
- **Original loan amount:** ₹
- **Current balance:** ₹
- **Interest rate:** __%
- **EMI:** ₹/month
- **Tenure remaining:** months
- **Holder (whose name):**

### 14.2 Credit card outstanding (revolving)
- For each card: bank, outstanding, APR if applicable

### 14.3 Other liabilities
- Anything else owed: family loans, deferred payments, etc.

---

## 15. Open Items / Flagged for Follow-up

(Auto-populate from any UNKNOWN field above. Each entry includes the source the user should consult to fill it in.)

- [ ] [Field] — [fetch from source] — [why it matters]

Examples:
- [ ] EPF prior employer consolidation status — fetch from UAN portal — needed to compute total EPF balance
- [ ] PPF account opening dates — fetch from PPF passbook — needed for maturity date computation
- [ ] Specific direct equity purchase prices — fetch from broker capital gains statement — needed for cost basis on potential sale

---

## 16. Reconciliation Notes

(Tensions surfaced during the grilling and how the user resolved them.)

- **Tension:** [e.g. goals.md said ₹50L emergency FD, file captures ₹47L FDs total — ₹3L gap]
  **Resolution:** [e.g. "User confirmed remaining ₹3L is in sweep-FD on savings account, recategorised under Section 2.1"]

---

## 17. Schema Limitations & To-Do for v2

- **Per-folio summary only.** Partial-redemption tax math will require transaction-level data. When tax-check encounters this need, generate `transactions.csv` companion file from CAS or manual entry.
- **No mark-to-market history.** This file is a snapshot. Historical NAV / unit values are not retained — fetch fresh on each portfolio review.
- **Real estate valuation is approximate.** Updated annually at most, no professional valuation captured.
- **Insurance lapse / premium status not tracked.** Manual check-in via portfolio-review skill.

---

## Appendix — How to use this file

This file is the holdings layer for the investment agent. Downstream skills read from here:
- **`portfolio-review`** uses Sections 1-13 to compute current allocation, drift vs target, and goal progress
- **`fund-allocate`** uses Section 1 (sub-portfolio split) and the per-scheme details for routing decisions
- **`tax-check`** uses per-holding cost basis and dates to compute capital gains; flags when transaction-level detail is required

Re-run `portfolio-grill` (full or partial) after any of these triggers:
- New SIP started or stopped
- Lump sum invested
- Redemption or switch
- Material change in PPF/NPS/EPF/VPF contribution
- New insurance policy
- Property transaction
- Every 3 months as a routine refresh (just to update current values)
- After any goals.md re-grill that changes sub-portfolio assignment logic
```

## TEMPLATE ENDS ABOVE THIS LINE
