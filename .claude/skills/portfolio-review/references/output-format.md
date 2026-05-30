# Output format — portfolio-review

The exact structure portfolio-review uses for its findings report. Use verbatim.

The report opens with a one-line summary so the user can decide at-a-glance whether this is a "skim and acknowledge" review or a "dig in and decide" review.

---

## Summary line (always first)

One of:
- **"All tracking. No action recommended."** (steady-state, no findings)
- **"<N> findings: <X> ACTION, <Y> WATCH, <Z> INFO."** (findings present)

---

## Full report structure

```markdown
# Portfolio Review — YYYY-MM-DD

**Last review:** [date / first run]
**Mode:** [first run with backlog / steady-state / post-event]
**Summary:** [the summary line above]

---

## Discovery snapshot

From `scripts/discover.py`:
- NAV freshness: [FRESH/STALE], latest_nav_date YYYY-MM-DD
- Ledger: txn_count N, latest_txn_date YYYY-MM-DD
- Drawdown gate (§6.4) per sub-portfolio: [weighted_dd %, block_at_minus_20pct true/false]
- Stale laws/ files: [list, if any]
- Open ACTIONs from prior reviews: N

---

## 1. Goal progress

For each goal in `goals.md` §5 (and `user-principles.md` §5 earmarks):

### <Goal name> (<target> by <date>)
- **Earmarked corpus today:** ₹X
- **Glide-path expected today:** ₹Y (if computable per `user-principles.md` §4)
- **Deviation:** Z% (or "tracking")
- **Scenarios** (from `projection.goal_progress()`): base / optimistic / pessimistic — pct_of_target
- **Note:** [contextual note if deviation > 10%]

---

## 2. Sub-portfolio status

Targets per `user-principles.md` §3.

| Sub-portfolio | Equity % | Debt % | Gold % | Other % | Total ₹ | Drift flag |
|---|---|---|---|---|---|---|
| <name 1> | X | Y | Z | W | ₹V | [in target / drift breach] |
| <name 2> | ... | ... | ... | ... | ... | ... |
| **Aggregate household** | ... | ... | ... | ... | ... | (reporting only per `principles.md` §2.1) |

[Brief commentary on drift, especially flagging `principles.md` §6.3 — "use flows over sales" — wherever drift is correctable through future flows.]

---

## 3. Findings

Sorted: ACTION first (by impact), then WATCH (by relevance), then INFO.

### ACTION-YYYY-MM-DD-001: [headline]

**Principle applied:** [reference, e.g. `principles.md` §4.1]

**Detail:**
[2-4 sentences explaining the situation]

**Trade-offs / cost:**
[If a tax event is involved, the tax-check report excerpt goes here. Otherwise, "no tax cost" or specifics like "operational cost: ~30 minutes to open PPF account online".]

**Tax-check result** (if applicable):
- Net tax cost: ₹X
- Net proceeds: ₹Y
- Holding-period flag: [if applicable]
- Source rules: `laws/<file>.md` §X.Y
- [Full tax-check output available on request]

**What this skill recommends:**
[1-2 sentences with the specific action]

**What would change this recommendation:**
[1 sentence — e.g., "if user moves to Old Regime", "if exit load window closes"]

---

### ACTION-YYYY-MM-DD-002: [headline]
[Same structure]

---

### WATCH-YYYY-MM-DD-001: [headline]

**Principle applied:** ...

**Detail:**
[Why this is being watched, not yet acted on]

**Threshold for action:**
[What condition would shift this from WATCH to ACTION]

**Next check:**
[When the skill will reassess]

---

### INFO-YYYY-MM-DD-001: [headline]

**Detail:**
[Educational / contextual note]

**Source / reference:** [if applicable]

---

## 4. Open items from prior reviews

[For each open finding from `decisions-log.md` still pending:]

- [ID] [headline] — [status: still pending / condition changed / partial progress]

---

## 5. Findings consolidation reminder

(Optional, displayed only if 5+ findings)

> Many findings on this run. Suggested order to work through them:
> 1. [Highest-impact item]
> 2. [Next-highest]
> 3. [Defer the rest to next review]

---

## 6. What you can do now

[1-2 sentences summarising the most useful next step. Examples:]

- "Run `/fund-allocate` to design the SIP structure for your monthly surplus."
- "Open the PPF accounts flagged above — ~30 minutes each online; meaningful unused capacity."
- "Nothing urgent. Next review in 1 week."

---

## 7. Decisions logged

After user response, this section is appended:

| ID | Severity | Headline | User response | Follow-up |
|---|---|---|---|---|
| ACTION-... | ACTION | <headline> | Acted: <what> on YYYY-MM-DD | None |
| ACTION-... | ACTION | <headline> | Deferred: <reason> | YYYY-MM-DD |
| WATCH-... | WATCH | <headline> | Noted | YYYY-MM-DD |
| INFO-... | INFO | <headline> | Noted | None |

[All entries also appended to `decisions-log.md` with full detail.]

---

**Next portfolio-review due:** YYYY-MM-DD (per the user's stated cadence in `goals.md`; sooner if requested).
```

