import httpx
from sqlalchemy import select
from ..models.db_models import Bot
from ..database import AsyncSessionLocal

async def deliver_webhook(data: dict):
    bot_id = data.get("bot_id")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Bot).where(Bot.user_id == bot_id))
        bot = result.scalar_one_or_none()
        if not bot or not bot.webhook_url:
            return
        async with httpx.AsyncClient() as client:
            try:
                await client.post(bot.webhook_url, json=data, timeout=5)
            except Exception as e:
                print(f"Webhook delivery failed for {bot_id}: {e}")