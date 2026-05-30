#!/usr/bin/env python3
"""Tests for scripts/lib/stp_plan.py."""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from lib.db import init_db  # noqa: E402
from lib.stp_plan import (  # noqa: E402
    plan_lump_purchase,
    plan_stp,
    should_use_stp,
    STP_THRESHOLD_INR,
)


def make_temp_db() -> Path:
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    init_db(f.name)
    return Path(f.name)


def insert_navs(db_path: Path, scheme_code: int, series: list[tuple[str, float]]):
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO nav_history (scheme_code, nav_date, nav) VALUES (?, ?, ?)",
            [(scheme_code, d, n) for d, n in series],
        )


def write_ledger(path: Path, txns: list[dict]):
    path.write_text(json.dumps(txns))


class TestShouldUseStp(unittest.TestCase):
    def test_threshold(self):
        self.assertFalse(should_use_stp(50000))
        self.assertFalse(should_use_stp(STP_THRESHOLD_INR - 1))
        self.assertTrue(should_use_stp(STP_THRESHOLD_INR))
        self.assertTrue(should_use_stp(500000))


class TestPlanLumpPurchase(unittest.TestCase):
    def setUp(self):
        self.db = make_temp_db()
        self.ledger = Path(tempfile.mktemp(suffix=".json"))
        write_ledger(self.ledger, [])
        insert_navs(self.db, 122639, [
            ("2026-05-08", 91.5245),
        ])

    def test_basic_purchase(self):
        result = plan_lump_purchase(
            amount_inr=170000,
            scheme_code=122639,
            scheme_name="PPFCF",
            sub_portfolio="father",
            purchase_date="2026-05-10",
            db_path=self.db,
            ledger_path=self.ledger,
        )
        self.assertEqual(result["type"], "purchase")
        self.assertEqual(result["scheme_code"], 122639)
        self.assertEqual(result["amount_inr"], 170000.0)
        self.assertAlmostEqual(result["nav"], 91.5245, places=4)
        self.assertAlmostEqual(result["units"], 170000 / 91.5245, places=2)
        self.assertEqual(result["sub_portfolio"], "father")
        self.assertEqual(result["source"], "user-dictated")

    def test_explicit_nav_overrides(self):
        result = plan_lump_purchase(
            amount_inr=10000, scheme_code=122639, scheme_name="PPFCF",
            sub_portfolio="father", purchase_date="2026-05-10",
            nav=100.0, db_path=self.db, ledger_path=self.ledger,
        )
        self.assertEqual(result["nav"], 100.0)
        self.assertEqual(result["units"], 100.0)

    def test_invalid_sub_portfolio(self):
        with self.assertRaises(ValueError):
            plan_lump_purchase(
                amount_inr=1000, scheme_code=122639, scheme_name="PPFCF",
                sub_portfolio="invalid", db_path=self.db, ledger_path=self.ledger,
            )

    def test_no_nav_raises(self):
        with self.assertRaises(ValueError):
            plan_lump_purchase(
                amount_inr=1000, scheme_code=999999, scheme_name="ghost",
                sub_portfolio="father", db_path=self.db, ledger_path=self.ledger,
            )


