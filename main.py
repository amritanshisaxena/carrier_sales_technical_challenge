"""FastAPI app: the carrier-facing API the HappyRobot agent calls, plus the
endpoints that feed the ops dashboard.

Endpoints (all require the X-API-Key header except /health):
  GET  /health           -> liveness check (open, used by Render)
  GET  /verify-carrier   -> FMCSA eligibility check
  GET  /loads            -> search available loads
  POST /evaluate-offer   -> deterministic negotiation decision (server-side rounds)
  POST /calls            -> store a completed call (posted by the post-call webhook)
  GET  /metrics          -> aggregated stats for the dashboard

The dashboard route (GET /) is added later once we build the Jinja page.
"""

from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import db
from auth import require_api_key
from fmcsa import verify_carrier
from negotiation import decide
from schemas import (
    Load,
    CarrierVerification,
    OfferRequest,
    OfferResponse,
    CallRecord,
    MetricsResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()  # create tables + seed loads on startup
    yield


app = FastAPI(title="Inbound Carrier Sales API", version="1.0.0", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Ops dashboard. Rendered server-side from the DB, so no API key is exposed in
    the browser and the team can view it openly. Data endpoints stay key-protected."""
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"metrics": db.compute_metrics(), "calls": db.fetch_calls()[:15]},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/verify-carrier", response_model=CarrierVerification)
async def verify(mc: str = Query(..., description="Carrier MC / docket number"),
                 _: bool = Depends(require_api_key)):
    return await verify_carrier(mc)


@app.get("/loads", response_model=List[Load])
async def loads(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    equipment_type: Optional[str] = None,
    _: bool = Depends(require_api_key),
):
    return db.search_loads(origin=origin, destination=destination, equipment_type=equipment_type)


@app.post("/evaluate-offer", response_model=OfferResponse)
async def evaluate_offer(req: OfferRequest, _: bool = Depends(require_api_key)):
    load = db.get_load(req.load_id)
    if not load:
        raise HTTPException(status_code=404, detail="Load not found.")

    session = db.get_or_create_session(req.mc_number, req.load_id, load["loadboard_rate"])
    this_round = session["round_count"] + 1

    decision, broker_offer, message = decide(
        carrier_offer=req.carrier_offer,
        loadboard_rate=load["loadboard_rate"],
        last_broker_offer=session["last_broker_offer"],
        round_number=this_round,
    )

    status = {"accept": "accepted", "reject": "rejected", "counter": "open"}[decision]
    db.update_session(session["session_key"], broker_offer, this_round, status)

    return OfferResponse(decision=decision, round=this_round, broker_offer=broker_offer, message=message)


@app.post("/calls")
async def log_call(record: CallRecord, _: bool = Depends(require_api_key)):
    payload = record.model_dump()

    # If the platform didn't send negotiation_rounds, backfill from our session store.
    if payload.get("negotiation_rounds") is None and payload.get("mc_number") and payload.get("load_id"):
        session = db._fetch_session(payload["mc_number"], payload["load_id"])  # type: ignore[attr-defined]
        if session:
            payload["negotiation_rounds"] = session["round_count"]
            if payload.get("loadboard_rate") is None:
                payload["loadboard_rate"] = session["loadboard_rate"]

    call_id = db.insert_call(payload)
    return {"status": "stored", "call_id": call_id}


@app.get("/metrics", response_model=MetricsResponse)
async def metrics(_: bool = Depends(require_api_key)):
    return db.compute_metrics()