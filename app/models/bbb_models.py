from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class BroadcasterRequest(BaseModel):
    """
    Broadcaster Model for joining a BBB meeting
    """
    bbb_health_check_url: str
    bbb_server_url: str
    rtmp_url: str
    stream_key: str

class BroadcasterReq(BaseModel):
    meeting_id: str
    rtmp_url: str
    stream_key: str
    password: str

class BroadcasterResponse(BaseModel):
    """
    Response model from the broadcaster service
    """
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None

class MeetingAttendee(BaseModel):
    """
    Model for an attendee in a BBB meeting
    """
    userID: Optional[str] = None
    fullName: Optional[str] = None
    role: Optional[str] = None
    isPresenter: Optional[bool] = None
    isListeningOnly: Optional[bool] = None
    hasJoinedVoice: Optional[bool] = None
    hasVideo: Optional[bool] = None
    clientType: Optional[str] = None

class Meeting(BaseModel):
    """
    Model for a BBB meeting
    """
    meetingID: str
    meetingName: str
    createTime: Optional[str] = None
    createDate: Optional[str] = None
    voiceBridge: Optional[str] = None
    dialNumber: Optional[str] = None
    attendeePW: Optional[str] = None
    moderatorPW: Optional[str] = None
    running: Optional[bool] = None
    duration: Optional[int] = None
    hasUserJoined: Optional[bool] = None
    recording: Optional[bool] = None
    hasBeenForciblyEnded: Optional[bool] = None
    startTime: Optional[int] = None
    endTime: Optional[int] = None
    participantCount: Optional[int] = None
    listenerCount: Optional[int] = None
    voiceParticipantCount: Optional[int] = None
    videoCount: Optional[int] = None
    maxUsers: Optional[int] = None
    moderatorCount: Optional[int] = None
    attendees: Optional[List[MeetingAttendee]] = None