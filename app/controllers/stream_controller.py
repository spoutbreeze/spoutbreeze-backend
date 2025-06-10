from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.config.database.session import get_db
from app.controllers.user_controller import get_current_user
from app.models.user_models import User
from app.models.stream_schemas import (
    StreamSettingsResponse,
    StreamSettingsUpdate,
    CreateStreamSettingsCreate,
    StreamSettingsDeleteResponse,
)
from app.services.stream_service import RtmpEndpointService

router = APIRouter(prefix="/api/stream-endpoint", tags=["Stream Endpoints"])
rtmp_service = RtmpEndpointService()


@router.post("/create", response_model=StreamSettingsResponse)
async def create_stream_settings(
    stream_settings: CreateStreamSettingsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamSettingsResponse:
    """
    Create a new stream settings for the current user.

    Args:
        stream_settings: The stream settings to create.
        db: The database session.
        current_user: The current user.

    Returns:
        The created stream settings.
    """
    try:
        new_stream_settings = await rtmp_service.create_stream_settings(
            stream_settings=stream_settings,
            user_id=UUID(str(current_user.id)),
            db=db,
        )
        return new_stream_settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[StreamSettingsResponse])
async def get_stream_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[StreamSettingsResponse]:
    """
    Get all stream settings for the current user.

    Args:
        db: The database session.
        current_user: The current user.

    Returns:
        A list of stream settings.
    """
    try:
        stream_settings = await rtmp_service.get_stream_settings_by_user_id(
            user_id=UUID(str(current_user.id)),
            db=db,
        )
        return stream_settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stream_settings_id}", response_model=StreamSettingsResponse)
async def get_stream_settings_by_id(
    stream_settings_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamSettingsResponse:
    """
    Get stream settings by ID.

    Args:
        stream_settings_id: The ID of the stream settings.
        db: The database session.

    Returns:
        The stream settings.
    """
    try:
        stream_settings = await rtmp_service.get_stream_settings_by_id(
            stream_settings_id=stream_settings_id,
            db=db,
        )
        if not stream_settings:
            raise HTTPException(status_code=404, detail="Stream settings not found")
        return stream_settings
    except HTTPException:
        # Re-raise HTTPException without changing it
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{stream_settings_id}", response_model=StreamSettingsResponse)
async def update_stream_settings(
    stream_settings_id: UUID,
    stream_settings_update: StreamSettingsUpdate,
    db: AsyncSession = Depends(get_db),
) -> StreamSettingsResponse:
    """
    Update stream settings by ID.

    Args:
        stream_settings_id: The ID of the stream settings.
        stream_settings_update: The updated stream settings.
        db: The database session.

    Returns:
        The updated stream settings.
    """
    try:
        updated_stream_settings = await rtmp_service.update_stream_settings(
            stream_settings_id=stream_settings_id,
            stream_settings_update=stream_settings_update,
            db=db,
        )
        if not updated_stream_settings:
            raise HTTPException(status_code=404, detail="Stream settings not found")
        return updated_stream_settings
    except HTTPException:
        # Re-raise HTTPException without changing it
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{stream_settings_id}", response_model=StreamSettingsDeleteResponse)
async def delete_stream_settings(
    stream_settings_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamSettingsDeleteResponse:
    """
    Delete stream settings by ID.
    Args:
        stream_settings_id: The ID of the stream settings.
        db: The database session.
        current_user: The current user.
    Returns:
        The deleted stream settings.
    """
    try:
        deleted_stream_settings = await rtmp_service.delete_stream_settings(
            stream_settings_id=stream_settings_id,
            user_id=UUID(str(current_user.id)),
            db=db,
        )
        if not deleted_stream_settings:
            raise HTTPException(status_code=404, detail="Stream settings not found")
        return deleted_stream_settings
    except HTTPException:
        # Re-raise HTTPException without changing it
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
