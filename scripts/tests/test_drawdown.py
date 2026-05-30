#!/usr/bin/env python3
"""Tests for scripts/lib/drawdown.py."""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from lib.db import init_db  # noqa: E402
from lib.drawdown import (  # noqa: E402
    aggregate_equity_drawdown,
    classify_sleeve,
    current_drawdown,
    is_equity_for_drawdown,
    peak_nav,
)


def make_temp_db() -> Path:
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    init_db(f.name)
    return Path(f.name)


def insert_scheme(db_path: Path, scheme_code: int, **kwargs):
    defaults = dict(
        scheme_name=f"Scheme {scheme_code}",
        amc="Test AMC",
        category="Equity Scheme - Flexi Cap Fund",
        plan="Direct",
        option_type="Growth",
        first_seen="2020-01-01",
        last_seen="2026-05-08",
    )
    defaults.update(kwargs)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO schemes (scheme_code, scheme_name, amc, category, plan, "
            "option_type, first_seen, last_seen) VALUES (?,?,?,?,?,?,?,?)",
            (
                scheme_code, defaults["scheme_name"], defaults["amc"],
                defaults["category"], defaults["plan"], defaults["option_type"],
                defaults["first_seen"], defaults["last_seen"],
            ),
        )


def insert_navs(db_path: Path, scheme_code: int, series: list[tuple[str, float]]):
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO nav_history (scheme_code, nav_date, nav) VALUES (?, ?, ?)",
            [(scheme_code, d, n) for d, n in series],
        )


def write_ledger(path: Path, txns: list[dict]):
    path.write_text(json.dumps(txns))


class TestEquityClassification(unittest.TestCase):
    def test_equity_categories(self):
        for cat in [
            "Equity Scheme - Large Cap Fund",
            "Equity Scheme - Mid Cap Fund",
            "Equity Scheme - Flexi Cap Fund",
            "Equity Scheme - ELSS",
        ]:
            self.assertTrue(is_equity_for_drawdown(cat))

    def test_non_equity_default(self):
        for cat in [
            "Debt Scheme - Short Duration Fund",
            "Hybrid Scheme - Multi Asset Allocation",
            "Hybrid Scheme - Aggressive Hybrid Fund",
            "Other Scheme - Gold ETF",
            None,
            "",
        ]:
            self.assertFalse(is_equity_for_drawdown(cat), cat)

    def test_index_funds_count_as_equity(self):
        # Equity index funds live under "Other Scheme - Index Funds" in AMFI
        # vocab — they are full-volatility equity exposure and MUST count
        # toward the §6.4 drawdown gate. Regression for prior silent miss.
        cat = "Other Scheme - Index Funds"
        for name in [
            "Motilal Oswal Nifty Midcap 150 Index Fund - Direct Plan",
            "Motilal Oswal Nifty Smallcap 250 Index Fund - Direct Plan",
            "UTI Nifty 50 Index Fund Direct Growth",
            "HDFC Nifty Next 50 Index Fund - Direct Plan",
        ]:
            self.assertTrue(is_equity_for_drawdown(cat, name), f"{name} should be equity")

    def test_debt_index_funds_are_not_equity(self):
        # Gilt/G-Sec/Bharat Bond/constant-maturity index funds also live under
        # "Other Scheme - Index Funds" — they are debt and must NOT count.
        cat = "Other Scheme - Index Funds"
        for name in [
            "Bharat Bond ETF - April 2031",
            "ICICI Prudential Nifty G-Sec Index Fund",
            "Edelweiss Nifty PSU Bond Plus SDL Index Fund 2026",
            "SBI Nifty 10 Yr G-Sec Constant Maturity Index Fund",
        ]:
            self.assertFalse(is_equity_for_drawdown(cat, name), f"{name} should NOT be equity")

    def test_overseas_fof_counts_as_equity(self):
        # International equity FoFs default to equity classification.
        cat = "Other Scheme - FoF Overseas"
        self.assertTrue(is_equity_for_drawdown(cat, "Motilal Oswal Nasdaq 100 FOF - Direct"))
        self.assertTrue(is_equity_for_drawdown(cat, "Mirae Asset NYSE FANG+ ETF FoF - Direct"))

    def test_gold_fof_via_name_disambiguation(self):
        # SBI GOLD FUND is categorised "Other Scheme - FoF Domestic" — must
        # classify as gold (not equity) via name-based disambiguation.
        self.assertEqual(
            classify_sleeve("Other Scheme - FoF Domestic", "SBI GOLD FUND - DIRECT PLAN - GROWTH"),
            "gold",
        )
        self.assertFalse(
            is_equity_for_drawdown("Other Scheme - FoF Domestic", "SBI GOLD FUND - DIRECT PLAN - GROWTH")
        )

    def test_hybrid_equity_oriented_optin(self):
        cat = "Hybrid Scheme - Multi Asset Allocation"
        self.assertFalse(is_equity_for_drawdown(cat, include_hybrid_equity_oriented=False))
        self.assertTrue(is_equity_for_drawdown(cat, include_hybrid_equity_oriented=True))

    def test_hybrid_equity_savings_canonical_string(self):
        # AMFI canonical category is "Hybrid Scheme - Equity Savings" (no
        # "Fund" suffix). The opt-in must include it. Regression for the
        # SEBI-vocab typo that silently excluded it before.
        cat = "Hybrid Scheme - Equity Savings"
        self.assertFalse(is_equity_for_drawdown(cat, include_hybrid_equity_oriented=False))
        self.assertTrue(is_equity_for_drawdown(cat, include_hybrid_equity_oriented=True))

    def test_hybrid_conservative_excluded_even_with_optin(self):
        # Conservative Hybrid is debt-oriented (≤25% equity) — must NOT count
        # even when the equity-oriented opt-in is enabled.
        cat = "Hybrid Scheme - Conservative Hybrid Fund"
        self.assertFalse(is_equity_for_drawdown(cat, include_hybrid_equity_oriented=True))


