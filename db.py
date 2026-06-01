"""SQLite persistence layer.

Three tables:
  - loads                : the broker's available freight (seeded from loads.json)
  - negotiation_sessions : tracks an in-progress negotiation per (mc_number, load_id)
                           so round-counting is server-side and deterministic
  - calls                : one row per completed call, written by the post-call webhook

Using sqlite3 from the standard library keeps the dependency surface tiny and the
whole thing runs in one container with no external database.
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import settings

SEED_FILE = Path(__file__).parent / "loads.json"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn


def init_db() -> None:
    """Create tables if they don't exist, then seed loads once."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS loads (
            load_id TEXT PRIMARY KEY,
            origin TEXT,
            destination TEXT,
            pickup_datetime TEXT,
            delivery_datetime TEXT,
            equipment_type TEXT,
            loadboard_rate REAL,
            notes TEXT,
            weight REAL,
            commodity_type TEXT,
            num_of_pieces INTEGER,
            miles REAL,
            dimensions TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS negotiation_sessions (
            session_key TEXT PRIMARY KEY,   -- mc_number + ":" + load_id
            mc_number TEXT,
            load_id TEXT,
            loadboard_rate REAL,
            last_broker_offer REAL,
            round_count INTEGER,
            status TEXT,                     -- open | accepted | rejected
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mc_number TEXT,
            carrier_name TEXT,
            load_id TEXT,
            outcome TEXT,
            agreed_rate REAL,
            loadboard_rate REAL,
            negotiation_rounds INTEGER,
            sentiment TEXT,
            transcript TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )

    conn.commit()
    _seed_loads(conn)
    conn.close()


def _seed_loads(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM loads")
    if cur.fetchone()["c"] > 0:
        return  # already seeded

    loads = json.loads(SEED_FILE.read_text())
    for ld in loads:
        cur.execute(
            """
            INSERT INTO loads (load_id, origin, destination, pickup_datetime,
                delivery_datetime, equipment_type, loadboard_rate, notes, weight,
                commodity_type, num_of_pieces, miles, dimensions)
            VALUES (:load_id, :origin, :destination, :pickup_datetime,
                :delivery_datetime, :equipment_type, :loadboard_rate, :notes, :weight,
                :commodity_type, :num_of_pieces, :miles, :dimensions)
            """,
            ld,
        )
    conn.commit()


# ---------- Loads ----------

def search_loads(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    equipment_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Case-insensitive partial match on the fields a carrier would mention."""
    conn = get_conn()
    cur = conn.cursor()
    clauses, params = [], []
    if origin:
        clauses.append("LOWER(origin) LIKE ?")
        params.append(f"%{origin.lower()}%")
    if destination:
        clauses.append("LOWER(destination) LIKE ?")
        params.append(f"%{destination.lower()}%")
    if equipment_type:
        clauses.append("LOWER(equipment_type) LIKE ?")
        params.append(f"%{equipment_type.lower()}%")
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    cur.execute(f"SELECT * FROM loads{where} ORDER BY loadboard_rate DESC", params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_load(load_id: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM loads WHERE load_id = ?", (load_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------- Negotiation sessions ----------

def get_or_create_session(mc_number: str, load_id: str, loadboard_rate: float) -> Dict[str, Any]:
    key = f"{mc_number}:{load_id}"
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM negotiation_sessions WHERE session_key = ?", (key,))
    row = cur.fetchone()
    if row is None:
        cur.execute(
            """
            INSERT INTO negotiation_sessions
                (session_key, mc_number, load_id, loadboard_rate, last_broker_offer, round_count, status)
            VALUES (?, ?, ?, ?, ?, 0, 'open')
            """,
            (key, mc_number, load_id, loadboard_rate, loadboard_rate),
        )
        conn.commit()
        cur.execute("SELECT * FROM negotiation_sessions WHERE session_key = ?", (key,))
        row = cur.fetchone()
    result = dict(row)
    conn.close()
    return result


def _fetch_session(mc_number: str, load_id: str) -> Optional[Dict[str, Any]]:
    key = f"{mc_number}:{load_id}"
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM negotiation_sessions WHERE session_key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_session(session_key: str, last_broker_offer: float, round_count: int, status: str) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE negotiation_sessions SET last_broker_offer = ?, round_count = ?, status = ? WHERE session_key = ?",
        (last_broker_offer, round_count, status, session_key),
    )
    conn.commit()
    conn.close()


# ---------- Calls ----------

def insert_call(record: Dict[str, Any]) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO calls (mc_number, carrier_name, load_id, outcome, agreed_rate,
            loadboard_rate, negotiation_rounds, sentiment, transcript)
        VALUES (:mc_number, :carrier_name, :load_id, :outcome, :agreed_rate,
            :loadboard_rate, :negotiation_rounds, :sentiment, :transcript)
        """,
        record,
    )
    conn.commit()
    call_id = cur.lastrowid
    conn.close()
    return call_id


def fetch_calls() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM calls ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def compute_metrics() -> Dict[str, Any]:
    calls = fetch_calls()
    total = len(calls)

    outcomes: Dict[str, int] = {}
    sentiment: Dict[str, int] = {}
    booked = [c for c in calls if c["outcome"] == "booked"]
    rounds_vals = [c["negotiation_rounds"] for c in calls if c["negotiation_rounds"] is not None]
    agreed_vals = [c["agreed_rate"] for c in booked if c["agreed_rate"] is not None]
    loadboard_on_booked = [c["loadboard_rate"] for c in booked if c["loadboard_rate"] is not None]
    margin_deltas = [
        c["agreed_rate"] - c["loadboard_rate"]
        for c in booked
        if c["agreed_rate"] is not None and c["loadboard_rate"] is not None
    ]

    for c in calls:
        outcomes[c["outcome"]] = outcomes.get(c["outcome"], 0) + 1
        s = c["sentiment"] or "unknown"
        sentiment[s] = sentiment.get(s, 0) + 1

    def avg(xs):
        return round(sum(xs) / len(xs), 2) if xs else None

    return {
        "total_calls": total,
        "outcomes": outcomes,
        "sentiment": sentiment,
        "booking_rate": round(len(booked) / total, 3) if total else 0.0,
        "avg_negotiation_rounds": avg(rounds_vals),
        "avg_agreed_rate": avg(agreed_vals),
        "avg_loadboard_rate_on_booked": avg(loadboard_on_booked),
        "avg_margin_delta": avg(margin_deltas),
        "not_eligible_count": outcomes.get("not_eligible", 0),
    }
