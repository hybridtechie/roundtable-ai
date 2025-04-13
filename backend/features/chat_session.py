from pydantic import BaseModel
from fastapi import HTTPException
from cosmos_db import cosmos_client
from logger_config import setup_logger
from features.meeting import get_meeting
from features.group import get_group
from datetime import datetime, timezone
import uuid

# Set up logger
logger = setup_logger(__name__)


# Models for chat endpoints
class ChatSessionCreate(BaseModel):
    meeting_id: str
    user_message: str
    session_id: str = None


async def get_user_chat_sessions(user_id: str) -> list:
    """Fetch all chat sessions for a user with meeting details."""
    try:
        chat_sessions = await cosmos_client.get_user_chat_sessions(user_id)

        # Enhance each chat session with meeting details
        enhanced_sessions = []
        for session in chat_sessions:
            # Get meeting details
            meeting_id = session.get("meeting_id")
            if meeting_id:
                try:
                    meeting = await get_meeting(meeting_id, user_id)

                    # Add meeting details to the session
                    session["meeting_topic"] = meeting.topic
                    session["meeting_name"] = meeting.name
                    session["participants"] = meeting.participants

                    # Check if meeting has a group_id and get group details
                    if meeting.group_ids and len(meeting.group_ids) > 0:
                        group_id = meeting.group_ids[0]  # Get the first group_id
                        try:
                            group = await get_group(group_id, user_id)
                            if group:
                                session["group_name"] = group.get("name")
                                session["group_id"] = group.get("id")
                        except Exception as e:
                            logger.warning(f"Could not fetch group details for meeting {meeting_id}: {str(e)}")
                            # Continue even if group details can't be fetched

                except Exception as e:
                    logger.warning(f"Could not fetch meeting details for chat session {session.get('id')}: {str(e)}")
                    # Continue even if meeting details can't be fetched
            session["display_messages"] = []
            session["messages"] = []

            enhanced_sessions.append(session)

        logger.info(f"Retrieved and enhanced {len(enhanced_sessions)} chat sessions for user {user_id}")
        return enhanced_sessions

    except Exception as e:
        logger.error(f"Error fetching chat sessions for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat sessions")


async def get_chat_session_by_id(session_id: str, user_id: str) -> dict:
    """Fetch a specific chat session by ID with meeting details."""
    try:
        # Get the chat session
        try:
            chat_session = await cosmos_client.get_chat_session(session_id, user_id)
        except Exception as e:
            logger.error(f"Error retrieving chat session {session_id}: {str(e)}")
            raise HTTPException(status_code=404, detail="Chat session not found")

        # Get meeting details
        meeting_id = chat_session.get("meeting_id")
        if meeting_id:
            try:
                meeting = await get_meeting(meeting_id, user_id)

                # Add meeting details to the response
                chat_session["meeting_topic"] = meeting.topic
                chat_session["meeting_name"] = meeting.name
                chat_session["participants"] = meeting.participants

                # Check if meeting has a group_id and get group details
                if meeting.group_ids and len(meeting.group_ids) > 0:
                    group_id = meeting.group_ids[0]  # Get the first group_id
                    try:
                        group = await get_group(group_id, user_id)
                        if group:
                            chat_session["group_name"] = group.get("name")
                    except Exception as e:
                        logger.warning(f"Could not fetch group details for meeting {meeting_id}: {str(e)}")
                        # Continue even if group details can't be fetched

            except Exception as e:
                logger.warning(f"Could not fetch meeting details for chat session {session_id}: {str(e)}")
                # Continue even if meeting details can't be fetched

        logger.info(f"Retrieved chat session {session_id} for user {user_id}")
        return chat_session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat session {session_id} for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat session")


async def delete_chat_session(session_id: str, user_id: str) -> dict:
    """Delete a chat session by ID."""
    try:
        # Check if the chat session exists
        try:
            chat_session = await cosmos_client.get_chat_session(session_id, user_id)
        except Exception as e:
            logger.error(f"Error retrieving chat session {session_id} for deletion: {str(e)}")
            raise HTTPException(status_code=404, detail="Chat session not found")

        # Delete the chat session
        await cosmos_client.delete_chat_session(session_id, user_id)

        logger.info(f"Deleted chat session {session_id} for user {user_id}")
        return {"message": f"Chat session {session_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session {session_id} for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete chat session")


async def create_chat_session(meeting_id: str, user_id: str, participant_id: str = None) -> dict:
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    chat_session = {"id": session_id, "meeting_id": meeting_id, "user_id": user_id, "messages": [], "display_messages": []}
    if participant_id:
        chat_session["participant_id"] = participant_id

    # Create session using cosmos_db client
    await cosmos_client.create_chat_session(chat_session)

    return chat_session
