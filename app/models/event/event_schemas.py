from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class EventBase(BaseModel):
    """
    Base model for event
    """

    title: str
    description: Optional[str] = None
    occurs: str
    start_date: datetime
    end_date: datetime
    start_time: datetime
    organizer: str
    channel_id: UUID


class EventCreate(EventBase):
    """
    Create model for event
    """

    meeting_id: Optional[str] = None
    attendee_pw: Optional[str] = None
    moderator_pw: Optional[str] = None


class EventUpdate(BaseModel):
    """
    Update model for event
    """

    title: Optional[str] = None
    description: Optional[str] = None
    occurs: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    start_time: Optional[datetime] = None
    organizer: Optional[str] = None
    channel_id: Optional[UUID] = None


class EventResponse(EventBase):
    """
    Response model for event
    """

    id: UUID
    user_id: UUID
    channel_id: UUID
    meeting_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class EventListResponse(BaseModel):
    """
    List response model for event
    """

    events: List[EventResponse]
    total: int