---

## `decisions-log.md` format

This file lives in the project root. Created on first portfolio-review run if not present.

Structure:

```markdown
# Decisions Log

> Audit trail of every recommendation made by the investment agent and the user's response.
> Maintained automatically by portfolio-review and fund-allocate. Append-only — entries are not edited or deleted.

---

## Index by date

- YYYY-MM-DD: First portfolio-review (backlog mode) — N findings
- YYYY-MM-DD: Steady-state — 0 findings
- ...

---

## Entries

### YYYY-MM-DD — Portfolio Review

#### ACTION-YYYY-MM-DD-001 — <headline>

**Severity:** ACTION
**Principle applied:** `principles.md` §X.Y

**Detail:**
[Full detail from the review report]

**Tax-check result:** [excerpt or N/A]

**Recommendation:**
[Specific action]

**User response:** Acted — <what> on YYYY-MM-DD
**Follow-up:** [date or None]
**Status:** [Open / Closed]

---

#### ACTION-YYYY-MM-DD-002 — <headline>
[Same structure]

---

[... etc per finding]
```

---

## Output format conventions

- **Headlines** are 5-10 words, action-oriented (e.g. "Open PPF accounts for both holders", not "PPF").
- **Detail sections** are 2-4 sentences; the user shouldn't need to read 10 lines to understand what's being flagged.
- **Tax-check excerpts** show the headline numbers (tax cost, net proceeds, holding-period flags). Full tax-check report available on request.
- **All currency** in ₹ with commas for readability (e.g., ₹1,50,000 not ₹150000).
- **Dates** in ISO format (YYYY-MM-DD).
- **Citations** of `laws/` files use full path: `laws/equity-mf.md §3`.
- **Sub-portfolio names** come from `user-principles.md` §2 — never hardcoded.
- **Sleeve targets** come from `user-principles.md` §3 — never hardcoded.

---

## When the user pushes back on a finding

If the user says "I disagree with finding X", capture:
- The user's reasoning
- The agent's original reasoning
- Mark the finding as Rejected with the reason in `decisions-log.md`
- Do NOT re-litigate the same finding in subsequent reviews unless the underlying data changes

This prevents the agent from being annoying. Once a finding is Rejected with a stated reason, the agent respects the user's call.

---

## When findings cluster

If many findings share a root cause (e.g., "no SIPs running" creates allocation drift findings, fresh-money capacity findings, AND glide-path deviation findings), consolidate into one finding with sub-points. Don't pad the count.

---

## When the laws are stale

If `laws/` files have `last_verified_against_budget` older than the most recent Budget, the report begins with a warning:

> "⚠️ Some laws files are stale (last verified Budget XYZ, current is Budget YYY). Findings below are computed under the older rules. Run `/laws-refresh` to update."

The skill still produces findings — but with the caveat at the top.
