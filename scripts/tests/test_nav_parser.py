#!/usr/bin/env python3
"""
Tests for fetch_nav.py — parser, classifiers, and DB roundtrip.

Run: python -m pytest scripts/tests/test_nav_parser.py -v
Or:  python scripts/tests/test_nav_parser.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

# Make the scripts dir importable
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from fetch_nav import (  # noqa: E402
    _classify_option,
    _classify_plan,
    _parse_date,
    parse_nav_file,
    store_records,
)
from lib.db import get_conn, init_db  # noqa: E402

# A realistic snippet of AMFI's NAVAll.txt format. Multiple AMCs, multiple categories,
# direct + regular, growth + IDCW, edge cases (legacy schemes without plan label,
# schemes with '-' for missing ISIN, etc.)
SAMPLE_NAV_FILE = """\

 Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date

Open Ended Schemes(Equity Scheme - Large Cap Fund)

Aditya Birla Sun Life Mutual Fund

103176;INF209KA12Z1;-;Aditya Birla Sun Life Frontline Equity Fund - Direct Plan - Growth;456.7800;06-May-2026
103177;INF209KA12Z2;INF209KA12Z3;Aditya Birla Sun Life Frontline Equity Fund - Direct Plan - IDCW;78.4500;06-May-2026
103178;INF209KA12Z4;-;Aditya Birla Sun Life Frontline Equity Fund - Regular Plan - Growth;420.1100;06-May-2026

HDFC Mutual Fund

118989;INF179K01YV8;-;HDFC Top 100 Fund - Direct Plan - Growth;1098.7641;06-May-2026
118990;INF179K01YW6;-;HDFC Top 100 Fund - Regular Plan - Growth;1011.2300;06-May-2026

Open Ended Schemes(Equity Scheme - Mid Cap Fund)

Quant Mutual Fund

120505;INF966L01HS9;-;Quant Mid Cap Fund - Direct Plan - Growth;245.6700;06-May-2026

Open Ended Schemes(Debt Scheme - Liquid Fund)

ICICI Prudential Mutual Fund

100025;INF109K01ZZ8;INF109K01ZZ9;ICICI Prudential Liquid Fund - Direct Plan - Growth;345.1234;06-May-2026

Open Ended Schemes(Other Scheme - Index Funds)

UTI Mutual Fund

145678;INF789F01XY5;-;UTI Nifty 50 Index Fund - Direct Plan - Growth;138.4500;06-May-2026

Close Ended Schemes(Debt Scheme - Fixed Maturity Plans)

SBI Mutual Fund

99999;INF200K01AB1;-;SBI Fixed Maturity Plan Series 12 - Regular Plan - Growth;15.6700;06-May-2026
"""

MALFORMED_LINES_FILE = """\
 Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date

Open Ended Schemes(Equity Scheme - Large Cap Fund)

Test Mutual Fund

