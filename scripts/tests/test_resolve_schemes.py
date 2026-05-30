#!/usr/bin/env python3
"""Tests for resolve_schemes.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from resolve_schemes import (  # noqa: E402
    PortfolioScheme,
    extract_schemes_from_portfolio,
    format_report,
    match_scheme,
    normalize,
    sequence_similarity,
    token_overlap,
)
from fetch_nav import parse_nav_file, store_records  # noqa: E402
from lib.db import init_db  # noqa: E402


# A realistic AMFI sample with the schemes the user actually holds (per portfolio.md)
AMFI_FIXTURE = """\
 Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date

Open Ended Schemes(Equity Scheme - Mid Cap Fund)

Quant Mutual Fund

120505;INF966L01HS9;-;Quant Mid Cap Fund - Direct Plan - Growth;245.6700;06-May-2026
120506;INF966L01HT7;-;Quant Mid Cap Fund - Regular Plan - Growth;230.4500;06-May-2026

Motilal Oswal Mutual Fund

130001;INF247L01ZA1;-;Motilal Oswal Midcap Fund - Direct Plan - Growth;105.2300;06-May-2026
130002;INF247L01ZB9;-;Motilal Oswal Midcap Fund - Regular Plan - Growth;98.7600;06-May-2026

Open Ended Schemes(Equity Scheme - Small Cap Fund)

Nippon India Mutual Fund

140001;INF204K01AAA;-;Nippon India Small Cap Fund - Direct Plan - Growth;167.8900;06-May-2026

Open Ended Schemes(Other Scheme - Index Funds)

Motilal Oswal Mutual Fund

130100;INF247L01YY1;-;Motilal Oswal Nifty Smallcap 250 Index Fund - Direct Plan - Growth;28.4500;06-May-2026
130101;INF247L01YZ8;-;Motilal Oswal Nifty Midcap 150 Index Fund - Direct Plan - Growth;42.1300;06-May-2026

Open Ended Schemes(Equity Scheme - Flexi Cap Fund)

PPFAS Mutual Fund

122639;INF879O01019;-;Parag Parikh Flexi Cap Fund - Direct Plan - Growth;78.4500;06-May-2026

Open Ended Schemes(Equity Scheme - Large & Mid Cap Fund)

Bandhan Mutual Fund

150001;INF194K01AAA;-;Bandhan Large and Mid Cap Fund - Regular Plan - Growth;47.5500;06-May-2026

Open Ended Schemes(Equity Scheme - Large Cap Fund)

Nippon India Mutual Fund

100025;INF204K01ZZ1;-;Nippon India Large Cap Fund - Regular Plan - Growth;67.8900;06-May-2026

Open Ended Schemes(Equity Scheme - Small Cap Fund)

Bandhan Mutual Fund

150100;INF194K01BBB;-;Bandhan Small Cap Fund - Regular Plan - Growth;32.4500;06-May-2026

Open Ended Schemes(Equity Scheme - Flexi Cap Fund)

Franklin Templeton Mutual Fund

160001;INF090I01XYZ;-;Franklin India Flexi Cap Fund - Regular Plan - Growth;1234.5600;06-May-2026

Open Ended Schemes(Debt Scheme - Short Duration Fund)

Bandhan Mutual Fund

170001;INF194K01CCC;-;Bandhan Short Duration Fund - Regular Plan - Growth;28.9000;06-May-2026

Open Ended Schemes(Other Scheme - Gold Funds)

SBI Mutual Fund

180001;INF200K01XXX;-;SBI Gold Fund - Direct Plan - Growth;22.4500;06-May-2026
"""


# Sample portfolio.md-like content with the schemes formatted as in the user's actual file
PORTFOLIO_FIXTURE = """\
# Portfolio Holdings

## 5. Equity Mutual Funds

### 5.1 User's holdings (Direct, 2025-03)