class TestPeakAndDrawdown(unittest.TestCase):
    def setUp(self):
        self.db = make_temp_db()
        insert_scheme(self.db, 100)

    def test_peak_nav_in_window(self):
        # Peak in middle, latest at lower NAV
        series = [
            ("2025-05-01", 100.0),
            ("2025-08-01", 150.0),  # peak
            ("2025-12-01", 130.0),
            ("2026-05-08", 120.0),  # latest, 20% drawdown
        ]
        insert_navs(self.db, 100, series)
        pk = peak_nav(100, db_path=self.db)
        self.assertEqual(pk, ("2025-08-01", 150.0))

    def test_drawdown_negative(self):
        series = [
            ("2025-05-01", 100.0),
            ("2025-08-01", 150.0),
            ("2026-05-08", 120.0),
        ]
        insert_navs(self.db, 100, series)
        dd = current_drawdown(100, db_path=self.db)
        self.assertIsNotNone(dd)
        self.assertAlmostEqual(dd["drawdown"], -0.20, places=4)
        self.assertEqual(dd["peak_date"], "2025-08-01")
        self.assertEqual(dd["latest_date"], "2026-05-08")

    def test_drawdown_zero_at_peak(self):
        series = [
            ("2025-05-01", 100.0),
            ("2026-05-08", 150.0),  # latest is the peak
        ]
        insert_navs(self.db, 100, series)
        dd = current_drawdown(100, db_path=self.db)
        self.assertAlmostEqual(dd["drawdown"], 0.0, places=4)

    def test_lookback_excludes_old_peak(self):
        # Peak 3 years ago, but lookback is 730 days (2 years)
        series = [
            ("2022-01-01", 200.0),  # outside 2-year window
            ("2025-01-01", 100.0),
            ("2026-05-08", 120.0),
        ]
        insert_navs(self.db, 100, series)
        dd = current_drawdown(100, lookback_days=730, db_path=self.db)
        # Within window: peak is 120 (latest); drawdown 0
        self.assertAlmostEqual(dd["drawdown"], 0.0, places=4)
        # Wider lookback picks up the older peak
        dd = current_drawdown(100, lookback_days=2000, db_path=self.db)
        self.assertAlmostEqual(dd["drawdown"], -0.40, places=4)

    def test_no_history_returns_none(self):
        insert_scheme(self.db, 200)
        self.assertIsNone(peak_nav(200, db_path=self.db))
        self.assertIsNone(current_drawdown(200, db_path=self.db))


