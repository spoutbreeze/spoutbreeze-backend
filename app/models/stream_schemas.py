from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class streamSettingsBase(BaseModel):
    """
    Base model for stream settings
    """
    title: str
    stream_key: str
    rtmp_url: str

class CreateStreamSettingsCreate(streamSettingsBase):
    """
    Create model for stream settings
    """
    pass

class StreamSettingsUpdate(BaseModel):
    """
    Update model for stream settings
    """
    title: Optional[str] = None
    rtmp_url: Optional[str] = None
    stream_key: Optional[str] = None

class StreamSettingsResponse(streamSettingsBase):
    """
    Response model for stream settings
    """
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class StreamSettingsListResponse(BaseModel):
    """
    List response model for stream settings
    """
    stream_settings: List[StreamSettingsResponse]
    total: int

    model_config = {
        "from_attributes": True,
    }

class StreamSettingsDeleteResponse(BaseModel):
    """
    Delete response model for stream settings
    """
    message: str
    id: UUID

    model_config = {
        "from_attributes": True,
    }