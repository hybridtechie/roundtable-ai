from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from features.participant import create_participant, get_participant, update_participant, delete_participant, list_participants, ParticipantCreate, ParticipantUpdate
from features.meeting import create_meeting, list_meetings, set_meeting_topic, MeetingCreate, MeetingTopic
from features.group import create_group, get_group, update_group, delete_group, list_groups, GroupCreate, GroupUpdate
from features.chat import stream_meeting_discussion
from fastapi.responses import StreamingResponse
import uvicorn
from dotenv import load_dotenv
import os
from logger_config import setup_logger
from utils_llm import LLMClient
from prompts import generate_questions_prompt
from pydantic import BaseModel

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


# 01 Create Participant
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

# 02 List Participants
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

# 03 Get Participant
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

# 04 Update Participant
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

# 05 Delete Participant
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


# 06 Create Group
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

#  07 List Groups
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


# 08 Get Group
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

#  09 Update Group
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

#  10 Delete Group
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


# 11 Create Meeting
@app.post("/meeting")
async def create_meeting_endpoint(meeting: MeetingCreate):
    try:
        logger.info("Creating new meeting with group: %s", meeting.group_id)
        result = await create_meeting(meeting)
        logger.info("Successfully created meeting: %s", result.get("id"))
        return result
    except Exception as e:
        logger.error("Failed to create meeting: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create meeting: {str(e)}")

# 12 List Meetings
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

# 13 Start Meeting
@app.get("/chat-stream")
async def chat_stream_endpoint(meeting_id: str):
    try:
        logger.info("Starting streaming chat discussion for Meeting: %s", meeting_id)
        # Wrap the async generator in StreamingResponse
        return StreamingResponse(stream_meeting_discussion(meeting_id), media_type="text/event-stream")
    except Exception as e:
        logger.error("Failed to stream chat for group %s: %s", meeting_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stream chat: {str(e)}")

# 14 Generate Questions
@app.get("/get-questions")
async def generate_questions_endpoint(topic: str, group_id: str):
    try:
        logger.info("Generating questions for topic: %s and group: %s", topic, group_id)

        # Fetch group details
        group = await get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_id} not found")

        # Initialize LLM client
        llm_client = LLMClient(provider="azure")

        # Get prompt from prompts.py

        prompt = generate_questions_prompt(topic, group)

        messages = [{"role": "system", "content": prompt}]
        response, _ = llm_client.send_request(messages)
        questions = [line.strip()[3:] for line in response.strip().split("\n") if line.strip()]

        if len(questions) < 10:
            raise HTTPException(status_code=500, detail="Failed to generate sufficient questions")

        logger.info("Generated questions: %s", questions)
        return {"questions": questions}
    except Exception as e:
        logger.error("Failed to generate questions: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")


# Run the app
if __name__ == "__main__":
    try:
        port = int(os.getenv("PORT", "8000"))
        logger.info("Starting FastAPI server on port %d", port)
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        logger.error("Failed to start FastAPI server: %s", str(e), exc_info=True)
        raise
