import httpx
from ..config import settings

async def generate_totp_secret(user_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{settings.TOTP_SERVICE_URL}/generate", json={"user_id": user_id})
        resp.raise_for_status()
        return resp.json()

async def verify_totp_code(user_id: str, secret: str, code: str) -> bool:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{settings.TOTP_SERVICE_URL}/verify", json={"user_id": user_id, "secret": secret, "code": code})
        if resp.status_code == 200:
            return resp.json().get("valid", False)
        return False
# Синоним для обратной совместимости
verify_totp = verify_totp_code