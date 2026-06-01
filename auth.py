"""API key authentication.

Every protected endpoint depends on require_api_key. The caller (the HappyRobot
agent's Webhook node, and your dashboard) must send the key in the X-API-Key header.
This satisfies the challenge's "API key authentication for all endpoints" requirement.
"""

from fastapi import Header, HTTPException, status

from config import settings


async def require_api_key(x_api_key: str = Header(default="")) -> bool:
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
    return True
