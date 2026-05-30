# Data sources — portfolio-grill

A reference for **where** to find each piece of information the grill needs. Use these to direct the user when they don't have data at hand.

---

## Mutual fund holdings (debt + equity + ELSS + hybrid + gold MF)

### Primary source: Consolidated Account Statement (CAS)
A CAS is a single document covering **all** your mutual fund holdings across **all AMCs** in India. Two registrars publish CAS depending on which AMCs your funds are with:

- **CAMS:** https://www.camsonline.com → "Investor Services" → "Mailback Services" → "Consolidated Account Statement"
- **KFintech:** https://mfs.kfintech.com → "Investor Services" → "Consolidated Account Statement"

You can also get CAS via NSDL/CDSL if your funds are held in demat form:
- **NSDL CAS:** https://nsdl.co.in → eServices → CAS for demat accounts
- **CDSL CAS:** https://www.cdslindia.com → CAS

CAS is **password-protected**: PAN (uppercase) + DOB (DDMMYYYY).

### What CAS contains
- Folio number per scheme
- Scheme name (full, with Direct/Regular indicated)
- AMC
- Total units held
- Latest NAV
- Current value
- Average cost / cost basis
- Transaction history (purchases, redemptions, switches, dividends)
- ARN code if Regular plan

### How to use CAS in the grill
For each MF holding, the user can look up:
- Folio
- Scheme name (full)
- Plan: read from scheme name — "Direct Plan - Growth" suffix means Direct; absence (or "Regular") means Regular
- Total units, current NAV, current value — all on CAS
- Average cost — on CAS
- First purchase date — earliest entry in transaction history
- Most recent purchase date — most recent buy entry

### If user doesn't have CAS handy
- Tell them how to generate one (link above; arrives within 1-3 hours)
- Or: capture rough numbers now, mark precision items as `UNKNOWN — fetch from CAS` for follow-up
- Each AMC's website also lets you log in and view your holdings — slower than CAS but works for one fund at a time

---

## EPF / VPF

### Primary source: UAN portal
- **URL:** https://unifiedportal-mem.epfindia.gov.in
- **Login:** UAN + password (or Aadhaar + OTP)
- **PassBook:** download passbook from "View Passbook" — shows EPF balance, employer/employee contributions monthly, interest credited annually

### What UAN portal shows
- EPF balance: split into employee contribution + employer contribution + employee pension contribution + employer pension contribution
- Year-by-year contribution history
- Service period details (first joining date)
- Multiple member IDs if user has had multiple employers — needed to confirm consolidation status

