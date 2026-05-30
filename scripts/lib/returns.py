"""
Trailing returns, alpha, and tracking error helpers.

`get_returns` (annualised CAGR over a window) lives in fund_quality.py and is
re-exposed here for convenience.

This module adds the relative-performance helpers that fund-allocate needs:

- alpha_vs_benchmark: fund_return − benchmark_return, both annualised over the
  same window. Used to evaluate whether an active fund earned its fee.
- tracking_error: annualised stdev of daily fund_return − benchmark_return.
  Used to differentiate index funds (where 3Y return clusters in a few bps).
- discover_benchmark_for_category: pick a sensible default benchmark scheme
  for a given SEBI category — Nifty 50 index for large-cap, Nifty Midcap 150
  for mid, etc.

Sign conventions:
- Returns are decimals (0.12 = 12% p.a.). Negative on losses.
- Alpha follows the same convention; positive = fund beat benchmark.
- Tracking error is always non-negative (annualised stdev).
"""

from __future__ import annotations

import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from .db import get_conn
    from .fund_quality import get_returns  # re-exported
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from db import get_conn  # type: ignore
    from fund_quality import get_returns  # type: ignore  # noqa: F401


# Default benchmark mapping by SEBI category.
#
# Only mappings where the SEBI category cleanly corresponds to a single index
# are listed. For categories whose universe is broader than the cap-bucket
# (Flexi/Multi/Value/ELSS/Focused/Contra/Dividend Yield/Sectoral) there is no
# single "right" benchmark — picking Nifty 50 there silently misleads alpha.
# Returning None forces the caller to pass a specific benchmark.
#
# Index Funds have no fixed mapping (the fund IS an index of varying flavour);
# the caller chooses the benchmark of interest (or skips alpha and just uses
# tracking_error against the underlying live index data).
DEFAULT_BENCHMARK_BY_CATEGORY = {
    # Large-cap → Nifty 50 (UTI Nifty 50 Index Direct, oldest/largest)
    "Equity Scheme - Large Cap Fund": 120716,
    # Mid-cap → Nifty Midcap 150 (Motilal Oswal Direct)
    "Equity Scheme - Mid Cap Fund": 147622,
    # Small-cap → Nifty Smallcap 250 (Motilal Oswal Direct)
    "Equity Scheme - Small Cap Fund": 147623,
}


def discover_benchmark_for_category(category: str | None) -> int | None:
    """
    Default benchmark scheme_code for a given SEBI category.

    Returns None when no single sensible default exists — including for
    Flexi/Multi/Value/ELSS/Focused/Contra/Dividend-Yield/Sectoral (universe is
    wider than any single index) and for "Other Scheme - Index Funds" (the
    fund itself is an index tracker; the caller specifies the live-index
    benchmark to compute tracking error against). Caller is expected to pass
    the desired benchmark scheme_code explicitly in those cases.
    """
    if not category:
        return None
    return DEFAULT_BENCHMARK_BY_CATEGORY.get(category)


def alpha_vs_benchmark(
    fund_code: int,
    benchmark_code: int,
    period_days: int,
    db_path=None,
) -> dict | None:
    """
    Annualised fund return minus annualised benchmark return over the same window.

    Both legs are computed from the *aligned* daily-NAV series — first and last
    NAVs on dates where both fund and benchmark publish — so a stale NAV on one
    side cannot misalign the windows. Requires ≥ 80% of the requested
    period_days of coverage; below that, returns None to avoid annualising a
    short window.

    Returns:
        {
          "fund_code": int, "benchmark_code": int,
          "period_days": int,
          "n_overlapping_days": int,
          "actual_days": int,                # span of aligned window
          "fund_return": float, "benchmark_return": float,
          "alpha": float,                    # fund_return − benchmark_return
        }
    or None if insufficient overlap.
    """
    # Alpha only needs first/last anchors, so pass min_rows=2.
    series = _aligned_daily_navs(
        fund_code, benchmark_code, period_days, db_path, min_rows=2,
    )
    if not series:
        return None
    first_date_s, fund_first, bench_first = series[0]
    last_date_s, fund_last, bench_last = series[-1]
    if fund_first <= 0 or bench_first <= 0 or fund_last <= 0 or bench_last <= 0:
        return None
    first_d = datetime.strptime(first_date_s, "%Y-%m-%d").date()
    last_d = datetime.strptime(last_date_s, "%Y-%m-%d").date()
    actual_days = (last_d - first_d).days
    if actual_days < period_days * 0.8 or actual_days < 1:
        return None
    fund_r = (fund_last / fund_first) ** (365.0 / actual_days) - 1.0
    bench_r = (bench_last / bench_first) ** (365.0 / actual_days) - 1.0
    return {
        "fund_code": fund_code,
        "benchmark_code": benchmark_code,
        "period_days": period_days,
        "n_overlapping_days": len(series),
        "actual_days": actual_days,
        "fund_return": round(fund_r, 6),
        "benchmark_return": round(bench_r, 6),
        "alpha": round(fund_r - bench_r, 6),
    }


