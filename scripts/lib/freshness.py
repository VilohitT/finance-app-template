"""
freshness.py — header parsing and date-arithmetic for laws/*.md and goals.md.

Single source of truth for staleness signals consumed by both
`scripts/check_freshness.py` and `scripts/discover.py`. Keeps the two callers
from drifting apart on what counts as "stale."

Signals currently computed:
  • most_recent_budget_year — Indian Union Budget cadence (presented every Feb 1)
  • current_small_savings_quarter — Indian Government small-savings rate cycle
  • parse_law_header — extracts last_updated, last_verified_against_budget, and
    any `As-of: Q* FY YYYY-YY` annotation from a laws/*.md header
  • parse_goals_header — extracts last_updated and review_due from goals.md
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

_BUDGET_YEAR_RE = re.compile(r"\b(?:Union\s+)?Budget\s+(\d{4})\b", re.IGNORECASE)
_LAST_UPDATED_RE = re.compile(r"^last_updated:\s*(\S+)", re.MULTILINE)
_REVIEW_DUE_RE = re.compile(r"^review_due:\s*(\S+)", re.MULTILINE)
_VERIFIED_BUDGET_RE = re.compile(
    r"^last_verified_against_budget:\s*(.+)$", re.MULTILINE
)
# Matches "As-of: Q4 FY 2025-26", "**As-of:** Q1 FY 2026-27", "As of Q2 FY 2024-25", etc.
_AS_OF_QUARTER_RE = re.compile(
    r"As[\s-]of:?\s*\*{0,2}\s*Q([1-4])\s+FY\s+(\d{4})-(\d{2})",
    re.IGNORECASE,
)


@dataclass
class LawHeader:
    last_updated: str | None
    last_verified_raw: str | None
    verified_budget_year: int | None
    as_of_q: int | None
    as_of_fy_start_year: int | None  # e.g. 2025 for "FY 2025-26"


def most_recent_budget_year(today: date) -> int:
    """The Union Budget is presented on 1 February. From Feb 1 onward the
    most recent Budget year is the current calendar year; before that it's
    the previous calendar year."""
    return today.year if (today.month, today.day) >= (2, 1) else today.year - 1


def current_small_savings_quarter(today: date) -> tuple[int, int]:
    """
    Returns (q_num, fy_start_year) for the current small-savings rate cycle
    quarter as of `today`. Indian FY runs Apr-Mar:
      Q1 = Apr-Jun, Q2 = Jul-Sep, Q3 = Oct-Dec, Q4 = Jan-Mar.
    Notifications are issued at quarter-end for the upcoming quarter, so by
    the first day of any quarter the rate for that quarter is "live."
    """
    m, y = today.month, today.year
    if 4 <= m <= 6:
        return 1, y
    if 7 <= m <= 9:
        return 2, y
    if 10 <= m <= 12:
        return 3, y
    return 4, y - 1  # Jan-Mar belongs to the FY that ends in the current year


def quarter_end_year_month(q: int, fy_start_year: int) -> tuple[int, int]:
    """Calendar (year, month) at which a given fiscal-year quarter ends."""
    return {
        1: (fy_start_year, 6),
        2: (fy_start_year, 9),
        3: (fy_start_year, 12),
        4: (fy_start_year + 1, 3),
    }[q]


def fy_label(fy_start_year: int) -> str:
    """'2025' → 'FY 2025-26'."""
    return f"FY {fy_start_year}-{(fy_start_year + 1) % 100:02d}"


def quarter_label(q: int, fy_start_year: int) -> str:
    """(4, 2025) → 'Q4 FY 2025-26'."""
    return f"Q{q} {fy_label(fy_start_year)}"


def parse_law_header(text: str) -> LawHeader:
    """Parse the front-matter-ish header of a laws/*.md file."""
    last_updated = _LAST_UPDATED_RE.search(text)
    verified = _VERIFIED_BUDGET_RE.search(text)
    verified_raw = verified.group(1).strip() if verified else None
    verified_year: int | None = None
    if verified_raw:
        m = _BUDGET_YEAR_RE.search(verified_raw)
        if m:
            verified_year = int(m.group(1))

    as_of_q: int | None = None
    as_of_fy_start_year: int | None = None
    m = _AS_OF_QUARTER_RE.search(text)
    if m:
        as_of_q = int(m.group(1))
        as_of_fy_start_year = int(m.group(2))

    return LawHeader(
        last_updated=last_updated.group(1) if last_updated else None,
        last_verified_raw=verified_raw,
        verified_budget_year=verified_year,
        as_of_q=as_of_q,
        as_of_fy_start_year=as_of_fy_start_year,
    )


def parse_goals_header(text: str) -> dict:
    last_updated = _LAST_UPDATED_RE.search(text)
    review_due = _REVIEW_DUE_RE.search(text)
    return {
        "last_updated": last_updated.group(1) if last_updated else None,
        "review_due": review_due.group(1) if review_due else None,
    }


def quarter_lag(header: LawHeader, today: date) -> bool | None:
    """
    Return True if the file's `As-of: Q* FY YYYY-YY` annotation is older than
    the current rate-cycle quarter, False if current, None when the file does
    not track quarterly rates (no `As-of:` annotation present).
    """
    if header.as_of_q is None or header.as_of_fy_start_year is None:
        return None
    file_end = quarter_end_year_month(header.as_of_q, header.as_of_fy_start_year)
    cur_q, cur_fy = current_small_savings_quarter(today)
    cur_end = quarter_end_year_month(cur_q, cur_fy)
    return file_end < cur_end
