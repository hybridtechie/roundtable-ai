from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from features.participant import create_participant, list_participants, ParticipantCreate
from features.meeting import create_meeting, list_meetings, set_meeting_topic, MeetingCreate, MeetingTopic
from features.chat import start_meeting_discussion, stream_meeting_discussion, ChatMessage
import uvicorn
from dotenv import load_dotenv
import os

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
    return await create_participant(participant)


@app.get("/participants")
async def list_participants_endpoint():
    return await list_participants()


# Meetings endpoints
@app.post("/meeting")
async def create_meeting_endpoint(meeting: MeetingCreate):
    return await create_meeting(meeting)


@app.get("/meetings")
async def list_meetings_endpoint():
    return await list_meetings()


@app.post("/meeting/topic")
async def set_meeting_topic_endpoint(meeting_topic: MeetingTopic):
    return await set_meeting_topic(meeting_topic)


# Chat endpoints
@app.post("/chat")
async def chat_endpoint(message: ChatMessage):
    return await start_meeting_discussion(message.meeting_id, message.message)


@app.get("/chat-stream")
async def chat_stream_endpoint(meeting_id: str, message: str):
    return await stream_meeting_discussion(meeting_id, message)


# Run the app
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
