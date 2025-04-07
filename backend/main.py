from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from features.participant import create_participant, get_participant, update_participant, delete_participant, list_participants, ParticipantCreate, ParticipantUpdate
from features.meeting import create_meeting, get_meeting, list_meetings, set_meeting_topic, delete_meeting, MeetingCreate, MeetingTopic
from features.group import create_group, get_group, update_group, delete_group, list_groups, GroupCreate, GroupUpdate
from features.chat import stream_meeting_discussion, MeetingDiscussion
from features.chat_session import ChatSessionCreate, get_user_chat_sessions, get_chat_session_by_id, delete_chat_session
from features.llm import create_llm_account, update_llm_account, delete_llm_account, get_llm_accounts, set_default_provider, LLMAccountCreate, LLMAccountUpdate
from features.questions import generate_questions
from features.user import get_me, get_me_detail, login_user
from fastapi.responses import StreamingResponse
import uvicorn
from dotenv import load_dotenv
import os
from logger_config import setup_logger
from utils_llm import LLMClient
from prompts import generate_questions_prompt
import requests
from typing import Annotated
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jws, jwt, ExpiredSignatureError, JWTError, JWSError
from jose.exceptions import JWTClaimsError
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
    allow_origins=["http://localhost:5173", "https://wa-roundtableai-frontend-cefzgxbba8c4aqga.australiaeast-01.azurewebsites.net"],  # Local development frontend URL  # Azure deployed frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE") # Keep for potential future use with access tokens
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID") # Add Client ID for ID token validation

jwks_endpoint = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
jwks = requests.get(jwks_endpoint).json()["keys"]

security = HTTPBearer()

class UserClaims(BaseModel):
    sub: str
    permissions: list[str]

def find_public_key(kid):
    for key in jwks:
        if key["kid"] == kid:
            return key


def validate_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    try:
        unverified_headers = jws.get_unverified_header(credentials.credentials)
        token_payload = jwt.decode(
            token=credentials.credentials,
            key=find_public_key(unverified_headers["kid"]),
            audience=AUTH0_AUDIENCE,
            algorithms="RS256",
        )
        return UserClaims(
            sub=token_payload["sub"], permissions=token_payload.get("permissions", [])
        )
    except (
        ExpiredSignatureError,
        JWTError,
        JWTClaimsError,
        JWSError,
    ) as error:
        raise HTTPException(status_code=401, detail=str(error))

# Health Check endpoint
@app.get("/")
async def health_check():
    try:
        logger.info("Health check request received")
        return {"status": "Healthy"}
    except Exception as e:
        logger.error("Health check failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Service unhealthy")


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
async def list_participants_endpoint(user_id: str):
    try:
        logger.info("Fetching all participants for user: %s", user_id)
        result = await list_participants(user_id)
        logger.info("Successfully retrieved participants")
        return result
    except Exception as e:
        logger.error("Failed to fetch participants: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch participants: {str(e)}")


# 03 Get Participant
@app.get("/participant/{participant_id}")
async def get_participant_endpoint(participant_id: str, user_id: str):
    try:
        logger.info("Fetching participant: %s for user: %s", participant_id, user_id)
        result = await get_participant(participant_id, user_id)
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
async def delete_participant_endpoint(participant_id: str, user_id: str):
    try:
        logger.info("Deleting participant: %s for user: %s", participant_id, user_id)
        result = await delete_participant(participant_id, user_id)
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
async def list_groups_endpoint(user_id: str):
    try:
        logger.info("Fetching all groups for user: %s", user_id)
        result = await list_groups(user_id)
        logger.info("Successfully retrieved groups")
        return result
    except Exception as e:
        logger.error("Failed to fetch groups: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch groups: {str(e)}")


