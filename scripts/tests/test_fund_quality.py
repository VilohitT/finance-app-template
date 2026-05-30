#!/usr/bin/env python3
"""
Tests for scripts/lib/fund_quality.py and scripts/build_quality_template.py.

Covers:
- JSON loading (well-formed, malformed, missing, weird shapes)
- get_vintage / get_returns with synthetic NAV history
- get_quality merging (db + nav_history + JSON; conflict resolution)
- filter_candidates with various filter combos and rank fields
- Schema migration (adding aum columns to existing DB without data loss)
- build_quality_template bootstrap (idempotent, preserves prior entries)
"""

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

# Imports under test
from lib.fund_quality import (  # noqa: E402
    QUALITY_FIELDS,
    filter_candidates,
    get_quality,
    get_returns,
    get_vintage,
    load_quality,
)
from lib.db import init_db, get_conn  # noqa: E402


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def make_temp_db() -> Path:
    """Create an empty initialized DB, return its path."""
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    init_db(f.name)
    return Path(f.name)


def insert_scheme(db_path: Path, scheme_code: int, **fields) -> None:
    """Insert a row into the schemes table with sensible defaults."""
    defaults = dict(
        scheme_name=f"Test Scheme {scheme_code}",
        amc="Test AMC",
        category="Equity Scheme - Flexi Cap Fund",
        plan="Direct",
        option_type="Growth",
        first_seen="2020-01-01",
        last_seen="2026-05-08",
    )
    defaults.update(fields)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """INSERT INTO schemes (
                scheme_code, scheme_name, amc, category, plan, option_type,
                first_seen, last_seen, aum_crore, aum_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                scheme_code,
                defaults["scheme_name"],
                defaults["amc"],
                defaults["category"],
                defaults["plan"],
                defaults["option_type"],
                defaults["first_seen"],
                defaults["last_seen"],
                defaults.get("aum_crore"),
                defaults.get("aum_date"),
            ),
        )
        conn.commit()


def insert_nav_series(
    db_path: Path,
    scheme_code: int,
    start_date: date,
    end_date: date,
    start_nav: float,
    end_nav: float,
) -> None:
    """Insert a linear NAV progression from start_date/start_nav to end_date/end_nav."""
    days = (end_date - start_date).days
    if days <= 0:
        return
    daily_growth = (end_nav / start_nav) ** (1.0 / days)
    with sqlite3.connect(db_path) as conn:
        nav = start_nav
        for d in range(days + 1):
            current_date = start_date + timedelta(days=d)
            conn.execute(
                "INSERT OR IGNORE INTO nav_history (scheme_code, nav_date, nav) "
                "VALUES (?, ?, ?)",
                (scheme_code, current_date.isoformat(), nav),
            )
            nav *= daily_growth
        conn.commit()


# --------------------------------------------------------------------------
# load_quality
# --------------------------------------------------------------------------

class TestLoadQuality(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        self.tmp.close()
        self.path = Path(self.tmp.name)

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def write(self, obj):
        self.path.write_text(json.dumps(obj))

    def test_missing_file_returns_empty(self):
        self.path.unlink()
        self.assertEqual(load_quality(self.path), {})

    def test_empty_root_returns_empty(self):
        self.write({})
        self.assertEqual(load_quality(self.path), {})

    def test_well_formed_returns_int_keyed_dict(self):
        self.write({
            "_meta": {"schema_version": "1.0"},
            "schemes": {
                "122639": {"ter": 0.62, "manager_name": "X"},
                "108768": {"ter": 1.20},
            },
        })
        result = load_quality(self.path)
        self.assertEqual(set(result.keys()), {122639, 108768})
        self.assertEqual(result[122639]["ter"], 0.62)
        self.assertEqual(result[108768]["ter"], 1.20)

    def test_skips_null_entries(self):
        self.write({"schemes": {"100": {"ter": 0.5}, "200": None}})
        result = load_quality(self.path)
        self.assertEqual(set(result.keys()), {100})

    def test_skips_non_int_keys(self):
        self.write({"schemes": {"valid_122639": {"ter": 0.5}, "100": {"ter": 0.6}}})
        result = load_quality(self.path)
        self.assertEqual(set(result.keys()), {100})

    def test_handles_missing_schemes_block(self):
        self.write({"_meta": {}})
        self.assertEqual(load_quality(self.path), {})

    def test_handles_array_root(self):
        # Some user might mistakenly write the root as a list; treat as empty
        self.path.write_text("[1, 2, 3]")
        self.assertEqual(load_quality(self.path), {})


# --------------------------------------------------------------------------
# get_vintage
# --------------------------------------------------------------------------

class TestGetVintage(unittest.TestCase):
    def setUp(self):
        self.db = make_temp_db()

    def tearDown(self):
        self.db.unlink(missing_ok=True)

    def test_no_history_returns_none(self):
        insert_scheme(self.db, 100)
        self.assertIsNone(get_vintage(100, self.db))

    def test_returns_earliest_date(self):
        insert_scheme(self.db, 100)
        insert_nav_series(self.db, 100, date(2023, 1, 1), date(2026, 5, 8), 100.0, 150.0)
        self.assertEqual(get_vintage(100, self.db), "2023-01-01")

    def test_unknown_scheme_returns_none(self):
        # Scheme not in nav_history at all
        self.assertIsNone(get_vintage(99999, self.db))


# --------------------------------------------------------------------------
# get_returns
# --------------------------------------------------------------------------

class TestGetReturns(unittest.TestCase):
    def setUp(self):
        self.db = make_temp_db()
        insert_scheme(self.db, 100)
        # Insert a clean ~12% annualised series over 3 years: 100 → ~140.5
        insert_nav_series(
            self.db, 100,
            date(2023, 5, 8), date(2026, 5, 8),
            100.0, 140.49,  # 1.12 ** 3 ≈ 1.4049
        )

    def tearDown(self):
        self.db.unlink(missing_ok=True)

    def test_one_year_return(self):
        r = get_returns(100, 365, self.db)
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r, 0.12, places=2)

    def test_three_year_return(self):
        r = get_returns(100, 365 * 3, self.db)
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r, 0.12, places=2)

    def test_period_too_long_returns_none(self):
        # Asking for 5Y when we only have 3Y → not enough coverage
        r = get_returns(100, 365 * 5, self.db)
        self.assertIsNone(r)

    def test_no_history_returns_none(self):
        insert_scheme(self.db, 200)
        self.assertIsNone(get_returns(200, 365, self.db))

    def test_unknown_scheme_returns_none(self):
        self.assertIsNone(get_returns(99999, 365, self.db))

    def test_zero_or_negative_period(self):
        self.assertIsNone(get_returns(100, 0, self.db))
        self.assertIsNone(get_returns(100, -100, self.db))


# --------------------------------------------------------------------------
# get_quality
# --------------------------------------------------------------------------

class TestGetQuality(unittest.TestCase):
    def setUp(self):
        self.db = make_temp_db()
        self.json_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        self.json_file.close()
        self.json_path = Path(self.json_file.name)

    def tearDown(self):
        self.db.unlink(missing_ok=True)
        self.json_path.unlink(missing_ok=True)

    def _write_json(self, content):
        self.json_path.write_text(json.dumps(content))

    def test_unknown_scheme_returns_error(self):
        self._write_json({"schemes": {}})
        result = get_quality(999, self.db, self.json_path)
        self.assertIn("error", result)

    def test_full_merge(self):
        insert_scheme(self.db, 100, scheme_name="Test Flexi Cap", category="Flexi Cap", plan="Direct")
        insert_nav_series(self.db, 100, date(2020, 1, 1), date(2026, 5, 8), 100.0, 200.0)
        self._write_json({
            "schemes": {
                "100": {
                    "ter": 0.62,
                    "manager_name": "Test Manager",
                    "manager_since": "2020-01-01",
                    "aum_crore": 5000.0,
                    "last_verified": "2026-05-09",
                    "notes": "test notes",
                }
            }
        })
        q = get_quality(100, self.db, self.json_path)
        self.assertEqual(q["scheme_name"], "Test Flexi Cap")
        self.assertEqual(q["ter"], 0.62)
        self.assertEqual(q["manager_name"], "Test Manager")
        self.assertEqual(q["aum_crore"], 5000.0)
        self.assertEqual(q["aum_source"], "json")
        self.assertEqual(q["vintage_date"], "2020-01-01")
        self.assertGreater(q["vintage_years"], 6.0)
        self.assertGreater(q["manager_tenure_years"], 6.0)
        self.assertEqual(q["quality_completeness"], 1.0)
        self.assertIsNotNone(q["return_1y"])
        self.assertIsNotNone(q["return_3y"])
        self.assertIsNotNone(q["return_5y"])

    def test_aum_db_fallback(self):
        # No AUM in JSON, but aum_crore is set on the schemes row
        insert_scheme(self.db, 100, aum_crore=1234.5, aum_date="2026-05-01")
        self._write_json({"schemes": {"100": {"ter": 0.5}}})
        q = get_quality(100, self.db, self.json_path)
        self.assertEqual(q["aum_crore"], 1234.5)
        self.assertEqual(q["aum_source"], "db")

    def test_aum_json_overrides_db(self):
        insert_scheme(self.db, 100, aum_crore=1000.0)
        self._write_json({"schemes": {"100": {"aum_crore": 9999.0}}})
        q = get_quality(100, self.db, self.json_path)
        self.assertEqual(q["aum_crore"], 9999.0)
        self.assertEqual(q["aum_source"], "json")

    def test_partial_quality_completeness(self):
        insert_scheme(self.db, 100)
        # Only 2 of 4 quality fields filled
        self._write_json({"schemes": {"100": {"ter": 0.5, "manager_name": "X"}}})
        q = get_quality(100, self.db, self.json_path)
        self.assertEqual(q["quality_completeness"], 2 / 4)

    def test_no_json_entry_returns_nones(self):
        insert_scheme(self.db, 100)
        self._write_json({"schemes": {}})
        q = get_quality(100, self.db, self.json_path)
        self.assertIsNone(q["ter"])
        self.assertIsNone(q["manager_name"])
        self.assertEqual(q["quality_completeness"], 0.0)


# --------------------------------------------------------------------------
# filter_candidates
# --------------------------------------------------------------------------

class TestFilterCandidates(unittest.TestCase):
    def setUp(self):
        self.db = make_temp_db()
        self.json_path = Path(tempfile.NamedTemporaryFile(suffix=".json", delete=False).name)

        # Three schemes in same category, varying returns and quality
        # Scheme 100: high return (15% over 3Y), full quality data
        insert_scheme(self.db, 100, scheme_name="Top Performer", category="Flexi Cap")
        insert_nav_series(self.db, 100, date(2022, 5, 8), date(2026, 5, 8), 100.0, 174.9)  # ~15%

        # Scheme 200: medium return (10%), partial quality
        insert_scheme(self.db, 200, scheme_name="Mid Performer", category="Flexi Cap")
        insert_nav_series(self.db, 200, date(2022, 5, 8), date(2026, 5, 8), 100.0, 146.41)  # ~10%

        # Scheme 300: low return (5%), no quality data, short vintage
        insert_scheme(self.db, 300, scheme_name="Newer Fund", category="Flexi Cap")
        insert_nav_series(self.db, 300, date(2025, 5, 8), date(2026, 5, 8), 100.0, 105.0)  # ~5%, only 1Y old

        # Scheme 400: different category
        insert_scheme(self.db, 400, scheme_name="Different Cat", category="Large Cap")
        insert_nav_series(self.db, 400, date(2022, 5, 8), date(2026, 5, 8), 100.0, 160.0)

        self.json_path.write_text(json.dumps({
            "schemes": {
                "100": {
                    "ter": 0.5, "manager_name": "A", "manager_since": "2018-01-01",
                    "aum_crore": 5000.0,
                },
                "200": {"ter": 1.2, "manager_name": "B"},  # partial
                # 300 has no entry
            }
        }))

    def tearDown(self):
        self.db.unlink(missing_ok=True)
        self.json_path.unlink(missing_ok=True)

    def test_category_filter(self):
        results = filter_candidates(category="Flexi Cap", db_path=self.db, json_path=self.json_path)
        codes = {r["scheme_code"] for r in results}
        self.assertEqual(codes, {100, 200, 300})

    def test_ranking_by_return_3y(self):
        results = filter_candidates(category="Flexi Cap", rank_by="return_3y",
                                     db_path=self.db, json_path=self.json_path)
        # 100 (15%) > 200 (10%); 300 has no 3Y history → goes last (None)
        self.assertEqual(results[0]["scheme_code"], 100)
        self.assertEqual(results[1]["scheme_code"], 200)
        self.assertEqual(results[2]["scheme_code"], 300)
        self.assertIsNone(results[2]["return_3y"])

    def test_min_vintage_filter(self):
        results = filter_candidates(category="Flexi Cap", min_vintage_years=3.0,
                                     db_path=self.db, json_path=self.json_path)
        # 300 has only 1Y vintage → excluded
        codes = {r["scheme_code"] for r in results}
        self.assertEqual(codes, {100, 200})

    def test_max_ter_filter(self):
        results = filter_candidates(category="Flexi Cap", max_ter=1.0,
                                     db_path=self.db, json_path=self.json_path)
        # 100 (TER 0.5) passes; 200 (TER 1.2) fails; 300 (TER unknown) fails
        codes = {r["scheme_code"] for r in results}
        self.assertEqual(codes, {100})

    def test_require_quality_data(self):
        results = filter_candidates(category="Flexi Cap", require_quality_data=True,
                                     db_path=self.db, json_path=self.json_path)
        # Only scheme 100 has all 4 quality fields populated
        codes = {r["scheme_code"] for r in results}
        self.assertEqual(codes, {100})

    def test_min_aum_filter_excludes_unknown_aum(self):
        results = filter_candidates(category="Flexi Cap", min_aum_crore=1000.0,
                                     db_path=self.db, json_path=self.json_path)
        # Only 100 has known AUM (5000 ≥ 1000); 200 and 300 have None AUM → excluded
        codes = {r["scheme_code"] for r in results}
        self.assertEqual(codes, {100})

    def test_plan_filter(self):
        # All test schemes default to Direct; insert one Regular for contrast
        insert_scheme(self.db, 500, scheme_name="Regular Scheme", category="Flexi Cap", plan="Regular")
        results = filter_candidates(category="Flexi Cap", plan="Direct",
                                     db_path=self.db, json_path=self.json_path)
        codes = {r["scheme_code"] for r in results}
        self.assertNotIn(500, codes)

    def test_limit(self):
        results = filter_candidates(category="Flexi Cap", limit=2,
                                     db_path=self.db, json_path=self.json_path)
        self.assertEqual(len(results), 2)


# --------------------------------------------------------------------------
# Schema migration (existing DB → adds columns; preserves data)
# --------------------------------------------------------------------------

class TestSchemaMigration(unittest.TestCase):
    def test_migration_adds_columns_to_existing_db(self):
        """A pre-Phase-3 DB (Phase 2 schema, has ISIN cols, no AUM cols) should get aum cols added."""
        f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        f.close()
        path = Path(f.name)
        try:
            # Simulate a pre-Phase-3 DB: Phase 2 schema, with ISIN columns but no AUM.
            # This matches what existing users have on disk.
            with sqlite3.connect(path) as conn:
                conn.executescript("""
                    CREATE TABLE schemes (
                        scheme_code      INTEGER PRIMARY KEY,
                        isin_growth      TEXT,
                        isin_div_reinv   TEXT,
                        scheme_name      TEXT NOT NULL,
                        amc              TEXT NOT NULL,
                        category         TEXT NOT NULL,
                        plan             TEXT,
                        option_type      TEXT,
                        first_seen       DATE,
                        last_seen        DATE
                    );
                    CREATE TABLE nav_history (
                        scheme_code INTEGER, nav_date DATE, nav REAL,
                        PRIMARY KEY (scheme_code, nav_date)
                    );
                    CREATE TABLE fetch_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, fetch_time DATETIME,
                        status TEXT, record_count INTEGER, error_message TEXT
                    );
                    INSERT INTO schemes (scheme_code, scheme_name, amc, category)
                    VALUES (100, 'Pre-Phase-3 Scheme', 'Test', 'Flexi Cap');
                """)

            # Run init_db, which should apply the migration in-place
            init_db(path)

            # New columns should exist; existing data preserved
            with sqlite3.connect(path) as conn:
                cols = {r[1] for r in conn.execute("PRAGMA table_info(schemes)").fetchall()}
                self.assertIn("aum_crore", cols)
                self.assertIn("aum_date", cols)

                row = conn.execute(
                    "SELECT scheme_name, aum_crore FROM schemes WHERE scheme_code = 100"
                ).fetchone()
                self.assertEqual(row[0], "Pre-Phase-3 Scheme")
                self.assertIsNone(row[1])

            # Re-running init_db should be idempotent (no error, columns still there,
            # data unchanged)
            init_db(path)
            init_db(path)
            with sqlite3.connect(path) as conn:
                row = conn.execute(
                    "SELECT scheme_name FROM schemes WHERE scheme_code = 100"
                ).fetchone()
                self.assertEqual(row[0], "Pre-Phase-3 Scheme")
        finally:
            path.unlink(missing_ok=True)

    def test_fresh_db_has_aum_columns(self):
        path = make_temp_db()
        try:
            with sqlite3.connect(path) as conn:
                cols = {r[1] for r in conn.execute("PRAGMA table_info(schemes)").fetchall()}
                self.assertIn("aum_crore", cols)
                self.assertIn("aum_date", cols)
        finally:
            path.unlink(missing_ok=True)


# --------------------------------------------------------------------------
# build_quality_template (bootstrap utility)
# --------------------------------------------------------------------------

class TestBuildQualityTemplate(unittest.TestCase):
    def setUp(self):
        self.db = make_temp_db()
        # Patch the DEFAULT_DB_PATH so build_quality_template uses our test DB
        import lib.db as dbmod
        self._orig_db = dbmod.DEFAULT_DB_PATH
        dbmod.DEFAULT_DB_PATH = self.db

        # Set up minimal portfolio.md
        self.portfolio_path = Path(tempfile.NamedTemporaryFile(
            suffix=".md", delete=False).name)
        self.json_path = Path(tempfile.NamedTemporaryFile(
            suffix=".json", delete=False).name)
        self.json_path.unlink()  # we want to test the create-fresh path

        self.portfolio_path.write_text("""
