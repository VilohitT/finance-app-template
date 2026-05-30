---
name: principles-grill
description: Conducts a structured interview to capture the user's investment-structure choices — household architecture (single portfolio or multi-entity sub-portfolios), sleeve targets per sub-portfolio, glide paths, goal-bucket overlay, money routing rules, tax regime committed, vehicles in use (PPF/EPF/VPF/NPS/SCSS/SSY/SGB), deployment priority overrides, drift correction policy, and STP threshold. Writes user-principles.md, the user-side companion to principles.md. Use after /finance-grill once goals.md is populated, before /portfolio-grill (which needs to know the sub-portfolio names). Re-run when household composition materially changes (marriage, new dependent, retirement of an entity), when allocation philosophy shifts after a lived bear market, or when the user wants to revise their sleeve targets. Indian-context aware (PPF/EPF/VPF/NPS/SCSS/SSY vehicles, Old vs New Regime, SEBI category vocabulary for sleeve targets).
---

# principles-grill

A structured interview skill that captures the user's *structural choices* on top of the universal framework in `principles.md`. The output is `user-principles.md` — the document downstream skills (`portfolio-grill`, `portfolio-review`, `fund-allocate`) read for sub-portfolio names, sleeve targets, glide paths, routing rules, regime, and vehicle choices.

`principles.md` describes the framework; `user-principles.md` describes the user's instance of that framework.

## When to use

Trigger this skill when:

- The user has just completed `/finance-grill` (so `goals.md` exists)
- They say "set up my investment structure" / "design my allocation" / "what should my sleeve targets be"
- A material change in household composition (marriage, new dependent, entity retirement) means the structure needs to be re-thought
- After a lived bear market when the user's risk tolerance has been revised
- The user wants to revise specific choices (e.g., "I want to add an international allocation" — partial refresh)

Typical full run: 10-15 minutes. Partial refresh of one or two sections: 3-5 minutes.

## Prerequisites

- `goals.md` should exist (run `/finance-grill` first). The skill reads it for: tax bracket, dependents, employment type, risk tolerance, retirement target, income sources, surplus.
- `principles.md` exists in the template (universal framework, not user-specific). The skill cites it for context but doesn't modify it.

If `goals.md` doesn't exist, the skill stops and tells the user to run `/finance-grill` first.

## What this skill produces

A single file: `user-principles.md`, saved at the project root.

Structure (sections will be present in the output):

```
# Your Investment Configuration
last_updated: YYYY-MM-DD
populated_by: principles-grill v1
review_due: <today + 12 months>

## 1. Household architecture
   - Option A (single portfolio) or Option B (multi-entity sub-portfolios)
   - Rationale

## 2. Sub-portfolios
   - Per sub-portfolio: name, holder/role, source of capital

## 3. Sleeve targets per sub-portfolio
   - Per sub-portfolio: equity / debt / gold (+ optional international, other)
   - Drift bands (default ±5pp)

## 4. Glide paths
   - Per sub-portfolio: waypoint allocations and dates

## 5. Goal-bucket overlay
   - Goals from goals.md mapped to sub-portfolios
   - Glide schedule per dated goal

## 6. Money routing rules
   - Per inflow source: default sub-portfolio
   - Flexibility rules for over-rides

## 7. Tax regime committed (this FY)
   - Per filer: New / Old / pending

## 8. Vehicles in use / planned
   - PPF, EPF/VPF, NPS Tier 1, SCSS, SSY, SGB
   - Per vehicle: holder(s), current/target contributions

## 9. Deployment priority
   - Default ladder from principles.md §4.1, or user overrides

## 10. Drift correction policy
   - Threshold (default 5pp)
   - Prefer flows vs sales (default: flows)

## 11. STP threshold
   - Lump size triggering STP vs direct (default ₹3L for equity)

## 12. Notes
   - Any other structural choices, exclusions, philosophy notes
```

## Operating principles

### Read goals.md before asking anything

The grill's questions adapt to what's already in `goals.md`:
- If `goals.md` says "single, no dependents, salaried" → Option A is the natural default; ask anyway but recommend.
- If `goals.md` says "household pooled with parents, two earners" → Option B should be considered.
- If `goals.md` records a 30% tax bracket and "tax priority 3/10" → use the New Regime default in §7 and the standard debt ladder in §9.
- If `goals.md` records a retirement target with a year, use that year as the terminal waypoint in §4.

The grill never re-asks information that's already in `goals.md` — but does cite it ("per your goals.md, retirement target is 2051 — should the user sub-portfolio's terminal glide-path waypoint be 2051?").

### Frame Option A vs Option B honestly

Many users default to Option B (sub-portfolios) when Option A (single portfolio) is simpler and equally valid. Sub-portfolios make sense when:
- Multiple earners in the same household have materially different effective horizons (e.g. 20-year vs 5-year retirement windows)
- Different entities have different tax positions and you want routing flexibility
- A meaningful pool needs to be locked away from rest (e.g. an emergency fund or a goal earmark)

