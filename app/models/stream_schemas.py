from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class RtmpEndpointBase(BaseModel):
    """
    Base model for stream settings
    """

    title: str
    stream_key: str
    rtmp_url: str


class CreateRtmpEndpointCreate(RtmpEndpointBase):
    """
    Create model for stream settings
    """

    pass


class RtmpEndpointUpdate(BaseModel):
    """
    Update model for stream settings
    """

    title: Optional[str] = None
    rtmp_url: Optional[str] = None
    stream_key: Optional[str] = None


class RtmpEndpointResponse(RtmpEndpointBase):
    """
    Response model for stream settings
    """

    id: UUID
    user_id: UUID
    user_first_name: str
    user_last_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RtmpEndpointListResponse(BaseModel):
    """
    List response model for stream settings
    """

    stream_settings: List[RtmpEndpointResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


class RtmpEndpointDeleteResponse(BaseModel):
    """
    Delete response model for stream settings
    """

    message: str
    id: UUID

    model_config = ConfigDict(from_attributes=True)
