---
name: finance-grill
description: Conducts a deep, structured interview to capture all financial details, life context, and investment goals needed for personalised investment planning in the Indian context. Produces a complete goals.md file as output. Use whenever the user wants to set up an investment agent or planner, articulate financial goals from scratch, "grill me about my finances", build a foundation goals doc, or systematically think through retirement / education / wealth goals. Invoke proactively when the user mentions setting up a portfolio plan, financial planning, or wanting their financial profile captured — even if they don't say the word "skill". Covers mutual funds, debt, gold, government schemes (PPF/EPF/VPF/NPS/SSY/SCSS), SGBs, real estate, insurance, tax position, and goals across all standard life categories.
---

# finance-grill

A Socratic interview skill that builds a complete Indian-context financial profile by asking the right questions in the right order. Designed for users who don't fully know their goals yet — it helps them discover those goals through guided questioning, not just extract them.

The output is a single structured markdown file (`goals.md`) that becomes the foundation document for downstream investment skills (portfolio review, fresh-fund allocation, tax checks, etc.).

## When to use

Trigger this skill when the user wants to:
- Set up an investment agent or planner and needs a baseline goals doc
- "Grill me on my finances" / "help me figure out my financial goals"
- Build a financial plan from scratch
- Capture their full financial profile in a structured way
- Refresh / redo their goals doc after a major life change

This is typically a **one-time** comprehensive interview taking 20–40 minutes. After it's done, the user reviews and edits `goals.md`, and downstream skills read from it.

## What this skill produces

A single file: `goals.md`, saved in the user's current working directory unless they specify otherwise.

The exact schema is in `references/goals-template.md`. Read that file before starting and use it verbatim as the output structure.

## Operating principles

### Socratic, not extractive

Many users don't have crisp answers to "what are your financial goals?" The job is to help them discover those goals, not demand they already exist. Use scenarios, examples, and gentle probing.

When a user says something vague ("save for the future"), don't accept it. Probe:
- "Future how far out — 5 years, 20 years, retirement?"
- "Save how much, roughly? Today's rupees is fine."
- "What's the future state you're saving for? A house? Kids' education? Just security?"

`references/techniques.md` has a detailed playbook of Socratic moves — read it before starting.

### One section at a time, batched questions

Never dump all questions at once. Run section by section. Within each section, ask 4–8 related questions per turn. Wait for the user's response, fill in the structure, then move on.

### Adapt based on answers

- If single with no kids and no plans for them → skip kids' education, kids' marriage, SSY
- If salaried → focus on EPF/VPF and NPS Tier 1 (employer route)
- If self-employed → focus on PPF, NPS Tier 1 (individual), self-funded retirement
- If they say they only invest in MFs/gold → probe whether they've considered tax-efficient government schemes
- If 60+ → ask about SCSS
- If retired → skip "active income" questions and pivot to drawdown planning

### Push back on internal contradictions

The most valuable thing this interview does is surface contradictions the user hasn't noticed. Common ones:
- Wants 15%+ returns but says they can't tolerate any losses
- Wants to invest aggressively but has no emergency fund
- Wants to retire in 10 years but has saved < 10× annual expenses
- Says they're long-term-oriented but checks portfolio daily
- Wants ELSS for tax savings but says they need full liquidity

When you spot a contradiction, name it kindly: "I'm noticing a tension between X and Y — which side do you want to revise?"

### Real risk tolerance ≠ claimed risk tolerance

Don't trust self-reports like "I'm moderate risk." That tells you almost nothing. Use scenario questions (see `references/techniques.md`). What people actually did in March 2020 / 2008 / a personal financial setback tells you more than what they claim they would do.

### Educate briefly where needed

The user is not assumed to be an investing expert. When asking about PPF, briefly explain it (one line). When asking about old vs new tax regime, give a one-liner. Don't lecture. Just enough so the answer is informed.

Example:
> "Are you on the old or new tax regime? (Old has 80C/80D/HRA deductions; new has lower slabs but fewer deductions. Most salaried with rent + 80C investments stay on old; pure salaried with no deductions often prefer new.)"

### Don't editorialise on their existing choices

If they hold ULIPs or endowment policies you wouldn't recommend, just record it and flag it for later review. The interview captures state — it doesn't dispense advice. A separate downstream skill will surface optimisation opportunities.

### Capture absolute numbers, not just percentages

"I save about 30% of my income" is less useful than "I save about ₹80,000/month." Always nudge toward absolute rupee figures. Today's rupees is fine; don't ask the user to inflation-adjust.

## Workflow

### Step 0: Read the reference files

Before starting the conversation, read these in order:
1. `references/goals-template.md` — the exact output schema
2. `references/questions.md` — the full question bank, organised by section
3. `references/techniques.md` — Socratic techniques, scenario prompts, vague-answer handling

### Step 0b: Phase 0 — programmatic re-grill trigger check

Before deciding whether this is a first-time grill or a refresh, run from the project root:

```
python3 scripts/check_freshness.py goals
```

The script reads `goals.md`'s `last_updated`, `review_due`, and `missing_review_due` headers and prints a structured status block (or `NO_GOALS_FILE` if there isn't one yet). Exit code is `0` if the file is within its review window, `3` if overdue, missing the `review_due` field, or absent.

