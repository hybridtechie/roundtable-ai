from fastapi import APIRouter, Depends, HTTPException
from typing import List
from logger_config import setup_logger

from features.meeting import create_meeting, get_meeting, list_meetings, delete_meeting, MeetingCreate

from models import MeetingResponse, ListMeetingsResponse, DeleteResponse

from auth import UserClaims, validate_token

logger = setup_logger(__name__)

router = APIRouter(prefix="/meeting", tags=["Meetings"])


@router.post("", response_model=MeetingResponse, status_code=201, summary="Create a new meeting")
async def create_meeting_endpoint(meeting: MeetingCreate, current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        meeting.user_id = user_id
        logger.info("User '%s' attempting to create new meeting for group: %s", user_id, meeting.group_id)

        created_meeting = await create_meeting(meeting)

        if not created_meeting or "meeting_id" not in created_meeting:
            logger.error("Meeting creation failed for user '%s', group '%s'. create_meeting returned None.", user_id, meeting.group_id)
            raise HTTPException(status_code=500, detail="Failed to create meeting record.")

        response = {
            "id": created_meeting["meeting_id"],
            "group_id": meeting.group_id or "",
            "topic": meeting.topic,
            "status": "created",
            "created_at": str(int(meeting._ts)) if meeting._ts else "",
            "user_id": user_id,
        }

        logger.info("Successfully created meeting with ID: %s for user '%s'", response["id"], user_id)
        return response
    except Exception as e:
        logger.error("User '%s' failed to create meeting for group '%s': %s", user_id, meeting.group_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create meeting: {str(e)}")


@router.get("s", response_model=ListMeetingsResponse, summary="List all meetings for the authenticated user")
async def list_meetings_endpoint(current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        logger.info("Fetching all meetings for user: %s", user_id)
        result = await list_meetings(user_id)
        logger.info("Successfully retrieved %d meetings for user: %s", len(result.get("meetings", [])), user_id)
        return result
    except Exception as e:
        logger.error("Failed to fetch meetings for user %s: %s", user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch meetings: {str(e)}")


@router.get("/{meeting_id}", response_model=MeetingResponse, summary="Get a specific meeting")
async def get_meeting_endpoint(meeting_id: str, current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        logger.info("Fetching meeting_id: %s for user: %s", meeting_id, user_id)
        meeting = await get_meeting(meeting_id, user_id)
        if meeting is None:
            logger.warning("Meeting %s not found for user %s", meeting_id, user_id)
            raise HTTPException(status_code=404, detail="Meeting not found or access denied")
        logger.info("Successfully retrieved meeting: %s", meeting_id)
        return meeting
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to fetch meeting %s for user %s: %s", meeting_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch meeting: {str(e)}")


@router.delete("/{meeting_id}", response_model=DeleteResponse, summary="Delete a meeting")
async def delete_meeting_endpoint(meeting_id: str, current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        logger.info("User '%s' attempting to delete meeting_id: %s", user_id, meeting_id)
        result = await delete_meeting(meeting_id, user_id)
        logger.info("Successfully deleted meeting: %s by user %s", meeting_id, user_id)
        return result
    except Exception as e:
        logger.error("Failed to delete meeting %s for user %s: %s", meeting_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete meeting: {str(e)}")
