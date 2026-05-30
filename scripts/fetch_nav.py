#!/usr/bin/env python3
"""
fetch_nav.py — Download and parse AMFI's NAVAll.txt daily NAV file.

Source: https://www.amfiindia.com/spages/NAVAll.txt
Updated: daily after market close (~10pm IST on business days)
Format: pipe-delimited (semicolons, despite the .txt extension), with category and AMC
        sections as plain-text headers between record blocks.

Usage:
    python fetch_nav.py                    # fetch live and store to data/market.db
    python fetch_nav.py --dry-run          # parse only, don't write to DB
    python fetch_nav.py --from-file PATH   # parse a local file (for testing)
    python fetch_nav.py --quiet            # suppress per-record progress output

Exits 0 on success, non-zero on failure. Writes a row to fetch_log on every run.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Allow running as both a module and a script.
try:
    from .lib.db import get_conn, log_fetch
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lib.db import get_conn, log_fetch  # type: ignore

NAV_URL = "https://www.amfiindia.com/spages/NAVAll.txt"
SOURCE_NAME = "amfi_nav"

# Header line we expect at the top of NAVAll.txt
EXPECTED_HEADER = "Scheme Code"


@dataclass
class SchemeRecord:
    scheme_code: int
    isin_growth: str | None
    isin_div_reinv: str | None
    scheme_name: str
    nav: float
    nav_date: str  # ISO YYYY-MM-DD
    amc: str
    category: str
    plan: str | None  # 'Direct' / 'Regular' / None
    option_type: str | None  # 'Growth' / 'IDCW' / 'Reinvest' / None


def _parse_date(raw: str) -> str:
    """Parse AMFI's DD-MMM-YYYY format (e.g. '06-May-2026') into ISO YYYY-MM-DD."""
    return datetime.strptime(raw.strip(), "%d-%b-%Y").strftime("%Y-%m-%d")


def _classify_plan(scheme_name: str) -> str | None:
    """
    Detect Direct vs Regular from the scheme name.

    AMFI conventions vary by AMC, but most modern funds explicitly include 'Direct'
    or '(D)' / 'DIR' for Direct, and 'Regular' / '(R)' / 'REG' for Regular.
    Older/legacy schemes may not specify; return None in that case rather than guess.
    """
    upper = scheme_name.upper()
    has_direct = bool(re.search(r"\bDIRECT\b|\bDIR\b|\(D\)", upper))
    has_regular = bool(re.search(r"\bREGULAR\b|\bREG\b|\(R\)", upper))
    if has_direct and not has_regular:
        return "Direct"
    if has_regular and not has_direct:
        return "Regular"
    return None  # ambiguous or pre-2013 unified plan


def _classify_option(scheme_name: str) -> str | None:
    """Detect Growth / IDCW (formerly Dividend) / Reinvestment options from name."""
    upper = scheme_name.upper()
    if "GROWTH" in upper or upper.endswith("- G") or upper.endswith(" G"):
        return "Growth"
    if "REINVEST" in upper or "REINV" in upper:
        return "Reinvest"
    if "IDCW" in upper or "DIVIDEND" in upper or "DIV" in upper or "PAYOUT" in upper:
        return "IDCW"
    return None


def _is_category_header(line: str) -> bool:
    """
    Category headers in NAVAll.txt look like:
        'Open Ended Schemes(Equity Scheme - Large Cap Fund)'
        'Close Ended Schemes(Debt Scheme - Fixed Maturity Plans)'
    Always include parentheses with the category descriptor inside.
    """
    return ("Schemes(" in line) and (")" in line) and (";" not in line)


def _is_amc_header(line: str, current_category: str | None) -> bool:
    """
    AMC headers are non-empty lines without semicolons that aren't category headers.
    They typically end with 'Mutual Fund' but a few don't, so we use a structural test.
    """
    if not line or ";" in line or _is_category_header(line):
        return False
    return current_category is not None  # AMC headers always come after a category


def parse_nav_file(content: str) -> list[SchemeRecord]:
    """
    Parse the AMFI NAVAll.txt content into structured records.

    Format observed:
        - First non-blank line is the column header
        - Then alternating sections of:
            'Open/Close Ended Schemes(<category>)'  ← category header
            '<AMC name>'                             ← AMC header (often 'X Mutual Fund')
            'code;isin_g;isin_d;name;nav;date'       ← scheme records
            'code;...'
            ...
        - Records use ';' as delimiter; '-' represents NULL in ISIN fields
        - Date format: DD-MMM-YYYY
    """
    records: list[SchemeRecord] = []
    current_category: str | None = None
    current_amc: str | None = None
    header_seen = False
    skipped_lines = 0

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if not header_seen:
            if line.startswith(EXPECTED_HEADER):
                header_seen = True
                continue
            # Tolerate a few non-empty lines before the header (some mirrors prepend BOM/notes)
            if skipped_lines > 5:
                raise ValueError(
                    f"Could not find expected header starting with '{EXPECTED_HEADER}' "
                    f"within first 5 non-empty lines. Got: {line!r}"
                )
            skipped_lines += 1
            continue

        if _is_category_header(line):
            # Extract everything between '(' and the last ')'
            match = re.search(r"\(([^()]+)\)\s*$", line)
            current_category = match.group(1).strip() if match else line
            current_amc = None
            continue

        if ";" not in line:
            # AMC header (or stray noise after categories)
            if current_category is not None:
                current_amc = line
            continue

        # Scheme record
        parts = line.split(";")
        if len(parts) < 6:
            continue  # malformed; skip silently — don't fail the whole fetch
        try:
            code_str, isin_g, isin_d, name, nav_str, date_str = (p.strip() for p in parts[:6])
            scheme_code = int(code_str)
            nav_value = float(nav_str)
            nav_date = _parse_date(date_str)
        except (ValueError, IndexError):
            continue  # malformed numeric/date; skip

        if current_amc is None or current_category is None:
            continue  # record outside any AMC/category section; skip

        records.append(
            SchemeRecord(
                scheme_code=scheme_code,
                isin_growth=isin_g if isin_g and isin_g != "-" else None,
                isin_div_reinv=isin_d if isin_d and isin_d != "-" else None,
                scheme_name=name,
                nav=nav_value,
                nav_date=nav_date,
                amc=current_amc,
                category=current_category,
                plan=_classify_plan(name),
                option_type=_classify_option(name),
            )
        )

    return records


