#!/usr/bin/env python3
"""
Tests for fetch_nav_history.py — JSON parser, date handling, portfolio extraction,
and full DB roundtrip.

Run: python scripts/tests/test_nav_history.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from fetch_nav_history import (  # noqa: E402
    _normalize_purchase_date,
    extract_holdings_from_portfolio,
    parse_mfapi_date,
    payload_to_records,
)
from fetch_nav import store_records  # noqa: E402
from lib.db import get_conn, init_db  # noqa: E402


# Realistic mfapi.in response shape (PPFAS Flexi Cap, Direct, Growth)
SAMPLE_PPFCF_RESPONSE = {
    "meta": {
        "fund_house": "PPFAS Mutual Fund",
        "scheme_type": "Open Ended Schemes",
        "scheme_category": "Equity Scheme - Flexi Cap Fund",
        "scheme_code": 122639,
        "scheme_name": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth"
    },
    "data": [
        {"date": "08-05-2026", "nav": "78.4500"},
        {"date": "07-05-2026", "nav": "78.1200"},
        {"date": "06-05-2026", "nav": "77.9800"},
        {"date": "05-05-2026", "nav": "77.5000"},
        {"date": "02-05-2026", "nav": "77.6500"},
        {"date": "01-05-2026", "nav": "77.4000"},
        {"date": "30-04-2026", "nav": "77.0000"},
        {"date": "29-04-2026", "nav": "76.5000"},
    ],
    "status": "SUCCESS"
}

# Pre-2013 legacy scheme — name has no Direct/Regular marker
SAMPLE_LEGACY_RESPONSE = {
    "meta": {
        "fund_house": "Nippon India Mutual Fund",
        "scheme_type": "Open Ended Schemes",
        "scheme_category": "Debt Scheme - Floater Fund",
        "scheme_code": 102673,
        "scheme_name": "Nippon India Floating Rate Fund - Growth"
    },
    "data": [
        {"date": "08-05-2026", "nav": "45.2300"},
        {"date": "07-05-2026", "nav": "45.2100"},
    ],
    "status": "SUCCESS"
}

# mfapi.in returns this shape on bad scheme code
SAMPLE_FAIL_RESPONSE = {"status": "FAIL"}

# Response with malformed entries mixed in (parser should skip silently)
SAMPLE_MALFORMED_RESPONSE = {
    "meta": {
        "fund_house": "Test AMC",
        "scheme_type": "Open Ended",
        "scheme_category": "Test",
        "scheme_code": 999999,
        "scheme_name": "Test Fund - Direct - Growth"
    },
    "data": [
        {"date": "08-05-2026", "nav": "100.5"},
        {"date": "not-a-date", "nav": "100.5"},      # bad date — skip
        {"date": "07-05-2026", "nav": "not-a-number"},  # bad nav — skip
        {"date": "06-05-2026"},                         # missing nav — skip
        {"date": "05-05-2026", "nav": "99.0"},
    ],
    "status": "SUCCESS"
}

# Realistic portfolio.md fragment with a mix of resolved and unresolved schemes
SAMPLE_PORTFOLIO = """
# Portfolio Holdings

last_updated: 2026-05-09

## 5. Equity Mutual Funds

### 5.1 User's holdings

| # | Scheme | AMC | Plan | scheme_code | Capital | First purchase | Active/Index | Sub-port | Earmark |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Quant Mid Cap Fund — Direct G | Quant | Direct | 120841 | ₹43,000 | 2025-03 | Active | user | retirement |
| 2 | Parag Parikh Flexi Cap Fund | PPFAS | Direct | 122639 | ₹5,000 | 2025-03 | Active | user | retirement |

## 4. Debt Mutual Funds

| # | Scheme | AMC | Plan | scheme_code | Capital invested | First purchase | SIP | Sub-port | Earmark |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Bandhan Short Duration Fund | Bandhan | Regular | 108768 | ₹6,79,000 | 2026-04-15 | No | father | retirement |
| 2 | Nippon Floater | Nippon India | Regular | 102673 | ₹1,38,000 | 2026-04 | No | father | retirement |
| 3 | Some Unresolved Scheme | X | Regular | UNRESOLVED | ₹50,000 | 2026-04 | No | father | retirement |

## 10.3 Gold Mutual Funds (FoF)

| # | Scheme | AMC | Plan | scheme_code | Capital | First purchase | SIP | Sub-port | Earmark |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SBI Gold Fund | SBI | Direct | 119788 | ₹1,10,000 | 2024-03 | No | user | retirement |

## 7. Hybrid

