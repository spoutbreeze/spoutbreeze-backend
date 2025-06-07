from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class ChannelBase(BaseModel):
    """
    Base model for channel
    """

    name: str


class ChannelCreate(ChannelBase):
    """
    Create model for channel
    """

    pass


class ChannelUpdate(BaseModel):
    """
    Update model for channel
    """

    name: Optional[str] = None


class ChannelResponse(ChannelBase):
    """
    Response model for channel
    """

    id: UUID
    creator_id: UUID
    creator_first_name: str
    creator_last_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChannelListResponse(BaseModel):
    """
    List response model for channel
    """

    channels: List[ChannelResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)
