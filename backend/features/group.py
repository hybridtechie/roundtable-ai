from fastapi import HTTPException
from pydantic import BaseModel, Field
import sqlite3
from uuid import uuid4
from typing import Optional, List
import json
from db import collection  # Import ChromaDB collection
from logger_config import setup_logger

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
    userId: str = Field(default="SuperAdmin", min_length=1)


class GroupCreate(GroupBase):
    id: Optional[str] = None
    context: Optional[str] = None


class GroupUpdate(GroupBase):
    pass


async def create_group(group: GroupCreate):
    """Create a new Group in SQLite and optionally store its context in ChromaDB."""
    logger.info("Creating new group with name: %s", group.name)

    # Validate all required fields
    validate_group_data(group.name, group.description, group.participant_ids)

    # Generate UUID if id not provided
    if group.id is None:
        group.id = str(uuid4())
        logger.debug("Generated new UUID for group: %s", group.id)

    conn = None
    try:
        conn = sqlite3.connect("roundtableai.db")
        cursor = conn.cursor()

        # Validate all participant IDs exist
        for participant_id in group.participant_ids:
            cursor.execute("SELECT id FROM participants WHERE id = ?", (participant_id,))
            if not cursor.fetchone():
                logger.error("Participant not found: %s", participant_id)
                raise HTTPException(status_code=404, detail=f"Participant ID '{participant_id}' not found")

        participant_ids_json = json.dumps(group.participant_ids)

        cursor.execute(
            "INSERT INTO groups (id, name, description, participant_ids, userId) VALUES (?, ?, ?, ?, ?)",
            (group.id, group.name, group.description, participant_ids_json, group.userId),
        )

        # Store context in ChromaDB if provided
        if group.context:
            try:
                collection.add(documents=[group.context], ids=[group.id])
                logger.info("Successfully added group context to ChromaDB: %s", group.id)
            except Exception as e:
                logger.error("Failed to add group context to ChromaDB: %s - Error: %s", group.id, str(e), exc_info=True)
                cursor.execute("DELETE FROM groups WHERE id = ?", (group.id,))
                conn.commit()
                raise HTTPException(status_code=500, detail="Failed to store group context in vector database")

        conn.commit()
        logger.info("Successfully created group: %s", group.id)
        return {"message": f"Group '{group.name}' with ID '{group.id}' created successfully"}

    except sqlite3.IntegrityError as e:
        logger.error("SQLite integrity error while creating group: %s - Error: %s", group.id, str(e), exc_info=True)
        raise HTTPException(status_code=400, detail=f"Group ID '{group.id}' already exists")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error("Unexpected error while creating group: %s - Error: %s", group.id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while creating group")
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")


async def update_group(group_id: str, group: GroupUpdate):
    """Update a Group in SQLite."""
    conn = None
    try:
        logger.info("Updating group with ID: %s", group_id)
        conn = sqlite3.connect("roundtableai.db")
        cursor = conn.cursor()

        # Check if group exists
        cursor.execute("SELECT 1 FROM groups WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            logger.error("Group not found with ID: %s", group_id)
            raise HTTPException(status_code=404, detail=f"Group with ID '{group_id}' not found")

        # Validate all participant IDs exist
        for participant_id in group.participant_ids:
            cursor.execute("SELECT id FROM participants WHERE id = ?", (participant_id,))
            if not cursor.fetchone():
                logger.error("Participant not found: %s", participant_id)
                raise HTTPException(status_code=404, detail=f"Participant ID '{participant_id}' not found")

        participant_ids_json = json.dumps(group.participant_ids)

        cursor.execute(
            "UPDATE groups SET name = ?, description = ?, participant_ids = ?, userId = ? WHERE id = ?",
            (group.name, group.description, participant_ids_json, group.userId, group_id),
        )

        conn.commit()
        logger.info("Successfully updated group: %s", group_id)
        return {"message": f"Group with ID '{group_id}' updated successfully"}

    except sqlite3.Error as e:
        logger.error("Database error while updating group %s: %s", group_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to update group in database")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error("Unexpected error while updating group %s: %s", group_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error while updating group")
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")


async def delete_group(group_id: str):
    """Delete a Group from SQLite and ChromaDB."""
    conn = None
    try:
        logger.info("Deleting group with ID: %s", group_id)
        conn = sqlite3.connect("roundtableai.db")
        cursor = conn.cursor()

        # Check if group exists
        cursor.execute("SELECT 1 FROM groups WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            logger.error("Group not found with ID: %s", group_id)
            raise HTTPException(status_code=404, detail=f"Group with ID '{group_id}' not found")

        # Delete from SQLite
        cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))

        # Delete from ChromaDB
        try:
            collection.delete(ids=[group_id])
            logger.info("Successfully deleted group context from ChromaDB: %s", group_id)
        except Exception as e:
            logger.error("Failed to delete group context from ChromaDB: %s - Error: %s", group_id, str(e))
            # Continue with deletion even if ChromaDB fails

        conn.commit()
        logger.info("Successfully deleted group: %s", group_id)
        return {"message": f"Group with ID '{group_id}' deleted successfully"}

    except sqlite3.Error as e:
        logger.error("Database error while deleting group %s: %s", group_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to delete group from database")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error("Unexpected error while deleting group %s: %s", group_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error while deleting group")
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")


async def get_group(group_id: str):
    """Get a specific Group from SQLite with expanded participant details."""
    conn = None
    try:
        logger.info("Fetching group with ID: %s", group_id)
        conn = sqlite3.connect("roundtableai.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, description, participant_ids, userId FROM groups WHERE id = ?", (group_id,))
        row = cursor.fetchone()

        if not row:
            logger.error("Group not found with ID: %s", group_id)
            raise HTTPException(status_code=404, detail=f"Group with ID '{group_id}' not found")

        participant_ids = json.loads(row[3])
        participants = []

        # Fetch participant details
        for participant_id in participant_ids:
            cursor.execute("SELECT id, name, role FROM participants WHERE id = ?", (participant_id,))
            participant = cursor.fetchone()
            if participant:
                participants.append({"id": participant[0], "name": participant[1], "role": participant[2]})

        # Get context from ChromaDB if available
        try:
            context_result = collection.get(ids=[group_id])
            context = context_result["documents"][0] if context_result["documents"] else ""
        except Exception as e:
            logger.error("Failed to fetch context from ChromaDB for group %s: %s", group_id, str(e))
            context = ""

        group = {"id": row[0], "name": row[1], "description": row[2], "userId": row[4], "participant_ids": participant_ids, "participants": participants, "context": context}

        logger.info("Successfully retrieved group: %s", group_id)
        return group

    except sqlite3.Error as e:
        logger.error("Database error while fetching group %s: %s", group_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve group from database")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error("Unexpected error while fetching group %s: %s", group_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error while retrieving group")
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")


async def list_groups():
    """List all Groups from SQLite with expanded participant details."""
    conn = None
    try:
        logger.info("Fetching all groups with participant details")
        conn = sqlite3.connect("roundtableai.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, description, participant_ids, userId FROM groups")
        groups_raw = cursor.fetchall()
        logger.debug("Retrieved %d groups from database", len(groups_raw))

        groups_data = []
        for row in groups_raw:
            try:
                participant_ids = json.loads(row[3])
                group = {"id": row[0], "name": row[1], "description": row[2], "userId": row[4], "participant_ids": participant_ids, "participants": []}

                # Fetch participant details for each participant_id
                for participant_id in participant_ids:
                    cursor.execute("SELECT id, name, role FROM participants WHERE id = ?", (participant_id,))
                    participant = cursor.fetchone()
                    if participant:
                        group["participants"].append({"participant_id": participant[0], "name": participant[1], "role": participant[2]})
                    else:
                        logger.warning("Participant %s not found for group %s", participant_id, group["id"])

                groups_data.append(group)

            except json.JSONDecodeError as e:
                logger.error("Failed to parse participant_ids JSON for group %s: %s", row[0], str(e), exc_info=True)
                continue

        logger.info("Successfully retrieved %d groups with participant details", len(groups_data))
        return {"groups": groups_data}

    except sqlite3.Error as e:
        logger.error("Database error while fetching groups: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve groups from database")
    except Exception as e:
        logger.error("Unexpected error while fetching groups: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving groups")
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")
