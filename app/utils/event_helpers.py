from uuid import UUID
from datetime import datetime, timezone
from typing import Dict, Any

from app.models.event.event_models import Event
from app.models.event.event_schemas import EventCreate
from app.models.bbb_schemas import CreateMeetingRequest


class EventHelpers:
    """
    Helper class for managing events
    """

    @staticmethod
    def prepare_event_data(
        event: EventCreate,
        user_id: UUID,
        channel_id: UUID,
    ) -> Dict[str, Any]:
        """
        Prepare event data for creation.
        """
        # Ensure all dates are timezone-aware
        start_date = EventHelpers._ensure_timezone_aware(event.start_date)
        end_date = EventHelpers._ensure_timezone_aware(event.end_date)
        start_time = EventHelpers._ensure_timezone_aware(event.start_time)

        # Prepare the event data
        new_event = Event(
            title=event.title,
            description=event.description,
            occurs=event.occurs,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            creator_id=user_id,
            channel_id=channel_id,
        )
        return new_event

    @staticmethod
    def prepare_bbb_meeting_request(
        event: EventCreate,
        new_event: Event,
    ) -> CreateMeetingRequest:
        """
        Prepare BBB meeting request data.
        """
        # Use a unique meeting ID to prevent duplicates
        event_id_short = str(new_event.id).split("-")[0]
        unique_meeting_id = f"{event_id_short}_{event.title.replace(' ', '_')}"[:32]

        # Create the meeting request
        meeting_request = CreateMeetingRequest(
            name=event.title,
            meeting_id=unique_meeting_id,
            attendee_pw=event.attendee_pw,
            moderator_pw=event.moderator_pw,
            welcome=f"Welcome to {event.title}",
        )
        return meeting_request

    @staticmethod
    def _ensure_timezone_aware(
        dt: datetime,
    ) -> datetime:
        """
        Ensure the given datetime is timezone-aware.
        """
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
