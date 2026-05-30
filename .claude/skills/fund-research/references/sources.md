# Sources for fund-research

Curated list of authoritative web sources for each `fund_quality.json` field.
WebFetch any URL here; AMC factsheet PDFs are the gold standard for TER/manager,
screeners are the gold standard for filtering by category.

---

## Primary sources (always cite)

### AMC factsheets (gold standard for TER, manager, manager_since, AUM)

Each AMC publishes a monthly fact sheet PDF with per-scheme TER, manager(s),
manager-since-date, AUM, top-10 holdings, sector mix.

Search pattern: `<AMC name> factsheet <month> <year> pdf`

| AMC | Typical URL pattern |
|---|---|
| Parag Parikh (PPFAS) | `https://amc.ppfas.com/downloads/factsheet/` |
| Motilal Oswal | `https://www.motilaloswalmf.com/download/factsheet` |
| HDFC | `https://www.hdfcfund.com/our-products/factsheet` |
| ICICI Prudential | `https://www.icicipruamc.com/downloads/monthly-fact-sheet` |
| SBI | `https://www.sbimf.com/downloads/monthly-fact-sheet` |
| Nippon India | `https://mf.nipponindiaim.com/InvestorServices/download/Pages/factsheet.aspx` |
| Axis | `https://www.axismf.com/downloads/factsheet` |
| Kotak | `https://www.kotakmf.com/Information/factsheet` |
| UTI | `https://www.utimf.com/forms-and-downloads/factsheets` |
| DSP | `https://www.dspim.com/forms-and-downloads/factsheet` |
| Mirae Asset | `https://www.miraeassetmf.co.in/downloads/factsheet` |
| Franklin Templeton | `https://www.franklintempletonindia.com/our-funds/forms-and-applications/factsheet` |
| Edelweiss | `https://www.edelweissmf.com/Information/factsheet` |
| Quant | `https://www.quantmutual.com/downloads/factsheet` |
| Bandhan | `https://bandhanmutual.com/Information/factsheet` |
| WhiteOak Capital | `https://whiteoakamc.com/downloads/factsheet` |

### Value Research Online (screener + per-fund detail)

`https://www.valueresearchonline.com/funds/`

Free tier has:
- Per-category screener: filter by category, plan, sort by 1Y/3Y/5Y return, AUM
- Per-fund page: TER, AUM, expense ratio history, manager bio, holdings
- Direct comparison between two funds

URL pattern: `https://www.valueresearchonline.com/funds/<scheme-slug>/`

The screener URL pattern with filters:
`https://www.valueresearchonline.com/funds/selector/category/<category-slug>/?end-type=1&plan-type=Direct&sort=return-3y`

### Freefincal "Plumb Line" lists

`https://freefincal.com/free-mutual-fund-screeners/`

M Pattabiraman (Pattu)'s curated lists by category. Updated quarterly. He
applies a "robust over reactive" lens: stable mandate, manager tenure, low
churn. AMCs flagged "skip" or "watch" by Pattu deserve a `notes:` mention.

Specific lists:
- Plumb Line for index funds (TER and tracking-error focus)
- Active equity Plumb Line (rolling 5Y vs benchmark)
- Debt fund screener (credit-quality focus)
- Hybrid screener

### AMFI (regulator data)

- **NAVAll.txt** (daily NAV file) — already ingested by `scripts/fetch_nav.py`. Use for cross-checking the canonical scheme name.
- **AMFI category-wise AUM** (monthly) — `https://www.amfiindia.com/research-information/aum-data/categorywise` — useful for AMC-level AUM sanity check.
- **SEBI categorisation circular** — defines what each category means; `laws/sebi-categories.md` mirrors the relevant rules.

---

## Secondary sources (use for cross-checking)

### Moneycontrol

`https://www.moneycontrol.com/mutual-funds/`

Useful for: per-scheme expense ratio, AUM, manager. Less curated than VR but
covers more schemes.

### Morningstar India

`https://www.morningstar.in/funds`

Useful for: independent rating (1-5 stars), risk-adjusted return scoring.
Doesn't substitute for direct factsheet check on TER/manager but adds a
quality flag to capture in `notes`.

### MFCentral / CAMS / KFintech

Investor-portal data — accurate AUM and folio data per AMC, but typically
behind a login. Useful for the user's own holdings; not a research-universe
source.

---

## Per-field source priority

| Field | Primary | Secondary | Tertiary |
|---|---|---|---|
| `ter` | AMC factsheet | Value Research | Moneycontrol |
| `aum_crore` | AMC factsheet | AMFI category PDF | Value Research |
| `manager_name` | AMC factsheet | Value Research | AMC website "Our Team" |
| `manager_since` | AMC factsheet manager bio | Value Research manager profile | AMC website |
| `vintage` (scheme launch date) | AMC factsheet | AMFI scheme list | Value Research |
| `notes` (mandate, AUM bloat, etc.) | Pattu Freefincal | Morningstar | AMC factsheet |

---

## When sources disagree

- **TER:** factsheet wins (it's the SEBI-required disclosure).
- **AUM:** factsheet wins; 1-5% variance is normal due to date-of-snapshot.
- **Manager:** if factsheet says different from VR/Morningstar, factsheet wins (it's contemporaneous; VR can lag manager changes by weeks).
- **Manager-since-date:** sometimes ambiguous when a co-manager has been there longer than the lead. Capture lead-manager-since-date by default; mention co-manager dates in `notes`.

---

## What to flag in `notes`

- AUM > ₹50,000 Cr in mid/small cap categories (bloat risk)
- Manager change in the last 12 months (style-drift risk window)
- TER changed materially in the last year (regulatory or AMC-fee revision)
- Pattu's "skip" or "watch" rating
- Morningstar 1-2 stars (not necessarily disqualifying but worth noting)
- Recent SEBI action against the AMC
- AMC merger / recategorisation history (e.g. Bandhan acquired IDFC AMC; some scheme IDs persist)

---

## Refresh cadence per field

| Field | Cadence |
|---|---|
| `ter` | Annually (changes are infrequent except at regulatory events) |
| `aum_crore` | Quarterly |
| `manager_name` | When portfolio-review or news flags a change |
| `manager_since` | Same as `manager_name` |
| `last_verified` | Whenever any of the above is touched |
| `notes` | Ad-hoc |
