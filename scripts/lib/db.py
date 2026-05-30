"""
Database schema and connection helpers for the finance-app data layer.

The data layer uses SQLite for reliability, simplicity, and zero infrastructure overhead.
A single .db file holds all market data; backed up by copying the file.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "market.db"


SCHEMA = """
-- Daily NAV records, one row per scheme per date.
-- Append-only table; never UPDATE existing rows.
CREATE TABLE IF NOT EXISTS nav_history (
    scheme_code INTEGER NOT NULL,
    nav_date    DATE    NOT NULL,
    nav         REAL    NOT NULL,
    PRIMARY KEY (scheme_code, nav_date)
);

-- Scheme metadata; latest known values per scheme.
-- Updated when fetch_nav.py sees a scheme; preserves history via last_seen.
-- aum_crore / aum_date populated by future AMFI AUM fetcher OR manual override
-- via fund_quality.json (see scripts/lib/fund_quality.py for read path).
CREATE TABLE IF NOT EXISTS schemes (
    scheme_code      INTEGER PRIMARY KEY,
    isin_growth      TEXT,
    isin_div_reinv   TEXT,
    scheme_name      TEXT    NOT NULL,
    amc              TEXT    NOT NULL,
    category         TEXT    NOT NULL,
    plan             TEXT,           -- 'Direct' / 'Regular' / NULL when ambiguous
    option_type      TEXT,           -- 'Growth' / 'IDCW' / 'Reinvest' / NULL
    first_seen       DATE,
    last_seen        DATE,
    aum_crore        REAL,           -- Latest known AUM in ₹ crores; NULL if unknown
    aum_date         DATE            -- Date the aum_crore figure was reported
);

-- Fetch audit log. Every fetcher run writes a row here.
-- Used to flag stale data and surface fetch failures.
CREATE TABLE IF NOT EXISTS fetch_log (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    source         TEXT     NOT NULL,
    fetch_time     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status         TEXT     NOT NULL,
    record_count   INTEGER,
    error_message  TEXT
);

-- Indexes for common access patterns.
CREATE INDEX IF NOT EXISTS idx_nav_date          ON nav_history(nav_date);
CREATE INDEX IF NOT EXISTS idx_schemes_amc       ON schemes(amc);
CREATE INDEX IF NOT EXISTS idx_schemes_category  ON schemes(category);
CREATE INDEX IF NOT EXISTS idx_schemes_name      ON schemes(scheme_name);
CREATE INDEX IF NOT EXISTS idx_schemes_isin_g    ON schemes(isin_growth);
CREATE INDEX IF NOT EXISTS idx_fetch_source_time ON fetch_log(source, fetch_time DESC);
"""


def _migrate_schema(conn: sqlite3.Connection) -> None:
    """
    Apply additive migrations to existing databases. Idempotent.

    SQLite's CREATE TABLE IF NOT EXISTS doesn't add new columns to an
    already-existing table. For schema additions we use ALTER TABLE guarded
    by a column-existence check via PRAGMA table_info.

    This is the right pattern: it lets fresh installs get the canonical
    schema (above) while existing databases get the new columns added
    in-place without losing data.
    """
    # schemes: aum_crore + aum_date (added Phase 3)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(schemes)").fetchall()}
    if "aum_crore" not in cols:
        conn.execute("ALTER TABLE schemes ADD COLUMN aum_crore REAL")
    if "aum_date" not in cols:
        conn.execute("ALTER TABLE schemes ADD COLUMN aum_date DATE")


def init_db(db_path: Path | str | None = None) -> None:
    """Create the schema if it doesn't exist. Idempotent. Resolves DEFAULT_DB_PATH at call time."""
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        _migrate_schema(conn)
        conn.commit()


@contextmanager
def get_conn(db_path: Path | str | None = None) -> Iterator[sqlite3.Connection]:
    """
    Context manager yielding a SQLite connection. Foreign keys ON, row factory dict-like.
    Auto-commits on successful exit; auto-rollback on exception.

    Resolves db_path at call time (rather than via default argument capture) so that
    callers — including tests — can monkey-patch the module-level DEFAULT_DB_PATH and
    have subsequent get_conn() invocations honour the new value.
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    db_path = Path(db_path)
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def log_fetch(
    source: str,
    status: str,
    record_count: int | None = None,
    error_message: str | None = None,
    db_path: Path | str | None = None,
) -> None:
    """Append a row to the fetch_log audit trail."""
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO fetch_log (source, status, record_count, error_message) "
            "VALUES (?, ?, ?, ?)",
            (source, status, record_count, error_message),
        )


def last_fetch_time(source: str, db_path: Path | str | None = None) -> str | None:
    """Return ISO timestamp of last successful fetch for a source, or None."""
    with get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT fetch_time FROM fetch_log "
            "WHERE source = ? AND status = 'success' "
            "ORDER BY fetch_time DESC LIMIT 1",
            (source,),
        ).fetchone()
    return row["fetch_time"] if row else None
