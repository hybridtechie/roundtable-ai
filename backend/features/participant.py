from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, Field, validator
from uuid import uuid4
from typing import Optional, List, Dict
import re
from logger_config import setup_logger
from cosmos_db import cosmos_client
from blob_db import blob_db

# Set up logger
logger = setup_logger(__name__)


def generate_persona_description(participant: "ParticipantBase") -> str:
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
        ("Additional Information", participant.additional_info),
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
            ("style_preferences", 1000),
        ]

        for field, max_length in required_fields:
            if not data.get(field) or not str(data[field]).strip():
                logger.error(f"Validation failed: {field} is empty or whitespace")
                raise HTTPException(status_code=400, detail=f"{field.replace('_', ' ').title()} is required")

            if len(str(data[field])) > max_length:
                logger.error(f"Validation failed: {field} length exceeds {max_length} characters")
                raise HTTPException(status_code=400, detail=f"{field.replace('_', ' ').title()} must be less than {max_length} characters")

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
    docs: Optional[List[Dict]] = Field(default_factory=list)

    @validator('docs')
    def validate_docs(cls, v):
        if v is None:
            return []
        return v


class ParticipantCreate(ParticipantBase):
    id: Optional[str] = None


class ParticipantUpdate(ParticipantBase):
    pass


class ParticipantResponse(ParticipantBase):
    id: str


async def create_participant(participant: ParticipantCreate) -> ParticipantResponse:
    """Create a new Participant and return the created object."""
    logger.info("Creating new participant with name: %s", participant.name)

    # Validate all required fields
    participant_dict = participant.dict(exclude_unset=True)
    validate_participant_data(participant_dict)

    # Generate UUID if id not provided
    generated_id = participant.id if participant.id else str(uuid4())
    logger.debug("Using participant ID: %s", generated_id)

    try:
        # Generate persona description
        persona_description = generate_persona_description(participant)

        # Prepare the data to be stored in Cosmos DB
        participant_data = {
            "id": generated_id,
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
            "persona_description": persona_description,
            "docs": []
        }

        await cosmos_client.add_participant(participant.user_id, participant_data)
        logger.info("Successfully created participant: %s", generated_id)

        return ParticipantResponse(**participant_data)

    except Exception as e:
        logger.error("Error creating participant: %s - Error: %s", generated_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while creating participant")


async def update_participant(participant_id: str, participant: ParticipantUpdate) -> ParticipantResponse:
    """Update a Participant and return the updated object."""
    try:
        logger.info("Updating participant with ID: %s", participant_id)

        # Get current participant to check existence
        current_participant = await cosmos_client.get_participant(participant.user_id, participant_id)
        if not current_participant:
            logger.error("Participant not found with ID: %s", participant_id)
            raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")

        # Validate incoming data
        participant_dict = participant.dict(exclude_unset=True)
        validate_participant_data(participant_dict)

        # Generate persona description
        persona_description = generate_persona_description(participant)

        # Prepare the full data object for update in Cosmos DB
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
            "persona_description": persona_description,
            "docs": current_participant.get("docs", [])  # Preserve existing docs
        }

        await cosmos_client.update_participant(participant.user_id, participant_id, participant_data)
        logger.info("Successfully updated participant: %s", participant_id)

        return ParticipantResponse(**participant_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating participant %s: %s", participant_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while updating participant")


async def delete_participant(participant_id: str, user_id: str) -> dict:
    """Delete a Participant and return the deleted ID."""
    try:
        logger.info("Deleting participant with ID: %s for user: %s", participant_id, user_id)

        # Get current participant to check existence and get documents
        current_participant = await cosmos_client.get_participant(user_id, participant_id)
        if not current_participant:
            logger.error("Participant not found with ID: %s", participant_id)
            raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")

        # Delete all associated documents from blob storage
        for doc in current_participant.get("docs", []):
            try:
                await blob_db.delete_file(user_id, doc["path"])
            except Exception as e:
                logger.warning("Failed to delete document %s: %s", doc.get("id"), str(e))

        await cosmos_client.delete_participant(user_id, participant_id)
        logger.info("Successfully deleted participant: %s", participant_id)

        return {"deleted_id": participant_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting participant %s: %s", participant_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while deleting participant")