### EPS / EPF split
EPF = retirement savings (matched 12% on Basic+DA)
EPS = pension contribution (capped, 8.33% of employer's 12% goes here, max ₹1,250/month)

User mostly cares about EPF balance for portfolio purposes.

### VPF
VPF appears as additional employee contribution within the same EPF account. If user has been doing VPF, the passbook shows the higher employee contribution.

### Current Basic + DA
Not on UAN portal — check latest salary slip.

---

## NPS

### Primary source: CRA portal (NSDL or KFin CRA)
- **NSDL CRA:** https://www.cra-nsdl.com (most NPS subscribers)
- **KFin CRA:** https://www.kfintechpfm.com (newer/specific subscriber base)
- **Login:** PRAN + password

### What it shows
- Current corpus (Tier 1 and Tier 2 separately)
- Asset-class allocation (E / C / G / A breakdown)
- Pension Fund Manager
- Allocation choice (Active vs Auto + lifecycle)
- Contribution history
- Annual statement (transaction summary, NAV history)

### eNPS portal
- **URL:** https://www.enps.nsdl.com
- For new subscribers and contributions, also gives historical view

### Employer 80CCD(2)
Not on CRA portal directly — user should check Form 16 / salary slip / HR for employer's NPS contribution amount.

---

## PPF

### Primary source: PPF passbook (from bank or post office)
- **Bank PPF:** access through bank's net banking → Investments → PPF → Passbook
- **Post Office PPF:** physical passbook + India Post net banking if enabled

### What passbook shows
- Account number
- Account opening date — needed to compute maturity
- Current balance
- Year-by-year contributions and interest
- Loan/withdrawal history if any

### Maturity date calculation
Maturity = 1 April of (FY of opening + 16). Example: opened October 2026 → FY of opening = 2026-27 → maturity = 1 April 2042.

For accounts in extension blocks: maturity adjusted in 5-year increments.

---

## Bank fixed deposits

### Primary source: bank passbook / net banking statement
- Bank's net banking portal → Deposits → FDs/RDs
- Or: physical FDR (Fixed Deposit Receipt) certificate

### What to extract
- Bank name
- FD account number / FDR number
- Principal amount
- Deposit date
- Maturity date
- Interest rate (locked at deposit)
- Interest payout: cumulative (interest reinvested) / quarterly / monthly / on maturity
- Auto-renewal: y/n

### For the emergency fund (₹50L per goals.md)
Critical to capture each FD in the ladder separately if it's laddered. If single FD: single record. If laddered: multiple records.

### Tax-saving FDs (5-year lock-in)
These are 80C-eligible. Note as `type: tax-saving` and check 80C claim history.

---

## Direct equities (stocks)

### Primary sources
- **Broker portal:** Zerodha Console, Groww, Upstox, ICICI Direct, HDFC Securities, etc.
- **Demat statement** from CDSL or NSDL: shows holdings + transaction history
- **Capital gains report** from broker (Zerodha Console > Reports > Tax P&L) — most useful for cost basis

### What to extract
- Company name
- Quantity (current holding, post any splits/bonuses)
- Average purchase price (broker's "Average buy price")
- Total cost basis
- First purchase date — broker's "First buy date" or earliest transaction
- Current price and current value (live)
- Sector

### Common issue
Old direct stock holdings may have purchase records that are hard to reconstruct (broker switched, merger between brokers, etc.). For very old holdings without clean records:
- Use BSE / NSE historical data for the purchase date if known
- Or use CDSL/NSDL annual statement to confirm holding quantity, then approximate cost basis from a reasonable assumption — flag this with explicit "reconstructed cost basis" note

For per goals.md: 8 stocks, ₹2.5L total, dormant. Capture as best the user can; flag missing fields.

---

## Sovereign Gold Bonds (SGBs)

### Primary sources
- **If held in demat:** depository statement (NSDL or CDSL) shows SGB holdings as ISIN-based entries
- **If held in physical certificate form:** Certificate of Holding from RBI E-Kuber (issued at allotment)
- **If purchased online via bank:** bank's net banking portal shows the holding under Securities

### What to extract
- Tranche identifier — comes from the issue notification (e.g., "SGB 2020-21 Series VII")
- Issue date — also from notification
- Maturity date — issue date + 8 years
- Units (in grams)
- Issue price per gram (from notification — that's the original allotment price; current value is at today's gold rate)
- Acquisition route — primary subscription (during issuance window) or secondary market purchase

### How to find tranche details
RBI publishes each tranche's terms. ISIN starts with "IN0020XXXXXXXX" — searching that ISIN on NSDL/CDSL gives tranche info.

> Per goals.md: user has no SGBs currently.

---

## Gold ETFs / Gold MFs / Digital gold / Physical gold

### Gold ETF (held in demat)
- Broker portal or demat statement
- Need: ETF name, units, average price, first purchase date, current NAV

### Gold MF (FoF)
- Same as MF — CAS captures it

### Digital gold
- Platform's app: MMTC-PAMP, Augmont, SafeGold, Paytm Gold, etc.
- Shows: total grams held, current value, transaction history
- No tax benefit — taxed like physical gold

### Physical gold
- User has to estimate
- For jewellery: 22K = ~91.6% gold; estimate by weight × current 22K rate × 0.916 — but most users just give an approximate value
- For investment-grade bullion / coins: weight × current 24K rate

---

## Real estate

### Primary source: user's recollection + recent area transaction prices
- For market value: rough estimate based on recent comparable sales in the area
- Property tax receipts confirm registered ownership
- For loan: latest loan statement from lender

### Acceptable precision
₹50L granularity is fine for primary residence. ₹10L granularity for investment property. The agent doesn't need professional valuation.

---

## Insurance policies

### Primary source: policy documents
- Soft copy in user's email (sent at issuance) or hard copy
- Insurer's customer portal: ICICI Pru, HDFC Life, etc. all have customer logins

### What to extract
- Policy number
- Sum assured
- Annual premium
- Policy start date
- Policy end date or tenure
- Premium-paying party — **important** for 80C/80D eligibility
- Riders if any

### Health insurance (employer)
- HR portal or HR contact for sum assured details
- Per goals.md: this is a known UNKNOWN — fetch from HR

---

## Crypto / VDA

### Primary sources
- Indian exchange (CoinDCX, WazirX, etc.): account statement
- Foreign exchange (Binance, etc.): need to be aware that holding foreign crypto via foreign exchange has reporting implications

### What to extract
- Coin / token
- Quantity
- Average buy price
- Current price
- Cost basis
- Held since (first purchase)

Note: all crypto gains taxed at 30% flat (Section 115BBH), no setoff against losses. This is a known tax-inefficient holding.

> Per goals.md: None.

---

## Loans (liabilities)

### Primary source: latest loan statement
- Lender's portal or physical statement
- Shows: original amount, current balance, EMI, rate, tenure remaining

### What to extract
- Loan type
- Lender
- Original sanction
- Current balance
- Interest rate (note if floating — current rate)
- EMI
- Tenure remaining
- Holder

> Per goals.md: None.

---

## What if the user doesn't have any of these handy?

The grill should not block on missing data. Standard fallback:

1. Mark the field `UNKNOWN — fetch from <specific source>` per the lookup above
2. Move on with whatever information is available
3. Section 15 (Open Items) of portfolio.md collects all UNKNOWNs as a checklist with their fetch sources
4. The user works through the checklist over the days/weeks following the grill, updating portfolio.md as data is fetched

The agent should make clear that a partial portfolio.md is **fine to start with** — downstream skills work with what's there and flag where data gaps prevent recommendations.

The single most useful thing the user can do before the grill is generate the **CAS** from CAMS or KFintech. That alone fills ~70% of typical portfolio data for a household with mutual fund focus.
