from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from ..database import get_db
from ..models import Message, Chat, ChatParticipant
from ..schemas import MessageSend, MessageResponse
from ..auth import get_current_user
from ..services.kafka_logger import log_event
from uuid import UUID
import json

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/", response_model=MessageResponse)
async def send_message(msg_data: MessageSend, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Проверка прав (участник чата)
    result = await db.execute(select(ChatParticipant).where(ChatParticipant.chat_id == msg_data.chat_id, ChatParticipant.user_id == current_user.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a participant")
    new_msg = Message(
        chat_id=msg_data.chat_id,
        sender_id=current_user.id,
        reply_to_message_id=msg_data.reply_to,
        text=msg_data.text,  # зашифрованный текст
        attachments=msg_data.attachments
    )
    db.add(new_msg)
    await db.commit()
    await db.refresh(new_msg)
    # Обновить last_message в чате
    await db.execute(
        Chat.update().where(Chat.id == msg_data.chat_id).values(
            last_message_id=new_msg.id,
            last_message_at=new_msg.created_at,
            last_message_snippet=(msg_data.text[:50] if msg_data.text else "[media]"),
            last_message_sender_id=current_user.id
        )
    )
    await db.commit()
    await log_event({"event": "message_sent", "chat_id": str(msg_data.chat_id), "user_id": str(current_user.id)})
    return new_msg

@router.get("/{chat_id}", response_model=list[MessageResponse])
async def get_messages(chat_id: UUID, limit: int = 50, offset: int = 0, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Проверка участия
    result = await db.execute(select(ChatParticipant).where(ChatParticipant.chat_id == chat_id, ChatParticipant.user_id == current_user.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a participant")
    result = await db.execute(
        select(Message).where(Message.chat_id == chat_id, Message.deleted_at.is_(None))
        .order_by(desc(Message.created_at)).offset(offset).limit(limit)
    )
    return result.scalars().all()