# laws/debt-mf.md

last_updated: 2026-05-03
last_verified_against_budget: Union Budget 2026
covers: Debt mutual funds — three different tax treatments based on purchase and sale date

> **The most error-prone area in MF taxation.** Three different regimes apply to debt MFs depending on when units were purchased and when they were sold. Mistakes here are common and material.

---

## 1. Three regimes for debt MF capital gains

### Regime A: Purchased before 1 April 2023, sold before 23 July 2024 (mostly historical now)
- **LTCG threshold:** > 36 months
- **LTCG rate:** 20% with indexation (cost adjusted using CII)
- **STCG:** ≤ 36 months → slab rate
- This regime applied to legacy holdings sold before the Budget 2024 changes. Now mostly closed for new transactions.

### Regime B: Purchased before 1 April 2023, sold on/after 23 July 2024 (transitional rule)
- **LTCG threshold:** > 24 months (reduced from 36)
- **LTCG rate:** 12.5% **without indexation** (Section 112)
- **STCG:** ≤ 24 months → slab rate
- This regime applies to legacy holdings that the user still has. Sale post-23-Jul-2024 with original purchase pre-1-Apr-2023.
- **Indexation benefit was available for property pre-23-Jul-2024 by resident individuals/HUF, but NOT for debt MFs.** Debt MFs lose indexation regardless.

### Regime C: Purchased on/after 1 April 2023 (Specified Mutual Fund — Section 50AA)
- **All gains taxed at slab rate**, regardless of holding period
- No LTCG concept applies
- No 12.5% rate
- No ₹1.25L exemption (which is equity-only anyway)
- Effectively, debt MFs purchased after 1 April 2023 are taxed like a recurring deposit / FD interest at slab rate

**Specified Mutual Fund definition:** A mutual fund where invested in equity ≤ 35% of total proceeds. Includes:
- All standard debt funds (liquid, ultra-short, short duration, corporate bond, gilt, banking & PSU, dynamic bond, credit risk)
- Gold MFs / Gold ETF FoFs (may classify here depending on structure)
- International funds (treated as non-equity for tax)
- Fund-of-funds investing in non-equity
- Market-Linked Debentures (MLDs)

---

## 2. Holding-period tracking for debt MF holdings

For the user's existing ₹10L debt MF holding (per goals.md Section 3.2 — "short-term debt fund(s) at Bandhan Bank"):
- Purchase date determines which Regime applies
- If purchased after 1 April 2023 (likely given user is 24 and started investing 1-2 years ago) → **Regime C** → all gains slab rate
- The ₹10L is in 30% bracket, so any gains realised come out at 30% + 4% cess = 31.2% effective. This is significantly worse than the pre-2023 LTCG-with-indexation regime.

This is the central reason `principles.md` (Section 2.6) places PPF and VPF above debt MFs in the debt allocation priority for the 30% bracket — sovereign EEE wrappers escape this slab-rate trap.

---

## 3. STCG and LTCG terminology under Regime C

Under Regime C, technically there is no LTCG — all gains are short-term and taxed at slab. The terms STCG / LTCG are sometimes still used colloquially in factsheets and statements, but the legal treatment is uniform.

For Regime B, the 24-month holding period still creates an LTCG bucket (12.5% no indexation) and STCG bucket (slab). Worth tracking explicitly.

---

## 4. Set-off and carry-forward of debt MF losses

- **STCL on debt MF (Regime C — common case):** can be set off against STCG (any) and LTCG (any), carry-forward 8 AY
- **STCL on debt MF (Regime B):** same as above
- **LTCL on debt MF (only possible under Regime B for sales > 24 months from a pre-Apr-2023 purchase):** can be set off only against LTCG (any), carry-forward 8 AY
- Practical: tax-loss harvesting on debt MFs has limited value in 30% bracket because:
  - Losses are STCL under Regime C, useful but not magnified
  - The small annual gains are taxed at slab anyway, so harvesting LTCL doesn't escape a 12.5% threshold the way equity loss harvesting reduces above-₹1.25L LTCG

