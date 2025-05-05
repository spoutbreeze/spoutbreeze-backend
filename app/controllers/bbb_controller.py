from fastapi import APIRouter, Body

from app.services.bbb_service import BBBService
from app.models.bbb_models import (
    CreateMeetingRequest,
    JoinMeetingRequest,
    EndMeetingRequest,
    GetMeetingInfoRequest,
    IsMeetingRunningRequest,
)

router = APIRouter(prefix="/api/bbb", tags=["BigBlueButton"])
bbb_service = BBBService()


@router.get("/")
def root():
    return {"message": "BBB API Integration with FastAPI"}


@router.post("/create")
def create_meeting(request: CreateMeetingRequest = Body(...)):
    """Create a new BBB meeting."""
    return bbb_service.create_meeting(request=request)


@router.post("/join")
def join_meeting(request: JoinMeetingRequest = Body(...)):
    """Join a BBB meeting."""
    return bbb_service.join_meeting(request=request)


@router.post("/end")
def end_meeting(request: EndMeetingRequest = Body(...)):
    """End a BBB meeting."""
    return bbb_service.end_meeting(request=request)


@router.post("/is-meeting-running")
def is_meeting_running(request: IsMeetingRunningRequest = Body(...)):
    """Check if a meeting is running."""
    return bbb_service.is_meeting_running(request=request)


@router.post("/get-meeting-info")
def get_meeting_info(request: GetMeetingInfoRequest = Body(...)):
    """Get detailed information about a meeting."""
    return bbb_service.get_meeting_info(request=request)


@router.get("/get-meetings")
def get_meetings():
    """Get the list of all meetings."""
    return bbb_service.get_meetings()
