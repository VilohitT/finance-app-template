# laws/equity-mf.md

last_updated: 2026-05-03
last_verified_against_budget: Union Budget 2026
covers: Equity-oriented mutual funds, ELSS, hybrid (equity-oriented) MFs

---

## 1. Definition — what counts as "equity-oriented" for tax

A scheme qualifies as equity-oriented for tax purposes if it invests **at least 65% of its total proceeds in equity shares of domestic companies**. The 65% test is on a daily-average basis through the year per SEBI/AMFI norms.

**Categories that typically qualify:**
- Large-cap, mid-cap, small-cap, multi-cap, flexi-cap, focused funds
- ELSS (always equity)
- Aggressive Hybrid Funds (≥65% equity by mandate)
- Equity Savings Funds (typically ≥65% equity if they meet the test, but check fund-specific composition)
- Sectoral / thematic funds (if invested in domestic equity)

**Categories that may or may not qualify — check fund factsheet:**
- Balanced Advantage / Dynamic Asset Allocation: equity component flexes; tax classification depends on actual equity exposure averaged
- Multi-asset allocation funds: depends on equity proportion; many sit between 35-65% (treated as Section 112 hybrid, not equity)
- International funds: typically classified as non-equity for tax even if they invest in foreign equity, because the 65% test specifies *domestic* equity

**Practical:** AMFI's published category, fund factsheet's "Tax treatment" line, and CAS / capital gains statement label the gain type. The agent verifies against fund factsheet during fund selection.

---

## 2. STCG (holding ≤ 12 months)

- **Rate:** 20% (Section 111A) — was 15% pre-23-Jul-2024
- Plus 4% cess
- Plus surcharge as applicable (capped at 15% for equity STCG even at very high incomes)
- Available against STCL set-off

---

## 3. LTCG (holding > 12 months)

- **Rate:** 12.5% (Section 112A) — was 10% pre-23-Jul-2024
- **Annual exemption:** ₹1.25 lakh (was ₹1L pre-23-Jul-2024)
- Per financial year, per PAN, aggregate across all equity LTCG sources
- No indexation
- Plus 4% cess and surcharge (cap 15%)

---

## 4. ELSS — special rules

- **Lock-in: 3 years from each individual purchase / SIP installment.** Each SIP installment has its own 3-year clock.
- **Eligible for Section 80C deduction up to ₹1.5L** (within overall 80C limit), **only under Old Tax Regime**
- **No deduction under New Tax Regime** — ELSS effectively becomes a regular equity fund with a lock-in
- After lock-in: gains are LTCG (since holding > 1 year by definition), taxed at 12.5% above ₹1.25L exemption
- **Implication:** in the New Tax Regime, ELSS offers no tax advantage over a regular equity fund — and has the disadvantage of the 3-year lock-in. Only invest in ELSS if you're on Old Regime AND the 80C bucket isn't already filled by other means (PPF, EPF, term insurance premium, etc.).

---

## 5. SIP taxation — first-in-first-out (FIFO)

For SIPs, each installment has its own purchase date and cost basis. On redemption:
- **FIFO method** is applied — earliest purchases redeemed first
- Each installment's holding period is computed independently
- Some installments may be LTCG, others STCG, in a single redemption event
- The CAS and broker capital gains statements break this down automatically

**Practical:** when stopping or switching a long-running SIP, the LTCG-eligible portion can be redeemed first to use the ₹1.25L exemption efficiently; the STCG-only portion (newer installments) can be deferred until they cross 12 months.

---

## 6. Switching, Direct vs Regular, dividend reinvestment

- **Switching between schemes** (even within the same AMC) = redemption of old scheme + fresh purchase of new scheme. Triggers capital gains. Holding period and cost basis on the new scheme starts fresh.
- **Switching from Regular to Direct plan** = same as above. A common trap: investors think they're "just upgrading" but it's a tax event.
- **Dividend / IDCW reinvestment** = each reinvestment counts as a fresh purchase with its own cost basis and 12-month clock. Dividend itself is taxed at slab rate before reinvestment.
- **Growth option** (no dividends) — recommended over IDCW for tax efficiency; AMFI now requires explicit option choice at investment.

---

## 7. Dividend (IDCW) taxation

- Dividend Distribution Tax (DDT) abolished from FY 2020-21
- Dividends are now taxed in the **investor's hands at slab rate** (under "Income from Other Sources")
- TDS at 10% if dividend from a single AMC > ₹10,000 in a financial year (raised from ₹5,000 in Budget 2025)
- TDS is not the final tax — must be reconciled at ITR filing
- Dividends are not eligible for the ₹1.25L LTCG exemption (different head of income)

**Implication:** Growth option dominates IDCW for almost all investors. IDCW only makes sense for someone who needs the income stream and is in a low slab.

---

## 8. Exit load

- Most equity funds have an exit load if redeemed within 1 year (typically 1%)
- Specific rates vary by fund and category — check fund factsheet
- ELSS has no exit load after the 3-year lock-in, since pre-lock-in redemption isn't possible
- Exit load is deducted from the redemption amount and is not a tax (the post-load amount is what triggers the capital gains computation)

---

## 9. Loss harvesting (LTCL / STCL on equity MFs)

- **STCL** can be set off against STCG and LTCG (both equity and non-equity)
- **LTCL** can be set off only against LTCG (equity or non-equity)
- Both can be carried forward 8 assessment years (ITR must be filed by the due date)
- For an equity LTCG sale, LTCL is applied **before** the ₹1.25L exemption — so loss harvesting reduces taxable LTCG below the threshold rather than just reducing tax above it

---

## 10. Specific disclosures the agent uses

When running a tax check on an equity MF transaction, the agent needs:
- Fund category (to verify equity-oriented for tax)
- Purchase date (for holding period)
- Purchase NAV / cost basis (for gain computation)
- Sale date and NAV (for sale proceeds)
- Exit load applied (for net proceeds)
- Cumulative LTCG used in current FY (to apply remaining ₹1.25L exemption)
- ELSS-specific: lock-in expiry date for the relevant tranche

These come from the user's CAS / KFintech / CAMS statements, which `portfolio.md` is meant to track.

---

## Sources / verification

- Section 111A (equity STCG), Section 112A (equity LTCG), Section 80C (ELSS deduction)
- Finance (No. 2) Act, 2024 — rate revisions
- AMFI categorisation rules: https://www.amfiindia.com
- SEBI MF categorisation circular (see `sebi-categories.md`)