class TestAggregateDrawdown(unittest.TestCase):
    def setUp(self):
        self.db = make_temp_db()
        self.ledger = Path(tempfile.mktemp(suffix=".json"))

    def _setup_two_equity(self):
        insert_scheme(self.db, 100, category="Equity Scheme - Large Cap Fund")
        insert_scheme(self.db, 200, category="Equity Scheme - Mid Cap Fund")
        insert_scheme(self.db, 300, category="Debt Scheme - Short Duration Fund")
        # Scheme 100: 10% drawdown
        insert_navs(self.db, 100, [
            ("2025-08-01", 100.0), ("2026-05-08", 90.0),
        ])
        # Scheme 200: 30% drawdown
        insert_navs(self.db, 200, [
            ("2025-08-01", 100.0), ("2026-05-08", 70.0),
        ])
        # Scheme 300: irrelevant (debt)
        insert_navs(self.db, 300, [
            ("2025-08-01", 50.0), ("2026-05-08", 53.0),
        ])

    def test_value_weighted_aggregate(self):
        self._setup_two_equity()
        # Equal value in 100 and 200 → average 20% drawdown → blocks
        write_ledger(self.ledger, [
            {"txn_id": "1", "date": "2026-04-01", "type": "purchase", "scheme_code": 100,
             "scheme_name": "Sch 100", "amount_inr": 9000.0, "nav": 90.0, "units": 100.0,
             "sub_portfolio": "father", "source": "backfill"},
            {"txn_id": "2", "date": "2026-04-01", "type": "purchase", "scheme_code": 200,
             "scheme_name": "Sch 200", "amount_inr": 7000.0, "nav": 70.0, "units": 100.0,
             "sub_portfolio": "father", "source": "backfill"},
            # Debt holding — must be excluded
            {"txn_id": "3", "date": "2026-04-01", "type": "purchase", "scheme_code": 300,
             "scheme_name": "Sch 300", "amount_inr": 5300.0, "nav": 53.0, "units": 100.0,
             "sub_portfolio": "father", "source": "backfill"},
        ])
        result = aggregate_equity_drawdown(
            sub_portfolio="father", ledger_path=self.ledger, db_path=self.db,
        )
        # Total equity value = 9000 + 7000 = 16000
        self.assertAlmostEqual(result["total_equity_value_inr"], 16000.0, places=2)
        # Weighted drawdown: (9000 * -0.10 + 7000 * -0.30) / 16000 = -0.1875
        self.assertAlmostEqual(result["weighted_drawdown"], -0.1875, places=4)
        self.assertFalse(result["block_at_minus_20pct"])
        self.assertEqual(len(result["schemes"]), 2)
        # Excludes debt
        self.assertNotIn(300, [s["scheme_code"] for s in result["schemes"]])

    def test_block_triggers_at_20pct(self):
        self._setup_two_equity()
        # Heavier weight on the deeper-drawdown scheme → cross threshold
        write_ledger(self.ledger, [
            {"txn_id": "1", "date": "2026-04-01", "type": "purchase", "scheme_code": 100,
             "scheme_name": "Sch 100", "amount_inr": 1000.0, "nav": 90.0, "units": 11.11,
             "sub_portfolio": "father", "source": "backfill"},
            {"txn_id": "2", "date": "2026-04-01", "type": "purchase", "scheme_code": 200,
             "scheme_name": "Sch 200", "amount_inr": 9000.0, "nav": 70.0, "units": 128.57,
             "sub_portfolio": "father", "source": "backfill"},
        ])
        result = aggregate_equity_drawdown(
            sub_portfolio="father", ledger_path=self.ledger, db_path=self.db,
        )
        # Weighted: (~1000 * -0.10 + ~9000 * -0.30) / ~10000 = -0.28
        self.assertLess(result["weighted_drawdown"], -0.20)
        self.assertTrue(result["block_at_minus_20pct"])

    def test_empty_ledger_returns_zero(self):
        write_ledger(self.ledger, [])
        result = aggregate_equity_drawdown(
            sub_portfolio="father", ledger_path=self.ledger, db_path=self.db,
        )
        self.assertEqual(result["total_equity_value_inr"], 0.0)
        self.assertFalse(result["block_at_minus_20pct"])

    def test_missing_nav_history_flagged(self):
        # Regression: an equity holding with units > 0 but no NAV history is
        # silently dropped from the value-weighted drawdown (because cv has
        # current_value_inr=None). That distortion must surface via
        # `missing_history` so callers know the gate may understate.
        insert_scheme(self.db, 100, category="Equity Scheme - Large Cap Fund")
        # No nav_history for 100
        write_ledger(self.ledger, [
            {"txn_id": "1", "date": "2026-04-01", "type": "purchase", "scheme_code": 100,
             "scheme_name": "Sch 100", "amount_inr": 1000.0, "nav": 50.0, "units": 20.0,
             "sub_portfolio": "father", "source": "backfill"},
        ])
        result = aggregate_equity_drawdown(
            sub_portfolio="father", ledger_path=self.ledger, db_path=self.db,
        )
        # Holding with no history is excluded from value but MUST be flagged
        self.assertEqual(result["total_equity_value_inr"], 0.0)
        self.assertEqual(result["missing_history"], [100])
        # And it must NOT be classified as block_at_minus_20pct (we have no
        # signal — better to surface than to fabricate)
        self.assertFalse(result["block_at_minus_20pct"])

    def test_redeemed_equity_not_flagged(self):
        # If the user has fully redeemed an equity holding (units == 0), it
        # should NOT show up in missing_history — the holding doesn't exist
        # any more, and flagging it would be noise.
        insert_scheme(self.db, 100, category="Equity Scheme - Large Cap Fund")
        write_ledger(self.ledger, [
            {"txn_id": "1", "date": "2026-04-01", "type": "purchase", "scheme_code": 100,
             "scheme_name": "Sch 100", "amount_inr": 1000.0, "nav": 50.0, "units": 20.0,
             "sub_portfolio": "father", "source": "backfill"},
            {"txn_id": "2", "date": "2026-04-10", "type": "redemption", "scheme_code": 100,
             "scheme_name": "Sch 100", "amount_inr": -1100.0, "nav": 55.0, "units": -20.0,
             "sub_portfolio": "father", "source": "backfill"},
        ])
        result = aggregate_equity_drawdown(
            sub_portfolio="father", ledger_path=self.ledger, db_path=self.db,
        )
        self.assertEqual(result["missing_history"], [])


if __name__ == "__main__":
    unittest.main()
