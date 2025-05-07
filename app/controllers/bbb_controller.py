from fastapi import APIRouter, Body, Depends

from app.services.bbb_service import BBBService
from app.models.bbb_schemas import (
    CreateMeetingRequest,
    JoinMeetingRequest,
    EndMeetingRequest,
    GetMeetingInfoRequest,
    IsMeetingRunningRequest,
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
async def end_meeting(request: EndMeetingRequest = Body(...)):
    """End a BBB meeting."""
    result = await bbb_service.end_meeting(request=request)
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
