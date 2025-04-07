from fastapi import HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4
from typing import Optional, List
import json
from logger_config import setup_logger
from cosmos_db import cosmos_client

# Set up logger
logger = setup_logger(__name__)


def validate_group_data(name: str, description: str, participant_ids: List[str]) -> None:
    """Validate group data before creation."""
    try:
        if not name or not name.strip():
            logger.error("Validation failed: Name is empty or whitespace")
            raise HTTPException(status_code=400, detail="Name is required")
        if not description or not description.strip():
            logger.error("Validation failed: Description is empty or whitespace")
            raise HTTPException(status_code=400, detail="Description is required")
        if not participant_ids:
            logger.error("Validation failed: No participant IDs provided")
            raise HTTPException(status_code=400, detail="At least one participant is required")
        if len(name) > 100:
            logger.error("Validation failed: Name length exceeds 100 characters")
            raise HTTPException(status_code=400, detail="Name must be less than 100 characters")
        if len(description) > 1000:
            logger.error("Validation failed: Description length exceeds 1000 characters")
            raise HTTPException(status_code=400, detail="Description must be less than 1000 characters")

        logger.debug("Group data validation successful")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during group validation: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during validation")


class GroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    participant_ids: List[str]
    user_id: str = Field(default="roundtable_ai_admin", min_length=1)


class GroupCreate(GroupBase):
    id: Optional[str] = None
    context: Optional[str] = None


class GroupUpdate(GroupBase):
    pass


async def create_group(group: GroupCreate):
    """Create a new Group."""
    logger.info("Creating new group with name: %s", group.name)

    # Validate all required fields
    validate_group_data(group.name, group.description, group.participant_ids)

    # Generate UUID if id not provided
    if group.id is None:
        group.id = str(uuid4())
        logger.debug("Generated new UUID for group: %s", group.id)

    try:
        # Validate all participant IDs exist
        for participant_id in group.participant_ids:
            participant = await cosmos_client.get_participant(group.user_id, participant_id)
            if not participant:
                logger.error("Participant not found: %s", participant_id)
                raise HTTPException(status_code=404, detail=f"Participant ID '{participant_id}' not found")

        # Store the group data in Cosmos DB
        group_data = {"id": group.id, "name": group.name, "description": group.description, "participant_ids": group.participant_ids, "user_id": group.user_id}

        if group.context:
            group_data["context"] = group.context

        await cosmos_client.add_group(group.user_id, group_data)
        logger.info("Successfully created group: %s", group.id)
        return {"message": f"Group '{group.name}' with ID '{group.id}' created successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating group: %s - Error: %s", group.id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while creating group")


async def update_group(group_id: str, group: GroupUpdate):
    """Update a Group."""
    try:
        logger.info("Updating group with ID: %s", group_id)

        # Check if group exists
        existing_group = await cosmos_client.get_group(group.user_id, group_id)
        if not existing_group:
            logger.error("Group not found with ID: %s", group_id)
            raise HTTPException(status_code=404, detail=f"Group with ID '{group_id}' not found")

        # Validate all participant IDs exist
        for participant_id in group.participant_ids:
            participant = await cosmos_client.get_participant(group.user_id, participant_id)
            if not participant:
                logger.error("Participant not found: %s", participant_id)
                raise HTTPException(status_code=404, detail=f"Participant ID '{participant_id}' not found")

        # Update group data
        group_data = {"id": group_id, "name": group.name, "description": group.description, "participant_ids": group.participant_ids, "user_id": group.user_id}

        await cosmos_client.update_group(group.user_id, group_id, group_data)
        logger.info("Successfully updated group: %s", group_id)
        return {"message": f"Group with ID '{group_id}' updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating group %s: %s", group_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error while updating group")


async def delete_group(group_id: str, user_id: str):
    """Delete a Group."""
    try:
        logger.info("Deleting group with ID: %s", group_id)

        # Check if group exists
        existing_group = await cosmos_client.get_group(user_id, group_id)
        if not existing_group:
            logger.error("Group not found with ID: %s", group_id)
            raise HTTPException(status_code=404, detail=f"Group with ID '{group_id}' not found")

        await cosmos_client.delete_group(user_id, group_id)
        logger.info("Successfully deleted group: %s", group_id)
        return {"message": f"Group with ID '{group_id}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting group %s: %s", group_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error while deleting group")


async def get_group(group_id: str, user_id: str):
    """Get a specific Group with expanded participant details."""
    try:
        logger.info("Fetching group with ID: %s", group_id)

        group = await cosmos_client.get_group(user_id, group_id)
        if not group:
            logger.error("Group not found with ID: %s", group_id)
            raise HTTPException(status_code=404, detail=f"Group with ID '{group_id}' not found")

        # Fetch participant details
        participants = []
        for participant_id in group.get("participant_ids", []):
            participant = await cosmos_client.get_participant(user_id, participant_id)
            if participant:
                participants.append({"id": participant.get("id"), "name": participant.get("name"), "role": participant.get("role")})

        group["participants"] = participants
        logger.info("Successfully retrieved group: %s", group_id)
        return group

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching group %s: %s", group_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error while retrieving group")


async def list_groups(user_id: str):
    """List all Groups with expanded participant details."""
    try:
        logger.info("Fetching all groups with participant details")

        groups = await cosmos_client.list_groups(user_id)
        groups_data = []

        for group in groups:
            participants = []
            for participant_id in group.get("participant_ids", []):
                participant = await cosmos_client.get_participant(user_id, participant_id)
                if participant:
                    participants.append({"participant_id": participant.get("id"), "name": participant.get("name"), "role": participant.get("role")})
                else:
                    logger.warning("Participant %s not found for group %s", participant_id, group.get("id"))

            group_data = {
                "id": group.get("id"),
                "name": group.get("name"),
                "description": group.get("description"),
                "user_id": group.get("user_id"),
                "participant_ids": group.get("participant_ids", []),
                "participants": participants,
            }
            groups_data.append(group_data)

        logger.info("Successfully retrieved %d groups with participant details", len(groups_data))
        return {"groups": groups_data}

    except Exception as e:
        logger.error("Error listing groups: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving groups")