def store_records(
    records: list[SchemeRecord],
    db_path: Path | str | None = None,
) -> tuple[int, int]:
    """
    Persist parsed records to SQLite.
    Returns (nav_rows_inserted, scheme_rows_upserted).

    db_path defaults to lib.db.DEFAULT_DB_PATH at call time (resolved by get_conn).
    """
    nav_inserted = 0
    schemes_upserted = 0
    today_iso = datetime.now().strftime("%Y-%m-%d")

    with get_conn(db_path) as conn:
        for r in records:
            # NAV history: append-only via INSERT OR IGNORE (PK is scheme_code+date)
            cur = conn.execute(
                "INSERT OR IGNORE INTO nav_history (scheme_code, nav_date, nav) "
                "VALUES (?, ?, ?)",
                (r.scheme_code, r.nav_date, r.nav),
            )
            if cur.rowcount > 0:
                nav_inserted += 1

            # Schemes table: upsert; preserve first_seen, advance last_seen
            existing = conn.execute(
                "SELECT first_seen FROM schemes WHERE scheme_code = ?",
                (r.scheme_code,),
            ).fetchone()
            first_seen = existing["first_seen"] if existing else today_iso

            conn.execute(
                """
                INSERT INTO schemes (
                    scheme_code, isin_growth, isin_div_reinv, scheme_name, amc,
                    category, plan, option_type, first_seen, last_seen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(scheme_code) DO UPDATE SET
                    isin_growth    = excluded.isin_growth,
                    isin_div_reinv = excluded.isin_div_reinv,
                    scheme_name    = excluded.scheme_name,
                    amc            = excluded.amc,
                    category       = excluded.category,
                    plan           = excluded.plan,
                    option_type    = excluded.option_type,
                    last_seen      = excluded.last_seen
                """,
                (
                    r.scheme_code,
                    r.isin_growth,
                    r.isin_div_reinv,
                    r.scheme_name,
                    r.amc,
                    r.category,
                    r.plan,
                    r.option_type,
                    first_seen,
                    today_iso,
                ),
            )
            schemes_upserted += 1

    return nav_inserted, schemes_upserted


def fetch_amfi_text(timeout: int = 30) -> str:
    """Download NAVAll.txt with a sensible UA and timeout."""
    req = urllib.request.Request(
        NAV_URL,
        headers={
            "User-Agent": "finance-app/1.0 (personal portfolio tool)",
            "Accept": "text/plain",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="parse only; don't write to DB")
    ap.add_argument("--from-file", type=Path, help="parse a local file instead of fetching")
    ap.add_argument("--quiet", action="store_true", help="reduce output verbosity")
    args = ap.parse_args()

    try:
        if args.from_file:
            content = args.from_file.read_text(encoding="utf-8", errors="replace")
            source_label = f"file:{args.from_file.name}"
        else:
            if not args.quiet:
                print(f"Fetching {NAV_URL} ...")
            content = fetch_amfi_text()
            source_label = NAV_URL

        if not args.quiet:
            print(f"Parsing {len(content):,} bytes from {source_label}")

        records = parse_nav_file(content)

        if not records:
            log_fetch(SOURCE_NAME, "failed", 0, "no records parsed")
            print("ERROR: No records parsed. File format may have changed.", file=sys.stderr)
            return 2

        if not args.quiet:
            print(f"Parsed {len(records):,} scheme records")
            unique_amcs = len({r.amc for r in records})
            unique_categories = len({r.category for r in records})
            print(f"  AMCs: {unique_amcs}, Categories: {unique_categories}")

        if args.dry_run:
            log_fetch(SOURCE_NAME, "success", len(records), "dry-run; not stored")
            print("Dry run complete; nothing written.")
            return 0

        nav_inserted, schemes_upserted = store_records(records)
        log_fetch(SOURCE_NAME, "success", len(records))

        if not args.quiet:
            print(f"Stored: {nav_inserted:,} new NAV rows, {schemes_upserted:,} schemes upserted")
        return 0

    except urllib.error.URLError as e:
        log_fetch(SOURCE_NAME, "failed", 0, f"network error: {e}")
        print(f"ERROR: Could not reach AMFI: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        log_fetch(SOURCE_NAME, "failed", 0, str(e))
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
