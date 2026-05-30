#!/usr/bin/env python3
"""
recurring_runner.py — Generate ledger entries for active SIPs and STPs.

Reads data/recurring.json, walks each active recurring entry, and appends one
ledger row (SIP) or two linked rows (STP) for every scheduled tranche between
its start_date and today (inclusive) that is not already in the ledger.

Idempotent: re-runs are safe. Each generated row carries the recurring's
sip_id or stp_id; the runner skips dates that already have a matching row.

Usage:
    python scripts/recurring_runner.py                # do it
    python scripts/recurring_runner.py --dry-run      # preview, don't write
    python scripts/recurring_runner.py --as-of 2026-06-15
                                                      # override "today" (testing)

Schema of data/recurring.json:

    {
      "sips": [
        {
          "sip_id": "sip-ppfas-monthly-5k",
          "destination_scheme_code": 122639,
          "destination_scheme_name": "Parag Parikh Flexi Cap Fund",
          "amount_inr": 5000,
          "frequency": "monthly",
          "day_of_month": 5,
          "start_date": "2026-06-05",
          "end_date": null,
          "sub_portfolio": "user",
          "status": "active"
        }
      ],
      "stps": [
        {
          "stp_id": "stp-bandhan-sd-to-franklin-flexi",
          "source_scheme_code": 108768,
          "source_scheme_name": "Bandhan Short Duration Fund",
          "source_tax_category": "specified-mf",
          "destination_scheme_code": 100520,
          "destination_scheme_name": "Franklin India Flexi Cap — Reg-G",
          "amount_inr_per_tranche": 25000,
          "frequency": "monthly",
          "day_of_month": 5,
          "start_date": "2026-06-05",
          "end_date": null,
          "stop_when_source_exhausted": true,
          "sub_portfolio": "father",
          "status": "active",
          "exit_load": null
        }
      ]
    }

`exit_load` is `{"days": int, "pct": float}` or null. If non-null, the runner
applies pct to the full tranche when the FIFO-oldest consumed lot was purchased
within `days` of the tranche date. Approximation: exit load in real AMCs is
per-lot; we apply the worst case to the whole tranche if any unit is in-window.

Exit codes: 0 success, 1 user error, 2 partial failure (some tranches couldn't
be generated; ledger left untouched)
"""

from __future__ import annotations

import argparse
import calendar
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.db import get_conn  # noqa: E402
from lib.transactions import (  # noqa: E402
    DEFAULT_LEDGER_PATH,
    DEFAULT_RECURRING_PATH,
    load_transactions,
    save_transactions,
    load_recurring,
    save_recurring,
    make_purchase,
    make_redemption,
    validate_transaction,
    get_nav_on_date,
    nearest_business_day_nav,
    units_per_scheme,
    consume_fifo,
)


