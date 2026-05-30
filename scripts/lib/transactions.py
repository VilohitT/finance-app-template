"""
Transaction ledger for the finance-app data layer.

The ledger lives at data/transactions.json. Every event that changes
unit holdings — purchase, SIP, STP leg, switch, redemption, dividend
reinvestment — appends one row. portfolio.md becomes a derived view,
regenerated from the ledger by render_portfolio.py.

Schema
------
Each transaction is a dict with keys:

    txn_id            : str   — unique, format "YYYY-MM-DD-<scheme>-<type>-<seq>"
    date              : str   — ISO date "YYYY-MM-DD"
    type              : str   — "purchase" | "redemption" | "switch-in" | "switch-out"
    scheme_code       : int   — AMFI scheme code
    scheme_name       : str   — canonical AMFI name (informational; scheme_code is the key)
    amount_inr        : float — signed; positive on purchases, negative on redemptions
    nav               : float — NAV used for this leg (₹ per unit)
    units             : float — signed; positive on purchases, negative on redemptions
    sub_portfolio     : str   — "user" | "father" | "joint-locked"
    source            : str   — "user-dictated" | "stp-runner" | "sip-runner" | "backfill"
    linked_txn_id     : str?  — pairs the two legs of a switch/STP (null otherwise)
    stp_id            : str?  — groups all tranches of a recurring STP
    sip_id            : str?  — groups all tranches of a recurring SIP
    exit_load_inr     : float — exit load deducted on this leg (0 if none)
    cost_basis_consumed_inr : float?  — only on redemption rows; FIFO-computed
    realised_gain_inr       : float?  — only on redemption rows
    gain_classification     : str?    — only on redemption rows; see classify_gain()
    notes             : str   — free-text, default ""

The ledger is append-only in spirit. Edits are allowed only to fix mistakes
(e.g., wrong NAV from a holiday); never to "rewrite history" of executed flows.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

DEFAULT_LEDGER_PATH = Path(__file__).resolve().parents[2] / "data" / "transactions.json"
DEFAULT_RECURRING_PATH = Path(__file__).resolve().parents[2] / "data" / "recurring.json"

VALID_TYPES = {"purchase", "redemption", "switch-in", "switch-out"}
VALID_SUB_PORTFOLIOS = {"user", "father", "joint-locked"}
VALID_SOURCES = {"user-dictated", "stp-runner", "sip-runner", "backfill", "manual-correction"}

# Tax categories used by classify_gain. The recurring.json STP entries and the
# log_transaction.py CLI must specify one of these for the source scheme.
VALID_TAX_CATEGORIES = {
    "equity",                    # equity-oriented MF (≥65% equity); LTCG > 12mo
    "non-equity-pre-Apr-2023",   # debt/hybrid acquired before 1-Apr-2023; LTCG > 24mo, 20% with indexation (legacy)
    "non-equity-pre-Apr-2023-no-indexation-post-23-Jul-2024",  # post-Budget 2024 LTCG flat 12.5% no-indexation, 24mo
    "specified-mf",              # debt MF acquired on/after 1-Apr-2023 OR gold MF; slab rate, no LTCG benefit
    "hybrid-equity-oriented",    # ≥65% equity hybrid; treated as equity
    "hybrid-debt-oriented",      # <65% equity; treated as specified-mf if acquired post-Apr-2023, else non-equity
}

EQUITY_LTCG_BOUNDARY_DAYS = 365      # >12 months for equity LTCG
NONEQUITY_LTCG_BOUNDARY_DAYS = 365 * 2  # >24 months for non-equity LTCG (post-2024)


# --------------------------------------------------------------------------
# Load / save
# --------------------------------------------------------------------------

def load_transactions(path: Path | str | None = None) -> list[dict]:
    """Load the ledger. Returns [] if the file is empty or missing."""
    p = Path(path) if path else DEFAULT_LEDGER_PATH
    if not p.exists():
        return []
    text = p.read_text().strip()
    if not text:
        return []
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError(f"{p}: expected a JSON list, got {type(data).__name__}")
    return data


def save_transactions(txns: list[dict], path: Path | str | None = None) -> None:
    """Atomic write: write to .tmp, fsync, rename. Survives mid-write crashes."""
    p = Path(path) if path else DEFAULT_LEDGER_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w") as f:
        json.dump(txns, f, indent=2, ensure_ascii=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(p)


def load_recurring(path: Path | str | None = None) -> dict:
    """Load the SIP/STP registry."""
    p = Path(path) if path else DEFAULT_RECURRING_PATH
    if not p.exists():
        return {"sips": [], "stps": []}
    data = json.loads(p.read_text())
    data.setdefault("sips", [])
    data.setdefault("stps", [])
    return data


def save_recurring(data: dict, path: Path | str | None = None) -> None:
    """Atomic write of the recurring registry."""
    p = Path(path) if path else DEFAULT_RECURRING_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(p)


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

def validate_transaction(t: dict) -> list[str]:
    """Return a list of human-readable problems with t. Empty list = valid."""
    errs: list[str] = []
    required = {"txn_id", "date", "type", "scheme_code", "scheme_name",
                "amount_inr", "nav", "units", "sub_portfolio", "source"}
    missing = required - set(t.keys())
    if missing:
        errs.append(f"missing keys: {sorted(missing)}")
        return errs

    if t["type"] not in VALID_TYPES:
        errs.append(f"type must be one of {VALID_TYPES}, got {t['type']!r}")
    if t["sub_portfolio"] not in VALID_SUB_PORTFOLIOS:
        errs.append(f"sub_portfolio must be one of {VALID_SUB_PORTFOLIOS}, got {t['sub_portfolio']!r}")
    if t["source"] not in VALID_SOURCES:
        errs.append(f"source must be one of {VALID_SOURCES}, got {t['source']!r}")

    try:
        datetime.strptime(t["date"], "%Y-%m-%d")
    except (ValueError, TypeError):
        errs.append(f"date must be ISO YYYY-MM-DD, got {t['date']!r}")

    if not isinstance(t["scheme_code"], int):
        errs.append(f"scheme_code must be int, got {type(t['scheme_code']).__name__}")

    if t["nav"] is not None and t["nav"] <= 0:
        errs.append(f"nav must be positive, got {t['nav']}")

    is_buy = t["type"] in {"purchase", "switch-in"}
    is_sell = t["type"] in {"redemption", "switch-out"}

    if is_buy and (t["amount_inr"] <= 0 or t["units"] <= 0):
        errs.append(f"buy-side legs need positive amount/units; got amount={t['amount_inr']}, units={t['units']}")
    if is_sell and (t["amount_inr"] >= 0 or t["units"] >= 0):
        errs.append(f"sell-side legs need negative amount/units; got amount={t['amount_inr']}, units={t['units']}")

    return errs


# --------------------------------------------------------------------------
# txn_id construction
# --------------------------------------------------------------------------

def _next_seq(date_str: str, scheme_code: int, type_: str, txns: Iterable[dict]) -> int:
    """Find the next unused sequence number for a (date, scheme, type) triple."""
    prefix = f"{date_str}-{scheme_code}-{type_}-"
    used = set()
    for t in txns:
        if t["txn_id"].startswith(prefix):
            try:
                used.add(int(t["txn_id"].rsplit("-", 1)[-1]))
            except ValueError:
                continue
    n = 1
    while n in used:
        n += 1
    return n


def make_txn_id(date_str: str, scheme_code: int, type_: str, txns: Iterable[dict]) -> str:
    return f"{date_str}-{scheme_code}-{type_}-{_next_seq(date_str, scheme_code, type_, txns)}"


# --------------------------------------------------------------------------
# NAV lookups (against market.db)
# --------------------------------------------------------------------------

def get_nav_on_date(scheme_code: int, target_date: str, conn: sqlite3.Connection) -> float | None:
    """Exact-date NAV lookup. Returns None if no row for that date."""
    row = conn.execute(
        "SELECT nav FROM nav_history WHERE scheme_code = ? AND nav_date = ?",
        (scheme_code, target_date),
    ).fetchone()
    return float(row[0]) if row else None


def nearest_business_day_nav(
    scheme_code: int,
    target_date: str,
    conn: sqlite3.Connection,
    direction: str = "forward",
    max_days: int = 7,
) -> tuple[str, float] | None:
    """
    NAV-on-or-after (direction='forward') or NAV-on-or-before (direction='backward')
    the target date, capped at max_days. Returns (actual_date, nav) or None.

    AMC convention: SIP/STP debits on a holiday post at the next-business-day NAV.
    Hence forward-search is the default for runners.
    """
    if direction == "forward":
        row = conn.execute(
            """
            SELECT nav_date, nav FROM nav_history
            WHERE scheme_code = ? AND nav_date >= ? AND nav_date <= DATE(?, ?)
            ORDER BY nav_date ASC LIMIT 1
            """,
            (scheme_code, target_date, target_date, f"+{max_days} days"),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT nav_date, nav FROM nav_history
            WHERE scheme_code = ? AND nav_date <= ? AND nav_date >= DATE(?, ?)
            ORDER BY nav_date DESC LIMIT 1
            """,
            (scheme_code, target_date, target_date, f"-{max_days} days"),
        ).fetchone()
    if not row:
        return None
    return (str(row[0]), float(row[1]))


