#!/usr/bin/env python3
"""Tests for scripts/lib/projection.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from lib.projection import (  # noqa: E402
    LumpReceipt,
    DEFAULT_REAL_RETURN_SCENARIOS,
    goal_progress,
    project_corpus,
    project_drift,
)


class TestProjectDrift(unittest.TestCase):
    def test_father_post_5_5l_lump_one_year(self):
        # Real scenario: father starts at 21/67/12/0, applies the recommended flows,
        # projected one year forward
        current = {"equity": 355250, "debt": 1148000, "gold": 0, "hybrid": 200000}
        flows = {"equity": 450000, "debt": 0, "gold": 30000, "hybrid": 70000}
        result = project_drift(current, flows, months=12)
        # After flow, equity should be 805250
        self.assertEqual(
            result["sleeve_projections"]["equity"]["after_flow"], 805250
        )
        # Project equity at 5%: 805250 * 1.05 = 845512.5
        self.assertAlmostEqual(
            result["sleeve_projections"]["equity"]["projected"], 845512.5, places=0
        )
        # Total after flow = 17.03L + 5.5L = 22.53L
        self.assertEqual(result["totals"]["after_flow"], 2253250)

    def test_zero_months_returns_no_growth(self):
        current = {"equity": 1000}
        flows = {"equity": 500}
        result = project_drift(current, flows, months=0)
        self.assertEqual(
            result["sleeve_projections"]["equity"]["projected"], 1500
        )

    def test_pct_sums_to_one(self):
        result = project_drift(
            {"equity": 1000, "debt": 1000}, {"equity": 0, "debt": 0}, months=12,
        )
        total_pct = sum(result["projected_pct"].values())
        self.assertAlmostEqual(total_pct, 1.0, places=4)

    def test_effective_equity_includes_hybrid(self):
        current = {"equity": 100, "hybrid": 100}
        flows = {"equity": 0, "hybrid": 0}
        result = project_drift(current, flows, months=0, hybrid_equity_weight=0.65)
        # equity 100 + 0.65 * 100 = 165 / 200 = 82.5%
        self.assertAlmostEqual(result["effective_equity_pct"], 0.825, places=4)


class TestProjectCorpus(unittest.TestCase):
    def test_simple_compounding_no_flow(self):
        # 100 at 12% for 1 year → 112.68 (monthly compounding)
        result = project_corpus(
            start_value_inr=100,
            monthly_flow_inr=0,
            target_date="2027-05-10",
            real_return_pct=0.12,
            today="2026-05-10",
        )
        self.assertEqual(result["months"], 12)
        self.assertAlmostEqual(result["single_scenario"], 112.68, places=2)

    def test_with_monthly_flow(self):
        result = project_corpus(
            start_value_inr=0,
            monthly_flow_inr=10000,
            target_date="2027-05-10",
            real_return_pct=0.12,
            today="2026-05-10",
        )
        # 12 contributions of 10K growing — each month's contribution gets
        # different number of compounding periods
        # Simple sanity: total contributions = 120000, with growth should exceed
        self.assertGreater(result["single_scenario"], 120000)
        self.assertLess(result["single_scenario"], 130000)

    def test_lump_schedule(self):
        lumps = [
            LumpReceipt(date="2026-08-10", amount_inr=100000),
            LumpReceipt(date="2027-02-10", amount_inr=200000),
        ]
        result = project_corpus(
            start_value_inr=0,
            monthly_flow_inr=0,
            target_date="2027-05-10",
            real_return_pct=0.0,
            lump_schedule=lumps,
            today="2026-05-10",
        )
        # 0% return; both lumps should show up
        self.assertEqual(result["single_scenario"], 300000)

    def test_scenario_dict(self):
        result = project_corpus(
            start_value_inr=100,
            monthly_flow_inr=0,
            target_date="2027-05-10",
            real_return_pct=DEFAULT_REAL_RETURN_SCENARIOS,
            today="2026-05-10",
        )
        self.assertIn("base", result["scenarios"])
        self.assertIn("optimistic", result["scenarios"])
        self.assertIn("pessimistic", result["scenarios"])
        self.assertGreater(
            result["scenarios"]["optimistic"]["final_corpus_inr"],
            result["scenarios"]["pessimistic"]["final_corpus_inr"],
        )

    def test_invalid_target_date_raises(self):
        with self.assertRaises(ValueError):
            project_corpus(
                start_value_inr=100, monthly_flow_inr=0,
                target_date="2024-01-01", today="2026-05-10",
            )


class TestGoalProgress(unittest.TestCase):
    def test_retirement_scenario(self):
        # User retirement: start ₹6.43L, ₹2L/month flow, target ₹12 Cr by 2051
        result = goal_progress(
            current_corpus_inr=643000,
            target_corpus_inr=120000000,
            target_date="2051-05-10",
            monthly_flow_inr=200000,
            real_return_pct=DEFAULT_REAL_RETURN_SCENARIOS,
            today="2026-05-10",
        )
        # Should land in the ballpark — base scenario is achievable per goals.md
        for name, info in result["scenarios"].items():
            self.assertIn("pct_of_target", info)
            self.assertIn("shortfall_inr", info)
            self.assertGreater(info["pct_of_target"], 0.5)


if __name__ == "__main__":
    unittest.main()
