from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import StickerPack, Sticker, File
from ..auth import get_current_user
from ..schemas import StickerPackResponse, StickerResponse
from uuid import UUID

router = APIRouter(prefix="/stickers", tags=["stickers"])

@router.get("/packs", response_model=list[StickerPackResponse])
async def get_sticker_packs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StickerPack).where(StickerPack.is_official == True))
    packs = result.scalars().all()
    return packs

@router.get("/pack/{pack_id}", response_model=list[StickerResponse])
async def get_stickers_by_pack(pack_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Sticker).where(Sticker.pack_id == pack_id))
    return result.scalars().all()