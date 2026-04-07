from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

# ========== User ==========
class UserCreate(BaseModel):
    phone_number: str
    username: Optional[str] = Field(None, min_length=3, max_length=20, pattern=r'^[a-zA-Z0-9_]+$')
    display_name: str
    password: str

class UserLogin(BaseModel):
    phone_number: str
    password: str
    totp_code: Optional[str] = None

class UserResponse(BaseModel):
    id: UUID
    phone_number: str
    username: Optional[str]
    display_name: str
    avatar_url: Optional[str]
    bio: Optional[str]
    status: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TOTPEnableRequest(BaseModel):
    user_id: UUID
    secret: str
    code: str

class TOTPGenerateResponse(BaseModel):
    secret: str
    provisioning_uri: str

# ========== Chat ==========
class ChatCreate(BaseModel):
    type: str  # personal, group, channel, secret
    title: Optional[str] = None
    participant_ids: List[UUID]

class ChatResponse(BaseModel):
    id: UUID
    type: str
    title: Optional[str]
    avatar_url: Optional[str]
    created_by: UUID
    created_at: datetime
    participants: List[UserResponse]

# ========== Message ==========
class MessageSend(BaseModel):
    chat_id: UUID
    text: Optional[str] = None
    attachments: Optional[List[Dict]] = None
    reply_to: Optional[UUID] = None
    ttl_seconds: Optional[int] = None
    is_voice: bool = False

class MessageResponse(BaseModel):
    id: UUID
    chat_id: UUID
    sender_id: UUID
    text: Optional[str]
    attachments: Optional[List[Dict]]
    created_at: datetime

# ========== File ==========
class FileUploadResponse(BaseModel):
    file_id: UUID
    upload_url: str
    file_url: str

# ========== Prekey ==========
class PrekeyPublish(BaseModel):
    prekey_id: int
    prekey_data: str
    signature: str

class PrekeyResponse(BaseModel):
    user_id: UUID
    prekey_id: int
    prekey_data: str
    signature: str

# ========== Contact ==========
class ContactSyncRequest(BaseModel):
    phone_numbers: List[str]

class ContactSyncResponse(BaseModel):
    id: UUID
    phone_number: str
    display_name: Optional[str]
    username: Optional[str]

# ========== Invite ==========
class InviteCreateResponse(BaseModel):
    token: str
    link: str
    expires_at: datetime

# ========== Reaction ==========
class ReactionCreate(BaseModel):
    reaction: str

# ========== Sticker ==========
class StickerPackResponse(BaseModel):
    id: UUID
    title: str
    author_id: Optional[UUID]
    is_official: bool

class StickerResponse(BaseModel):
    id: UUID
    pack_id: UUID
    emoji: Optional[str]
    image_url: str
# ========== Call ==========
class CallStartRequest(BaseModel):
    to_user_id: UUID
    call_type: str = "video"

class CallResponse(BaseModel):
    call_id: UUID
    from_user: UUID
    to_user: UUID
    status: str
    started_at: datetime