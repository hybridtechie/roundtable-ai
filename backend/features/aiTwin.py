from fastapi import HTTPException
from pydantic import BaseModel
import sqlite3
from db import collection  # Import ChromaDB collection

class AiTwinCreate(BaseModel):
    id: str
    name: str
    persona_description: str
    context: str
    userId: str = "SuperAdmin"

async def create_aitwin(aitwin: AiTwinCreate):
    """Create a new AiTwin in SQLite and store its context in ChromaDB."""
    conn = sqlite3.connect("aitwins.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO aitwins (id, name, persona_description, userId) VALUES (?, ?, ?, ?)",
            (aitwin.id, aitwin.name, aitwin.persona_description, aitwin.userId),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail=f"AiTwin ID '{aitwin.id}' already exists")
    conn.close()

    collection.add(documents=[aitwin.context], ids=[aitwin.id])
    return {"message": f"AiTwin '{aitwin.name}' with ID '{aitwin.id}' created successfully"}

async def list_aitwins():
    """List all AiTwins from SQLite."""
    conn = sqlite3.connect("aitwins.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, persona_description FROM aitwins")
    aitwins = [{"id": row[0], "name": row[1], "persona_description": row[2]} for row in cursor.fetchall()]
    conn.close()
    return {"aitwins": aitwins}