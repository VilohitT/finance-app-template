# laws/sebi-categories.md

last_updated: 2026-05-03
last_verified_against_budget: Union Budget 2026 (no SEBI categorisation changes)
last_verified_against_sebi_circular: SEBI categorisation circular SEBI/HO/IMD/DF3/CIR/P/2017/114 (foundational) and subsequent updates
covers: SEBI mutual fund categorisation rules — what each category actually means

> **Why this file exists:** "large cap" or "flexicap" or "balanced advantage" are tightly defined by SEBI, not by the fund's marketing. The agent uses these definitions to verify category-fit during fund selection and to identify style drift in routine review. Misreading category = misreading risk.

---

## 1. Equity scheme categories

### 1.1 Large Cap Fund
- Minimum **80% in equity of large-cap companies**
- "Large cap" = top **100 companies by market capitalisation** (per AMFI list, updated half-yearly)
- AMFI publishes the official top-100 list every six months (June-end, December-end). Fund managers must align to that list.

### 1.2 Mid Cap Fund
- Minimum **65% in equity of mid-cap companies**
- "Mid cap" = companies ranked **101st to 250th** by market cap (per AMFI list)

### 1.3 Small Cap Fund
- Minimum **65% in equity of small-cap companies**
- "Small cap" = companies ranked **251st onward** by market cap

### 1.4 Multi Cap Fund
- Minimum **75% in equity**, with mandated allocation:
  - At least **25% in large-cap**
  - At least **25% in mid-cap**
  - At least **25% in small-cap**
- The remaining 25% is at fund manager's discretion across cap segments

### 1.5 Flexi Cap Fund
- Minimum **65% in equity**, free allocation across market caps at fund manager's discretion
- No mandatory minimum in any specific cap segment
- More flexibility than Multi Cap

### 1.6 Large & Mid Cap Fund
- Minimum **35% in large cap** AND minimum **35% in mid cap**
- Remaining 30% flexible (typically in small cap or cash/debt)

### 1.7 ELSS (Equity Linked Savings Scheme)
- Minimum **80% in equity**
- 3-year lock-in
- 80C eligible (Old Regime)

### 1.8 Focused Fund
- Maximum **30 stocks**
- Minimum **65% in equity**

### 1.9 Sectoral / Thematic Fund
- Minimum **80% in equity** of the named sector/theme

### 1.10 Dividend Yield Fund
- Minimum **65% in equity**, predominantly in dividend-yielding stocks

### 1.11 Value / Contra Fund
- Minimum **65% in equity**, value-investing or contrarian style

---

## 2. Hybrid scheme categories

### 2.1 Aggressive Hybrid Fund
- **65-80% in equity**, **20-35% in debt**
- Treated as **equity-oriented for tax** (since equity ≥ 65%) — see `equity-mf.md`

### 2.2 Balanced Hybrid Fund
- **40-60% in equity**, **40-60% in debt**
- **Equity allocation < 65% means debt-tax treatment** for many such funds — but each fund's daily-average equity allocation determines this
- Borderline case for tax — verify per fund

### 2.3 Conservative Hybrid Fund
- **10-25% in equity**, **75-90% in debt**
- Debt-tax treatment (Section 50AA for post-Apr-2023 buys → slab rate)

### 2.4 Equity Savings Fund
- Equity + arbitrage + debt
- Targets **65%+ equity-and-arbitrage** to qualify for equity tax treatment
- Arbitrage component is a hedged equity position (low risk)
- Lower volatility than pure equity, equity-tax treatment if allocation rules met

### 2.5 Multi Asset Allocation Fund
- Invests in **at least 3 asset classes**, minimum **10% in each**
- Tax treatment depends on equity allocation: if ≥ 65% domestic equity → equity tax; if 35-65% → Section 112 hybrid; if < 35% → Specified Mutual Fund slab rate
- The user holds ~20% of equity MF corpus in a multi-asset fund per goals.md — verify which tax bucket it falls under during portfolio.md construction

### 2.6 Balanced Advantage / Dynamic Asset Allocation Fund (BAF / DAAF)
- Equity allocation **dynamically managed** based on market valuations
- Tax treatment depends on **realized monthly average equity exposure**
- Most BAFs maintain 65%+ effective equity (including arbitrage hedges) to qualify for equity tax treatment
- Verify per scheme — some BAFs are equity-oriented, others fall under hybrid / non-equity treatment

### 2.7 Arbitrage Fund
- Min **65% in equity arbitrage** (long-short hedged equity positions)
- Treated as **equity-oriented for tax**
- Net market exposure near zero — yield similar to short-duration debt
- Very useful for short-horizon parking with equity tax treatment (post-12-month LTCG at 12.5%)

---

## 3. Debt scheme categories

Each maps to a duration profile and credit profile. All are Specified Mutual Fund per Section 50AA for post-April-2023 buys → slab rate taxation.

### 3.1 Overnight Fund
- Macaulay duration **≤ 1 day**
- Invest in overnight reverse repos, overnight money market

### 3.2 Liquid Fund
- Macaulay duration **up to 91 days** (3 months)
- T-bills, money market, very short-term debt

