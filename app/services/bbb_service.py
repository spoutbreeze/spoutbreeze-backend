import time
import json
import requests
from urllib.parse import urlencode
from typing import Optional, Dict, Any, List, Union
from fastapi import HTTPException
from fastapi.responses import RedirectResponse

from app.config.settings import get_settings
from app.utils.bbb_helpers import parse_xml_response, generate_checksum
from app.models.bbb_models import (
    CreateMeetingRequest,
    JoinMeetingRequest,
    EndMeetingRequest,
    GetMeetingInfoRequest,
    IsMeetingRunningRequest,
)


class BBBService:
    def __init__(self):
        self.settings = get_settings()
        self.server_base_url = self.settings.bbb_server_base_url
        self.secret = self.settings.bbb_secret

    def create_meeting(
        self,
        request: CreateMeetingRequest,
    ) -> Dict[str, Any]:
        """Create a new BBB meeting."""
        # Generate a meeting ID if not provided
        if not request.meeting_id:
            request.meeting_id = f"meeting-{int(time.time())}"

        # Prepare parameters for BBB API
        params = {
            "name": request.name,
            "meetingID": request.meeting_id,
            "attendeePW": request.attendee_pw,
            "moderatorPW": request.moderator_pw,
            "welcome": request.welcome,
            "maxParticipants": request.max_participants,
            "duration": request.duration,
            "record": request.record,
            "autoStartRecording": request.auto_start_recording,
            "allowStartStopRecording": request.allow_start_stop_recording,
            "moderatorOnlyMessage": request.moderator_only_message,
            "logo": request.logo_url,
            "pluginManifests": request.pluginManifests,
        }

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        # Call BBB API
        return self._call_bbb_api("create", params)

    def join_meeting(
        self,
        request: JoinMeetingRequest,
    ) -> Union[Dict[str, Any], RedirectResponse]:
        """Join a BBB meeting."""
        # Create base params
        processed_params = {}

        # Process parameters
        for key, value in {
            "meetingID": request.meeting_id,
            "fullName": request.full_name,
            "password": request.password,
            "userID": request.user_id,
        }.items():
            if value is not None:
                processed_params[key] = value

        # Handle pluginManifests separately
        if request.pluginManifests:
            # Convert Pydantic models to dict first, then to JSON string
            plugin_dicts = [plugin.dict() for plugin in request.pluginManifests]
            processed_params["pluginManifests"] = json.dumps(plugin_dicts)

        # Create query string
        query_string = urlencode([(k, v) for k, v in processed_params.items()])

        # Generate checksum
        checksum = generate_checksum("join", query_string, self.secret)

        # Create full URL
        join_url = f"{self.server_base_url}join?{query_string}&checksum={checksum}"

        # Either redirect or return the URL
        if request.redirect:
            return RedirectResponse(url=join_url)
        else:
            return {"join_url": join_url}

    def end_meeting(self, request: EndMeetingRequest) -> Dict[str, Any]:
        """End a BBB meeting."""
        params = {"meetingID": request.meeting_id, "password": request.password}

        return self._call_bbb_api("end", params)

    def is_meeting_running(self, request: IsMeetingRunningRequest) -> Dict[str, Any]:
        """Check if a meeting is running."""
        params = {"meetingID": request.meeting_id}

        return self._call_bbb_api("isMeetingRunning", params)

    def get_meeting_info(self, request: GetMeetingInfoRequest) -> Dict[str, Any]:
        """Get detailed information about a meeting."""
        params = {"meetingID": request.meeting_id, "password": request.password}

        return self._call_bbb_api("getMeetingInfo", params)

    def get_meetings(self) -> Dict[str, Any]:
        """Get the list of all meetings."""
        return self._call_bbb_api("getMeetings", {})

    def get_join_url(
        self,
        request: JoinMeetingRequest,
    ) -> str:
        """Generate a join URL for a BBB meeting."""
        # Create base params
        processed_params = {}

        # Process parameters
        for key, value in {
            "meetingID": request.meeting_id,
            "fullName": request.full_name,
            "password": request.password,
            "userID": request.user_id,
        }.items():
            if value is not None:
                processed_params[key] = value

        # Handle pluginManifests separately
        if request.pluginManifests:
            # Convert Pydantic models to dict first, then to JSON string
            plugin_dicts = [plugin.dict() for plugin in request.pluginManifests]
            processed_params["pluginManifests"] = json.dumps(plugin_dicts)

        query_string = urlencode([(k, v) for k, v in processed_params.items()])
        checksum = generate_checksum("join", query_string, self.secret)

        return f"{self.server_base_url}join?{query_string}&checksum={checksum}"

    def get_is_meeting_running_url(self, meeting_id: str) -> str:
        """Generate a URL to check if a meeting is running."""
        checksum = generate_checksum(
            "isMeetingRunning", f"meetingID={meeting_id}", self.secret
        )
        return f"{self.server_base_url}isMeetingRunning?meetingID={meeting_id}&checksum={checksum}"

    def _call_bbb_api(self, api_call: str, params: dict) -> dict:
        """Makes a call to the BBB API and returns the parsed XML response."""
        # Create a copy to avoid modifying the original
        processed_params = {}

        # Process parameters to handle special cases like pluginManifests
        for key, value in params.items():
            if key == "pluginManifests" and value:
                # Convert Pydantic models to dict first, then to JSON string
                plugin_dicts = [plugin.dict() for plugin in value]
                processed_params[key] = json.dumps(plugin_dicts)
            else:
                # For regular parameters, use them as is
                processed_params[key] = value

        # Sort parameters alphabetically as BBB requires
        query_string = urlencode(
            [(k, v) for k, v in processed_params.items() if v is not None]
        )

        # Generate checksum
        checksum = generate_checksum(api_call, query_string, self.secret)

        # Append checksum to parameters
        full_url = (
            f"{self.server_base_url}{api_call}?{query_string}&checksum={checksum}"
        )

        # Make the API call
        response = requests.get(full_url)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, detail="BBB API request failed"
            )

        # Parse XML response
        return parse_xml_response(response.content, api_call)