123456;INFXXX;-;Valid Scheme - Direct Plan - Growth;100.50;06-May-2026
not_a_number;INFXXX;-;Bad scheme code;100.50;06-May-2026
234567;INFYYY;-;Bad NAV - Direct Plan - Growth;not_a_float;06-May-2026
345678;INFZZZ;-;Bad Date - Direct Plan - Growth;100.50;not-a-date
456789;INFAAA;-;Too few fields
567890;INFBBB;-;Valid Second - Direct Plan - Growth;200.75;06-May-2026
"""


class TestPlanClassifier(unittest.TestCase):
    def test_direct_explicit(self):
        self.assertEqual(_classify_plan("HDFC Top 100 Fund - Direct Plan - Growth"), "Direct")

    def test_regular_explicit(self):
        self.assertEqual(_classify_plan("HDFC Top 100 Fund - Regular Plan - Growth"), "Regular")

    def test_dir_abbreviation(self):
        self.assertEqual(_classify_plan("Some Fund - DIR - G"), "Direct")

    def test_reg_abbreviation(self):
        self.assertEqual(_classify_plan("Some Fund - REG - G"), "Regular")

    def test_parenthesised_d(self):
        self.assertEqual(_classify_plan("Some Fund (D) Growth"), "Direct")

    def test_parenthesised_r(self):
        self.assertEqual(_classify_plan("Some Fund (R) Growth"), "Regular")

    def test_legacy_no_plan_marker(self):
        # Pre-2013 schemes don't have plan labels
        self.assertIsNone(_classify_plan("Old Equity Fund Growth"))

    def test_ambiguous_both_words(self):
        # If somehow both appear, return None rather than guess
        self.assertIsNone(_classify_plan("Direct Regular Confusion Fund"))


class TestOptionClassifier(unittest.TestCase):
    def test_growth(self):
        self.assertEqual(_classify_option("Some Fund - Direct Plan - Growth"), "Growth")

    def test_idcw(self):
        self.assertEqual(_classify_option("Some Fund - Direct Plan - IDCW"), "IDCW")

    def test_dividend_legacy(self):
        # Older schemes still labelled 'Dividend' rather than IDCW
        self.assertEqual(_classify_option("Old Fund Dividend"), "IDCW")

    def test_reinvest(self):
        self.assertEqual(_classify_option("Some Fund - Reinvest"), "Reinvest")

    def test_growth_short(self):
        self.assertEqual(_classify_option("HDFC Banking Fund - G"), "Growth")


class TestDateParser(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(_parse_date("06-May-2026"), "2026-05-06")

    def test_january(self):
        self.assertEqual(_parse_date("01-Jan-2024"), "2024-01-01")

    def test_december(self):
        self.assertEqual(_parse_date("31-Dec-2025"), "2025-12-31")

    def test_with_whitespace(self):
        self.assertEqual(_parse_date(" 15-Aug-2024 "), "2024-08-15")


class TestNavParser(unittest.TestCase):
    def test_full_sample(self):
        records = parse_nav_file(SAMPLE_NAV_FILE)
        # Sample has 8 valid scheme records (3 ABSL + 2 HDFC + 1 Quant + 1 ICICI + 1 UTI + 1 SBI FMP)
        self.assertEqual(len(records), 9)

    def test_amc_assignment(self):
        records = parse_nav_file(SAMPLE_NAV_FILE)
        absl = [r for r in records if r.scheme_code in (103176, 103177, 103178)]
        self.assertTrue(all(r.amc == "Aditya Birla Sun Life Mutual Fund" for r in absl))
        hdfc = [r for r in records if r.scheme_code in (118989, 118990)]
        self.assertTrue(all(r.amc == "HDFC Mutual Fund" for r in hdfc))

    def test_category_assignment(self):
        records = parse_nav_file(SAMPLE_NAV_FILE)
        large_cap = [r for r in records if r.scheme_code in (103176, 103177, 103178, 118989, 118990)]
        self.assertTrue(all(r.category == "Equity Scheme - Large Cap Fund" for r in large_cap))
        mid_cap = [r for r in records if r.scheme_code == 120505]
        self.assertEqual(mid_cap[0].category, "Equity Scheme - Mid Cap Fund")
        liquid = [r for r in records if r.scheme_code == 100025]
        self.assertEqual(liquid[0].category, "Debt Scheme - Liquid Fund")
        index = [r for r in records if r.scheme_code == 145678]
        self.assertEqual(index[0].category, "Other Scheme - Index Funds")

    def test_close_ended_categories_captured(self):
        records = parse_nav_file(SAMPLE_NAV_FILE)
        fmp = [r for r in records if r.scheme_code == 99999]
        self.assertEqual(len(fmp), 1)
        self.assertEqual(fmp[0].category, "Debt Scheme - Fixed Maturity Plans")

    def test_plan_extraction(self):
        records = parse_nav_file(SAMPLE_NAV_FILE)
        by_code = {r.scheme_code: r for r in records}
        self.assertEqual(by_code[103176].plan, "Direct")
        self.assertEqual(by_code[103178].plan, "Regular")
        self.assertEqual(by_code[118989].plan, "Direct")
        self.assertEqual(by_code[118990].plan, "Regular")

    def test_option_extraction(self):
        records = parse_nav_file(SAMPLE_NAV_FILE)
        by_code = {r.scheme_code: r for r in records}
        self.assertEqual(by_code[103176].option_type, "Growth")
        self.assertEqual(by_code[103177].option_type, "IDCW")
        self.assertEqual(by_code[145678].option_type, "Growth")

    def test_isin_dash_to_none(self):
        records = parse_nav_file(SAMPLE_NAV_FILE)
        by_code = {r.scheme_code: r for r in records}
        # Schemes with '-' in div-reinv ISIN should have None
        self.assertIsNone(by_code[103176].isin_div_reinv)
        # Schemes with valid div-reinv ISIN should preserve it
        self.assertEqual(by_code[103177].isin_div_reinv, "INF209KA12Z3")

    def test_nav_value_parsed(self):
        records = parse_nav_file(SAMPLE_NAV_FILE)
        by_code = {r.scheme_code: r for r in records}
        self.assertAlmostEqual(by_code[103176].nav, 456.78, places=2)
        self.assertAlmostEqual(by_code[118989].nav, 1098.7641, places=4)

    def test_date_iso_format(self):
        records = parse_nav_file(SAMPLE_NAV_FILE)
        self.assertTrue(all(r.nav_date == "2026-05-06" for r in records))

    def test_malformed_lines_skipped_not_fatal(self):
        records = parse_nav_file(MALFORMED_LINES_FILE)
        # Should keep the 2 valid records, skip the 4 malformed ones silently
        self.assertEqual(len(records), 2)
        codes = {r.scheme_code for r in records}
        self.assertEqual(codes, {123456, 567890})

    def test_empty_file_returns_empty(self):
        self.assertEqual(parse_nav_file(""), [])

    def test_missing_header_raises(self):
        bad = "Some random content\nnot AMFI format\n"
        with self.assertRaises(ValueError):
            # Need enough non-empty lines to trip the safety check (>5)
            parse_nav_file(bad + "\n".join(f"line {i}" for i in range(10)))


class TestDatabaseRoundtrip(unittest.TestCase):
    def setUp(self):
        # Use a fresh temp DB per test
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        self.db_path = Path(self.tmp_db.name)
        init_db(self.db_path)

    def tearDown(self):
        self.db_path.unlink(missing_ok=True)

    def test_store_and_read_back(self):
        records = parse_nav_file(SAMPLE_NAV_FILE)
        nav_inserted, schemes_upserted = store_records(records, db_path=self.db_path)
        self.assertEqual(nav_inserted, 9)
        self.assertEqual(schemes_upserted, 9)

        with get_conn(self.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) AS c FROM nav_history").fetchone()["c"]
            self.assertEqual(count, 9)
            count = conn.execute("SELECT COUNT(*) AS c FROM schemes").fetchone()["c"]
            self.assertEqual(count, 9)

            # Look up a specific scheme
            row = conn.execute(
                "SELECT scheme_name, plan, option_type, amc, category "
                "FROM schemes WHERE scheme_code = 118989"
            ).fetchone()
            self.assertEqual(row["amc"], "HDFC Mutual Fund")
            self.assertEqual(row["plan"], "Direct")
            self.assertEqual(row["option_type"], "Growth")
            self.assertEqual(row["category"], "Equity Scheme - Large Cap Fund")

    def test_idempotent_reinsertion(self):
        """Running twice with same data shouldn't duplicate NAV rows."""
        records = parse_nav_file(SAMPLE_NAV_FILE)
        store_records(records, db_path=self.db_path)
        store_records(records, db_path=self.db_path)  # second run

        with get_conn(self.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) AS c FROM nav_history").fetchone()["c"]
            self.assertEqual(count, 9)  # not 18


if __name__ == "__main__":
    unittest.main(verbosity=2)
