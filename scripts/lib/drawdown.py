"""
Drawdown helpers for the §6.4 rebalance-block check and weekly review surveillance.

Two views:

1. **Per-scheme drawdown** (`current_drawdown`) — how far below its trailing peak
   the latest NAV sits. Negative number, e.g. -0.18 = 18% below peak.

2. **Aggregate equity drawdown** (`aggregate_equity_drawdown`) — value-weighted
   drawdown across the equity holdings in a sub-portfolio. This is the input to
   principles.md §6.4: "Don't rebalance during a 20%+ drawdown."

What counts as "equity" for drawdown purposes:
- Pure equity schemes (SEBI category prefix "Equity Scheme -")
- Optionally, equity-oriented hybrids (Aggressive Hybrid, Equity Savings, and
  Multi Asset funds with ≥65% equity). Default OFF — drawdown is a price-volatility
  signal, hybrids dampen it. Pass include_hybrid_equity_oriented=True to include.

Used by:
- scripts/discover.py (Phase 0 of fund-allocate)
- fund-allocate's drawdown gate before equity-additive recommendations
- portfolio-review's findings-checklist line 56 (currently inlined; should call here)
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from .db import get_conn
    from .transactions import (
        DEFAULT_LEDGER_PATH,
        load_transactions,
        current_value_per_scheme,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from db import get_conn  # type: ignore
    from transactions import (  # type: ignore
        DEFAULT_LEDGER_PATH,
        load_transactions,
        current_value_per_scheme,
    )


DEFAULT_LOOKBACK_DAYS = 730  # ~24 months — matches portfolio-review's findings-checklist


def peak_nav(
    scheme_code: int,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    db_path=None,
) -> tuple[str, float] | None:
    """
    Return (date, NAV) of the highest NAV in the trailing `lookback_days` window.
    Window is anchored to the latest available NAV date for this scheme.

    Returns None if the scheme has no NAV history at all.
    """
    with get_conn(db_path) as conn:
        latest_row = conn.execute(
            "SELECT nav_date FROM nav_history "
            "WHERE scheme_code = ? ORDER BY nav_date DESC LIMIT 1",
            (scheme_code,),
        ).fetchone()
        if not latest_row:
            return None
        latest_date = datetime.strptime(latest_row["nav_date"], "%Y-%m-%d").date()
        window_start = (latest_date - timedelta(days=lookback_days)).isoformat()
        peak = conn.execute(
            "SELECT nav_date, nav FROM nav_history "
            "WHERE scheme_code = ? AND nav_date >= ? "
            "ORDER BY nav DESC, nav_date ASC LIMIT 1",
            (scheme_code, window_start),
        ).fetchone()
    if not peak:
        return None
    return peak["nav_date"], peak["nav"]


def current_drawdown(
    scheme_code: int,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    db_path=None,
) -> dict | None:
    """
    Per-scheme drawdown vs trailing peak.

    Returns:
        {
          "scheme_code": int,
          "peak_date": str,
          "peak_nav": float,
          "latest_date": str,
          "latest_nav": float,
          "drawdown": float,          # negative or zero; -0.18 = 18% below peak
          "days_since_peak": int,
        }
    or None if NAV history is missing.
    """
    pk = peak_nav(scheme_code, lookback_days, db_path)
    if not pk:
        return None
    peak_d, peak_n = pk
    with get_conn(db_path) as conn:
        latest = conn.execute(
            "SELECT nav_date, nav FROM nav_history "
            "WHERE scheme_code = ? ORDER BY nav_date DESC LIMIT 1",
            (scheme_code,),
        ).fetchone()
    if not latest:
        return None
    latest_d, latest_n = latest["nav_date"], latest["nav"]
    drawdown = (latest_n / peak_n) - 1.0 if peak_n > 0 else 0.0
    days_since = (
        datetime.strptime(latest_d, "%Y-%m-%d").date()
        - datetime.strptime(peak_d, "%Y-%m-%d").date()
    ).days
    return {
        "scheme_code": scheme_code,
        "peak_date": peak_d,
        "peak_nav": peak_n,
        "latest_date": latest_d,
        "latest_nav": latest_n,
        "drawdown": round(drawdown, 6),
        "days_since_peak": days_since,
    }


# Categories whose schemes count as "equity" for drawdown purposes.
EQUITY_CATEGORY_PREFIXES = ("Equity Scheme -",)

# Canonical AMFI category strings (verified via SELECT DISTINCT category FROM schemes).
# Note: AMFI uses "Hybrid Scheme - Equity Savings" (no "Fund" suffix).
HYBRID_EQUITY_ORIENTED_CATEGORIES = (
    "Hybrid Scheme - Aggressive Hybrid Fund",
    "Hybrid Scheme - Equity Savings",
    "Hybrid Scheme - Multi Asset Allocation",
    # Balanced Hybrid is borderline; user-overlay can promote specific schemes
)

# Tokens that mark an "Other Scheme - Index Funds" entry as a debt/gilt index
# rather than an equity index. Used by classify_sleeve to disambiguate.
DEBT_INDEX_NAME_TOKENS = (
    "gilt",
    "g-sec",
    "g sec",
    "bharat bond",
    "psu bond",
    "psu debt",
    "constant maturity",
    "constant duration",
    "10 yr",
    "10-yr",
    "10 year",
    "sdl",
    "debt index",
)


def classify_sleeve(category: str | None, scheme_name: str | None = None) -> str:
    """
    Classify a SEBI category (with optional scheme name for disambiguation) into
    one of: equity / debt / gold / hybrid / other.

    This is the single source of truth for sleeve classification across the
    codebase — both the §6.4 drawdown gate (is_equity_for_drawdown) and the
    Phase-0 sub-portfolio totals (discover.py) call into here so the two views
    of "equity" cannot disagree.

    Index funds and overseas FoFs live under "Other Scheme - ..." categories
    in AMFI vocabulary, so a category-prefix-only check would silently exclude
    real equity exposure from the drawdown gate. Name-based disambiguation
    handles gold-FoFs (categorised as "Other Scheme - FoF Domestic") and
    debt-index funds (categorised as "Other Scheme - Index Funds").
    """
    if not category:
        return "other"
    if category.startswith("Equity Scheme"):
        return "equity"
    if category.startswith("Debt Scheme"):
        return "debt"
    if category.startswith("Hybrid Scheme"):
        return "hybrid"
    if category == "Other Scheme - Gold ETF":
        return "gold"
    nm = (scheme_name or "").lower()
    if category.startswith("Other Scheme - FoF Domestic"):
        if "gold" in nm:
            return "gold"
        # Bharat Bond ETF FoFs and other debt FoFs live here too
        if any(tok in nm for tok in DEBT_INDEX_NAME_TOKENS):
            return "debt"
        # Default: equity FoF (e.g. fund-of-equity-funds)
        return "equity"
    if category == "Other Scheme - FoF Overseas":
        # Default to equity (international equity FoFs are the dominant case);
        # name-based override for the rare overseas debt FoF.
        if any(tok in nm for tok in DEBT_INDEX_NAME_TOKENS):
            return "debt"
        return "equity"
    if category == "Other Scheme - Index Funds":
        if any(tok in nm for tok in DEBT_INDEX_NAME_TOKENS):
            return "debt"
        return "equity"
    if category == "Other Scheme - Other  ETFs" or category == "Other Scheme - Other ETFs":
        # AMFI sometimes emits a double space. Treat as equity unless name says debt.
        if any(tok in nm for tok in DEBT_INDEX_NAME_TOKENS):
            return "debt"
        return "equity"
    return "other"


def is_equity_for_drawdown(
    category: str | None,
    scheme_name: str | None = None,
    include_hybrid_equity_oriented: bool = False,
) -> bool:
    """
    True if a holding contributes to the §6.4 aggregate equity drawdown gate.

    `scheme_name` enables name-based disambiguation for "Other Scheme - ..."
    categories that mix equity and debt (e.g. Index Funds, FoF Domestic).
    Callers that don't have the name will lose the index/overseas exposure
    from the gate — pass it whenever available.
    """
    sleeve = classify_sleeve(category, scheme_name)
    if sleeve == "equity":
        return True
    if include_hybrid_equity_oriented and sleeve == "hybrid":
        return category in HYBRID_EQUITY_ORIENTED_CATEGORIES
    return False


def aggregate_equity_drawdown(
    sub_portfolio: str | None = None,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    include_hybrid_equity_oriented: bool = False,
    ledger_path=None,
    db_path=None,
) -> dict:
    """
    Value-weighted aggregate drawdown across equity holdings.

    sub_portfolio:
        - "user" / "father" / "joint-locked": restrict to that sub-portfolio
        - None: aggregate across all sub-portfolios

    Returns:
        {
          "sub_portfolio": str | None,
          "total_equity_value_inr": float,
          "weighted_drawdown": float,        # value-weighted; negative
          "block_at_minus_20pct": bool,      # principle 6.4 gate
          "schemes": [
            {
              "scheme_code": int, "scheme_name": str, "category": str,
              "current_value_inr": float, "weight": float, "drawdown": float,
              "peak_date": str, "latest_date": str,
            },
            ...
          ],
          "missing_history": [scheme_code, ...]   # equity holdings with no NAV history
        }
    """
    txns = load_transactions(ledger_path)
    if not txns:
        return {
            "sub_portfolio": sub_portfolio,
            "total_equity_value_inr": 0.0,
            "weighted_drawdown": 0.0,
            "block_at_minus_20pct": False,
            "schemes": [],
            "missing_history": [],
        }
    if sub_portfolio:
        txns = [t for t in txns if t.get("sub_portfolio") == sub_portfolio]

    with get_conn(db_path) as conn:
        cv = current_value_per_scheme(txns, conn)
        # Pull category for every scheme we hold
        if not cv:
            categories = {}
        else:
            placeholders = ",".join("?" * len(cv))
            rows = conn.execute(
                f"SELECT scheme_code, scheme_name, category FROM schemes "
                f"WHERE scheme_code IN ({placeholders})",
                list(cv.keys()),
            ).fetchall()
            categories = {r["scheme_code"]: (r["scheme_name"], r["category"]) for r in rows}

    rows_out = []
    missing = []
    total_equity_value = 0.0
    weighted_dd_numerator = 0.0

    for sc, info in cv.items():
        name, cat = categories.get(sc, (None, None))
        if not is_equity_for_drawdown(cat, name, include_hybrid_equity_oriented):
            continue
        cur_val = info.get("current_value_inr")
        # An equity holding with units > 0 but no NAV history shows up here as
        # current_value_inr=None. That means the gate cannot value-weight it,
        # so we record it in `missing_history` and surface to the caller — the
        # gate may understate true drawdown when this list is non-empty.
        if cur_val is None:
            if info.get("units", 0) > 0:
                missing.append(sc)
            continue
        if cur_val <= 0:
            continue
        dd = current_drawdown(sc, lookback_days, db_path)
        if not dd:
            missing.append(sc)
            continue
        rows_out.append({
            "scheme_code": sc,
            "scheme_name": name,
            "category": cat,
            "current_value_inr": cur_val,
            "drawdown": dd["drawdown"],
            "peak_date": dd["peak_date"],
            "latest_date": dd["latest_date"],
        })
        total_equity_value += cur_val
        weighted_dd_numerator += cur_val * dd["drawdown"]

    weighted_dd = (weighted_dd_numerator / total_equity_value) if total_equity_value > 0 else 0.0
    # Add weight column now that totals are known
    for r in rows_out:
        r["weight"] = round(r["current_value_inr"] / total_equity_value, 4) if total_equity_value > 0 else 0.0

    return {
        "sub_portfolio": sub_portfolio,
        "total_equity_value_inr": round(total_equity_value, 2),
        "weighted_drawdown": round(weighted_dd, 6),
        "block_at_minus_20pct": weighted_dd <= -0.20,
        "schemes": sorted(rows_out, key=lambda r: r["drawdown"]),
        "missing_history": missing,
    }
