from fastapi import HTTPException
from pydantic import BaseModel, Field
import sqlite3
from uuid import uuid4
from typing import Optional
from db import collection  # Import ChromaDB collection


def validate_participant_data(name: str, persona_description: str, context: str) -> None:
    """Validate Participant data before creation."""
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


class ParticipantCreate(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100)
    persona_description: str = Field(..., min_length=1, max_length=1000)
    context: str = Field(..., min_length=1, max_length=10000)
    role: str = Field(default="Team Member", min_length=1, max_length=50)
    userId: str = Field(default="SuperAdmin", min_length=1)


async def create_participant(participant: ParticipantCreate):
    """Create a new Participant in SQLite and store its context in ChromaDB."""
    # Validate all required fields
    validate_participant_data(participant.name, participant.persona_description, participant.context)

    conn = sqlite3.connect("roundtableai.db")
    cursor = conn.cursor()

    # Generate UUID if id not provided
    if participant.id is None:
        participant.id = str(uuid4())

    try:
        cursor.execute(
            "INSERT INTO participants (id, name, persona_description, role, userId) VALUES (?, ?, ?, ?, ?)",
            (participant.id, participant.name, participant.persona_description, participant.role, participant.userId),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Participant ID '{participant.id}' already exists")
    conn.close()

    collection.add(documents=[participant.context], ids=[participant.id])
    return {"message": f"Participant '{participant.name}' with ID '{participant.id}' created successfully"}


async def list_participants():
    """List all Participants from SQLite."""
    conn = sqlite3.connect("roundtableai.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, persona_description, role FROM participants")
    participants = [{"id": row[0], "name": row[1], "persona_description": row[2], "role": row[3]} for row in cursor.fetchall()]
    conn.close()
    return {"participants": participants}
