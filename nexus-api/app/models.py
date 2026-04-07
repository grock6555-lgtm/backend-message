from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer, JSON, Enum, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY, TSVECTOR
from sqlalchemy.sql import func
from .database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(20), unique=True, nullable=False)
    username = Column(String(32), unique=True, nullable=True)
    display_name = Column(String(100), nullable=False)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    status = Column(String(50), default="online")
    is_bot = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    email = Column(String(255), nullable=True, unique=True)
    password_hash = Column(String(255), nullable=False)   # <-- добавить
    totp_secret = Column(String(255), nullable=True)      # <-- добавить
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    password_hash = Column(String(255), nullable=False)
    totp_secret = Column(String(255), nullable=True)

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_name = Column(String(100))
    device_type = Column(String(20))
    push_token = Column(String(255))
    last_active_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)

class Chat(Base):
    __tablename__ = "chats"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum("personal", "group", "channel", "secret", name="chat_type"), nullable=False)
    title = Column(String(100))
    avatar_url = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    last_message_id = Column(UUID(as_uuid=True), nullable=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    last_message_snippet = Column(Text, nullable=True)
    last_message_sender_id = Column(UUID(as_uuid=True), nullable=True)

class ChatParticipant(Base):
    __tablename__ = "chat_participants"
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(Enum("owner", "admin", "member", name="participant_role"), default="member")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_read_message_id = Column(UUID(as_uuid=True), nullable=True)
    notifications_enabled = Column(Boolean, default=True)

class Message(Base):
    __tablename__ = "messages"
    ttl_seconds = Column(Integer, nullable=True)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reply_to_message_id = Column(UUID(as_uuid=True), nullable=True)
    text = Column(Text, nullable=True)
    attachments = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    search_vector = Column(TSVECTOR, nullable=True)

class File(Base):
    __tablename__ = "files"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), nullable=True)
    file_url = Column(Text, nullable=False)
    cdn_url = Column(Text, nullable=True)
    file_type = Column(String(50))
    mime_type = Column(String(100))
    file_size = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    duration_sec = Column(Integer)
    preview_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_voice = Column(Boolean, default=False)
    duration_sec = Column(Integer, nullable=True)  # уже есть

class E2EESession(Base):
    __tablename__ = "e2ee_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_a_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user_b_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_key = Column(Text, nullable=True)  # зашифрованный ключ сессии
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class E2EEPrekey(Base):
    __tablename__ = "e2ee_prekeys"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    prekey_id = Column(Integer, primary_key=True)
    prekey_data = Column(Text, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Bot(Base):
    __tablename__ = "bots"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    token_hash = Column(Text, nullable=False)
    webhook_url = Column(Text, nullable=True)
    webhook_events = Column(ARRAY(String), nullable=True)
    commands = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Дописать в конец файла models.py (уже существующие модели не трогаем)

class MessageReaction(Base):
    __tablename__ = "message_reactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reaction = Column(String(50), nullable=False)   # например, "❤️", "👍", "😂"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('message_id', 'user_id', name='unique_user_message_reaction'),)

class ChatInvite(Base):
    __tablename__ = "chat_invites"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)  # случайная строка
    expires_at = Column(DateTime(timezone=True), nullable=False)
    max_uses = Column(Integer, default=1)
    uses = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserContact(Base):
    __tablename__ = "user_contacts"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    contact_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    local_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
class Call(Base):
    __tablename__ = "calls"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caller_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    callee_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_sec = Column(Integer, nullable=True)
    status = Column(String(20), default="initiated")  # initiated, ringing, in_progress, missed, ended, rejected
    call_type = Column(String(20), default="video")   # video, audio
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CallParticipant(Base):
    __tablename__ = "call_participants"
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    joined_at = Column(DateTime(timezone=True), nullable=True)
    left_at = Column(DateTime(timezone=True), nullable=True)
    is_video_on = Column(Boolean, default=True)
    is_muted = Column(Boolean, default=False)