def latest_nav(scheme_code: int, conn: sqlite3.Connection) -> tuple[str, float] | None:
    """Most recent NAV available for a scheme. (date, nav) or None."""
    row = conn.execute(
        "SELECT nav_date, nav FROM nav_history WHERE scheme_code = ? "
        "ORDER BY nav_date DESC LIMIT 1",
        (scheme_code,),
    ).fetchone()
    if not row:
        return None
    return (str(row[0]), float(row[1]))


# --------------------------------------------------------------------------
# Append helpers
# --------------------------------------------------------------------------

def make_purchase(
    *,
    date_str: str,
    scheme_code: int,
    scheme_name: str,
    amount_inr: float,
    nav: float,
    sub_portfolio: str,
    source: str,
    txns: list[dict],
    sip_id: str | None = None,
    stp_id: str | None = None,
    linked_txn_id: str | None = None,
    exit_load_inr: float = 0.0,
    notes: str = "",
    type_: str = "purchase",
) -> dict:
    """Build a purchase (or switch-in) row. Does not append; caller decides."""
    units = round(amount_inr / nav, 4)
    return {
        "txn_id": make_txn_id(date_str, scheme_code, type_, txns),
        "date": date_str,
        "type": type_,
        "scheme_code": scheme_code,
        "scheme_name": scheme_name,
        "amount_inr": round(amount_inr, 2),
        "nav": round(nav, 4),
        "units": units,
        "sub_portfolio": sub_portfolio,
        "source": source,
        "linked_txn_id": linked_txn_id,
        "stp_id": stp_id,
        "sip_id": sip_id,
        "exit_load_inr": round(exit_load_inr, 2),
        "notes": notes,
    }


