# laws/regime-comparison.md

last_updated: 2026-05-03
last_verified_against_budget: Union Budget 2026
covers: Old vs New tax regime — slabs, rebate, deductions, and decision logic for the household

> **For this household:** annual regime decision is overdue per goals.md Section 9. This file gives the rules; `tax-check` does the actual arithmetic against current household profile.

---

## 1. New Tax Regime (Default for individuals from FY 2023-24)

### 1.1 Slab structure (FY 2025-26 / AY 2026-27)
Set under Section 115BAC(1A), unchanged in Budget 2026.

| Income | Rate |
|---|---|
| Up to ₹4,00,000 | Nil |
| ₹4,00,001 – ₹8,00,000 | 5% |
| ₹8,00,001 – ₹12,00,000 | 10% |
| ₹12,00,001 – ₹16,00,000 | 15% |
| ₹16,00,001 – ₹20,00,000 | 20% |
| ₹20,00,001 – ₹24,00,000 | 25% |
| Above ₹24,00,000 | 30% |

Same slabs apply regardless of age (no separate slab benefit for senior or super-senior citizens under the new regime).

### 1.2 Section 87A rebate (FY 2025-26 onward)
- **Up to ₹60,000 rebate** for resident individuals with taxable income ≤ ₹12 lakh
- Effectively makes total income up to ₹12L tax-free
- **Marginal relief** kicks in for income marginally above ₹12L: tax payable ≤ amount by which income exceeds ₹12L. Practical effect: tax on ₹12.1L is ₹10,000 (not ₹61,500). Marginal relief disappears around ₹12.75L; beyond that, full slab rates apply.
- Not available for NRIs
- Not available against income taxed at special rates (LTCG, STCG on equity, lottery, crypto, etc.)

### 1.3 Standard deduction (salaried only)
- **₹75,000** flat (was ₹50,000 before Budget 2025)
- Available under both old and new regime for salaried income; new regime grants ₹75K, old grants ₹50K
- Effectively makes salaried income up to ₹12,75,000 tax-free under the new regime (₹12L rebate ceiling + ₹75K standard deduction)

### 1.4 What is allowed under New Regime
- Section 80CCD(2) — employer's NPS contribution up to **14% of (basic + DA)** for all employees (govt and private alike, post Budget 2024). Combined cap with EPF + superannuation = ₹7.5L/year aggregate.
- Section 24(b) interest deduction on let-out (rented) property loans
- Family pension deduction up to ₹25,000 (raised from ₹15,000 in Budget 2024)
- Standard deduction ₹75K (salaried)
- Marginal relief and rebate as above

### 1.5 What is NOT allowed under New Regime
- Section 80C (PPF/EPF/ELSS/life insurance/principal home loan/etc. — all ₹1.5L deductions)
- Section 80CCD(1) — own NPS contribution (10% of salary or ₹1.5L)
- Section 80CCD(1B) — additional ₹50K NPS deduction
- Section 80D — health insurance premium deduction
- HRA exemption (Section 10(13A))
- LTA (Section 10(5))
- Section 80E — education loan interest
- Section 80EEA / 80EE — additional home loan interest deductions
- Section 24(b) interest deduction on **self-occupied** property (allowed only for let-out)
- 80TTA / 80TTB — savings interest deductions
- Most other deductions under Chapter VI-A

---

## 2. Old Tax Regime

### 2.1 Slab structure (FY 2025-26 / AY 2026-27, no change in Budget 2026)

For individuals < 60:
| Income | Rate |
|---|---|
| Up to ₹2,50,000 | Nil |
| ₹2,50,001 – ₹5,00,000 | 5% |
| ₹5,00,001 – ₹10,00,000 | 20% |
| Above ₹10,00,000 | 30% |

For senior citizens (60–79): basic exemption ₹3,00,000.
For super senior citizens (80+): basic exemption ₹5,00,000.

### 2.2 Section 87A rebate
- Up to **₹12,500** for taxable income ≤ ₹5 lakh

### 2.3 Standard deduction (salaried only)
- **₹50,000** flat (unchanged in Budget 2025/2026)

### 2.4 Major deductions available under Old Regime
- **Section 80C** — up to ₹1.5L combined: PPF, EPF, VPF, ELSS, NSC, SCSS principal, life insurance premium, principal home loan repayment, tuition fees, ULIP premium (cap conditions apply), Sukanya Samriddhi, post office time deposit (5-yr)
- **Section 80CCD(1B)** — additional ₹50K for NPS Tier 1 contribution beyond the 80C ₹1.5L
- **Section 80CCD(2)** — employer NPS contribution up to **10% of salary (basic+DA) for private sector / 14% for government sector under old regime** — note the asymmetry vs new regime
- **Section 80D** — health insurance premium: ₹25K for self+family (₹50K if senior citizen self), additional ₹25K for parents (₹50K if parents are senior citizens). Total cap ₹1L if both self and parents are seniors. Includes preventive health check-up up to ₹5K within these limits.
- **Section 80E** — interest on education loan (no upper limit, available 8 years from start of repayment)
- **Section 80G** — donations to specified funds
- **Section 24(b)** — home loan interest on self-occupied: up to ₹2L. On let-out: full interest deductible (with ₹2L cap on overall house property loss carry-forward).
- **Section 80EEA** — additional ₹1.5L home loan interest for first-time buyers (conditions apply)
- **HRA** under Section 10(13A) — least of (actual rent paid – 10% of basic salary, 50% of basic in metros / 40% non-metro, actual HRA received)
- **LTA** under Section 10(5) — twice in a block of 4 calendar years, for domestic travel

