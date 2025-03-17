from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from features.participant import (
    create_participant,
    get_participant,
    update_participant,
    delete_participant,
    list_participants,
    ParticipantCreate,
    ParticipantUpdate
)
from features.meeting import create_meeting, list_meetings, set_meeting_topic, MeetingCreate, MeetingTopic
from features.group import (
    create_group,
    get_group,
    update_group,
    delete_group,
    list_groups,
    GroupCreate,
    GroupUpdate
)
from features.chat import start_meeting_discussion, stream_meeting_discussion, ChatMessage
import uvicorn
from dotenv import load_dotenv
import os
from logger_config import setup_logger

# Set up logger
logger = setup_logger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# Participant endpoints
@app.post("/participant")
async def create_participant_endpoint(participant: ParticipantCreate):
    try:
        logger.info("Creating new participant: %s", participant.name)
        result = await create_participant(participant)
        logger.info("Successfully created participant: %s", participant.name)
        return result
    except Exception as e:
        logger.error("Failed to create participant: %s - Error: %s", participant.name, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create participant: {str(e)}")


@app.get("/participants")
async def list_participants_endpoint():
    try:
        logger.info("Fetching all participants")
        result = await list_participants()
        logger.info("Successfully retrieved participants")
        return result
    except Exception as e:
        logger.error("Failed to fetch participants: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch participants: {str(e)}")


@app.get("/participant/{participant_id}")
async def get_participant_endpoint(participant_id: str):
    try:
        logger.info("Fetching participant: %s", participant_id)
        result = await get_participant(participant_id)
        logger.info("Successfully retrieved participant: %s", participant_id)
        return result
    except Exception as e:
        logger.error("Failed to fetch participant %s: %s", participant_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch participant: {str(e)}")


@app.put("/participant/{participant_id}")
async def update_participant_endpoint(participant_id: str, participant: ParticipantUpdate):
    try:
        logger.info("Updating participant: %s", participant_id)
        result = await update_participant(participant_id, participant)
        logger.info("Successfully updated participant: %s", participant_id)
        return result
    except Exception as e:
        logger.error("Failed to update participant %s: %s", participant_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update participant: {str(e)}")


@app.delete("/participant/{participant_id}")
async def delete_participant_endpoint(participant_id: str):
    try:
        logger.info("Deleting participant: %s", participant_id)
        result = await delete_participant(participant_id)
        logger.info("Successfully deleted participant: %s", participant_id)
        return result
    except Exception as e:
        logger.error("Failed to delete participant %s: %s", participant_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete participant: {str(e)}")


# Group endpoints
@app.post("/group")
async def create_group_endpoint(group: GroupCreate):
    try:
        logger.info("Creating new group: %s", group.name)
        result = await create_group(group)
        logger.info("Successfully created group: %s", group.name)
        return result
    except Exception as e:
        logger.error("Failed to create group: %s - Error: %s", group.name, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create group: {str(e)}")


@app.get("/groups")
async def list_groups_endpoint():
    try:
        logger.info("Fetching all groups")
        result = await list_groups()
        logger.info("Successfully retrieved groups")
        return result
    except Exception as e:
        logger.error("Failed to fetch groups: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch groups: {str(e)}")


@app.get("/group/{group_id}")
async def get_group_endpoint(group_id: str):
    try:
        logger.info("Fetching group: %s", group_id)
        result = await get_group(group_id)
        logger.info("Successfully retrieved group: %s", group_id)
        return result
    except Exception as e:
        logger.error("Failed to fetch group %s: %s", group_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch group: {str(e)}")


@app.put("/group/{group_id}")
async def update_group_endpoint(group_id: str, group: GroupUpdate):
    try:
        logger.info("Updating group: %s", group_id)
        result = await update_group(group_id, group)
        logger.info("Successfully updated group: %s", group_id)
        return result
    except Exception as e:
        logger.error("Failed to update group %s: %s", group_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update group: {str(e)}")


@app.delete("/group/{group_id}")
async def delete_group_endpoint(group_id: str):
    try:
        logger.info("Deleting group: %s", group_id)
        result = await delete_group(group_id)
        logger.info("Successfully deleted group: %s", group_id)
        return result
    except Exception as e:
        logger.error("Failed to delete group %s: %s", group_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete group: {str(e)}")


# Meetings endpoints
@app.post("/meeting")
async def create_meeting_endpoint(meeting: MeetingCreate):
    try:
        logger.info("Creating new meeting with participants: %s", meeting.participant_ids)
        result = await create_meeting(meeting)
        logger.info("Successfully created meeting: %s", result.get("id"))
        return result
    except Exception as e:
        logger.error("Failed to create meeting: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create meeting: {str(e)}")


@app.get("/meetings")
async def list_meetings_endpoint():
    try:
        logger.info("Fetching all meetings")
        result = await list_meetings()
        logger.info("Successfully retrieved %d meetings", len(result))
        return result
    except Exception as e:
        logger.error("Failed to fetch meetings: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch meetings: {str(e)}")


# Chat endpoints
@app.post("/chat")
async def chat_endpoint(message: ChatMessage):
    try:
        logger.info("Starting chat discussion for meeting: %s", message.meeting_id)
        result = await start_meeting_discussion(message.meeting_id, message.message)
        logger.info("Successfully processed chat message for meeting: %s", message.meeting_id)
        return result
    except Exception as e:
        logger.error("Failed to process chat message for meeting %s: %s", message.meeting_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process chat message: {str(e)}")


@app.get("/chat-stream")
async def chat_stream_endpoint(group_id: str, message: str):
    try:
        logger.info("Starting streaming chat discussion for group: %s", group_id)
        return await stream_meeting_discussion(group_id, message)
    except Exception as e:
        logger.error("Failed to stream chat for group %s: %s", group_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stream chat: {str(e)}")


# Run the app
if __name__ == "__main__":
    try:
        port = int(os.getenv("PORT", "8000"))
        logger.info("Starting FastAPI server on port %d", port)
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        logger.error("Failed to start FastAPI server: %s", str(e), exc_info=True)
        raise
