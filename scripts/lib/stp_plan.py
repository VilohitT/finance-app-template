"""
STP and lump-purchase planner.

When fund-allocate decides to deploy ₹X into equity, two paths:

- ₹X < ~₹3L → direct lump purchase (plan_lump_purchase)
- ₹X ≥ ~₹3L → park in arbitrage/liquid, STP over 3-6 months (plan_stp)

Both helpers compute the structured artefacts that the caller writes:
- A purchase transaction for the parking buy (if STP) or the destination
  buy (if direct lump).
- A `recurring.json` STP entry the runner consumes to generate monthly tranches.

The planner does NOT mutate anything on disk — it returns dicts that the
caller appends and saves. Keeps the planning step pure and testable.

References:
- principles.md §8.5 (STP threshold and behavioural smoothing)
- scripts/lib/transactions.py (txn schema)
- data/recurring.json (registry schema)
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

try:
    from .transactions import (
        load_transactions,
        make_txn_id,
        latest_nav,
        VALID_TAX_CATEGORIES,
        VALID_SUB_PORTFOLIOS,
    )
    from .db import get_conn
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from transactions import (  # type: ignore
        load_transactions,
        make_txn_id,
        latest_nav,
        VALID_TAX_CATEGORIES,
        VALID_SUB_PORTFOLIOS,
    )
    from db import get_conn  # type: ignore


STP_THRESHOLD_INR = 300000  # principle 8.5 — lumps ≥ ~₹3L into equity → STP
DEFAULT_STP_MONTHS = 6


def _adjust_day_of_month(year: int, month: int, day: int) -> date:
    """Snap day-of-month to the last valid date in the target month if needed."""
    # March 31 + 1 month → April 30 (April has only 30 days)
    while True:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1
            if day < 28:  # safety
                raise


def _next_tranche_date(start: date, n_months: int, day_of_month: int) -> date:
    """Date of the n-th monthly tranche, anchored to (start.year, start.month)
    on `day_of_month`. Use _first_tranche_on_or_after to pick the anchor that
    keeps the schedule strictly on or after `start`."""
    month = start.month + n_months
    year = start.year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    return _adjust_day_of_month(year, month, day_of_month)


def _first_tranche_on_or_after(start: date, day_of_month: int) -> date:
    """
    Return the first `day_of_month` that lands on or after `start`.

    If start.day <= day_of_month, the same calendar month works; otherwise we
    roll into the following month. This is the anchor that subsequent
    `_next_tranche_date(anchor, n, day_of_month)` calls compose with.
    """
    candidate = _adjust_day_of_month(start.year, start.month, day_of_month)
    if candidate < start:
        roll_month = start.month + 1
        roll_year = start.year + (roll_month - 1) // 12
        roll_month = ((roll_month - 1) % 12) + 1
        candidate = _adjust_day_of_month(roll_year, roll_month, day_of_month)
    return candidate


def plan_lump_purchase(
    amount_inr: float,
    scheme_code: int,
    scheme_name: str,
    sub_portfolio: str,
    purchase_date: str | None = None,
    nav: float | None = None,
    db_path=None,
    ledger_path=None,
    notes: str = "",
) -> dict:
    """
    Plan a one-shot lump purchase. Returns the txn dict to append to the ledger.

    NAV resolution: caller may pass `nav`; otherwise looked up from market.db
    (latest if `purchase_date` is None or in the future, else the closest
    on-or-before-the-date NAV).
    """
    if sub_portfolio not in VALID_SUB_PORTFOLIOS:
        raise ValueError(f"sub_portfolio must be one of {VALID_SUB_PORTFOLIOS}")
    if amount_inr <= 0:
        raise ValueError(f"amount must be positive, got {amount_inr}")

    pdate = purchase_date or date.today().isoformat()

    if nav is None:
        with get_conn(db_path) as conn:
            row = conn.execute(
                "SELECT nav FROM nav_history WHERE scheme_code = ? AND nav_date <= ? "
                "ORDER BY nav_date DESC LIMIT 1",
                (scheme_code, pdate),
            ).fetchone()
            if not row:
                latest = latest_nav(scheme_code, conn)
                if not latest:
                    raise ValueError(f"No NAV available for scheme {scheme_code}")
                _, nav = latest
            else:
                nav = row["nav"]

    units = round(amount_inr / nav, 4)
    txns = load_transactions(ledger_path)
    txn_id = make_txn_id(pdate, scheme_code, "purchase", txns)

    return {
        "txn_id": txn_id,
        "date": pdate,
        "type": "purchase",
        "scheme_code": scheme_code,
        "scheme_name": scheme_name,
        "amount_inr": round(float(amount_inr), 2),
        "nav": float(nav),
        "units": units,
        "sub_portfolio": sub_portfolio,
        "source": "user-dictated",
        "linked_txn_id": None,
        "stp_id": None,
        "sip_id": None,
        "exit_load_inr": 0.0,
        "notes": notes or "lump purchase via plan_lump_purchase",
    }


def plan_stp(
    lump_inr: float,
    source_scheme_code: int,
    source_scheme_name: str,
    dest_scheme_code: int,
    dest_scheme_name: str,
    months: int,
    sub_portfolio: str,
    source_tax_category: str,
    start_date: str | None = None,
    day_of_month: int = 15,
    parking_purchase_date: str | None = None,
    parking_nav: float | None = None,
    exit_load: dict | None = None,
    db_path=None,
    ledger_path=None,
) -> dict:
    """
    Plan a lump → STP deployment.

    Returns:
      {
        "parking_purchase": {...},        # txn dict to append to ledger
        "recurring_stp": {...},           # entry to append to recurring.json["stps"]
        "schedule": [date, ...],          # the n monthly tranche dates
        "monthly_amount_inr": float,
      }

    Validation:
      - sub_portfolio in VALID_SUB_PORTFOLIOS
      - source_tax_category in VALID_TAX_CATEGORIES
      - months ∈ [1, 12]
      - day_of_month ∈ [1, 31]
      - lump_inr > 0
    """
    if sub_portfolio not in VALID_SUB_PORTFOLIOS:
        raise ValueError(f"sub_portfolio must be one of {VALID_SUB_PORTFOLIOS}")
    if source_tax_category not in VALID_TAX_CATEGORIES:
        raise ValueError(f"source_tax_category must be one of {VALID_TAX_CATEGORIES}")
    if not (1 <= months <= 12):
        raise ValueError(f"months must be 1-12, got {months}")
    if not (1 <= day_of_month <= 31):
        raise ValueError(f"day_of_month must be 1-31, got {day_of_month}")
    if lump_inr <= 0:
        raise ValueError(f"lump_inr must be positive, got {lump_inr}")

    pdate = parking_purchase_date or date.today().isoformat()
    sdate = start_date or date.today().isoformat()
    sdate_d = datetime.strptime(sdate, "%Y-%m-%d").date()

    parking = plan_lump_purchase(
        amount_inr=lump_inr,
        scheme_code=source_scheme_code,
        scheme_name=source_scheme_name,
        sub_portfolio=sub_portfolio,
        purchase_date=pdate,
        nav=parking_nav,
        db_path=db_path,
        ledger_path=ledger_path,
        notes=f"STP parking — {months}-month deployment to scheme {dest_scheme_code}",
    )

    monthly = round(lump_inr / months, 2)
    # Rounding can leave a residual of up to ~₹0.01 × months in the parking
    # source. Track it so the final tranche can absorb it (caller-visible via
    # `final_tranche_amount_inr`); the runner reads `amount_inr_per_tranche`
    # for tranches 1..N-1 and an optional override for the last.
    final_tranche = round(lump_inr - monthly * (months - 1), 2)
    # Anchor the schedule on the first valid tranche on or after start_date,
    # so a start_date past `day_of_month` rolls into the next month rather than
    # emitting a tranche before start_date.
    anchor = _first_tranche_on_or_after(sdate_d, day_of_month)
    schedule = [
        _next_tranche_date(anchor, n, day_of_month).isoformat() for n in range(months)
    ]
    end_date = schedule[-1]

    # Construct stp_id deterministically: STP-<startdate>-<source>-<dest>
    stp_id = f"STP-{sdate}-{source_scheme_code}-to-{dest_scheme_code}"

    recurring_entry = {
        "stp_id": stp_id,
        "source_scheme_code": source_scheme_code,
        "source_scheme_name": source_scheme_name,
        "destination_scheme_code": dest_scheme_code,
        "destination_scheme_name": dest_scheme_name,
        "amount_inr_per_tranche": monthly,
        # Last-tranche override absorbs the rounding residual so monthly×N
        # exactly equals lump_inr. Runner reads this on the final scheduled
        # date when present; defaults to amount_inr_per_tranche otherwise.
        "final_tranche_amount_inr": final_tranche,
        "frequency": "monthly",
        "day_of_month": day_of_month,
        "start_date": sdate,
        "end_date": end_date,
        "sub_portfolio": sub_portfolio,
        "source_tax_category": source_tax_category,
        "stop_when_source_exhausted": True,
        "exit_load": exit_load,
        "status": "active",
    }

    return {
        "parking_purchase": parking,
        "recurring_stp": recurring_entry,
        "schedule": schedule,
        "monthly_amount_inr": monthly,
        "final_tranche_amount_inr": final_tranche,
        "total_inr": round(monthly * (months - 1) + final_tranche, 2),
    }


def should_use_stp(equity_amount_inr: float, threshold_inr: float = STP_THRESHOLD_INR) -> bool:
    """Principle 8.5: lumps ≥ ~₹3L into equity → STP."""
    return equity_amount_inr >= threshold_inr
