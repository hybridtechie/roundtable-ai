from fastapi import HTTPException
from pydantic import BaseModel
import sqlite3
from db import collection  # Import ChromaDB collection

class AgentCreate(BaseModel):
    id: str
    name: str
    persona_description: str
    context: str

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

async def list_agents():
    """List all agents from SQLite."""
    conn = sqlite3.connect("agents.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, persona_description FROM agents")
    agents = [{"id": row[0], "name": row[1], "persona_description": row[2]} for row in cursor.fetchall()]
    conn.close()
    return {"agents": agents}