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
    timezone: str = "UTC"


class EventCreate(EventBase):
    """
    Create model for event
    """

    organizer_ids: Optional[List[UUID]] = []
    channel_name: str


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
    organizer_ids: Optional[List[UUID]] = None
    channel_id: Optional[UUID] = None
    timezone: Optional[str] = None


class OrganizerResponse(BaseModel):
    """
    Response model for organizer
    """

    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str

    model_config = {
        "from_attributes": True,
    }


class EventResponse(EventBase):
    """
    Response model for event
    """

    id: UUID
    creator_id: UUID
    organizers: List[OrganizerResponse] = []
    channel_id: UUID
    meeting_id: Optional[str] = None
    attendee_pw: Optional[str] = None
    moderator_pw: Optional[str] = None
    meeting_created: bool
    timezone: str
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

    model_config = {
        "from_attributes": True,
    }
