import json
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from datetime import date, timedelta
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
            run_id TEXT,
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
    if ", " in low:
        city, state = low.rsplit(", ", 1)
        abbrev = STATE_ABBREVS.get(state)
        if abbrev:
            variants.append(f"%{city}%, {abbrev}")
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
        INSERT INTO calls (run_id, mc_number, carrier_name, load_id, outcome, agreed_rate,
            loadboard_rate, negotiation_rounds, sentiment, transcript)
        VALUES (%(run_id)s, %(mc_number)s, %(carrier_name)s, %(load_id)s, %(outcome)s, %(agreed_rate)s,
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


def compute_dashboard_data() -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 1. Bookings per day (last 7 days)
    today = date.today()
    week_ago = today - timedelta(days=6)
    cur.execute(
        """
        SELECT DATE(created_at) AS day, COUNT(*) AS cnt
        FROM calls
        WHERE outcome = 'booked' AND created_at >= %s
        GROUP BY DATE(created_at)
        ORDER BY day
        """,
        (week_ago,),
    )
    day_counts = {str(r["day"]): r["cnt"] for r in cur.fetchall()}
    labels, values = [], []
    for i in range(7):
        d = week_ago + timedelta(days=i)
        labels.append(d.strftime("%b %d"))
        values.append(day_counts.get(str(d), 0))
    bookings_per_day = {"labels": labels, "values": values}

    # 2. Non-booked reasons
    cur.execute(
        """
        SELECT outcome, COUNT(*) AS cnt
        FROM calls
        WHERE outcome != 'booked'
        GROUP BY outcome
        """
    )
    non_booked_reasons = {r["outcome"]: r["cnt"] for r in cur.fetchall()}

    # 3. Pickup time patterns (booked vs not booked) — bucketed by time of day
    cur.execute(
        """
        SELECT
            CASE
                WHEN EXTRACT(HOUR FROM l.pickup_datetime::timestamp) BETWEEN 6 AND 11 THEN 'Morning'
                WHEN EXTRACT(HOUR FROM l.pickup_datetime::timestamp) BETWEEN 12 AND 17 THEN 'Afternoon'
                WHEN EXTRACT(HOUR FROM l.pickup_datetime::timestamp) BETWEEN 18 AND 23 THEN 'Evening'
                ELSE 'Night'
            END AS time_bucket,
            c.outcome,
            COUNT(*) AS cnt
        FROM calls c
        JOIN loads l ON c.load_id = l.load_id
        WHERE c.load_id IS NOT NULL
        GROUP BY time_bucket, c.outcome
        """
    )
    bucket_order = ["Morning", "Afternoon", "Evening", "Night"]
    bucket_booked = {b: 0 for b in bucket_order}
    bucket_not_booked = {b: 0 for b in bucket_order}
    for r in cur.fetchall():
        b = r["time_bucket"]
        if r["outcome"] == "booked":
            bucket_booked[b] += r["cnt"]
        else:
            bucket_not_booked[b] += r["cnt"]
    pickup_time_patterns = {
        "labels": bucket_order,
        "booked": [bucket_booked[b] for b in bucket_order],
        "not_booked": [bucket_not_booked[b] for b in bucket_order],
    }

    # 4. Equipment type distribution
    cur.execute(
        """
        SELECT
            l.equipment_type,
            SUM(CASE WHEN c.outcome = 'booked' THEN 1 ELSE 0 END) AS booked,
            SUM(CASE WHEN c.outcome != 'booked' THEN 1 ELSE 0 END) AS not_booked
        FROM calls c
        JOIN loads l ON c.load_id = l.load_id
        WHERE c.load_id IS NOT NULL
        GROUP BY l.equipment_type
        ORDER BY booked DESC
        """
    )
    eq_labels, eq_booked, eq_not_booked = [], [], []
    for r in cur.fetchall():
        eq_labels.append(r["equipment_type"])
        eq_booked.append(r["booked"])
        eq_not_booked.append(r["not_booked"])
    equipment_distribution = {
        "labels": eq_labels,
        "booked": eq_booked,
        "not_booked": eq_not_booked,
    }

    # 5. Distance vs booking (scatter data)
    cur.execute(
        """
        SELECT l.miles, c.outcome, c.agreed_rate, l.loadboard_rate
        FROM calls c
        JOIN loads l ON c.load_id = l.load_id
        WHERE c.load_id IS NOT NULL AND l.miles IS NOT NULL
        """
    )
    scatter_booked, scatter_not_booked = [], []
    for r in cur.fetchall():
        rate = r["agreed_rate"] if r["outcome"] == "booked" and r["agreed_rate"] else r["loadboard_rate"]
        if rate is None:
            continue
        point = {"x": float(r["miles"]), "y": float(rate)}
        if r["outcome"] == "booked":
            scatter_booked.append(point)
        else:
            scatter_not_booked.append(point)
    distance_booking = {"booked": scatter_booked, "not_booked": scatter_not_booked}

    conn.close()
    return {
        "bookings_per_day": bookings_per_day,
        "non_booked_reasons": non_booked_reasons,
        "pickup_time_patterns": pickup_time_patterns,
        "equipment_distribution": equipment_distribution,
        "distance_booking": distance_booking,
    }