Decision tree (use the script's output verbatim — do not re-read goals.md prose to second-guess it):
- **`NO_GOALS_FILE`** → first-time grill; run all 8 sections.
- **`overdue: False` and `missing_review_due: False`** → quote the `last_updated` and `review_due` dates back to the user, then ask whether they want a *full* re-grill or a *partial refresh* (e.g., only Sections 2 and 5 because their income changed). Default to partial unless they ask otherwise — full re-grills overwrite settled answers.
- **`overdue: True`** → tell the user the file is past its `review_due` date, recommend a full re-grill, and proceed once they confirm.
- **`missing_review_due: True` (file present but lacks `review_due`)** → quote the `last_updated` date back to the user, explain that the file has no `review_due` field, and ask whether they want (a) a partial refresh of named sections, (b) a full re-grill, or (c) just to set a `review_due` date (default: `last_updated + 6 months`). Whichever path they choose, write a `review_due` value when updating `goals.md` so future runs land in a normal branch.

If the user asks for a partial refresh, restrict the interview to the named sections and update only those in `goals.md`. For a full re-grill, run all 8 sections and overwrite.

### Step 1: Set expectations

Open with a brief intro along these lines:

> "I'm going to ask you a structured set of questions to build out your financial profile. This will take roughly 20–40 minutes depending on how much detail you have at hand. We'll go section by section — 8 sections total. Within each, I'll ask several related questions.
>
> A few ground rules:
> - If you don't know an answer, say so and we'll flag it for follow-up. Don't guess.
> - Today's rupees are fine. I don't need you to inflation-adjust anything.
> - Round numbers are fine. Approximate is better than skipped.
> - At the end, I'll write everything to `goals.md`, surface any contradictions, and you can review/edit.
>
> Ready to start?"

Wait for confirmation. If they want to dive in, proceed.

### Step 2: Run the eight sections in order

Run sections in this order, following `references/questions.md`:

1. **Personal & eligibility context** — DOB, residency, marital status, dependents, employment type, parental obligations, health
2. **Income, cash flow, and tax** — gross income, take-home, tax regime, expenses, surplus, EMIs
3. **Existing assets and portfolio** — savings, FDs, MFs, government schemes, gold, stocks, real estate, insurance assets, alts
4. **Insurance & protection** — term cover, health cover, parents' cover, ULIPs to flag
5. **Goals & time horizons** — the Socratic centerpiece (most time spent here)
6. **Real risk tolerance** — behavioral scenarios, lock-in tolerance, panic threshold
7. **Constraints, preferences, values** — ethical exclusions, aversions, time available
8. **Knowledge & behavior** — self-rated knowledge, check frequency, biases recognised

Within each section, follow the question batches and probing strategies in `questions.md`.

### Step 3: Mid-flight summary check

After Section 5 (goals), pause and summarise back what you've heard:

> "Before we go further, here's what I've captured so far. Please correct anything that's wrong or missing:
> - [bullet summary of personal context]
> - [bullet summary of income/expenses]
> - [bullet summary of existing assets]
> - [bullet summary of goals]
>
> Anything to add or change?"

This is especially important after the goals section because users often realise they forgot a goal once they hear the list back.

### Step 4: Run sections 6–8

Continue with risk tolerance, constraints, and knowledge sections.

### Step 5: Contradictions pass

After all eight sections, do an explicit contradictions sweep. Look for tensions like:
- Goals vs surplus (can't reach the goal with the available monthly surplus + reasonable returns)
- Risk tolerance vs return expectations
- Goals vs liquidity needs
- Existing portfolio vs stated risk tolerance
- Lock-in tolerance vs goals timing
- Insurance gaps that invalidate the investment plan (e.g., no health cover — one hospitalisation could derail everything)

Present 2–5 tensions you noticed. For each, ask the user which side they want to revise. Update mental model accordingly.

### Step 6: Write goals.md

Generate the file using `references/goals-template.md` exactly. Conventions:

- `last_updated:` — today's date in ISO format (YYYY-MM-DD)
- `last_grilled_by: finance-grill v1`
- `review_due:` — 6 months from today, ISO format
- Use **`UNKNOWN — flagged for follow-up`** for anything the user couldn't answer
- Use **`N/A`** for fields that don't apply (e.g., SSY when no daughter)
- Specific rupee numbers wherever possible (today's rupees)
- For dates, ISO format (YYYY-MM-DD) or YYYY for years-only
- Section 9 ("Open Items") lists every UNKNOWN field so the user has a checklist
- Section 10 ("Contradictions Surfaced") records the tensions found and how the user resolved them

Save the file to the user's current working directory unless they specified another path.

### Step 7: Close out

Tell the user:
- Where the file is saved
- That they should review it once and edit anything wrong
- That this file is the input for downstream investment skills (portfolio review, fund allocation, tax checks), so accuracy matters
- Suggest they re-run this skill after any major life event (marriage, child, job change, inheritance, retirement) or every 6–12 months

End by asking: "Anything you want to add, change, or revisit before we close out?"

## Key reminders

- **Capture, don't advise.** Don't recommend products or strategies during the interview. That's for downstream skills.
- **Don't moralise.** No judgment on existing holdings, even ones the agent might later flag.
- **Indian context.** Tax bracket, residency, scheme eligibility, regime choice — these matter and feed downstream tax logic.
- **Precise output.** The output is data for other skills. Be structured and consistent.
- **Respect "I don't know".** Flag and move on; don't drag the conversation chasing one missing field.
