#!/usr/bin/env python3
"""
fetch_nav_history.py — Backfill historical NAVs for portfolio holdings.

Source: mfapi.in (community-maintained AMFI mirror, stable JSON API).
Endpoint: https://api.mfapi.in/mf/<scheme_code>

Why this source over AMFI direct:
    - mfapi.in exposes AMFI data via a stable JSON API (one GET per scheme;
      returns full available history).
    - AMFI's portal historical endpoint is HTML-form based with parameters
      that vary across access patterns; reliable scraping requires iteration.
    - mfapi.in has been stable for years; used by many similar portfolio tools.

Trade-off acknowledged: third-party dependency.
    The daily fetcher (fetch_nav.py) uses AMFI direct (NAVAll.txt), so
    forward-looking refresh isn't dependent on mfapi.in. Only this one-time
    backfill is. After this runs, history is persisted locally in market.db
    and survives whatever happens to mfapi.in.

If mfapi.in becomes unavailable, fallback options:
    1. Run fetch_nav.py daily; history accumulates forward.
    2. Manually fetch AMFI portal historical CSV and use --from-file mode.
    3. Switch to a different mirror (mftool, rapidapi, etc.).

Usage:
    python fetch_nav_history.py
        # Read portfolio.md, find resolved (scheme_code, first_purchase_date)
        # pairs, fetch history from purchase to today for each.

    python fetch_nav_history.py --scheme-code 122639 --from-date 2024-01-01
        # Backfill one specific scheme over a custom range.

    python fetch_nav_history.py --codes-file data/candidate_universe.txt
        # Backfill full available history for every scheme code listed in the
        # file (one per line; '#' starts a comment; blank lines ignored). Use
        # this to seed the candidate universe for fund-allocate, not just held
        # positions.

    python fetch_nav_history.py --dry-run
        # Parse and report; don't write to DB.

    python fetch_nav_history.py --from-file response.json
        # Skip HTTP; parse a saved mfapi.in JSON response (testing/recovery).

Exit codes: 0 success, 1 input error, 2 partial failure, 3 network error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# Reuse helpers from fetch_nav.py and the shared db module
try:
    from .lib.db import log_fetch
    from .fetch_nav import (
        SchemeRecord,
        store_records,
        _classify_option,
        _classify_plan,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lib.db import log_fetch  # type: ignore
    from fetch_nav import (  # type: ignore
        SchemeRecord,
        store_records,
        _classify_option,
        _classify_plan,
    )


MFAPI_URL_TEMPLATE = "https://api.mfapi.in/mf/{scheme_code}"
SOURCE_NAME = "mfapi_history"
PACING_SECONDS = 1.5  # between requests; mfapi.in is responsive
REQUEST_TIMEOUT = 30  # per-request timeout
RATE_LIMIT_BACKOFF = 30  # seconds before retry on HTTP 429


def parse_mfapi_date(date_str: str) -> str:
    """Convert mfapi.in's DD-MM-YYYY format to ISO YYYY-MM-DD."""
    return datetime.strptime(date_str.strip(), "%d-%m-%Y").strftime("%Y-%m-%d")


def _normalize_purchase_date(s: str) -> str | None:
    """
    Convert YYYY-MM-DD or YYYY-MM (from portfolio.md) to ISO YYYY-MM-DD.

    YYYY-MM defaults to the first of the month. This is a deliberate slight
    over-fetch — purchasing on, say, 2026-04-15 with this normalisation gives
    us NAV history from 2026-04-01, which is fine: a few extra days of NAV
    data has zero downside and lets us verify NAV at purchase date precisely
    later if needed.

    Returns None if the input doesn't match either format.
    """
    s = s.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    if re.match(r"^\d{4}-\d{2}$", s):
        return f"{s}-01"
    return None


def fetch_scheme_history(scheme_code: int, quiet: bool = False) -> dict | None:
    """
    Fetch full available NAV history for a scheme from mfapi.in.

    Returns the parsed JSON dict on success, or None on failure (network error,
    bad JSON, non-SUCCESS status). Retries once on HTTP 429 (rate limit).
    """
    url = MFAPI_URL_TEMPLATE.format(scheme_code=scheme_code)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "finance-app/1.0 (personal portfolio tool)",
            "Accept": "application/json",
        },
    )

    def _do_request() -> dict | None:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))

    try:
        return _do_request()
    except urllib.error.HTTPError as e:
        if e.code == 429:
            if not quiet:
                print(f"    rate-limited; backing off {RATE_LIMIT_BACKOFF}s and retrying...",
                      file=sys.stderr)
            time.sleep(RATE_LIMIT_BACKOFF)
            try:
                return _do_request()
            except Exception as e2:
                if not quiet:
                    print(f"    retry failed: {e2}", file=sys.stderr)
                return None
        if not quiet:
            print(f"    HTTP {e.code}: {e.reason}", file=sys.stderr)
        return None
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        if not quiet:
            print(f"    error: {e}", file=sys.stderr)
        return None