# Portfolio

## Holdings

| # | Scheme | AMC | Plan | scheme_code | Capital | First purchase |
|---|---|---|---|---|---|---|
| 1 | Test Fund A | X | Direct | 100 | ₹50,000 | 2025-03 |
| 2 | Test Fund B | Y | Direct | 200 | ₹50,000 | 2025-03 |
""")
        # Insert these in the schemes table so name_ref can be looked up
        insert_scheme(self.db, 100, scheme_name="Test Scheme 100 Canonical")
        insert_scheme(self.db, 200, scheme_name="Test Scheme 200 Canonical")

    def tearDown(self):
        import lib.db as dbmod
        dbmod.DEFAULT_DB_PATH = self._orig_db
        self.db.unlink(missing_ok=True)
        self.portfolio_path.unlink(missing_ok=True)
        self.json_path.unlink(missing_ok=True)

    def _run_template_builder(self):
        """Invoke build_quality_template.main() with our test paths."""
        import build_quality_template as bqt
        # main() reads sys.argv; patch it for the test
        old_argv = sys.argv
        try:
            sys.argv = [
                "build_quality_template.py",
                "--portfolio", str(self.portfolio_path),
                "--output", str(self.json_path),
                "--quiet",
            ]
            return bqt.main()
        finally:
            sys.argv = old_argv

    def test_creates_template_for_new_schemes(self):
        rc = self._run_template_builder()
        self.assertEqual(rc, 0)
        data = json.loads(self.json_path.read_text())
        self.assertIn("schemes", data)
        self.assertIn("100", data["schemes"])
        self.assertIn("200", data["schemes"])
        self.assertEqual(data["schemes"]["100"]["name_ref"], "Test Scheme 100 Canonical")
        self.assertIsNone(data["schemes"]["100"]["ter"])

    def test_idempotent_run_preserves_existing_data(self):
        # First run creates templates
        self._run_template_builder()
        # User fills in a value
        data = json.loads(self.json_path.read_text())
        data["schemes"]["100"]["ter"] = 0.55
        data["schemes"]["100"]["manager_name"] = "User Filled"
        self.json_path.write_text(json.dumps(data))

        # Second run shouldn't overwrite
        self._run_template_builder()
        data2 = json.loads(self.json_path.read_text())
        self.assertEqual(data2["schemes"]["100"]["ter"], 0.55)
        self.assertEqual(data2["schemes"]["100"]["manager_name"], "User Filled")


if __name__ == "__main__":
    unittest.main(verbosity=2)
