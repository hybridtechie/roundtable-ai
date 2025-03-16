from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import chromadb
import os
import json
import sqlite3
from dotenv import load_dotenv
from utils_llm import LLMClient  # Assuming this exists from your earlier code
import uuid  # For generating unique chatroom IDs

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# In-memory dictionary to store chatrooms (chatroom_id: list of agent_ids)
chatrooms = {}

# Initialize SQLite database
def init_sqlite_db():
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            persona TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Initialize ChromaDB client and get or create the "agents" collection
chroma_client = chromadb.Client()
try:
    collection = chroma_client.create_collection(name="agents")
except Exception:
    collection = chroma_client.get_collection(name="agents")

# Define request models using Pydantic
class AgentCreate(BaseModel):
    id: str  # Now requiring ID explicitly
    name: str
    persona: str
    context: str

class ChatMessage(BaseModel):
    agent_id: str  # Changed from agent_name to agent_id for consistency
    message: str

class ChatroomCreate(BaseModel):
    agent_ids: list[str]

# Helper function to get LLM client
def get_llm_client():
    return LLMClient(provider=os.getenv("LLM_PROVIDER", "azure"))

# Initialize the SQLite database on startup
init_sqlite_db()

# Endpoint to create an agent
@app.post("/create-agent")
async def create_agent(agent: AgentCreate):
    """Create a new agent in SQLite and store its context in ChromaDB."""
    # Insert agent into SQLite
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO agents (id, name, persona) VALUES (?, ?, ?)",
                       (agent.id, agent.name, agent.persona))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Agent ID '{agent.id}' already exists")
    conn.close()

    # Store context in ChromaDB
    collection.add(
        documents=[agent.context],
        ids=[agent.id]
    )
    return {"message": f"Agent '{agent.name}' with ID '{agent.id}' created successfully"}

# Endpoint to list all agents
@app.get("/list-agents")
async def list_agents():
    """List all agents from SQLite."""
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, persona FROM agents")
    agents = [{"id": row[0], "name": row[1], "persona": row[2]} for row in cursor.fetchall()]
    conn.close()
    return {"agents": agents}

# Endpoint to create a chatroom
@app.post("/create-chatroom")
async def create_chatroom(chatroom: ChatroomCreate):
    """Create a chatroom with a list of agent IDs as participants."""
    # Validate agent_ids exist in SQLite
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    for agent_id in chatroom.agent_ids:
        cursor.execute("SELECT id FROM agents WHERE id = ?", (agent_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"Agent ID '{agent_id}' not found")
    conn.close()

    # Generate a unique chatroom ID
    chatroom_id = str(uuid.uuid4())
    
    # Store the chatroom with its participants
    chatrooms[chatroom_id] = chatroom.agent_ids
    
    return {"chatroom_id": chatroom_id}

# Endpoint to chat with an agent
@app.post("/chat")
async def chat(message: ChatMessage):
    """Simulate a chat with an agent using its context from ChromaDB and persona from SQLite."""
    # Retrieve agent persona from SQLite
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, persona FROM agents WHERE id = ?", (message.agent_id,))
    result = cursor.fetchone()
    conn.close()
    if not result:
        raise HTTPException(status_code=404, detail=f"Agent ID '{message.agent_id}' not found")
    agent_name, persona = result

    # Retrieve agent context from ChromaDB
    results = collection.get(ids=[message.agent_id])
    if not results['documents']:
        raise HTTPException(status_code=404, detail=f"Context for agent ID '{message.agent_id}' not found")
    context = results['documents'][0]

    # Generate a response using Azure OpenAI
    llm_client = get_llm_client()
    messages = [
        {"role": "system", "content": f"You are {agent_name} with persona: {persona}. Context: {context}"},
        {"role": "user", "content": message.message}
    ]
    response = llm_client.send_request(messages)
    
    return {"response": response}

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)