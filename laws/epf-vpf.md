# laws/epf-vpf.md

last_updated: 2026-05-03
last_verified_against_budget: Union Budget 2026
covers: Employees' Provident Fund (EPF), Voluntary Provident Fund (VPF), tax thresholds

---

## 1. Current interest rate

- **EPF rate for FY 2024-25: 8.25%** (declared by EPFO Central Board of Trustees, approved by Ministry of Finance)
- **EPF rate for FY 2025-26: VERIFY** — typically declared in Feb-Mar 2026 by EPFO; if not yet declared at time of reading, the prior year's rate is the conservative assumption
- VPF earns the same rate as EPF (it's the same pool)
- Compounded annually, credited at the end of the financial year

> **Action item for laws-refresh:** check EPFO's most recent rate announcement — usually published as a press release on epfindia.gov.in around February-March each year for the just-ended FY, and around April-May for the upcoming FY.

---

## 2. EPF — basic structure

### 2.1 Mandatory contribution structure
For salaried employees in establishments with 20+ employees (and some with fewer):

- **Employee contribution:** 12% of (Basic Salary + Dearness Allowance)
- **Employer contribution:** 12% of (Basic + DA), split as:
  - 8.33% goes to EPS (Employees' Pension Scheme) — capped at ₹1,250/month based on ₹15,000 wage ceiling for EPS
  - 3.67% (or balance) goes to EPF
- All amounts are deposited monthly to the employee's UAN-linked EPF account

### 2.2 Voluntary contributions (VPF)
- Employee can contribute **above the mandatory 12%**, up to **100% of (Basic + DA)** as VPF
- Employer is NOT obligated to match VPF contributions (only mandatory 12% gets matched)
- VPF earns the same rate as EPF
- Contributions are entirely voluntary and can be started/stopped through the employer

---

## 3. Tax treatment

### 3.1 Contribution (deposit phase)

Both Old and New Regime:
- **Employer's 12% contribution to EPF** is exempt from tax in employee's hands up to the combined ₹7.5 lakh annual cap (EPF + NPS-80CCD(2) + superannuation). Above ₹7.5L combined, the excess is taxable in the year of contribution.

Old Regime only:
- **Employee's contribution to EPF + VPF** counts toward 80C ₹1.5L deduction (alongside PPF, ELSS, etc.)
- Combined 80C cap is ₹1.5L — so EPF + PPF + ELSS + insurance + tuition fees + home loan principal cannot exceed ₹1.5L total deduction

New Regime:
- Employee's own contribution gets no deduction
- Only the employer's 12% remains exempt (subject to ₹7.5L cap)

### 3.2 Interest accrual phase — the ₹2.5 lakh threshold rule (very important)

Since FY 2021-22, interest on employee's contributions to EPF/VPF is taxable if the contributions exceed certain thresholds:

- **₹2.5 lakh per FY** for contributions to EPF + VPF (employee contribution only) — applies to private-sector employees and most others
- **₹5 lakh per FY** if there is no employer contribution (i.e., government/PF schemes where employer doesn't contribute)
- Interest on contributions **above the threshold** is taxable as "Income from Other Sources" at slab rate
- Interest on contributions **up to the threshold** remains tax-free

**Practical implication for VPF in this household:**
- User's mandatory EPF contribution = 12% × Basic. If user's basic is ₹40,000/month, mandatory employee EPF = ₹57,600/year. Headroom under ₹2.5L threshold = ₹1,92,400.
- VPF up to that headroom continues to enjoy fully tax-free interest under EEE.
- VPF beyond ₹2.5L total contribution: interest on excess becomes taxable at slab — partially erodes VPF's advantage but not destructively. At 30% bracket, post-tax yield on excess VPF is still ~5.8% (compared to ~5.2% on liquid debt MF), so still better than alternatives.

### 3.3 Withdrawal phase

Tax-free if withdrawn:
- After 5 years of continuous service (counts across employers if UAN is consolidated)
- On retirement after age 58
- Due to disability or termination by employer for reasons beyond employee's control

Taxable (TDS at 10% if withdrawal > ₹50,000):
- If service less than 5 years and withdrawal happens (e.g. job change without transfer)
- Cumulative tax: previously claimed 80C deductions are reversed (added to current year income), employer contribution treated as salary in year of withdrawal, interest taxed in year accrued, employee contribution returned tax-free

**Practical:** Keep UAN consolidated across job changes. Don't withdraw EPF on job change — transfer instead. The 5-year clock continues across employers if you transfer the balance.

---

## 4. UAN and consolidation

- Universal Account Number (UAN) is permanent and links all EPF accounts across employers
- Consolidation should happen on every job change to maintain continuous service period
- Online consolidation via member.epfindia.gov.in
- Per `goals.md` Section 9 — UAN active is confirmed but consolidation status with prior employers not probed; verify during portfolio.md construction

---

## 5. Premature withdrawal options (without leaving job)

- For self-marriage, child's marriage, sibling's marriage: up to 50% of employee's contribution + interest, allowed after 7 years of service
- For child's higher education: same 50% rule, after 7 years
- For house construction/purchase: up to 36 months of basic+DA, after 5 years of service
- For medical emergency (self/family): no waiting period, employee contribution + interest
- Pre-retirement (age 54): up to 90% of total balance for retirement preparation

These are partial withdrawals; account remains open. Don't trigger tax events on amounts under the 5-year threshold.

---

## 6. Operational mechanics for this household

For the user (salaried with EPF + employer match per `goals.md`):

### 6.1 VPF capacity assessment
- User's basic salary share of ₹20L gross — check actual basic component (typical structures put basic at 30-50% of gross)
- Mandatory EPF on that basic
- VPF can scale up to 100% of basic+DA additionally
- Total EPF+VPF should ideally stay ≤ ₹2.5L/FY to keep all interest tax-free
- Beyond ₹2.5L, partial taxation kicks in but the wrapper remains attractive

### 6.2 Comparison to PPF (Section 4.4 of `regime-comparison.md` complement)

| Feature | PPF | EPF/VPF |
|---|---|---|
| Current rate | 7.1% | 8.25% (FY 2024-25); FY 2025-26 to verify |
| Lock-in | 15 years | Till retirement / job change |
| 80C eligible (Old Regime) | Yes | Yes (within ₹1.5L combined cap) |
| New Regime deduction | None | Employer's 12% still exempt up to ₹7.5L cap |
| Threshold for tax-free interest | None | ₹2.5L employee contribution/yr |
| Liquidity | Partial after year 7 | Limited; transfer on job change |
| Eligible for father (business owner) | Yes | No (only salaried with PF establishment) |
| Practical use for this user | All eligible household members | User's salaried route |

**Implication:** VPF up to the ₹2.5L threshold is a stronger first deployment than PPF for the user (higher rate, salaried convenience). Beyond ₹2.5L, marginal benefit erodes; PPF takes over. For father, PPF is the only option (no EPF without formal employment).

### 6.3 Suggested deployment sequence (under Old Regime, if chosen)
1. Mandatory EPF (already happening)
2. VPF up to the ₹2.5L threshold for fully tax-free interest
3. PPF for both user and father (₹1.5L each)
4. NPS Tier 1 for additional ₹50K 80CCD(1B) deduction

Under New Regime:
1. Mandatory EPF (already happening)
2. VPF up to ₹2.5L threshold (still tax-free interest, no 80C benefit)
3. NPS only if employer offers 80CCD(2) route (worth pursuing if available)
4. PPF for tax-free growth even without deduction

---

## 7. Operational status for this household

Per `goals.md` Section 3.4:
- EPF balance ₹1.5L, employer-matched
- No VPF currently → significant unused capacity at low friction
- UAN active

Per `goals.md` Section 9 open items:
- Confirm prior employer consolidation status
- Confirm whether basic salary supports the contemplated VPF scaling

---

## Sources / verification

- Employees' Provident Funds and Miscellaneous Provisions Act, 1952
- Section 10(11), Section 10(12), Section 80C of the Income Tax Act
- Finance Act 2021 — introduced ₹2.5L employee contribution threshold for taxable interest
- Finance Act 2023 — confirmed ₹7.5L combined employer contribution cap (EPF + NPS + superannuation)
- EPFO website: https://www.epfindia.gov.in
- For latest interest rate, check EPFO press releases on the above site
