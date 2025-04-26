import requests
from fastapi import HTTPException
from typing import Dict, Any

from app.models.bbb_models import (
    BroadcasterRequest,
    IsMeetingRunningRequest,
    GetMeetingInfoRequest
)
from app.config.settings import get_settings
from app.services.bbb_service import BBBService


class BroadcasterService:
    def __init__(self):
        self.settings = get_settings()
        self.broadcaster_api_url = self.settings.broadcaster_api_url

    async def start_broadcasting(
        self,
        meeting_id: str,
        rtmp_url: str,
        stream_key: str,
        password: str,
        bbb_service: BBBService,
    ) -> Dict[str, Any]:
        """Start broadcasting a BBB meeting to RTMP."""
        try:
            # First check if the meeting is running
            is_running_request = IsMeetingRunningRequest(meeting_id=meeting_id)
            is_running = bbb_service.is_meeting_running(request=is_running_request)

            if is_running.get("running", "false").lower() != "true":
                # Commented out as per original code
                # raise HTTPException(status_code=400, detail="Meeting is not running")
                pass

            # Get meeting details to verify password
            meeting_info_request = GetMeetingInfoRequest(meeting_id=meeting_id, password=password)
            meeting_info = bbb_service.get_meeting_info(request=meeting_info_request)

            # Get the join URL
            join_url = bbb_service.get_join_url(
                meeting_id=meeting_id, full_name="Broadcaster Bot", password=password
            )

            # Get the health check URL
            is_meeting_running_url = bbb_service.get_is_meeting_running_url(meeting_id)

            # Call the broadcaster service
            broadcaster_response = await self._call_broadcaster_service(
                is_meeting_running_url=is_meeting_running_url,
                join_url=join_url,
                rtmp_url=rtmp_url,
                stream_key=stream_key,
            )

            return {
                "status": "success",
                "message": "Broadcaster started successfully",
                "broadcaster_response": broadcaster_response,
                "meeting_info": meeting_info,
            }
        except Exception as e:
            # Better error handling to see what's going wrong
            raise HTTPException(
                status_code=500, detail=f"Error in broadcaster: {str(e)}"
            )

    async def _call_broadcaster_service(
        self, is_meeting_running_url: str, join_url: str, rtmp_url: str, stream_key: str
    ) -> Dict[str, Any]:
        """
        Call the broadcaster service to join a BBB meeting.
        """
        try:
            # Prepare the payload for the broadcaster service
            payload = BroadcasterRequest(
                bbb_health_check_url=is_meeting_running_url,
                bbb_server_url=join_url,
                rtmp_url=rtmp_url,
                stream_key=stream_key,
            )

            # Call the broadcaster service
            response = requests.post(
                self.broadcaster_api_url,
                json=payload.dict(),
                headers={
                    "Content-Type": "application/json",
                    "accept": "application/json",
                },
            )

            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"Broadcaster service returned status code: {response.status_code}",
                    "details": response.text,
                }

            return response.json()
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error calling broadcaster service: {str(e)}",
            }
