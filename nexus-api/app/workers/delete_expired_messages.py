import asyncio
from datetime import datetime, timedelta
from sqlalchemy import delete
from app.database import AsyncSessionLocal
from app.models import Message

async def delete_expired_messages():
    while True:
        async with AsyncSessionLocal() as db:
            now = datetime.utcnow()
            stmt = delete(Message).where(
                Message.ttl_seconds.is_not(None),
                Message.created_at + timedelta(seconds=Message.ttl_seconds) < now
            )
            result = await db.execute(stmt)
            await db.commit()
            if result.rowcount:
                print(f"Deleted {result.rowcount} expired messages")
        await asyncio.sleep(60)  # каждую минуту

if __name__ == "__main__":
    asyncio.run(delete_expired_messages())