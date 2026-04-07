import redis.asyncio as redis
import json
from ..config import settings

redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD, decode_responses=True)

async def queue_file_scan(file_id: str, bucket: str, object_name: str):
    task = {"file_id": file_id, "bucket": bucket, "object_name": object_name}
    await redis_client.lpush("antivirus:scan", json.dumps(task))

async def get_scan_result(file_id: str) -> dict | None:
    data = await redis_client.get(f"antivirus:result:{file_id}")
    if data:
        return json.loads(data)
    return None