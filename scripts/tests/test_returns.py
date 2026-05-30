#!/usr/bin/env python3
"""Tests for scripts/lib/returns.py."""

from __future__ import annotations

import math
import sqlite3
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from lib.db import init_db  # noqa: E402
from lib.returns import (  # noqa: E402
    alpha_vs_benchmark,
    discover_benchmark_for_category,
    tracking_error,
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


def make_daily_series(start: date, days: int, start_nav: float, daily_pct: float) -> list[tuple[str, float]]:
    """Generate daily NAV series compounding at `daily_pct` per step."""
    out = []
    nav = start_nav
    d = start
    for _ in range(days):
        out.append((d.isoformat(), nav))
        nav *= (1 + daily_pct)
        d += timedelta(days=1)
    return out


class TestBenchmarkDiscovery(unittest.TestCase):
    def test_known_categories(self):
        self.assertEqual(
            discover_benchmark_for_category("Equity Scheme - Large Cap Fund"), 120716
        )
        self.assertEqual(
            discover_benchmark_for_category("Equity Scheme - Mid Cap Fund"), 147622
        )
        self.assertEqual(
            discover_benchmark_for_category("Equity Scheme - Small Cap Fund"), 147623
        )

    def test_unknown_category_returns_none(self):
        self.assertIsNone(discover_benchmark_for_category("Debt Scheme - Liquid Fund"))
        self.assertIsNone(discover_benchmark_for_category(None))


class TestAlpha(unittest.TestCase):
    def setUp(self):
        self.db = make_temp_db()
        # Fund: starts at 100, 2 years later at 144 → ~20% CAGR
        # Benchmark: starts at 50, 2 years later at 60.5 → ~10% CAGR
        # Alpha ≈ 10pp
        insert_navs(self.db, 1, [
            ("2024-05-08", 100.0),
            ("2026-05-08", 144.0),
        ])
        insert_navs(self.db, 2, [
            ("2024-05-08", 50.0),
            ("2026-05-08", 60.5),
        ])

    def test_alpha_positive(self):
        r = alpha_vs_benchmark(1, 2, period_days=730, db_path=self.db)
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r["fund_return"], 0.20, places=2)
        self.assertAlmostEqual(r["benchmark_return"], 0.10, places=2)
        self.assertAlmostEqual(r["alpha"], 0.10, places=2)

    def test_alpha_none_when_missing(self):
        r = alpha_vs_benchmark(1, 999, period_days=730, db_path=self.db)
        self.assertIsNone(r)


class TestTrackingError(unittest.TestCase):
    def setUp(self):
        self.db = make_temp_db()

    def test_zero_when_perfect_tracker(self):
        # Both schemes follow exactly the same daily returns
        series_a = make_daily_series(date(2025, 1, 1), 365, 100.0, 0.0005)
        series_b = make_daily_series(date(2025, 1, 1), 365, 50.0, 0.0005)
        insert_navs(self.db, 1, series_a)
        insert_navs(self.db, 2, series_b)
        te = tracking_error(1, 2, period_days=400, db_path=self.db)
        self.assertIsNotNone(te)
        self.assertLess(te["annualised_te"], 1e-6)

    def test_nonzero_with_drift(self):
        # Fund deviates by random-ish daily noise
        import random
        random.seed(42)
        d = date(2025, 1, 1)
        a, b = 100.0, 50.0
        series_a, series_b = [], []
        for _ in range(365):
            series_a.append((d.isoformat(), a))
            series_b.append((d.isoformat(), b))
            # Same drift but fund has additional noise
            base = 0.0005
            a *= (1 + base + random.gauss(0, 0.002))
            b *= (1 + base)
            d += timedelta(days=1)
        insert_navs(self.db, 10, series_a)
        insert_navs(self.db, 11, series_b)
        te = tracking_error(10, 11, period_days=400, db_path=self.db)
        self.assertIsNotNone(te)
        # Daily noise stdev ~0.002 → annualised ~0.002 * sqrt(252) ≈ 0.032 (3.2%)
        self.assertGreater(te["annualised_te"], 0.02)
        self.assertLess(te["annualised_te"], 0.05)
        self.assertGreater(te["n_overlapping_days"], 300)

    def test_none_when_insufficient_overlap(self):
        # Schemes with no overlapping dates
        insert_navs(self.db, 20, [(d.isoformat(), 100.0) for d in [date(2025, 1, 1)]])
        insert_navs(self.db, 21, [(d.isoformat(), 50.0) for d in [date(2025, 6, 1)]])
        te = tracking_error(20, 21, period_days=730, db_path=self.db)
        self.assertIsNone(te)


if __name__ == "__main__":
    unittest.main()
