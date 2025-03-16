from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import json
import sqlite3
from dotenv import load_dotenv
from utils_llm import LLMClient  # Assuming this exists from your earlier code
import uuid  # For generating unique chatroom IDs
from chat import start_chatroom_discussion  # Import the new chat function
from db import collection  # Import ChromaDB collection

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

# Define request models using Pydantic
class AgentCreate(BaseModel):
    id: str
    name: str
    persona_description: str
    context: str

class ChatMessage(BaseModel):
    chatroom_id: str
    message: str

class ChatroomCreate(BaseModel):
    agent_ids: list[str]

class ChatroomTopic(BaseModel):
    chatroom_id: str
    topic: str

# Helper function to get LLM client
def get_llm_client():
    return LLMClient(provider=os.getenv("LLM_PROVIDER", "azure"))

# Endpoint to create an agent
@app.post("/create-agent")
async def create_agent(agent: AgentCreate):
    """Create a new agent in SQLite and store its context in ChromaDB."""
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO agents (id, name, persona_description) VALUES (?, ?, ?)",
            (agent.id, agent.name, agent.persona_description),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Agent ID '{agent.id}' already exists")
    conn.close()

    collection.add(documents=[agent.context], ids=[agent.id])
    return {"message": f"Agent '{agent.name}' with ID '{agent.id}' created successfully"}

# Endpoint to list all agents
@app.get("/list-agents")
async def list_agents():
    """List all agents from SQLite."""
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, persona_description FROM agents")
    agents = [{"id": row[0], "name": row[1], "persona_description": row[2]} for row in cursor.fetchall()]
    conn.close()
    return {"agents": agents}

# Endpoint to create a chatroom
@app.post("/create-chatroom")
async def create_chatroom(chatroom: ChatroomCreate):
    """Create a chatroom with a list of agent IDs as participants."""
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    for agent_id in chatroom.agent_ids:
        cursor.execute("SELECT id FROM agents WHERE id = ?", (agent_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"Agent ID '{agent_id}' not found")

    chatroom_id = str(uuid.uuid4())
    agent_ids_json = json.dumps(chatroom.agent_ids)
    cursor.execute("INSERT INTO chatrooms (id, agent_ids, topic) VALUES (?, ?, ?)", (chatroom_id, agent_ids_json, None))
    conn.commit()
    conn.close()
    return {"chatroom_id": chatroom_id}

# Endpoint to list all chatrooms
@app.get("/list-chatrooms")
async def list_chatrooms():
    """List all chatrooms from SQLite."""
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, agent_ids, topic FROM chatrooms")
    chatrooms_data = [{"id": row[0], "agent_ids": json.loads(row[1]), "topic": row[2]} for row in cursor.fetchall()]
    conn.close()
    return {"chatrooms": chatrooms_data}

# Endpoint to set a topic for a chatroom
@app.post("/set-chatroom-topic")
async def set_chatroom_topic(chatroom_topic: ChatroomTopic):
    """Set a topic for an existing chatroom."""
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM chatrooms WHERE id = ?", (chatroom_topic.chatroom_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Chatroom ID '{chatroom_topic.chatroom_id}' not found")

    cursor.execute("UPDATE chatrooms SET topic = ? WHERE id = ?", (chatroom_topic.topic, chatroom_topic.chatroom_id))
    conn.commit()
    conn.close()
    return {"message": f"Topic '{chatroom_topic.topic}' set for chatroom '{chatroom_topic.chatroom_id}'"}

# Updated chat endpoint to use chatroom
@app.post("/chat")
async def chat(message: ChatMessage):
    """Start a chatroom discussion with orchestrator."""
    result = await start_chatroom_discussion(message.chatroom_id, message.message)
    return result

# Run the app
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)