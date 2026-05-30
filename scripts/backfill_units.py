#!/usr/bin/env python3
"""
backfill_units.py — One-time tool to seed data/transactions.json with the
historical purchase rows that produce today's holdings.

Workflow:
    1) Generate a template by parsing portfolio.md:

           python scripts/backfill_units.py --extract-template \\
               > data/backfill_input.json

       The template lists every MF holding from portfolio.md with
       `purchase_date` left as the existing first-purchase month
       (which is approximate). You (or a grill conversation) edit the
       file to specify exact dates and split tranches if needed.

    2) Dry-run to preview what would be appended:

           python scripts/backfill_units.py --apply data/backfill_input.json --dry-run

       NAVs are looked up from market.db. If any NAV is missing, the
       script automatically calls fetch_scheme_history for the required
       schemes and re-tries once.

    3) Apply:

           python scripts/backfill_units.py --apply data/backfill_input.json

       Each entry is appended as a `purchase` row with source='backfill'.
       Idempotency: re-running with the same input skips rows whose
       (date, scheme_code, type='purchase', source='backfill') tuple is
       already in the ledger.

Schema of the input file (`data/backfill_input.json`):

    {
      "schemes": [
        {
          "scheme_code": 120841,
          "scheme_name": "Quant Mid Cap Fund — Direct G",
          "purchase_date": "2025-03-15",
          "amount_inr": 43000,
          "sub_portfolio": "user",
          "notes": ""
        },
        ...
      ]
    }

Multi-tranche purchases: include multiple entries for the same scheme_code
with different purchase_dates and amounts.

Exit codes: 0 success, 1 user error, 2 NAV resolution failed
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.db import get_conn  # noqa: E402
from lib.transactions import (  # noqa: E402
    VALID_SUB_PORTFOLIOS,
    DEFAULT_LEDGER_PATH,
    load_transactions,
    save_transactions,
    make_purchase,
    validate_transaction,
    get_nav_on_date,
    nearest_business_day_nav,
)

ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO_PATH = ROOT / "portfolio.md"


# --------------------------------------------------------------------------
# Template extraction from portfolio.md
# --------------------------------------------------------------------------

def parse_holdings_from_portfolio(text: str) -> list[dict]:
    """
    Walk portfolio.md tables; emit one entry per MF holding.

    Recognises tables with these columns: 'Scheme', 'scheme_code', 'Capital'
    (or 'Capital invested'), 'First purchase', 'Sub-port' (or 'Sub-portfolio').

    Returns a list of dicts:
        {scheme_code, scheme_name, purchase_date, amount_inr, sub_portfolio, notes}
    """
    out: list[dict] = []
    in_table = False
    headers: list[str] = []
    indices: dict[str, int] = {}

    def _index_for(headers_lc: list[str], names: tuple[str, ...]) -> int | None:
        for i, h in enumerate(headers_lc):
            if h in names:
                return i
        return None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("|") and "---" in line:
            in_table = True
            continue
        if in_table and not line.startswith("|"):
            in_table = False
            headers = []
            indices = {}
            continue
        if line.startswith("|") and not in_table:
            headers = [c.strip() for c in line.strip("|").split("|")]
            headers_lc = [h.lower() for h in headers]
            indices = {
                "scheme": _index_for(headers_lc, ("scheme", "instrument")),
                "scheme_code": _index_for(headers_lc, ("scheme_code",)),
                "capital": _index_for(headers_lc, ("capital", "capital invested", "cost basis")),
                "first_purchase": _index_for(headers_lc, ("first purchase", "first_purchase")),
                "sub": _index_for(headers_lc, ("sub-port", "sub-portfolio")),
            }
            continue

        if (in_table and line.startswith("|")
                and indices.get("scheme_code") is not None
                and indices.get("capital") is not None):
            cells = [c.strip() for c in line.strip("|").split("|")]
            try:
                code_cell = cells[indices["scheme_code"]]
            except IndexError:
                continue
            if not code_cell or code_cell in ("UNRESOLVED", "—", "-", "N/A"):
                continue
            try:
                scheme_code = int(code_cell)
            except ValueError:
                continue

            scheme_name = cells[indices["scheme"]] if indices["scheme"] is not None else f"<scheme {scheme_code}>"
            cap_str = cells[indices["capital"]] if indices["capital"] is not None else ""
            amount = _parse_inr(cap_str)
            if amount is None or amount <= 0:
                continue

            purchase_str = (cells[indices["first_purchase"]]
                            if indices.get("first_purchase") is not None else "")
            purchase_date = _normalise_purchase_date(purchase_str)

            sub = (cells[indices["sub"]] if indices.get("sub") is not None else "user").strip()
            if sub not in VALID_SUB_PORTFOLIOS:
                sub = "user"

            out.append({
                "scheme_code": scheme_code,
                "scheme_name": scheme_name,
                "purchase_date": purchase_date,
                "amount_inr": amount,
                "sub_portfolio": sub,
                "notes": "",
            })

    return out


def _parse_inr(s: str) -> float | None:
    """Parse '₹43,000' or '43,000' or '43000' → 43000.0."""
    s = s.replace("₹", "").replace(",", "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _normalise_purchase_date(s: str) -> str:
    """Convert '2025-03', '2025-03-15', or 'Mar 2025' to YYYY-MM-DD.
    Month-only inputs default to the 15th (mid-month proxy)."""
    s = s.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    if re.match(r"^\d{4}-\d{2}$", s):
        return f"{s}-15"
    months = {m: i for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun",
         "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
    m = re.match(r"^([A-Za-z]{3})\s+(\d{4})$", s)
    if m:
        mn = months.get(m.group(1).lower())
        if mn:
            return f"{m.group(2)}-{mn:02d}-15"
    return ""


# --------------------------------------------------------------------------
# NAV resolution with auto-backfill
# --------------------------------------------------------------------------

def ensure_nav_for_scheme(scheme_code: int, target_date: str) -> tuple[float, str] | None:
    """
    Try to find a NAV in market.db for scheme_code on/around target_date.
    If missing, invoke fetch_scheme_history once to backfill, then retry.
    Returns (nav, source_note) or None if even after backfill no NAV is found.
    """
    with get_conn() as conn:
        nav = get_nav_on_date(scheme_code, target_date, conn)
        if nav is not None:
            return (nav, f"market.db exact {target_date}")
        fwd = nearest_business_day_nav(scheme_code, target_date, conn,
                                       direction="forward", max_days=7)
        if fwd:
            return (fwd[1], f"market.db forward-fallback {fwd[0]} (target {target_date})")
        bwd = nearest_business_day_nav(scheme_code, target_date, conn,
                                       direction="backward", max_days=7)
        if bwd:
            return (bwd[1], f"market.db backward-fallback {bwd[0]} (target {target_date})")

    # Not in DB → try the backfill path.
    print(f"  NAV missing for {scheme_code} near {target_date}; invoking fetch_nav_history...",
          file=sys.stderr)
    try:
        from fetch_nav_history import fetch_scheme_history, payload_to_records
        from lib.db import get_conn as _gc
        payload = fetch_scheme_history(scheme_code, quiet=True)
        if payload:
            records = payload_to_records(payload, scheme_code, from_date=None)
            with _gc() as conn:
                conn.executemany(
                    "INSERT OR IGNORE INTO nav_history (scheme_code, nav_date, nav) VALUES (?, ?, ?)",
                    [(r.scheme_code, r.nav_date, r.nav) for r in records],
                )
    except Exception as e:
        print(f"  fetch_scheme_history failed: {e}", file=sys.stderr)
        return None

    # Retry.
    with get_conn() as conn:
        nav = get_nav_on_date(scheme_code, target_date, conn)
        if nav is not None:
            return (nav, f"market.db (post-backfill) exact {target_date}")
        fwd = nearest_business_day_nav(scheme_code, target_date, conn,
                                       direction="forward", max_days=7)
        if fwd:
            return (fwd[1], f"market.db (post-backfill) forward {fwd[0]}")
        bwd = nearest_business_day_nav(scheme_code, target_date, conn,
                                       direction="backward", max_days=14)
        if bwd:
            return (bwd[1], f"market.db (post-backfill) backward {bwd[0]}")
    return None


# --------------------------------------------------------------------------
# Apply
# --------------------------------------------------------------------------

def already_logged(txns: list[dict], entry: dict) -> bool:
    """Idempotency check: same date + scheme + amount + source='backfill'."""
    for t in txns:
        if (t.get("source") == "backfill"
                and t["scheme_code"] == entry["scheme_code"]
                and t["date"] == entry["purchase_date"]
                and abs(t["amount_inr"] - entry["amount_inr"]) < 0.01
                and t["type"] == "purchase"):
            return True
    return False


def apply_config(config_path: Path, dry_run: bool) -> int:
    config = json.loads(config_path.read_text())
    entries = config.get("schemes", [])
    if not entries:
        print("Empty schemes list in config; nothing to do.", file=sys.stderr)
        return 1

    txns = load_transactions()
    appended = 0
    skipped_existing = 0
    failed = 0
    pending: list[dict] = []

    for entry in entries:
        # Validate.
        for k in ("scheme_code", "scheme_name", "purchase_date", "amount_inr", "sub_portfolio"):
            if k not in entry:
                print(f"ERROR: missing key {k!r} in entry: {entry}", file=sys.stderr)
                return 1
        if entry["sub_portfolio"] not in VALID_SUB_PORTFOLIOS:
            print(f"ERROR: invalid sub_portfolio {entry['sub_portfolio']!r}", file=sys.stderr)
            return 1
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", entry["purchase_date"]):
            print(f"ERROR: purchase_date must be YYYY-MM-DD, got {entry['purchase_date']!r}", file=sys.stderr)
            return 1

        if already_logged(txns, entry):
            print(f"SKIP (already in ledger): {entry['scheme_code']} on {entry['purchase_date']}")
            skipped_existing += 1
            continue

        nav_result = ensure_nav_for_scheme(entry["scheme_code"], entry["purchase_date"])
        if nav_result is None:
            print(f"FAIL: no NAV for scheme {entry['scheme_code']} near {entry['purchase_date']}",
                  file=sys.stderr)
            failed += 1
            continue
        nav, src = nav_result

        txn = make_purchase(
            date_str=entry["purchase_date"],
            scheme_code=entry["scheme_code"],
            scheme_name=entry["scheme_name"],
            amount_inr=entry["amount_inr"],
            nav=nav,
            sub_portfolio=entry["sub_portfolio"],
            source="backfill",
            txns=txns + pending,
            notes=(entry.get("notes", "") + f" [nav: {src}]").strip(),
        )
        errs = validate_transaction(txn)
        if errs:
            print(f"VALIDATION FAILED for {entry['scheme_code']} on {entry['purchase_date']}: {errs}",
                  file=sys.stderr)
            failed += 1
            continue

        pending.append(txn)
        print(f"  → {txn['txn_id']}: {entry['scheme_name']}")
        print(f"      amount: ₹{entry['amount_inr']:,.2f}  nav: ₹{nav:.4f}  units: {txn['units']}")
        print(f"      source: {src}")
        appended += 1

    print()
    print(f"Plan: {appended} new, {skipped_existing} already-logged, {failed} failed.")

    if failed:
        print("Aborting (some entries failed). Fix errors and re-run.", file=sys.stderr)
        return 2
    if dry_run:
        print("(dry-run; no changes written)")
        return 0
    if not pending:
        print("Nothing to write.")
        return 0

    txns.extend(pending)
    save_transactions(txns)
    print(f"Wrote {len(pending)} new rows to {DEFAULT_LEDGER_PATH}.")
    return 0


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--extract-template", action="store_true",
                   help="Parse portfolio.md, emit a JSON template to stdout")
    g.add_argument("--apply", metavar="CONFIG", help="Apply a backfill config")
    p.add_argument("--dry-run", action="store_true", help="With --apply: don't write")
    p.add_argument("--portfolio", default=str(PORTFOLIO_PATH))
    args = p.parse_args()

    if args.extract_template:
        text = Path(args.portfolio).read_text()
        holdings = parse_holdings_from_portfolio(text)
        print(json.dumps({"schemes": holdings}, indent=2, ensure_ascii=False))
        return 0

    if args.apply:
        return apply_config(Path(args.apply), args.dry_run)

    return 1


if __name__ == "__main__":
    sys.exit(main())
