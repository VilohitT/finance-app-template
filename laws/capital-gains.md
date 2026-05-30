# laws/capital-gains.md

last_updated: 2026-05-03
last_verified_against_budget: Union Budget 2026
covers: Capital gains framework — holding periods, rates, set-off, harvesting

> **Pivot date for current rules: 23 July 2024.** The Finance (No. 2) Act, 2024 changed holding periods, tax rates, and indexation rules for transfers on or after this date. Most rules in this file reflect the post-23-July-2024 regime, which is now stable. Budget 2025 and 2026 made no changes to capital gains rates or thresholds.

---

## 1. Asset class → holding period → gain type

| Asset class | Short-term threshold | Long-term threshold | Section |
|---|---|---|---|
| Listed equity shares (STT paid) | ≤ 12 months | > 12 months | 111A / 112A |
| Equity-oriented mutual funds | ≤ 12 months | > 12 months | 111A / 112A |
| ELSS | Cannot redeem within 3-yr lock-in; LTCG always | LTCG always | 112A |
| Hybrid MF, equity ≥ 65% | ≤ 12 months | > 12 months | 111A / 112A |
| Hybrid MF, equity 35–65% | ≤ 24 months | > 24 months | 112 (12.5% no indexation) |
| Debt MF (purchased before 1 Apr 2023) | ≤ 24 months | > 24 months (post 23 Jul 2024 sale) | 112 (12.5% no indexation) |
| Debt MF (purchased on/after 1 Apr 2023) | Always short-term | Never long-term | 50AA (slab rate) |
| SGB (listed, sold on exchange) | ≤ 12 months | > 12 months | 112 (12.5% no indexation) |
| SGB (held to 8-yr maturity by primary subscriber) | N/A | Capital gains exempt | Special exemption — see `gold.md` |
| Gold ETFs (with physical gold backing) | ≤ 12 months (post 1 Apr 2025 buys) | > 12 months | Treated as equity-like for LTCG/STCG since 1 Apr 2025 |
| Physical gold, jewellery | ≤ 24 months | > 24 months | 112 (12.5% no indexation) |
| Land / building | ≤ 24 months | > 24 months | 112 (special indexation option for resident individuals/HUF on pre-23-Jul-2024 purchases) |
| Listed bonds | ≤ 12 months | > 12 months | 112 |
| Unlisted shares / unlisted bonds / debentures | ≤ 24 months | > 24 months | 112 (slab rate for some categories) |
| Cryptocurrency / VDA | All gains taxed at 30% flat | All gains taxed at 30% flat | 115BBH |

---

## 2. Tax rates (post 23 July 2024)

### 2.1 Equity STCG (Section 111A)
- **20%** flat (was 15% pre-23-Jul-2024)
- Applies to listed shares + equity-oriented MFs sold within 12 months where STT was paid
- Surcharge and 4% cess apply on top
- Held without STT (off-market): treated as regular STCG, taxed at slab rate

### 2.2 Equity LTCG (Section 112A)
- **12.5%** flat (was 10% pre-23-Jul-2024)
- Applies to gains exceeding the **₹1.25 lakh annual exemption** (was ₹1L pre-23-Jul-2024)
- Per financial year, per PAN, aggregate across all equity LTCG including listed shares + equity MFs + business trusts
- No indexation
- Surcharge and 4% cess apply on top of the 12.5% rate

### 2.3 Other LTCG (Section 112)
- **12.5%** flat, no indexation, for transfers on/after 23 July 2024
- One narrow exception: **resident individuals and HUF selling immovable property acquired before 23 July 2024** can choose between (a) 12.5% no indexation or (b) 20% with indexation, whichever yields lower tax
- For all other 112 assets (listed bonds, debt MFs purchased before 1 Apr 2023 sold after 24 months, etc.) — uniform 12.5% no indexation
- Cost Inflation Index (CII) for FY 2025-26 = 376 (per CBDT Notification No. 70/2025)

### 2.4 Other STCG (slab-rate)
- Slab-rate STCG applies to non-equity STCG — debt funds, real estate, gold (in some forms), unlisted shares
- Plus 4% cess and surcharge

### 2.5 Special: debt MF and Specified Mutual Fund (Section 50AA)
- **All gains taxed at slab rate regardless of holding period** for units acquired on/after 1 Apr 2023 in any fund where ≤ 35% is invested in domestic equity
- This includes: debt funds, gold MFs (until clarification), international funds, fund-of-funds investing in non-equity, market-linked debentures
- See `debt-mf.md` for the layered date-based rules

---

## 3. Surcharge and cess (apply on top of LTCG/STCG rates)

### 3.1 Surcharge under New Regime (FY 2025-26 onward)
| Total income | Surcharge |
|---|---|
| > ₹50 lakh ≤ ₹1 Cr | 10% |
| > ₹1 Cr ≤ ₹2 Cr | 15% |
| > ₹2 Cr | 25% (capped — applies to all higher slabs) |

