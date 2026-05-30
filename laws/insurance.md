# laws/insurance.md

last_updated: 2026-05-03
last_verified_against_budget: Union Budget 2026
covers: Term life, health insurance, ULIPs, 80C / 80D / Section 10(10D) provisions

> **Per goals.md:** the user has elected to not push protection insurance further, accepting residual risk (Tension 4). This file captures the rules; the agent does not recommend protection products absent a triggering event per `principles.md` Section 7.

---

## 1. Term life insurance

### 1.1 Premium deduction
- **Section 80C:** premium counts toward overall ₹1.5L 80C limit (Old Regime only)
- **New Regime: no deduction** — paying full premium from post-tax income
- Conditions: premium must not exceed 10% of sum assured for policies issued on or after 1 April 2012 (else limited deduction)

### 1.2 Death benefit (payout to nominee)
- **Tax-free under Section 10(10D)** in nominee's hands
- Both regimes
- No upper limit on the tax-free death benefit
- Term insurance death benefits are universally tax-exempt

### 1.3 Maturity benefit
- For pure term insurance: there is no maturity benefit (policyholder survives → no payout, premiums forfeited as cost of cover)
- Section 10(10D) doesn't even come into play for pure term

### 1.4 Operational notes for this household

User's existing cover (per goals.md Section 4):
- ICICI Prudential pure term, ₹2 Cr sum assured, ₹25K/year premium, 25 years remaining
- Premium paid by grandparents — flagged for continuity
- **80C deduction implication:** even though grandparents pay, the user is the proposer and policyholder. If the user is on Old Regime AND wants to claim 80C, they would need to be the one paying. Currently they're not, so no 80C claim is being made. If grandparents pay, no one claims 80C on this premium (grandparents may not need it, user can't claim what they didn't pay).

### 1.5 Common pitfalls
- "Money-back" or "endowment" policies marketed as life insurance: these are bundled investment products with poor returns — covered separately below
- Riders attached to term policies (accidental death, critical illness): may have separate deduction treatment under different sections
- Sum assured ratio: <10x annual income is generally underinsured for someone with dependents — `principles.md` flags this only in user-initiated review, not proactively

---

## 2. Health insurance

### 2.1 Premium deduction — Section 80D (Old Regime only)

| Beneficiary | Maximum deduction |
|---|---|
| Self + spouse + dependent children (all < 60) | ₹25,000 |
| Self / spouse > 60 (senior citizen) | ₹50,000 |
| Parents (< 60) | ₹25,000 (additional) |
| Parents (≥ 60, senior citizens) | ₹50,000 (additional) |
| Combined cap if self AND parents are senior citizens | ₹1,00,000 |

- **Preventive health check-up** counts within these limits up to ₹5,000
- **New Regime: no 80D deduction** — premiums paid from post-tax income

### 2.2 Claim payout / reimbursement
- Hospitalisation reimbursements / cashless settlements are **not taxable** in either regime
- The insurer pays the hospital directly (cashless) or reimburses the policyholder — neither is treated as income

### 2.3 For this household

User's situation per goals.md Section 4:
- Employer group floater covers user, father, mother (sum assured unknown — flagged for follow-up)
- **No personal (non-employer) cover** — single point of failure on job change
- No critical illness rider, no disability cover
- Father: military/ECHS coverage in addition to employer floater

**80D potential under Old Regime:**
- If user opens a separate health policy for parents (mother already + father with ECHS): ₹50K under 80D for senior parents (father turns 60 in 2028; until then may be < 60)
- This is one of the levers that makes Old Regime more attractive for the household — but only if user actually buys parental cover. Per goals.md Tension 4, user has elected not to.

### 2.4 80D and parents — operational note

If the user later changes course and buys parental cover:
- Cover purchased by user, claimed against user's income → 80D deduction in user's filing (Old Regime)
- Premium does NOT need to be funded from user's income to claim — what matters is who pays the premium and whose income the deduction is sought against. Parents themselves cannot claim if they don't pay, even if they're the insured.
- Cashless settlement to hospital still tax-free regardless of who paid premium

This routing (user pays parental health premium for 80D under Old Regime) is one of the few clear Old Regime advantages remaining, depending on how the regime decision lands.

---

## 3. ULIPs (Unit Linked Insurance Plans)

