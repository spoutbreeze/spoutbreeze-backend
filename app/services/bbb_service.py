import time
import hashlib
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from typing import Optional, Dict, Any, List
from fastapi import HTTPException
from fastapi.responses import RedirectResponse

from app.config.settings import get_settings
from app.models.bbb_models import Meeting, MeetingAttendee
from app.utils.bbb_helpers import parse_xml_response, generate_checksum


class BBBService:
    def __init__(self):
        self.settings = get_settings()
        self.server_base_url = self.settings.bbb_server_base_url
        self.secret = self.settings.bbb_secret

    def create_meeting(
            self,
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
    ) -> Dict[str, Any]:
        """Create a new BBB meeting."""
        # Generate a meeting ID if not provided
        if not meeting_id:
            meeting_id = f"meeting-{int(time.time())}"

        # Prepare parameters for BBB API
        params = {
            "name": name,
            "meetingID": meeting_id,
            "attendeePW": attendee_pw,
            "moderatorPW": moderator_pw,
            "welcome": welcome,
            "maxParticipants": max_participants,
            "duration": duration,
            "record": record,
            "autoStartRecording": auto_start_recording,
            "allowStartStopRecording": allow_start_stop_recording,
            "moderatorOnlyMessage": moderator_only_message,
            "logo": logo_url
        }

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        # Call BBB API
        return self._call_bbb_api("create", params)

    def join_meeting(
            self,
            meeting_id: str,
            full_name: str,
            password: str,
            user_id: Optional[str] = None,
            redirect: bool = True
    ) -> Dict[str, Any]:
        """Join a BBB meeting."""
        params = {
            "meetingID": meeting_id,
            "fullName": full_name,
            "password": password,
            "userID": user_id
        }

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        query_string = urlencode([(k, v) for k, v in params.items() if v])
        checksum = generate_checksum("join", query_string, self.secret)

        join_url = f"{self.server_base_url}join?{query_string}&checksum={checksum}"

        # Either redirect or return the URL
        if redirect:
            return RedirectResponse(url=join_url)
        else:
            return {"join_url": join_url}

    def end_meeting(self, meeting_id: str, password: str) -> Dict[str, Any]:
        """End a BBB meeting."""
        params = {
            "meetingID": meeting_id,
            "password": password
        }

        return self._call_bbb_api("end", params)

    def is_meeting_running(self, meeting_id: str) -> Dict[str, Any]:
        """Check if a meeting is running."""
        params = {
            "meetingID": meeting_id
        }

        return self._call_bbb_api("isMeetingRunning", params)

    def get_meeting_info(self, meeting_id: str, password: str) -> Dict[str, Any]:
        """Get detailed information about a meeting."""
        params = {
            "meetingID": meeting_id,
            "password": password
        }

        return self._call_bbb_api("getMeetingInfo", params)

    def get_meetings(self) -> Dict[str, Any]:
        """Get the list of all meetings."""
        return self._call_bbb_api("getMeetings", {})

    def get_join_url(self, meeting_id: str, full_name: str, password: str, user_id: Optional[str] = None) -> str:
        """Generate a join URL for a BBB meeting."""
        params = {
            "meetingID": meeting_id,
            "fullName": full_name,
            "password": password,
            "userID": user_id
        }

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        query_string = urlencode([(k, v) for k, v in params.items() if v])
        checksum = generate_checksum("join", query_string, self.secret)

        return f"{self.server_base_url}join?{query_string}&checksum={checksum}"

    def get_is_meeting_running_url(self, meeting_id: str) -> str:
        """Generate a URL to check if a meeting is running."""
        checksum = generate_checksum("isMeetingRunning", f"meetingID={meeting_id}", self.secret)
        return f"{self.server_base_url}isMeetingRunning?meetingID={meeting_id}&checksum={checksum}"

    def _call_bbb_api(self, api_call: str, params: dict) -> dict:
        """Makes a call to the BBB API and returns the parsed XML response."""
        # Sort parameters alphabetically as BBB requires
        query_string = urlencode([(k, v) for k, v in params.items() if v])

        # Generate checksum
        checksum = generate_checksum(api_call, query_string, self.secret)

        # Append checksum to parameters
        full_url = f"{self.server_base_url}{api_call}?{query_string}&checksum={checksum}"

        # Make the API call
        response = requests.get(full_url)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="BBB API request failed")

        # Parse XML response
        return parse_xml_response(response.content, api_call)