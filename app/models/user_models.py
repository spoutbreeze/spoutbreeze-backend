from __future__ import annotations
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.config.database.session import Base
from app.models.bbb_models import BbbMeeting
from app.models.channel.channels_model import Channel
from app.models.stream_models import StreamSettings  # assuming Base is the DeclarativeBase
from app.models.event.event_models import Event  # assuming Base is the DeclarativeBase

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )
    keycloak_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), onupdate=datetime.now(), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships – note the use of fully qualified names if needed or move to __init__.py import order
    stream_settings: Mapped[list[StreamSettings]] = relationship(
        "StreamSettings", back_populates="user", cascade="all, delete-orphan"
    )
    bbb_meetings: Mapped[list[BbbMeeting]] = relationship(
        "BbbMeeting", back_populates="user", cascade="all, delete-orphan"
    )
    channels: Mapped[list[Channel]] = relationship(
        "app.models.channel.channels_model.Channel", back_populates="creator", cascade="all, delete-orphan"
    )
    created_events: Mapped[list[Event]] = relationship(
        "app.models.event.event_models.Event", back_populates="creator", cascade="all, delete-orphan"
    )
    organized_events: Mapped[list[Event]] = relationship(
        "app.models.event.event_models.Event",
        secondary="user_event_association",
        back_populates="organizers",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id!r}, username={self.username!r}, email={self.email!r})>"
