from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..services.bot_service import BotService
from ..models.schemas import BotCreate, BotResponse, BotWebhookUpdate
from ..redis_client import redis_client
import json

router = APIRouter(prefix="/bots", tags=["bots"])

@router.post("/", response_model=BotResponse, status_code=201)
async def create_bot(bot_data: BotCreate, db: AsyncSession = Depends(get_db)):
    service = BotService(db)
    return await service.create_bot(bot_data)

@router.post("/{bot_id}/webhook")
async def set_webhook(bot_id: str, webhook_data: BotWebhookUpdate, db: AsyncSession = Depends(get_db)):
    service = BotService(db)
    await service.set_webhook(bot_id, str(webhook_data.url), webhook_data.events)
    return {"status": "ok"}

@router.post("/{bot_id}/send")
async def send_message(bot_id: str, message_data: dict, db: AsyncSession = Depends(get_db)):
    service = BotService(db)
    bot = await service.get_bot(bot_id)
    if not bot:
        raise HTTPException(404, "Bot not found")
    payload = {
        "bot_id": bot_id,
        "chat_id": message_data["chat_id"],
        "text": message_data["text"],
        "attachments": message_data.get("attachments", [])
    }
    await redis_client.publish("bot:outgoing", json.dumps(payload))
    return {"status": "queued"}