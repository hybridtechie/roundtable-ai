from fastapi import APIRouter, Depends, HTTPException
from typing import List
from logger_config import setup_logger
from features.chat_session import get_user_chat_sessions, get_chat_session_by_id, delete_chat_session
from models import DeleteResponse
from auth import UserClaims, validate_token

logger = setup_logger(__name__)

router = APIRouter(prefix="/chat-session", tags=["Chat Sessions"])


@router.get("s", summary="List all chat sessions for the authenticated user")
async def list_chat_sessions_endpoint(current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        logger.info("Fetching chat sessions for user: %s", user_id)
        sessions_list = await get_user_chat_sessions(user_id)
        logger.info("Successfully retrieved %d chat sessions for user: %s", len(sessions_list), user_id)
        return {"chat_sessions": sessions_list}
    except Exception as e:
        logger.error("Failed to fetch chat sessions for user %s: %s", user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat sessions: {str(e)}")


@router.get("/{session_id}", summary="Get a specific chat session")
async def get_chat_session_endpoint(session_id: str, current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        logger.info("Fetching chat session: %s for user: %s", session_id, user_id)
        session = await get_chat_session_by_id(session_id, user_id)
        if session is None:
            logger.warning("Chat session %s not found for user %s", session_id, user_id)
            raise HTTPException(status_code=404, detail="Chat session not found or access denied")
        logger.info("Successfully retrieved chat session: %s", session_id)
        return session
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to fetch chat session %s for user %s: %s", session_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat session: {str(e)}")


@router.delete("/{session_id}", response_model=DeleteResponse, summary="Delete a chat session")
async def delete_chat_session_endpoint(session_id: str, current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        logger.info("User '%s' attempting to delete chat session: %s", user_id, session_id)
        result = await delete_chat_session(session_id, user_id)
        logger.info("Successfully deleted chat session: %s by user %s", session_id, user_id)
        return result
    except Exception as e:
        logger.error("Failed to delete chat session %s for user %s: %s", session_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete chat session: {str(e)}")
