from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from logger_config import setup_logger

# Feature imports
from features.meeting import get_meeting  # Needed for both endpoints
from features.chat import stream_meeting_discussion, MeetingDiscussion
from features.chat_session import ChatSessionCreate  # Input model for chat request

# Model imports
# Define specific response models in models.py if needed for chat operations
# from models import ChatResponse, ChatStreamConfirmation (Example names)

# Auth imports
from auth import UserClaims, validate_token

# Logger setup
logger = setup_logger(__name__)

# Create an APIRouter instance
router = APIRouter(tags=["Chat"])  # Tag for OpenAPI documentation

# --- Chat Endpoints ---


# 13 Start Meeting Stream
@router.get("/chat-stream", summary="Start streaming chat discussion for a meeting")
async def chat_stream_endpoint(meeting_id: str):
    """
    Initiates a server-sent event stream for real-time chat discussion within a specific meeting.
    Requires `meeting_id` as a query parameter and a valid authentication token.
    """
    try:
        # user_id = current_user.email
        user_id = "ping.nith@gmail.com"
        logger.info("User '%s' requesting chat stream for Meeting: %s", user_id, meeting_id)

        # Fetch the meeting to ensure it exists and the user has access
        meeting = await get_meeting(meeting_id, user_id)
        if meeting is None:
            logger.warning("Chat stream request failed: Meeting %s not found for user %s", meeting_id, user_id)
            raise HTTPException(status_code=404, detail="Meeting not found or access denied")

        logger.info("Starting chat stream for Meeting: %s, User: %s", meeting_id, user_id)
        # stream_meeting_discussion likely needs the meeting object fetched above
        # Ensure the function signature matches how it's called.
        return StreamingResponse(stream_meeting_discussion(meeting), media_type="text/event-stream")

    except HTTPException as http_exc:  # Re-raise 404
        raise http_exc
    except Exception as e:
        logger.error("Failed to start chat stream for meeting %s, user %s: %s", meeting_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stream chat: {str(e)}")


# Handle Chat Request (within a session context, linked to a meeting)
# Original endpoint was POST /chat-session, let's keep it consistent for now,
# although it might logically fit under /meeting/{meeting_id}/chat
@router.post("/chat-session", summary="Process a chat request within a meeting")
# Add response_model=YourChatResponseModel if you define one in models.py
async def chat_request_endpoint(chat_request: ChatSessionCreate, current_user: UserClaims = Depends(validate_token)):
    """
    Handles a specific chat message or request within the context of a meeting's discussion.
    Requires chat request details (including `meeting_id`) in the request body and a valid authentication token.
    """
    try:
        user_id = current_user.email
        meeting_id = chat_request.meeting_id
        logger.info("User '%s' processing chat request for Meeting: %s", user_id, meeting_id)

        # Fetch the meeting to ensure it exists and the user has access
        meeting = await get_meeting(meeting_id, user_id)
        if meeting is None:
            logger.warning("Chat request failed: Meeting %s not found for user %s", meeting_id, user_id)
            raise HTTPException(status_code=404, detail="Meeting not found or access denied")

        # Initialize the discussion handler
        discussion = MeetingDiscussion(meeting)  # Pass the fetched meeting object

        # Handle the chat request using the feature logic
        result = await discussion.handle_chat_request(chat_request)  # Pass the input request model

        logger.info("Successfully processed chat request for meeting %s by user %s", meeting_id, user_id)
        # The original code returned 'result' directly. Define a response model for clarity if possible.
        return result

    except HTTPException as http_exc:  # Re-raise 404
        raise http_exc
    except Exception as e:
        logger.error("Failed to process chat request for meeting %s, user %s: %s", meeting_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process chat request: {str(e)}")
