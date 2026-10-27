"""SQLite persistence (standard-library sqlite3, parameterised queries only)."""
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "foodbridge.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS donations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    food_name       TEXT    NOT NULL,
    description     TEXT    NOT NULL,
    servings        INTEGER NOT NULL CHECK (servings > 0),
    location        TEXT    NOT NULL,
    pickup_deadline TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'available'
                            CHECK (status IN ('available', 'claimed')),
    donor_name      TEXT    NOT NULL,
    donor_contact   TEXT    NOT NULL,
    category        TEXT,
    created_at      TEXT    NOT NULL,
    claimed_by      TEXT,
    claimed_at      TEXT
);
CREATE INDEX IF NOT EXISTS idx_donations_status_deadline
    ON donations (status, pickup_deadline);
"""

# 'expired' is derived, not stored: an unclaimed donation whose deadline passed.
_SELECT = """
SELECT * FROM (
    SELECT d.*,
           CASE WHEN d.status = 'available' AND d.pickup_deadline <= :now
                THEN 'expired' ELSE d.status END AS effective_status
    FROM donations d
)
"""


def fmt(dt: datetime) -> str:
    """Fixed-width UTC timestamp so string comparison == time comparison."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(path: str) -> sqlite3.Connection:
    # check_same_thread=False: FastAPI may run a request's dependency and
    # endpoint on different worker threads. Each request has its own connection.
    conn = sqlite3.connect(path, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: str) -> None:
    conn = connect(path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def _to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["status"] = d.pop("effective_status")
    return d


def create_donation(conn: sqlite3.Connection, data: dict, now: datetime) -> dict:
    cur = conn.execute(
        """INSERT INTO donations
           (food_name, description, servings, location, pickup_deadline,
            status, donor_name, donor_contact, category, created_at)
           VALUES (?, ?, ?, ?, ?, 'available', ?, ?, ?, ?)""",
        (
            data["food_name"],
            data["description"],
            data["servings"],
            data["location"],
            fmt(data["pickup_deadline"]),
            data["donor_name"],
            data["donor_contact"],
            data.get("category"),
            fmt(now),
        ),
    )
    conn.commit()
    return get_donation(conn, cur.lastrowid, now)  # type: ignore[arg-type]


def get_donation(conn: sqlite3.Connection, donation_id: int, now: datetime) -> Optional[dict]:
    row = conn.execute(
        _SELECT + " WHERE id = :id", {"now": fmt(now), "id": donation_id}
    ).fetchone()
    return _to_dict(row) if row else None


def list_donations(
    conn: sqlite3.Connection,
    now: datetime,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    sql = _SELECT
    params: dict = {"now": fmt(now), "limit": limit, "offset": offset}
    if status:
        sql += " WHERE effective_status = :status"
        params["status"] = status
    sql += " ORDER BY id DESC LIMIT :limit OFFSET :offset"
    return [_to_dict(r) for r in conn.execute(sql, params).fetchall()]


def claim_donation(
    conn: sqlite3.Connection, donation_id: int, claimed_by: str, now: datetime
) -> tuple:
    """Atomically claim a donation.

    The status check and the update are ONE statement, so two concurrent
    claims can never both succeed. Returns (outcome, donation_dict_or_None)
    where outcome is 'claimed' | 'not_found' | 'already_claimed' | 'expired'.
    """
    cur = conn.execute(
        """UPDATE donations
              SET status = 'claimed', claimed_by = ?, claimed_at = ?
            WHERE id = ? AND status = 'available' AND pickup_deadline > ?""",
        (claimed_by, fmt(now), donation_id, fmt(now)),
    )
    conn.commit()
    row = conn.execute(
        _SELECT + " WHERE id = :id", {"now": fmt(now), "id": donation_id}
    ).fetchone()
    if row is None:
        return "not_found", None
    donation = _to_dict(row)
    if cur.rowcount == 1:
        donation["donor_contact"] = row["donor_contact"]
        return "claimed", donation
    if donation["status"] == "claimed":
        return "already_claimed", donation
    return "expired", donation
