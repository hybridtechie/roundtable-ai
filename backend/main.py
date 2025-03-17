from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from features.agents import create_agent, list_agents, AgentCreate
from features.chatrooms import create_chatroom, list_chatrooms, set_chatroom_topic, ChatroomCreate, ChatroomTopic
from features.chat import start_chatroom_discussion, stream_chatroom_discussion, ChatMessage
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

# Agents endpoints
@app.post("/create-agent")
async def create_agent_endpoint(agent: AgentCreate):
    return await create_agent(agent)

@app.get("/list-agents")
async def list_agents_endpoint():
    return await list_agents()

# Chatrooms endpoints
@app.post("/create-chatroom")
async def create_chatroom_endpoint(chatroom: ChatroomCreate):
    return await create_chatroom(chatroom)

@app.get("/list-chatrooms")
async def list_chatrooms_endpoint():
    return await list_chatrooms()

@app.post("/set-chatroom-topic")
async def set_chatroom_topic_endpoint(chatroom_topic: ChatroomTopic):
    return await set_chatroom_topic(chatroom_topic)

# Chat endpoints
@app.post("/chat")
async def chat_endpoint(message: ChatMessage):
    return await start_chatroom_discussion(message.chatroom_id, message.message)

@app.post("/chat-stream")
async def chat_stream_endpoint(message: ChatMessage):
    return await stream_chatroom_discussion(message.chatroom_id, message.message)

# Run the app
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)