def parse_iso(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def fmt_iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")


# --------------------------------------------------------------------------
# Date scheduling
# --------------------------------------------------------------------------

def scheduled_dates_monthly(
    start: date,
    end: date,
    day_of_month: int,
) -> list[date]:
    """
    Return the list of monthly scheduled dates between `start` and `end`
    (inclusive of both endpoints if they hit), each clamped to the last
    day of the month if day_of_month exceeds it.

    The FIRST scheduled date is start (regardless of day_of_month) — that's
    the convention for recurring registrations: "first tranche fires on
    the registration date itself, then on day_of_month each subsequent month."
    Subsequent dates are derived from the month after start.

    Wait — actually the convention we want is: the registration's start_date
    IS the first scheduled date (which the user supplies in canonical form).
    Subsequent dates: same day_of_month each subsequent month.
    """
    out: list[date] = []
    if start > end:
        return out
    out.append(start)
    # March forward by month, snapping to day_of_month (clamped).
    y, m = start.year, start.month
    while True:
        m += 1
        if m > 12:
            m = 1
            y += 1
        last_day = calendar.monthrange(y, m)[1]
        d = min(day_of_month, last_day)
        cand = date(y, m, d)
        if cand > end:
            break
        out.append(cand)
    return out


# --------------------------------------------------------------------------
# Idempotency
# --------------------------------------------------------------------------

def already_logged(txns: list[dict], recurring_id_field: str, recurring_id: str, txn_date: str) -> bool:
    for t in txns:
        if t.get(recurring_id_field) == recurring_id and t["date"] == txn_date:
            return True
    return False


# --------------------------------------------------------------------------
# NAV resolution
# --------------------------------------------------------------------------

def resolve_nav(conn, scheme_code: int, target_date: str) -> tuple[float, str] | None:
    nav = get_nav_on_date(scheme_code, target_date, conn)
    if nav is not None:
        return (nav, f"exact {target_date}")
    fwd = nearest_business_day_nav(scheme_code, target_date, conn, direction="forward", max_days=7)
    if fwd:
        return (fwd[1], f"forward-fallback {fwd[0]} (target {target_date})")
    bwd = nearest_business_day_nav(scheme_code, target_date, conn, direction="backward", max_days=7)
    if bwd:
        return (bwd[1], f"backward-fallback {bwd[0]} (target {target_date})")
    return None


# --------------------------------------------------------------------------
# SIP generation
# --------------------------------------------------------------------------

@dataclass
class GenerationResult:
    new_rows: list[dict]
    notes: list[str]
    failed: list[str]


def generate_sip_tranches(
    sip: dict,
    txns: list[dict],
    as_of: date,
    conn,
) -> GenerationResult:
    res = GenerationResult([], [], [])
    if sip.get("status") != "active":
        return res
    if sip.get("frequency", "monthly") != "monthly":
        res.notes.append(f"sip {sip['sip_id']}: unsupported frequency {sip.get('frequency')!r}; skipping")
        return res

    start = parse_iso(sip["start_date"])
    end_raw = sip.get("end_date")
    end = min(as_of, parse_iso(end_raw)) if end_raw else as_of
    dates = scheduled_dates_monthly(start, end, int(sip["day_of_month"]))

    pending = txns + res.new_rows  # for cumulative txn_id sequencing
    for d in dates:
        ds = fmt_iso(d)
        if already_logged(txns + res.new_rows, "sip_id", sip["sip_id"], ds):
            continue
        nav_result = resolve_nav(conn, sip["destination_scheme_code"], ds)
        if not nav_result:
            res.failed.append(f"SIP {sip['sip_id']}: no NAV near {ds}")
            continue
        nav, src = nav_result
        row = make_purchase(
            date_str=ds,
            scheme_code=sip["destination_scheme_code"],
            scheme_name=sip["destination_scheme_name"],
            amount_inr=float(sip["amount_inr"]),
            nav=nav,
            sub_portfolio=sip["sub_portfolio"],
            source="sip-runner",
            txns=pending,
            sip_id=sip["sip_id"],
            notes=f"SIP tranche [nav: {src}]",
        )
        errs = validate_transaction(row)
        if errs:
            res.failed.append(f"SIP {sip['sip_id']} {ds}: validation failed: {errs}")
            continue
        res.new_rows.append(row)
        pending = txns + res.new_rows
        res.notes.append(f"SIP {sip['sip_id']} {ds}: ₹{sip['amount_inr']:,.0f} → {row['units']} units @ ₹{nav:.4f}")
    return res


# --------------------------------------------------------------------------
# STP generation
# --------------------------------------------------------------------------

def _exit_load_for_tranche(
    stp: dict,
    consumed_lots: list[tuple[float, str, str]],
    sale_date: date,
    proceeds_pre_load: float,
) -> float:
    """
    Compute exit load applied to a tranche. Uses worst-case: if any consumed
    lot's purchase date is within `days`, apply pct to the entire tranche.
    """
    rule = stp.get("exit_load")
    if not rule:
        return 0.0
    days = int(rule["days"])
    pct = float(rule["pct"])
    for (_units, _tid, purchase_date_str) in consumed_lots:
        purchase_d = parse_iso(purchase_date_str)
        if (sale_date - purchase_d).days < days:
            return round(proceeds_pre_load * pct, 2)
    return 0.0


def generate_stp_tranches(
    stp: dict,
    txns: list[dict],
    as_of: date,
    conn,
) -> tuple[GenerationResult, str | None]:
    """
    Returns (result, new_status_or_None). new_status_or_None is non-None
    if the source corpus exhausted mid-walk and stop_when_source_exhausted
    is true — caller should write back the updated status to recurring.json.
    """
    res = GenerationResult([], [], [])
    new_status: str | None = None
    if stp.get("status") != "active":
        return (res, None)
    if stp.get("frequency", "monthly") != "monthly":
        res.notes.append(f"stp {stp['stp_id']}: unsupported frequency {stp.get('frequency')!r}; skipping")
        return (res, None)

    src_code = int(stp["source_scheme_code"])
    src_name = stp["source_scheme_name"]
    src_tax = stp["source_tax_category"]
    dst_code = int(stp["destination_scheme_code"])
    dst_name = stp["destination_scheme_name"]
    amount = float(stp["amount_inr_per_tranche"])
    # Optional override for the final scheduled tranche so plan_stp can absorb
    # the lump_inr/months rounding residual without leaving paisa stuck in the
    # parking source. None → use `amount` for every tranche.
    final_amount = stp.get("final_tranche_amount_inr")
    final_amount = float(final_amount) if final_amount is not None else None
    sub = stp["sub_portfolio"]
    stop_on_exhaust = bool(stp.get("stop_when_source_exhausted", True))

    start = parse_iso(stp["start_date"])
    end_raw = stp.get("end_date")
    end = min(as_of, parse_iso(end_raw)) if end_raw else as_of
    dates = scheduled_dates_monthly(start, end, int(stp["day_of_month"]))
    end_full = parse_iso(end_raw) if end_raw else None

    pending = txns + res.new_rows
    for d in dates:
        ds = fmt_iso(d)
        if already_logged(txns + res.new_rows, "stp_id", stp["stp_id"], ds):
            continue

        # Resolve NAVs for both legs.
        src_nav_result = resolve_nav(conn, src_code, ds)
        dst_nav_result = resolve_nav(conn, dst_code, ds)
        if not src_nav_result or not dst_nav_result:
            res.failed.append(f"STP {stp['stp_id']} {ds}: missing NAV for source or destination")
            continue
        src_nav, src_src = src_nav_result
        dst_nav, dst_src = dst_nav_result

        # Last scheduled tranche absorbs any rounding residual when an override
        # is provided. Match by date against the registry's end_date so a
        # bounded STP cleanly drains its parking source.
        tranche_amount = amount
        if final_amount is not None and end_full is not None and d == end_full:
            tranche_amount = final_amount

        # Determine units to sell from source = tranche_amount / src_nav.
        units_to_sell = round(tranche_amount / src_nav, 4)

        # Check source has enough units (live, including all prior pending rows).
        live_units = units_per_scheme(pending).get(src_code, 0.0)
        if units_to_sell > live_units + 1e-4:
            if stop_on_exhaust:
                # Optional: post a partial last tranche using whatever's left.
                if live_units > 1e-4:
                    units_to_sell = round(live_units, 4)
                    res.notes.append(f"STP {stp['stp_id']} {ds}: partial tranche — "
                                     f"only {units_to_sell} units left in source")
                else:
                    new_status = "ended-source-exhausted"
                    res.notes.append(f"STP {stp['stp_id']} {ds}: source exhausted; stopping STP")
                    break
            else:
                res.failed.append(
                    f"STP {stp['stp_id']} {ds}: source under-funded "
                    f"(needs {units_to_sell}, has {live_units:.4f})"
                )
                continue

        # Build redemption (sell) row first — its FIFO is computed against `pending`.
        try:
            sell_row = make_redemption(
                date_str=ds,
                scheme_code=src_code,
                scheme_name=src_name,
                units_to_sell=units_to_sell,
                nav=src_nav,
                sub_portfolio=sub,
                source="stp-runner",
                txns=pending,
                tax_category=src_tax,
                stp_id=stp["stp_id"],
                exit_load_inr=0.0,  # placeholder; recompute below using lots
                notes=f"STP sell leg [nav: {src_src}]",
                type_="redemption",
            )
        except ValueError as e:
            res.failed.append(f"STP {stp['stp_id']} {ds}: {e}")
            continue

        # Re-compute exit load using consumed lots; rebuild sell row with corrected proceeds.
        consumed = [(lot["units"], lot["source_txn_id"], lot["purchase_date"])
                    for lot in sell_row["fifo_lots_consumed"]]
        gross_proceeds = round(units_to_sell * src_nav, 2)
        exit_load = _exit_load_for_tranche(stp, consumed, d, gross_proceeds)
        if exit_load > 0:
            sell_row = make_redemption(
                date_str=ds,
                scheme_code=src_code,
                scheme_name=src_name,
                units_to_sell=units_to_sell,
                nav=src_nav,
                sub_portfolio=sub,
                source="stp-runner",
                txns=pending,
                tax_category=src_tax,
                stp_id=stp["stp_id"],
                exit_load_inr=exit_load,
                notes=f"STP sell leg [nav: {src_src}; exit-load {exit_load:.2f}]",
                type_="redemption",
            )

        # Now build buy row using NET proceeds (gross - exit_load).
        net_for_buy = round(gross_proceeds - exit_load, 2)
        # Update sell row's linked id later, after buy row's id is known.
        # For now insert sell row into pending so buy row's seq number doesn't collide.
        pending_with_sell = pending + [sell_row]
        buy_row = make_purchase(
            date_str=ds,
            scheme_code=dst_code,
            scheme_name=dst_name,
            amount_inr=net_for_buy,
            nav=dst_nav,
            sub_portfolio=sub,
            source="stp-runner",
            txns=pending_with_sell,
            stp_id=stp["stp_id"],
            linked_txn_id=sell_row["txn_id"],
            notes=f"STP buy leg [nav: {dst_src}]",
            type_="purchase",
        )
        # Backfill sell.linked_txn_id now that buy.txn_id is known.
        sell_row["linked_txn_id"] = buy_row["txn_id"]

        for r in (sell_row, buy_row):
            errs = validate_transaction(r)
            if errs:
                res.failed.append(f"STP {stp['stp_id']} {ds}: validation failed: {errs}")
                # Don't append either leg — keep them paired or not at all.
                break
        else:
            res.new_rows.append(sell_row)
            res.new_rows.append(buy_row)
            pending = txns + res.new_rows
            res.notes.append(
                f"STP {stp['stp_id']} {ds}: sold {units_to_sell} src @ ₹{src_nav:.4f} "
                f"(gain {sell_row['realised_gain_inr']:+.2f}, "
                f"{sell_row['gain_classification']}), "
                f"bought {buy_row['units']} dst @ ₹{dst_nav:.4f}"
            )

    return (res, new_status)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="Preview only; do not write")
    p.add_argument("--as-of", default=None, help="Override 'today' (YYYY-MM-DD)")
    p.add_argument("--ledger", default=str(DEFAULT_LEDGER_PATH))
    p.add_argument("--recurring", default=str(DEFAULT_RECURRING_PATH))
    args = p.parse_args()

    as_of = parse_iso(args.as_of) if args.as_of else date.today()
    txns = load_transactions(args.ledger)
    recurring = load_recurring(args.recurring)

    all_new: list[dict] = []
    notes: list[str] = []
    failed: list[str] = []
    status_updates: list[tuple[str, str]] = []  # (stp_id, new_status)

    with get_conn() as conn:
        for sip in recurring.get("sips", []):
            res = generate_sip_tranches(sip, txns + all_new, as_of, conn)
            all_new.extend(res.new_rows)
            notes.extend(res.notes)
            failed.extend(res.failed)
        for stp in recurring.get("stps", []):
            res, new_status = generate_stp_tranches(stp, txns + all_new, as_of, conn)
            all_new.extend(res.new_rows)
            notes.extend(res.notes)
            failed.extend(res.failed)
            if new_status:
                status_updates.append((stp["stp_id"], new_status))

    print(f"=== recurring_runner — as of {as_of} ===")
    if not notes and not failed:
        print("No new tranches to generate (everything up to date).")
    for n in notes:
        print(f"  • {n}")
    if failed:
        print()
        print("FAILURES:")
        for f in failed:
            print(f"  ✗ {f}")
        print(f"\nAborting due to {len(failed)} failure(s); ledger left untouched.")
        return 2
    if not all_new:
        return 0

    print(f"\n→ {len(all_new)} new ledger row(s) ready to append.")
    if args.dry_run:
        print("(dry-run; not writing)")
        return 0

    txns.extend(all_new)
    save_transactions(txns, args.ledger)
    print(f"Wrote {len(all_new)} rows to {args.ledger}.")

    # Persist STP status changes.
    if status_updates:
        for stp in recurring.get("stps", []):
            for stp_id, new_status in status_updates:
                if stp["stp_id"] == stp_id:
                    stp["status"] = new_status
        save_recurring(recurring, args.recurring)
        print(f"Updated STP status: {status_updates}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
