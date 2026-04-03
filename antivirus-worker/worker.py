import os
import json
import redis
import time

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=True
)

def process_task(task):
    file_id = task["file_id"]
    # Имитация проверки (без YARA)
    result = {"safe": True, "file_id": file_id, "note": "YARA disabled"}
    r.setex(f"antivirus:result:{file_id}", 3600, json.dumps(result))
    print(f"Processed {file_id}")

def worker():
    print("Antivirus worker started (YARA disabled)")
    while True:
        _, data = r.blpop("antivirus:scan")
        task = json.loads(data)
        process_task(task)

if __name__ == "__main__":
    worker()