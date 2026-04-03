import json
from kafka import KafkaConsumer
from elasticsearch import Elasticsearch
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

es = Elasticsearch(os.getenv("ELASTICSEARCH_HOST", "http://elasticsearch:9200"))
consumer = KafkaConsumer(
    "security-logs",
    bootstrap_servers=os.getenv("KAFKA_HOST", "kafka:9092"),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda m: m.decode()  # оставляем как строку, потом разберём
)

for msg in consumer:
    try:
        log = json.loads(msg.value)
        log["@timestamp"] = datetime.utcnow().isoformat()
        # Анонимизация (опционально)
        if "user_id" in log:
            # log["user_id_hash"] = ... (пока пропустим)
            pass
        es.index(index="security-logs", body=log)
        logger.info(f"Indexed log: {log.get('event')}")
    except Exception as e:
        logger.error(f"Failed to process message: {msg.value}, error: {e}")