def make_redemption(
    *,
    date_str: str,
    scheme_code: int,
    scheme_name: str,
    units_to_sell: float,
    nav: float,
    sub_portfolio: str,
    source: str,
    txns: list[dict],
    tax_category: str,
    stp_id: str | None = None,
    linked_txn_id: str | None = None,
    exit_load_inr: float = 0.0,
    notes: str = "",
    type_: str = "redemption",
) -> dict:
    """
    Build a redemption (or switch-out) row. Computes FIFO cost-basis consumed
    against existing rows for the same scheme_code, and fills realised_gain_inr
    + gain_classification.

    Does not mutate txns; the FIFO computation is purely for reporting.
    Note: classification uses the *earliest* consumed lot's purchase date for
    the holding-period check. If the FIFO consumes lots straddling the LTCG
    boundary, this is approximate — proper STCG/LTCG split requires per-lot
    accounting at tax-filing time. For weekly review this approximation is fine;
    flag in notes when it matters.
    """
    cost_basis, lots = consume_fifo(scheme_code, units_to_sell, txns)
    proceeds = round(units_to_sell * nav - exit_load_inr, 2)
    gain = round(proceeds - cost_basis, 2)

    earliest_purchase = lots[0][2] if lots else None
    classification = classify_gain(
        purchase_date=earliest_purchase,
        sale_date=date_str,
        tax_category=tax_category,
    ) if earliest_purchase else "unclassified"

    return {
        "txn_id": make_txn_id(date_str, scheme_code, type_, txns),
        "date": date_str,
        "type": type_,
        "scheme_code": scheme_code,
        "scheme_name": scheme_name,
        "amount_inr": -round(proceeds, 2),
        "nav": round(nav, 4),
        "units": -round(units_to_sell, 4),
        "sub_portfolio": sub_portfolio,
        "source": source,
        "linked_txn_id": linked_txn_id,
        "stp_id": stp_id,
        "sip_id": None,
        "exit_load_inr": round(exit_load_inr, 2),
        "cost_basis_consumed_inr": round(cost_basis, 2),
        "realised_gain_inr": gain,
        "gain_classification": classification,
        "fifo_lots_consumed": [
            {"units": round(u, 4), "source_txn_id": tid, "purchase_date": pd}
            for (u, tid, pd) in lots
        ],
        "notes": notes,
    }


