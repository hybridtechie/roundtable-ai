from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from logger_config import setup_logger

# Feature imports
from features.participant import create_participant, get_participant, update_participant, delete_participant, list_participants, ParticipantCreate, ParticipantUpdate

# Model imports
# Use absolute import from 'backend' directory perspective
from models import ParticipantResponse, ListParticipantsResponse, DeleteResponse

# Auth imports (Optional - Consider adding Depends(validate_token) for user-specific actions)
# from ..auth import UserClaims, validate_token

# Logger setup
logger = setup_logger(__name__)

# Create an APIRouter instance
router = APIRouter(prefix="/participant", tags=["Participants"])  # Prefix for all routes in this router  # Tag for OpenAPI documentation

# --- Participant Endpoints ---
# Note: These endpoints currently rely on user_id passed as a query parameter.
# Consider refactoring to use Depends(validate_token) to get the authenticated user's ID
# for enhanced security and consistency, especially for list, get, delete operations.


# 01 Create Participant
@router.post("", response_model=ParticipantResponse, status_code=201, summary="Create a new participant")  # Route is POST /participant
async def create_participant_endpoint(participant: ParticipantCreate):
    """
    Creates a new participant profile.
    Requires participant details in the request body.
    Currently does not enforce user ownership via token, relies on user_id in ParticipantCreate.
    """
    # Consider adding user_id validation/assignment here if needed based on auth
    # user_id = current_user.email # Example if using Depends(validate_token)
    # participant.user_id = user_id
    try:
        logger.info("Attempting to create new participant: %s", participant.name)
        # The feature function returns the created participant object
        created_participant = await create_participant(participant)
        logger.info("Successfully created participant ID: %s Name: %s", created_participant.id, created_participant.name)
        return created_participant
    except Exception as e:
        logger.error("Failed to create participant '%s': %s", participant.name, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create participant: {str(e)}")


# 02 List Participants
@router.get("s", response_model=ListParticipantsResponse, summary="List participants for a specific user")  # Route is GET /participants
async def list_participants_endpoint(user_id: str = Query(..., description="The ID of the user whose participants to list")):
    """
    Retrieves a list of participants associated with a specific user ID.
    Requires `user_id` as a query parameter.
    Note: Consider using authentication to fetch participants for the *logged-in* user instead.
    """
    try:
        logger.info("Fetching all participants for user: %s", user_id)
        # The feature function returns a dict {"participants": [...]}
        result = await list_participants(user_id)
        logger.info("Successfully retrieved %d participants for user: %s", len(result.get("participants", [])), user_id)
        return result
    except Exception as e:
        logger.error("Failed to fetch participants for user %s: %s", user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch participants: {str(e)}")


# 03 Get Participant
@router.get("/{participant_id}", response_model=ParticipantResponse, summary="Get a specific participant")
async def get_participant_endpoint(participant_id: str, user_id: str = Query(..., description="The ID of the user owner")):
    """
    Retrieves details for a specific participant by their ID, verifying user ownership.
    Requires `participant_id` in the path and `user_id` as a query parameter.
    Note: Consider using authentication to verify ownership against the logged-in user.
    """
    try:
        logger.info("Fetching participant: %s for user: %s", participant_id, user_id)
        # The feature function returns the participant object directly or None
        participant = await get_participant(participant_id, user_id)
        if participant is None:
            logger.warning("Participant %s not found for user %s", participant_id, user_id)
            raise HTTPException(status_code=404, detail="Participant not found or access denied")
        logger.info("Successfully retrieved participant: %s", participant_id)
        return participant
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to fetch participant %s for user %s: %s", participant_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch participant: {str(e)}")


# 04 Update Participant
@router.put("/{participant_id}", response_model=ParticipantResponse, summary="Update an existing participant")
async def update_participant_endpoint(participant_id: str, participant: ParticipantUpdate):
    """
    Updates an existing participant's details.
    Requires `participant_id` in the path and update data in the request body.
    Note: Currently does not explicitly check user ownership via token. The `update_participant`
    feature function might handle this internally, or it should be added here using authentication.
    """
    # Consider adding user_id check:
    # user_id = current_user.email # Example if using Depends(validate_token)
    # Add logic to verify participant_id belongs to user_id before updating
    try:
        logger.info("Attempting to update participant: %s", participant_id)
        # The feature function returns the updated participant object or None
        updated_participant = await update_participant(participant_id, participant)
        if updated_participant is None:
            logger.warning("Update failed for participant %s. Not found or error.", participant_id)
            raise HTTPException(status_code=404, detail="Participant not found or update failed")
        logger.info("Successfully updated participant: %s", participant_id)
        return updated_participant
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error("Failed to update participant %s: %s", participant_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update participant: {str(e)}")


# 05 Delete Participant
@router.delete("/{participant_id}", response_model=DeleteResponse, summary="Delete a participant")
async def delete_participant_endpoint(participant_id: str, user_id: str = Query(..., description="The ID of the user owner")):
    """
    Deletes a participant by their ID, verifying user ownership.
    Requires `participant_id` in the path and `user_id` as a query parameter.
    Note: Consider using authentication to verify ownership against the logged-in user.
    """
    try:
        logger.info("Attempting to delete participant: %s for user: %s", participant_id, user_id)
        # The feature function returns {"deleted_id": participant_id} or raises/returns None
        result = await delete_participant(participant_id, user_id)
        # Add check if deletion failed (e.g., participant not found for user)
        # if result is None:
        #     raise HTTPException(status_code=404, detail="Participant not found or cannot be deleted")
        logger.info("Successfully deleted participant: %s by user %s", participant_id, user_id)
        return result  # Should match DeleteResponse model
    except Exception as e:
        logger.error("Failed to delete participant %s for user %s: %s", participant_id, user_id, str(e), exc_info=True)
        # Determine if 404 or 500 is more appropriate based on expected errors
        raise HTTPException(status_code=500, detail=f"Failed to delete participant: {str(e)}")
