from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.config.database.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )
    keycloak_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)

    # Relationships
    stream_settings = relationship(
        "StreamSettings", back_populates="user", cascade="all, delete-orphan"
    )
    bbb_meetings = relationship(
        "BbbMeeting", back_populates="user", cascade="all, delete-orphan"
    )
    channels = relationship(
        "Channel", back_populates="creator", cascade="all, delete-orphan"
    )
    created_events = relationship(
        "Event", back_populates="creator", cascade="all, delete-orphan"
    )
    organized_events = relationship(
        "Event",
        secondary="user_event_association",
        back_populates="organizers",
    )
