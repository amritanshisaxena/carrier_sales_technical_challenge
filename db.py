import json
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import settings

SEED_FILE = Path(__file__).parent / "loads.json"


def get_conn():
    return psycopg2.connect(settings.database_url)


def init_db() -> None:
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
        CREATE TABLE IF NOT EXISTS calls (
            id SERIAL PRIMARY KEY,
            mc_number TEXT,
            carrier_name TEXT,
            load_id TEXT,
            outcome TEXT,
            agreed_rate REAL,
            loadboard_rate REAL,
            negotiation_rounds INTEGER,
            sentiment TEXT,
            transcript TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """
    )

    conn.commit()
    _seed_loads(conn)
    conn.close()


def _seed_loads(conn) -> None:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM loads")
    if cur.fetchone()[0] > 0:
        return

    loads = json.loads(SEED_FILE.read_text())
    for ld in loads:
        cur.execute(
            """
            INSERT INTO loads (load_id, origin, destination, pickup_datetime,
                delivery_datetime, equipment_type, loadboard_rate, notes, weight,
                commodity_type, num_of_pieces, miles, dimensions)
            VALUES (%(load_id)s, %(origin)s, %(destination)s, %(pickup_datetime)s,
                %(delivery_datetime)s, %(equipment_type)s, %(loadboard_rate)s, %(notes)s,
                %(weight)s, %(commodity_type)s, %(num_of_pieces)s, %(miles)s, %(dimensions)s)
            """,
            ld,
        )
    conn.commit()


STATE_ABBREVS = {
    "alabama": "al", "alaska": "ak", "arizona": "az", "arkansas": "ar",
    "california": "ca", "colorado": "co", "connecticut": "ct", "delaware": "de",
    "florida": "fl", "georgia": "ga", "hawaii": "hi", "idaho": "id",
    "illinois": "il", "indiana": "in", "iowa": "ia", "kansas": "ks",
    "kentucky": "ky", "louisiana": "la", "maine": "me", "maryland": "md",
    "massachusetts": "ma", "michigan": "mi", "minnesota": "mn", "mississippi": "ms",
    "missouri": "mo", "montana": "mt", "nebraska": "ne", "nevada": "nv",
    "new hampshire": "nh", "new jersey": "nj", "new mexico": "nm", "new york": "ny",
    "north carolina": "nc", "north dakota": "nd", "ohio": "oh", "oklahoma": "ok",
    "oregon": "or", "pennsylvania": "pa", "rhode island": "ri", "south carolina": "sc",
    "south dakota": "sd", "tennessee": "tn", "texas": "tx", "utah": "ut",
    "vermont": "vt", "virginia": "va", "washington": "wa", "west virginia": "wv",
    "wisconsin": "wi", "wyoming": "wy",
}


def _expand_location(term: str) -> list[str]:
    low = term.lower().strip()
    variants = [f"%{low}%"]
    if low in STATE_ABBREVS:
        variants.append(f"%, {STATE_ABBREVS[low]}")
    return variants


# ---------- Loads ----------

def search_loads(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    equipment_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    clauses, params = [], []
    if origin:
        variants = _expand_location(origin)
        sub = " OR ".join(["LOWER(origin) LIKE %s"] * len(variants))
        clauses.append(f"({sub})")
        params.extend(variants)
    if destination:
        variants = _expand_location(destination)
        sub = " OR ".join(["LOWER(destination) LIKE %s"] * len(variants))
        clauses.append(f"({sub})")
        params.extend(variants)
    if equipment_type:
        clauses.append("LOWER(equipment_type) LIKE %s")
        params.append(f"%{equipment_type.lower()}%")
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    cur.execute(f"SELECT * FROM loads{where} ORDER BY loadboard_rate DESC", params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ---------- Calls ----------

def insert_call(record: Dict[str, Any]) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO calls (mc_number, carrier_name, load_id, outcome, agreed_rate,
            loadboard_rate, negotiation_rounds, sentiment, transcript)
        VALUES (%(mc_number)s, %(carrier_name)s, %(load_id)s, %(outcome)s, %(agreed_rate)s,
            %(loadboard_rate)s, %(negotiation_rounds)s, %(sentiment)s, %(transcript)s)
        RETURNING id
        """,
        record,
    )
    call_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return call_id


def fetch_calls() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM calls ORDER BY created_at DESC")
    rows = []
    for r in cur.fetchall():
        row = dict(r)
        if row.get("created_at"):
            row["created_at"] = str(row["created_at"])
        rows.append(row)
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
