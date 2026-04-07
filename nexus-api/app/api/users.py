from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import User, UserSession
from ..schemas import UserCreate, UserLogin, UserResponse, Token, TOTPGenerateResponse, TOTPEnableRequest
from ..auth import hash_password, verify_password, create_access_token, create_refresh_token, get_current_user
from ..services.totp_client import generate_totp_secret, verify_totp_code
from ..services.blacklist_client import revoke_token
from ..services.kafka_logger import log_event
import uuid
import segno
from io import BytesIO
from uuid import UUID
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Проверка уникальности
    existing = await db.execute(select(User).where((User.phone_number == user_data.phone_number) | (User.username == user_data.username)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone or username already exists")
    hashed = hash_password(user_data.password)
    new_user = User(
        phone_number=user_data.phone_number,
        username=user_data.username,
        display_name=user_data.display_name,
        password_hash=hashed  # добавьте поле password_hash в модель User!
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    await log_event({"event": "user_registered", "user_id": str(new_user.id), "phone": user_data.phone_number})
    return new_user

@router.get("/me/qr")
async def get_my_qr(current_user=Depends(get_current_user)):
    # Данные для QR: ссылка на профиль в формате глубокой ссылки
    qr_data = f"https://nexus.chat/add/{current_user.id}"  # или nexus://user/{current_user.id}
    qr = segno.make(qr_data, error='H')
    img_bytes = BytesIO()
    qr.save(img_bytes, kind='png', scale=8)
    img_bytes.seek(0)
    return StreamingResponse(img_bytes, media_type="image/png")

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone_number == login_data.phone_number))
    user = result.scalar_one_or_none()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # 2FA
    if user.totp_secret:  # предполагаем поле totp_secret в User
        if not login_data.totp_code:
            raise HTTPException(status_code=401, detail="TOTP required")
        if not await verify_totp_code(str(user.id), user.totp_secret, login_data.totp_code):
            raise HTTPException(status_code=401, detail="Invalid TOTP")
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    await log_event({"event": "user_login", "user_id": str(user.id), "success": True})
    return {"access_token": access_token, "refresh_token": refresh_token}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout")
async def logout(token: str, current_user: User = Depends(get_current_user)):
    await revoke_token(token)
    return {"status": "logged out"}

@router.post("/2fa/generate", response_model=TOTPGenerateResponse)
async def generate_2fa(current_user: User = Depends(get_current_user)):
    data = await generate_totp_secret(str(current_user.id))
    return data

@router.post("/2fa/enable")
async def enable_2fa(req: TOTPEnableRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not await verify_totp_code(str(current_user.id), req.secret, req.code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")
    current_user.totp_secret = req.secret
    await db.commit()
    return {"status": "enabled"}
@router.get("/{user_id}/status")
async def get_user_status(user_id: UUID):
    is_online = await redis_client.exists(f"user_online:{user_id}")
    return {"user_id": user_id, "online": is_online == 1, "last_seen": None}  # можно добавить last_seen
@router.get("/find")
async def find_user(identifier: str, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Найти пользователя по username (с @ или без), номеру телефона или ID"""
    if identifier.startswith("@"):
        identifier = identifier[1:]
    result = await db.execute(
        select(User).where(
            (User.username == identifier) | (User.phone_number == identifier) | (User.id == identifier),
            User.deleted_at.is_(None),
            User.id != current_user.id
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return {"id": user.id, "username": user.username, "display_name": user.display_name, "phone": user.phone_number, "avatar": user.avatar_url}