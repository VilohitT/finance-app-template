"""
Fund quality query interface — TER, manager, AUM, returns, vintage.

Combines three sources:

1. **schemes table** (populated by fetch_nav.py from AMFI's NAVAll.txt)
   Provides: scheme_name, amc, category, plan, option_type. AUM column exists
   (added Phase 3) but is currently NULL for all schemes pending an AMFI AUM
   fetcher. Until that exists, AUM comes from fund_quality.json overrides.

2. **nav_history table** (populated by fetch_nav.py daily and fetch_nav_history.py
   for historical backfills). Used to derive:
     - vintage_date    = MIN(nav_date) for the scheme
     - return_1y/3y/5y = annualised growth over the trailing window

3. **fund_quality.json** (user-maintained at `data/fund_quality.json`)
   Per-scheme overlay with TER, manager_name, manager_since, optional AUM
   override, last_verified date, free-form notes. Slow-moving qualitative data
   that no public source aggregates reliably across all funds.

When sources conflict (e.g., AUM in both schemes table and JSON), the JSON
override wins. The merged dict tracks `aum_source` so callers know which
source produced each value.

Used by:
- fund-allocate skill (selecting candidates from the universe)
- portfolio-review skill (cross-checking quality on held funds, when needed)
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Reuse the connection helper. Try package import; fall back to script-style.
try:
    from .db import get_conn
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from db import get_conn  # type: ignore


# Project root: <root>/scripts/lib/fund_quality.py → parents[2] is <root>
# fund_quality.json lives in data/ (canonical location since Phase 3 install)
DEFAULT_JSON_PATH = Path(__file__).resolve().parents[2] / "data" / "fund_quality.json"


# Fields that fund_quality.json contributes; used for completeness scoring.
QUALITY_FIELDS = ("ter", "manager_name", "manager_since", "aum_crore")


def _today() -> date:
    """Indirection for tests to override 'today' if needed."""
    return date.today()


def load_quality(json_path: Path | str | None = None) -> dict[int, dict]:
    """
    Load fund_quality.json. Returns dict keyed by int scheme_code.

    File shape (root object):
        {
          "_meta": {...},                    # ignored by code
          "schemes": {
            "122639": {                      # JSON keys are strings; we coerce to int
              "name_ref": "...",             # for editor's reference; not consumed
              "ter": 0.62,
              "manager_name": "...",
              "manager_since": "2013-05-13", # ISO YYYY-MM-DD
              "aum_crore": 65000.0,
              "last_verified": "2026-05-09",
              "notes": "..."
            },
            ...
          }
        }

    Missing file or empty schemes block → returns {}. Malformed JSON raises.
    """
    path = Path(json_path) if json_path else DEFAULT_JSON_PATH
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {}
    schemes_block = data.get("schemes", {}) if isinstance(data.get("schemes"), dict) else {}
    out: dict[int, dict] = {}
    for k, v in schemes_block.items():
        if v is None:
            continue
        try:
            out[int(k)] = v
        except (TypeError, ValueError):
            continue  # skip malformed key
    return out


def get_vintage(scheme_code: int, db_path=None) -> str | None:
    """
    Earliest nav_date for this scheme in nav_history. ISO YYYY-MM-DD or None.

    'Vintage' here = first date we have NAV data, which approximates the scheme's
    listing/inception date for schemes covered by the backfill. For schemes where
    NAV history was never backfilled (only today's NAVAll.txt), vintage will read
    as 'today' which is misleading — callers should treat that as 'unknown
    vintage' rather than 'just launched'. The vintage_years field in get_quality
    flags this implicitly: 0.0 vintage_years on a real scheme = 'no history'.
    """
    with get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT MIN(nav_date) AS earliest FROM nav_history WHERE scheme_code = ?",
            (scheme_code,),
        ).fetchone()
    return row["earliest"] if row and row["earliest"] else None


def get_returns(scheme_code: int, period_days: int, db_path=None) -> float | None:
    """
    Annualised trailing return over the last `period_days` days.

    Returns decimal (0.12 = 12% p.a.), or None if insufficient history. The
    annualisation requires at least 80% of the requested period to be covered
    by available data; below that, returns None to avoid misleading short-window
    annualisations.

    Implementation: fetch latest NAV and the closest NAV on/before
    (latest_date - period_days). Compute (latest/past) ** (365/actual_days) - 1.
    """
    if period_days < 1:
        return None

    with get_conn(db_path) as conn:
        latest_row = conn.execute(
            "SELECT nav_date, nav FROM nav_history "
            "WHERE scheme_code = ? "
            "ORDER BY nav_date DESC LIMIT 1",
            (scheme_code,),
        ).fetchone()
        if not latest_row:
            return None

        latest_date = datetime.strptime(latest_row["nav_date"], "%Y-%m-%d").date()
        target_date = latest_date - timedelta(days=period_days)

        past_row = conn.execute(
            "SELECT nav_date, nav FROM nav_history "
            "WHERE scheme_code = ? AND nav_date <= ? "
            "ORDER BY nav_date DESC LIMIT 1",
            (scheme_code, target_date.isoformat()),
        ).fetchone()
        if not past_row:
            return None

    past_date = datetime.strptime(past_row["nav_date"], "%Y-%m-%d").date()
    actual_days = (latest_date - past_date).days

    # Require at least 80% of the requested window. Avoids annualising a 60-day
    # return into a "5-year" figure.
    if actual_days < period_days * 0.8 or actual_days < 1:
        return None
    if past_row["nav"] is None or past_row["nav"] <= 0:
        return None

    growth = latest_row["nav"] / past_row["nav"]
    return growth ** (365.0 / actual_days) - 1.0


def _years_between(iso_start: str | None, ref: date | None = None) -> float | None:
    """Helper: return decimal years between iso_start and ref (today by default)."""
    if not iso_start:
        return None
    try:
        start = datetime.strptime(iso_start, "%Y-%m-%d").date()
    except ValueError:
        return None
    end = ref or _today()
    return (end - start).days / 365.25


def get_quality(scheme_code: int, db_path=None, json_path=None) -> dict:
    """
    Return merged quality data for a single scheme.

    Joins schemes table (structural metadata + AUM if populated), nav_history
    derivations (vintage, trailing returns), and fund_quality.json (TER, manager,
    manual AUM override).

    Returns a dict with these keys (any may be None except scheme_code):
      scheme_code, scheme_name, amc, category, plan, option_type
      ter, manager_name, manager_since, manager_tenure_years
      aum_crore, aum_source ('json' / 'db' / None)
      last_verified, notes
      vintage_date, vintage_years
      return_1y, return_3y, return_5y
      quality_completeness    (0.0-1.0; fraction of QUALITY_FIELDS populated)

    For a scheme not in the schemes table, returns {scheme_code, error}.
    """
    json_data = load_quality(json_path)
    json_entry = json_data.get(scheme_code, {}) or {}

    with get_conn(db_path) as conn:
        scheme_row = conn.execute(
            "SELECT * FROM schemes WHERE scheme_code = ?", (scheme_code,)
        ).fetchone()
        if not scheme_row:
            return {"scheme_code": scheme_code, "error": "scheme not found in schemes table"}
        scheme_dict = dict(scheme_row)

    vintage_date = get_vintage(scheme_code, db_path)
    vintage_years = _years_between(vintage_date)

    manager_since = json_entry.get("manager_since")
    manager_tenure_years = _years_between(manager_since)

    # AUM: JSON override wins over schemes.aum_crore
    aum_crore: float | None = json_entry.get("aum_crore")
    aum_source: str | None = None
    if aum_crore is not None:
        aum_source = "json"
    else:
        db_aum = scheme_dict.get("aum_crore")
        if db_aum is not None:
            aum_crore = db_aum
            aum_source = "db"

    return_1y = get_returns(scheme_code, 365, db_path)
    return_3y = get_returns(scheme_code, 365 * 3, db_path)
    return_5y = get_returns(scheme_code, 365 * 5, db_path)

    populated = sum(1 for f in QUALITY_FIELDS if json_entry.get(f) is not None)
    completeness = populated / len(QUALITY_FIELDS)

    return {
        "scheme_code": scheme_code,
        "scheme_name": scheme_dict["scheme_name"],
        "amc": scheme_dict.get("amc"),
        "category": scheme_dict.get("category"),
        "plan": scheme_dict.get("plan"),
        "option_type": scheme_dict.get("option_type"),

        # JSON-sourced (slow-moving qualitative data)
        "ter": json_entry.get("ter"),
        "manager_name": json_entry.get("manager_name"),
        "manager_since": manager_since,
        "manager_tenure_years": manager_tenure_years,
        "aum_crore": aum_crore,
        "aum_source": aum_source,
        "last_verified": json_entry.get("last_verified"),
        "notes": json_entry.get("notes"),

        # Derived from nav_history
        "vintage_date": vintage_date,
        "vintage_years": vintage_years,
        "return_1y": return_1y,
        "return_3y": return_3y,
        "return_5y": return_5y,

        # Meta — how confident is fund-allocate in this row's quality data?
        "quality_completeness": completeness,
    }


def filter_candidates(
    category: str | None = None,
    plan: str | None = None,
    min_aum_crore: float | None = None,
    max_ter: float | None = None,
    min_vintage_years: float | None = None,
    min_manager_tenure_years: float | None = None,
    rank_by: str = "return_3y",
    limit: int = 20,
    require_quality_data: bool = False,
    db_path=None,
    json_path=None,
) -> list[dict]:
    """
    Find ranked candidate funds matching the given filters.

    Two-stage filtering for performance:
      1. SQL filter on category/plan (cheap; narrows ~14,000 schemes to ~50-200)
      2. Python filter on derived/JSON fields (vintage, AUM, TER, manager tenure)

    Returns a list of dicts (same shape as get_quality output) sorted by
    `rank_by` descending. Funds with None for the rank field are placed last,
    not excluded (so that a fund with no NAV history still surfaces if it
    matches structural filters — useful for showing "this fund matches your
    category but we have no return data on it").

    If require_quality_data=True, restricts to funds with all QUALITY_FIELDS
    populated. Use this for high-confidence fund-allocate recommendations
    where you want all four of TER, manager_name, manager_since, aum_crore.
    """
    with get_conn(db_path) as conn:
        sql = "SELECT scheme_code FROM schemes WHERE 1=1"
        params: list = []
        if category:
            sql += " AND category = ?"
            params.append(category)
        if plan:
            sql += " AND plan = ?"
            params.append(plan)
        candidate_codes = [r["scheme_code"] for r in conn.execute(sql, params).fetchall()]

    candidates: list[dict] = []
    for code in candidate_codes:
        q = get_quality(code, db_path, json_path)
        if q.get("error"):
            continue

        # Post-hydration filters. None on a filtered field excludes the fund —
        # we can't confirm the threshold is met without data.
        if min_vintage_years is not None:
            if q["vintage_years"] is None or q["vintage_years"] < min_vintage_years:
                continue
        if min_aum_crore is not None:
            if q["aum_crore"] is None or q["aum_crore"] < min_aum_crore:
                continue
        if max_ter is not None:
            if q["ter"] is None or q["ter"] > max_ter:
                continue
        if min_manager_tenure_years is not None:
            if q["manager_tenure_years"] is None or q["manager_tenure_years"] < min_manager_tenure_years:
                continue
        if require_quality_data and q["quality_completeness"] < 1.0:
            continue

        candidates.append(q)

    # Sort: None values last (so they don't poison the top of the list);
    # otherwise descending by rank_by.
    def _sort_key(c):
        v = c.get(rank_by)
        return (1, 0.0) if v is None else (0, -float(v))

    candidates.sort(key=_sort_key)
    return candidates[:limit]
