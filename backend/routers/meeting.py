from fastapi import APIRouter, Depends, HTTPException
from typing import List
from logger_config import setup_logger

# Feature imports
from features.meeting import (
    create_meeting, get_meeting, list_meetings, delete_meeting,
    MeetingCreate # Assuming MeetingCreate is the input model
)
# Import MeetingTopic if set_meeting_topic endpoint is added later
# from features.meeting import set_meeting_topic, MeetingTopic

# Model imports
# Use absolute import from 'backend' directory perspective
from models import MeetingResponse, ListMeetingsResponse, DeleteResponse

# Auth imports
from auth import UserClaims, validate_token

# Logger setup
logger = setup_logger(__name__)

# Create an APIRouter instance
router = APIRouter(
    prefix="/meeting",  # Prefix for all routes in this router
    tags=["Meetings"]   # Tag for OpenAPI documentation
)

# --- Meeting Endpoints ---

# 11 Create Meeting
@router.post("", response_model=MeetingResponse, status_code=201, summary="Create a new meeting")
async def create_meeting_endpoint(meeting: MeetingCreate, current_user: UserClaims = Depends(validate_token)):
    """
    Creates a new meeting associated with a group and the authenticated user.
    Requires meeting details (including group_id) in the request body and a valid authentication token.
    """
    try:
        user_id = current_user.email
        # Add user_id to the meeting data if the create_meeting function expects it
        # meeting.user_id = user_id # Uncomment if needed by create_meeting
        logger.info("User '%s' attempting to create new meeting for group: %s", user_id, meeting.group_id)

        # Assuming create_meeting now returns a Pydantic model or dict matching MeetingResponse
        created_meeting = await create_meeting(meeting, user_id) # Pass user_id if required

        # Check if creation was successful (adjust based on create_meeting return type)
        if not created_meeting:
             logger.error("Meeting creation failed for user '%s', group '%s'. create_meeting returned None.", user_id, meeting.group_id)
             raise HTTPException(status_code=500, detail="Failed to create meeting record.")

        logger.info("Successfully created meeting with ID: %s for user '%s'", created_meeting.id, user_id)
        return created_meeting
    except Exception as e:
        logger.error("User '%s' failed to create meeting for group '%s': %s", user_id, meeting.group_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create meeting: {str(e)}")


# 12 List Meetings
@router.get("s", response_model=ListMeetingsResponse, summary="List all meetings for the authenticated user") # Route is /meetings
async def list_meetings_endpoint(current_user: UserClaims = Depends(validate_token)):
    """
    Retrieves a list of meetings associated with the authenticated user.
    Requires a valid authentication token.
    """
    try:
        user_id = current_user.email
        logger.info("Fetching all meetings for user: %s", user_id)
        # Assuming list_meetings returns a dict {"meetings": [...]} matching ListMeetingsResponse
        result = await list_meetings(user_id)
        logger.info("Successfully retrieved %d meetings for user: %s", len(result.get("meetings", [])), user_id)
        return result
    except Exception as e:
        logger.error("Failed to fetch meetings for user %s: %s", user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch meetings: {str(e)}")


# Get Meeting
@router.get("/{meeting_id}", response_model=MeetingResponse, summary="Get a specific meeting")
async def get_meeting_endpoint(meeting_id: str, current_user: UserClaims = Depends(validate_token)):
    """
    Retrieves details for a specific meeting by its ID, ensuring it belongs to the authenticated user.
    Requires `meeting_id` in the path and a valid authentication token.
    """
    try:
        user_id = current_user.email
        logger.info("Fetching meeting_id: %s for user: %s", meeting_id, user_id)
        # Assuming get_meeting returns the meeting object or None
        meeting = await get_meeting(meeting_id, user_id)
        if meeting is None:
            logger.warning("Meeting %s not found for user %s", meeting_id, user_id)
            raise HTTPException(status_code=404, detail="Meeting not found or access denied")
        logger.info("Successfully retrieved meeting: %s", meeting_id)
        return meeting
    except HTTPException as http_exc: # Re-raise 404
        raise http_exc
    except Exception as e:
        logger.error("Failed to fetch meeting %s for user %s: %s", meeting_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch meeting: {str(e)}")


# Delete Meeting
@router.delete("/{meeting_id}", response_model=DeleteResponse, summary="Delete a meeting")
async def delete_meeting_endpoint(meeting_id: str, current_user: UserClaims = Depends(validate_token)):
    """
    Deletes a meeting by its ID, ensuring it belongs to the authenticated user.
    Requires `meeting_id` in the path and a valid authentication token.
    """
    try:
        user_id = current_user.email
        logger.info("User '%s' attempting to delete meeting_id: %s", user_id, meeting_id)
        # Assuming delete_meeting returns {"deleted_id": meeting_id} on success or raises/returns None on failure
        result = await delete_meeting(meeting_id, user_id)
        # Add check if deletion failed (e.g., meeting not found for user)
        # If delete_meeting returns None on not found/permission error:
        # if result is None:
        #     raise HTTPException(status_code=404, detail="Meeting not found or cannot be deleted")
        logger.info("Successfully deleted meeting: %s by user %s", meeting_id, user_id)
        return result # Should match DeleteResponse model
    except Exception as e: # Catch potential errors
        logger.error("Failed to delete meeting %s for user %s: %s", meeting_id, user_id, str(e), exc_info=True)
        # Determine if 404 or 500 is more appropriate based on expected errors
        raise HTTPException(status_code=500, detail=f"Failed to delete meeting: {str(e)}")

# Note: The set_meeting_topic endpoint was not included in the original list to move,
# but could be added here similarly if needed.

# Note: The /chat-stream endpoint related to meetings will be handled in the chat router.