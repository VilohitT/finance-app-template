---
name: portfolio-grill
description: Conducts a structured interview to capture the user's complete investment portfolio — every holding across mutual funds, debt instruments, government schemes, gold, direct equities, real estate, and insurance — into a single structured portfolio.md file. Use whenever the user wants to build their portfolio file from scratch, "grill me on my portfolio", set up the holdings tracker for an investment agent, refresh portfolio.md after a major change, or capture all current investments in one place. Invoke proactively when the user mentions setting up portfolio tracking, building the data layer for their investment agent, or saying they need to "list out all my investments." Indian-context aware — handles MFs (Direct/Regular, equity/debt/hybrid/ELSS), all government schemes (PPF/EPF/VPF/NPS/SSY/SCSS), SGBs and gold, real estate, and insurance assets. Captures sub-portfolio assignment and goal earmarks per the user's structure in user-principles.md (single-portfolio or multi-entity).
---

# portfolio-grill

A structured interview skill that builds a complete Indian-context investment portfolio file. Designed for one-time comprehensive capture of all current holdings, with sub-portfolio assignment and goal earmarks baked in so downstream skills (`/portfolio-review`, `/fund-allocate`, `/tax-check`) can reason about each holding properly.

The output is a single structured markdown file (`portfolio.md`) that becomes the holdings layer for the investment agent.

## When to use

Trigger when the user wants to:
- Set up the portfolio file for the first time
- Refresh portfolio.md after a material change in holdings
- Capture all current investments in one structured place
- "Grill me on my portfolio"
- Build the holdings tracker for downstream investment skills

This is typically a **one-time** comprehensive interview, taking 30–60 minutes depending on the number of holdings. Re-runs after acquisitions/exits are usually partial — only the affected sections get refreshed, not the whole interview.

## Prerequisites

Before running, the user should ideally have already run:
- `/finance-grill` → `goals.md` (so the agent knows tax bracket, dependents, etc.)
- `/principles-grill` → `user-principles.md` (so the agent knows the sub-portfolio architecture, sleeve targets, and how to ask about assignments)

If `user-principles.md` doesn't exist yet, the grill will ask whether the user wants to (a) defer portfolio-grill until they've set up their investment structure, or (b) proceed assuming a single portfolio (Option A) and tag every holding with the single portfolio name.

## What this skill produces

A single file: `portfolio.md`, saved in the project root.

The exact schema is in `references/portfolio-template.md`. Read that file before starting and use it verbatim as the output structure.

**Section 1.5 (Live MF Holdings) is managed by `scripts/render_portfolio.py`** — the region between `<!-- BEGIN: managed-by-render -->` and `<!-- END: managed-by-render -->` is auto-rendered from `data/transactions.json`. Do NOT hand-write unit counts, current values, or live NAVs anywhere in portfolio.md. Capture cost basis and first-purchase month-year as below; the ledger fills in the rest.

For new MF holdings introduced during the grill, also append a backfill row to `data/transactions.json` (one per scheme, dated to the agreed wave date — ask the user if they want exact-day or mid-month-15th approximation), and run `python scripts/render_portfolio.py --write` at the end to refresh Section 1.5. Use `scripts/backfill_units.py --apply` for the actual append (build a small JSON config for the new schemes; do not hand-edit the ledger).

## Operating principles

### Default: minimal 7-field capture for MFs

For each MF holding, the default capture is **seven fields**:

1. Scheme name (full, AMFI-canonical after inline resolve)
2. Plan — Direct or Regular
3. Capital invested (cost basis, total ₹)
4. Month-year of first investment (e.g., `2025-03`)
5. SIP active y/n (with monthly amount if yes)
6. Sub-portfolio — name from `user-principles.md` (or the single portfolio name)
7. Goal earmark — name from `user-principles.md` §5 (or `unallocated`)

