from sqlalchemy import Column, String, ForeignKey, DateTime
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..config.database.session import Base


class StreamSettings(Base):
    __tablename__ = "stream_endpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)    
    title = Column(String, nullable=False)
    rtmp_url = Column(String, nullable=False)
    stream_key = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    user = relationship("User", back_populates="stream_settings")