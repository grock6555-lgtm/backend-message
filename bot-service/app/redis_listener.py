import asyncio
import json
import logging
from .redis_client import redis_client
from .services.webhook_delivery import deliver_webhook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def listen_to_redis():
    logger.info("Starting Redis listener for bot:incoming")
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("bot:incoming")
    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            logger.info(f"Received message: {data}")
            asyncio.create_task(deliver_webhook(data))