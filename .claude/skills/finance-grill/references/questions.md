# Question bank — finance-grill

The full set of questions, organised by section. Within each section, questions are grouped into **batches** — present each batch as one turn, wait for the user's response, fill in the data, then either probe or move to the next batch.

Probing strategies for vague answers are in `techniques.md`.

---

## Section 1 — Personal & Eligibility Context

**Why this section exists:** establishes who the user is, which government schemes they're eligible for (PPF/EPF/NPS/SSY/SCSS all have eligibility rules), and the life context that shapes their goals.

### Batch 1.1 — Identity basics
Ask all together:
- What's your date of birth? (Needed for retirement horizon and SCSS eligibility later.)
- Citizenship and residential status — Resident Indian, NRI, OCI, or other? (Affects which mutual funds you can hold and tax treatment.)
- Marital status — single, married, divorced, widowed?
- If married: is your spouse working? Roughly what's their income? Do you plan finances jointly or separately?

### Batch 1.2 — Dependents
- Do you have children? If yes, for each: age, and how financially dependent are they on you (fully / partially / no longer)?
- Any special-needs dependents (children, siblings, parents) requiring long-term financial planning?
- Do you have parents you support financially now or expect to in the future? Roughly how much per month, or what kind of obligation?

### Batch 1.3 — Work and health
- What's your employment type — salaried, self-employed, business owner, freelancer, retired, mixed? (This determines EPF/NPS routes.)
- If salaried: does your employer offer EPF? Is NPS available as a workplace benefit?
- Roughly how stable is your income? (Very stable / mostly stable / variable / volatile)
- Any health conditions — yours or in the family — that materially affect insurance needs or emergency fund sizing?

---

## Section 2 — Income, Cash Flow & Tax

**Why this section exists:** establishes monetary capacity, tax position, and how much surplus is actually available for investing. Tax bracket especially matters because it changes which schemes are most efficient.

### Batch 2.1 — Income
- Gross annual income (all sources combined, pre-tax)?
- Sources of income — salary / business / rental / capital gains / dividends / interest / consulting? Roughly what % from each?
- Any major expected income changes in the next 1–3 years (raise, switch, sabbatical, business expansion, retirement)?

### Batch 2.2 — Tax position
- Are you on the **old** or **new** tax regime?
  > Brief explainer if asked: Old regime allows 80C/80D/HRA/home loan interest deductions but has higher slabs. New regime has lower slabs but very few deductions allowed. People with significant 80C investments + rent + home loan usually stay on old; people with no major deductions often prefer new.
- Roughly what's your **marginal tax rate** after current deductions? (10% / 20% / 30%, plus surcharge if applicable.) If unsure: take gross income, subtract rough deductions, and we'll estimate together.

### Batch 2.3 — Expenses and surplus
- Monthly take-home (after tax, EPF, etc.) — average?
- Monthly **fixed** expenses — rent or home loan EMI, school fees, utilities, insurance premiums, household help, subscriptions. Roughly?
- Monthly **variable** expenses — food, fuel, eating out, shopping, entertainment, travel. Roughly?
- After all that, what's the typical monthly surplus? (i.e. money that ends up sitting in savings or going to investments)
- Is the surplus consistent or lumpy? (Some people get bonuses, business owners have spiky income.)

### Batch 2.4 — Loans and obligations
- Active loans / EMIs — for each, capture: type (home / car / personal / education / credit-card-rollover), interest rate, current balance, EMI amount, tenure remaining.
- Any irregular but predictable large outflows? (Annual insurance premium, school fees due Aug, tax payment in March, etc.)

---

## Section 3 — Existing Assets & Portfolio

**Why this section exists:** complete inventory of what they already hold. Detail level here is approximate at the category level — a separate portfolio.md will hold scheme-level details.

### Batch 3.1 — Liquid assets
- Total balance across savings/current accounts?
- Do you maintain a **separate** emergency fund? If yes — where (sweep-FD, liquid fund, separate savings account?), how much, and is it explicitly earmarked?

### Batch 3.2 — Fixed deposits & debt
- Fixed deposits — total value, roughly, and rough tenure ladder (any maturing in next 12 months?)
- Recurring deposits, if any?
- Debt mutual funds — type (liquid / ultra-short / short / corporate / gilt) and total approx?
- Any RBI Floating Rate Bonds, tax-free bonds, or other government bonds?

