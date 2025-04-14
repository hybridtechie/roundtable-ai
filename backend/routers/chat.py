from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from logger_config import setup_logger
from typing import Annotated, Optional  # Import Annotated and Optional

from features.meeting import get_meeting
from features.chat import stream_meeting_discussion, MeetingDiscussion
from features.chat_session import ChatSessionCreate

# Import the new validation function and UserClaims
from auth import UserClaims, validate_token, validate_token_from_string

logger = setup_logger(__name__)

router = APIRouter(tags=["Chat"])


@router.get("/chat-stream", summary="Start streaming chat discussion for a meeting")
# Add token as a query parameter dependency
async def chat_stream_endpoint(meeting_id: str, token: Annotated[Optional[str], Query()] = None):
    try:
        if not token:
            logger.warning("Chat stream request failed: No token provided for Meeting %s", meeting_id)
            raise HTTPException(status_code=401, detail="Authentication token required")

        # Validate the token from the query parameter
        current_user: UserClaims = validate_token_from_string(token)
        user_id = current_user.email  # Get user_id from validated token

        logger.info("User '%s' requesting chat stream for Meeting: %s", user_id, meeting_id)

        meeting = await get_meeting(meeting_id, user_id)
        if meeting is None:
            logger.warning("Chat stream request failed: Meeting %s not found for user %s", meeting_id, user_id)
            raise HTTPException(status_code=404, detail="Meeting not found or access denied")

        logger.info("Starting chat stream for Meeting: %s, User: %s", meeting_id, user_id)
        return StreamingResponse(stream_meeting_discussion(meeting), media_type="text/event-stream")

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to start chat stream for meeting %s, user %s: %s", meeting_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stream chat: {str(e)}")


@router.post("/chat-session", summary="Process a chat request within a meeting")
async def chat_request_endpoint(chat_request: ChatSessionCreate, current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        meeting_id = chat_request.meeting_id
        logger.info("User '%s' processing chat request for Meeting: %s", user_id, meeting_id)

        meeting = await get_meeting(meeting_id, user_id)
        if meeting is None:
            logger.warning("Chat request failed: Meeting %s not found for user %s", meeting_id, user_id)
            raise HTTPException(status_code=404, detail="Meeting not found or access denied")

        discussion = MeetingDiscussion(meeting)

        result = await discussion.handle_chat_request(chat_request)

        logger.info("Successfully processed chat request for meeting %s by user %s", meeting_id, user_id)
        return result

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to process chat request for meeting %s, user %s: %s", meeting_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process chat request: {str(e)}")