| # | Scheme | AMC | Plan | scheme_code | Capital | First purchase | Sub-port | Earmark |
|---|---|---|---|---|---|---|---|---|
| 1 | ICICI Pru Multi-Asset | ICICI | Regular | 101144 | ₹1,00,000 | 2026-04 | father | retirement |
"""


class TestDateParser(unittest.TestCase):
    def test_basic_dd_mm_yyyy(self):
        self.assertEqual(parse_mfapi_date("08-05-2026"), "2026-05-08")

    def test_january(self):
        self.assertEqual(parse_mfapi_date("01-01-2024"), "2024-01-01")

    def test_december(self):
        self.assertEqual(parse_mfapi_date("31-12-2025"), "2025-12-31")

    def test_with_whitespace(self):
        self.assertEqual(parse_mfapi_date(" 15-08-2024 "), "2024-08-15")


class TestNormalizePurchaseDate(unittest.TestCase):
    def test_full_iso(self):
        self.assertEqual(_normalize_purchase_date("2026-04-15"), "2026-04-15")

    def test_year_month_only(self):
        self.assertEqual(_normalize_purchase_date("2026-04"), "2026-04-01")

    def test_invalid_returns_none(self):
        self.assertIsNone(_normalize_purchase_date("Q1 2026"))
        self.assertIsNone(_normalize_purchase_date(""))
        self.assertIsNone(_normalize_purchase_date("2026"))
        self.assertIsNone(_normalize_purchase_date("April 2026"))


class TestPayloadToRecords(unittest.TestCase):
    def test_basic_full_history(self):
        records = payload_to_records(SAMPLE_PPFCF_RESPONSE)
        self.assertEqual(len(records), 8)
        self.assertEqual(records[0].scheme_code, 122639)
        self.assertEqual(records[0].plan, "Direct")
        self.assertEqual(records[0].option_type, "Growth")
        self.assertEqual(records[0].amc, "PPFAS Mutual Fund")
        self.assertEqual(records[0].category, "Equity Scheme - Flexi Cap Fund")

    def test_iso_dates(self):
        records = payload_to_records(SAMPLE_PPFCF_RESPONSE)
        for r in records:
            self.assertRegex(r.nav_date, r"^\d{4}-\d{2}-\d{2}$")

    def test_legacy_scheme_no_plan(self):
        records = payload_to_records(SAMPLE_LEGACY_RESPONSE)
        self.assertEqual(len(records), 2)
        # Pre-2013 schemes have no Direct/Regular marker → plan should be None
        self.assertIsNone(records[0].plan)
        self.assertEqual(records[0].option_type, "Growth")

    def test_failed_payload_returns_empty(self):
        self.assertEqual(payload_to_records(SAMPLE_FAIL_RESPONSE), [])

    def test_none_payload(self):
        self.assertEqual(payload_to_records(None), [])

    def test_empty_payload(self):
        self.assertEqual(payload_to_records({}), [])

    def test_malformed_entries_skipped(self):
        records = payload_to_records(SAMPLE_MALFORMED_RESPONSE)
        # 2 valid entries; 3 malformed should be silently skipped
        self.assertEqual(len(records), 2)
        self.assertEqual({r.nav for r in records}, {100.5, 99.0})

    def test_date_filter_from_only(self):
        # Bound at 2026-05-01: keeps 5 entries (2026-05-01 through 2026-05-08)
        records = payload_to_records(SAMPLE_PPFCF_RESPONSE, from_date="2026-05-01")
        self.assertEqual(len(records), 6)
        self.assertTrue(all(r.nav_date >= "2026-05-01" for r in records))

    def test_date_filter_to_only(self):
        # Bound at 2026-05-02: keeps 4 entries (29-04, 30-04, 01-05, 02-05)
        records = payload_to_records(SAMPLE_PPFCF_RESPONSE, to_date="2026-05-02")
        self.assertEqual(len(records), 4)
        self.assertTrue(all(r.nav_date <= "2026-05-02" for r in records))

    def test_date_filter_both_bounds(self):
        records = payload_to_records(
            SAMPLE_PPFCF_RESPONSE,
            from_date="2026-05-02",
            to_date="2026-05-06",
        )
        # 02-05, 05-05, 06-05 (03-05 and 04-05 weren't in sample)
        self.assertEqual(len(records), 3)
        for r in records:
            self.assertTrue("2026-05-02" <= r.nav_date <= "2026-05-06")

    def test_inclusive_bounds(self):
        # Both ends should be inclusive
        records = payload_to_records(
            SAMPLE_PPFCF_RESPONSE,
            from_date="2026-05-08",
            to_date="2026-05-08",
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].nav_date, "2026-05-08")


class TestExtractHoldings(unittest.TestCase):
    def test_extracts_resolved_holdings(self):
        holdings = extract_holdings_from_portfolio(SAMPLE_PORTFOLIO)
        codes = sorted(h[0] for h in holdings)
        # Should find: 120841, 122639, 108768, 102673, 119788, 101144
        # Should skip: UNRESOLVED row
        self.assertEqual(codes, sorted([120841, 122639, 108768, 102673, 119788, 101144]))

    def test_skips_unresolved(self):
        holdings = extract_holdings_from_portfolio(SAMPLE_PORTFOLIO)
        codes = [h[0] for h in holdings]
        self.assertNotIn("UNRESOLVED", codes)
        # Six resolved (one row was UNRESOLVED → skipped)
        self.assertEqual(len(codes), 6)

    def test_purchase_date_normalised(self):
        holdings = extract_holdings_from_portfolio(SAMPLE_PORTFOLIO)
        by_code = {c: d for c, d in holdings}
        # YYYY-MM should normalise to YYYY-MM-01
        self.assertEqual(by_code[120841], "2025-03-01")
        self.assertEqual(by_code[102673], "2026-04-01")
        self.assertEqual(by_code[119788], "2024-03-01")
        # YYYY-MM-DD should pass through
        self.assertEqual(by_code[108768], "2026-04-15")

    def test_handles_multiple_tables(self):
        holdings = extract_holdings_from_portfolio(SAMPLE_PORTFOLIO)
        # Schemes from 4 different tables — all should be captured
        amcs_present = set()
        for code, _ in holdings:
            if code in (120841, 122639):
                amcs_present.add("equity")
            elif code in (108768, 102673):
                amcs_present.add("debt")
            elif code == 119788:
                amcs_present.add("gold")
            elif code == 101144:
                amcs_present.add("hybrid")
        self.assertEqual(amcs_present, {"equity", "debt", "gold", "hybrid"})

    def test_empty_portfolio(self):
        self.assertEqual(extract_holdings_from_portfolio(""), [])

    def test_portfolio_without_scheme_code_column(self):
        # Older portfolio.md (pre-resolution) has no scheme_code column
        old_portfolio = """