That's it. **Do not ask for** units, current NAV, current value, average purchase NAV, total cost basis from CAS, folio numbers, or exact purchase dates by default. Section 1.5 (auto-rendered from `data/transactions.json` plus live NAVs in `data/market.db`) supplies units, NAVs, and current values. Folio numbers / exact units / average purchase NAV are only needed when a specific tax/redemption decision requires precision — flag them `UNKNOWN — fetch from CAS` in Section 16 and resolve them then.

Why minimal-capture is the default: the ledger backfills units and current values once cost basis + purchase month are known; collecting more upfront makes the interview longer without improving downstream accuracy. The exception is when the user has explicit tax-precision needs (a partial redemption near a holding-period boundary, or an active LTCG harvesting plan) — in those cases, opt into heavy mode.

### Heavy mode (opt-in only)

Do not run heavy mode unless the user explicitly asks for it ("I want exact units / full precision / capture everything"). When opted in, also capture: total units, current NAV, current value, average purchase NAV, total cost basis (from CAS), folio number, first purchase date (exact), most recent purchase date. `references/portfolio-template.md` shows the heavy field list as a fold-out — default to minimal.

### Non-MF holdings still need type-specific fields

FDs, PPF, EPF/VPF, NPS, SGBs, real estate, insurance, etc. don't have a ledger to backfill them, so the type-specific field lists in `references/sections.md` and `references/portfolio-template.md` are required. Minimal mode applies to MFs only.

If any value is missing or the user is unsure, **don't guess.** Mark the field `UNKNOWN — fetch from <source>` (`references/data-sources.md` has the canonical source list) and surface it in Section 16 (Open Items).

### Skip empty buckets fast

Most users won't have holdings in every category. The grill should:
- Open each section with a single Yes/No question: "Do you have any [category]?"
- If No, write `None.` to that section and move on
- If Yes, proceed with the full per-holding capture

Don't pretend to interview about an empty bucket.

### Ledger is the source of truth for MF holdings

`data/transactions.json` is canonical for every MF position. Section 1.5 of `portfolio.md` is auto-rendered from the ledger plus live NAVs. Do not hand-write unit counts, current values, or NAVs anywhere in `portfolio.md`.

In minimal-capture mode this means: when a new MF holding is introduced during the grill, the ledger gets a backfill row (via `scripts/backfill_units.py --apply`) carrying the cost basis and the agreed wave date; the per-scheme block in `portfolio.md` carries only the seven fields. Section 1.5 then renders exact units / NAVs / current values automatically when `scripts/render_portfolio.py --write` runs at the end.

Per-transaction (FIFO-grade) granularity isn't captured at grill time. When `/tax-check` later needs FIFO for a partial redemption, the ledger's transaction rows are the authority; only when those rows are themselves a backfill summary will tax-check ask the user to add detail.

### Sub-portfolio assignment is mandatory

Read `user-principles.md` §1 to learn the user's portfolio architecture:
- **Option A (single portfolio):** every holding gets tagged with the single portfolio name.
- **Option B (multi-entity sub-portfolios):** every holding gets tagged with one of the sub-portfolio names defined in `user-principles.md` §2.

For each holding, ask: "Which sub-portfolio does this belong to?" Default suggestions based on the routing rules in `user-principles.md` §6 (e.g. salary income → designated sub-portfolio), but always allow override and confirm.

For pre-existing holdings accumulated before the user adopted this structure, the user makes the call. Generic heuristics:
- Equity holdings funded from a specific entity's income → that entity's sub-portfolio
- Debt holdings jointly funded or in a joint name → ask explicitly; "joint-locked" or similar tag may apply
- Locked emergency funds → typically tagged separately (per `user-principles.md` §1 if a joint-locked pool is defined)

### Goal earmarking is informational

Read `user-principles.md` §5 to learn the user's goal-bucket structure. For each holding, ask: "Is this earmarked toward any specific goal, or is it general portfolio?"

Goal options come from the user's actual goals (per `goals.md` §5 and `user-principles.md` §5). Common examples:
- `retirement` — toward retirement corpus
- `property` — toward a property purchase goal
- `education` — toward kids' education
- `emergency` — for the emergency-fund bucket
- `legacy` — assets earmarked for legacy / next generation
- `unallocated` — sits in the household pool, not earmarked

