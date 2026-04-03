import os
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

def get_delay(user_id: str) -> int:
    fails = r.get(f"totp:fails:{user_id}")
    if not fails:
        return 0
    fails = int(fails)
    return min(30 + max(0, (fails - 3)) * 5, 300)

def record_failure(user_id: str):
    fails = r.incr(f"totp:fails:{user_id}")
    if fails == 1:
        r.expire(f"totp:fails:{user_id}", 600)

def reset_failures(user_id: str):
    r.delete(f"totp:fails:{user_id}")