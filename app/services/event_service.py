from typing import List, Dict, Any
from uuid import UUID

from app.models.user_models import User
from app.models.event.event_models import Event
from app.models.event.event_schemas import EventCreate, EventUpdate, EventResponse
from app.models.channel.channels_schemas import ChannelCreate, ChannelResponse
from app.services.channels_service import ChannelsService
from app.services.bbb_service import BBBService
from app.utils.event_helpers import EventHelpers


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from app.config.logger_config import logger


class EventService:
    """
    Service class for managing events
    """

    def __init__(self):
        self.bbb_service = BBBService()
        self.channel_service = ChannelsService()
        self.event_helpers = EventHelpers()

    async def create_event(
        self,
        db: AsyncSession,
        event: EventCreate,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """
        Create a new event.
        """
        try:
            channel = await self._get_or_create_channel(
                db=db,
                channel_name=event.channel_name,
                user_id=user_id,
            )

            # Create the event
            new_event = self.event_helpers.prepare_event_data(
                event=event,
                user_id=user_id,
                channel_id=channel.id,
            )

            # Collect organizers first if provided
            organizers = []
            if hasattr(event, "organizer_ids") and event.organizer_ids:
                for organizer_id in event.organizer_ids:
                    # Check if the user exists
                    result = await db.execute(
                        select(User).where(User.id == organizer_id)
                    )
                    organizer = result.scalars().first()
                    if not organizer:
                        raise ValueError(f"User with ID {organizer_id} does not exist.")
                    organizers.append(organizer)

            # Add the new event to the session
            db.add(new_event)

            # Add organizers after adding the event
            if organizers:
                new_event.organizers.extend(organizers)

            # Commit the changes
            await db.commit()

            # Refresh the event with eager loading of relationships
            result = await db.execute(
                select(Event)
                .options(
                    selectinload(Event.organizers),
                    selectinload(Event.channel),
                    selectinload(Event.creator),
                )
                .where(Event.id == new_event.id)
            )
            new_event = result.scalars().first()

            logger.info(
                f"Event {new_event.title} created for user {user_id} in channel {channel.name}"
            )

            # Create the meeting in BBB
            bbb_meeting = await self._create_bbb_meeting(
                db=db,
                event=event,
                new_event=new_event,
                user_id=user_id,
            )

            # Check if meeting_id is in the response or at a different path
            meeting_id = (
                bbb_meeting.get("meeting_id")
                or bbb_meeting.get("meetingID")
                or bbb_meeting.get("id")
                or "unknown"
            )

            logger.info(
                f"User with ID {user_id} created BBB meeting with ID {meeting_id} for event {new_event.title}"
            )

            # Create organizers list without accessing lazy-loaded attributes
            organizers_list = []
            for organizer in new_event.organizers:
                organizers_list.append(
                    {
                        "id": str(organizer.id),
                        "username": organizer.username,
                        "email": organizer.email,
                        "first_name": organizer.first_name,
                        "last_name": organizer.last_name,
                    }
                )

            event_dict = {
                "id": str(new_event.id),
                "title": new_event.title,
                "description": new_event.description,
                "occurs": new_event.occurs,
                "start_date": new_event.start_date,
                "end_date": new_event.end_date,
                "start_time": new_event.start_time,
                "channel_name": new_event.channel.name,
                "creator_id": str(new_event.creator_id),
                "organizers": organizers_list,
                "channel_id": str(new_event.channel_id),
                "meeting_id": meeting_id,
                "created_at": new_event.created_at,
                "updated_at": new_event.updated_at,
            }

            # Convert to EventResponse
            event_response = EventResponse.model_validate(event_dict)

            return {
                "event": event_response,
                "bbb_meeting": bbb_meeting,
            }
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            await db.rollback()
            raise

    async def get_event_by_id(
        self,
        db: AsyncSession,
        event_id: UUID,
    ) -> EventResponse:
        """
        Get an event by ID.
        """
        try:
            result = await db.execute(
                select(Event)
                .options(
                    selectinload(Event.organizers),
                    selectinload(Event.channel),
                    selectinload(Event.creator),
                )
                .where(Event.id == event_id)
            )
            event = result.scalars().first()

            if not event:
                raise ValueError(f"Event with ID {event_id} does not exist.")

            logger.info(f"Event retrieved with ID {event_id}")
            return event
        except Exception as e:
            logger.error(f"Error retrieving event with ID {event_id}: {e}")
            raise

    async def get_all_events(
        self,
        db: AsyncSession,
    ) -> List[EventResponse]:
        """
        Get all events.
        """
        try:
            result = await db.execute(
                select(Event).options(
                    selectinload(Event.organizers),
                    selectinload(Event.channel),
                    selectinload(Event.creator),
                )
            )
            events = result.scalars().all()

            if not events:
                raise ValueError("No events found.")

            logger.info(f"Retrieved {len(events)} events")
            return events
        except Exception as e:
            logger.error(f"Error retrieving events: {e}")
            raise

    async def update_event(
        self,
        db: AsyncSession,
        event_id: UUID,
        event_update: EventUpdate,
        user_id: UUID,
    ) -> EventResponse:
        """
        Update an event by ID.
        """
        # Check if the event exists
        select_stmt = (
            select(Event)
            .options(
                selectinload(Event.organizers),
                selectinload(Event.channel),
                selectinload(Event.creator),
            )
            .where(Event.id == event_id, Event.creator_id == user_id)
        )
        result = await db.execute(select_stmt)
        event = result.scalars().first()
        if not event:
            raise ValueError(
                f"Event with ID {event_id} does not exist or does not belong to user {user_id}."
            )

        # Update the event
        try:
            # Handle basic fields
            update_data = {}
            for field, value in event_update.model_dump().items():
                if (
                    value is not None and field != "organizer_ids"
                ):  # Skip organizer_ids for direct update
                    update_data[field] = value

            if update_data:  # Only update if there are fields to update
                update_stmt = (
                    update(Event).where(Event.id == event_id).values(**update_data)
                )
                await db.execute(update_stmt)

            # Handle organizers separately if provided
            if event_update.organizer_ids is not None:
                # Clear existing organizers
                event.organizers = []

                # Add new organizers
                for organizer_id in event_update.organizer_ids:
                    # Verify user exists
                    organizer_result = await db.execute(
                        select(User).where(User.id == organizer_id)
                    )
                    organizer = organizer_result.scalars().first()
                    if organizer:
                        event.organizers.append(organizer)
                    else:
                        logger.warning(
                            f"User with ID {organizer_id} not found when updating event organizers"
                        )

            await db.commit()
            await db.refresh(event)
            return event
        except Exception as e:
            logger.error(f"Error updating event with ID {event_id}: {e}")
            await db.rollback()
            raise

    async def delete_event(
        self,
        db: AsyncSession,
        event_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Delete an event by ID.
        """
        try:
            # Check if the event exists and belongs to the user
            select_stmt = select(Event).where(
                Event.id == event_id, Event.creator_id == user_id
            )
            result = await db.execute(select_stmt)
            event = result.scalars().first()
            if not event:
                raise ValueError(
                    f"Event with ID {event_id} does not exist or does not belong to user {user_id}."
                )

            # Delete the event
            delete_stmt = delete(Event).where(Event.id == event_id)
            await db.execute(delete_stmt)
            await db.commit()

            logger.info(f"Event with ID {event_id} deleted for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting event with ID {event_id}: {e}")
            await db.rollback()
            raise

    async def _get_or_create_channel(
        self,
        db: AsyncSession,
        channel_name: str,
        user_id: UUID,
    ) -> ChannelResponse:
        """
        Get or create a channel.
        """
        channel = await self.channel_service.get_channel_by_name(
            db=db, channel_name=channel_name, user_id=user_id
        )
        if not channel:
            channel_create = ChannelCreate(name=channel_name)
            channel = await self.channel_service.create_channel(
                db=db, channel_create=channel_create, user_id=user_id
            )
        return channel

    async def _create_bbb_meeting(
        self,
        db: AsyncSession,
        event: EventCreate,
        new_event: Event,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """
        Create a BBB meeting for the event.
        """
        # Create the meeting in BBB
        meeting_request = self.event_helpers.prepare_bbb_meeting_request(
            event=event,
            new_event=new_event,
        )

        bbb_meeting = await self.bbb_service.create_meeting(
            request=meeting_request,
            user_id=user_id,
            db=db,
        )

        return bbb_meeting