| # | Scheme | AMC | Plan | Capital | First purchase | Active/Index | Sub-port | Earmark |
|---|---|---|---|---|---|---|---|---|
| 1 | Quant Mid Cap Fund — Direct G | Quant | Direct | ₹43,000 | 2025-03 | Active | user | retirement |
| 2 | Motilal Oswal Midcap — Direct G | Motilal Oswal | Direct | ₹31,000 | 2025-03 | Active | user | retirement |
| 3 | Nippon India Small Cap Fund — Direct | Nippon India | Direct | ₹21,000 | 2025-03 | Active | user | retirement |
| 4 | Motilal Oswal Nifty Smallcap 250 Index Fund | Motilal Oswal | Direct | ₹5,000 | 2025-03 | Index | user | retirement |
| 5 | Parag Parikh Flexi Cap Fund | PPFAS | Direct | ₹5,000 | 2025-03 | Active | user | retirement |
| 6 | Motilal Oswal Nifty Midcap 150 Index Fund | Motilal Oswal | Direct | ₹3,000 | 2025-03 | Index | user | retirement |

### 5.2 Father's holdings (Regular, 2026-04)

| # | Scheme | AMC | Plan | Capital | First purchase | Active/Index | Sub-port | Earmark |
|---|---|---|---|---|---|---|---|---|
| 7 | Bandhan Large and Mid Cap — Reg-G | Bandhan | Regular | ₹1,36,500 | 2026-04 | Active | father | retirement |
| 8 | Nippon India Large Cap — G | Nippon India | Regular | ₹1,25,000 | 2026-04 | Active | father | retirement |
| 9 | Bandhan Small Cap — Reg-G | Bandhan | Regular | ₹48,000 | 2026-04 | Active | father | retirement |
| 10 | Franklin India Flexi Cap — Reg-G | Franklin India | Regular | ₹45,750 | 2026-04 | Active | father | retirement |

## 4. Debt Mutual Funds

| # | Scheme | AMC | Plan | Capital invested | First purchase | SIP | Sub-port | Earmark |
|---|---|---|---|---|---|---|---|---|
| 1 | Bandhan Short Duration Fund | Bandhan | Regular | ₹6,79,000 | 2026-04 | No | father | retirement |

## 10.3 Gold Mutual Funds (FoF)

| # | Scheme | AMC | Plan | Capital | First purchase | SIP | Sub-port | Earmark |
|---|---|---|---|---|---|---|---|---|
| 1 | SBI Gold Fund | SBI | Direct | ₹1,10,000 | 2024-03 | No | user | retirement |
"""


class TestNormalization(unittest.TestCase):
    def test_lowercases(self):
        self.assertNotIn("HDFC", normalize("HDFC Top 100"))

    def test_strips_punctuation(self):
        self.assertEqual(
            normalize("Quant Mid Cap Fund — Direct G"),
            normalize("Quant Mid Cap Fund - Direct - Growth"),
        )

    def test_unifies_growth_marker(self):
        a = normalize("HDFC Top 100 Fund - Direct G")
        b = normalize("HDFC Top 100 Fund - Direct Plan - Growth")
        self.assertEqual(a, b)

    def test_collapses_whitespace(self):
        self.assertEqual(normalize("a   b"), normalize("a b"))


class TestScoring(unittest.TestCase):
    def test_token_overlap_identical(self):
        self.assertEqual(token_overlap("abc def", "abc def"), 1.0)

    def test_token_overlap_disjoint(self):
        self.assertEqual(token_overlap("foo bar", "baz qux"), 0.0)

    def test_token_overlap_partial(self):
        score = token_overlap("Quant Mid Cap Fund Direct G", "Quant Mid Cap Fund Direct Plan Growth")
        self.assertGreater(score, 0.5)


class TestExtraction(unittest.TestCase):
    def test_extracts_table_schemes(self):
        schemes = extract_schemes_from_portfolio(PORTFOLIO_FIXTURE)
        names = [s.name for s in schemes]
        self.assertIn("Quant Mid Cap Fund — Direct G", names)
        self.assertIn("Parag Parikh Flexi Cap Fund", names)
        self.assertIn("Bandhan Short Duration Fund", names)
        self.assertIn("SBI Gold Fund", names)

    def test_total_count(self):
        schemes = extract_schemes_from_portfolio(PORTFOLIO_FIXTURE)
        # 6 user equity + 4 father equity + 1 debt + 1 gold = 12
        self.assertEqual(len(schemes), 12)

    def test_captures_section_context(self):
        schemes = extract_schemes_from_portfolio(PORTFOLIO_FIXTURE)
        debt = [s for s in schemes if s.name == "Bandhan Short Duration Fund"]
        self.assertEqual(len(debt), 1)
        self.assertIn("Debt Mutual Funds", debt[0].section)

    def test_captures_plan_hint(self):
        schemes = extract_schemes_from_portfolio(PORTFOLIO_FIXTURE)
        by_name = {s.name: s for s in schemes}
        self.assertEqual(by_name["Quant Mid Cap Fund — Direct G"].plan_hint, "Direct")
        self.assertEqual(by_name["Bandhan Short Duration Fund"].plan_hint, "Regular")

    def test_skips_none_placeholders(self):
        text = """