# --------------------------------------------------------------------------
# Aggregations
# --------------------------------------------------------------------------

def units_per_scheme(txns: Iterable[dict]) -> dict[int, float]:
    """Net units held per scheme_code. Sums signed units across the ledger."""
    out: dict[int, float] = defaultdict(float)
    for t in txns:
        out[t["scheme_code"]] += t["units"]
    # Round to 4dp; expose via dict not defaultdict.
    return {k: round(v, 4) for k, v in out.items() if abs(v) > 1e-9}


def cost_basis_per_scheme(txns: Iterable[dict]) -> dict[int, float]:
    """
    Net cost basis still held per scheme_code, after FIFO consumption.
    = sum(buy amount_inr) - sum(cost_basis_consumed_inr on sell rows)
    """
    out: dict[int, float] = defaultdict(float)
    for t in txns:
        if t["type"] in {"purchase", "switch-in"}:
            out[t["scheme_code"]] += t["amount_inr"]
        elif t["type"] in {"redemption", "switch-out"}:
            out[t["scheme_code"]] -= t.get("cost_basis_consumed_inr", 0.0)
    return {k: round(v, 2) for k, v in out.items() if abs(v) > 0.01}


def current_value_per_scheme(
    txns: Iterable[dict],
    conn: sqlite3.Connection,
) -> dict[int, dict[str, Any]]:
    """
    Per-scheme current value summary. Returns:
        {
          scheme_code: {
            "units": float,
            "cost_basis_inr": float,
            "latest_nav": float | None,
            "latest_nav_date": str | None,
            "current_value_inr": float | None,
            "unrealised_gain_inr": float | None,
          }, ...
        }
    """
    units = units_per_scheme(txns)
    cost = cost_basis_per_scheme(txns)
    out: dict[int, dict[str, Any]] = {}
    for sc, u in units.items():
        latest = latest_nav(sc, conn)
        if latest:
            nd, nv = latest
            cv = round(u * nv, 2)
            cb = cost.get(sc, 0.0)
            out[sc] = {
                "units": u,
                "cost_basis_inr": cb,
                "latest_nav": nv,
                "latest_nav_date": nd,
                "current_value_inr": cv,
                "unrealised_gain_inr": round(cv - cb, 2),
            }
        else:
            out[sc] = {
                "units": u,
                "cost_basis_inr": cost.get(sc, 0.0),
                "latest_nav": None,
                "latest_nav_date": None,
                "current_value_inr": None,
                "unrealised_gain_inr": None,
            }
    return out


# --------------------------------------------------------------------------
# FIFO cost-basis consumer
# --------------------------------------------------------------------------

