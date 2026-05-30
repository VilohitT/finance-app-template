---
name: laws-refresh
description: Refreshes the laws/ folder of the user's investment agent — capital gains rules, tax regimes, PPF/EPF/VPF/NPS/SCSS rates and rules, SGB / gold tax, SEBI categorisation, and insurance provisions. Use whenever the user asks to refresh laws, update tax rules, check whether laws.md is current, after a Union Budget, after a quarterly small-savings rate revision, or whenever the user asks "are my tax rules up to date." Invoke proactively when laws files are flagged as stale or when the agent encounters a tax/scheme question and notices the relevant laws file is older than the most recent Budget. Reads each file in the laws/ folder, identifies what may have changed via authoritative web sources (Income Tax Department, SEBI, AMFI, RBI, Ministry of Finance), and proposes diffs for the user to review and approve before any update is committed.
---

# laws-refresh

A manual-trigger refresh skill for the Indian-context investment-agent law reference (`laws/`). The skill reads the existing files, surfaces which sections may be stale, fetches verified updates from authoritative sources, and produces a structured diff for the user to approve. **Nothing in `laws/` is updated silently.**

## When to use

Trigger when the user wants any of:
- Refresh `laws.md` after the latest Union Budget
- Check whether the laws files are still current
- Update small-savings rates (PPF, SCSS quarterly revisions; EPF annual revision)
- "Are my tax rules up to date?"
- Periodic 6-12 month routine refresh
- Specific update for a single file ("just refresh `nps.md`")

The skill is also invoked indirectly by other skills (`tax-check`, `portfolio-review`, `fund-allocate`) when they detect a stale file. In that case, the calling skill says: "I noticed `<file>` was last verified for Budget XYZ — running `laws-refresh` to check what's changed before relying on it." Then it runs this skill.

## What this skill produces

For each file refreshed:
1. **A diff** showing proposed additions, deletions, and changes
2. **Source citations** for each proposed change (URL + brief excerpt)
3. **A confidence rating** for each proposed change: HIGH (sourced from authoritative gov / regulator URL), MEDIUM (sourced from a reputable secondary like a major tax/MF publication), LOW (heuristic update only — flag for user verification)
4. **A summary report** explaining what changed and what didn't

The user reviews each diff and approves / rejects before commit. The skill does not write to disk until approval.

## Workflow

### Step 1: Phase 0 — programmatic staleness scan

Before reading any prose or web-fetching anything, run from the project root:

```
python3 scripts/check_freshness.py laws
```

The script parses every `laws/*.md` header (`last_updated`, `last_verified_against_budget`, and any `As-of: Q* FY YYYY-YY` annotation on rate-tracking files), computes the most-recently-presented Union Budget (every Feb 1) and the current small-savings rate quarter, and prints a structured per-file table flagging:
- **`OK`** — current on every axis.
- **`BUDGET-LAG`** — `last_verified_against_budget` is older than the most recent Budget; the file is presumed stale even if `last_updated` is recent.
- **`NO-BUDGET-TAG`** — header missing or unparseable; refresh and add the tag.
- **`STALE>1y`** — `last_updated` is more than 365 days old (catches the case where someone bumped the Budget tag without re-reading the file).
- **`QUARTER-LAG`** — applies to files that carry an `As-of: Q* FY YYYY-YY` annotation (currently `ppf.md`, `scss.md`); the annotation is older than the current rate-cycle quarter.

Exit code is `0` if all files are current, `3` if any file is flagged. (`scripts/discover.py` Section 7 surfaces the identical signals — both call `scripts/lib/freshness.py` so the two paths cannot drift. Use `check_freshness.py laws` when you only need the laws view; use `discover.py` when you also need the rest of the Phase 0 dashboard.)

Use the table — not prose-reading — to scope the refresh:
- **All files OK and the user didn't name a specific file:** confirm with the user whether to still proceed (e.g., they're chasing a mid-year notification), or stop early.
- **Some files flagged:** restrict the run to flagged files unless the user expands. Quote the script's output back so the user sees exactly which files you'll touch.
- **User named a specific file** ("just `nps.md`"): honour that scope regardless of the script's verdict, but still surface the script's flag for that file so the user knows whether the run is corrective (flagged) or precautionary (OK).

### Step 2: Read the targeted files