Earmarks are informational only. They don't constrain allocation logic; they help the review skill report goal progress.

### Validate scheme names inline, not after the fact

When the user dictates a mutual-fund scheme name (Sections 3, 4, 5, 6, 9 — debt MF, equity MF, ELSS, hybrid, gold MF), **resolve it to an AMFI scheme code in the same turn** rather than collecting all names and resolving in a post-grill pass. Run:

```
python3 scripts/resolve_schemes.py --names "<dictated name>" --quiet
```

Then read the report:
- `HIGH` — confirm the canonical AMFI name + scheme code with the user in one short sentence ("AMFI lists this as 'Parag Parikh Flexi Cap Fund — Direct Plan — Growth', code 122639 — does that match what you hold?") and record both in the working notes.
- `MEDIUM` — surface the candidate plus 1–2 alternates and ask the user which is theirs before recording.
- `LOW` / `NONE` — ask the user to read the scheme name verbatim from their CAS or AMC statement; if still unresolvable, mark `scheme_code: UNKNOWN — fetch from CAS` and move on.

Why inline rather than batch: catches typos and ambiguous names *while the user is still on that scheme*, instead of forcing a second back-and-forth round after the interview. If the database lookup fails (e.g., `schemes` table empty), tell the user and continue capturing names verbatim — a one-shot post-grill `resolve_schemes.py --file portfolio.md` pass will still work, but is the fallback, not the default.

### Direct vs Regular plan capture is critical

For every mutual fund, explicitly capture whether it's a **Direct** or **Regular** plan. Direct plans have ~1% lower expense ratio. Per `principles.md` §3.1, new investments should be Direct only. The review skill will likely flag any Regular plan for switch consideration, so accuracy here matters.

### Indian-context fields for non-MF holdings

For MFs, the seven minimal fields cover the grill (see above). For everything else, the type-specific fields below are required because no ledger backfills them:

- **PPF:** account opening date, current branch/bank, latest balance, FY contributions to date, maturity date
- **EPF/VPF:** UAN, current employer establishment ID, employee+employer contribution history, VPF rate if any
- **NPS:** PRAN, Tier 1 vs Tier 2, scheme preference (Active/Auto), allocation across E/C/G/A
- **SGB tranches:** tranche identifier (e.g., 2020-21 Series VII), issue date, maturity date, units (grams), interest payment dates
- **FDs:** bank, deposit date, maturity date, rate, interest payout frequency
- **Real estate:** location, market value (approximate), loan balance and rate if any
- **Insurance:** policy number, sum assured, premium, policy date, premium-paying party

`references/portfolio-template.md` enumerates exactly which fields each holding type requires.

### Don't editorialise on holdings

If a holding is suboptimal (Regular plan, Gold MF instead of Gold ETF, an inefficient debt fund), **just record it.** The `/portfolio-review` skill will surface optimisation opportunities. The grill captures state; it does not advise.

### Don't recompute tax-relevant past events

Don't try to calculate cost basis from current value and assumed return. Don't reconstruct a missing purchase date by guessing. If data is missing, mark it `UNKNOWN — fetch from <source>` and move on.

## Workflow

### Step 0: Read the reference files

Before starting the conversation, read these:
1. `references/portfolio-template.md` — the exact output schema
2. `references/sections.md` — the section-by-section question playbook
3. `references/data-sources.md` — where each piece of information lives (CAS, UAN, bank passbook, etc.)

Plus the user's setup files:
- `goals.md` — for tax bracket, dependents, employment type, declared holdings hints
- `user-principles.md` — for sub-portfolio architecture, names, goal-bucket structure, routing rules

If `user-principles.md` doesn't exist, ask the user whether to (a) pause this grill and run `/principles-grill` first, or (b) proceed assuming a single portfolio.

### Step 0b: Phase 0 — discover what's already captured

Before starting the interview, run:

```
python3 scripts/discover.py
```

