from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ..database import get_db
from ..models import Message, MessageReaction
from ..auth import get_current_user
from ..schemas import ReactionCreate
from ..api.ws import manager as ws_manager
from uuid import UUID

router = APIRouter(prefix="/messages", tags=["reactions"])

@router.post("/{message_id}/reaction")
async def add_reaction(message_id: UUID, reaction_data: ReactionCreate, 
                       current_user=Depends(get_current_user), 
                       db: AsyncSession = Depends(get_db)):
    # Проверка существования сообщения
    msg_result = await db.execute(select(Message).where(Message.id == message_id))
    msg = msg_result.scalar_one_or_none()
    if not msg:
        raise HTTPException(404, "Message not found")
    # Удаляем старую реакцию, если есть
    await db.execute(delete(MessageReaction).where(
        MessageReaction.message_id == message_id,
        MessageReaction.user_id == current_user.id
    ))
    # Добавляем новую
    reaction = MessageReaction(
        message_id=message_id,
        user_id=current_user.id,
        reaction=reaction_data.reaction
    )
    db.add(reaction)
    await db.commit()
    # Отправляем уведомление через WebSocket
    await ws_manager.send_personal(str(msg.sender_id), {
        "type": "reaction",
        "message_id": str(message_id),
        "user_id": str(current_user.id),
        "reaction": reaction_data.reaction
    })
    return {"status": "added"}

@router.delete("/{message_id}/reaction")
async def remove_reaction(message_id: UUID, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(MessageReaction).where(
        MessageReaction.message_id == message_id,
        MessageReaction.user_id == current_user.id
    ))
    await db.commit()
    return {"status": "removed"}