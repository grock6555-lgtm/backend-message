from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import secrets
from ..database import get_db
from ..models import ChatInvite, Chat, ChatParticipant
from ..auth import get_current_user
from ..schemas import InviteCreateResponse, JoinLinkRequest
from uuid import UUID

router = APIRouter(prefix="/chats", tags=["invites"])

@router.post("/{chat_id}/invite-link", response_model=InviteCreateResponse)
async def create_invite_link(chat_id: UUID, expires_hours: int = 24, max_uses: int = 1,
                             current_user=Depends(get_current_user), 
                             db: AsyncSession = Depends(get_db)):
    # Проверяем, что пользователь – участник чата
    participant = await db.execute(select(ChatParticipant).where(
        ChatParticipant.chat_id == chat_id,
        ChatParticipant.user_id == current_user.id
    ))
    if not participant.scalar_one_or_none():
        raise HTTPException(403, "Not a participant")
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
    invite = ChatInvite(
        chat_id=chat_id,
        created_by=current_user.id,
        token=token,
        expires_at=expires_at,
        max_uses=max_uses
    )
    db.add(invite)
    await db.commit()
    return InviteCreateResponse(token=token, link=f"https://nexus.chat/join/{token}", expires_at=expires_at)

@router.post("/join/{token}")
async def join_by_link(token: str, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    invite = await db.execute(select(ChatInvite).where(ChatInvite.token == token))
    invite = invite.scalar_one_or_none()
    if not invite:
        raise HTTPException(404, "Invalid invite")
    if invite.expires_at < datetime.utcnow():
        raise HTTPException(400, "Invite expired")
    if invite.uses >= invite.max_uses:
        raise HTTPException(400, "Invite already used")
    # Добавляем пользователя в чат
    existing = await db.execute(select(ChatParticipant).where(
        ChatParticipant.chat_id == invite.chat_id,
        ChatParticipant.user_id == current_user.id
    ))
    if not existing.scalar_one_or_none():
        new_participant = ChatParticipant(
            chat_id=invite.chat_id,
            user_id=current_user.id
        )
        db.add(new_participant)
        invite.uses += 1
        await db.commit()
    return {"status": "added", "chat_id": str(invite.chat_id)}