If none of those apply, Option A is the right call. The grill should *recommend* Option A in those cases, not blindly default to Option B.

### Sleeve targets — anchor on horizon, not age

Per `principles.md` §1.8, the right anchor is the actual horizon of the capital, not the holder's age. The grill explicitly asks:
- "What's the effective horizon of this sub-portfolio's capital? How many years until you'd need to draw it down materially?"
- "Does the holder have income covering their monthly expenses, so this corpus doesn't need to fund cash flow?"

A 60-year-old whose pension covers expenses has a 20+ year horizon on the corpus → can run equity-heavy. A 25-year-old saving for a 2-year property goal has a 2-year horizon → debt-heavy on that capital.

### Glide paths are optional but useful for dated goals

For undated, long-horizon goals (retirement 25+ years out), a glide path is useful but not urgent — the agent applies the static target until the goal is closer.

For dated, near-term goals (property in 7 years, education in 10 years), glide paths are important because they encode "shift to debt as the date approaches." The grill asks for waypoints when the user names a dated goal in `goals.md`.

Default waypoint structure for a long-horizon retirement goal: terminal (target date) → T-3 → T-7 → today. The grill suggests a default schedule and lets the user override.

### Routing rules are explicit, not assumed

For multi-entity households, money routing is a frequent source of confusion. The grill captures explicit rules:
- "Where does your monthly salary surplus go by default?"
- "If a tax-deductible vehicle (PPF) is underfilled in entity A but maxed in entity B, can a transfer to A happen? Under what circumstances?"
- "Joint expenses: which sub-portfolio funds them?"

Capture these explicitly so downstream skills can apply them consistently.

### Tax regime is a real decision

Many users assume "New Regime is better because slabs are lower." That's often but not always true — for users with significant 80C / 80CCD / 80D deductions under Old Regime, the math can flip. The grill:
- Reads `goals.md` for tax bracket and current declared regime
- Asks the user whether they've actually computed both regimes for this FY
- If yes: capture the committed choice
- If no: capture the current default and flag "compare both regimes this FY" as an open item

This is a recurring annual decision (per `principles.md` §4.2) — the grill records that.

### Don't editorialise on user choices

If the user wants 100% equity and is in their 50s, the grill records it (with a flag to revisit) rather than refusing or lecturing. The grill captures state; `/portfolio-review` surfaces principle-mismatches as findings.

## Workflow

### Step 0 — Read prerequisites

Read in order:
1. `goals.md` — verify it exists; if missing, stop and tell the user to run `/finance-grill` first
2. `principles.md` — for context (the framework the user's choices configure)
3. `user-principles.md` — if it exists, this is a refresh or partial-update run; read existing content

### Step 1 — Set expectations

Open with a brief intro:

> "I'm going to capture your investment-structure choices in `user-principles.md`. This sits alongside `principles.md` (the universal framework) and tells downstream skills how *you specifically* want money managed.
>
> 12 sections, roughly 10-15 minutes. We'll cover:
>   1. Household architecture — single portfolio or multiple sub-portfolios?
>   2. Sub-portfolio names and holders (if multiple)
>   3. Sleeve targets per sub-portfolio (equity/debt/gold %)
>   4. Glide paths (how targets shift as goal dates approach)
>   5. Goal-bucket overlay
>   6. Money routing rules
>   7. Tax regime committed this FY
>   8. Vehicles in use or planned (PPF, EPF, NPS, etc.)
>   9. Deployment priority — default or overrides
>  10. Drift correction policy
>  11. STP threshold
>  12. Any other notes
>
> I'll cite your `goals.md` where relevant so we're not re-asking things you've already answered.
>
> Ready to start?"

Wait for confirmation. Allow the user to scope to specific sections ("just §3 and §6, the rest is already set").

### Step 2 — Run the 12 sections

#### §1. Household architecture

Ask:

> "Looking at your `goals.md`, you've described <single earner / household with X / etc.>. Two ways to structure this:
>
> **Option A — Single portfolio:** one allocation target, one set of sleeve %s, one glide path. Simplest. Right when there's one investor (or pooled household with shared goals and horizons).
>
> **Option B — Multi-entity sub-portfolios:** separate sleeve targets, glide paths, and routing rules per entity. Right when entities have materially different horizons or tax positions.
>
> Given your situation, I'd recommend [Option A / Option B] because [reasoning]. Which do you want?"

Capture the choice with rationale.

#### §2. Sub-portfolios (if Option B)

For each sub-portfolio:
- Name (e.g., "me", "spouse", "father-pooled", "joint-locked")
- Holder / role
- Source of capital (income source funding it)
- Any locked-allocation constraints

#### §3. Sleeve targets per sub-portfolio

For each (or the single) sub-portfolio:
- Equity %
- Debt %
- Gold %
- Other? (international, REITs)
- Drift band (default ±5pp)

Reference `principles.md` §2.4 for the within-equity SAA structure (Nifty 50 48% / NN50 12% / Flexicap 22% / Mid 7% / Small 4% / Intl 7% defaults). Ask whether to use those defaults or override.

For each sub-portfolio, also capture: effective horizon, whether the holder's income covers monthly expenses (so corpus doesn't need to fund cash flow).

