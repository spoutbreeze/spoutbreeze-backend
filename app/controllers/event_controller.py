from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from uuid import UUID

from app.config.database.session import get_db
from app.controllers.user_controller import get_current_user
from app.models.user_models import User
from app.models.event.event_schemas import (
    EventCreate,
    EventResponse,
    EventListResponse,
    EventUpdate,
)
from app.services.event_service import EventService
from app.services.bbb_service import BBBService

router = APIRouter(prefix="/api/events", tags=["Events"])
event_service = EventService()
bbb_service = BBBService()


@router.post("/", response_model=Dict[str, Any])
async def create_event(
    event_create: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Create a new event for the current user.

    Args:
        event_create: The event to create.
        db: The database session.
        current_user: The current user.

    Returns:
        The created event.
    """
    try:
        new_event = await event_service.create_event(
            db=db,
            event=event_create,
            user_id=UUID(str(current_user.id)),
        )
        return new_event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all", response_model=EventListResponse)
async def get_all_events(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventListResponse:
    """
    Get all events for the current user.

    Args:
        db: The database session.
        current_user: The current user.

    Returns:
        A list of events.
    """
    try:
        events = await event_service.get_all_events(db=db)
        return EventListResponse(events=events, total=len(events))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventResponse:
    """
    Get an event by ID for the current user.

    Args:
        event_id: The ID of the event to retrieve.
        db: The database session.
        current_user: The current user.

    Returns:
        The event with the specified ID.
    """
    try:
        event = await event_service.get_event_by_id(
            db=db,
            event_id=event_id,
        )
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Get event by channel ID
@router.get("/channel/{channel_id}", response_model=EventListResponse)
async def get_events_by_channel(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventListResponse:
    """
    Get all events for a specific channel.

    Args:
        channel_id: The ID of the channel.
        db: The database session.
        current_user: The current user.

    Returns:
        A list of events for the specified channel.
    """
    try:
        events = await event_service.get_events_by_channel_id(
            db=db,
            channel_id=channel_id,
        )

        return EventListResponse(events=events, total=len(events))
    except ValueError as e:
        # Handle the case where the channel ID is not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    event_update: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventResponse:
    """
    Update an event by ID for the current user.

    Args:
        event_id: The ID of the event to update.
        event_update: The updated event data.
        db: The database session.
        current_user: The current user.

    Returns:
        The updated event.
    """
    try:
        updated_event = await event_service.update_event(
            db=db,
            event_id=event_id,
            event_update=event_update,
            user_id=UUID(str(current_user.id)),
        )
        return updated_event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{event_id}", response_model=Dict[str, str])
async def delete_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Delete an event by ID for the current user.

    Args:
        event_id: The ID of the event to delete.
        db: The database session.
        current_user: The current user.

    Returns:
        A message indicating the result of the deletion.
    """
    try:
        await event_service.delete_event(
            db=db,
            event_id=event_id,
            user_id=UUID(str(current_user.id)),
        )
        return {"message": "Event deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
