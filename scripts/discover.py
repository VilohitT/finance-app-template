#!/usr/bin/env python3
"""
discover.py — mandatory Phase 0 entry point for fund-allocate (and any skill
that needs to know "what tools and data are available right now").

Emits a structured discovery report covering:
  1. Helper inventory          (every public function in scripts/lib/)
  2. Script inventory          (every executable in scripts/)
  3. NAV freshness             (last_fetch_time, staleness flag)
  4. Ledger health             (txn count, latest date)
  5. Recurring registry stats  (active SIPs/STPs)
  6. fund_quality.json coverage (entries, completeness)
  7. laws/ staleness           (vs most recent Union Budget + rate quarter)
  8. decisions-log open ACTIONs (unresolved findings)
  9. Aggregate equity drawdown (per sub-portfolio — feeds §6.4 gate)
 10. Sub-portfolio totals      (current value, sleeve mix)
 11. Ledger schemes            (per-scheme holdings — feeds portfolio-grill Step 0b)

Designed so a calling skill (or a human) can quote the output verbatim and
have a complete map of what's known, what's stale, and what's gated.

Exit codes:
    0 = report emitted; no critical blockers
    1 = invocation error
    2 = critical blocker present (e.g. ledger empty when it shouldn't be)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
LIB_DIR = SCRIPTS_DIR / "lib"
sys.path.insert(0, str(SCRIPTS_DIR))

from lib.db import get_conn, last_fetch_time  # noqa: E402
from lib.transactions import (  # noqa: E402
    DEFAULT_LEDGER_PATH,
    DEFAULT_RECURRING_PATH,
    load_recurring,
    load_transactions,
    current_value_per_scheme,
)
from lib.drawdown import aggregate_equity_drawdown, classify_sleeve  # noqa: E402
from lib.fund_quality import load_quality, QUALITY_FIELDS  # noqa: E402
from lib.freshness import (  # noqa: E402
    most_recent_budget_year,
    parse_law_header,
    quarter_label,
    quarter_lag,
)

LAWS_DIR = ROOT / "laws"
DECISIONS_LOG = ROOT / "decisions-log.md"
FUND_QUALITY_JSON = ROOT / "data" / "fund_quality.json"
TODAY = date.today()


def _section(title: str) -> str:
    return f"\n{'=' * 78}\n{title}\n{'=' * 78}"


# ----------------------------------------------------------------------------
# 1. Helper inventory
# ----------------------------------------------------------------------------

def helper_inventory() -> list[dict]:
    """Walk scripts/lib/*.py and return public-function summaries."""
    out = []
    for f in sorted(LIB_DIR.glob("*.py")):
        if f.name.startswith("_"):
            continue
        text = f.read_text()
        funcs = []
        # Naive but safe: top-level "def name(...)" lines outside underscore prefix
        for line in text.splitlines():
            if line.startswith("def ") and not line.startswith("def _"):
                name = line[4:].split("(")[0].strip()
                funcs.append(name)
        # Module docstring (first triple-quoted block)
        doc = ""
        if text.startswith('"""'):
            end = text.find('"""', 3)
            if end > 3:
                first_line = text[3:end].strip().splitlines()[0]
                doc = first_line
        out.append({"module": f.stem, "doc": doc, "functions": funcs})
    return out


# ----------------------------------------------------------------------------
# 2. Script inventory
# ----------------------------------------------------------------------------

def script_inventory() -> list[dict]:
    """Walk scripts/*.py and return script names + first docstring line."""
    out = []
    for f in sorted(SCRIPTS_DIR.glob("*.py")):
        if f.stem in {"__init__", "discover"}:
            continue
        text = f.read_text()
        doc = ""
        # Module docstring
        idx = text.find('"""')
        if idx >= 0:
            end = text.find('"""', idx + 3)
            if end > idx:
                # First non-empty line of the docstring
                for line in text[idx + 3:end].strip().splitlines():
                    line = line.strip()
                    if line:
                        doc = line
                        break
        out.append({"script": f.name, "doc": doc})
    return out


# ----------------------------------------------------------------------------
# 3. NAV freshness
# ----------------------------------------------------------------------------

def nav_freshness() -> dict:
    last = last_fetch_time("amfi_nav")
    with get_conn() as conn:
        row = conn.execute(
            "SELECT MAX(nav_date) AS d, COUNT(DISTINCT scheme_code) AS n "
            "FROM nav_history"
        ).fetchone()
    latest_nav_date = row["d"] if row else None
    n_schemes_with_history = row["n"] if row else 0

    stale_24h = True
    fetch_age_hours = None
    if last:
        # SQLite CURRENT_TIMESTAMP is UTC and naive; defensively handle a
        # tz-suffixed value too. Coerce both sides to aware-UTC before subtracting
        # so we never raise the "naive vs aware" TypeError.
        s = last.replace("Z", "+00:00") if last.endswith("Z") else last
        last_dt = datetime.fromisoformat(s)
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        fetch_age_hours = (now - last_dt).total_seconds() / 3600
        stale_24h = fetch_age_hours > 24
    return {
        "last_fetch_time": last,
        "fetch_age_hours": round(fetch_age_hours, 1) if fetch_age_hours else None,
        "stale_24h": stale_24h,
        "latest_nav_date": latest_nav_date,
        "schemes_with_nav_history": n_schemes_with_history,
        "action_if_stale": "run `python3 scripts/fetch_nav.py --quiet` before relying on prices",
    }


# ----------------------------------------------------------------------------
# 4. Ledger health
# ----------------------------------------------------------------------------

def ledger_health() -> dict:
    txns = load_transactions()
    if not txns:
        return {
            "txn_count": 0,
            "latest_txn_date": None,
            "earliest_txn_date": None,
            "schemes_held": 0,
            "blocker": "LEDGER EMPTY — backfill required (scripts/backfill_units.py)",
        }
    dates = sorted(t["date"] for t in txns)
    schemes = {t["scheme_code"] for t in txns}
    with get_conn() as conn:
        cv = current_value_per_scheme(txns, conn)
    holdings_with_units = {sc: v for sc, v in cv.items() if v["units"] > 0}
    return {
        "txn_count": len(txns),
        "latest_txn_date": dates[-1],
        "earliest_txn_date": dates[0],
        "schemes_held": len(holdings_with_units),
        "schemes_with_history_in_ledger": len(schemes),
    }


# ----------------------------------------------------------------------------
# 5. Recurring registry
# ----------------------------------------------------------------------------

def recurring_stats() -> dict:
    rec = load_recurring()
    sips = rec.get("sips", [])
    stps = rec.get("stps", [])
    active_sips = [s for s in sips if s.get("status") == "active"]
    active_stps = [s for s in stps if s.get("status") == "active"]
    return {
        "active_sips": len(active_sips),
        "active_stps": len(active_stps),
        "total_sip_outflow_per_month": round(sum(s.get("amount_inr", 0) for s in active_sips), 2),
        "total_stp_outflow_per_month": round(sum(s.get("amount_inr_per_tranche", 0) for s in active_stps), 2),
    }


# ----------------------------------------------------------------------------
# 6. fund_quality.json coverage
# ----------------------------------------------------------------------------

def fund_quality_coverage() -> dict:
    quality = load_quality(FUND_QUALITY_JSON)
    if not quality:
        return {
            "n_entries": 0,
            "blocker": "fund_quality.json empty — sparse-data mode for everything",
        }
    # Bucket by category (need to join schemes table)
    if not quality:
        return {"n_entries": 0}
    codes = list(quality.keys())
    by_category: dict[str, int] = {}
    by_plan: dict[str, int] = {}
    completeness_total = 0.0
    n_complete = 0
    stale_entries = []
    cutoff = (TODAY - timedelta(days=90)).isoformat()
    with get_conn() as conn:
        placeholders = ",".join("?" * len(codes))
        rows = conn.execute(
            f"SELECT scheme_code, category, plan FROM schemes "
            f"WHERE scheme_code IN ({placeholders})",
            codes,
        ).fetchall()
    cat_by_code = {r["scheme_code"]: (r["category"], r["plan"]) for r in rows}

    for code, info in quality.items():
        cat, plan = cat_by_code.get(code, ("unknown", "unknown"))
        by_category[cat] = by_category.get(cat, 0) + 1
        plan_key = plan or "legacy"
        by_plan[plan_key] = by_plan.get(plan_key, 0) + 1
        # Completeness
        filled = sum(1 for f in QUALITY_FIELDS if info.get(f) is not None)
        ratio = filled / len(QUALITY_FIELDS)
        completeness_total += ratio
        if ratio >= 1.0:
            n_complete += 1
        # Staleness
        last_v = info.get("last_verified")
        if last_v and last_v < cutoff:
            stale_entries.append((code, last_v))

    return {
        "n_entries": len(quality),
        "n_complete_entries": n_complete,
        "avg_completeness": round(completeness_total / len(quality), 3),
        "by_category": dict(sorted(by_category.items(), key=lambda kv: -kv[1])),
        "by_plan": by_plan,
        "n_stale_over_90d": len(stale_entries),
        "action_for_sparse_categories": (
            "run /fund-research <category> to populate candidates"
        ),
    }


# ----------------------------------------------------------------------------
# 7. laws/ staleness
# ----------------------------------------------------------------------------

def laws_staleness() -> dict:
    """
    Walk laws/*.md (and laws/index.md) and surface the same staleness signals
    that `scripts/check_freshness.py laws` computes — both call into
    `scripts/lib/freshness.py` so the two paths can't drift apart.

    Per-file flags:
      - budget_lag:    last_verified_against_budget is older than the most
                       recent Union Budget (presented every Feb 1)
      - stale_over_1y: last_updated is more than 365 days old
      - quarter_lag:   for files that carry an `As-of: Q* FY YYYY-YY`
                       annotation (ppf.md, scss.md, …), the annotation is
                       older than the current rate-cycle quarter; None when
                       the file does not track quarterly rates
    """
    out: dict = {}
    cutoff = (TODAY - timedelta(days=365)).isoformat()
    expected_budget_year = most_recent_budget_year(TODAY)
    for f in sorted(LAWS_DIR.glob("*.md")):
        header = parse_law_header(f.read_text())
        budget_lag = (
            header.verified_budget_year < expected_budget_year
            if header.verified_budget_year is not None
            else None
        )
        as_of_label = (
            quarter_label(header.as_of_q, header.as_of_fy_start_year)
            if header.as_of_q is not None and header.as_of_fy_start_year is not None
            else None
        )
        out[f.name] = {
            "last_updated": header.last_updated,
            "last_verified_against_budget": header.last_verified_raw,
            "verified_budget_year": header.verified_budget_year,
            "expected_budget_year": expected_budget_year,
            "stale_over_1y": (
                (header.last_updated or "") < cutoff if header.last_updated else None
            ),
            "budget_lag": budget_lag,
            "quarter_lag": quarter_lag(header, TODAY),
            "as_of_quarter": as_of_label,
        }
    return out


# ----------------------------------------------------------------------------
# 8. decisions-log open ACTIONs
# ----------------------------------------------------------------------------

def decisions_log_open_actions() -> dict:
    if not DECISIONS_LOG.exists():
        return {"open_actions": 0, "note": "decisions-log.md does not exist"}
    text = DECISIONS_LOG.read_text()
    # Heuristic dashboard count — the skill is expected to read the log in
    # full and reconcile. We recognize the resolution markers actually used
    # in this household's log: `**Status:** acted/deferred`, `Status:
    # acted/deferred`, and the inline `**RESOLVED <date>**` / `**Closed
    # <date>**` patterns. New marker styles must be added here AND back-filled
    # into existing entries — otherwise the count silently overstates "open".
    action_headers = sum(1 for line in text.splitlines() if line.startswith("#### ACTION-"))
    deferred = text.count("**Status:** deferred") + text.count("Status: deferred")
    acted = (
        text.count("**Status:** acted")
        + text.count("Status: acted")
        + text.count("**RESOLVED ")
        + text.count("**Closed ")
    )
    return {
        "action_headers_total": action_headers,
        "explicitly_acted": acted,
        "explicitly_deferred": deferred,
        "guidance": "read decisions-log.md in full before allocating; deferred ACTIONs may still apply",
    }


# ----------------------------------------------------------------------------
# 9. Drawdown gate
# ----------------------------------------------------------------------------

def drawdown_gate() -> dict:
    sub_ports = ["user", "father"]
    out = {}
    blocker = False
    for sp in sub_ports:
        result = aggregate_equity_drawdown(sub_portfolio=sp)
        out[sp] = {
            "weighted_drawdown": result["weighted_drawdown"],
            "block_at_minus_20pct": result["block_at_minus_20pct"],
            "total_equity_value_inr": result["total_equity_value_inr"],
            "n_equity_schemes": len(result["schemes"]),
            # Equity holdings whose NAV history is missing — silently excluded
            # from the value-weighted drawdown. A non-zero count means the gate
            # may understate true drawdown; surface it so the caller knows.
            "n_missing_history": len(result.get("missing_history", [])),
            "missing_history_codes": result.get("missing_history", []),
        }
        if result["block_at_minus_20pct"]:
            blocker = True
    return {
        "per_sub_portfolio": out,
        "principle_64_blocked": blocker,
        "principle_ref": "principles.md §6.4 — no rebalancing into 20%+ drawdown",
    }


# ----------------------------------------------------------------------------
# 10. Sub-portfolio totals (uses render_portfolio's snapshot)
# ----------------------------------------------------------------------------

def sub_portfolio_totals() -> dict:
    """
    Bucket current value by (sub_portfolio, sleeve).

    Splits the ledger by sub_portfolio first and runs current_value_per_scheme
    on each split, so a scheme that has txns under multiple sub_portfolios
    (rare — convention is one-sub-portfolio-per-scheme — but possible after a
    re-attribution) is attributed correctly per sub_portfolio.
    """
    txns = load_transactions()
    if not txns:
        return {"empty_ledger": True}

    # Split by sub_portfolio
    by_sub: dict[str, list[dict]] = {}
    for t in txns:
        by_sub.setdefault(t.get("sub_portfolio", "unknown"), []).append(t)

    with get_conn() as conn:
        # Pre-fetch category metadata for every scheme appearing anywhere in the ledger
        all_codes = sorted({t["scheme_code"] for t in txns})
        if all_codes:
            placeholders = ",".join("?" * len(all_codes))
            rows = conn.execute(
                f"SELECT scheme_code, category, scheme_name FROM schemes "
                f"WHERE scheme_code IN ({placeholders})",
                all_codes,
            ).fetchall()
            cat_by_code = {r["scheme_code"]: (r["category"], r["scheme_name"]) for r in rows}
        else:
            cat_by_code = {}

        sub_port_breakdown: dict[str, dict[str, float]] = {}
        for sub, sub_txns in by_sub.items():
            cv = current_value_per_scheme(sub_txns, conn)
            for sc, info in cv.items():
                cur = info.get("current_value_inr")
                if cur is None or cur == 0:
                    continue
                cat, nm = cat_by_code.get(sc, (None, None))
                sleeve = classify_sleeve(cat, nm)
                sub_port_breakdown.setdefault(sub, {}).setdefault(sleeve, 0.0)
                sub_port_breakdown[sub][sleeve] += cur

    for sub, sleeves in sub_port_breakdown.items():
        sub_port_breakdown[sub] = {k: round(v, 2) for k, v in sleeves.items()}
    return sub_port_breakdown


# ----------------------------------------------------------------------------
# 11. Ledger schemes (per-scheme holdings)
# ----------------------------------------------------------------------------

def ledger_schemes() -> list[dict]:
    """
    One row per (scheme_code, sub_portfolio) currently held in the ledger
    with non-zero units. Ordered by sub_portfolio, then scheme_name. Used by
    `portfolio-grill` Step 0b to enumerate already-captured holdings before
    the per-scheme interview, so the agent never re-grills an in-ledger scheme.
    """
    txns = load_transactions()
    if not txns:
        return []

    by_sub: dict[str, list[dict]] = {}
    for t in txns:
        by_sub.setdefault(t.get("sub_portfolio", "unknown"), []).append(t)

    name_by_code: dict[int, str] = {}
    for t in txns:
        name_by_code.setdefault(t["scheme_code"], t.get("scheme_name") or "")

    rows: list[dict] = []
    with get_conn() as conn:
        for sub, sub_txns in by_sub.items():
            cv = current_value_per_scheme(sub_txns, conn)
            for sc, info in cv.items():
                if (info.get("units") or 0) <= 0:
                    continue
                rows.append({
                    "scheme_code": sc,
                    "scheme_name": name_by_code.get(sc, ""),
                    "sub_portfolio": sub,
                    "units": round(info.get("units") or 0, 4),
                    "current_value_inr": round(info.get("current_value_inr") or 0, 2),
                })
    rows.sort(key=lambda r: (r["sub_portfolio"], r["scheme_name"]))
    return rows


# ----------------------------------------------------------------------------
# Render
# ----------------------------------------------------------------------------

def render(report: dict) -> str:
    lines = []
    lines.append(_section("DISCOVERY REPORT — " + TODAY.isoformat()))
    lines.append(
        "This is the mandatory Phase 0 output for fund-allocate (and any skill that\n"
        "needs to know what tools/data exist). Quote the relevant rows below before\n"
        "any allocation. Re-run `python3 scripts/discover.py` if state may have changed."
    )

    lines.append(_section("1. HELPER INVENTORY  (scripts/lib/)"))
    for h in report["helpers"]:
        lines.append(f"  • {h['module']}:  {h['doc']}")
        for fn in h["functions"]:
            lines.append(f"      - {fn}()")

    lines.append(_section("2. SCRIPT INVENTORY  (scripts/)"))
    for s in report["scripts"]:
        lines.append(f"  • {s['script']}:  {s['doc']}")

    lines.append(_section("3. NAV FRESHNESS"))
    nf = report["nav_freshness"]
    flag = "STALE" if nf["stale_24h"] else "FRESH"
    lines.append(f"  status:                 {flag}")
    lines.append(f"  last_fetch_time:        {nf['last_fetch_time']}")
    lines.append(f"  fetch_age_hours:        {nf['fetch_age_hours']}")
    lines.append(f"  latest_nav_date:        {nf['latest_nav_date']}")
    lines.append(f"  schemes_with_history:   {nf['schemes_with_nav_history']}")
    if nf["stale_24h"]:
        lines.append(f"  ACTION:  {nf['action_if_stale']}")

    lines.append(_section("4. LEDGER HEALTH  (data/transactions.json)"))
    lh = report["ledger"]
    if "blocker" in lh:
        lines.append(f"  BLOCKER:                {lh['blocker']}")
    else:
        lines.append(f"  txn_count:              {lh['txn_count']}")
        lines.append(f"  date_range:             {lh['earliest_txn_date']} → {lh['latest_txn_date']}")
        lines.append(f"  schemes_held:           {lh['schemes_held']}")

    lines.append(_section("5. RECURRING REGISTRY  (data/recurring.json)"))
    rs = report["recurring"]
    lines.append(f"  active_sips:            {rs['active_sips']}  (₹{rs['total_sip_outflow_per_month']:,.0f}/mo)")
    lines.append(f"  active_stps:            {rs['active_stps']}  (₹{rs['total_stp_outflow_per_month']:,.0f}/mo)")

    lines.append(_section("6. FUND_QUALITY.JSON COVERAGE"))
    fq = report["fund_quality"]
    if "blocker" in fq:
        lines.append(f"  BLOCKER:                {fq['blocker']}")
    else:
        lines.append(f"  n_entries:              {fq['n_entries']}")
        lines.append(f"  n_complete:             {fq['n_complete_entries']}  (avg completeness {fq['avg_completeness']:.0%})")
        lines.append(f"  n_stale_over_90d:       {fq['n_stale_over_90d']}")
        lines.append(f"  by_plan:                {fq['by_plan']}")
        lines.append(f"  by_category:")
        for cat, n in fq["by_category"].items():
            lines.append(f"      [{n}]  {cat}")
        lines.append(f"  ACTION for sparse cats: {fq['action_for_sparse_categories']}")

    lines.append(_section("7. LAWS STALENESS  (laws/*.md)"))
    expected_year = None
    for info in report["laws"].values():
        if info.get("expected_budget_year") is not None:
            expected_year = info["expected_budget_year"]
            break
    if expected_year is not None:
        lines.append(f"  most_recent_budget:       Union Budget {expected_year}")
    from lib.freshness import current_small_savings_quarter
    cur_q, cur_fy = current_small_savings_quarter(TODAY)
    lines.append(f"  current_savings_quarter:  {quarter_label(cur_q, cur_fy)}")
    for fname, info in report["laws"].items():
        flags = []
        if info.get("budget_lag"):
            flags.append("BUDGET-LAG")
        if info.get("verified_budget_year") is None:
            flags.append("NO-BUDGET-TAG")
        if info.get("stale_over_1y"):
            flags.append("STALE>1y")
        if info.get("quarter_lag"):
            flags.append("QUARTER-LAG")
        flag = ",".join(flags) if flags else "OK"
        verified = info.get("verified_budget_year")
        verified_str = f"Budget {verified}" if verified is not None else "Budget=?"
        suffix = f"  as_of {info['as_of_quarter']}" if info.get("as_of_quarter") else ""
        lines.append(
            f"  {flag:24}  {fname}: last_updated {info['last_updated']}  "
            f"verified_against {verified_str}{suffix}"
        )
    lines.append(
        "  ACTION if any flagged: run `laws-refresh` (or scope to single file). "
        "BUDGET-LAG and QUARTER-LAG presume the file is stale even if last_updated is recent."
    )

    lines.append(_section("8. DECISIONS LOG OPEN ACTIONS"))
    dl = report["decisions_log"]
    if "open_actions" in dl:
        lines.append(f"  {dl['note']}")
    else:
        lines.append(f"  ACTION headers in log:  {dl['action_headers_total']}")
        lines.append(f"  explicitly acted:       {dl['explicitly_acted']}")
        lines.append(f"  explicitly deferred:    {dl['explicitly_deferred']}")
        lines.append(f"  GUIDANCE:               {dl['guidance']}")

    lines.append(_section("9. DRAWDOWN GATE  (principles.md §6.4)"))
    dg = report["drawdown"]
    if dg["principle_64_blocked"]:
        lines.append("  STATUS:                 ⚠️  BLOCKED — aggregate equity drawdown ≥20% in at least one sub-portfolio")
    else:
        lines.append("  STATUS:                 OPEN — equity-additive recommendations allowed")
    for sub, info in dg["per_sub_portfolio"].items():
        dd_pct = info["weighted_drawdown"] * 100
        flag = "BLOCK" if info["block_at_minus_20pct"] else "ok"
        lines.append(
            f"  {sub:6}  weighted_dd {dd_pct:+.2f}%  ({flag})  "
            f"equity_value ₹{info['total_equity_value_inr']:,.0f}  "
            f"n_schemes {info['n_equity_schemes']}"
        )
        if info.get("n_missing_history"):
            lines.append(
                f"          ⚠️  {info['n_missing_history']} equity scheme(s) "
                f"missing NAV history → drawdown understated. "
                f"codes: {info['missing_history_codes']}"
            )
    lines.append(f"  ref:                    {dg['principle_ref']}")

    lines.append(_section("10. SUB-PORTFOLIO TOTALS  (current value)"))
    spt = report["sub_portfolios"]
    if "empty_ledger" in spt:
        lines.append("  (ledger empty)")
    else:
        for sub, sleeves in spt.items():
            total = sum(sleeves.values())
            lines.append(f"  {sub}:")
            for sleeve, v in sorted(sleeves.items()):
                pct = (v / total * 100) if total > 0 else 0
                lines.append(f"      {sleeve:8}  ₹{v:>14,.0f}  ({pct:5.1f}%)")
            lines.append(f"      {'TOTAL':8}  ₹{total:>14,.0f}")

    lines.append(_section("11. LEDGER SCHEMES  (per-scheme holdings, units > 0)"))
    ls = report["ledger_schemes"]
    if not ls:
        lines.append("  (ledger empty — no captured schemes to skip)")
    else:
        lines.append(
            "  Use this list in `portfolio-grill` Step 0b: every row below is"
            " already in the ledger and"
        )
        lines.append(
            "  must NOT be re-grilled without explicit user confirmation."
        )
        lines.append(
            f"  {'sub_portfolio':14}  {'scheme_code':>11}  {'current_value':>16}  scheme_name"
        )
        for r in ls:
            lines.append(
                f"  {r['sub_portfolio']:14}  {r['scheme_code']:>11}  "
                f"₹{r['current_value_inr']:>14,.0f}  {r['scheme_name']}"
            )

    lines.append(_section("END OF DISCOVERY REPORT"))
    lines.append(
        "Next steps for fund-allocate:\n"
        "  • If §6.4 BLOCKED: do not propose equity-additive recommendations.\n"
        "  • If NAVs STALE: refresh before quoting current values.\n"
        "  • If ledger BLOCKER: run scripts/backfill_units.py first.\n"
        "  • For any sleeve where fund_quality.json has 0 entries in the needed category,\n"
        "    invoke /fund-research before committing a scheme pick.\n"
    )
    return "\n".join(lines)


def build_report() -> dict:
    return {
        "as_of": TODAY.isoformat(),
        "helpers": helper_inventory(),
        "scripts": script_inventory(),
        "nav_freshness": nav_freshness(),
        "ledger": ledger_health(),
        "recurring": recurring_stats(),
        "fund_quality": fund_quality_coverage(),
        "laws": laws_staleness(),
        "decisions_log": decisions_log_open_actions(),
        "drawdown": drawdown_gate(),
        "sub_portfolios": sub_portfolio_totals(),
        "ledger_schemes": ledger_schemes(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Discovery report for fund-allocate Phase 0.")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of formatted text.")
    args = ap.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(render(report))
    # Exit 2 only on hard blockers that prevent allocation entirely.
    # An empty fund_quality.json is NOT a blocker — sparse-data mode is a
    # documented graceful-degradation path; calling skills should still proceed
    # and prompt /fund-research where needed.
    hard_blocker = report["ledger"].get("blocker") is not None
    return 2 if hard_blocker else 0


if __name__ == "__main__":
    sys.exit(main())
