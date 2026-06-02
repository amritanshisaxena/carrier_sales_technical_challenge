from typing import Optional
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


class CallRecord(BaseModel):
    mc_number: Optional[str] = None
    carrier_name: Optional[str] = None
    load_id: Optional[str] = None
    outcome: str
    agreed_rate: Optional[float] = None
    loadboard_rate: Optional[float] = None
    negotiation_rounds: Optional[int] = None
    sentiment: Optional[str] = None
    transcript: Optional[str] = None


class MetricsResponse(BaseModel):
    total_calls: int
    outcomes: dict
    sentiment: dict
    booking_rate: float
    avg_negotiation_rounds: Optional[float]
    avg_agreed_rate: Optional[float]
    avg_loadboard_rate_on_booked: Optional[float]
    avg_margin_delta: Optional[float]
    not_eligible_count: int
