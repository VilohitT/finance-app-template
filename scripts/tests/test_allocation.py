#!/usr/bin/env python3
"""Tests for scripts/lib/allocation.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from lib.allocation import optimal_sleeve_split  # noqa: E402


class TestOptimalSleeveSplit(unittest.TestCase):
    def test_father_5_5l_lump_real_scenario(self):
        """The actual case from the conversation: father at 21/67/12/0, target 65/30/5."""
        current = {"equity": 355250, "debt": 1148000, "gold": 0, "hybrid": 200000}
        targets = {"equity": 0.65, "debt": 0.30, "gold": 0.05}
        result = optimal_sleeve_split(current, targets, new_money=550000)
        flows = result["flows"]
        # Bulk should go to equity (the biggest gap)
        self.assertGreater(flows["equity"], 400000)
        # Debt is over-allocated → zero flow
        self.assertEqual(flows.get("debt", 0), 0)
        # Gold has small gap → small flow
        self.assertGreater(flows.get("gold", 0), 0)
        self.assertLess(flows.get("gold", 0), 200000)
        # Sums to 5.5L
        self.assertAlmostEqual(sum(flows.values()), 550000, places=0)

    def test_zero_flow_to_overallocated(self):
        current = {"equity": 100, "debt": 900}  # 10/90 vs target 50/50
        targets = {"equity": 0.50, "debt": 0.50}
        result = optimal_sleeve_split(current, targets, new_money=100)
        # Debt over-allocated → zero flow
        self.assertEqual(result["flows"].get("debt", 0), 0)
        # All flow to equity
        self.assertEqual(result["flows"]["equity"], 100)

    def test_pro_rata_distribution(self):
        # Both sleeves under-allocated; should split pro-rata to gap
        current = {"equity": 0, "debt": 0}  # both at 0
        targets = {"equity": 0.70, "debt": 0.30}
        result = optimal_sleeve_split(current, targets, new_money=1000)
        # 70/30 split
        self.assertAlmostEqual(result["flows"]["equity"], 700, places=0)
        self.assertAlmostEqual(result["flows"]["debt"], 300, places=0)

    def test_sums_to_new_money_exactly(self):
        current = {"equity": 1000, "debt": 500, "gold": 100}
        targets = {"equity": 0.60, "debt": 0.30, "gold": 0.10}
        for amt in [100, 1234.56, 999999, 5500000]:
            result = optimal_sleeve_split(current, targets, new_money=amt)
            self.assertAlmostEqual(
                sum(result["flows"].values()), amt, places=2,
                msg=f"Failed sum check for new_money={amt}",
            )

    def test_excluded_sleeve_gets_zero(self):
        current = {"equity": 100, "debt": 100, "ppf": 50}
        targets = {"equity": 0.60, "debt": 0.30, "ppf": 0.10}
        result = optimal_sleeve_split(current, targets, new_money=1000, exclude_sleeves={"ppf"})
        self.assertEqual(result["flows"].get("ppf", 0), 0)
        # Money redistributes to equity + debt
        self.assertAlmostEqual(
            result["flows"]["equity"] + result["flows"]["debt"], 1000, places=2
        )

    def test_post_deployment_projection(self):
        current = {"equity": 0, "debt": 0}
        targets = {"equity": 1.0}
        result = optimal_sleeve_split(current, targets, new_money=1000)
        post = result["post_deployment"]
        self.assertAlmostEqual(post["after_inr"]["equity"], 1000, places=2)
        self.assertAlmostEqual(post["after_pct"]["equity"], 1.0, places=4)
        self.assertAlmostEqual(post["total_inr"], 1000, places=2)

    def test_hybrid_counted_as_partial_equity(self):
        current = {"equity": 0, "hybrid": 1000}
        targets = {"equity": 1.0}
        result = optimal_sleeve_split(current, targets, new_money=0, hybrid_equity_weight=0.65)
        post = result["post_deployment"]
        # 1000 hybrid * 0.65 = 650 effective equity
        self.assertAlmostEqual(post["effective_equity_inr"], 650, places=2)

    def test_target_validation(self):
        with self.assertRaises(ValueError):
            optimal_sleeve_split({}, {"equity": 0.5, "debt": 0.4}, new_money=100)
        with self.assertRaises(ValueError):
            optimal_sleeve_split({}, {"equity": 0.5, "debt": 0.5}, new_money=-1)

    def test_no_underallocation_parks_residual(self):
        # Already at target; new money has nowhere underallocated to go
        current = {"equity": 700, "debt": 300}
        targets = {"equity": 0.70, "debt": 0.30}
        result = optimal_sleeve_split(current, targets, new_money=100)
        # Should park residual in highest-target sleeve (equity)
        self.assertEqual(sum(result["flows"].values()), 100)

    def test_minimum_floor(self):
        current = {"equity": 100, "debt": 100, "gold": 0}
        targets = {"equity": 0.50, "debt": 0.40, "gold": 0.10}
        # Tiny new_money but want gold to get at least 10
        result = optimal_sleeve_split(current, targets, new_money=100, minimum_floor_inr=10)
        self.assertGreaterEqual(result["flows"].get("gold", 0), 10)

    def test_minimum_floor_under_tight_money(self):
        # New money smaller than the floor across all under-funded sleeves —
        # everyone gets a fractional share rather than zero.
        current = {"equity": 0, "debt": 0, "gold": 0}
        targets = {"equity": 0.50, "debt": 0.30, "gold": 0.20}
        result = optimal_sleeve_split(
            current, targets, new_money=300, minimum_floor_inr=1000,
        )
        # All three sleeves should receive something
        for k in ("equity", "debt", "gold"):
            self.assertGreater(result["flows"].get(k, 0), 0)
        self.assertAlmostEqual(sum(result["flows"].values()), 300, places=2)

    def test_minimum_floor_capped_by_gap(self):
        # Floor of 1000 but gold's gap is only 50 — flow must not exceed gap.
        current = {"equity": 0, "debt": 0, "gold": 950}
        targets = {"equity": 0.50, "debt": 0.40, "gold": 0.10}
        # Total = 950, target gold = 95. Already over target. Floor should not
        # push it above gap (which is negative → 0).
        result = optimal_sleeve_split(
            current, targets, new_money=1000, minimum_floor_inr=1000,
        )
        self.assertEqual(result["flows"].get("gold", 0), 0)

    def test_all_excluded_with_money_raises(self):
        # Regression for the "silent money loss" bug — if every sleeve named in
        # current/targets is excluded AND new_money > 0, the function must
        # raise rather than return flows summing to 0 (which silently drops
        # the money).
        with self.assertRaises(ValueError):
            optimal_sleeve_split(
                {"equity": 100, "debt": 100},
                {"equity": 0.5, "debt": 0.5},
                new_money=100,
                exclude_sleeves={"equity", "debt"},
            )
        # new_money=0 with all excluded is a legitimate no-op and must not raise
        result = optimal_sleeve_split(
            {"equity": 100, "debt": 100},
            {"equity": 0.5, "debt": 0.5},
            new_money=0,
            exclude_sleeves={"equity", "debt"},
        )
        self.assertEqual(sum(result["flows"].values()), 0)


if __name__ == "__main__":
    unittest.main()
