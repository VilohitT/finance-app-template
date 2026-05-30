#!/usr/bin/env python3
"""
resolve_schemes.py — Match portfolio.md scheme names to AMFI scheme codes.

Reads scheme names from portfolio.md (or stdin), fuzzy-matches them against the
schemes table in data/market.db, and prints a markdown patch the user can apply
to portfolio.md.

Usage:
    python resolve_schemes.py                    # read portfolio.md from project root
    python resolve_schemes.py --file PATH        # explicit portfolio.md path
    python resolve_schemes.py --names "name1,name2,name3"  # match specific names
    python resolve_schemes.py --interactive      # walk through low-confidence matches

Match strategy (in order):
    1. Exact name match (after light normalisation)
    2. Token-set match (handles word-order and minor punctuation differences)
    3. AMC + category + plan match (when name itself differs but other fields converge)
    4. Fuzzy substring match with a confidence score

Output is markdown showing each portfolio scheme with its resolved code(s) and
confidence rating: HIGH (1 unique exact match), MEDIUM (1 unique fuzzy match),
LOW (multiple candidates or weak match — needs manual review), NONE (no match).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

try:
    from .lib.db import get_conn
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lib.db import get_conn  # type: ignore


# Normalisation rules — applied in order. Designed so that scheme names typed
# different ways by AMFI vs the user end up identical.
#
# Examples this should unify:
#   "Quant Mid Cap Fund — Direct G"        →  "quant mid cap direct growth"
#   "Quant Mid Cap Fund - Direct Plan - Growth"  →  same
#   "HDFC Top 100 (D) (G)"                  →  "hdfc top 100 direct growth"
#   "Bandhan Small Cap — Reg-G"             →  "bandhan small cap regular growth"
#
# Rule order matters: parenthesised markers BEFORE punctuation stripping;
# 'direct plan'/'regular plan' BEFORE bare 'plan'; trailing 'g' → 'growth' AFTER
# punctuation strip but BEFORE the standalone 'fund' drop.
NORMALIZATION_RULES = [
    # Parenthesised markers — handle BEFORE stripping parens
    (r"\(g\)", " growth "),
    (r"\(d\)", " direct "),
    (r"\(r\)", " regular "),
    # Ampersand to word
    (r"&", " and "),
    # Drop the redundant 'mutual fund' phrase (carries no signal)
    (r"\bmutual\s+fund\b", " "),
    # Plan name canonicalisation — multi-word forms first
    (r"\bdirect\s+plan\b", "direct"),
    (r"\bregular\s+plan\b", "regular"),
    # Then abbreviations (with word boundaries, so 'dir' doesn't match in 'direct')
    (r"\breg\b", "regular"),
    (r"\bdir\b", "direct"),
    # Growth canonicalisation — multi-word forms before stripping punctuation
    (r"\bgrowth\s+option\b", "growth"),
    # Strip all remaining punctuation (hyphens, em-dashes, slashes, etc.)
    (r"[^\w\s]", " "),
    # AFTER punctuation strip: trailing standalone 'g' (from "Direct G") → growth
    (r"\bg\s*$", "growth"),
    # Mid-string 'direct g' or 'regular g' → expand
    (r"\b(direct|regular)\s+g\b", r"\1 growth"),
    # Drop the standalone word 'fund' — carries no matching signal
    (r"\bfund\b", " "),
    # Collapse whitespace
    (r"\s+", " "),
]


@dataclass
class PortfolioScheme:
    """A scheme name lifted from portfolio.md."""
    name: str
    section: str  # e.g. "5.1 User equity", "4 Debt MF", "10.3 Gold MF"
    line_no: int
    plan_hint: str | None = None  # 'Direct' / 'Regular' if explicit in source


@dataclass
class MatchResult:
    """Result of trying to match one portfolio scheme."""
    portfolio: PortfolioScheme
    matches: list[tuple[int, str, str, str, str, float]]
    # Each tuple: (scheme_code, scheme_name, plan, amc, category, confidence)
    confidence: str  # 'HIGH' / 'MEDIUM' / 'LOW' / 'NONE'


def normalize(name: str) -> str:
    """Lowercase + strip noise words/punctuation for tolerant matching."""
    s = name.lower().strip()
    for pattern, replacement in NORMALIZATION_RULES:
        s = re.sub(pattern, replacement, s)
    return s.strip()


def token_overlap(a: str, b: str) -> float:
    """Jaccard-style similarity on token sets after normalisation."""
    a_tokens = set(normalize(a).split())
    b_tokens = set(normalize(b).split())
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)


def token_containment(a: str, b: str) -> float:
    """
    Containment score: |intersection| / min(|a|, |b|).

    Captures the case where one name is a subset of the other — e.g. user types
    "Motilal Oswal Nifty Smallcap 250 Index Fund" while AMFI canonical is
    "Motilal Oswal Nifty Smallcap 250 Index Fund - Direct Plan - Growth". Jaccard
    penalises this even though the shorter is fully contained in the longer.
    """
    a_tokens = set(normalize(a).split())
    b_tokens = set(normalize(b).split())
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / min(len(a_tokens), len(b_tokens))


def sequence_similarity(a: str, b: str) -> float:
    """Character-level SequenceMatcher ratio after normalisation."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def extract_schemes_from_portfolio(portfolio_text: str) -> list[PortfolioScheme]:
    """
    Walk portfolio.md table rows and bullet lines, extracting scheme names.

    Looks for these patterns:
      - Markdown table rows where a 'Scheme' column appears (heuristic: pipe-delimited
        rows with a recognisable AMC keyword like 'Fund', 'Cap', 'Index', 'Debt', etc.)
      - Bullet/paragraph lines like '**Scheme name (full):** Some Fund Name'

    Section context is tracked from the most recent '## ' or '### ' heading.
    """
    schemes: list[PortfolioScheme] = []
    section = "(unknown)"
    in_table = False
    table_header_cells: list[str] = []
    scheme_col_idx: int | None = None
    plan_col_idx: int | None = None

    # AMC/scheme keyword regex — used as a sanity filter to avoid grabbing
    # rows from unrelated tables (insurance, real-estate, etc.). Includes both
    # spaced ('mid cap') and joined ('midcap') forms — AMC naming varies.
    fund_keyword = re.compile(
        r"\b(fund|index|etf|cap|debt|gold|liquid|equity|hybrid|allocation|saving|growth"
        r"|midcap|smallcap|largecap|flexicap|multicap|focused|elss|nifty|sensex|sip)\b",
        re.IGNORECASE,
    )

    for line_no, raw in enumerate(portfolio_text.splitlines(), start=1):
        line = raw.rstrip()

        # Track section
        m = re.match(r"^#{2,3}\s+(.+)$", line)
        if m:
            section = m.group(1).strip()
            in_table = False
            continue

        # Detect table boundaries
        if line.startswith("|") and "---" in line:
            # Separator row: previous line was the header
            in_table = True
            continue
        if in_table and not line.startswith("|"):
            in_table = False
            scheme_col_idx = None
            plan_col_idx = None
            continue

        # Capture table header
        if line.startswith("|") and not in_table:
            cells = [c.strip() for c in line.strip("|").split("|")]
            table_header_cells = cells
            scheme_col_idx = None
            plan_col_idx = None
            for i, c in enumerate(cells):
                lc = c.lower()
                if lc in ("scheme", "scheme name", "scheme / instrument", "fund", "instrument"):
                    scheme_col_idx = i
                if lc in ("plan", "plan (direct/regular)"):
                    plan_col_idx = i
            continue

        # Inside a table: extract scheme name from the scheme column
        if in_table and line.startswith("|") and scheme_col_idx is not None:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if scheme_col_idx >= len(cells):
                continue
            name_cell = cells[scheme_col_idx]
            # Skip if the cell is empty, a placeholder, or doesn't look like a fund
            if not name_cell or name_cell in ("None.", "N/A", "—", "-"):
                continue
            if not fund_keyword.search(name_cell):
                continue
            plan_hint = None
            if plan_col_idx is not None and plan_col_idx < len(cells):
                p = cells[plan_col_idx].strip().lower()
                if "direct" in p:
                    plan_hint = "Direct"
                elif "regular" in p:
                    plan_hint = "Regular"
            schemes.append(PortfolioScheme(
                name=name_cell,
                section=section,
                line_no=line_no,
                plan_hint=plan_hint,
            ))
            continue

        # Bullet/key-value pattern: '**Scheme name (full):** XYZ Fund - Direct'
        m = re.match(r"^\s*[-*]\s*\*\*Scheme\s+name(?:\s*\(full\))?\s*:\*\*\s*(.+)$", line)
        if m:
            name = m.group(1).strip()
            if name and name not in ("None.", "N/A"):
                schemes.append(PortfolioScheme(
                    name=name,
                    section=section,
                    line_no=line_no,
                    plan_hint=None,
                ))

    return schemes


