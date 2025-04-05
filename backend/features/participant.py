from fastapi import HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4
from typing import Optional
from logger_config import setup_logger
from cosmos_db import cosmos_client

# Set up logger
logger = setup_logger(__name__)

def generate_persona_description(participant: 'ParticipantBase') -> str:
    """Generate a markdown formatted persona description from participant fields."""
    persona_parts = [f"You are {participant.name} with role {participant.role}. Your details are below:\n"]
    
    field_sections = [
        ("Professional Background", participant.professional_background),
        ("Industry Experience", participant.industry_experience),
        ("Role Overview", participant.role_overview),
        ("Technical Stack", participant.technical_stack),
        ("Soft Skills", participant.soft_skills),
        ("Core Qualities", participant.core_qualities),
        ("Style Preferences", participant.style_preferences),
        ("Additional Information", participant.additional_info)
    ]
    
    for section_title, content in field_sections:
        if content:
            persona_parts.append(f"\n## {section_title}\n{content}")
            
    return "\n".join(persona_parts)


def validate_participant_data(data: dict) -> None:
    """Validate Participant data before creation."""
    try:
        required_fields = [
            ("name", 100),
            ("role", 100),
            ("professional_background", 2000),
            ("industry_experience", 1000),
            ("role_overview", 1000),
            ("technical_stack", 1000),
            ("soft_skills", 1000),
            ("core_qualities", 1000),
            ("style_preferences", 1000)
        ]

        for field, max_length in required_fields:
            if not data.get(field) or not str(data[field]).strip():
                logger.error(f"Validation failed: {field} is empty or whitespace")
                raise HTTPException(status_code=400, detail=f"{field.replace('_', ' ').title()} is required")
            
            if len(str(data[field])) > max_length:
                logger.error(f"Validation failed: {field} length exceeds {max_length} characters")
                raise HTTPException(
                    status_code=400,
                    detail=f"{field.replace('_', ' ').title()} must be less than {max_length} characters"
                )

        logger.debug("Participant data validation successful")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during participant validation: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during validation")


class ParticipantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., min_length=1, max_length=100)
    professional_background: str = Field(..., min_length=1, max_length=2000)
    industry_experience: str = Field(..., min_length=1, max_length=1000)
    role_overview: str = Field(..., min_length=1, max_length=1000)
    technical_stack: Optional[str] = Field(..., min_length=1, max_length=1000)
    soft_skills: Optional[str] = Field(..., min_length=1, max_length=1000)
    core_qualities: Optional[str] = Field(..., min_length=1, max_length=1000)
    style_preferences: Optional[str] = Field(..., min_length=1, max_length=1000)
    additional_info: Optional[str] = Field(default="", max_length=1000)
    user_id: str = Field(default="roundtable_ai_admin", min_length=1)
    persona_description: Optional[str] = Field(default="", max_length=5000)


class ParticipantCreate(ParticipantBase):
    id: Optional[str] = None


class ParticipantUpdate(ParticipantBase):
    pass


async def create_participant(participant: ParticipantCreate):
    """Create a new Participant."""
    logger.info("Creating new participant with name: %s", participant.name)

    # Validate all required fields
    # Convert model to dict for validation
    participant_dict = participant.dict()
    validate_participant_data(participant_dict)

    # Generate UUID if id not provided
    if participant.id is None:
        participant.id = str(uuid4())
        logger.debug("Generated new UUID for participant: %s", participant.id)

    try:
        # Generate persona description using helper function
        persona_description = generate_persona_description(participant)
        
        # Store the participant data in Cosmos DB
        participant_data = {
            "id": participant.id,
            "name": participant.name,
            "role": participant.role,
            "professional_background": participant.professional_background,
            "industry_experience": participant.industry_experience,
            "role_overview": participant.role_overview,
            "technical_stack": participant.technical_stack,
            "soft_skills": participant.soft_skills,
            "core_qualities": participant.core_qualities,
            "style_preferences": participant.style_preferences,
            "additional_info": participant.additional_info,
            "user_id": participant.user_id,
            "persona_description": persona_description
        }
        
        await cosmos_client.add_participant(participant.user_id, participant_data)
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
        current_participant = await cosmos_client.get_participant(participant.user_id, participant_id)
        if not current_participant:
            logger.error("Participant not found with ID: %s", participant_id)
            raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")

        # Generate persona description using helper function
        persona_description = generate_persona_description(participant)
        
        # Update participant data
        participant_data = {
            "id": participant_id,
            "name": participant.name,
            "role": participant.role,
            "professional_background": participant.professional_background,
            "industry_experience": participant.industry_experience,
            "role_overview": participant.role_overview,
            "technical_stack": participant.technical_stack,
            "soft_skills": participant.soft_skills,
            "core_qualities": participant.core_qualities,
            "style_preferences": participant.style_preferences,
            "additional_info": participant.additional_info,
            "user_id": participant.user_id,
            "persona_description": persona_description
        }

        await cosmos_client.update_participant(participant.user_id, participant_id, participant_data)
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
