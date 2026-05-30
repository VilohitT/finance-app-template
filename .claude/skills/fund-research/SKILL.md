---
name: fund-research
description: Populates data/fund_quality.json for a specific SEBI category by using WebFetch on Value Research / Freefincal / AMC factsheets to assemble a candidate shortlist. Captures TER, AUM, manager_name, manager_since, last_verified per scheme. Resolves scheme_code via the schemes table in data/market.db (failing loudly if unresolvable). Presents a structured diff to the user listing the proposed additions; never writes to fund_quality.json without explicit approval. Use whenever fund-allocate hits sparse-data mode for a category, the user asks "research large-cap funds for me", or fund_quality.json needs a refresh after manager-change news / quarterly re-verification. Indian-context aware — handles Direct vs Regular plans, the canonical AMFI category vocabulary (e.g. "Other Scheme - Index Funds" not "Equity Scheme - Index Funds"), and the ₹500cr/₹1000cr AUM floors per principles.md §3.5.
---

# fund-research

A focused skill that turns "I need 5 candidate funds for category X" into a vetted, scheme-coded list ready to drop into `data/fund_quality.json` for `filter_candidates()` to consume.

The skill exists because `fund_quality.json` is the bottleneck for `/fund-allocate`'s rich-data mode — without 3+ entries per category, `filter_candidates()` returns an empty list and selection falls back to deferral. fund-research is the on-demand way to grow that JSON without inventing data from training-data priors.

## When to use

Trigger this skill when:

- `/fund-allocate` flagged sparse-data for a category (most common)
- User says: "research large-cap Direct funds for me" / "find me top arbitrage funds" / "what are the best Nifty 50 trackers"
- A `discover.py` snapshot showed a category with 0 entries that the user is about to deploy into
- A scheduled quarterly refresh of existing `fund_quality.json` entries (TER/AUM may have moved)
- News broke about a manager change at an AMC the user holds

## What this skill does NOT do

- **Does not write to `fund_quality.json` silently.** Every change is a proposed diff the user approves before write.
- **Does not invent scheme codes.** Every recommended fund must resolve to a row in the `schemes` table. If a fund the AMC publishes hasn't been seen by AMFI's NAVAll yet, the skill flags it and skips.
- **Does not pick which fund the user should buy.** That's `/fund-allocate`'s job. fund-research populates the universe; selection happens downstream.
- **Does not scrape behind paywalls.** Value Research has a free public tier; AMC factsheets are public PDFs. Anything paywalled is a follow-up, not an output.
- **Does not refresh law/tax data.** That's `/laws-refresh`'s job.

## What this skill produces

A **proposed diff** structured per `references/diff-format.md`. Conceptually:

```
PROPOSED ADDITIONS to fund_quality.json — <category> — <YYYY-MM-DD>

For each candidate (5-10):
  scheme_code: <int, resolved against schemes table>
  name_ref:    <canonical AMFI name>
  ter:         <%>
  manager_name: <string>
  manager_since: <YYYY-MM-DD>
  aum_crore:   <₹ Cr>
  last_verified: <today>
  notes:       <free-text — sources, caveats, AUM-bloat flags>

  --- evidence ---
  primary_source_url: <URL>
  cross_check_url:    <URL>
  unresolved_fields:  <list, if any>

User confirms → entries appended to fund_quality.json (preserving existing).
User rejects / edits → no write; user dictates corrections.
```

## Workflow

### Phase 0 — Discovery snapshot (mandatory)

When invoked by another skill, the calling skill has already run `discover.py` and the relevant snapshot is in context — read theirs rather than re-running. When invoked directly, run it now:

```bash
python3 scripts/discover.py
```

Quote §6 (`fund_quality.json` coverage by category, by plan, with stale-entry count) before researching. This grounds the research scope: a category that already has 5+ complete entries needs a refresh, not an expansion; a category with 0 entries is the standard sparse-data trigger.

### Phase 1 — Identify the gap

Either:
- `/fund-allocate` invoked this skill with explicit `category` and `plan` parameters, OR
- The user asked. In that case, capture:
  - **Category:** must match canonical AMFI vocabulary. Verify via:
    ```bash
    sqlite3 data/market.db "SELECT DISTINCT category FROM schemes WHERE category LIKE '%<keyword>%' ORDER BY category;"
    ```
  - **Plan:** `Direct` (default for new investments per `principles.md` §3.1) or `Regular`
  - **Filter floor:** typical defaults from `principles.md` §3.5 / fund-allocate's per-category table
  - **Special context:** any constraints (e.g. "no AMC where user already holds 2+ funds" to limit overlap)

### Phase 2 — Check current state via the helper

Use `scripts/lib/fund_quality.load_quality()` to read existing entries; do not hand-roll JSON parsing. Cross-check against the schemes table for category and plan matching:

```python
import sys; sys.path.insert(0, 'scripts')
from lib.fund_quality import load_quality
from lib.db import get_conn

quality = load_quality()        # {scheme_code: {ter, manager_name, ...}, ...}
codes = list(quality.keys())
with get_conn() as conn:
    placeholders = ",".join("?" * len(codes)) if codes else "NULL"
    rows = conn.execute(
        f"SELECT scheme_code, scheme_name, category, plan FROM schemes "
        f"WHERE scheme_code IN ({placeholders})",
        codes,
    ).fetchall() if codes else []
existing = [
    r for r in rows
    if r["category"] == TARGET_CATEGORY and (r["plan"] == TARGET_PLAN or r["plan"] is None)
]
```

