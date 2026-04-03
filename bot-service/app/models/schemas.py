from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from uuid import UUID

class BotCreate(BaseModel):
    name: str
    username: str
    webhook_url: Optional[HttpUrl] = None
    events: List[str] = []

class BotResponse(BaseModel):
    id: UUID
    name: str
    username: str
    token: str
    webhook_url: Optional[HttpUrl]
    created_at: str

class BotWebhookUpdate(BaseModel):
    url: HttpUrl
    events: List[str]