"""Negotiation engine.

Design choice worth defending in the interview:
The decision logic is a PURE function (`decide`) — same inputs always give the same
output, no LLM, no randomness, no I/O. The agent on the HappyRobot side is great at
*conversation*, but you do not want a language model freelancing on price. Keeping the
money logic here makes it deterministic, unit-testable, and auditable. The agent just
relays the result.

Round-counting is also server-side (see db.negotiation_sessions) rather than asking the
model to count "back-and-forths" itself, because LLMs are unreliable at counting.

Policy:
  ceiling = loadboard_rate * (1 + BROKER_MAX_UPLIFT)   # most the broker will pay
  - carrier asks <= ceiling           -> ACCEPT at the carrier's number
  - carrier asks > ceiling, rounds left -> COUNTER at the midpoint of our last offer
                                           and their ask, capped at the ceiling
  - carrier asks > ceiling, no rounds left -> REJECT and walk away
"""

from typing import Tuple

from config import settings


def decide(
    carrier_offer: float,
    loadboard_rate: float,
    last_broker_offer: float,
    round_number: int,
) -> Tuple[str, float, str]:
    """Return (decision, broker_offer, message).

    decision is one of "accept" | "counter" | "reject".
    round_number is this round's index (1-based).
    """
    ceiling = round(loadboard_rate * (1 + settings.broker_max_uplift), 2)

    # Within budget -> take it.
    if carrier_offer <= ceiling:
        return (
            "accept",
            round(carrier_offer, 2),
            f"Great, we can do ${carrier_offer:,.0f} on this load. Let's lock it in.",
        )

    # Over budget and out of rounds -> walk away.
    if round_number >= settings.max_negotiation_rounds:
        return (
            "reject",
            last_broker_offer,
            f"I understand, but ${carrier_offer:,.0f} is above what we can pay on this "
            f"lane. Our best is ${last_broker_offer:,.0f}. If that doesn't work I "
            f"completely understand.",
        )

    # Over budget but rounds remain -> meet partway, never above the ceiling.
    midpoint = (last_broker_offer + carrier_offer) / 2
    counter = round(min(ceiling, midpoint), 2)
    # Make sure we actually move up from our last offer so it reads as a real counter.
    if counter <= last_broker_offer:
        counter = round(min(ceiling, last_broker_offer + 50), 2)

    return (
        "counter",
        counter,
        f"I can't get to ${carrier_offer:,.0f}, but I can come up to ${counter:,.0f}. "
        f"Does that work for you?",
    )
