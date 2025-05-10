from app.config.database.session import Base
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

# Association table for many-to-many relationship between Uusers and events
user_event_association = Table(
    "user_event_association",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("event_id", UUID(as_uuid=True), ForeignKey("events.id"), primary_key=True),
)