"""FastAPI app: data layer for the HappyRobot inbound carrier sales agent,
plus the endpoints that feed the ops dashboard.

The HappyRobot platform handles FMCSA verification, negotiation, call
classification, and sentiment analysis. This service provides:
  GET  /health   -> liveness check (open, used by Render)
  GET  /loads    -> search available loads (called by the agent)
  POST /calls    -> store a completed call (post-call webhook)
  GET  /metrics  -> aggregated stats for the dashboard
"""

from typing import Optional, List
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import httpx
from fastapi import FastAPI, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import db
from auth import require_api_key
from config import settings
from schemas import Load, CallRecord, MetricsResponse

HR_API_BASE = "https://platform.happyrobot.ai/api/v2"


async def fetch_happyrobot_data() -> Optional[dict]:
    if not settings.happyrobot_api_key or not settings.happyrobot_use_case_id:
        return None
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{HR_API_BASE}/runs",
                headers={"Authorization": f"Bearer {settings.happyrobot_api_key}"},
                params={"use_case_id": settings.happyrobot_use_case_id},
            )
            resp.raise_for_status()
            runs = resp.json().get("data", [])
    except Exception:
        return None

    runs_by_id = {}
    durations = []
    runs_per_day = {}

    for r in runs:
        runs_by_id[r["id"]] = r
        ts = r.get("timestamp")
        completed = r.get("completed_at")
        if ts and completed:
            start = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            end = datetime.fromisoformat(completed.replace("Z", "+00:00"))
            dur_seconds = (end - start).total_seconds()
            durations.append(dur_seconds)
            day = start.strftime("%b %d")
            runs_per_day[day] = runs_per_day.get(day, 0) + 1

    today = datetime.utcnow().date()
    labels, values = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        label = d.strftime("%b %d")
        labels.append(label)
        values.append(runs_per_day.get(label, 0))

    avg_duration = round(sum(durations) / len(durations)) if durations else None
    if avg_duration is not None:
        mins, secs = divmod(avg_duration, 60)
        avg_duration_display = f"{int(mins)}m {int(secs)}s"
    else:
        avg_duration_display = None

    return {
        "runs_by_id": runs_by_id,
        "avg_duration_display": avg_duration_display,
        "runs_per_day": {"labels": labels, "values": values},
        "total_runs": len(runs),
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Inbound Carrier Sales API", version="1.0.0", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    hr_data = await fetch_happyrobot_data()

    calls = db.fetch_calls()[:15]
    if hr_data and hr_data.get("runs_by_id"):
        for c in calls:
            run = hr_data["runs_by_id"].get(c.get("run_id"))
            if run and run.get("timestamp") and run.get("completed_at"):
                start = datetime.fromisoformat(run["timestamp"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(run["completed_at"].replace("Z", "+00:00"))
                dur = int((end - start).total_seconds())
                mins, secs = divmod(dur, 60)
                c["duration"] = f"{mins}m {secs}s"
                c["run_status"] = run.get("status", "—")
            else:
                c["duration"] = None
                c["run_status"] = None

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "metrics": db.compute_metrics(),
            "calls": calls,
            "dashboard_data": db.compute_dashboard_data(),
            "hr_data": hr_data,
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/loads", response_model=List[Load])
async def loads(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    equipment_type: Optional[str] = None,
    _: bool = Depends(require_api_key),
):
    return db.search_loads(origin=origin, destination=destination, equipment_type=equipment_type)


@app.post("/calls")
async def log_call(record: CallRecord, _: bool = Depends(require_api_key)):
    call_id = db.insert_call(record.model_dump())
    return {"status": "stored", "call_id": call_id}


@app.get("/metrics", response_model=MetricsResponse)
async def metrics(_: bool = Depends(require_api_key)):
    return db.compute_metrics()