For each in-scope file, read the full content to capture:
- `last_updated` date
- `last_verified_against_budget` value
- The covered topic and any `as_of_quarter` annotations on rate sections (PPF, SCSS, EPF — these change quarterly/annually and may be stale even when the budget tag is current)

### Step 3: Determine what else to check beyond the script's flags

Step 1's script catches `BUDGET-LAG`, `STALE>1y`, and `QUARTER-LAG` (the last applies to files that carry an `As-of: Q* FY YYYY-YY` annotation — currently `ppf.md` and `scss.md`). It does **not** know about other mid-cycle notifications, so for each in-scope file also consider:
- Most recent **annual** EPFO interest rate announcement (typically Feb-Mar) → relevant for `epf-vpf.md` (no quarterly tag)
- File-specific: SEBI circular dates (`sebi-categories.md`, MF rule files), RBI announcements (`gold.md` SGB tranches, RBI Floating-Rate Bonds in `bonds`-adjacent rules)
- Any rate-tracking file *without* an `As-of: Q* FY YYYY-YY` annotation that probably should have one — if you encounter one, propose adding the annotation as part of the refresh so future runs benefit from QUARTER-LAG detection

Add any file flagged here to the in-scope list, even if Step 1's table marked it OK.

### Step 4: Search authoritative sources

For each file flagged, web-search authoritative sources. Priority order:

**Primary sources (HIGH confidence):**
- `incometaxindia.gov.in` — Income Tax Act, FAQs, Budget documents, CBDT notifications
- `pib.gov.in` — Press Information Bureau official press releases (Budget speeches, Ministry announcements)
- `indiabudget.gov.in` — official Budget documents (Finance Bill, FAQs, Memorandum)
- `rbi.org.in` — RBI press releases, master circulars, SGB scheme calendars
- `sebi.gov.in` — SEBI circulars, master circulars on mutual funds
- `amfiindia.com` — AMFI categorisation rules, daily NAV, top-100 list
- `epfindia.gov.in` — EPFO press releases (interest rate announcements)
- `pfrda.org.in` — PFRDA circulars (NPS rules)
- `npstrust.org.in` — NPS Trust operational rules

**Secondary sources (MEDIUM confidence):**
- `cleartax.in`, `taxbuddy.com`, `legalsuvidha.com`, `bajajfinserv.in/investments`, etc. — tax / investment publications that summarise the primary law
- Use these for cross-checks and easy-to-read explanations
- A change must be cross-verifiable across at least two reputable secondaries before proposing — single-source secondary claims are flagged as MEDIUM but kept if the primary source can't be located

**Avoid (LOW or not used):**
- Forum posts, retail finance blogs without editorial standards, generic news sites without primary citation
- AI-generated summary sites that lack date stamps

### Step 5: For each file, produce a structured diff

Format each file's proposed changes as a structured block:

```
## File: laws/<filename>
### Current state
- last_updated: <date>
- last_verified_against_budget: <budget>

### Proposed changes
- [HIGH] Section X.Y: <description of change>
  Old: <verbatim old text or "ADD section">
  New: <verbatim proposed text>
  Source: <URL>
  Excerpt: "<short quote from source supporting the change>"

- [MEDIUM] Section A.B: <description>
  ...

### No-change confirmations
- Section P.Q (<topic>): verified unchanged. Source: <URL>

### Flagged for user judgment
- Section M.N: <ambiguity>. Multiple reputable sources interpret differently. Recommend user check with CA / official source before applying.
```

Each section should reference both the file structure and the specific subsection / table / paragraph being changed.

### Step 6: Present diffs to user, await approval

Present all file diffs to the user in a clean format. Group by file. For each file:
- Show the proposed `last_updated` and `last_verified_against_budget` values
- Show all HIGH-confidence changes prominently
- Show MEDIUM changes with a clearer caveat
- Show flagged items with a clear "this needs your judgment" call-out

Then ask the user to approve or reject each file, or specific changes within a file. The user can:
- Approve all changes to a file (commits the file in full)
- Approve specific sections only (commits a partial file update)
- Reject changes (file is not updated; the older version stands; flag is logged for next refresh)
- Request a re-research with stricter source criteria

### Step 7: Commit approved changes

Once approved:
1. Update each approved file with the new content
2. Update `last_updated` to today's date
3. Update `last_verified_against_budget` to the most recent Budget (only if the refresh confirmed the file matches that Budget — not automatically)
4. Update `laws/index.md`'s table of contents with new `last_verified` dates
5. If any file had partial approval, mark the un-updated sections with an `# UNRESOLVED` marker so the next refresh is unambiguous about what's still pending
6. Output a final commit summary: which files were updated, which sections changed, which were rejected, what's still flagged