### 3.1 Structure
- Bundles life insurance with market-linked investment
- Premium split between mortality charges (the cover) and investment (debt/equity/balanced funds)
- Various charges: premium allocation charge, policy admin charge, fund management charge, mortality charge — historically high, now somewhat moderated by IRDAI rules
- 5-year minimum lock-in period

### 3.2 Tax treatment

#### Premium deduction
- **Section 80C** under Old Regime (within ₹1.5L combined cap), if premium ≤ 10% of sum assured
- New Regime: no deduction

#### Maturity benefit
Pre-Budget 2021 ULIPs:
- Section 10(10D) — fully tax-free if premium ≤ 10% of sum assured

Post-Budget 2021 ULIPs (issued on/after 1 February 2021):
- **Section 10(10D) tax-free only if total annual premium across all ULIPs ≤ ₹2.5 lakh**
- If total annual ULIP premium exceeds ₹2.5L cumulatively across policies issued post-1-Feb-2021, the maturity gain is treated as **capital gain** at applicable rate (12.5% LTCG for equity ULIPs after 12 months; STCG slab rate within 12 months)
- This effectively closed a tax-arbitrage loophole where high-income investors used ULIPs to shelter equity gains

### 3.3 For this household

**No ULIPs currently held.** Per goals.md Section 3.8, no ULIPs/endowment/money-back/traditional. `principles.md` Section 3.3 says: never recommended.

This file's ULIP section exists only to support the agent if a future flag arises (e.g. user is offered a ULIP and asks about it — agent can explain the rules and trade-offs without needing fresh research).

---

## 4. Endowment, money-back, traditional savings policies

- Bundle protection + savings; fixed return promises (~4-6% IRR typically — comparable to FD post-tax but with a long lock-in)
- Premium under 80C (Old Regime) up to ₹1.5L cap, conditional on premium ≤ 10% of sum assured
- Maturity: tax-free under Section 10(10D) if premium ≤ 10% of sum assured (irrespective of date of issue)
- **Generally underperform on every dimension vs term + separate investments**
- **Not recommended.** Per `principles.md` Section 3.3, never.

This household has none. File section retained as reference only.

---

## 5. Critical illness and disability riders / standalone policies

### 5.1 Standalone Critical Illness (CI) plans
- Pay a lump sum on diagnosis of specified illness (cancer, heart attack, stroke, etc.)
- Premium under 80D up to ₹25K (within or in addition to the regular health premium, depending on policy structure — most insurers structure CI as an add-on or separate health policy)
- Payout: tax-free in nominee's / policyholder's hands (treated like a health insurance claim)
- New Regime: no 80D deduction at premium

### 5.2 Disability income / loss-of-income cover
- Pay monthly income if policyholder becomes disabled and cannot work
- Premium tax treatment: under 80D as health-related (if structured as a health rider) or 80U if structured as disability-specific (the 80U deduction is for disabled persons themselves and is separate from premium)
- Payout: typically tax-free per Section 10(10D) if structured as life insurance; treated as health benefit if a health-rider claim

### 5.3 Status for this household

Neither product is held. User has elected not to acquire (Tension 4). File section retained for reference.

---

## 6. Premium continuity flag — user's term insurance

Per goals.md Section 9, ICICI Pru ₹2 Cr term policy premium is currently paid by grandparents. If grandparents stop paying:

- Policy will lapse if premium is not paid by due date + grace period (typically 30 days for annual mode; 15 days for shorter modes)
- Reinstatement is possible but typically requires a fresh medical underwriting if lapsed for >6 months — rates may be revised upward
- For the user, switching to paying the premium themselves shifts ₹25K/year from grandparents' cash flow to user's

**Not a tax issue per se** — it's a continuity-of-cover issue. The agent flags this in the open-items list of any review where Section 4 / Section 9 of goals.md are referenced.

---

## Sources / verification

- Section 80C, 80D, 80DD, 80U of the Income Tax Act
- Section 10(10D) — life insurance proceeds exemption
- Section 10(10A) — pension commutation exemption
- Finance Act 2021 — introduced the ₹2.5L ULIP cap for tax-free maturity
- IRDAI website: https://www.irdai.gov.in
- For specific policy / premium details, refer to actual policy documents — these supersede any summary