def payload_to_records(
    payload: dict | None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[SchemeRecord]:
    """
    Convert mfapi.in JSON into a list of SchemeRecord, optionally filtered by date.

    Expected payload shape:
        {"meta": {"fund_house": str, "scheme_category": str, "scheme_code": int,
                  "scheme_name": str, "scheme_type": str},
         "data": [{"date": "DD-MM-YYYY", "nav": "<float as string>"}, ...],
         "status": "SUCCESS"}

    from_date and to_date are inclusive ISO YYYY-MM-DD bounds; either or both
    can be None (no bound on that side).
    """
    if not payload or payload.get("status") != "SUCCESS":
        return []

    meta = payload.get("meta") or {}
    data = payload.get("data") or []

    scheme_code = meta.get("scheme_code")
    scheme_name = (meta.get("scheme_name") or "").strip()
    amc = (meta.get("fund_house") or "").strip()
    category = (meta.get("scheme_category") or "").strip()

    if not scheme_code or not scheme_name:
        return []

    plan = _classify_plan(scheme_name)
    option_type = _classify_option(scheme_name)

    records: list[SchemeRecord] = []
    for entry in data:
        try:
            iso_date = parse_mfapi_date(entry["date"])
            nav_value = float(entry["nav"])
        except (KeyError, ValueError, TypeError):
            continue  # skip malformed entries silently

        if from_date and iso_date < from_date:
            continue
        if to_date and iso_date > to_date:
            continue

        records.append(SchemeRecord(
            scheme_code=int(scheme_code),
            isin_growth=None,        # mfapi.in doesn't expose ISIN
            isin_div_reinv=None,
            scheme_name=scheme_name,
            nav=nav_value,
            nav_date=iso_date,
            amc=amc,
            category=category,
            plan=plan,
            option_type=option_type,
        ))

    return records


def parse_codes_file(text: str) -> list[int]:
    """
    Parse a candidate-universe file: one scheme code per line, '#' starts a comment,
    blank lines ignored. Inline comments after a code (e.g. '120716  # UTI Nifty 50')
    are stripped. Duplicate codes are de-duplicated, preserving first occurrence.
    """
    seen: set[int] = set()
    codes: list[int] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        try:
            code = int(line)
        except ValueError:
            continue  # silently skip malformed lines
        if code in seen:
            continue
        seen.add(code)
        codes.append(code)
    return codes


def extract_holdings_from_portfolio(portfolio_text: str) -> list[tuple[int, str]]:
    """
    Walk portfolio.md table rows; extract (scheme_code, first_purchase_date) pairs.

    Looks for tables with both a 'scheme_code' column and a 'First purchase'
    (or similar) column. Skips rows where scheme_code is UNRESOLVED or absent.
    Normalises purchase dates to ISO YYYY-MM-DD.

    Returns a list of (scheme_code, iso_purchase_date) tuples.
    """
    holdings: list[tuple[int, str]] = []
    in_table = False
    scheme_code_idx: int | None = None
    purchase_idx: int | None = None

    for raw_line in portfolio_text.splitlines():
        line = raw_line.rstrip()

        # Separator line marks transition into table body
        if line.startswith("|") and "---" in line:
            in_table = True
            continue
        if in_table and not line.startswith("|"):
            in_table = False
            scheme_code_idx = None
            purchase_idx = None
            continue

        # Header row (immediately before separator)
        if line.startswith("|") and not in_table:
            cells = [c.strip() for c in line.strip("|").split("|")]
            scheme_code_idx = None
            purchase_idx = None
            for i, c in enumerate(cells):
                lc = c.lower()
                if lc == "scheme_code":
                    scheme_code_idx = i
                elif lc in ("first purchase", "first_purchase", "purchase date", "purchase"):
                    purchase_idx = i
            continue

        # Data row inside a table
        if (in_table and line.startswith("|")
                and scheme_code_idx is not None
                and purchase_idx is not None):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if scheme_code_idx >= len(cells) or purchase_idx >= len(cells):
                continue

            code_cell = cells[scheme_code_idx]
            purchase_cell = cells[purchase_idx]

            # Skip unresolved or empty rows
            if not code_cell or code_cell in ("UNRESOLVED", "—", "-", "N/A"):
                continue

            try:
                scheme_code = int(code_cell)
            except ValueError:
                continue

            iso_date = _normalize_purchase_date(purchase_cell)
            if not iso_date:
                continue

            holdings.append((scheme_code, iso_date))

    return holdings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", type=Path,
                    help="Path to portfolio.md (default: ../portfolio.md from script dir)")
    ap.add_argument("--scheme-code", type=int,
                    help="Single scheme to backfill (overrides portfolio.md scan)")
    ap.add_argument("--from-date",
                    help="Start date ISO YYYY-MM-DD (default: scheme's earliest purchase per portfolio.md)")
    ap.add_argument("--to-date",
                    help="End date ISO YYYY-MM-DD (default: today)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Parse and report; don't write to DB")
    ap.add_argument("--from-file", type=Path,
                    help="Skip HTTP; parse a saved mfapi.in JSON response")
    ap.add_argument("--codes-file", type=Path,
                    help="Path to a file of scheme codes (one per line, '#' comments allowed) "
                         "to backfill full history for. Use for the fund-allocate candidate universe.")
    ap.add_argument("--quiet", action="store_true",
                    help="Suppress per-scheme progress output")
    args = ap.parse_args()

    today_iso = datetime.now().strftime("%Y-%m-%d")

    # Mode 1: --from-file (no HTTP, parse a saved response)
    if args.from_file:
        try:
            payload = json.loads(args.from_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"ERROR reading {args.from_file}: {e}", file=sys.stderr)
            return 1

        records = payload_to_records(
            payload,
            from_date=args.from_date,
            to_date=args.to_date or today_iso,
        )
        if not args.quiet:
            print(f"Parsed {len(records)} records from {args.from_file.name}")

        if args.dry_run:
            log_fetch(SOURCE_NAME, "success", len(records), "dry-run from file")
            return 0

        nav_inserted, schemes_upserted = store_records(records)
        log_fetch(SOURCE_NAME, "success", len(records))
        if not args.quiet:
            print(f"Stored: {nav_inserted:,} new NAV rows, {schemes_upserted:,} scheme upserts")
        return 0

    # Mode 2: --scheme-code (single scheme over custom range)
    if args.scheme_code:
        targets: list[tuple[int, str, str]] = [
            (args.scheme_code,
             args.from_date or "2000-01-01",
             args.to_date or today_iso)
        ]
    # Mode 3: --codes-file (candidate universe; full history per scheme)
    elif args.codes_file:
        if not args.codes_file.exists():
            print(f"ERROR: codes file not found: {args.codes_file}", file=sys.stderr)
            return 1
        codes = parse_codes_file(args.codes_file.read_text(encoding="utf-8"))
        if not codes:
            print(f"ERROR: no scheme codes parsed from {args.codes_file}", file=sys.stderr)
            return 1
        from_date = args.from_date or "2000-01-01"
        to_date = args.to_date or today_iso
        targets = [(code, from_date, to_date) for code in codes]
    # Mode 4: default — read portfolio.md and backfill all resolved holdings
    else:
        portfolio_path = args.file or Path(__file__).resolve().parents[1] / "portfolio.md"
        if not portfolio_path.exists():
            print(f"ERROR: portfolio.md not found at {portfolio_path}", file=sys.stderr)
            print("Pass --file PATH or run from a project root containing portfolio.md.",
                  file=sys.stderr)
            return 1

        text = portfolio_path.read_text(encoding="utf-8")
        holdings = extract_holdings_from_portfolio(text)

        if not holdings:
            print("ERROR: no resolved (scheme_code, first_purchase_date) pairs found "
                  "in portfolio.md. Run resolve_schemes.py first or pass --scheme-code.",
                  file=sys.stderr)
            return 1

        targets = [(code, purchase, today_iso) for code, purchase in holdings]

    if not args.quiet:
        print(f"Backfilling {len(targets)} scheme(s) from mfapi.in")
        print(f"Pacing: {PACING_SECONDS}s between requests; "
              f"timeout: {REQUEST_TIMEOUT}s; retry-on-429 backoff: {RATE_LIMIT_BACKOFF}s")
        print()

    total_records = 0
    total_inserted = 0
    success_count = 0
    failed_codes: list[int] = []

    for i, (scheme_code, from_date, to_date) in enumerate(targets):
        if not args.quiet:
            print(f"  [{i+1}/{len(targets)}] scheme {scheme_code} "
                  f"({from_date} → {to_date}) ...", end=" ", flush=True)

        if i > 0:
            time.sleep(PACING_SECONDS)

        payload = fetch_scheme_history(scheme_code, quiet=args.quiet)
        if not payload:
            if not args.quiet:
                print("FAILED")
            failed_codes.append(scheme_code)
            continue

        records = payload_to_records(payload, from_date=from_date, to_date=to_date)

        if not args.quiet:
            scheme_name = ((payload.get("meta") or {}).get("scheme_name") or "")[:55]
            print(f"{len(records):>4} records — {scheme_name}")

        if not args.dry_run:
            nav_inserted, _ = store_records(records)
            total_inserted += nav_inserted

        total_records += len(records)
        success_count += 1

    # Audit log: success if all targets succeeded, partial otherwise
    status = "success" if not failed_codes else "partial"
    error_msg = f"failed scheme codes: {failed_codes}" if failed_codes else None
    log_fetch(SOURCE_NAME, status, total_records, error_msg)

    if not args.quiet:
        print()
        print(f"Done. {success_count}/{len(targets)} scheme(s) succeeded.")
        if not args.dry_run:
            print(f"Total records parsed: {total_records:,}; "
                  f"new NAV rows inserted: {total_inserted:,}")
        if failed_codes:
            print(f"Failed scheme codes: {failed_codes}")

    return 0 if not failed_codes else 2


if __name__ == "__main__":
    sys.exit(main())