def match_scheme(target: PortfolioScheme, db_schemes: list[dict]) -> MatchResult:
    """
    Find the best AMFI scheme(s) for one portfolio scheme.

    Returns MatchResult with confidence:
      HIGH: 1 unique normalized-equal candidate, plan matches if hinted
      MEDIUM: 1 unique candidate at high similarity (>= 0.85)
      LOW: multiple candidates or top similarity < 0.85
      NONE: top similarity < 0.55 (effectively unmatched)
    """
    target_norm = normalize(target.name)

    # Pass 1: exact normalized match
    exact = [s for s in db_schemes if normalize(s["scheme_name"]) == target_norm]
    if target.plan_hint:
        exact_plan = [s for s in exact if s["plan"] == target.plan_hint]
        if exact_plan:
            exact = exact_plan
    if len(exact) == 1:
        s = exact[0]
        return MatchResult(
            portfolio=target,
            matches=[(s["scheme_code"], s["scheme_name"], s["plan"], s["amc"], s["category"], 1.0)],
            confidence="HIGH",
        )
    if len(exact) > 1:
        # Multiple "exact" matches — usually means duplicates with subtle whitespace
        # diffs in AMFI, or growth+IDCW variants of same scheme. Surface all.
        return MatchResult(
            portfolio=target,
            matches=[
                (s["scheme_code"], s["scheme_name"], s["plan"], s["amc"], s["category"], 1.0)
                for s in exact
            ],
            confidence="LOW",
        )

    # Pass 2: scored fuzzy match across all schemes
    scored: list[tuple[float, dict]] = []
    for s in db_schemes:
        token_sim = token_overlap(target.name, s["scheme_name"])
        containment = token_containment(target.name, s["scheme_name"])
        seq_sim = sequence_similarity(target.name, s["scheme_name"])
        # Containment captures subset relationships (user's short name fully inside
        # AMFI's full name); Jaccard captures balanced overlap; sequence is a
        # character-level tiebreaker for very close strings.
        score = 0.35 * token_sim + 0.35 * containment + 0.30 * seq_sim

        # Subset-match floor: if user's normalised name is a strict subset of the
        # candidate's tokens AND the plan matches the hint, this is almost certainly
        # the right scheme even if jaccard pulls the combined score down due to
        # name-length asymmetry. Treat as a strong match. Common case: user types
        # 'SBI Gold Fund' / 'Parag Parikh Flexi Cap Fund' and AMFI canonical adds
        # ' - Direct Plan - Growth' suffix.
        if containment >= 0.999:  # ~= 1.0 with float tolerance
            if target.plan_hint and s["plan"] == target.plan_hint:
                score = max(score, 0.92)  # firmly into MEDIUM
            elif target.plan_hint is None and s["plan"] is None:
                score = max(score, 0.88)
            else:
                # Partial: subset match but plan ambiguous (no hint, or plan mismatch)
                score = max(score, 0.78)

        # Plan-match boost (independent of subset detection)
        if target.plan_hint and s["plan"] == target.plan_hint:
            score += 0.05

        scored.append((score, s))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:5]

    if not top:
        return MatchResult(portfolio=target, matches=[], confidence="NONE")

    top_score = top[0][0]

    # Confidence rating
    if top_score >= 0.85 and (len(top) == 1 or top[1][0] < top_score - 0.10):
        # Clear winner
        s = top[0][1]
        return MatchResult(
            portfolio=target,
            matches=[(s["scheme_code"], s["scheme_name"], s["plan"], s["amc"], s["category"], top_score)],
            confidence="MEDIUM",
        )
    if top_score < 0.55:
        return MatchResult(portfolio=target, matches=[], confidence="NONE")

    # Otherwise low confidence; surface top candidates for user review
    matches = [
        (s["scheme_code"], s["scheme_name"], s["plan"], s["amc"], s["category"], score)
        for score, s in top
        if score >= 0.55
    ]
    return MatchResult(portfolio=target, matches=matches, confidence="LOW")


