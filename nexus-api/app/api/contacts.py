from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import User, UserContact
from ..auth import get_current_user
from ..schemas import ContactSyncRequest, ContactSyncResponse
from uuid import UUID

router = APIRouter(prefix="/contacts", tags=["contacts"])

@router.post("/sync", response_model=list[ContactSyncResponse])
async def sync_contacts(sync_data: ContactSyncRequest, 
                        current_user=Depends(get_current_user), 
                        db: AsyncSession = Depends(get_db)):
    # Получаем список номеров из запроса
    phone_numbers = sync_data.phone_numbers
    # Находим зарегистрированных пользователей
    result = await db.execute(select(User).where(User.phone_number.in_(phone_numbers), User.deleted_at.is_(None)))
    users = result.scalars().all()
    # Для каждого найденного пользователя создаём запись в контактах (если ещё нет)
    for user in users:
        existing = await db.execute(select(UserContact).where(
            UserContact.user_id == current_user.id,
            UserContact.contact_user_id == user.id
        ))
        if not existing.scalar_one_or_none():
            new_contact = UserContact(
                user_id=current_user.id,
                contact_user_id=user.id
            )
            db.add(new_contact)
    await db.commit()
    # Возвращаем список найденных пользователей
    return [ContactSyncResponse(id=u.id, phone_number=u.phone_number, display_name=u.display_name, username=u.username) for u in users]

@router.get("/", response_model=list[ContactSyncResponse])
async def get_contacts(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).join(UserContact, UserContact.contact_user_id == User.id).where(UserContact.user_id == current_user.id)
    )
    return result.scalars().all()