async def get_participant(participant_id: str, user_id: str) -> ParticipantResponse:
    """Get a specific Participant."""
    try:
        logger.info("Fetching participant with ID: %s for user: %s", participant_id, user_id)
        participant = await cosmos_client.get_participant(user_id, participant_id)

        if not participant:
            logger.error("Participant not found with ID: %s", participant_id)
            raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")

        logger.info("Successfully retrieved participant: %s", participant_id)
        return ParticipantResponse(**participant)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching participant %s: %s", participant_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving participant")


async def list_participants(user_id: str) -> dict:
    """List all Participants for a user."""
    try:
        logger.info("Fetching all participants for user: %s", user_id)
        participants_list = await cosmos_client.list_participants(user_id)

        logger.info("Successfully retrieved %d participants for user: %s", len(participants_list), user_id)
        return {"participants": participants_list}

    except Exception as e:
        logger.error("Error listing participants for user %s: %s", user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving participants")


async def list_participant_documents(participant_id: str, user_id: str) -> dict:
    """List all documents for a participant."""
    try:
        logger.info("Fetching documents for participant ID: %s", participant_id)
        participant = await cosmos_client.get_participant(user_id, participant_id)
        
        if not participant:
            logger.error("Participant not found with ID: %s", participant_id)
            raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")
        
        docs = participant.get('docs', [])
        logger.info("Successfully retrieved %d documents for participant: %s", len(docs), participant_id)
        return {"documents": docs}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing documents for participant %s: %s", participant_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving documents")


async def upload_participant_document(participant_id: str, user_id: str, file: UploadFile) -> dict:
    """Upload a document for a participant."""
    try:
        logger.info("Uploading document for participant ID: %s", participant_id)
        
        # Get current participant to check existence
        participant = await cosmos_client.get_participant(user_id, participant_id)
        if not participant:
            logger.error("Participant not found with ID: %s", participant_id)
            raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")
        
        # Upload file to blob storage
        doc_info = await blob_db.upload_file(file, user_id)
        
        # Update participant's docs array in Cosmos DB
        if 'docs' not in participant:
            participant['docs'] = []
            
        participant['docs'].append(doc_info)
        await cosmos_client.update_participant(user_id, participant_id, participant)
        
        logger.info("Successfully uploaded document for participant: %s", participant_id)
        return doc_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error uploading document for participant %s: %s", participant_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while uploading document")


async def delete_participant_document(participant_id: str, user_id: str, doc_id: str) -> dict:
    """Delete a document from a participant."""
    try:
        logger.info("Deleting document %s for participant ID: %s", doc_id, participant_id)
        
        # Get current participant to check existence
        participant = await cosmos_client.get_participant(user_id, participant_id)
        if not participant:
            logger.error("Participant not found with ID: %s", participant_id)
            raise HTTPException(status_code=404, detail=f"Participant with ID '{participant_id}' not found")
        
        # Find and remove the document from the docs array
        docs = participant.get('docs', [])
        doc_to_delete = None
        updated_docs = []
        
        for doc in docs:
            if doc.get('id') == doc_id:
                doc_to_delete = doc
            else:
                updated_docs.append(doc)
                
        if not doc_to_delete:
            logger.error("Document %s not found for participant %s", doc_id, participant_id)
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Delete from blob storage
        await blob_db.delete_file(user_id, doc_to_delete['path'])
        
        # Update participant in Cosmos DB
        participant['docs'] = updated_docs
        await cosmos_client.update_participant(user_id, participant_id, participant)
        
        logger.info("Successfully deleted document %s for participant: %s", doc_id, participant_id)
        return {"deleted_id": doc_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting document for participant %s: %s", participant_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while deleting document")
