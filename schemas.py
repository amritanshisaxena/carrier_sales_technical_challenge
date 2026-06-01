"""Request and response shapes.

Pydantic models give you automatic validation and clean JSON. They also make the
auto-generated API docs (at /docs) readable, which is handy in the demo video.
"""

from typing import Optional, List
from pydantic import BaseModel


class Load(BaseModel):
    load_id: str
    origin: str
    destination: str
    pickup_datetime: str
    delivery_datetime: str
    equipment_type: str
    loadboard_rate: float
    notes: Optional[str] = None
    weight: Optional[float] = None
    commodity_type: Optional[str] = None
    num_of_pieces: Optional[int] = None
    miles: Optional[float] = None
    dimensions: Optional[str] = None


class CarrierVerification(BaseModel):
    mc_number: str
    eligible: bool
    carrier_name: Optional[str] = None
    reason: str
    source: str  # "fmcsa" or "mock"


class OfferRequest(BaseModel):
    mc_number: str
    load_id: str
    carrier_offer: float


class OfferResponse(BaseModel):
    decision: str          # "accept" | "counter" | "reject"
    round: int             # which negotiation round this was (1-based)
    broker_offer: float    # the number the broker is now standing behind
    message: str           # human-readable line the agent can relay to the carrier


class CallRecord(BaseModel):
    """What the HappyRobot post-call Webhook node POSTs to /calls.

    The platform's AI Extract node + classifiers produce these fields. Everything
    is optional except outcome, because a call can end at any stage.
    """
    mc_number: Optional[str] = None
    carrier_name: Optional[str] = None
    load_id: Optional[str] = None
    outcome: str  # "booked" | "declined" | "no_agreement" | "not_eligible"
    agreed_rate: Optional[float] = None
    loadboard_rate: Optional[float] = None
    negotiation_rounds: Optional[int] = None
    sentiment: Optional[str] = None  # "positive" | "neutral" | "negative"
    transcript: Optional[str] = None


class MetricsResponse(BaseModel):
    total_calls: int
    outcomes: dict
    sentiment: dict
    booking_rate: float
    avg_negotiation_rounds: Optional[float]
    avg_agreed_rate: Optional[float]
    avg_loadboard_rate_on_booked: Optional[float]
    avg_margin_delta: Optional[float]   # agreed - loadboard on booked loads
    not_eligible_count: int
