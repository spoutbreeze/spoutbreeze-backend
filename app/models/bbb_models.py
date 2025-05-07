from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.config.database.session import Base


class BbbMeeting(Base):
    __tablename__ = "bbb_meetings"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )
    meeting_id = Column(String, unique=True, index=True, nullable=False)
    internal_meeting_id = Column(String, unique=True, index=True, nullable=False)
    parent_meeting_id = Column(String, index=True)
    attendee_pw = Column(String, index=True, nullable=False)
    moderator_pw = Column(String, index=True, nullable=False)
    create_time = Column(String, index=True)
    voice_bridge = Column(String, index=True)
    dial_number = Column(String, index=True)
    has_user_joined = Column(String, index=True)
    duration = Column(String, index=True)
    has_been_forcibly_ended = Column(String, index=True)
    message_key = Column(String, index=True)
    message = Column(String, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="bbb_meetings")
