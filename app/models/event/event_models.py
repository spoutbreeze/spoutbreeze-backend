from sqlalchemy import Column, String, ForeignKey, DateTime
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.config.database.session import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    occurs = Column(String, nullable=False) # e.g., "once", "daily", "weekly", "monthly"
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False)

    # Relationships
    creator = relationship("User", back_populates="created_events")
    channel = relationship("Channel", back_populates="events")
    # Many events can have many organizers
    organizers = relationship(
        "User",
        secondary="user_event_association",
        back_populates="organized_events",
    )
