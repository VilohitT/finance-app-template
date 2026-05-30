# Diff format — fund-research output

The shape of the proposal the skill presents to the user before any write.
The user reads this, edits or accepts, then the skill writes to
`data/fund_quality.json`.

---

## Top-level structure

```
PROPOSED ADDITIONS to data/fund_quality.json
==============================================================================
Category:           <canonical AMFI category string>
Plan:               Direct | Regular
Date:               YYYY-MM-DD
Filter spec:        TER ≤ X.XX%, AUM ≥ ₹Ycr, vintage ≥ Z years, manager-tenure ≥ N years
Existing entries:   <N>  (in this category × plan)
Proposed new:       <M>  (after dedup)
Refresh proposals:  <K>  (entries already in JSON, fields will be updated)

------------------------------------------------------------------------------
[Per-candidate block — see below]
------------------------------------------------------------------------------

Sources used:
  • <URL 1>
  • <URL 2>
  • <URL 3>

Confirm action:
  [yes]    write all <M> additions and <K> refreshes to fund_quality.json
  [edit]   tell me which to drop or modify
  [no]     do not write anything
```

---

## Per-candidate block

```
[NEW]  scheme_code: 120716
  name_ref:        UTI Nifty 50 Index Fund - Direct Plan - Growth
  ter:             0.20%                    [source: UTI factsheet Apr 2026]
  manager_name:    Sharwan Kumar Goyal      [source: UTI factsheet]
  manager_since:   2018-07-19               [source: UTI manager bio]
  aum_crore:       18450                    [source: UTI factsheet, AMFI cross-check 18,420]
  vintage_years:   12.4                     [derived from nav_history MIN]
  return_3y:       10.83%                   [derived from nav_history]
  notes:           "Largest UTI Nifty 50 tracker. TER 20bps; tracking error ~12bps p.a. per VR. No mandate change since launch."
  
  evidence:
    - https://www.utimf.com/forms-and-downloads/factsheets/2026-04-factsheet.pdf
    - https://www.valueresearchonline.com/funds/16095/uti-nifty-50-index-fund-direct-plan/
    - https://freefincal.com/index-fund-screener-2026/

[REFRESH]  scheme_code: <existing scheme>  (already in JSON)
  Existing values → New values:
    ter:             X.XX%      → X.XX%   (unchanged)
    aum_crore:       <prev>     → <new>   (+/-N%)
    manager_since:   YYYY-MM-DD → YYYY-MM-DD (unchanged or new tenure)
    last_verified:   <prev>     → <today>
  evidence:
    - <AMC factsheet URL>
```

---

## Fields and their valid values

| Field | Type | Required for [NEW] | Source-of-truth |
|---|---|---|---|
| `scheme_code` | int | yes | `data/market.db` `schemes` table |
| `name_ref` | str | yes | AMFI canonical (`schemes.scheme_name`) |
| `ter` | float (%) | yes | AMC factsheet |
| `manager_name` | str | yes | AMC factsheet |
| `manager_since` | str (YYYY-MM-DD) | yes | AMC factsheet manager bio |
| `aum_crore` | float (₹ Cr) | yes | AMC factsheet |
| `last_verified` | str (YYYY-MM-DD) | yes | today |
| `notes` | str | yes (even if empty) | free text, capture URLs |

For unresolved fields (couldn't verify confidently), write `null` and list the
field in a per-candidate `unresolved_fields` line:

```
[NEW]  scheme_code: 999999
  name_ref:        Some Fund Name
  ter:             null
  manager_name:    null
  manager_since:   null
  aum_crore:       8000   [source: VR only — could not find factsheet]
  ...
  unresolved_fields: ter, manager_name, manager_since
  evidence: ...
```

The user decides whether to (a) accept the partial entry (`filter_candidates`
will exclude it from quality-scored ranking but it still appears with a
completeness flag), (b) edit fields manually, or (c) drop the candidate.

---

## Diff modes

The skill supports three modes, chosen automatically by Phase 1:

1. **Expand mode** — fewer than 5 entries exist for (category, plan); skill researches new candidates to bring count to 5-10.
2. **Refresh mode** — ≥5 entries already exist; skill re-verifies TER/AUM/manager-since against current factsheets, proposes updates only where values changed.
3. **Mixed mode** — both, when an existing entry warrants a refresh AND the user wants more candidates added.

The mode shows in the header:

```
Mode: expand    (existing 1 → proposing 7 new = 8 total)
Mode: refresh   (existing 8, proposing 3 field updates)
Mode: mixed     (existing 4 → proposing 4 new + 2 refreshes)
```

---

## Confirmation grammar

The user responds with one of:

- **`yes`** — write all proposed additions and refreshes verbatim
- **`yes except <list>`** — write everything except the listed scheme_codes (e.g. "yes except 999999, 888888")
- **`edit <scheme_code> <field> = <value>`** — modify before write (multiple allowed, comma-separated)
- **`no`** — abort; do not write anything

The skill echoes the final action to be taken before executing the write.

---

## Write semantics

Append-or-update against `data/fund_quality.json`:

- **New entries:** added under `schemes.<scheme_code>` (string keys, per existing JSON shape).
- **Refresh entries:** existing fields updated in place; fields not in the proposal are preserved.
- **Atomic write:** `tempfile.NamedTemporaryFile` → `os.replace()` to survive mid-write crashes.
- **`_meta.last_research_run`:** updated to today's date.

After write, the skill reports counts:

```
Wrote 5 new entries and refreshed 3 existing entries.
fund_quality.json now contains 25 entries across N categories.
```
