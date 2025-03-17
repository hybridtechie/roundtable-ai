from fastapi import HTTPException
from pydantic import BaseModel, Field
import sqlite3
from uuid import uuid4
from typing import Optional
from db import collection  # Import ChromaDB collection
from logger_config import setup_logger

# Set up logger
logger = setup_logger(__name__)


def validate_participant_data(name: str, persona_description: str, context: str) -> None:
    """Validate Participant data before creation."""
    try:
        if not name or not name.strip():
            logger.error("Validation failed: Name is empty or whitespace")
            raise HTTPException(status_code=400, detail="Name is required")
        if not persona_description or not persona_description.strip():
            logger.error("Validation failed: Persona description is empty or whitespace")
            raise HTTPException(status_code=400, detail="Persona description is required")
        if not context or not context.strip():
            logger.error("Validation failed: Context is empty or whitespace")
            raise HTTPException(status_code=400, detail="Context is required")
        if len(name) > 100:
            logger.error("Validation failed: Name length exceeds 100 characters")
            raise HTTPException(status_code=400, detail="Name must be less than 100 characters")
        if len(persona_description) > 1000:
            logger.error("Validation failed: Persona description length exceeds 1000 characters")
            raise HTTPException(status_code=400, detail="Persona description must be less than 1000 characters")
        if len(context) > 10000:
            logger.error("Validation failed: Context length exceeds 10000 characters")
            raise HTTPException(status_code=400, detail="Context must be less than 10000 characters")

        logger.debug("Participant data validation successful")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during participant validation: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during validation")


class ParticipantCreate(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100)
    persona_description: str = Field(..., min_length=1, max_length=1000)
    context: str = Field(..., min_length=1, max_length=10000)
    role: str = Field(default="Team Member", min_length=1, max_length=50)
    userId: str = Field(default="SuperAdmin", min_length=1)


async def create_participant(participant: ParticipantCreate):
    """Create a new Participant in SQLite and store its context in ChromaDB."""
    logger.info("Creating new participant with name: %s", participant.name)

    # Validate all required fields
    validate_participant_data(participant.name, participant.persona_description, participant.context)

    # Generate UUID if id not provided
    if participant.id is None:
        participant.id = str(uuid4())
        logger.debug("Generated new UUID for participant: %s", participant.id)

    conn = None
    try:
        conn = sqlite3.connect("roundtableai.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO participants (id, name, persona_description, role, userId) VALUES (?, ?, ?, ?, ?)",
            (participant.id, participant.name, participant.persona_description, participant.role, participant.userId),
        )
        conn.commit()
        logger.info("Successfully inserted participant into SQLite: %s", participant.id)

        try:
            collection.add(documents=[participant.context], ids=[participant.id])
            logger.info("Successfully added participant context to ChromaDB: %s", participant.id)
        except Exception as e:
            logger.error("Failed to add participant context to ChromaDB: %s - Error: %s", participant.id, str(e), exc_info=True)
            # Rollback SQLite insertion if ChromaDB fails
            cursor.execute("DELETE FROM participants WHERE id = ?", (participant.id,))
            conn.commit()
            raise HTTPException(status_code=500, detail="Failed to store participant context in vector database")

        return {"message": f"Participant '{participant.name}' with ID '{participant.id}' created successfully"}

    except sqlite3.IntegrityError as e:
        logger.error("SQLite integrity error while creating participant: %s - Error: %s", participant.id, str(e), exc_info=True)
        raise HTTPException(status_code=400, detail=f"Participant ID '{participant.id}' already exists")
    except Exception as e:
        logger.error("Unexpected error while creating participant: %s - Error: %s", participant.id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while creating participant")
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")


async def list_participants():
    """List all Participants from SQLite."""
    conn = None
    try:
        logger.info("Fetching all participants")
        conn = sqlite3.connect("roundtableai.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, persona_description, role FROM participants")
        participants = [{"id": row[0], "name": row[1], "persona_description": row[2], "role": row[3]} for row in cursor.fetchall()]

        logger.info("Successfully retrieved %d participants", len(participants))
        return {"participants": participants}

    except sqlite3.Error as e:
        logger.error("Database error while fetching participants: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve participants from database")
    except Exception as e:
        logger.error("Unexpected error while fetching participants: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving participants")
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")