### 3.3 Ultra Short Duration Fund
- Macaulay duration **3-6 months**

### 3.4 Low Duration Fund
- Macaulay duration **6-12 months**

### 3.5 Money Market Fund
- Up to 1-year maturity instruments only

### 3.6 Short Duration Fund
- Macaulay duration **1-3 years**

### 3.7 Medium Duration Fund
- Macaulay duration **3-4 years**

### 3.8 Medium to Long Duration Fund
- Macaulay duration **4-7 years**

### 3.9 Long Duration Fund
- Macaulay duration **> 7 years**

### 3.10 Dynamic Bond Fund
- Active duration management — can be anywhere on the curve

### 3.11 Corporate Bond Fund
- Min **80% in highest-rated corporate bonds (AA+ and above)**

### 3.12 Credit Risk Fund
- Min **65% in lower-rated corporate bonds (AA and below)**
- Higher yield, higher credit risk
- Generally avoid for this household

### 3.13 Banking & PSU Fund
- Min **80% in debt of banks, PSUs, public financial institutions**
- High credit quality

### 3.14 Gilt Fund
- Min **80% in government securities**

### 3.15 Gilt Fund with 10-year Constant Duration
- Min **80% in G-Sec** with average maturity ~10 years

### 3.16 Floater Fund
- Min **65% in floating-rate debt** (re-rates with interest rate movements)

---

## 4. Other categories

### 4.1 Index Funds
- Track a specified index passively
- TER caps lower than active funds
- Categorised by underlying index (Nifty 50, Nifty Next 50, Sensex, Nifty 500, Nifty Midcap 150, etc.)

### 4.2 ETFs
- Listed and traded on stock exchanges
- Demat account required
- Can include equity, debt, gold, international ETFs

### 4.3 Fund of Funds (FoF)
- Invest in other mutual funds
- Tax treatment depends on the underlying — most FoFs investing in non-equity get Section 50AA slab-rate treatment
- **Check carefully** — international FoFs and gold FoFs are often slab-rate even if branded "equity-like"

### 4.4 International Funds
- Invest in foreign equity / debt / commodities
- **Tax treatment: Specified Mutual Fund (Section 50AA)** for post-April-2023 buys → slab rate, regardless of underlying being foreign equity
- The 65% domestic equity test is strict — foreign equity does not count

---

## 5. How fund categorisation affects tax — cheat sheet

| Category | Domestic equity % | Tax treatment |
|---|---|---|
| Pure equity (large/mid/small cap, multicap, flexicap, ELSS, focused) | ≥ 80% (some 65%) | Equity (Section 111A/112A) |
| Aggressive Hybrid | 65-80% | Equity (Section 111A/112A) |
| Equity Savings | 65%+ (incl. arbitrage) | Equity (verify scheme rules) |
| Arbitrage Fund | 65%+ | Equity |
| Balanced Advantage | Depends on actual allocation | Verify per scheme |
| Multi Asset Allocation | 10% min in equity, can be 65%+ | Verify per scheme; some equity, some 112, some 50AA |
| Conservative Hybrid | 10-25% | Specified MF (Section 50AA) — slab rate |
| Pure debt categories | < 35% (typically 0%) | Specified MF (Section 50AA) — slab rate |
| Gold Fund (FoF) | 0% domestic equity | Specified MF — slab rate |
| Gold ETF (post 1 Apr 2025) | 0% (but special treatment) | LTCG 12.5% no indexation, 12-month holding |
| International Fund | Foreign equity, no domestic | Specified MF — slab rate |

---

## 6. Style drift — what to watch for

A fund's category is mandated; drifting outside category limits is a SEBI violation. But softer drift is common:

- **Style drift:** value fund holding growth stocks; growth fund holding value stocks
- **Cap drift within mandate:** large-cap fund holding 60% large cap and 40% mid+small cap (within technical compliance if 80% of large-cap segment is met, but skewing risk)
- **Sector concentration:** flexicap that effectively becomes a banking fund
- **Number of stocks:** focused fund ostensibly holding 30 stocks but with one stock at 15% (concentration risk)
- **Manager changes:** new manager may not honour the original strategy

The agent's `fund-allocate` skill (yet to be built) checks gates 1 (category fit) and 5 (long-term performance vs benchmark) using SEBI category data + fund factsheet portfolio data.

---

## 7. Where to verify category

For each fund:
- **AMFI fund details page:** https://www.amfiindia.com — shows official SEBI category
- **Fund factsheet:** monthly PDF from AMC website — shows current portfolio holdings, top 10 stocks, market-cap breakdown
- **CAS / KFintech / CAMS:** the consolidated account statement labels each holding's category

The agent reads category from fund factsheet (most authoritative), cross-checks with AMFI categorisation, and flags any discrepancy.

---

## Sources / verification

- SEBI Master Circular for Mutual Funds (consolidated SEBI MF rules)
- SEBI categorisation circular SEBI/HO/IMD/DF3/CIR/P/2017/114 (October 2017 — foundational; subsequent amendments)
- AMFI categorisation guidance: https://www.amfiindia.com
- Most recent AMFI top-100 list (for large/mid/small cap classification): published every six months in June and December
