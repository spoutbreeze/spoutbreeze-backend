from fastapi import APIRouter, Query, Depends
from fastapi.responses import RedirectResponse
from typing import Optional

from app.services.bbb_service import BBBService
from app.services.broadcaster_service import BroadcasterService
from app.models.bbb_models import BroadcasterResponse

router = APIRouter(prefix="/api/bbb", tags=["BigBlueButton"])
bbb_service = BBBService()
broadcaster_service = BroadcasterService()

@router.get("/")
def root():
    return {"message": "BBB API Integration with FastAPI"}

@router.get("/create")
def create_meeting(
        name: str,
        meeting_id: Optional[str] = None,
        attendee_pw: Optional[str] = None,
        moderator_pw: Optional[str] = None,
        welcome: Optional[str] = None,
        max_participants: Optional[int] = None,
        duration: Optional[int] = None,
        record: Optional[bool] = None,
        auto_start_recording: Optional[bool] = None,
        allow_start_stop_recording: Optional[bool] = None,
        moderator_only_message: Optional[str] = None,
        logo_url: Optional[str] = None
):
    """Create a new BBB meeting."""
    return bbb_service.create_meeting(
        name=name,
        meeting_id=meeting_id,
        attendee_pw=attendee_pw,
        moderator_pw=moderator_pw,
        welcome=welcome,
        max_participants=max_participants,
        duration=duration,
        record=record,
        auto_start_recording=auto_start_recording,
        allow_start_stop_recording=allow_start_stop_recording,
        moderator_only_message=moderator_only_message,
        logo_url=logo_url
    )

@router.get("/join")
def join_meeting(
        meeting_id: str,
        full_name: str,
        password: str,
        user_id: Optional[str] = None,
        redirect: bool = True
):
    """Join a BBB meeting."""
    return bbb_service.join_meeting(
        meeting_id=meeting_id,
        full_name=full_name,
        password=password,
        user_id=user_id,
        redirect=redirect
    )

@router.get("/end")
def end_meeting(meeting_id: str, password: str):
    """End a BBB meeting."""
    return bbb_service.end_meeting(meeting_id, password)

@router.get("/is-meeting-running")
def is_meeting_running(meeting_id: str):
    """Check if a meeting is running."""
    return bbb_service.is_meeting_running(meeting_id)

@router.get("/get-meeting-info")
def get_meeting_info(meeting_id: str, password: str):
    """Get detailed information about a meeting."""
    return bbb_service.get_meeting_info(meeting_id, password)

@router.get("/get-meetings")
def get_meetings():
    """Get the list of all meetings."""
    return bbb_service.get_meetings()

@router.post("/broadcaster")
async def broadcaster_meeting(
        meeting_id: str = Query(..., description="ID of the BBB meeting"),
        rtmp_url: str = Query(..., description="RTMP URL for the broadcaster"),
        stream_key: str = Query(..., description="Stream key for the broadcaster"),
        password: str = Query(..., description="Password for the BBB meeting"),
):
    """Start broadcasting a BBB meeting to RTMP (e.g., Twitch)."""
    return await broadcaster_service.start_broadcasting(
        meeting_id=meeting_id,
        rtmp_url=rtmp_url,
        stream_key=stream_key,
        password=password,
        bbb_service=bbb_service
    )