class TestPlanStp(unittest.TestCase):
    def setUp(self):
        self.db = make_temp_db()
        self.ledger = Path(tempfile.mktemp(suffix=".json"))
        write_ledger(self.ledger, [])
        # Arbitrage parking source
        insert_navs(self.db, 118931, [("2026-05-08", 33.72)])
        # Destination index fund
        insert_navs(self.db, 120716, [("2026-05-08", 169.01)])

    def test_real_scenario_father_4_5l_6mo(self):
        result = plan_stp(
            lump_inr=450000,
            source_scheme_code=118931,
            source_scheme_name="HDFC Arbitrage Direct",
            dest_scheme_code=120716,
            dest_scheme_name="UTI Nifty 50 Direct",
            months=6,
            sub_portfolio="father",
            source_tax_category="equity",
            start_date="2026-05-15",
            day_of_month=15,
            parking_purchase_date="2026-05-10",
            db_path=self.db,
            ledger_path=self.ledger,
        )
        self.assertEqual(result["monthly_amount_inr"], 75000.0)
        self.assertEqual(result["total_inr"], 450000.0)
        self.assertEqual(len(result["schedule"]), 6)
        self.assertEqual(result["schedule"][0], "2026-05-15")
        self.assertEqual(result["schedule"][5], "2026-10-15")
        self.assertEqual(result["recurring_stp"]["stp_id"],
                         "STP-2026-05-15-118931-to-120716")
        self.assertEqual(result["recurring_stp"]["amount_inr_per_tranche"], 75000.0)
        self.assertEqual(result["recurring_stp"]["start_date"], "2026-05-15")
        self.assertEqual(result["recurring_stp"]["end_date"], "2026-10-15")
        # Parking purchase well-formed
        self.assertEqual(result["parking_purchase"]["amount_inr"], 450000.0)
        self.assertEqual(result["parking_purchase"]["scheme_code"], 118931)
        # Schema regression: every key the runner reads must be present
        # (recurring_runner.py walks: stp_id, source_scheme_code, source_scheme_name,
        # destination_scheme_code, destination_scheme_name, amount_inr_per_tranche,
        # frequency, day_of_month, start_date, end_date, sub_portfolio,
        # source_tax_category, stop_when_source_exhausted, status, exit_load).
        runner_required_keys = {
            "stp_id", "source_scheme_code", "source_scheme_name",
            "destination_scheme_code", "destination_scheme_name",
            "amount_inr_per_tranche", "frequency", "day_of_month",
            "start_date", "end_date", "sub_portfolio",
            "source_tax_category", "stop_when_source_exhausted",
            "status", "exit_load",
        }
        self.assertTrue(
            runner_required_keys.issubset(result["recurring_stp"].keys()),
            f"missing keys: {runner_required_keys - result['recurring_stp'].keys()}",
        )

    def test_month_end_day_snap(self):
        # Start Jan 31 with day_of_month=31 → Feb 28/29 etc.
        result = plan_stp(
            lump_inr=60000,
            source_scheme_code=118931,
            source_scheme_name="HDFC Arbitrage",
            dest_scheme_code=120716,
            dest_scheme_name="UTI Nifty 50",
            months=3,
            sub_portfolio="father",
            source_tax_category="equity",
            start_date="2027-01-31",
            day_of_month=31,
            db_path=self.db,
            ledger_path=self.ledger,
        )
        self.assertEqual(result["schedule"][0], "2027-01-31")
        # Feb 2027 is not a leap year → 28
        self.assertEqual(result["schedule"][1], "2027-02-28")
        self.assertEqual(result["schedule"][2], "2027-03-31")

    def test_invalid_months(self):
        with self.assertRaises(ValueError):
            plan_stp(
                lump_inr=10000, source_scheme_code=118931,
                source_scheme_name="A", dest_scheme_code=120716, dest_scheme_name="B",
                months=0, sub_portfolio="father", source_tax_category="equity",
                db_path=self.db, ledger_path=self.ledger,
            )
        with self.assertRaises(ValueError):
            plan_stp(
                lump_inr=10000, source_scheme_code=118931,
                source_scheme_name="A", dest_scheme_code=120716, dest_scheme_name="B",
                months=24, sub_portfolio="father", source_tax_category="equity",
                db_path=self.db, ledger_path=self.ledger,
            )

    def test_invalid_tax_category(self):
        with self.assertRaises(ValueError):
            plan_stp(
                lump_inr=10000, source_scheme_code=118931,
                source_scheme_name="A", dest_scheme_code=120716, dest_scheme_name="B",
                months=3, sub_portfolio="father", source_tax_category="bogus",
                db_path=self.db, ledger_path=self.ledger,
            )

    def test_residual_absorbed_by_final_tranche(self):
        # Regression: 500000 / 6 = 83333.33 × 6 = 499999.98 — historical bug
        # left ₹0.02 stuck in the parking source forever. The fix: emit
        # `final_tranche_amount_inr` so the runner pays it on the last tranche
        # and the parking source drains exactly.
        result = plan_stp(
            lump_inr=500000,
            source_scheme_code=118931, source_scheme_name="X",
            dest_scheme_code=120716, dest_scheme_name="Y",
            months=6, sub_portfolio="user", source_tax_category="equity",
            start_date="2026-05-15", day_of_month=15,
            db_path=self.db, ledger_path=self.ledger,
        )
        self.assertEqual(result["monthly_amount_inr"], 83333.33)
        # The final tranche is the residual absorber
        self.assertAlmostEqual(result["final_tranche_amount_inr"], 83333.35, places=2)
        # And monthly × (months-1) + final_tranche must == lump_inr exactly
        total = (
            result["monthly_amount_inr"] * 5
            + result["final_tranche_amount_inr"]
        )
        self.assertAlmostEqual(total, 500000, places=2)
        self.assertEqual(result["total_inr"], 500000.0)
        # The recurring entry carries the override so the runner picks it up
        self.assertEqual(
            result["recurring_stp"]["final_tranche_amount_inr"],
            result["final_tranche_amount_inr"],
        )

    def test_no_residual_when_clean_division(self):
        # Sanity: when lump divides cleanly, final_tranche == monthly.
        result = plan_stp(
            lump_inr=600000,
            source_scheme_code=118931, source_scheme_name="X",
            dest_scheme_code=120716, dest_scheme_name="Y",
            months=6, sub_portfolio="user", source_tax_category="equity",
            start_date="2026-05-15", day_of_month=15,
            db_path=self.db, ledger_path=self.ledger,
        )
        self.assertEqual(result["monthly_amount_inr"], 100000.0)
        self.assertEqual(result["final_tranche_amount_inr"], 100000.0)


if __name__ == "__main__":
    unittest.main()
