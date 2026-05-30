#!/usr/bin/env python3
"""
render_portfolio.py — Regenerate the MF/STP-touched sections of portfolio.md
from the transaction ledger and current NAVs.

Inputs:
    data/transactions.json   — append-only ledger (source of truth)
    data/market.db           — NAV history + scheme metadata
    portfolio.md             — file with <!-- BEGIN: managed-by-render -->
                               and <!-- END: managed-by-render --> markers

Outputs (depending on mode):
    --write    : replaces managed region in portfolio.md atomically
    --print    : prints the rendered managed-region content to stdout
    --check    : prints a diff vs current portfolio.md content; non-zero exit if drift
    --json     : emits a structured snapshot (current value per scheme, sub-portfolio
                 totals, gain/loss) to stdout

Markers:
    Wrap the managed region in portfolio.md with these literal lines (no extra spaces):

        <!-- BEGIN: managed-by-render -->
        ... rendered content goes here ...
        <!-- END: managed-by-render -->

    On first migration, add the markers around the MF tables and let the script
    populate them. Static sections (FD, real estate, insurance, governance notes)
    sit OUTSIDE the markers and are not touched.

Exit codes: 0 success, 1 user error, 2 marker not found, 3 drift detected (--check)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.db import get_conn  # noqa: E402
from lib.transactions import (  # noqa: E402
    DEFAULT_LEDGER_PATH,
    load_transactions,
    units_per_scheme,
    cost_basis_per_scheme,
    current_value_per_scheme,
    value_by_sub_portfolio,
)

ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO_PATH = ROOT / "portfolio.md"
BEGIN_MARKER = "<!-- BEGIN: managed-by-render -->"
END_MARKER = "<!-- END: managed-by-render -->"


# --------------------------------------------------------------------------
# Build the structured snapshot
# --------------------------------------------------------------------------

def build_snapshot(txns: list[dict], conn) -> dict:
    """Return a structured snapshot used by both --json and the markdown renderer."""
    cv = current_value_per_scheme(txns, conn)
    if not cv:
        return {
            "as_of": str(date.today()),
            "schemes": [],
            "sub_portfolio_totals": {},
            "totals": {"cost_basis_inr": 0.0, "current_value_inr": 0.0, "unrealised_gain_inr": 0.0},
        }

    # Build a per-scheme snapshot row, joining ledger metadata.
    by_sc: dict[int, dict] = {}
    for t in txns:
        sc = t["scheme_code"]
        if sc not in by_sc:
            by_sc[sc] = {
                "scheme_code": sc,
                "scheme_name": t["scheme_name"],
                "sub_portfolio": t["sub_portfolio"],
                "first_purchase": t["date"],
                "active_sip": False,
                "active_stp_source": False,
                "active_stp_dest": False,
            }
        else:
            if t["date"] < by_sc[sc]["first_purchase"]:
                by_sc[sc]["first_purchase"] = t["date"]
        if t.get("sip_id"):
            by_sc[sc]["active_sip"] = True
        if t.get("stp_id"):
            if t["type"] in {"redemption", "switch-out"}:
                by_sc[sc]["active_stp_source"] = True
            else:
                by_sc[sc]["active_stp_dest"] = True

    schemes = []
    total_cost = 0.0
    total_value = 0.0
    for sc, info in cv.items():
        meta = by_sc.get(sc, {})
        row = {
            "scheme_code": sc,
            "scheme_name": meta.get("scheme_name", "?"),
            "sub_portfolio": meta.get("sub_portfolio", "?"),
            "first_purchase": meta.get("first_purchase"),
            "units": info["units"],
            "cost_basis_inr": info["cost_basis_inr"],
            "latest_nav": info["latest_nav"],
            "latest_nav_date": info["latest_nav_date"],
            "current_value_inr": info["current_value_inr"],
            "unrealised_gain_inr": info["unrealised_gain_inr"],
            "active_sip": meta.get("active_sip", False),
            "active_stp_source": meta.get("active_stp_source", False),
            "active_stp_dest": meta.get("active_stp_dest", False),
        }
        schemes.append(row)
        total_cost += row["cost_basis_inr"]
        if row["current_value_inr"] is not None:
            total_value += row["current_value_inr"]

    schemes.sort(key=lambda r: (r["sub_portfolio"], -r["cost_basis_inr"]))

    return {
        "as_of": str(date.today()),
        "schemes": schemes,
        "sub_portfolio_totals": value_by_sub_portfolio(txns, conn),
        "totals": {
            "cost_basis_inr": round(total_cost, 2),
            "current_value_inr": round(total_value, 2),
            "unrealised_gain_inr": round(total_value - total_cost, 2),
        },
    }


# --------------------------------------------------------------------------
# Markdown rendering
# --------------------------------------------------------------------------

def _fmt_inr(v: float | None) -> str:
    if v is None:
        return "—"
    sign = "-" if v < 0 else ""
    return f"{sign}₹{abs(v):,.0f}"


def render_markdown(snapshot: dict) -> str:
    """Render the managed-region markdown content."""
    if not snapshot["schemes"]:
        return (
            "_(Ledger empty — no transactions logged yet. Run "
            "`scripts/backfill_units.py` to seed historical purchases, or "
            "`scripts/log_transaction.py` to add new ones.)_\n"
        )

    lines: list[str] = []
    lines.append(f"_Auto-rendered from `data/transactions.json` as of {snapshot['as_of']}. "
                 "Do not hand-edit between the BEGIN/END markers._\n")

    # Summary table.
    t = snapshot["totals"]
    lines.append("### MF holdings — overall\n")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Total cost basis | {_fmt_inr(t['cost_basis_inr'])} |")
    lines.append(f"| Total current value | {_fmt_inr(t['current_value_inr'])} |")
    lines.append(f"| Unrealised gain/loss | {_fmt_inr(t['unrealised_gain_inr'])} |")
    if snapshot["sub_portfolio_totals"]:
        for sub, val in sorted(snapshot["sub_portfolio_totals"].items()):
            lines.append(f"| Sub-portfolio: {sub} | {_fmt_inr(val)} |")
    lines.append("")

    # Per-sub-portfolio holdings.
    by_sub: dict[str, list[dict]] = defaultdict(list)
    for s in snapshot["schemes"]:
        by_sub[s["sub_portfolio"]].append(s)

    for sub in sorted(by_sub.keys()):
        lines.append(f"### MF holdings — {sub} sub-portfolio\n")
        lines.append("| Scheme | Code | First buy | Units | Cost basis | Latest NAV | Current value | Unrealised | Flags |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for s in by_sub[sub]:
            flags = []
            if s["active_sip"]:
                flags.append("SIP")
            if s["active_stp_source"]:
                flags.append("STP-src")
            if s["active_stp_dest"]:
                flags.append("STP-dst")
            flag_str = " ".join(flags) if flags else "—"
            nav_str = (f"₹{s['latest_nav']:.4f} ({s['latest_nav_date']})"
                       if s["latest_nav"] else "—")
            lines.append(
                f"| {s['scheme_name']} | {s['scheme_code']} | {s['first_purchase']} | "
                f"{s['units']:.4f} | {_fmt_inr(s['cost_basis_inr'])} | {nav_str} | "
                f"{_fmt_inr(s['current_value_inr'])} | {_fmt_inr(s['unrealised_gain_inr'])} | {flag_str} |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Marker-based replacement
# --------------------------------------------------------------------------

def find_managed_region(text: str) -> tuple[int, int]:
    """Return (begin_idx, end_idx) — character positions of marker lines.
    Raises SystemExit(2) if markers not found exactly once."""
    begins = [i for i, line in enumerate(text.splitlines(keepends=True))
              if line.strip() == BEGIN_MARKER]
    ends = [i for i, line in enumerate(text.splitlines(keepends=True))
            if line.strip() == END_MARKER]
    if len(begins) != 1 or len(ends) != 1:
        print(
            f"ERROR: portfolio.md must contain exactly one each of {BEGIN_MARKER!r} "
            f"and {END_MARKER!r} marker lines. Found {len(begins)} BEGIN and {len(ends)} END.\n"
            f"Add the markers around the MF-tables region and re-run.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if ends[0] <= begins[0]:
        print(f"ERROR: END marker must come after BEGIN marker.", file=sys.stderr)
        raise SystemExit(2)
    return (begins[0], ends[0])


def splice_managed_region(text: str, new_content: str) -> str:
    lines = text.splitlines(keepends=True)
    begin_idx, end_idx = find_managed_region(text)
    head = "".join(lines[: begin_idx + 1])
    tail = "".join(lines[end_idx:])
    return head + "\n" + new_content + "\n" + tail


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="Replace managed region in portfolio.md")
    g.add_argument("--print", action="store_true", help="Print rendered managed-region to stdout")
    g.add_argument("--check", action="store_true", help="Print diff vs current portfolio.md, exit 3 if drift")
    g.add_argument("--json", action="store_true", help="Emit structured snapshot JSON")
    p.add_argument("--ledger", default=str(DEFAULT_LEDGER_PATH))
    p.add_argument("--portfolio", default=str(PORTFOLIO_PATH))
    args = p.parse_args()

    txns = load_transactions(args.ledger)
    with get_conn() as conn:
        snapshot = build_snapshot(txns, conn)

    if args.json:
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        return 0

    rendered = render_markdown(snapshot)

    if args.print:
        print(rendered)
        return 0

    portfolio_path = Path(args.portfolio)
    if not portfolio_path.exists():
        print(f"ERROR: portfolio file not found: {portfolio_path}", file=sys.stderr)
        return 1
    text = portfolio_path.read_text()
    new_text = splice_managed_region(text, rendered)

    if args.check:
        if new_text == text:
            print("OK — no drift between ledger-derived content and portfolio.md.")
            return 0
        # Show a minimal diff.
        import difflib
        diff = "".join(difflib.unified_diff(
            text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile="portfolio.md (current)",
            tofile="portfolio.md (would-be)",
            n=2,
        ))
        print(diff)
        return 3

    # --write: atomic
    tmp = portfolio_path.with_suffix(".md.tmp")
    tmp.write_text(new_text)
    tmp.replace(portfolio_path)
    print(f"Rewrote managed region in {portfolio_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
