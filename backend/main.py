from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from features.participant import create_participant, list_participants, ParticipantCreate
from features.meeting import create_meeting, list_meetings, set_meeting_topic, MeetingCreate, MeetingTopic
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
        logger.info("Successfully retrieved %d participants", len(result))
        return result
    except Exception as e:
        logger.error("Failed to fetch participants: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch participants: {str(e)}")


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


@app.post("/meeting/topic")
async def set_meeting_topic_endpoint(meeting_topic: MeetingTopic):
    try:
        logger.info("Setting topic for meeting: %s", meeting_topic.meeting_id)
        result = await set_meeting_topic(meeting_topic)
        logger.info("Successfully set topic for meeting: %s", meeting_topic.meeting_id)
        return result
    except Exception as e:
        logger.error("Failed to set meeting topic for meeting %s: %s", meeting_topic.meeting_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to set meeting topic: {str(e)}")


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
async def chat_stream_endpoint(meeting_id: str, message: str):
    try:
        logger.info("Starting streaming chat discussion for meeting: %s", meeting_id)
        return await stream_meeting_discussion(meeting_id, message)
    except Exception as e:
        logger.error("Failed to stream chat for meeting %s: %s", meeting_id, str(e), exc_info=True)
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
