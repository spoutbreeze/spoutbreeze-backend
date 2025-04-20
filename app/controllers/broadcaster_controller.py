from fastapi import APIRouter, Depends, Body
from app.services.broadcaster_service import BroadcasterService
from app.models.bbb_models import BroadcasterResponse, BroadcasterRobot
from app.services.bbb_service import BBBService


router = APIRouter(prefix="/api/bbb", tags=["Broadcaster"])

bbb_service = BBBService()
broadcaster_service = BroadcasterService()

@router.post("/broadcaster")
async def broadcaster_meeting(
        payload: BroadcasterRobot = Body(..., description="Broadcaster robot payload")
):
    """Start broadcasting a BBB meeting to RTMP (e.g., Twitch)."""
    return await broadcaster_service.start_broadcasting(
        meeting_id=payload.meeting_id,
        rtmp_url=payload.rtmp_url,
        stream_key=payload.stream_key,
        password=payload.password,
        bbb_service=bbb_service
    )