Use the output to:
- **Section 4 (LEDGER HEALTH)** — if `txn_count > 0`, the household already has MF holdings recorded. The Section 1.5 region of `portfolio.md` is auto-rendered from `data/transactions.json`.
- **Section 10 (SUB-PORTFOLIO TOTALS)** — confirms which sub-portfolios already hold value.
- **Section 11 (LEDGER SCHEMES)** — the canonical list of every `(sub_portfolio, scheme_code, scheme_name)` already captured. This is the input to the (a)/(b)/(c) prompt below.

Then, before running the per-scheme capture loop in Sections 3–6, present the Section 11 list back to the user:

> "Your ledger already has these MF holdings recorded:
>   • <scheme 1> (<sub-portfolio>, ₹X)
>   • <scheme 2> (<sub-portfolio>, ₹Y)
>   • …
> Do you want to (a) skip these and only capture *new* holdings, (b) re-confirm one or more (e.g. SIP amount changed, sub-portfolio reassignment), or (c) start over from scratch?"

Default to (a) unless the user signals otherwise. **Never re-grill a scheme that's already in the ledger** without explicit confirmation — the ledger is the source of truth for MF holdings.

If `discover.py` reports a hard blocker (`LEDGER EMPTY`), this is fine for a first-time grill — the ledger will be populated as you go.

### Step 1: Set expectations

Open with a brief intro along these lines:

> "I'm going to walk through every category of investment you might hold and capture the details. This typically takes 20–40 minutes in **minimal-capture mode**, which is the default. We'll go category by category — 14 sections total. Most categories will be a single 'no' and we move on.
>
> A few ground rules:
> - **For mutual funds, I'll capture seven things per scheme:** scheme name, Direct/Regular, capital invested (cost basis), month-year of first investment, whether SIP is active (and monthly amount), sub-portfolio, and goal earmark. Units, NAVs, and current values are auto-rendered from your ledger.
> - **For non-MF holdings (FDs, PPF, EPF, NPS, SGBs, real estate, insurance):** I'll need the type-specific fields, since there's no ledger to backfill them.
> - If a value isn't to hand, say so — we'll flag it `UNKNOWN — fetch from <source>`. Don't guess.
> - If you want **heavy mode** (full precision: exact units, NAVs, folios, average purchase NAVs), say so now and I'll switch.
>
> Ready to start?"

Wait for confirmation. If they want to fetch CAS first, pause; otherwise proceed.

### Step 2: Run the 14 sections in order

Run sections in this order, following `references/sections.md`:

1. **Liquid** — savings, current accounts, sweep FDs
2. **Fixed deposits** — bank and corporate, with maturity ladder
3. **Debt mutual funds** — per scheme summary
4. **Equity mutual funds** — per scheme summary, including hybrid (equity-oriented)
5. **ELSS** — separately to capture lock-in dates
6. **Hybrid / Multi-asset / BAF** — non-equity-oriented hybrid and multi-asset funds
7. **Government schemes** — PPF, EPF/VPF, NPS, SSY, SCSS, post office schemes
8. **Bonds** — RBI FRB, tax-free bonds, govt bonds
9. **Gold** — SGB tranches, Gold ETFs, Gold MFs, digital gold, physical gold (jewellery vs bullion separate)
10. **Direct equities** — per stock summary
11. **Real estate** — primary residence, investment, plots
12. **Insurance assets** — pure protection (term, health) and any mixed (ULIPs, endowments)
13. **Alternatives** — crypto, PMS, AIF, REITs, INVITs, foreign assets, anything else
14. **Liabilities** — loans, EMIs, credit card balances (for completeness; portfolio is net-of-debt)

Within each section, follow the question batches in `references/sections.md`.

For each holding, capture every required field. Don't skip fields — flag UNKNOWN if needed.

### Step 3: Mid-flight summary check

After Section 9 (Gold), pause and summarise back what you've captured so far:

> "Before we continue, here's what I've captured so far:
> - [bullet summary of liquid + FDs]
> - [bullet summary of MF holdings — count by category, total value, sub-portfolio split]
> - [bullet summary of government schemes]
> - [bullet summary of gold]
>
> Anything missing or wrong? Any holding I haven't asked about that you want to add?"

