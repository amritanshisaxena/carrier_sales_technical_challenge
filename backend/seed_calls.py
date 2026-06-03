"""Seed script — POSTs a handful of realistic calls to your running API so the
dashboard and the `calls` table fill up.

Uses only Python's standard library (no pip installs needed), so it runs in any
environment as long as your server is running.

Usage:
    1. Start the server in one terminal:   uvicorn main:app --reload
    2. In another terminal:                python seed_calls.py

Reads your API key from the .env file automatically. Override the target with the
BASE_URL env var to seed a deployed instance (e.g. BASE_URL=https://your-app.onrender.com).
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")


def read_api_key() -> str:
    env = Path(__file__).parent / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith("API_KEY="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("API_KEY", "")


CALLS = [
    {"mc_number": "210431", "carrier_name": "Blue Ridge Transport", "load_id": "HR-1001",
     "outcome": "booked", "agreed_rate": 2600, "loadboard_rate": 2400, "negotiation_rounds": 2, "sentiment": "positive"},
    {"mc_number": "338120", "carrier_name": "Summit Freight LLC", "load_id": "HR-1002",
     "outcome": "booked", "agreed_rate": 1950, "loadboard_rate": 1850, "negotiation_rounds": 1, "sentiment": "positive"},
    {"mc_number": "551902", "carrier_name": "Delta Haulers", "load_id": "HR-1005",
     "outcome": "no_agreement", "agreed_rate": None, "loadboard_rate": 2950, "negotiation_rounds": 3, "sentiment": "negative"},
    {"mc_number": "447781", "carrier_name": "Cardinal Logistics", "load_id": "HR-1003",
     "outcome": "declined", "agreed_rate": None, "loadboard_rate": 1100, "negotiation_rounds": 0, "sentiment": "neutral"},
    {"mc_number": "12345", "carrier_name": "MORAN SERVICE CORP", "load_id": None,
     "outcome": "not_eligible", "agreed_rate": None, "loadboard_rate": None, "negotiation_rounds": None, "sentiment": "neutral"},
    {"mc_number": "672244", "carrier_name": "Ironclad Carriers", "load_id": "HR-1009",
     "outcome": "booked", "agreed_rate": 1800, "loadboard_rate": 1700, "negotiation_rounds": 2, "sentiment": "positive"},
    {"mc_number": "729015", "carrier_name": "Prairie Line Freight", "load_id": "HR-1007",
     "outcome": "booked", "agreed_rate": 1250, "loadboard_rate": 1250, "negotiation_rounds": 0, "sentiment": "positive"},
    {"mc_number": "804113", "carrier_name": "Atlas Flatbed Co", "load_id": "HR-1004",
     "outcome": "no_agreement", "agreed_rate": None, "loadboard_rate": 1600, "negotiation_rounds": 3, "sentiment": "neutral"},
    {"mc_number": "915677", "carrier_name": "MedFleet Logistics", "load_id": "HR-1010",
     "outcome": "booked", "agreed_rate": 1230, "loadboard_rate": 1150, "negotiation_rounds": 1, "sentiment": "positive"},
]


def request(method: str, path: str, api_key: str, body: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def main() -> None:
    api_key = read_api_key()
    if not api_key:
        sys.exit("No API key found. Set API_KEY in .env or as an env var.")

    ok = 0
    for c in CALLS:
        try:
            request("POST", "/calls", api_key, c)
            ok += 1
            label = c["carrier_name"] or c["mc_number"]
            print(f"  stored: {label:24s} -> {c['outcome']}")
        except urllib.error.HTTPError as e:
            print(f"  FAILED: {c.get('carrier_name')} (HTTP {e.code} — check your API key)")
        except Exception as e:
            print(f"  FAILED: {c.get('carrier_name')} ({e})")

    print(f"\n{ok}/{len(CALLS)} calls seeded.")
    try:
        m = request("GET", "/metrics", api_key)
        print(f"Total calls: {m['total_calls']} | booking rate: {m['booking_rate']*100:.0f}% | "
              f"avg margin delta: ${m['avg_margin_delta']}")
    except Exception:
        pass
    print(f"\nOpen {BASE_URL}/ to see the dashboard populated.")


if __name__ == "__main__":
    main()