### Batch 3.3 — Mutual funds (equity / hybrid / ELSS)
- Roughly what's the total mutual fund corpus across equity + hybrid + ELSS?
- Approximate split — equity / hybrid / ELSS / international?
- **Direct or Regular plans?** (Direct plans have ~1% lower expense ratio. Big difference over decades.) If unsure, the way to check: in your CAS or fund statement, fund names show "(Direct)" or no suffix usually means Regular.
- Roughly how many distinct schemes do you hold? (We'll list them in detail in portfolio.md, not now.)

### Batch 3.4 — Government schemes (one of the most overlooked categories)
For each, check applicability and capture:

- **PPF** — do you have an account? Year opened? Current approximate balance? Annual contribution? (15-year lock-in from open date; matures and can be extended in 5-year blocks. EEE tax treatment — exempt at deposit, growth, withdrawal.)
- **EPF / VPF** (if salaried) — current balance? Are you contributing voluntarily beyond mandatory? UAN active and consolidated?
- **NPS** — Tier 1, Tier 2, both? Asset allocation choice (Active / Auto)? Current corpus? Are you using it for the additional ₹50K 80CCD(1B) deduction?
- **Sukanya Samriddhi (SSY)** — only applies if you have a daughter under 10. Open? Balance? Annual contribution?
- **Senior Citizens Savings Scheme (SCSS)** — only applies if 60+ (or 55+ in some early-retirement cases). Applicable now? Used?
- **Post Office schemes** — POMIS, NSC, KVP, post office RD?

### Batch 3.5 — Gold
- **Sovereign Gold Bonds (SGBs)** — which tranches do you hold? Maturity dates? (SGBs pay 2.5% p.a. interest semi-annually and capital gains are tax-free at 8-year maturity. Strictly better than gold ETFs for long holds.)
- **Gold ETFs / digital gold (e.g., Paytm/Augmont) / gold MFs** — approximate value?
- **Physical gold** — jewellery and bullion separately, rough value.

### Batch 3.6 — Equities and alternatives
- Direct stocks — approximate value, themes/concentration (e.g., 80% in 3 stocks vs spread across 30)?
- Cryptocurrency — value if any?
- PMS / AIF / structured products?
- REITs / INVITs?
- Foreign assets — US stocks via LRS, foreign bank accounts? (Has tax disclosure implications.)

### Batch 3.7 — Real estate
- Primary residence — approximate market value, home loan balance and rate if any?
- Investment property — value, rental yield if any, loan if any?
- Plots / agricultural land?

### Batch 3.8 — Insurance assets (separate from pure protection)
- Any **ULIPs**, **endowment**, **money-back**, or **traditional** life insurance policies that mix protection + investment? For each: sum assured, premium, year started, surrender value if known.
  > Note: just record. Don't editorialise during the interview. These often underperform but the assessment is for downstream skills.

---

## Section 4 — Insurance & Protection

**Why this section exists:** investment plans are fragile without proper protection. One uninsured hospitalisation or untimely death can wipe out years of investing.

### Batch 4.1 — Life cover
- Do you have **term life insurance**? Sum assured, annual premium, tenure remaining?
- Rule of thumb: 10–15× annual income is a common starting point for someone with dependents. We're not testing you — just capturing.

### Batch 4.2 — Health cover
- Health insurance — self / family floater / both? Total sum assured?
- Is this employer-provided + personal, or only one? (Employer-provided lapses if you leave the job — risk to flag.)
- Any **critical illness** rider or standalone CI cover?
- **Disability** cover (loss of income from accident/illness)?

### Batch 4.3 — Family
- Health cover for parents, if you support them?
- Health cover for spouse and kids — included in the same floater or separate?

---

## Section 5 — Goals & Time Horizons

**This is the Socratic centerpiece — most time should be spent here.** Many users haven't fully articulated their goals. The job here is partly discovery.

### Batch 5.1 — Open the section

Open with something like:

> "Now we'll talk about goals — this is the most important part. I'll suggest categories one at a time. For each, tell me whether it applies, and if so:
> - What's the target amount in **today's rupees** (don't try to inflation-adjust)
> - What's the target year
> - How critical is it — must-have, should-have, nice-to-have
> - How flexible are you on amount and timing
>
> If a category doesn't apply, just say so. If you have a goal I don't ask about, surface it."

### Batch 5.2 — Discovery prompts (use 2–3 to surface unstated goals)

These help users articulate goals they haven't named. Use them especially if the user seems to have a vague "save for the future" mindset.

- "If you had to imagine your life 10 years from now and it had gone really well financially, what would be different?"
- "What's keeping you up at night, financially?"
- "If you woke up tomorrow with ₹5 crore in your account, what would you do with it?"
- "What's your biggest financial regret so far?"
- "What's the one thing you wish you'd started 5 years ago?"
- "Imagine you got a call from a doctor saying you have to stop working in 5 years. What changes?"

Don't ask all of these — pick 2 that fit the user's energy and where you sense gaps.

### Batch 5.3 — Walk through standard goal categories

Go through each, ask whether it applies, and capture target amount / year / criticality / flexibility:

1. **Emergency fund** — target = 6–12 months of expenses, separately parked. Already set up? At what level?
2. **Retirement** — target retirement age? Desired monthly expense in **today's** rupees? Expected post-retirement lifespan / planning horizon?
3. **Children's education** — for each child: school, undergrad, postgrad? Domestic or abroad? Target year? (Foreign undergrad target ₹1–1.5 Cr today; domestic ₹15–30L; postgrad varies hugely. Help calibrate without leading them.)
4. **Children's marriage** (if culturally relevant for the user) — target amount and year?
5. **Home purchase / upgrade** — target year, target value, downpayment vs full?
6. **Vehicle purchase / replacement** — when, target?
7. **Major travel / experiences** — sabbatical, world trip, big anniversary trip?
8. **Parental care** — medical buffer for parents, retirement support?
9. **Specific large planned expenses** — known surgery, family event, planned career break?
10. **Wealth creation beyond goals** — FIRE (Financial Independence Retire Early)? Legacy / inheritance? Charitable?
11. **Anything else** — explicitly invite goals you haven't asked about.

For each goal that applies, capture as a structured entry:
- Target amount (today's ₹)
- Target year
- Criticality (must-have / should-have / nice-to-have)
- Flexibility on amount (rigid / somewhat flexible / very flexible)
- Flexibility on timing (rigid / somewhat flexible / very flexible)
- Existing earmarked savings toward this goal (if any)
- Notes (special considerations)

### Batch 5.4 — Mid-flight summary

At the end of Section 5, pause and summarise back the goals list, plus key facts from sections 1–4. Ask the user to correct/add. **This is required, not optional** — it's the most common point at which users realise they missed a goal.

---

## Section 6 — Real Risk Tolerance

**Why this section exists:** self-reported risk tolerance is famously unreliable. Use behavioural and scenario questions to triangulate.

### Batch 6.1 — Behavioural history (best signal)
- When markets dropped sharply in March 2020 (COVID crash), how did you respond? Sell out, hold, or invest more? What did you feel?
- Have you ever sold investments because you were scared? Bought because of FOMO? When?
- 2008 crisis (if applicable) — what did you do?

If they weren't investing in any of those periods, move to scenarios.

### Batch 6.2 — Scenario questions
- Hypothetical: your portfolio drops 30% in 6 months. Your honest reaction — sell, hold, or buy more?
- If you had to choose between (A) 8% guaranteed return vs (B) 12% expected return with 25% downside in any given year — which?
- Is there a specific rupee loss number that would cause you to panic-sell? What's that threshold? (Knowing the number is more useful than a percentage.)

### Batch 6.3 — Lock-in and liquidity
- Lock-in tolerance — are you OK with PPF's 15-year lock-in for the tax efficiency? ELSS 3-year? SGB 8-year? NPS lock-in until 60?
- How quickly might you actually need to access investments? (Job loss buffer, medical, family emergency?)
- Are existing liquid buffers enough that long-term investments can stay long-term?

### Batch 6.4 — Anxiety signals
- How often do you check your portfolio? (Daily often signals anxiety; monthly is healthier.)
- Have you ever changed asset allocation reactively after market news? How often?

---

## Section 7 — Constraints, Preferences, Values

### Batch 7.1
- Any **religious or ethical constraints** — Sharia compliance, exclusion of alcohol/tobacco/gambling stocks, ESG preferences?
- Any **asset class aversions** — "I'll never buy gold," "I don't trust stocks," "I won't invest in real estate"? What's behind that view?
- Any **product aversions** based on past experience? (Bad mis-sold ULIP, broker scam, etc.)

### Batch 7.2
- Time available to actively manage portfolio — minimal (set and forget) / moderate (review monthly) / active (review weekly)?
- Tax optimisation priority on a 1–10 scale — how much do you want the agent to lean toward tax-efficient choices even if they sacrifice some return or liquidity?
- Past investment mistakes you've learned from (one or two)?
- Anything else important the agent should know about your preferences?

---

## Section 8 — Knowledge & Behaviour

### Batch 8.1
- Self-rated investment knowledge on a 1–10 scale, where 1 = "what's a mutual fund" and 10 = "I read SEBI circulars for fun"?
- Information sources you currently trust — blogs, YouTube, advisors, books?
- Behavioural patterns you recognise in yourself — FOMO, recency bias (overweighting recent past), herd mentality, anchoring, loss aversion, lifestyle creep?
- One financial habit you'd most like to change?

---

## After Section 8 — Contradictions pass

Don't write goals.md yet. First, run the contradictions sweep described in SKILL.md Step 5. Common ones to scan for:

- Goals total vs realistic surplus + return expectations
- Risk tolerance (real, not claimed) vs return expectations baked into goals
- Goals timing vs lock-in tolerance
- Existing portfolio allocation vs stated risk tolerance
- Insurance gaps that invalidate the plan
- Liquidity needs vs investment horizons
- Tax regime choice vs which deductions/schemes they use
- Stated long-term mindset vs portfolio-checking frequency

Surface 2–5 of these. For each, ask which side they want to revise. Update mental model.

Only then write `goals.md`.
