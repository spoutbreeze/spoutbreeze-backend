from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.config.database.session import Base


class TwitchToken(Base):
    __tablename__ = "twitch_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    access_token: Mapped[str] = mapped_column(String, nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<TwitchToken(id={self.id!r}, is_active={self.is_active!r}, expires_at={self.expires_at!r})>"
