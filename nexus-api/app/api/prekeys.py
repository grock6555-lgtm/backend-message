from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import E2EEPrekey, User
from ..schemas import PrekeyPublish, PrekeyResponse
from ..auth import get_current_user
from ..services.crypto import verify_prekey
from uuid import UUID

router = APIRouter(prefix="/prekeys", tags=["prekeys"])

@router.post("/publish")
async def publish_prekey(prekey_data: PrekeyPublish, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Проверить подпись (серверная проверка, если нужно)
    # Здесь можно вызвать verify_prekey, если сервер знает публичный ключ
    existing = await db.execute(select(E2EEPrekey).where(E2EEPrekey.user_id == current_user.id, E2EEPrekey.prekey_id == prekey_data.prekey_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Prekey already exists")
    new_prekey = E2EEPrekey(
        user_id=current_user.id,
        prekey_id=prekey_data.prekey_id,
        prekey_data=prekey_data.prekey_data,
        used=False
    )
    db.add(new_prekey)
    await db.commit()
    return {"status": "published"}

@router.get("/{user_id}", response_model=list[PrekeyResponse])
async def get_prekeys(user_id: UUID, limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(E2EEPrekey).where(E2EEPrekey.user_id == user_id, E2EEPrekey.used == False)
        .order_by(E2EEPrekey.created_at).limit(limit)
    )
    prekeys = result.scalars().all()
    # Отмечаем их как used (клиент должен забрать и удалить с сервера)
    for p in prekeys:
        p.used = True
    await db.commit()
    return prekeys