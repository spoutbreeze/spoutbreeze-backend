from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse
import hashlib
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
import time
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/bbb", tags=["BigBlueButton"])

class BroadcasterRequest(BaseModel):
    """
    Broadcaster Model for joining a BBB meeting
    """
    bbb_server_url: str
    rtmp_url: str
    stream_key: str



# Configuration - replace with your actual BBB server details
BBB_SERVER_BASE_URL = "https://bbb3.riadvice.ovh/bigbluebutton/api/"
BBB_SECRET = "7s5PimdCDbeIhRkTbR11hqQmcPPhGLNvQACuLud9VKE"  # Get this from your BBB server

# Configuration for the broadcaster service
BROADCASTER_API_URL = "http://localhost:8081/broadcaster/joinBBB"


# Helper function to generate BBB API checksum
def generate_checksum(call_name: str, query_params: str, shared_secret: str) -> str:
    """Generates the checksum required for BBB API calls."""
    checksum_string = call_name + query_params + shared_secret
    return hashlib.sha1(checksum_string.encode('utf-8')).hexdigest()


# Helper function to make BBB API calls
def call_bbb_api(api_call: str, params: dict) -> dict:
    """Makes a call to the BBB API and returns the parsed XML response."""
    # Sort parameters alphabetically as BBB requires
    query_string = urlencode([(k, v) for k, v in params.items() if v])

    # Generate checksum
    checksum = generate_checksum(api_call, query_string, BBB_SECRET)

    # Append checksum to parameters
    full_url = f"{BBB_SERVER_BASE_URL}{api_call}?{query_string}&checksum={checksum}"

    # Make the API call
    response = requests.get(full_url)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="BBB API request failed")

    # Parse XML response
    try:
        root = ET.fromstring(response.content)
        result = {"returncode": root.findtext("returncode")}

        if result["returncode"] == "SUCCESS":
            # Special handling for getMeetings which has nested structure
            if api_call == "getMeetings":
                meetings_element = root.find("meetings")
                if meetings_element is not None:
                    meetings = []
                    for meeting in meetings_element.findall("meeting"):
                        meeting_info = {}
                        for element in meeting:
                            # Handle nested elements like attendees
                            if element.tag in ["attendees"]:
                                attendees = []
                                for attendee in element.findall("attendee"):
                                    attendee_info = {}
                                    for attr in attendee:
                                        attendee_info[attr.tag] = attr.text
                                    attendees.append(attendee_info)
                                meeting_info[element.tag] = attendees
                            else:
                                meeting_info[element.tag] = element.text
                        meetings.append(meeting_info)
                    result["meetings"] = meetings
                else:
                    result["meetings"] = []
            else:
                # Extract other elements based on API call
                for child in root:
                    if child.tag != "returncode":
                        result[child.tag] = child.text
        else:
            # Extract error message
            result["message"] = root.findtext("message", "Unknown error")
            raise HTTPException(status_code=400, detail=result["message"])

        return result
    except ET.ParseError:
        raise HTTPException(status_code=500, detail="Failed to parse BBB response")


async def broadcaster_service(join_url: str, rtmp_url: str, stream_key: str) -> dict:
    """
    Function to handle the broadcaster's request to join a BBB meeting.
    This function is called when the broadcaster wants to start streaming.
    """
    try:
        # Prepare the payload for the broadcaster service
        payload = {
            "bbb_server_url": join_url,
            "rtmp_url": rtmp_url,
            "stream_key": stream_key
        }

        # Call the broadcaster service
        response = requests.post(
            BROADCASTER_API_URL, 
            json=payload,
            headers={"Content-Type": "application/json", "accept": "application/json"}
        )
        
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"Broadcaster service returned status code: {response.status_code}",
                "details": response.text
            }

        return response.json()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error calling broadcaster service: {str(e)}"
        }

@router.post("/broadcaster")
async def broadcaster_meeting(
        meeting_id: str = Query(..., description="ID of the BBB meeting"),
        rtmp_url: str = Query(..., description="RTMP URL for the broadcaster"),
        stream_key: str = Query(..., description="Stream key for the broadcaster"),
        password: str = Query(..., description="Password for the BBB meeting"),
):
    """Start broadcasting a BBB meeting to RTMP (e.g., Twitch)."""
    try:
        # First check if the meeting is running
        is_running = call_bbb_api("isMeetingRunning", {"meetingID": meeting_id})

        if is_running.get("running", "false").lower() != "true":
            # I'll uncomment it later
            # raise HTTPException(status_code=400, detail="Meeting is not running")
            pass

        # Get meeting details to verify password
        meeting_info = call_bbb_api("getMeetingInfo", {"meetingID": meeting_id, "password": password})
        
        # Construct the proper join URL with checksum
        join_params = {
            "meetingID": meeting_id,
            "fullName": "Broadcaster Bot",
            "password": password
        }
        query_string = urlencode([(k, v) for k, v in join_params.items() if v])
        checksum = generate_checksum("join", query_string, BBB_SECRET)
        
        join_url = f"{BBB_SERVER_BASE_URL}join?{query_string}&checksum={checksum}"

        # Start the broadcaster
        broadcaster_response = await broadcaster_service(join_url, rtmp_url, stream_key)

        return {
            "status": "success",
            "message": "Broadcaster started successfully",
            "broadcaster_response": broadcaster_response,
            "meeting_info": meeting_info
        }
    except Exception as e:
        # Better error handling to see what's going wrong
        raise HTTPException(status_code=500, detail=f"Error in broadcaster: {str(e)}")



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
    response = call_bbb_api("create", params)
    return response


@router.get("/join")
def join_meeting(
        meeting_id: str,
        full_name: str,
        password: str,
        user_id: Optional[str] = None,
        redirect: bool = True
):
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
    checksum = generate_checksum("join", query_string, BBB_SECRET)

    join_url = f"{BBB_SERVER_BASE_URL}join?{query_string}&checksum={checksum}"

    # Either redirect or return the URL
    if redirect:
        return RedirectResponse(url=join_url)
    else:
        return {"join_url": join_url}


@router.get("/end")
def end_meeting(meeting_id: str, password: str):
    """End a BBB meeting."""
    params = {
        "meetingID": meeting_id,
        "password": password
    }

    response = call_bbb_api("end", params)
    return response


@router.get("/is-meeting-running")
def is_meeting_running(meeting_id: str):
    """Check if a meeting is running."""
    params = {
        "meetingID": meeting_id
    }

    response = call_bbb_api("isMeetingRunning", params)
    return response


@router.get("/get-meeting-info")
def get_meeting_info(meeting_id: str, password: str):
    """Get detailed information about a meeting."""
    params = {
        "meetingID": meeting_id,
        "password": password
    }

    response = call_bbb_api("getMeetingInfo", params)
    return response


@router.get("/get-meetings")
def get_meetings():
    """Get the list of all meetings."""
    response = call_bbb_api("getMeetings", {})
    return response