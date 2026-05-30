#!/usr/bin/env python3
"""Tests for scripts/discover.py — Phase 0 dashboard correctness."""

from __future__ import annotations

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import discover  # noqa: E402
from lib import transactions as txns_mod  # noqa: E402


class TestRecurringStats(unittest.TestCase):
    """Regression: STP outflow key drift.

    The historical bug had discover.py reading `amount_inr` while
    plan_stp / recurring.json schema uses `amount_inr_per_tranche`. The
    reported outflow was always ₹0. Test against a synthetic recurring.json.
    """

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump({
            "sips": [
                {"sip_id": "sip1", "amount_inr": 5000, "status": "active"},
                {"sip_id": "sip2", "amount_inr": 7500, "status": "active"},
                {"sip_id": "sip-paused", "amount_inr": 9999, "status": "paused"},
            ],
            "stps": [
                {"stp_id": "stp1", "amount_inr_per_tranche": 50000, "status": "active"},
                {"stp_id": "stp2", "amount_inr_per_tranche": 25000, "status": "active"},
                {"stp_id": "stp-old", "amount_inr_per_tranche": 99999, "status": "ended-source-exhausted"},
            ],
        }, self.tmp)
        self.tmp.close()

        # Monkey-patch DEFAULT_RECURRING_PATH so load_recurring picks our fixture
        self._orig_path = txns_mod.DEFAULT_RECURRING_PATH
        txns_mod.DEFAULT_RECURRING_PATH = Path(self.tmp.name)

    def tearDown(self):
        txns_mod.DEFAULT_RECURRING_PATH = self._orig_path
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_stp_outflow_aggregates_amount_inr_per_tranche(self):
        stats = discover.recurring_stats()
        self.assertEqual(stats["active_stps"], 2)
        # 50000 + 25000 = 75000; the paused / ended-source-exhausted entry
        # must NOT be counted
        self.assertEqual(stats["total_stp_outflow_per_month"], 75000)

    def test_sip_outflow_unaffected(self):
        stats = discover.recurring_stats()
        self.assertEqual(stats["active_sips"], 2)
        self.assertEqual(stats["total_sip_outflow_per_month"], 12500)


class TestDecisionsLogOpenActions(unittest.TestCase):
    """Regression: the heuristic must recognize the resolution markers
    actually used in the household's log (`**RESOLVED <date>**`,
    `**Closed <date>**`) — not just `Status: acted`."""

    def setUp(self):
        self._orig_log = discover.DECISIONS_LOG
        self.tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
        self.tmp.write(
            "# Decisions log\n\n"
            "#### ACTION-2026-05-09-001 — Open PPF\n"
            "**Status:** acted\n\n"
            "#### ACTION-2026-05-09-002 — NPS\n"
            "**RESOLVED 2026-05-10** — closed by user.\n\n"
            "#### ACTION-2026-05-09-003 — SIP design\n"
            "**Status:** deferred\n\n"
            "#### ACTION-2026-05-09-004 — Tax regime\n"
            "Still under deliberation; no resolution yet.\n\n"
            "#### ACTION-2026-05-09-005 — Property goal\n"
            "**Closed 2026-05-08** — moved to portfolio.md.\n"
        )
        self.tmp.close()
        discover.DECISIONS_LOG = Path(self.tmp.name)

    def tearDown(self):
        discover.DECISIONS_LOG = self._orig_log
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_recognizes_resolved_and_closed(self):
        result = discover.decisions_log_open_actions()
        self.assertEqual(result["action_headers_total"], 5)
        # 1× "Status: acted" + 1× RESOLVED + 1× Closed = 3
        self.assertEqual(result["explicitly_acted"], 3)
        self.assertEqual(result["explicitly_deferred"], 1)


if __name__ == "__main__":
    unittest.main()
