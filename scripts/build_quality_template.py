#!/usr/bin/env python3
"""
build_quality_template.py — Bootstrap or refresh fund_quality.json
                            from portfolio.md.

For each scheme_code in portfolio.md not already in fund_quality.json, adds an
empty template entry (all fields null, plus a name_ref for editor convenience).
**Existing entries are not modified** — your filled-in TER, manager, AUM data
is preserved across re-runs.

Run this:
- After initial setup, to generate the starter template
- After adding new holdings to portfolio.md
- Whenever fund-allocate suggests a candidate you want to research and add

After running, open fund_quality.json and fill in:
  ter            — Total Expense Ratio (%, e.g. 0.62)
  manager_name   — Lead manager's name (or 'A / B' for co-managed)
  manager_since  — ISO date the lead manager took over (YYYY-MM-DD)
  aum_crore      — Latest AUM in ₹ crores (from AMC factsheet)
  last_verified  — Today's ISO date when you check the fund
  notes          — Any free-text observation worth keeping

Source for these fields: the AMC's official monthly factsheet, available on
the AMC website. Search 'AMC NAME factsheet MONTH YEAR' to find the latest.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

# Reuse the portfolio extractor from fetch_nav_history.py — same logic for
# pulling (scheme_code, first_purchase_date) tuples out of portfolio.md tables.
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from .lib.db import get_conn
except ImportError:
    from lib.db import get_conn  # type: ignore

from fetch_nav_history import extract_holdings_from_portfolio  # type: ignore


DEFAULT_PORTFOLIO_PATH = Path(__file__).resolve().parents[1] / "portfolio.md"
DEFAULT_JSON_PATH = Path(__file__).resolve().parents[1] / "fund_quality.json"


EMPTY_TEMPLATE_FIELDS = {
    "ter": None,
    "manager_name": None,
    "manager_since": None,
    "aum_crore": None,
    "last_verified": None,
    "notes": None,
}


def _make_template_entry(scheme_code: int, db_path=None) -> dict:
    """Build an empty template entry for one scheme; embeds the canonical name as name_ref."""
    with get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT scheme_name FROM schemes WHERE scheme_code = ?", (scheme_code,)
        ).fetchone()
    name_ref = row["scheme_name"] if row else "(scheme not yet seen by fetch_nav.py)"
    return {"name_ref": name_ref, **EMPTY_TEMPLATE_FIELDS}


def _empty_root() -> dict:
    """Return the root JSON shape for a freshly-created fund_quality.json."""
    return {
        "_meta": {
            "schema_version": "1.0",
            "created": date.today().isoformat(),
            "documentation": (
                "User-maintained fund quality overlay. One entry per scheme_code "
                "with TER, manager_name, manager_since, aum_crore, last_verified, "
                "notes. Source: AMC monthly factsheets. See README_phase3.md."
            ),
        },
        "schemes": {},
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO_PATH,
                    help="portfolio.md path (default: ../portfolio.md from script dir)")
    ap.add_argument("--output", type=Path, default=DEFAULT_JSON_PATH,
                    help="fund_quality.json path (default: ../fund_quality.json)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not args.portfolio.exists():
        print(f"ERROR: portfolio.md not found at {args.portfolio}", file=sys.stderr)
        return 1

    portfolio_text = args.portfolio.read_text(encoding="utf-8")
    holdings = extract_holdings_from_portfolio(portfolio_text)
    if not holdings:
        print("ERROR: no resolved (scheme_code, first_purchase_date) pairs found "
              "in portfolio.md. Run scripts/resolve_schemes.py first.", file=sys.stderr)
        return 1

    scheme_codes = sorted({code for code, _ in holdings})

    # Load existing JSON or start fresh — preserve prior entries verbatim.
    if args.output.exists():
        try:
            existing = json.loads(args.output.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"ERROR: existing {args.output.name} is malformed JSON: {e}",
                  file=sys.stderr)
            print("Fix or delete the file before re-running.", file=sys.stderr)
            return 1
    else:
        existing = _empty_root()

    schemes_block = existing.setdefault("schemes", {})

    added = 0
    skipped = 0
    for code in scheme_codes:
        key = str(code)
        if key in schemes_block and schemes_block[key]:
            skipped += 1
            continue
        schemes_block[key] = _make_template_entry(code)
        added += 1

    # Bump _meta.last_updated
    if "_meta" in existing:
        existing["_meta"]["last_updated"] = date.today().isoformat()

    args.output.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if not args.quiet:
        print(f"Wrote {args.output}")
        print(f"  Added:   {added} new template entry/entries")
        print(f"  Skipped: {skipped} existing entry/entries (preserved verbatim)")
        if added:
            print()
            print("Next steps:")
            print(f"  1. Open {args.output} in your editor")
            print(f"  2. For each new entry, fill in: ter, manager_name, manager_since,")
            print(f"     aum_crore, last_verified")
            print(f"  3. Source: the AMC's latest monthly factsheet PDF")
            print(f"     (search 'AMC NAME factsheet MONTH YEAR')")

    return 0


if __name__ == "__main__":
    sys.exit(main())
