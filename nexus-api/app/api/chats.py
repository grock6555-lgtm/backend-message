from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import Chat, ChatParticipant, User
from ..schemas import ChatCreate, ChatResponse, UserResponse
from ..auth import get_current_user
from uuid import UUID

router = APIRouter(prefix="/chats", tags=["chats"])

@router.post("/", response_model=ChatResponse)
async def create_chat(chat_data: ChatCreate, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Создаём чат
    new_chat = Chat(
        type=chat_data.type,
        title=chat_data.title,
        created_by=current_user.id
    )
    db.add(new_chat)
    await db.flush()
    # Добавляем участников
    participants = set(chat_data.participant_ids) | {current_user.id}
    for uid in participants:
        participant = ChatParticipant(chat_id=new_chat.id, user_id=uid)
        db.add(participant)
    await db.commit()
    await db.refresh(new_chat)
    return new_chat

@router.get("/", response_model=list[ChatResponse])
async def get_my_chats(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chat).join(ChatParticipant).where(ChatParticipant.user_id == current_user.id, Chat.deleted_at.is_(None))
    )
    chats = result.scalars().all()
    return chats