This is especially important because users sometimes forget less-common holdings (RBI bonds, post office schemes, an old direct stock, an inherited gold coin) until prompted to review.

### Step 4: Run sections 10–14

Continue with direct equities, real estate, insurance, alternatives, liabilities.

### Step 5: Reconciliation pass

After all 14 sections, do a reconciliation:

- **Total household corpus computed** from the file should match what the user expects (cross-check against `goals.md` §3 totals if available)
- **Sub-portfolio split** — what % of investable corpus is in each sub-portfolio? Does the user think that mix is right?
- **Goal earmark coverage** — what % of corpus is earmarked vs unallocated?
- **Plan check** — any Regular plans flagged?
- **Scheme code coverage** — every MF scheme in Sections 3, 4, 5, 6, 9 should have an AMFI scheme code resolved during the interview. As a safety net, run the resolver against the working list of newly-captured names *before* writing `portfolio.md`:

  ```
  python3 scripts/resolve_schemes.py --names "<Name 1>, <Name 2>, …" --quiet
  ```

  Use `--names` (not `--file`) at this point — `portfolio.md` doesn't exist yet in this Step 5 reconciliation pass. Pass only schemes captured *during this grill*. Reconcile any LOW/NONE outputs with the user before writing the final file.

- **Any holdings still UNKNOWN** — list every field still pending

Surface tensions / oddities. Examples:
- "Your `goals.md` says you have ₹X emergency fund, but the FDs we captured total ₹Y. Is there another bucket?"
- "All your equity MFs are tagged 'X sub-portfolio', but `goals.md` mentions joint household sources. Do you want to reassign any?"

### Step 6: Write portfolio.md

Generate the file using `references/portfolio-template.md` exactly. Conventions:

- `last_updated:` — today's date in ISO format (YYYY-MM-DD)
- `last_grilled_by: portfolio-grill v1`
- `cost_basis_granularity: minimal-capture` (default) or `per-folio summary` if heavy mode was used
- `transactions_csv_present: false`
- Use **`UNKNOWN — fetch from <source>`** for missing fields, where `<source>` is the specific document/portal to consult
- Use **`N/A`** for categories with no holdings
- Round currency to nearest rupee or hundred rupees as appropriate
- ISO format dates (YYYY-MM-DD) wherever possible
- Sub-portfolio: per `user-principles.md` §2
- Goal earmark: per `user-principles.md` §5
- Section 16 ("Open Items") lists every UNKNOWN field as a checklist
- Section 17 ("Reconciliation Notes") records tensions surfaced and how the user resolved them

Save the file to the project root unless the user specifies otherwise.

### Step 7: Close out

Tell the user:
- Where the file is saved
- A summary: total household corpus, sub-portfolio split, number of distinct schemes, key open items
- That this file is the input for downstream investment skills, so accuracy matters
- That open items should be resolved soon (each has a fetch source noted)
- A reminder about the per-folio limitation — for accurate partial-redemption tax math, transaction-level data will eventually be needed
- Suggest re-running portfolio-grill (or doing a partial refresh) after any material change: new SIP started/stopped, lump sum invested, redemption, scheme switch, change in PPF/NPS contributions, new policy, new property

End by asking: "Anything else to capture or revisit before we close out?"

## Key reminders

- **Capture, don't advise.** No commentary on whether holdings are good/bad. The review skill handles that.
- **Precision over speed.** Better to flag UNKNOWN than to write a guess as fact.
- **Skip empty buckets.** Don't pretend to interview about something the user has zero of.
- **Sub-portfolio assignment is mandatory** — names from `user-principles.md` §2.
- **Goal earmark is informational** — names from `user-principles.md` §5.
- **Direct vs Regular plan check** for every MF — this is a known optimisation lever.
- **Indian-context fields** for each scheme type — folio numbers, PRANs, tranche IDs, etc.
- **Respect "I don't know".** Flag and move on; don't drag the conversation chasing a missing folio number.
