#!/usr/bin/env python3
"""
check_freshness.py — programmatic freshness check for goals.md and laws/*.md.

Used by `finance-grill` (Step 0b) and `laws-refresh` (Step 1) to decide whether
to run a full interview / refresh, a partial one, or skip — without relying on
the agent reading prose to spot stale headers.

Usage:
    python3 scripts/check_freshness.py goals    # check goals.md
    python3 scripts/check_freshness.py laws     # check every laws/*.md
    python3 scripts/check_freshness.py all      # both

Exit codes:
    0 = nothing stale
    1 = invocation error
    3 = at least one file is stale (overdue / budget-lag / quarter-lag /
        stale>1y) — caller should refresh
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from lib.freshness import (  # noqa: E402
    LawHeader,
    most_recent_budget_year,
    parse_goals_header,
    parse_law_header,
    quarter_label,
    quarter_lag,
)

GOALS = ROOT / "goals.md"
LAWS_DIR = ROOT / "laws"


def check_goals() -> tuple[bool, str]:
    """Return (is_stale, human-readable report)."""
    if not GOALS.exists():
        return True, "NO_GOALS_FILE — first-time grill required"

    header = parse_goals_header(GOALS.read_text())
    today = date.today().isoformat()

    last_updated_str = header["last_updated"] or "(missing)"
    review_due_str = header["review_due"] or "(missing)"
    overdue = bool(header["review_due"]) and header["review_due"] < today
    missing_review_due = header["review_due"] is None

    lines = [
        f"goals.md found at {GOALS}",
        f"  last_updated:    {last_updated_str}",
        f"  review_due:      {review_due_str}",
        f"  today:           {today}",
        f"  overdue:         {overdue}",
        f"  missing_review_due: {missing_review_due}",
    ]
    if overdue:
        lines.append(
            "  RECOMMENDATION: full re-grill — file is past its review_due date."
        )
    elif missing_review_due:
        lines.append(
            "  RECOMMENDATION: file lacks a review_due field — confirm with user "
            "whether to run a full re-grill or partial refresh, then write a "
            "review_due date to the file."
        )
    else:
        lines.append(
            "  RECOMMENDATION: still within review window — offer partial refresh "
            "(only changed sections) by default."
        )
    return overdue or missing_review_due, "\n".join(lines)


def _flags_for(header: LawHeader, today: date, expected_year: int) -> list[str]:
    flags: list[str] = []
    if header.verified_budget_year is None:
        flags.append("NO-BUDGET-TAG")
    elif header.verified_budget_year < expected_year:
        flags.append("BUDGET-LAG")
    if header.last_updated:
        cutoff = (today - timedelta(days=365)).isoformat()
        if header.last_updated < cutoff:
            flags.append("STALE>1y")
    if quarter_lag(header, today) is True:
        flags.append("QUARTER-LAG")
    return flags


def check_laws() -> tuple[bool, str]:
    """Return (is_stale, report). Stale if any file has any flag."""
    if not LAWS_DIR.exists():
        return True, f"NO_LAWS_DIR — {LAWS_DIR} does not exist"

    today = date.today()
    expected_year = most_recent_budget_year(today)
    files = sorted(LAWS_DIR.glob("*.md"))
    if not files:
        return True, "laws/ directory is empty — nothing to check"

    rows = []
    any_stale = False
    for f in files:
        header = parse_law_header(f.read_text())
        flags = _flags_for(header, today, expected_year)
        flag_str = ",".join(flags) if flags else "OK"
        if flags:
            any_stale = True

        last_updated_str = header.last_updated or "(missing)"
        verified_str = (
            f"Budget {header.verified_budget_year}"
            if header.verified_budget_year is not None
            else "Budget=?"
        )
        suffix = ""
        if header.as_of_q is not None and header.as_of_fy_start_year is not None:
            suffix = (
                f"  as_of {quarter_label(header.as_of_q, header.as_of_fy_start_year)}"
            )
        rows.append(
            f"  {flag_str:24}  {f.name}: last_updated {last_updated_str}  "
            f"verified_against {verified_str}{suffix}"
        )

    cur_q_label = quarter_label(*__current_quarter(today))
    header_lines = [
        f"laws/ scan ({len(files)} file(s))",
        f"  most_recent_budget:        Union Budget {expected_year}",
        f"  current_savings_quarter:   {cur_q_label}",
    ]
    if any_stale:
        header_lines.append(
            "  RECOMMENDATION: refresh flagged files via `laws-refresh` "
            "(scope to a single file with the user's permission to limit churn)."
        )
    else:
        header_lines.append(
            "  All files current with the most recent Union Budget and rate quarter."
        )
    return any_stale, "\n".join(header_lines + rows)


def __current_quarter(today: date) -> tuple[int, int]:
    # Avoid re-importing in the hot path of check_laws.
    from lib.freshness import current_small_savings_quarter
    return current_small_savings_quarter(today)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("scope", choices=["goals", "laws", "all"])
    args = ap.parse_args()

    stale = False
    if args.scope in ("goals", "all"):
        s, report = check_goals()
        print(report)
        stale = stale or s
    if args.scope == "all":
        print()
    if args.scope in ("laws", "all"):
        s, report = check_laws()
        print(report)
        stale = stale or s
    return 3 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
