# laws/gold.md

last_updated: 2026-05-03
last_verified_against_budget: Union Budget 2026
covers: Sovereign Gold Bonds (currently paused), Gold ETFs, Gold MFs, digital gold, physical gold

> **Major status note:** SGB issuance has been paused since February 2024. Government confirmed in Budget 2025 that no new tranches will be issued. Budget 2026 added that capital gains exemption at maturity now only applies to investors who bought directly from RBI (primary issuance) — secondary market buyers lose the maturity tax exemption. This is consequential for `principles.md` Section 2.7.

---

## 1. Sovereign Gold Bonds (SGB)

### 1.1 Current issuance status
- **No new SGB tranches since February 2024** (last tranche: 2023-24 Series IV, issued 21 Feb 2024)
- Government confirmed in Budget 2025 (Feb 2025) and reiterated in Budget 2026 that the SGB scheme is being phased out
- Reason cited: high cost of borrowing for the government as gold prices appreciated faster than expected
- **Existing SGB holders:** unaffected — original terms continue to maturity (8 years from issue) and pre-mature redemption windows continue
- **New investors who want SGB exposure:** can only buy on the **secondary market** (NSE/BSE) — but this loses the maturity tax exemption per Budget 2026

### 1.2 SGB structure (for existing holdings or secondary-market purchases)
- **Tenor:** 8 years from issue date
- **Interest:** 2.5% per annum on face value (issue price), paid semi-annually to bank account on 31 March and 30 September each year
- **Maturity:** at 8 years, redemption value = average closing price of 999 purity gold over previous 3 working days (per IBJA), times the gram count held
- **Premature redemption:** allowed after 5 years from issue, on interest payment dates only, by submitting request to issuing bank/post office/SHCIL
- **Listed/tradable:** SGBs are listed on NSE and BSE; can be sold on exchange at market price any time after listing

### 1.3 Tax treatment of SGB

#### Interest (2.5% semi-annual coupon)
- Taxable as **"Income from Other Sources"** at slab rate
- No TDS deducted
- Same treatment in both Old and New Regime
- Annual interest must be reported in ITR

#### Capital gains on SGB

| How acquired | How exited | Tax treatment |
|---|---|---|
| Bought on primary RBI issuance | Held to 8-year maturity | **Tax-exempt capital gain** (Section 47(viic)) — primary subscriber only, post Budget 2026 |
| Bought on secondary market | Held to 8-year maturity | **Capital gains taxable** at LTCG rate — Budget 2026 change |
| Either acquisition | Pre-mature redemption (5+ years, on coupon date with RBI) | **Tax-exempt for primary subscribers**; taxable for secondary buyers post Budget 2026 |
| Either acquisition | Sold on exchange before maturity | LTCG (>12 months): 12.5% no indexation under Section 112; STCG (≤12 months): slab rate |

**Critical update from Budget 2026:** Section 47(viic) exemption on SGB redemption applies only to subscribers of primary issuance from 1 April 2026 onward. Secondary market buyers don't get this exemption regardless of how long they've held.

#### Set-off and carry-forward
- Capital losses (when sold on exchange before maturity, at a loss): standard STCL/LTCL set-off rules apply per `capital-gains.md` Section 4

### 1.4 Implication for the household

For existing SGB holdings (none currently per goals.md Section 3.5):
- No SGB exposure — moot point currently

For future gold allocation:
- **Primary SGB issuance is unavailable.** Cannot buy fresh SGBs from RBI.
- **Secondary market SGB purchase is possible** but no longer enjoys the maturity tax exemption — significantly reduces the SGB-vs-Gold-ETF advantage
- For the 5% gold sleeve in each sub-portfolio (per `principles.md`), SGB is **no longer the strict-dominator** it was. Decision now genuinely hinges on:
  - Gold ETF: liquid, simple, equity-like LTCG treatment (12.5% no indexation post 1 Apr 2025)
  - Secondary market SGB: 2.5% coupon (taxable), capital gains taxable at sale, slightly higher liquidity friction
  - Gold MF (FoF): can be slab-rate taxable as Specified Mutual Fund — verify per scheme

The principle of "SGB-preferred" in `principles.md` Section 2.7 may need a small revision to reflect this. Pending user direction.

---

## 2. Gold ETFs

### 2.1 Structure
- ETFs with physical gold backing (≥95% physical gold)
- Each unit typically represents 1 gram (or 0.01 gram for some) of gold
- Trade on stock exchanges; need demat account
- Expense ratio typically 0.5-1.0% per annum

### 2.2 Tax treatment

