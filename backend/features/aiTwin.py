from fastapi import HTTPException
from pydantic import BaseModel, Field
import sqlite3
from uuid import uuid4
from typing import Optional
from db import collection  # Import ChromaDB collection


def validate_aitwin_data(name: str, persona_description: str, context: str) -> None:
    """Validate AiTwin data before creation."""
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    if not persona_description or not persona_description.strip():
        raise HTTPException(status_code=400, detail="Persona description is required")
    if not context or not context.strip():
        raise HTTPException(status_code=400, detail="Context is required")
    if len(name) > 100:
        raise HTTPException(status_code=400, detail="Name must be less than 100 characters")
    if len(persona_description) > 1000:
        raise HTTPException(status_code=400, detail="Persona description must be less than 1000 characters")
    if len(context) > 10000:
        raise HTTPException(status_code=400, detail="Context must be less than 10000 characters")


class AiTwinCreate(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100)
    persona_description: str = Field(..., min_length=1, max_length=1000)
    context: str = Field(..., min_length=1, max_length=10000)
    role: str = Field(default="Team Member", min_length=1, max_length=50)
    userId: str = Field(default="SuperAdmin", min_length=1)


async def create_aitwin(aitwin: AiTwinCreate):
    """Create a new AiTwin in SQLite and store its context in ChromaDB."""
    # Validate all required fields
    validate_aitwin_data(aitwin.name, aitwin.persona_description, aitwin.context)

    conn = sqlite3.connect("aitwins.db")
    cursor = conn.cursor()

    # Generate UUID if id not provided
    if aitwin.id is None:
        aitwin.id = str(uuid4())

    try:
        cursor.execute(
            "INSERT INTO aitwins (id, name, persona_description, role, userId) VALUES (?, ?, ?, ?, ?)",
            (aitwin.id, aitwin.name, aitwin.persona_description, aitwin.role, aitwin.userId),
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
    cursor.execute("SELECT id, name, persona_description, role FROM aitwins")
    aitwins = [{"id": row[0], "name": row[1], "persona_description": row[2], "role": row[3]} for row in cursor.fetchall()]
    conn.close()
    return {"aitwins": aitwins}
