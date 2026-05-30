# laws/index.md

last_updated: 2026-05-03
last_verified_against_budget: Union Budget 2026 (announced Feb 2026, effective FY 2026-27 mostly; some provisions live from FY 2025-26)
next_refresh_due: After next Union Budget OR any mid-year notification material to MF/PPF/EPF/NPS/SGB/SCSS

> **What this folder is.** A reference layer for the investment agent. Captures Indian tax and scheme rules for the asset classes and instruments in this portfolio. Read by `tax-check`, `portfolio-review`, and `fund-allocate` before any recommendation that depends on rule-specific facts.
>
> **What this folder is not.** Legal advice. The user is not a lawyer and neither is the agent. Any recommendation that hinges on a specific rule in this folder should encourage the user to verify against current Income Tax Department / SEBI / RBI / AMFI publications before acting.

---

## Files in this folder

| File | Covers | Last verified | Verify by |
|---|---|---|---|
| `capital-gains.md` | LTCG/STCG framework, holding periods, harvesting, set-off rules | 2026-05-03 | After every Budget |
| `regime-comparison.md` | Old vs new tax regime slabs, rebate, surcharge, decision logic | 2026-05-03 | After every Budget |
| `equity-mf.md` | Equity-oriented MFs incl. ELSS, hybrid (equity-oriented) | 2026-05-03 | After every Budget |
| `debt-mf.md` | Debt MFs — critical post-April-2023 changes, three regimes by purchase date | 2026-05-03 | After every Budget |
| `ppf.md` | PPF rules, eligibility, lock-in, withdrawal, tax treatment | 2026-05-03 | Quarterly (rate revisions) + Budget |
| `epf-vpf.md` | EPF, VPF, ₹2.5L threshold, taxation of excess interest | 2026-05-03 | Annually (rate announced Feb-Mar) + Budget |
| `nps.md` | NPS Tier 1 / Tier 2, all 80CCD provisions, exit rules | 2026-05-03 | After every Budget |
| `scss.md` | SCSS — relevant for father's eligibility window 2028 onward | 2026-05-03 | Quarterly (rate revisions) + Budget |
| `gold.md` | SGBs (currently paused), gold ETFs, digital, physical, all tax treatments | 2026-05-03 | After every Budget + RBI tranche announcements |
| `insurance.md` | Term life, health, ULIPs, 80C/80D provisions, Section 10(10D) | 2026-05-03 | After every Budget |
| `sebi-categories.md` | SEBI MF categorisation rules for accurate classification | 2026-05-03 | When SEBI revises categorisation circular |

---

## Staleness rules

The agent treats data as **stale** if any of these are true:
- `last_verified_against_budget` is older than the most recent passed Union Budget
- A mid-year notification has been published in a relevant area and `last_updated` precedes it
- `last_updated` is more than 12 months old regardless of Budget cycle

When invoking `tax-check` against a stale file, the agent does not refuse outright — it returns the answer with an explicit "this rule was last verified for Budget XYZ; please confirm against current Income Tax / SEBI / RBI sources before acting on a material decision" caveat.

To refresh, the user runs the `laws-refresh` skill. That skill proposes diffs for review; nothing updates silently.

---

## Conventions used inside the files

- **Section dates and rates carry their own footers.** Each file states `last_updated`, `last_verified_against_budget`, and a per-section `as_of_quarter` for fields like interest rates.
- **Three-state field labelling.** Where the FY 2025-26 / FY 2026-27 picture differs, both are shown side by side. Where a field is regime-dependent, both Old and New columns appear.
- **Source citations inline.** Each rule has a short citation pointing to its primary source (Income Tax Act section, SEBI circular reference, AMFI page, RBI press release). Citations are for the user's verification convenience, not legal authority.
- **No interpretation in the laws files.** These files capture *what the rule is*. Whether it applies to the user is for `tax-check` and `portfolio-review` to determine using `goals.md` + `principles.md` + the relevant laws file.

---

## How to use this folder

**For `tax-check` (the most frequent caller):**
1. Identify the asset class and transaction type
2. Read the relevant laws file (e.g. `equity-mf.md` for an equity MF redemption)
3. Cross-check holding period, gain type, applicable rate
4. Apply the user's bracket and regime from `goals.md`
5. Return: gain type, gain amount, tax owed, net proceeds, flags

**For `portfolio-review`:**
1. Read `capital-gains.md` to understand harvesting opportunities
2. Read `regime-comparison.md` annually for the regime decision
3. Read instrument-specific files for any holdings the review touches

**For `fund-allocate`:**
1. Read `equity-mf.md` / `debt-mf.md` for tax position of the addition
2. Read `ppf.md`, `nps.md`, `epf-vpf.md` to determine if scheme capacity should be filled before MF capacity
3. Read `regime-comparison.md` to verify regime-dependent assumptions

---

## Open caveats — read these before relying on this folder

1. **SGB issuance is paused.** No new tranches since Feb 2024. Government confirmed no fresh issuance plans in Budget 2025. Budget 2026 added that maturity tax-exemption now only applies to investors who bought directly from RBI (not secondary market). See `gold.md` for full picture. Principles.md Section 2.7 may need revision if the user wants to proceed without fresh SGB capacity.
2. **EPF interest rate** for FY 2025-26 was announced by EPFO in Feb-Mar 2026 — verify the exact figure in `epf-vpf.md`'s rate section before quoting in any user-facing output.
3. **Tax regime is a household-level annual decision.** `regime-comparison.md` walks through the trade-off given the user's household profile. Decision is overdue per goals.md Section 9.
4. **Income Tax Act 2025** comes into effect from 1 April 2026. Most provisions carry over with renumbered sections. Where a section number is given in this folder, the corresponding new section number is noted alongside where known. The agent should expect some renumbering churn through FY 2026-27.

---

## What's deliberately not in this folder

- **Foreign tax** (LRS-related US holdings, FATCA, etc.) — user has no foreign assets per goals.md. Add a `foreign.md` if this changes.
- **HUF formation, gift loops, complex structuring** — user's tax priority is 3/10 per goals.md. The agent does not pursue these.
- **Estate / inheritance tax planning** — out of scope for the current goals doc.
- **Securities transaction tax (STT) detail** beyond the broad fact that it applies to listed equity / equity MF transactions — not material to investing decisions at this user's scale.
- **TDS for NRIs** — user is Resident Indian; this would matter only if status changes.

If any of these become relevant, add a file and update this index.
