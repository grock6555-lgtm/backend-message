from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import File
from ..schemas import FileUploadResponse
from ..auth import get_current_user
from ..services.minio_client import create_presigned_upload_url
from ..services.antivirus_client import queue_file_scan
import uuid

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload", response_model=FileUploadResponse)
async def request_upload(filename: str, file_type: str, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    file_id = uuid.uuid4()
    object_name = f"{current_user.id}/{file_id}/{filename}"
    upload_url = create_presigned_upload_url("attachments", object_name)
    file_url = f"/files/{file_id}"  # будет редирект на presigned download
    new_file = File(id=file_id, file_url=file_url, mime_type=file_type, file_size=0)
    db.add(new_file)
    await db.commit()
    # После загрузки клиент уведомит сервер, что файл загружен (можно через callback)
    return FileUploadResponse(file_id=file_id, upload_url=upload_url, file_url=file_url)

@router.post("/upload/complete/{file_id}")
async def upload_complete(file_id: uuid.UUID, bucket: str, object_name: str, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Клиент сообщает, что файл загружен. Отправляем на антивирус.
    await queue_file_scan(str(file_id), bucket, object_name)
    return {"status": "scan_queued"}