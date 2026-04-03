from sqlalchemy import Column, String, DateTime, JSON, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from ..database import Base

class Bot(Base):
    __tablename__ = "bots"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    token_hash = Column(Text, nullable=False)
    webhook_url = Column(Text)
    webhook_events = Column(ARRAY(String))
    commands = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())