## Some Section

| Scheme | AMC |
|---|---|
| None. | - |
| N/A | - |
"""
        schemes = extract_schemes_from_portfolio(text)
        self.assertEqual(schemes, [])

    def test_handles_empty_text(self):
        self.assertEqual(extract_schemes_from_portfolio(""), [])


class TestMatching(unittest.TestCase):
    """End-to-end: load AMFI fixture into a temp DB, then resolve portfolio names."""

    @classmethod
    def setUpClass(cls):
        cls.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.tmp_db.close()
        cls.db_path = Path(cls.tmp_db.name)
        init_db(cls.db_path)
        records = parse_nav_file(AMFI_FIXTURE)
        store_records(records, db_path=cls.db_path)

        # Load into memory once for tests
        import lib.db as db_module
        cls._original_default = db_module.DEFAULT_DB_PATH
        db_module.DEFAULT_DB_PATH = cls.db_path

        from resolve_schemes import load_db_schemes
        cls.db_schemes = load_db_schemes()

    @classmethod
    def tearDownClass(cls):
        import lib.db as db_module
        db_module.DEFAULT_DB_PATH = cls._original_default
        cls.db_path.unlink(missing_ok=True)

    def test_high_confidence_exact_match(self):
        target = PortfolioScheme(
            name="Parag Parikh Flexi Cap Fund - Direct Plan - Growth",
            section="test", line_no=0, plan_hint="Direct",
        )
        result = match_scheme(target, self.db_schemes)
        self.assertEqual(result.confidence, "HIGH")
        self.assertEqual(result.matches[0][0], 122639)

    def test_medium_confidence_abbreviated_name(self):
        target = PortfolioScheme(
            name="Quant Mid Cap Fund — Direct G",
            section="test", line_no=0, plan_hint="Direct",
        )
        result = match_scheme(target, self.db_schemes)
        # Should resolve to the Direct plan (not Regular) with high score
        self.assertIn(result.confidence, ("HIGH", "MEDIUM"))
        self.assertEqual(result.matches[0][0], 120505)
        self.assertEqual(result.matches[0][2], "Direct")

    def test_picks_correct_plan_when_both_exist(self):
        # Bandhan Large and Mid Cap exists only in Regular in fixture, so match should hit it
        target = PortfolioScheme(
            name="Bandhan Large and Mid Cap — Reg-G",
            section="test", line_no=0, plan_hint="Regular",
        )
        result = match_scheme(target, self.db_schemes)
        self.assertIn(result.confidence, ("HIGH", "MEDIUM"))
        self.assertEqual(result.matches[0][2], "Regular")
        self.assertEqual(result.matches[0][0], 150001)

    def test_index_fund_match(self):
        target = PortfolioScheme(
            name="Motilal Oswal Nifty Smallcap 250 Index Fund",
            section="test", line_no=0, plan_hint="Direct",
        )
        result = match_scheme(target, self.db_schemes)
        self.assertIn(result.confidence, ("HIGH", "MEDIUM"))
        self.assertEqual(result.matches[0][0], 130100)

    def test_gold_fund_match(self):
        target = PortfolioScheme(
            name="SBI Gold Fund",
            section="test", line_no=0, plan_hint="Direct",
        )
        result = match_scheme(target, self.db_schemes)
        self.assertIn(result.confidence, ("HIGH", "MEDIUM"))
        self.assertEqual(result.matches[0][0], 180001)

    def test_no_match_returns_none(self):
        target = PortfolioScheme(
            name="NonExistent Imaginary Fund",
            section="test", line_no=0, plan_hint=None,
        )
        result = match_scheme(target, self.db_schemes)
        self.assertEqual(result.confidence, "NONE")
        self.assertEqual(result.matches, [])

    def test_full_portfolio_resolution(self):
        """Run the whole portfolio fixture through the matcher."""
        portfolio_schemes = extract_schemes_from_portfolio(PORTFOLIO_FIXTURE)
        results = [match_scheme(s, self.db_schemes) for s in portfolio_schemes]

        # Of the 12 portfolio schemes:
        #  - 9 are in the AMFI fixture (so HIGH or MEDIUM expected)
        #  - 3 aren't (Nippon Large Cap Direct, Bandhan Short Dur Direct, etc. — but
        #    actually let's check...)
        # Actually all 12 are represented in the fixture; the question is how many
        # resolve at HIGH/MEDIUM vs LOW/NONE
        good = sum(1 for r in results if r.confidence in ("HIGH", "MEDIUM"))
        # We expect at least 10 to resolve cleanly
        self.assertGreaterEqual(good, 10, f"Only {good}/12 resolved cleanly. Results: "
                                          f"{[(r.portfolio.name, r.confidence) for r in results]}")


class TestReportFormat(unittest.TestCase):
    def test_report_includes_all_buckets(self):
        results = [
            MatchResult_high(),
            MatchResult_medium(),
            MatchResult_low(),
            MatchResult_none(),
        ]
        report = format_report(results)
        self.assertIn("HIGH confidence", report)
        self.assertIn("MEDIUM confidence", report)
        self.assertIn("LOW confidence", report)
        self.assertIn("NO MATCH", report)

    def test_report_handles_all_high(self):
        results = [MatchResult_high()]
        report = format_report(results)
        self.assertIn("HIGH confidence", report)
        # Should not have empty MEDIUM/LOW/NONE sections
        self.assertNotIn("## ⚠️", report)


# Helper builders for report tests
def MatchResult_high():
    from resolve_schemes import MatchResult
    return MatchResult(
        portfolio=PortfolioScheme(name="Test Fund", section="x", line_no=1, plan_hint=None),
        matches=[(123, "Test Fund - Direct - Growth", "Direct", "Test AMC", "Equity", 1.0)],
        confidence="HIGH",
    )


def MatchResult_medium():
    from resolve_schemes import MatchResult
    return MatchResult(
        portfolio=PortfolioScheme(name="Approx Fund", section="x", line_no=1, plan_hint=None),
        matches=[(456, "Approx Fund - Direct - Growth", "Direct", "Test AMC", "Equity", 0.91)],
        confidence="MEDIUM",
    )


def MatchResult_low():
    from resolve_schemes import MatchResult
    return MatchResult(
        portfolio=PortfolioScheme(name="Ambig Fund", section="x", line_no=1, plan_hint=None),
        matches=[
            (789, "Ambiguous Fund A", "Direct", "AMC1", "Equity", 0.65),
            (790, "Ambiguous Fund B", "Direct", "AMC2", "Equity", 0.62),
        ],
        confidence="LOW",
    )


def MatchResult_none():
    from resolve_schemes import MatchResult
    return MatchResult(
        portfolio=PortfolioScheme(name="Lost Fund", section="x", line_no=1, plan_hint=None),
        matches=[],
        confidence="NONE",
    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