### Step 8: Output update log

Append a single-line summary to `laws/refresh-log.md` (create if absent):

```
2026-MM-DD: Refreshed [files]. Approved [N HIGH, M MEDIUM] changes. Rejected [K] changes. Flagged [J] for follow-up.
```

This gives the user a chronological audit trail of every refresh.

## Operating principles

### Honesty about uncertainty
LLMs hallucinate specifics. The agent's protection: every proposed change cites a source URL with a verbatim excerpt. If a source can't be located for a proposed change, the change is not proposed.

### Conservative on rate changes
Quarterly rate updates (PPF, SCSS, etc.) are easy to verify and should be HIGH-confidence. Annual EPFO rates are similar. Slab changes / 87A rebate changes / surcharge changes are major — verify across multiple primary sources.

### Don't propose changes that aren't visible in sources
If the secondary publications mention something but no primary source confirms it, mark MEDIUM and flag for user verification. Do not invent regulatory changes.

### Conservative on Section number references
The Income Tax Act 2025 takes effect 1 April 2026 with renumbered sections. The agent should:
- For FY 2025-26 returns (filed July 2026): refer to old IT Act 1961 section numbers
- For FY 2026-27 onward: use new IT Act 2025 section numbers but cross-reference old numbers in parentheses for at least 2 years
- Flag any section-number change as MEDIUM (cross-numbering errors are common) and ask user to verify before relying on a specific section

### Don't update laws based on user instruction alone
If the user says "I heard PPF rate is now 8%, update the file" — the agent does not update unless an authoritative source confirms. The agent runs the search; if the source confirms, updates with HIGH confidence; if not, declines and explains.

### Single-file refresh is OK
The user may say "just refresh `nps.md`." Honour the scope; don't refresh other files unless the user expands.

### Out-of-scope: rule interpretation
If the user asks "should I switch to old regime?" — that's `tax-check` or `portfolio-review` territory, not `laws-refresh`. The skill stays in its lane: it captures *what the rules are*, not *what the user should do under them*.

## Common refresh scenarios

### Scenario 1: Post-Union Budget refresh (Feb)
Highest-impact run. Budget changes typically affect:
- `regime-comparison.md` — slab changes, rebate changes, basic exemption
- `capital-gains.md` — rate changes, threshold changes
- `equity-mf.md`, `debt-mf.md` — pivot dates, new sections
- Often `gold.md` — SGB issuance status, exemption changes
- Sometimes `nps.md`, `epf-vpf.md` — threshold or 80CCD changes

### Scenario 2: Quarterly small-savings rate revision (Mar/Jun/Sep/Dec last day)
Lower-impact run. Affects:
- `ppf.md` — rate
- `scss.md` — rate
- Possibly `epf-vpf.md` if EPFO has announced (typically just once a year, so usually not)
- Other small savings (KVP, NSC, etc.) if added to scope later

### Scenario 3: Annual EPFO rate announcement (Feb-Mar)
- `epf-vpf.md` — current year rate, prior year rate

### Scenario 4: SEBI categorisation update (occasional)
- `sebi-categories.md` — category definitions, AUM thresholds

### Scenario 5: User-triggered "single fact" check
- "Has the SGB scheme resumed?" → check `gold.md` Section 1.1, refresh if changed
- "Is debt MF indexation back?" → check `debt-mf.md`, no change expected but verify

## Important: things this skill does NOT do

- **Does not write to laws/ files without user approval.** Every change goes through diff + approval.
- **Does not invent rules from training data.** Every change has a sourced citation.
- **Does not interpret rules** — that's downstream skills.
- **Does not refresh `principles.md` or `goals.md`.** Those are user-owned documents.
- **Does not advise on whether old or new regime is better** — that's `tax-check` / `portfolio-review`.

## Testing / verification

After the first run on this folder, the user can sanity-check by:
- Picking one HIGH-confidence change and clicking through the source URL to verify
- Checking that `last_updated` and `last_verified_against_budget` were updated only on approved files
- Reading `laws/refresh-log.md` to see the audit trail

If anything looks wrong, the user can roll back manually (the laws files are markdown — `git revert` if version-controlled, or paste the old version).
