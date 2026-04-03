import hashlib
import os
import redis
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

class RevokeRequest(BaseModel):
    token: str
    ttl_seconds: int = 604800

@app.post("/revoke")
async def revoke(req: RevokeRequest):
    token_hash = hashlib.sha256(req.token.encode()).hexdigest()
    r.setex(f"blacklist:{token_hash}", req.ttl_seconds, "revoked")
    return {"status": "revoked"}

@app.get("/check")
async def check(token: str):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    if r.exists(f"blacklist:{token_hash}"):
        return {"blacklisted": True}
    return {"blacklisted": False}

@app.get("/health")
async def health():
    return {"status": "ok"}