**For Gold ETFs purchased on or after 1 April 2025:**
- Treated similarly to equity for LTCG/STCG holding periods (12 months threshold)
- LTCG rate: 12.5% without indexation
- No ₹1.25L exemption (that's equity-only under Section 112A; Gold ETF gains fall under Section 112)
- STCG: slab rate

**For Gold ETFs purchased before 1 April 2025:**
- Treated as Specified Mutual Fund (Section 50AA equivalent for gold) for some categories
- Check fund factsheet for actual treatment — there's still some ambiguity in practice
- Conservative treatment: assume slab rate at sale unless held to a clarified LTCG-eligible threshold

### 2.3 Operational

- Liquid: can be sold any time on the exchange
- Brokerage applies on each transaction
- Dividend / IDCW: irrelevant — gold ETFs don't pay yield (no coupon equivalent unlike SGB)

---

## 3. Gold Mutual Funds (Fund of Funds)

- Open-ended mutual funds that invest in gold ETFs
- Slightly higher expense ratio (0.5-1.5% on top of underlying ETF expense)
- No demat account required — can use SIP from regular MF platforms
- **Tax treatment:** Specified Mutual Fund (Section 50AA) — slab rate on all gains regardless of holding period, for units acquired post 1 April 2023
- This is a meaningful disadvantage in 30% bracket

**Implication for this household:** the existing ₹1L SBI Gold MF holding (per goals.md Section 3.5) is taxed at slab rate at any sale. For a 30% bracket holder, this is a material drag. Consideration during portfolio review: whether to switch to a Gold ETF (more tax-efficient) or wait for a tax-loss-harvesting opportunity.

---

## 4. Digital gold

- Digital gold platforms (MMTC-PAMP, Augmont, SafeGold, Paytm Gold, Google Pay) offer pure digital gold backed by physical reserves
- Convenient for small purchases and small-denomination accumulation
- Tax treatment: like physical gold (Section 112, 24-month LTCG threshold, 12.5% no indexation)
- **Storage charges and platform fees apply** — typically eat into returns
- **Conversion / redemption costs:** redeeming as physical gold incurs making charges; redeeming as cash incurs spread vs spot price
- **Generally not recommended for investment-grade allocations** — better to use Gold ETF for liquid exposure or SGB if available

---

## 5. Physical gold

### 5.1 Jewellery
- Investment-grade purity is rare in jewellery (typically 22K = 91.6% gold, with making charges 8-25% on top)
- **Making charges are sunk** — do not recover at sale
- **GST 3% on purchase** (3% on the gold value plus 5% on making charges in some jurisdictions)
- Storage cost (locker if used)
- Insurance / theft risk
- **Not investment gold for portfolio purposes.** Per `principles.md` Section 2.7: existing physical jewellery has emotional/utility value, not portfolio value. Don't rebalance.

### 5.2 Bullion / coins
- Higher purity (99.5% — 99.9%)
- Lower making charges (~3-5%) but still meaningful
- GST 3%
- Easier to verify and sell vs jewellery
- Tax: Section 112 — 24-month LTCG threshold, 12.5% no indexation
- **Authentication risk at sale** — buyer may discount for non-standard pieces

### 5.3 Tax on physical gold

| Holding | Treatment |
|---|---|
| ≤ 24 months | STCG at slab rate |
| > 24 months | LTCG at 12.5% no indexation (Section 112) |

For property-like indexation choice: doesn't apply to gold (only immovable property has the special transitional indexation option).

---

## 6. Summary recommendation matrix for this household

For the 5% gold sleeve in each sub-portfolio:

| Vehicle | Convenience | Tax efficiency | Liquidity | Recommendation |
|---|---|---|---|---|
| Primary SGB | N/A (paused) | Best (if hold to maturity, primary subscriber) | Low (5+ year for premature redemption) | Unavailable currently |
| Secondary SGB | Medium | Reduced (no maturity exemption post Budget 2026) | Medium | Selective; modest case |
| Gold ETF | High | Good (12.5% LTCG post 1 Apr 2025) | High | **Default for new gold allocation** |
| Gold MF (FoF) | High | Poor (slab rate, Specified MF) | High | Avoid for 30% bracket |
| Digital gold | High | Like physical (24-month LTCG) | High | Not preferred |
| Physical bullion | Low | Like physical (24-month LTCG) | Low | Skip; portfolio purpose only |
| Physical jewellery | Low | Like physical | Low | Existing only; don't add |

Existing household gold:
- ₹1L Gold MF (SBI) — tax-inefficient under Specified MF rules; consider transition to Gold ETF on a tax-favourable occasion
- ₹1L physical gold (jewellery + bullion) — leave alone per principle

For new gold deployment: **Gold ETF** is the practical default. Re-evaluate if SGB issuance resumes.

---

## Sources / verification

- Section 47(viic) — capital gains exemption on SGB maturity (now restricted to primary subscribers per Budget 2026)
- Section 112 (LTCG on gold ETFs and physical gold)
- Section 50AA (Specified Mutual Fund — affects Gold MFs)
- Finance Act 2024 — first round of capital gains restructuring effective 23 July 2024
- Finance Act 2025 (Budget 2025) — confirmation of SGB scheme phase-out
- Finance Act 2026 (Budget 2026) — restriction of SGB maturity exemption to primary subscribers
- RBI SGB scheme page: https://www.rbi.org.in/Scripts/BS_SwarnaBharat.aspx
- AMFI for Gold MF / Gold ETF categorisation
