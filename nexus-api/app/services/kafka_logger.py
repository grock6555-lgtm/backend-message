from kafka import KafkaProducer
import json
import asyncio
from ..config import settings

producer = None

def get_producer():
    global producer
    if producer is None:
        producer = KafkaProducer(bootstrap_servers=settings.KAFKA_HOST, value_serializer=lambda v: json.dumps(v).encode())
    return producer

async def log_event(event: dict):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: get_producer().send("security-logs", event))