If ≥5 entries already exist for this (category, plan), report and ask the user whether they want a refresh (TER/AUM/manager re-verification) or a true expansion (new candidates beyond what's there).

### Phase 3 — Web research

Sources are documented in `references/sources.md`. Default flow:

1. **Value Research** screener for the category (`https://www.valueresearchonline.com/funds/`) — filter by category + plan (Direct), sort by 5Y return, capture the top 8-12 names. Public landing pages show TER, AUM, manager.
2. **Freefincal "Plumb Line"** (`https://freefincal.com/free-mutual-fund-screeners/`) — curated lists by category. Cross-reference VR's top names; AMCs Pattu flags as "skip" get a note.
3. **AMC factsheet PDF** for the top 5-8 candidates from steps 1-2. Search `<AMC name> factsheet <month> <year>` and verify TER, manager-since-date, AUM. AMC factsheets are the authoritative source for these fields.
4. **AMFI category PDF** (monthly) for AUM cross-check at AMC level. Optional.

Gather, per candidate:
- Scheme name (as canonical AMFI name as possible — must match what's in `schemes` table)
- TER (in %)
- AUM (in ₹ crores)
- Manager name (lead + co-managers)
- Manager-since date (ISO)
- Notes (anything material — AUM-bloat watch, mandate change history, etc.)

Use WebFetch for every URL; record the URL alongside each datapoint.

### Phase 4 — Resolve scheme codes

For each candidate, find the AMFI scheme code:

```bash
sqlite3 data/market.db "SELECT scheme_code, scheme_name FROM schemes WHERE scheme_name LIKE '%<keyword>%' AND plan='<Direct or Regular>' AND scheme_name LIKE '%Growth%' ORDER BY scheme_code;"
```

If the search returns multiple, narrow with AMC name. If 0, the scheme is not in NAVAll yet — flag it as `unresolved` and skip (don't add to JSON without a code).

Also call `scripts/resolve_schemes.py --interactive` if available for fuzzy matches.

### Phase 5 — Assemble the diff

Build the proposed JSON additions in the format of `references/diff-format.md`:

```json
{
  "<scheme_code>": {
    "name_ref": "<canonical AMFI name>",
    "ter": <number>,
    "manager_name": "<string>",
    "manager_since": "<YYYY-MM-DD>",
    "aum_crore": <number>,
    "last_verified": "<today>",
    "notes": "<free-text — include source URLs and any caveats>"
  },
  ...
}
```

For any field you couldn't verify confidently from the sources, leave the field as `null` and list the field in `unresolved_fields`. The user decides whether to fill manually before confirming.

### Phase 6 — Present to user

Output:

```
PROPOSED ADDITIONS to data/fund_quality.json
Category: <...>      Plan: <...>      Date: YYYY-MM-DD
Existing entries in this (category, plan): <N>
Proposed new entries: <M>

[Per candidate, the structured block]

Sources used:
  - <URL>
  - <URL>
  - ...

Confirm to write? (yes / edit / no)
```

Wait for explicit approval. On `edit`, the user dictates which entries to drop or modify. On `no`, do nothing (the research stays in the conversation but the JSON is untouched).

### Phase 7 — Write the diff

On `yes`:

```python
import json
from datetime import date
from pathlib import Path

path = Path('data/fund_quality.json')
data = json.loads(path.read_text())
schemes = data.setdefault('schemes', {})
for code, entry in proposed_diff.items():
    if str(code) in schemes:
        # Refresh-mode: merge non-null fields into existing
        schemes[str(code)].update({k: v for k, v in entry.items() if v is not None})
    else:
        schemes[str(code)] = entry
# Update _meta so future runs can tell when the universe was last touched.
data.setdefault('_meta', {})['last_research_run'] = date.today().isoformat()
# Atomic write via tempfile rename
tmp = path.with_suffix('.tmp')
tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
tmp.replace(path)
```

Confirm write to user with the count of added vs refreshed entries.

### Phase 8 — Closing

Tell the user:
- Number of entries added / refreshed
- For any `unresolved` candidates: what was missing and how to fill
- A reminder that downstream skills (`/fund-allocate`) will see the new universe immediately on next invocation
- Suggested re-research cadence for this category (typically quarterly for AUM/TER, annually for full re-verification)

## Operating principles

### Never silent writes

Every write to `fund_quality.json` is preceded by an explicit user confirmation. The user must see what's being added before it lands. This matches the pattern of `/laws-refresh` (proposes diffs, waits for approval).

### Source diversity

A field captured from a single source is suspect. The skill prefers two independent sources for TER and AUM. AMC factsheet (primary) + Value Research/Freefincal (cross-check) is the standard pattern. Note in the candidate's `notes` field when only a single source was available.

### Verify against schemes table before proposing

If a candidate doesn't resolve to a `schemes` row, it doesn't get added to `fund_quality.json`. Reason: `filter_candidates()` joins on `schemes.scheme_code`; an unresolved entry is invisible.

### Match canonical AMFI names

The `name_ref` field is for the editor's reference. Match the AMFI canonical name (per `schemes.scheme_name`) so future cross-checks via SQL work cleanly.

### Cite URLs in `notes`

Future you will want to know where a TER or manager_since came from. Capture URLs in the `notes` field for every entry. When the user runs a quarterly refresh, those URLs are the starting point.

## Key reminders

- **Never write without user confirmation.** Diffs are proposals.
- **Never invent scheme codes.** Resolve against the `schemes` table or skip.
- **Two sources beat one.** AMC factsheet + screener cross-check is the default.
- **Quote URLs in `notes`.** Future-self thanks you.
- **Use canonical category strings.** SQL `SELECT DISTINCT category` is your friend.
