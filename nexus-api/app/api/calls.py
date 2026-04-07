# app/models.py
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Boolean, Text, ForeignKey, Integer, JSON, 
    Enum, Index, UniqueConstraint, BigInteger, ARRAY, Float, Table
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

# ==============================
# 1. Пользователи и сессии
# ==============================

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
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    totp_secret = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_users_phone", "phone_number"),
        Index("idx_users_username", "username", postgresql_where=username.isnot(None)),
        Index("idx_users_deleted_at", "deleted_at", postgresql_where=deleted_at.is_(None)),
    )

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_name = Column(String(100), nullable=True)
    device_type = Column(String(20), nullable=True)
    push_token = Column(String(255), nullable=True)
    last_active_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_sessions_user", "user_id"),
        Index("idx_sessions_revoked", "revoked_at", postgresql_where=revoked_at.is_(None)),
        UniqueConstraint("user_id", "device_name", name="uq_user_device"),
    )

# ==============================
# 2. Чаты и участники
# ==============================

class Chat(Base):
    __tablename__ = "chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum("personal", "group", "channel", "secret", name="chat_type"), nullable=False)
    title = Column(String(100), nullable=True)
    avatar_url = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    last_message_id = Column(UUID(as_uuid=True), nullable=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    last_message_snippet = Column(Text, nullable=True)
    last_message_sender_id = Column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("idx_chats_last_message_at", "last_message_at", postgresql_where=deleted_at.is_(None)),
        Index("idx_chats_created_by", "created_by"),
    )

class ChatParticipant(Base):
    __tablename__ = "chat_participants"

    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(Enum("owner", "admin", "member", name="participant_role"), default="member")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_read_message_id = Column(UUID(as_uuid=True), nullable=True)
    notifications_enabled = Column(Boolean, default=True)

    __table_args__ = (
        Index("idx_chat_participants_chat", "chat_id"),
        Index("idx_chat_participants_user_last_read", "user_id", "last_read_message_id"),
    )

# ==============================
# 3. Сообщения (партиционированная таблица)
# ==============================

class Message(Base):
    __tablename__ = "messages"

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
    ttl_seconds = Column(Integer, nullable=True)

    __table_args__ = (
        Index("idx_messages_chat_id", "chat_id", "created_at"),
        Index("idx_messages_sender_id", "sender_id", "created_at"),
        Index("idx_messages_reply_to", "reply_to_message_id"),
        Index("idx_messages_deleted_at", "deleted_at", postgresql_where=deleted_at.is_(None)),
        Index("idx_messages_search", "search_vector", postgresql_using="gin"),
    )

# ==============================
# 4. Файлы
# ==============================

class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), nullable=True)
    file_url = Column(Text, nullable=False)
    cdn_url = Column(Text, nullable=True)
    file_type = Column(String(50), nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration_sec = Column(Integer, nullable=True)
    preview_url = Column(Text, nullable=True)
    is_voice = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_files_message", "message_id"),
        Index("idx_files_cdn", "cdn_url"),
    )

# ==============================
# 5. Стикеры
# ==============================

class StickerPack(Base):
    __tablename__ = "sticker_packs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(100), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_official = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_sticker_packs_author", "author_id"),
    )

class Sticker(Base):
    __tablename__ = "stickers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pack_id = Column(UUID(as_uuid=True), ForeignKey("sticker_packs.id", ondelete="CASCADE"), nullable=False)
    emoji = Column(String(10), nullable=True)
    image_url = Column(Text, nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_stickers_pack", "pack_id"),
    )

# ==============================
# 6. Реакции на сообщения
# ==============================

class MessageReaction(Base):
    __tablename__ = "message_reactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reaction = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="unique_user_message_reaction"),
        Index("idx_reactions_message", "message_id"),
        Index("idx_reactions_user", "user_id"),
    )

# ==============================
# 7. Приглашения в чаты
# ==============================

class ChatInvite(Base):
    __tablename__ = "chat_invites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    max_uses = Column(Integer, default=1)
    uses = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_invites_token", "token"),
        Index("idx_invites_chat", "chat_id"),
    )

# ==============================
# 8. Контакты пользователей
# ==============================

class UserContact(Base):
    __tablename__ = "user_contacts"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    contact_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    local_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_contacts_user", "user_id"),
        Index("idx_contacts_contact", "contact_user_id"),
    )

# ==============================
# 9. Блокировки пользователей
# ==============================

class UserBlocked(Base):
    __tablename__ = "user_blocked"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    blocked_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ==============================
# 10. Настройки приватности
# ==============================

class UserPrivacySettings(Base):
    __tablename__ = "user_privacy_settings"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    last_seen_privacy = Column(String(20), default="everyone")
    profile_photo_privacy = Column(String(20), default="everyone")
    bio_privacy = Column(String(20), default="everyone")
    phone_privacy = Column(String(20), default="contacts")
    group_invite_privacy = Column(String(20), default="everyone")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# ==============================
# 11. E2EE сессии и prekey
# ==============================

class E2EESession(Base):
    __tablename__ = "e2ee_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_a_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user_b_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_key = Column(Text, nullable=True)  # зашифрованный ключ сессии
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("chat_id", "user_a_id", "user_b_id", name="uq_e2ee_session"),
        Index("idx_e2ee_users", "user_a_id", "user_b_id"),
    )

class E2EEPrekey(Base):
    __tablename__ = "e2ee_prekeys"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    prekey_id = Column(Integer, primary_key=True)
    prekey_data = Column(Text, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ==============================
# 12. Боты и очередь сообщений
# ==============================

class Bot(Base):
    __tablename__ = "bots"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    token_hash = Column(Text, nullable=False)
    webhook_url = Column(Text, nullable=True)
    webhook_events = Column(ARRAY(String), nullable=True)
    commands = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class BotMessageQueue(Base):
    __tablename__ = "bot_message_queue"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.user_id", ondelete="CASCADE"), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_bot_queue_status", "status", "created_at", postgresql_where=status == "pending"),
    )

# ==============================
# 13. Аналитика активности
# ==============================

class UserActivity(Base):
    __tablename__ = "user_activity"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_type = Column(String(50), nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_activity_user", "user_id"),
        Index("idx_activity_type", "activity_type"),
    )