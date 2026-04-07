from minio import Minio
from ..config import settings

minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False
)

def create_presigned_upload_url(bucket: str, object_name: str, expiry: int = 300) -> str:
    return minio_client.presigned_put_object(bucket, object_name, expires=timedelta(seconds=expiry))

def create_presigned_download_url(bucket: str, object_name: str, expiry: int = 3600) -> str:
    return minio_client.presigned_get_object(bucket, object_name, expires=timedelta(seconds=expiry))