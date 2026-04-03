import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import pyotp
import redis
from adaptive_limiter import get_delay, record_failure, reset_failures
from recovery_codes import generate_recovery_codes, hash_recovery_codes, verify_recovery_code

app = FastAPI()

# Подключение к Redis с паролем
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

class GenerateRequest(BaseModel):
    user_id: str

class VerifyRequest(BaseModel):
    user_id: str
    secret: str
    code: str

class RecoveryGenerateResponse(BaseModel):
    codes: List[str]
    hashes: List[str]

@app.post("/generate")
async def generate_totp(req: GenerateRequest):
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=req.user_id, issuer_name="NexusChat")
    return {"secret": secret, "provisioning_uri": uri}

@app.post("/verify")
async def verify_totp(req: VerifyRequest):
    delay = get_delay(req.user_id)
    if delay > 0:
        time.sleep(delay)
    totp = pyotp.TOTP(req.secret)
    if not totp.verify(req.code, valid_window=1):
        record_failure(req.user_id)
        raise HTTPException(400, "Invalid TOTP code")
    reset_failures(req.user_id)
    return {"valid": True}

@app.post("/recovery/generate", response_model=RecoveryGenerateResponse)
async def generate_recovery(req: GenerateRequest):
    codes = generate_recovery_codes()
    hashes = hash_recovery_codes(codes)
    return {"codes": codes, "hashes": hashes}

@app.post("/recovery/verify")
async def verify_recovery(req: dict):
    if verify_recovery_code(req["code"], req["hashed_code"]):
        return {"valid": True}
    raise HTTPException(400, "Invalid recovery code")

@app.get("/health")
async def health():
    return {"status": "ok"}