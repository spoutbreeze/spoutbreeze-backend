from __future__ import annotations
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.config.database.session import Base

# Type checking imports that don't cause runtime circular imports
if TYPE_CHECKING:
    from app.models.user_models import User
    from app.models.event.event_models import Event


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(), onupdate=datetime.now()
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Relationships with fully qualified string references
    creator: Mapped["User"] = relationship(
        "app.models.user_models.User", back_populates="channels"
    )
    events: Mapped[List["Event"]] = relationship(
        "app.models.event.event_models.Event", back_populates="channel", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Channel(id={self.id!r}, name={self.name!r})>"
