from fastapi import HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4
from typing import Optional
from logger_config import setup_logger
from cosmos_db import cosmos_client

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


class ParticipantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    persona_description: str = Field(..., min_length=1, max_length=1000)
    role: str = Field(default="Team Member", min_length=1, max_length=50)
    userId: str = Field(default="roundtable_ai_admin", min_length=1)


class ParticipantCreate(ParticipantBase):
    id: Optional[str] = None
    context: str = Field(..., min_length=1, max_length=10000)


class ParticipantUpdate(ParticipantBase):
    context: Optional[str] = Field(None, min_length=1, max_length=10000)


async def create_participant(participant: ParticipantCreate):
    """Create a new Participant."""
    logger.info("Creating new participant with name: %s", participant.name)

    # Validate all required fields
    validate_participant_data(participant.name, participant.persona_description, participant.context)

    # Generate UUID if id not provided
    if participant.id is None:
        participant.id = str(uuid4())
        logger.debug("Generated new UUID for participant: %s", participant.id)

    try:
        # Store the participant data in Cosmos DB
        participant_data = {
            "id": participant.id,
            "name": participant.name,
            "persona_description": participant.persona_description,
            "role": participant.role,
            "context": participant.context,
            "userId": participant.userId
        }
        
        await cosmos_client.add_participant(participant.userId, participant_data)
        logger.info("Successfully created participant: %s", participant.id)
        
        return {"message": f"Participant '{participant.name}' with ID '{participant.id}' created successfully"}

    except Exception as e:
        logger.error("Error creating participant: %s - Error: %s", participant.id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while creating participant")


async def update_participant(participant_id: str, participant: ParticipantUpdate):
    """Update a Participant."""
    try:
        logger.info("Updating participant with ID: %s", participant_id)
        
        # Get current participant to check existence
        current_participant = await cosmos_client.get_participant(participant.userId, participant_id)
        if not current_participant:
            logger.error("Participant not found with ID: %s", participant_id)
            raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")

        # Update participant data
        participant_data = {
            "id": participant_id,
            "name": participant.name,
            "persona_description": participant.persona_description,
            "role": participant.role,
            "userId": participant.userId
        }
        
        if participant.context:
            participant_data["context"] = participant.context

        await cosmos_client.update_participant(participant.userId, participant_id, participant_data)
        logger.info("Successfully updated participant: %s", participant_id)
        return {"message": f"Participant with ID '{participant_id}' updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating participant %s: %s", participant_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error while updating participant")


async def delete_participant(participant_id: str, user_id: str):
    """Delete a Participant."""
    try:
        logger.info("Deleting participant with ID: %s", participant_id)
        
        # Get current participant to check existence
        current_participant = await cosmos_client.get_participant(user_id, participant_id)
        if not current_participant:
            logger.error("Participant not found with ID: %s", participant_id)
            raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")

        await cosmos_client.delete_participant(user_id, participant_id)
        logger.info("Successfully deleted participant: %s", participant_id)
        return {"message": f"Participant with ID '{participant_id}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting participant %s: %s", participant_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error while deleting participant")


async def get_participant(participant_id: str, user_id: str):
    """Get a specific Participant."""
    try:
        logger.info("Fetching participant with ID: %s", participant_id)
        participant = await cosmos_client.get_participant(user_id, participant_id)
        
        if not participant:
            logger.error("Participant not found with ID: %s", participant_id)
            raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")

        logger.info("Successfully retrieved participant: %s", participant_id)
        return participant

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching participant %s: %s", participant_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error while retrieving participant")


async def list_participants(user_id: str):
    """List all Participants."""
    try:
        logger.info("Fetching all participants")
        participants = await cosmos_client.list_participants(user_id)
        
        logger.info("Successfully retrieved %d participants", len(participants))
        return {"participants": participants}

    except Exception as e:
        logger.error("Error listing participants: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving participants")
