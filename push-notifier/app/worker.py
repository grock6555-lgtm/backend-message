import asyncio
import json
import logging
from .redis_client import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_push(task: dict):
    logger.info(f"Push task: {task}")

async def listen():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("push:tasks")
    logger.info("Listening on push:tasks")
    async for message in pubsub.listen():
        if message["type"] == "message":
            task = json.loads(message["data"])
            asyncio.create_task(process_push(task))

if __name__ == "__main__":
    asyncio.run(listen())