### 2.5 Surcharge under Old Regime
Higher than new regime at upper end:
| Total income | Surcharge |
|---|---|
| > ₹50L ≤ ₹1Cr | 10% |
| > ₹1Cr ≤ ₹2Cr | 15% |
| > ₹2Cr ≤ ₹5Cr | 25% |
| > ₹5Cr | 37% |

(In contrast, new regime caps surcharge at 25% for incomes above ₹2Cr.)

---

## 3. Health & Education Cess (both regimes)
**4%** on (tax + surcharge). Universal.

---

## 4. Choosing the regime — operational rules

### 4.1 Eligibility to switch
- **Salaried + no business income:** can choose either regime each financial year, declared at ITR filing time.
- **Business income:** can opt out of new regime once, but switching back is restricted; effectively a one-time choice.

### 4.2 Default
New regime is the default unless specifically opted out at ITR filing.

### 4.3 The household's structural decision factors

For this household specifically (per goals.md):

**Old regime gets attractive when:**
- 80C is fully used: ₹1.5L total possible across PPF (user) + PPF (father) + ELSS + insurance premiums + EPF
- 80CCD(1B): another ₹50K via NPS Tier 1 (user)
- 80D: ₹25K self + family, ₹50K parents (since parents are seniors / father turns 60 in 2028) = up to ₹75K
- 80CCD(2): up to 10% of basic+DA via employer NPS — hits max ~₹2L if employer offers it on user's basic
- HRA exemption — only relevant if user pays rent (currently lives in owned residence per goals.md, so HRA = N/A)
- Total potential deductions accessible: roughly ₹4L+ for the user's own filing under old regime

**New regime gets attractive when:**
- The user has no significant deductions to claim (minimal investments, no rent paid, no parental health premium, etc.)
- The user prefers simplicity over the optimisation grind
- Income is below ₹12.75L (then 0 tax under new regime regardless; old regime can also achieve 0 tax with deductions but requires effort)

### 4.4 Decision logic for `tax-check` to apply (rough — verify with actual numbers)

For the user (₹20L salary, projected to ₹80L):

**At ₹20L salary, user-only filing:**
- New regime tax (after standard deduction ₹75K → taxable ₹19.25L):
  - 4-8L: 5% = ₹20K
  - 8-12L: 10% = ₹40K
  - 12-16L: 15% = ₹60K
  - 16-19.25L: 20% × 3.25L = ₹65K
  - Subtotal: ₹1.85L + 4% cess = ₹1.92L
- Old regime tax with full deductions (₹2L 80C+80CCD(1B), ₹75K 80D, ₹50K standard ded, ₹2L employer NPS 80CCD(2)) — taxable = 20L – 5.25L = 14.75L:
  - 0-2.5L: 0
  - 2.5-5L: 5% = ₹12.5K
  - 5-10L: 20% = ₹1L
  - 10-14.75L: 30% × 4.75L = ₹1.42L
  - Subtotal: ₹2.55L + 4% cess = ₹2.65L
- **Old regime is worse for the user at ₹20L** because the slab penalty (30% from ₹10L vs new regime's 30% only from ₹24L) overwhelms the deductions.
- **At ₹80L salary, the gap likely tilts: with ₹5.25L deductions plus surcharge differences, old regime could become competitive.** Re-run yearly.

**At ₹80L (projected 2029):**
- Direct comparison must be re-run with then-applicable rules. Likely new regime still wins because the slab compression (30% only above ₹24L) provides massive headroom that even ₹5.25L of deductions can't beat below a certain corpus.
- **The breakpoint where old regime overtakes new regime for this household, with full deductions used, is somewhere in the ₹35-50L individual income range.** Approximate; needs precise modelling at the moment of decision.

**The agent's default assumption was that old regime wins for this household. This calculation suggests the opposite — new regime is likely better for the user's individual filing at current income levels.** Important update for principles.md and the routing logic in any recommendation that depends on regime.

### 4.5 Routing flexibility doesn't change individual regime decisions
Each filer (user / father) chooses their own regime separately. Routing of contributions to PPF/NPS/etc. only matters if those contributions actually deliver a deduction, which under new regime they don't (except 80CCD(2) which requires employer participation).

For father (business income): regime choice depends on his business income deductions and other factors; out of scope for this file. The father's regime decision is its own annual review.

---

## 5. Income Tax Act 2025 — what's coming

The new Income Tax Act 2025 was passed and comes into effect from **1 April 2026**. It replaces the Income Tax Act 1961. Key implications:

- Section numbers will renumber (e.g., 80C provisions move to a new section identifier; 80CCD provisions move to Section 124 in the new act)
- The agent should expect transitional ambiguity through FY 2026-27 — old section references in returns vs new section references in current law
- For ITR for FY 2025-26 (filed July 2026), old IT Act 1961 sections apply
- Substantive changes are minimal in this transition; mostly a re-organisation and language cleanup

---

## Sources / verification

- Finance Act 2025 (Union Budget 2025) — major changes: rebate ₹60K, slabs revised under new regime, basic exemption ₹4L
- Finance Act 2026 (Union Budget 2026) — no changes to rates
- Income Tax Department FAQs on Budget 2025: https://incometaxindia.gov.in/Documents/Budget/budget-2025/faqs-budget-2025.pdf
- Section 115BAC(1A) for the new regime statutory basis
- Section 87A for the rebate
