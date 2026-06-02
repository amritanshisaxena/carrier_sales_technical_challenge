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

from fastapi import FastAPI, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import db
from auth import require_api_key
from schemas import Load, CallRecord, MetricsResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Inbound Carrier Sales API", version="1.0.0", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "metrics": db.compute_metrics(),
            "calls": db.fetch_calls()[:15],
            "dashboard_data": db.compute_dashboard_data(),
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