# Goals.md template — finance-grill

This is the **exact** structure for the output file. Use it verbatim. Field-level conventions:

- **`UNKNOWN — flagged for follow-up`** — use when user couldn't answer; auto-populate Section 9 list
- **`N/A`** — use when the question genuinely doesn't apply (e.g. SSY when no daughter under 10)
- Rupee figures: today's rupees, no inflation adjustment, no commas needed inside values but human-readable is fine (e.g. `₹15,00,000` or `₹15L` — pick one and be consistent)
- Dates: ISO format `YYYY-MM-DD` for full dates, `YYYY` for years-only
- Lists with no entries: write `None.` rather than empty bullets

---

## TEMPLATE BEGINS BELOW THIS LINE — copy from here downward

```markdown
# Financial Goals & Profile

last_updated: YYYY-MM-DD
last_grilled_by: finance-grill v1
review_due: YYYY-MM-DD

---

## 1. Personal & Eligibility Context

- **Date of birth:**
- **Age (at last_updated):**
- **Residential status:** (Resident / NRI / OCI / other)
- **Marital status:**
- **Spouse:** (working / not / income / planning style — or N/A)
- **Dependents:**
  - [Relationship, age]: dependency level, special needs if any
- **Employment type:** (salaried / self-employed / business owner / freelancer / retired / mixed)
- **Employer benefits:** (EPF / NPS workplace / health cover / other — or N/A)
- **Income stability:** (very stable / mostly stable / variable / volatile)
- **Health considerations:**
- **Parental support obligations:**

---

## 2. Income & Cash Flow

- **Gross annual income:** ₹
- **Income sources & rough split:**
- **Expected income changes (1–3 yrs):**
- **Tax regime:** (old / new)
- **Marginal tax bracket:** ~%
- **Monthly take-home:** ₹
- **Monthly fixed expenses:** ₹
- **Monthly variable expenses:** ₹
- **Average monthly surplus available for investing:** ₹
- **Surplus consistency:** (consistent / lumpy — describe)
- **Active loans:**
  - Type — interest rate — current balance — EMI — tenure remaining
- **Irregular but predictable large outflows:**

---

## 3. Existing Assets & Portfolio

(Detailed scheme-level holdings will live in `portfolio.md` later. This section is category-level summary.)

### 3.1 Liquid
- **Savings/current account total:** ₹
- **Separate emergency fund:** (yes/no — where parked — amount)

### 3.2 Fixed deposits & debt instruments
- **FDs total:** ₹ (rough tenure ladder)
- **Recurring deposits:**
- **Debt mutual funds:** ₹ (categories: liquid / ultra-short / short / corporate / gilt)
- **RBI Floating Rate Bonds, tax-free bonds, other govt bonds:**

### 3.3 Mutual funds (equity / hybrid / ELSS / international)
- **Total corpus:** ₹
- **Approximate split:** equity __% / hybrid __% / ELSS __% / international __%
- **Direct or Regular plans:**
- **Number of distinct schemes:**

### 3.4 Government schemes
- **PPF:** opened YYYY, balance ₹, annual contribution ₹, maturity year YYYY — or N/A
- **EPF / VPF:** balance ₹, voluntary contribution status, UAN consolidated y/n — or N/A
- **NPS Tier 1:** corpus ₹, allocation choice (Active/Auto), using ₹50K 80CCD(1B) y/n — or N/A
- **NPS Tier 2:** corpus ₹ — or N/A
- **Sukanya Samriddhi (SSY):** balance ₹, annual contribution ₹ — or N/A
- **SCSS:** applicable y/n, balance ₹ — or N/A
- **Post Office (POMIS / NSC / KVP / RD):**

### 3.5 Gold
- **Sovereign Gold Bonds:** tranches & maturity dates, total grams / value
- **Gold ETFs / digital gold / gold MFs:** ₹
- **Physical gold:** jewellery ₹, bullion ₹

### 3.6 Direct equities
- **Total value:** ₹
- **Concentration / themes:**

### 3.7 Real estate
- **Primary residence:** market value ₹, home loan balance ₹, rate __%
- **Investment property:** value ₹, rental yield %, loan if any
- **Plots / agricultural land:**

### 3.8 Insurance assets (mixed protection + investment)
- **ULIPs / endowment / money-back / traditional:**
  - Policy: sum assured ₹, premium ₹/yr, year started, surrender value ₹

### 3.9 Alternatives
- **Cryptocurrency:** ₹
- **PMS / AIFs:**
- **REITs / INVITs:**
- **Foreign assets (LRS):**
- **Other:**

---

## 4. Insurance & Protection

- **Term life insurance:** sum assured ₹, premium ₹/yr, tenure remaining
- **Health insurance:**
  - Self/family floater: sum assured ₹, employer + personal split
  - Critical illness rider/standalone: yes/no, sum assured ₹
  - Disability cover: yes/no, sum assured ₹
- **Health cover for parents:**
- **Notable gaps flagged:**

---

## 5. Goals

(One subsection per goal. Order roughly by criticality and timeline.)

### 5.1 [Goal name — e.g. Emergency fund / Retirement / Child 1 undergrad / etc.]
- **Target amount (today's ₹):**
- **Target year:**
- **Criticality:** must-have / should-have / nice-to-have
- **Flexibility on amount:** rigid / somewhat flexible / very flexible
- **Flexibility on timing:** rigid / somewhat flexible / very flexible
- **Existing earmarked savings:**
- **Notes:**

### 5.2 [Next goal]
(repeat structure)

---

## 6. Risk Tolerance

- **Self-rated (1–10):**
- **Behavioural evidence (past actions in real downturns / past panic-sells / FOMO buys):**
- **Scenario reactions:**
  - 30% drawdown response:
  - 8% guaranteed vs 12% with 25% downside choice:
  - Panic-sell rupee threshold: ₹
- **Lock-in tolerance:** (PPF 15-yr / ELSS 3-yr / SGB 8-yr / NPS to 60 — comfortable y/n)
- **Liquidity needs:**
- **Portfolio-check frequency:** (daily / weekly / monthly / quarterly / yearly)
- **Verdict:** conservative / moderate / aggressive — and key caveats

---

## 7. Constraints, Preferences, Values

- **Religious/ethical constraints:**
- **Asset class aversions & reasons:**
- **Product aversions / past bad experiences:**
- **Time available for active management:** minimal / moderate / active
- **Tax optimisation priority (1–10):**
- **Past mistakes & lessons:**
- **Other important notes:**

---

## 8. Knowledge & Behaviour

- **Self-rated investment knowledge (1–10):**
- **Trusted information sources:**
- **Behavioural patterns to watch (FOMO / recency / herd / anchoring / loss aversion / lifestyle creep):**
- **One habit to change:**

---

## 9. Open Items / Flagged for Follow-up

(Auto-populate from any UNKNOWN field above. Each item is a checklist entry the user should resolve.)

- [ ] [Field name in section X.Y] — [why it matters]

---

## 10. Contradictions Surfaced & Resolutions

(From the contradictions sweep at end of interview. Each entry: what the tension was, how the user resolved it.)

- **Tension:** [e.g. Wants to retire at 50 with ₹2L/month expenses but current surplus + corpus implies that needs ~14% real returns]
  **Resolution:** [e.g. User pushed retirement to age 55 and accepted ₹1.6L/month target]

---

## Appendix — How to use this file

This file is the foundation document for the investment agent. Downstream skills (portfolio-review, fund-allocate, tax-check) read from here.

If any field is `UNKNOWN`, the agent will treat that as "I don't have information" and either work around it or ask before making recommendations that depend on it.

Re-run the `finance-grill` skill after any of these triggers:
- Major life event (marriage, child, job change, inheritance, retirement, loss of a dependent)
- Material income change (>20% up or down)
- Goal added or removed
- Every 6–12 months as a routine refresh
```

## TEMPLATE ENDS ABOVE THIS LINE
