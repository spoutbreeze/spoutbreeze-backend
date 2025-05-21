from fastapi import APIRouter, Body, Depends, Request, BackgroundTasks

from app.services.bbb_service import BBBService
from app.models.bbb_schemas import (
    CreateMeetingRequest,
    JoinMeetingRequest,
    EndMeetingRequest,
    GetMeetingInfoRequest,
    IsMeetingRunningRequest,
    GetRecordingRequest,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database.session import get_db
from app.controllers.user_controller import get_current_user
from app.models.user_models import User
from uuid import UUID

router = APIRouter(prefix="/api/bbb", tags=["BigBlueButton"])
bbb_service = BBBService()


@router.get("/")
def root():
    return {"message": "BBB API Integration with FastAPI"}


@router.post("/create")
async def create_meeting(
    request: CreateMeetingRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new BBB meeting."""
    result = await bbb_service.create_meeting(
        request=request,
        user_id=UUID(str(current_user.id)),
        db=db,
    )
    return result


@router.post("/join")
def join_meeting(request: JoinMeetingRequest = Body(...)):
    """Join a BBB meeting."""
    return bbb_service.join_meeting(request=request)


@router.post("/end")
async def end_meeting(
    request: EndMeetingRequest = Body(...), db: AsyncSession = Depends(get_db)
):
    """End a BBB meeting."""
    result = await bbb_service.end_meeting(request=request, db=db)
    return result


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


@router.post("/get-recordings")
def get_recordings(request: GetRecordingRequest = Body(...)):
    """Get the list of all recordings."""
    return bbb_service.get_recordings(request=request)


@router.get("/callback/meeting-ended")
async def meeting_ended_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """Callback endpoint for when a BBB meeting ends."""
    try:
        params = dict(request.query_params)
        meeting_id = params.get("meetingID")
        if not meeting_id:
            return {"error": "Missing meetingID in query parameters"}

        result = await bbb_service.meeting_ended_callback(meeting_id=meeting_id, db=db)
        return result
    except Exception as e:
        return {"error": str(e)}

@router.post("/maintenance/cleanup-old-meetings")
async def cleanup_old_meetings(
    days: int = 30,
    background_tasks: BackgroundTasks = None,
):
    """
    Cleanup old meetings that are older than the specified number of days.
    This is a background task that runs asynchronously.
    """
    if background_tasks:
        background_tasks.add_task(bbb_service._clean_up_meetings_background, days=days)
        return {"message": f"Cleanup task for meetings older than {days} days has been started."}
    else:
        await bbb_service._clean_up_meetings_background(days=days)
        return {"message": f"Cleanup task for meetings older than {days} days has been completed."}
    
