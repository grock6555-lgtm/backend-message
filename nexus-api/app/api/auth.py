from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from ..database import get_db
from ..models import User, UserSession
from ..schemas import UserCreate, UserLogin, UserResponse, Token, TOTPGenerateResponse, TOTPEnableRequest
from ..auth import hash_password, verify_password, create_access_token, create_refresh_token, get_current_user
from ..services.totp_client import generate_totp_secret, verify_totp_code
from ..services.blacklist_client import revoke_token
from ..services.kafka_logger import log_event
from ..utils.redis_client import redis_client
@router.get("/search")
async def search_users(q: str, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Поиск по username или номеру телефона"""
    q_like = f"%{q}%"
    result = await db.execute(
        select(User).where(
            (User.username.ilike(q_like)) | (User.phone_number.ilike(q_like)),
            User.deleted_at.is_(None),
            User.id != current_user.id
        ).limit(20)
    )
    users = result.scalars().all()
    return [{"id": u.id, "username": u.username, "display_name": u.display_name, "phone": u.phone_number} for u in users]