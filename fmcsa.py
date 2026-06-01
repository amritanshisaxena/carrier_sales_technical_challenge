"""FMCSA carrier verification.

Looks up a carrier by MC (docket) number against the FMCSA QCMobile API and decides
whether they're eligible to haul. If no webKey is configured, or the call fails/times
out, we fall back to a deterministic mock so a live demo never breaks on a slow
government API. That fallback is a deliberate reliability choice, not a shortcut —
and it's worth saying so in the interview.

NOTE: confirm the real FMCSA JSON shape against a live response once you have your
webKey. The parsing below is defensive and logs what it sees; adjust field names if
FMCSA returns something slightly different.
"""

import httpx

from config import settings
from schemas import CarrierVerification

FMCSA_BASE = "https://mobile.fmcsa.dot.gov/qc/services"

# MC numbers the mock treats as NOT eligible, so you can demo the rejection path
# (e.g. tell the agent your MC is 999999 to see it decline the carrier).
MOCK_INELIGIBLE = {"000000", "999999", "111111"}


def _mock_verify(mc_number: str) -> CarrierVerification:
    digits = mc_number.strip()
    if not digits.isdigit() or len(digits) < 5:
        return CarrierVerification(
            mc_number=mc_number,
            eligible=False,
            carrier_name=None,
            reason="MC number is not a valid format.",
            source="mock",
        )
    if digits in MOCK_INELIGIBLE:
        return CarrierVerification(
            mc_number=mc_number,
            eligible=False,
            carrier_name=f"Carrier {digits} LLC",
            reason="Carrier is not authorized to operate (mock).",
            source="mock",
        )
    return CarrierVerification(
        mc_number=mc_number,
        eligible=True,
        carrier_name=f"Carrier {digits} LLC",
        reason="Active and authorized to operate (mock).",
        source="mock",
    )


async def verify_carrier(mc_number: str) -> CarrierVerification:
    mc = mc_number.strip()

    # No key configured -> mock.
    if not settings.fmcsa_webkey:
        return _mock_verify(mc)

    url = f"{FMCSA_BASE}/carriers/docket-number/{mc}"
    params = {"webKey": settings.fmcsa_webkey}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        # Any network/parse error -> fall back so the call keeps moving.
        if settings.use_mock_fmcsa:
            return _mock_verify(mc)
        return CarrierVerification(
            mc_number=mc,
            eligible=False,
            carrier_name=None,
            reason="Could not verify carrier with FMCSA at this time.",
            source="fmcsa",
        )

    return _parse_fmcsa_response(data, mc)


def _parse_fmcsa_response(data: dict, mc: str) -> CarrierVerification:
    """Pure, testable parser for an FMCSA carrier response.

    Eligibility is NOT just `allowedToOperate`. A carrier can be allowed to operate
    federally yet have inactive for-hire authority, which means they can't legally haul
    our freight. So we require BOTH:
        - allowedToOperate == "Y", AND
        - active common OR contract operating authority (status "A").
    This mirrors how a real broker vets a carrier before tendering a load.
    """
    # content may be a dict (single carrier) or a list (matches) depending on endpoint.
    content = data.get("content")
    carrier = None
    if isinstance(content, list) and content:
        carrier = content[0].get("carrier") if isinstance(content[0], dict) else None
    elif isinstance(content, dict):
        carrier = content.get("carrier", content)

    if not carrier:
        return CarrierVerification(
            mc_number=mc, eligible=False, carrier_name=None,
            reason="No carrier found for that MC number.", source="fmcsa",
        )

    name = carrier.get("legalName") or carrier.get("dbaName")
    allowed = str(carrier.get("allowedToOperate", "")).upper() == "Y"
    common_active = str(carrier.get("commonAuthorityStatus", "")).upper() == "A"
    contract_active = str(carrier.get("contractAuthorityStatus", "")).upper() == "A"
    has_authority = common_active or contract_active

    eligible = allowed and has_authority
    if eligible:
        reason = "Active and authorized to operate with valid for-hire authority."
    elif not allowed:
        reason = "Carrier is not authorized to operate."
    else:
        reason = "Carrier does not have active for-hire operating authority."

    return CarrierVerification(
        mc_number=mc, eligible=eligible, carrier_name=name, reason=reason, source="fmcsa",
    )