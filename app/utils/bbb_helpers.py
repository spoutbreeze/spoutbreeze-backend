import hashlib
import xml.etree.ElementTree as ET
from fastapi import HTTPException
from typing import Dict, Any, List

def generate_checksum(call_name: str, query_params: str, shared_secret: str) -> str:
    """Generates the checksum required for BBB API calls."""
    checksum_string = call_name + query_params + shared_secret
    return hashlib.sha1(checksum_string.encode('utf-8')).hexdigest()

def parse_xml_response(xml_content: bytes, api_call: str) -> Dict[str, Any]:
    """Parses the XML response from BBB API."""
    try:
        root = ET.fromstring(xml_content)
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