#### §4. Glide paths

For each sub-portfolio with a dated goal driving allocation shifts:
- Terminal waypoint (allocation at the goal date)
- Intermediate waypoints (T-3, T-7, etc.)
- Today's allocation (already in §3)

For undated long-horizon corpus: glide path is optional; skip or use a default if the user prefers.

#### §5. Goal-bucket overlay

For each goal in `goals.md` §5:
- Which sub-portfolio funds it?
- Is it earmarked (allocation locked toward this goal) or just a target the household pool flows toward?
- For dated earmarks: glide schedule

#### §6. Money routing rules

For each inflow named in `goals.md` §2 (salary, business income, pension, etc.):
- Default sub-portfolio it routes to
- Over-ride flexibility (when can the default be deviated from?)

#### §7. Tax regime committed (this FY)

For each filer:
- Current declared regime: New / Old / pending
- Have both been computed for this FY?
- If yes: committed choice
- If no: flag "regime comparison overdue" as an open item; record current default

#### §8. Vehicles in use / planned

For each Indian vehicle:
- **PPF**: which holder(s) have an account; current FY contribution; target
- **EPF**: salaried holder(s) only; current basic+DA driving employee contribution
- **VPF**: salaried holder(s); current/target contribution within ₹2.5L tax-free threshold
- **NPS Tier 1**: which holder; route (employer 80CCD(2) / personal 80CCD(1B)); current contribution
- **SCSS**: only relevant if a holder is 60+ or approaching
- **SSY**: only relevant if there's a daughter under 10
- **SGB**: status — historical holdings only (issuance paused); revisit if resumed

Capture per-vehicle holder + current contribution + target.

#### §9. Deployment priority

Show the default ladder from `principles.md` §4.1:
> 1. PPF (per holder)
> 2. NPS Tier 1 via 80CCD(2) (employer route)
> 3. NPS Tier 1 personal 80CCD(1B) (Old Regime only)
> 4. VPF (salaried)
> 5. SCSS (60+)
> 6. SGB tranche (if RBI issuance resumed)
> 7. SIP / STP into category-shaped needs

Ask: "Use this default or override the ordering?"

Capture any overrides with rationale.

#### §10. Drift correction policy

Ask:
- Threshold for action (default 5pp)
- Prefer flows vs sales when drift exceeds threshold (default: flows per `principles.md` §6.3)

#### §11. STP threshold

Ask:
- Lump size into equity that triggers STP staging (default ₹3L)
- STP duration default (default 6 months for isolated lumps; 3 per lump for sequential)

#### §12. Notes

Open-ended:
- Any AMCs to prefer or avoid
- Ethical exclusions
- Specific products to always avoid (e.g., conservative hybrids)
- Anything else structural

### Step 3 — Reconciliation

After all 12 sections, summarise and check for tensions:
- Sub-portfolio sleeve targets vs `goals.md` risk tolerance — coherent?
- Glide paths vs goal dates — math works?
- Routing rules vs income sources — every inflow has a default destination?
- Tax regime vs vehicles — if Old Regime, NPS personal 80CCD(1B) makes sense; if New Regime, only employer 80CCD(2) is worth using
- Vehicle contributions vs surplus in `goals.md` — is the planned annual contribution achievable?

Surface tensions for the user to resolve.

### Step 4 — Write user-principles.md

Generate the file in the structure outlined above. Conventions:

- `last_updated:` — today's date in ISO format (YYYY-MM-DD)
- `populated_by: principles-grill v1`
- `review_due:` — today + 12 months
- Use **`UNKNOWN`** for fields the user couldn't answer
- Use **`N/A`** for fields that don't apply
- Reference `principles.md` for the framework rules being configured

Save at the project root.

### Step 5 — Close out

Tell the user:
- Where the file is saved
- Summary: architecture chosen (A or B), number of sub-portfolios, key sleeve targets
- Open items (e.g., regime comparison overdue)
- Next step: `/portfolio-grill` to capture every holding into `portfolio.md`
- Re-run principles-grill when household composition changes, after a lived bear market, or annually

## Key reminders

- **Read `goals.md` first.** Don't re-ask things already captured.
- **Anchor sleeve targets on horizon, not age.** Per `principles.md` §1.8.
- **Recommend Option A when it fits.** Don't default to Option B reflexively.
- **Glide paths are optional** for undated long-horizon goals.
- **Routing rules are explicit.** Capture defaults and over-ride conditions.
- **Tax regime is annual.** Flag overdue comparisons as open items.
- **Don't editorialise.** Capture user choices even when principle-borderline; `/portfolio-review` surfaces mismatches.
- **Reconcile before writing.** Surface coherence-tensions to the user.