def load_db_schemes() -> list[dict]:
    """Load all schemes from the data layer. Convert sqlite3.Row to plain dicts."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT scheme_code, scheme_name, plan, amc, category, option_type "
            "FROM schemes"
        ).fetchall()
    return [dict(r) for r in rows]


def format_report(results: list[MatchResult]) -> str:
    """Generate a markdown report the user can review and apply to portfolio.md."""
    out: list[str] = []
    out.append("# Scheme Code Resolution Report")
    out.append("")
    out.append(f"_Generated against AMFI schemes table; {len(results)} portfolio schemes processed._")
    out.append("")

    high = [r for r in results if r.confidence == "HIGH"]
    medium = [r for r in results if r.confidence == "MEDIUM"]
    low = [r for r in results if r.confidence == "LOW"]
    none = [r for r in results if r.confidence == "NONE"]

    out.append("## Summary")
    out.append("")
    out.append(f"- HIGH confidence (apply directly): **{len(high)}**")
    out.append(f"- MEDIUM confidence (verify, then apply): **{len(medium)}**")
    out.append(f"- LOW confidence (manual review): **{len(low)}**")
    out.append(f"- NO MATCH (likely typo or scheme retired): **{len(none)}**")
    out.append("")

    if high:
        out.append("## ✅ HIGH confidence matches — apply to portfolio.md")
        out.append("")
        out.append("| Portfolio name | Code | AMFI canonical name | Plan | AMC |")
        out.append("|---|---|---|---|---|")
        for r in high:
            for code, name, plan, amc, _, _ in r.matches:
                out.append(f"| {r.portfolio.name} | `{code}` | {name} | {plan or '-'} | {amc} |")
        out.append("")

    if medium:
        out.append("## ⚠️ MEDIUM confidence matches — verify, then apply")
        out.append("")
        out.append("| Portfolio name | Code | AMFI canonical name | Plan | AMC | Score |")
        out.append("|---|---|---|---|---|---|")
        for r in medium:
            for code, name, plan, amc, _, score in r.matches:
                out.append(
                    f"| {r.portfolio.name} | `{code}` | {name} | {plan or '-'} | {amc} | {score:.2f} |"
                )
        out.append("")

    if low:
        out.append("## ❓ LOW confidence — manual review needed")
        out.append("")
        out.append("Multiple candidates or weak similarity. Pick the right one or note none apply.")
        out.append("")
        for r in low:
            out.append(f"### {r.portfolio.name}")
            out.append(f"_(from section: {r.portfolio.section})_")
            out.append("")
            out.append("| Code | AMFI canonical name | Plan | AMC | Category | Score |")
            out.append("|---|---|---|---|---|---|")
            for code, name, plan, amc, cat, score in r.matches:
                out.append(
                    f"| `{code}` | {name} | {plan or '-'} | {amc} | {cat} | {score:.2f} |"
                )
            out.append("")

    if none:
        out.append("## ❌ NO MATCH — likely typo or scheme not in current AMFI data")
        out.append("")
        for r in none:
            out.append(f"- **{r.portfolio.name}** _(section: {r.portfolio.section})_")
        out.append("")
        out.append("Possible reasons: scheme has been wound up, name typed differently in portfolio.md, or AMFI data is stale (run `fetch_nav.py` to refresh).")
        out.append("")

    out.append("## How to apply")
    out.append("")
    out.append("Add a `scheme_code:` field to each holding in portfolio.md. For example:")
    out.append("")
    out.append("```")
    out.append("| # | Scheme | AMC | Plan | scheme_code | Capital invested | ...")
    out.append("|---|---|---|---|---|---|---")
    out.append("| 1 | Quant Mid Cap Fund — Direct G | Quant | Direct | 120505 | ₹43,000 | ...")
    out.append("```")
    out.append("")
    out.append("Or append the code in the existing notes column. Either works for downstream skills.")
    out.append("")

    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", type=Path, help="Path to portfolio.md (default: ../portfolio.md)")
    ap.add_argument("--names", help="Comma-separated scheme names instead of file")
    ap.add_argument("--quiet", action="store_true", help="Suppress progress output")
    args = ap.parse_args()

    # Load portfolio schemes
    if args.names:
        schemes = [
            PortfolioScheme(name=n.strip(), section="(stdin)", line_no=0, plan_hint=None)
            for n in args.names.split(",") if n.strip()
        ]
    else:
        portfolio_path = args.file or Path(__file__).resolve().parents[1] / "portfolio.md"
        if not portfolio_path.exists():
            print(f"ERROR: portfolio.md not found at {portfolio_path}", file=sys.stderr)
            print("Pass --file PATH or run from a project root containing portfolio.md.", file=sys.stderr)
            return 1
        text = portfolio_path.read_text(encoding="utf-8")
        schemes = extract_schemes_from_portfolio(text)

    if not schemes:
        print("No scheme names found to resolve.", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Resolving {len(schemes)} scheme name(s) against AMFI database...", file=sys.stderr)

    # Load DB schemes
    db_schemes = load_db_schemes()
    if not db_schemes:
        print("ERROR: schemes table is empty. Run `python scripts/fetch_nav.py` first.", file=sys.stderr)
        return 2

    if not args.quiet:
        print(f"  ({len(db_schemes):,} schemes available in market.db)", file=sys.stderr)

    # Match each
    results = [match_scheme(s, db_schemes) for s in schemes]

    # Print report to stdout (so user can pipe / redirect)
    print(format_report(results))

    # Summary line to stderr
    if not args.quiet:
        high = sum(1 for r in results if r.confidence == "HIGH")
        med = sum(1 for r in results if r.confidence == "MEDIUM")
        low = sum(1 for r in results if r.confidence == "LOW")
        none = sum(1 for r in results if r.confidence == "NONE")
        print(f"Done. HIGH={high} MEDIUM={med} LOW={low} NONE={none}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