| # | Scheme | AMC | Plan | Capital | First purchase |
|---|---|---|---|---|---|
| 1 | Some Fund | X | Direct | ₹1L | 2025-01 |
"""
        self.assertEqual(extract_holdings_from_portfolio(old_portfolio), [])


class TestEndToEnd(unittest.TestCase):
    """Full pipeline: payload → records → DB → readback."""

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        self.db_path = Path(self.tmp_db.name)
        init_db(self.db_path)

    def tearDown(self):
        self.db_path.unlink(missing_ok=True)

    def test_full_roundtrip(self):
        records = payload_to_records(SAMPLE_PPFCF_RESPONSE)
        nav_inserted, _ = store_records(records, db_path=self.db_path)
        self.assertEqual(nav_inserted, 8)

        with get_conn(self.db_path) as conn:
            # nav_history should have 8 distinct (scheme_code, nav_date) rows
            count = conn.execute("SELECT COUNT(*) FROM nav_history").fetchone()[0]
            self.assertEqual(count, 8)

            # schemes table should have 1 row (8 records all share scheme_code=122639)
            count = conn.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]
            self.assertEqual(count, 1)

            # Verify metadata captured correctly
            row = conn.execute(
                "SELECT scheme_name, plan, option_type, amc FROM schemes WHERE scheme_code = 122639"
            ).fetchone()
            self.assertEqual(row["plan"], "Direct")
            self.assertEqual(row["option_type"], "Growth")
            self.assertEqual(row["amc"], "PPFAS Mutual Fund")

    def test_idempotent_reinsertion(self):
        """Running the same payload twice should not duplicate rows."""
        records = payload_to_records(SAMPLE_PPFCF_RESPONSE)
        store_records(records, db_path=self.db_path)
        store_records(records, db_path=self.db_path)  # second run

        with get_conn(self.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM nav_history").fetchone()[0]
            self.assertEqual(count, 8)  # not 16

    def test_date_filtered_storage(self):
        records = payload_to_records(SAMPLE_PPFCF_RESPONSE, from_date="2026-05-01")
        nav_inserted, _ = store_records(records, db_path=self.db_path)
        self.assertEqual(nav_inserted, 6)

    def test_two_schemes_combined(self):
        """Storing records for two distinct schemes; both should be in DB."""
        records1 = payload_to_records(SAMPLE_PPFCF_RESPONSE)
        records2 = payload_to_records(SAMPLE_LEGACY_RESPONSE)
        store_records(records1, db_path=self.db_path)
        store_records(records2, db_path=self.db_path)

        with get_conn(self.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]
            self.assertEqual(count, 2)

            count = conn.execute("SELECT COUNT(*) FROM nav_history").fetchone()[0]
            self.assertEqual(count, 10)  # 8 + 2


if __name__ == "__main__":
    unittest.main(verbosity=2)