### 3.2 Surcharge under Old Regime
| Total income | Surcharge |
|---|---|
| > ₹50 lakh ≤ ₹1 Cr | 10% |
| > ₹1 Cr ≤ ₹2 Cr | 15% |
| > ₹2 Cr ≤ ₹5 Cr | 25% |
| > ₹5 Cr | 37% |

### 3.3 Special surcharge cap on LTCG / STCG
For income from listed equity / equity MFs taxed under 111A and 112A, the **maximum surcharge is capped at 15%** regardless of total income. This applies in both regimes.

### 3.4 Health & Education Cess
**4%** on (tax + surcharge). Applies in both regimes universally.

---

## 4. Set-off and carry-forward of losses

- **Short-term capital loss (STCL):** can be set off against both STCG and LTCG
- **Long-term capital loss (LTCL):** can be set off **only** against LTCG
- Both can be carried forward up to **8 assessment years**, provided the ITR is filed within the due date under Section 139(1)
- Capital losses **cannot** be set off against salary, business income, or other income heads
- Within capital gains, the order of set-off matters; LTCL absorbs LTCG before the ₹1.25L exemption is applied (i.e. LTCL effectively reduces taxable LTCG before threshold)

---

## 5. The ₹1.25 lakh equity LTCG exemption — operational notes

This is the single most relevant feature for routine portfolio management.

- **₹1.25L per financial year**, per PAN, aggregate across all equity LTCG sources
- Applies only to gains under Section 112A (listed equity + equity MFs + business trusts where STT paid)
- Does **not** apply to:
  - Section 112 LTCG (real estate, debt MFs sold under transitional rules, listed bonds)
  - Specified Mutual Fund gains (always slab rate, no exemption)
  - Cryptocurrency (always 30% flat, no exemption)

### 5.1 Tax-loss harvesting using this exemption (legal, recommended in routine review)

Sell-and-rebuy mechanics:
1. Each March, the agent computes year-to-date realised LTCG.
2. If the user is below the ₹1.25L threshold and has unrealised LTCG in equity holdings, the agent recommends selling units up to the threshold and rebuying.
3. The rebuy resets cost basis to current price, reducing future LTCG liability by an equivalent amount.
4. Constraints: no exit load (most equity MFs after 1 year have none), small bid-ask spread on listed equity, T+1 to T+2 settlement.
5. **Important:** the rebuy must be at market price (no fictitious price). The "30-day wash sale" rule does not exist under Indian capital gains rules — but the SEBI position is that bona fide trades are required, not paper transactions.

### 5.2 Common pitfalls
- The ₹1.25L exemption is **per financial year**, not per asset. Multiple equity sources aggregate.
- Switching between schemes is a **redemption event** for tax purposes — even within the same AMC. Counts as a sale.
- Switching from Regular to Direct plan: redemption + new purchase. Triggers cap gains on the redemption.
- Dividend reinvestment plans (IDCW): each reinvestment is a fresh purchase with its own cost basis and holding period.

---

## 6. Special situations

### 6.1 NRI capital gains
User is Resident Indian per goals.md, so this section is not active. If status changes, NRI rates and TDS withholding rules apply (largely aligned post-Budget 2024); add a section here when relevant.

### 6.2 Buyback (since 1 Oct 2024)
Buyback proceeds are taxed as dividend income at slab rate in the hands of the shareholder (was previously tax-free for the shareholder; tax was on the company). Not directly relevant unless user holds direct equities that go through buyback.

### 6.3 Section 54 / 54F / 54EC reinvestment exemptions
For property capital gains, reinvestment into a new house (54), new asset (54F), or specified bonds (54EC) can defer or eliminate the tax. Maximum exemption capped at ₹10 Cr from AY 2024-25 onward. Not currently relevant — user has no taxable property sale planned. Will become relevant if the property goal in 2033-2035 results in a future sale.

---

## 7. Reporting in ITR

For reference; not directly an action item for the agent:
- **ITR-2 / ITR-3** is required if you have capital gains (cannot use ITR-1)
- **Schedule 112A**: for LTCG on listed equity + equity MFs (granular trade-wise)
- **Schedule CG**: for other capital gains (property, debt MFs, gold, etc.)
- **Source documents**: CAS / KFintech / CAMS capital gains report; broker capital gains statement (Zerodha Console, Groww, Upstox); registered sale deed for property

---

## Sources / verification

- Finance (No. 2) Act, 2024 — particularly amendments to Sections 111A, 112, 112A, 50AA
- Finance Act 2025 — Budget 2025 confirmed FY 2025-26 rates with no changes
- Finance Act 2026 — Budget 2026 confirmed FY 2026-27 rates with no changes
- Income Tax Department: https://incometaxindia.gov.in
- CBDT Notification No. 70/2025 (CII for FY 2025-26 = 376)
