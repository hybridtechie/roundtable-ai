from fastapi import APIRouter, Depends, HTTPException
from typing import List
from logger_config import setup_logger

# Feature imports
from features.chat_session import (
    get_user_chat_sessions,
    get_chat_session_by_id,
    delete_chat_session
)

# Model imports
# Use absolute import from 'backend' directory perspective
from models import ListChatSessionsResponse, ChatSessionResponse, DeleteResponse

# Auth imports
from auth import UserClaims, validate_token

# Logger setup
logger = setup_logger(__name__)

# Create an APIRouter instance
router = APIRouter(
    prefix="/chat-session",    # Prefix for all routes in this router
    tags=["Chat Sessions"]     # Tag for OpenAPI documentation
)

# --- Chat Session CRUD Endpoints ---

# List Chat Sessions for User
@router.get("s", response_model=ListChatSessionsResponse, summary="List all chat sessions for the authenticated user") # Route is /chat-sessions
async def list_chat_sessions_endpoint(current_user: UserClaims = Depends(validate_token)):
    """
    Retrieves a list of chat sessions associated with the authenticated user.
    Requires a valid authentication token.
    """
    try:
        user_id = current_user.email
        logger.info("Fetching chat sessions for user: %s", user_id)
        # Assuming get_user_chat_sessions returns a list of session objects
        sessions_list = await get_user_chat_sessions(user_id)
        logger.info("Successfully retrieved %d chat sessions for user: %s", len(sessions_list), user_id)
        # Wrap the list in the response model structure
        return {"chat_sessions": sessions_list}
    except Exception as e:
        logger.error("Failed to fetch chat sessions for user %s: %s", user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat sessions: {str(e)}")


# Get Specific Chat Session
@router.get("/{session_id}", response_model=ChatSessionResponse, summary="Get a specific chat session")
async def get_chat_session_endpoint(session_id: str, current_user: UserClaims = Depends(validate_token)):
    """
    Retrieves details for a specific chat session by its ID, ensuring it belongs to the authenticated user.
    Requires `session_id` in the path and a valid authentication token.
    """
    try:
        user_id = current_user.email
        logger.info("Fetching chat session: %s for user: %s", session_id, user_id)
        # Assuming get_chat_session_by_id returns the session object or None
        session = await get_chat_session_by_id(session_id, user_id)
        if session is None:
            logger.warning("Chat session %s not found for user %s", session_id, user_id)
            raise HTTPException(status_code=404, detail="Chat session not found or access denied")
        logger.info("Successfully retrieved chat session: %s", session_id)
        return session
    except HTTPException as http_exc: # Re-raise 404
        raise http_exc
    except Exception as e:
        logger.error("Failed to fetch chat session %s for user %s: %s", session_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat session: {str(e)}")


# Delete Chat Session
@router.delete("/{session_id}", response_model=DeleteResponse, summary="Delete a chat session")
async def delete_chat_session_endpoint(session_id: str, current_user: UserClaims = Depends(validate_token)):
    """
    Deletes a chat session by its ID, ensuring it belongs to the authenticated user.
    Requires `session_id` in the path and a valid authentication token.
    """
    try:
        user_id = current_user.email
        logger.info("User '%s' attempting to delete chat session: %s", user_id, session_id)
        # Assuming delete_chat_session returns {"deleted_id": session_id} or similar on success
        result = await delete_chat_session(session_id, user_id)
        # Add check if deletion failed (e.g., session not found for user)
        # If delete_chat_session returns None on not found/permission error:
        # if result is None:
        #     raise HTTPException(status_code=404, detail="Chat session not found or cannot be deleted")
        logger.info("Successfully deleted chat session: %s by user %s", session_id, user_id)
        return result # Should match DeleteResponse model
    except Exception as e: # Catch potential errors
        logger.error("Failed to delete chat session %s for user %s: %s", session_id, user_id, str(e), exc_info=True)
        # Determine if 404 or 500 is more appropriate
        raise HTTPException(status_code=500, detail=f"Failed to delete chat session: {str(e)}")