---

## 5. Switching within debt MF schemes

- Switching is a redemption + fresh purchase, just like equity (see `equity-mf.md` Section 6)
- Each switch resets cost basis and starts a new holding period
- Under Regime C, switching is more frequent than equity churning would be (no LTCG threshold to preserve), so the only friction is exit load (typically minimal on liquid / ultra-short funds) and the realised gain tax event itself

**Operational note:** debt MF switching is sometimes recommended to chase yield. The agent does not encourage this — the tax friction in Regime C plus the principle in `principles.md` Section 6.3 (use flows over sales) means switches should be rare and rationale-driven.

---

## 6. Categories the household holds or might hold

Reference for fund-allocate decisions:

### 6.1 Liquid funds
- Invest in money market instruments, T-bills, very short-term debt
- Suitable for emergency-adjacent capital, parking money for redeployment
- Lowest interest rate risk, lowest credit risk among debt MFs
- Yield typically aligned with overnight rates (currently ~6.5-7%)
- All gains under Regime C → slab rate
- Operationally redeemable T+1; some have instant redemption up to ₹50K

### 6.2 Ultra-short / Money Market funds
- Slightly longer maturity profile than liquid (3-6 months)
- Slightly higher yield than liquid
- Same Regime C tax treatment
- Suitable for known short-term outflows where instant redemption isn't required

### 6.3 Short / Banking & PSU / Corporate Bond funds
- 1-3 year average maturity profile
- Higher interest rate risk (NAV moves more with yield changes)
- Higher yield than liquid (~7-8%)
- Same Regime C tax treatment
- Used for the medium-term debt sleeve where some volatility is acceptable

### 6.4 Gilt / Long-duration funds
- Pure G-Sec exposure
- Long average maturity (5+ years), high interest rate risk
- Yield similar to current 10-year G-Sec (~6.3-6.6% currently)
- Same Regime C tax treatment
- Generally not recommended for this household — sovereign EEE wrappers (PPF, NPS) deliver similar yield with no tax leakage

### 6.5 Dynamic bond / Credit risk funds
- Active duration management or lower-rated paper for higher yield
- Higher complexity, higher credit risk
- Generally not recommended for the conservative household debt sleeve

---

## 7. Disclosure-level data the agent needs

For a tax check on a debt MF redemption:
- Purchase date(s) — to determine Regime A/B/C
- Purchase value(s) — for cost basis
- Redemption date and value
- Exit load if any
- Holding period for each tranche if SIP-based (FIFO applies)
- Whether any STCL/LTCL is available for set-off
- User's marginal tax rate from `goals.md`

For Regime C: gain × marginal rate × 1.04 (cess) = tax owed.
For Regime B with > 24-month holding: gain × 12.5% × (1 + cess + applicable surcharge) = tax owed.

---

## 8. Key implication for portfolio decisions

Under Regime C (post-Apr-2023 purchases at 30% bracket):
- Effective post-tax yield on a 7.5% gross liquid fund: 7.5% × (1 - 0.312) = **5.16%**
- PPF gross: **7.1%**, post-tax: **7.1%** (EEE)
- The PPF advantage is enormous in 30% bracket.

This is the single most consequential rule in this folder for the household's 30% bracket. The agent should not recommend large debt MF allocations in the user sub-portfolio's debt sleeve when PPF capacity is unfilled.

For the father sub-portfolio — same logic but father's tax bracket and deduction situation may differ; verify before applying same conclusion.

---

## Sources / verification

- Section 50AA (Specified Mutual Fund — slab rate treatment for post-Apr-2023 acquisitions)
- Section 112 (12.5% no indexation for transitional Regime B sales)
- Finance Act 2023 — introduced the 1 April 2023 cutoff
- Finance (No. 2) Act 2024 — set the 23 July 2024 pivot for transitional rules
- AMFI categorisation guidance for Specified Mutual Fund classification
