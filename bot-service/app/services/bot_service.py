from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import bcrypt
import secrets
from ..models.db_models import Bot
from ..models.schemas import BotCreate
from fastapi import HTTPException

class BotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_bot(self, data: BotCreate):
        token = secrets.token_urlsafe(32)
        token_hash = bcrypt.hashpw(token.encode(), bcrypt.gensalt()).decode()
        user_id = UUID(int=secrets.randbits(128))
        bot = Bot(
            user_id=user_id,
            token_hash=token_hash,
            webhook_url=str(data.webhook_url) if data.webhook_url else None,
            webhook_events=data.events,
            commands=[]
        )
        self.db.add(bot)
        await self.db.commit()
        await self.db.refresh(bot)
        return {
            "id": bot.user_id,
            "name": data.name,
            "username": data.username,
            "token": token,
            "webhook_url": bot.webhook_url,
            "created_at": bot.created_at.isoformat()
        }

    async def set_webhook(self, bot_id: str, url: str, events: list):
        result = await self.db.execute(select(Bot).where(Bot.user_id == bot_id))
        bot = result.scalar_one_or_none()
        if not bot:
            raise HTTPException(404, "Bot not found")
        bot.webhook_url = url
        bot.webhook_events = events
        await self.db.commit()

    async def get_bot(self, bot_id: str):
        result = await self.db.execute(select(Bot).where(Bot.user_id == bot_id))
        return result.scalar_one_or_none()