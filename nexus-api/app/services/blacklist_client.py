import httpx
from ..config import settings

async def is_token_blacklisted(token: str) -> bool:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.BLACKLIST_SERVICE_URL}/check", params={"token": token})
        if resp.status_code == 200:
            return resp.json().get("blacklisted", False)
        return False

async def revoke_token(token: str, ttl: int = 604800):
    async with httpx.AsyncClient() as client:
        await client.post(f"{settings.BLACKLIST_SERVICE_URL}/revoke", json={"token": token, "ttl_seconds": ttl})