def consume_fifo(
    scheme_code: int,
    units_to_sell: float,
    txns: Iterable[dict],
) -> tuple[float, list[tuple[float, str, str]]]:
    """
    Compute the cost basis consumed when selling `units_to_sell` units of
    scheme_code from the FIFO queue derived from `txns`.

    Returns (total_cost_basis_consumed_inr, lots_consumed).
    lots_consumed is a list of (units, source_txn_id, source_purchase_date).

    FIFO is the income-tax default for MF unit accounting in India.

    Walks all prior buy rows in date order, subtracting any prior sells
    (also in date order) so partial earlier redemptions are honoured.
    """
    if units_to_sell <= 0:
        return (0.0, [])

    # Build the per-lot remaining queue. Lot = each buy row.
    lots: list[dict] = []  # {"date", "remaining", "nav", "txn_id"}
    sells_pending: list[float] = []  # sell sizes in date order

    sorted_txns = sorted(
        (t for t in txns if t["scheme_code"] == scheme_code),
        key=lambda t: (t["date"], t["txn_id"]),
    )
    for t in sorted_txns:
        if t["type"] in {"purchase", "switch-in"}:
            lots.append({
                "date": t["date"],
                "remaining": float(t["units"]),
                "nav": float(t["nav"]),
                "txn_id": t["txn_id"],
            })
        elif t["type"] in {"redemption", "switch-out"}:
            sells_pending.append(abs(float(t["units"])))

    # Apply prior sells against lots in FIFO order to find the live queue.
    for sold in sells_pending:
        remaining_to_apply = sold
        for lot in lots:
            if remaining_to_apply <= 1e-9:
                break
            if lot["remaining"] <= 1e-9:
                continue
            take = min(lot["remaining"], remaining_to_apply)
            lot["remaining"] -= take
            remaining_to_apply -= take

    # Now consume `units_to_sell` against the remaining lots.
    remaining_to_sell = units_to_sell
    cost_basis = 0.0
    consumed: list[tuple[float, str, str]] = []
    for lot in lots:
        if remaining_to_sell <= 1e-9:
            break
        if lot["remaining"] <= 1e-9:
            continue
        take = min(lot["remaining"], remaining_to_sell)
        cost_basis += take * lot["nav"]
        consumed.append((take, lot["txn_id"], lot["date"]))
        lot["remaining"] -= take
        remaining_to_sell -= take

    if remaining_to_sell > 1e-4:
        raise ValueError(
            f"FIFO under-supply: scheme {scheme_code} has insufficient units to sell "
            f"{units_to_sell:.4f} (short by {remaining_to_sell:.4f}). Check ledger."
        )
    return (round(cost_basis, 2), consumed)


# --------------------------------------------------------------------------
# Tax classification
# --------------------------------------------------------------------------

def classify_gain(
    *,
    purchase_date: str,
    sale_date: str,
    tax_category: str,
) -> str:
    """
    Coarse STCG/LTCG classification. tax-check skill should refine.

    Boundaries (post-Budget-2024, applicable to sales on/after 23-Jul-2024):
    - Equity / equity-oriented hybrid: > 12 months → LTCG (12.5% flat, ₹1.25L exemption)
    - Non-equity (legacy debt pre-Apr-2023, foreign, gold post-2024): > 24 months → LTCG (12.5% flat, no indexation)
    - Specified MF (post-Apr-2023 debt MF, gold MF, ≥65% debt hybrid): always slab — no LTCG benefit
    """
    p = datetime.strptime(purchase_date, "%Y-%m-%d").date()
    s = datetime.strptime(sale_date, "%Y-%m-%d").date()
    holding_days = (s - p).days

    if tax_category == "specified-mf" or tax_category == "hybrid-debt-oriented":
        return "STCG-debt-Specified-MF (slab)" if holding_days <= NONEQUITY_LTCG_BOUNDARY_DAYS else "LTCG-debt-Specified-MF (slab)"

    if tax_category in {"equity", "hybrid-equity-oriented"}:
        return "STCG-equity (20%)" if holding_days <= EQUITY_LTCG_BOUNDARY_DAYS else "LTCG-equity (12.5% over ₹1.25L)"

    if tax_category in {"non-equity-pre-Apr-2023",
                        "non-equity-pre-Apr-2023-no-indexation-post-23-Jul-2024"}:
        return "STCG-non-equity (slab)" if holding_days <= NONEQUITY_LTCG_BOUNDARY_DAYS else "LTCG-non-equity (12.5% no indexation)"

    return "unclassified"


# --------------------------------------------------------------------------
# Sub-portfolio aggregations (for portfolio-review)
# --------------------------------------------------------------------------

def value_by_sub_portfolio(
    txns: Iterable[dict],
    conn: sqlite3.Connection,
) -> dict[str, float]:
    """Total current value (₹) per sub-portfolio across all MF schemes in ledger."""
    txns_list = list(txns)
    cv = current_value_per_scheme(txns_list, conn)
    # Pick any txn for each scheme to look up sub_portfolio (it's per-scheme by convention).
    scheme_to_sub: dict[int, str] = {}
    for t in txns_list:
        scheme_to_sub.setdefault(t["scheme_code"], t["sub_portfolio"])
    out: dict[str, float] = defaultdict(float)
    for sc, info in cv.items():
        if info["current_value_inr"] is None:
            continue
        out[scheme_to_sub.get(sc, "unknown")] += info["current_value_inr"]
    return {k: round(v, 2) for k, v in out.items()}