# 08 Get Group
@app.get("/group/{group_id}")
async def get_group_endpoint(group_id: str, user_id: str):
    try:
        logger.info("Fetching group: %s for user: %s", group_id, user_id)
        result = await get_group(group_id, user_id)
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
async def delete_group_endpoint(group_id: str, user_id: str):
    try:
        logger.info("Deleting group: %s for user: %s", group_id, user_id)
        result = await delete_group(group_id, user_id)
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
async def list_meetings_endpoint(user_id: str):
    try:
        logger.info("Fetching all meetings for user: %s", user_id)
        result = await list_meetings(user_id)
        logger.info("Successfully retrieved %d meetings", len(result["meetings"]))
        return result
    except Exception as e:
        logger.error("Failed to fetch meetings: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch meetings: {str(e)}")


# Delete Meeting
@app.delete("/meeting/{meeting_id}")
async def delete_meeting_endpoint(meeting_id: str, user_id: str):
    try:
        logger.info("Deleting meeting: %s for user: %s", meeting_id, user_id)
        result = await delete_meeting(meeting_id, user_id)
        logger.info("Successfully deleted meeting: %s", meeting_id)
        return result
    except Exception as e:
        logger.error("Failed to delete meeting %s: %s", meeting_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete meeting: {str(e)}")


# Get Meeting
@app.get("/meeting/{meeting_id}")
async def get_meeting_endpoint(meeting_id: str, user_id: str):
    try:
        logger.info("Fetching meeting: %s for user: %s", meeting_id, user_id)
        result = await get_meeting(meeting_id, user_id)
        logger.info("Successfully retrieved meeting: %s", meeting_id)
        return result
    except Exception as e:
        logger.error("Failed to fetch meeting %s: %s", meeting_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch meeting: {str(e)}")


# 13 Start Meeting
@app.get("/chat-stream")
async def chat_stream_endpoint(meeting_id: str, user_id: str):
    try:
        logger.info("Starting streaming chat discussion for Meeting: %s, User: %s", meeting_id, user_id)
        # Get meeting with updated signature
        meeting = await get_meeting(meeting_id, user_id)
        # Wrap the async generator in StreamingResponse
        return StreamingResponse(stream_meeting_discussion(meeting), media_type="text/event-stream")
    except Exception as e:
        logger.error("Failed to stream chat for meeting %s: %s", meeting_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stream chat: {str(e)}")


# Chat Session endpoint
@app.post("/chat-session")
async def chat_session_endpoint(chat_request: ChatSessionCreate, user_id: str):
    try:
        logger.info("Processing chat request for Meeting: %s, User: %s", chat_request.meeting_id, user_id)

        # Get meeting details
        meeting = await get_meeting(chat_request.meeting_id, user_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Initialize MeetingDiscussion
        discussion = MeetingDiscussion(meeting)

        # Handle the chat request
        result = await discussion.handle_chat_request(chat_request)

        logger.info("Successfully processed chat request")
        return result
    except Exception as e:
        logger.error("Failed to process chat request: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process chat request: {str(e)}")


# Chat Sessions endpoint
@app.get("/chat-sessions")
async def list_chat_sessions_endpoint(user_id: str):
    try:
        logger.info("Fetching chat sessions for user: %s", user_id)
        result = await get_user_chat_sessions(user_id)
        logger.info("Successfully retrieved chat sessions for user: %s", user_id)
        return {"chat_sessions": result}
    except Exception as e:
        logger.error("Failed to fetch chat sessions: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat sessions: {str(e)}")


# Get Chat Session by ID endpoint
@app.get("/chat-session/{session_id}")
async def get_chat_session_endpoint(session_id: str, user_id: str):
    try:
        logger.info("Fetching chat session: %s for user: %s", session_id, user_id)
        result = await get_chat_session_by_id(session_id, user_id)
        logger.info("Successfully retrieved chat session: %s", session_id)
        return result
    except Exception as e:
        logger.error("Failed to fetch chat session %s: %s", session_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat session: {str(e)}")


# Delete Chat Session endpoint
@app.delete("/chat-session/{session_id}")
async def delete_chat_session_endpoint(session_id: str, user_id: str):
    try:
        logger.info("Deleting chat session: %s for user: %s", session_id, user_id)
        result = await delete_chat_session(session_id, user_id)
        logger.info("Successfully deleted chat session: %s", session_id)
        return result
    except Exception as e:
        logger.error("Failed to delete chat session %s: %s", session_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete chat session: {str(e)}")


# LLM Account Management Endpoints


# Create LLM Account
@app.post("/llm-account")
async def create_llm_account_endpoint(llm: LLMAccountCreate):
    try:
        logger.info("Creating LLM account for provider: %s", llm.provider)
        result = await create_llm_account(llm)
        logger.info("Successfully created LLM account")
        return result
    except Exception as e:
        logger.error("Failed to create LLM account: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create LLM account: {str(e)}")


# List LLM Accounts
@app.get("/llm-accounts")
async def list_llm_accounts_endpoint(user_id: str):
    try:
        logger.info("Fetching LLM accounts for user: %s", user_id)
        result = await get_llm_accounts(user_id)
        logger.info("Successfully retrieved LLM accounts")
        return result
    except Exception as e:
        logger.error("Failed to fetch LLM accounts: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch LLM accounts: {str(e)}")


# Update LLM Account
@app.put("/llm-account/{provider}")
async def update_llm_account_endpoint(provider: str, llm: LLMAccountUpdate):
    try:
        logger.info("Updating LLM account for provider: %s", provider)
        result = await update_llm_account(provider, llm)
        logger.info("Successfully updated LLM account")
        return result
    except Exception as e:
        logger.error("Failed to update LLM account: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update LLM account: {str(e)}")


# Delete LLM Account
@app.delete("/llm-account/{provider}")
async def delete_llm_account_endpoint(provider: str, user_id: str):
    try:
        logger.info("Deleting LLM account for provider: %s", provider)
        result = await delete_llm_account(provider, user_id)
        logger.info("Successfully deleted LLM account")
        return result
    except Exception as e:
        logger.error("Failed to delete LLM account: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete LLM account: {str(e)}")


# Set Default Provider
@app.put("/llm-account/{provider}/set-default")
async def set_default_provider_endpoint(provider: str, user_id: str):
    try:
        logger.info("Setting default provider to: %s", provider)
        result = await set_default_provider(provider, user_id)
        logger.info("Successfully set default provider")
        return result
    except Exception as e:
        logger.error("Failed to set default provider: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to set default provider: {str(e)}")


# 14 Generate Questions
@app.get("/get-questions")
async def generate_questions_endpoint(topic: str, group_id: str, user_id: str):
    """Endpoint to generate questions based on topic and group context."""
    try:
        result = await generate_questions(topic, group_id, user_id)
        return result
    except Exception as e:
        logger.error("Failed to generate questions: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")

# User Endpoints

# Login User
@app.post("/login")
async def login_endpoint(token_payload: UserClaims = Depends(validate_token)):
    try:
        logger.info("Processing login request")
        # result = await login_user(authorization)
        logger.info("Successfully processed login request")
        return token_payload
    except Exception as e:
        logger.error("Login failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")



# Get Basic User Information
@app.get("/user/me")
async def get_user_info_endpoint(user_id: str):
    try:
        logger.info("Fetching basic user information for user: %s", user_id)
        result = await get_me(user_id)
        logger.info("Successfully retrieved basic user information")
        return result
    except Exception as e:
        logger.error("Failed to fetch user information: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch user information: {str(e)}")


# Get Detailed User Information with Counts
@app.get("/user/me/detail")
async def get_user_detail_endpoint(user_id: str):
    try:
        logger.info("Fetching detailed user information for user: %s", user_id)
        result = await get_me_detail(user_id)
        logger.info("Successfully retrieved detailed user information")
        return result
    except Exception as e:
        logger.error("Failed to fetch detailed user information: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch detailed user information: {str(e)}")


# Run the app
if __name__ == "__main__":
    try:
        port = int(os.getenv("PORT", "8000"))
        logger.info("Starting FastAPI server on port %d", port)
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        logger.error("Failed to start FastAPI server: %s", str(e), exc_info=True)
        raise