def _aligned_daily_navs(
    fund_code: int,
    benchmark_code: int,
    period_days: int,
    db_path=None,
    min_rows: int = 30,
) -> list[tuple[str, float, float]] | None:
    """
    Return list of (date, fund_nav, benchmark_nav) for dates where BOTH have data
    within the trailing `period_days` window. Returns None if either lacks data
    or fewer than `min_rows` overlapping dates exist (default 30, the floor for
    a meaningful tracking-error series). Alpha callers can pass min_rows=2 to
    get just the first/last anchors without requiring a dense daily series.
    """
    with get_conn(db_path) as conn:
        latest = conn.execute(
            "SELECT MAX(nav_date) AS d FROM nav_history WHERE scheme_code IN (?, ?)",
            (fund_code, benchmark_code),
        ).fetchone()
        if not latest or not latest["d"]:
            return None
        latest_date = datetime.strptime(latest["d"], "%Y-%m-%d").date()
        window_start = (latest_date - timedelta(days=period_days)).isoformat()
        rows = conn.execute(
            """
            SELECT f.nav_date, f.nav AS fund_nav, b.nav AS bench_nav
            FROM nav_history f
            JOIN nav_history b
              ON b.scheme_code = ? AND b.nav_date = f.nav_date
            WHERE f.scheme_code = ? AND f.nav_date >= ?
            ORDER BY f.nav_date ASC
            """,
            (benchmark_code, fund_code, window_start),
        ).fetchall()
    if len(rows) < min_rows:
        return None
    return [(r["nav_date"], r["fund_nav"], r["bench_nav"]) for r in rows]


def tracking_error(
    fund_code: int,
    benchmark_code: int,
    period_days: int,
    db_path=None,
) -> dict | None:
    """
    Annualised tracking error: stdev of daily (fund_return − benchmark_return) × √252.

    Returns:
        {
          "fund_code": int, "benchmark_code": int,
          "period_days": int,
          "n_overlapping_days": int,
          "annualised_te": float,        # decimal; e.g. 0.0023 = 23 bps p.a.
          "mean_daily_diff": float,      # daily mean difference (sanity check)
        }
    or None if insufficient overlap.
    """
    series = _aligned_daily_navs(fund_code, benchmark_code, period_days, db_path)
    if not series or len(series) < 30:
        return None

    # Daily log returns avoid bias from compounding when differencing
    fund_returns = []
    bench_returns = []
    for i in range(1, len(series)):
        _, f1, b1 = series[i - 1]
        _, f2, b2 = series[i]
        if f1 <= 0 or b1 <= 0 or f2 <= 0 or b2 <= 0:
            continue
        fund_returns.append(math.log(f2 / f1))
        bench_returns.append(math.log(b2 / b1))

    n = len(fund_returns)
    if n < 20:
        return None
    diffs = [f - b for f, b in zip(fund_returns, bench_returns)]
    mean = sum(diffs) / n
    variance = sum((d - mean) ** 2 for d in diffs) / max(n - 1, 1)
    stdev = math.sqrt(variance)
    # Annualise assuming ~252 trading days
    annualised = stdev * math.sqrt(252)
    return {
        "fund_code": fund_code,
        "benchmark_code": benchmark_code,
        "period_days": period_days,
        "n_overlapping_days": n,
        "annualised_te": round(annualised, 6),
        "mean_daily_diff": round(mean, 8),
    }
