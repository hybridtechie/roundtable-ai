from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from logger_config import setup_logger
from auth import UserClaims, validate_token
from features.participant import create_participant, get_participant, update_participant, delete_participant, list_participants, ParticipantCreate, ParticipantUpdate
from models import ParticipantResponse, ListParticipantsResponse, DeleteResponse

logger = setup_logger(__name__)

router = APIRouter(prefix="/participant", tags=["Participants"])


@router.post("", response_model=ParticipantResponse, status_code=201, summary="Create a new participant")
async def create_participant_endpoint(participant: ParticipantCreate, current_user: UserClaims = Depends(validate_token)):

    try:
        logger.info("Attempting to create new participant: %s", participant.name)
        created_participant = await create_participant(participant)
        logger.info("Successfully created participant ID: %s Name: %s", created_participant.id, created_participant.name)
        return created_participant
    except Exception as e:
        logger.error("Failed to create participant '%s': %s", participant.name, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create participant: {str(e)}")


@router.get("s", response_model=ListParticipantsResponse, summary="List participants for a specific user")
async def list_participants_endpoint(current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        logger.info("Fetching all participants for user: %s", user_id)
        result = await list_participants(user_id)
        logger.info("Successfully retrieved %d participants for user: %s", len(result.get("participants", [])), user_id)
        return result
    except Exception as e:
        logger.error("Failed to fetch participants for user %s: %s", user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch participants: {str(e)}")


@router.get("/{participant_id}", response_model=ParticipantResponse, summary="Get a specific participant")
async def get_participant_endpoint(participant_id: str, current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        logger.info("Fetching participant: %s for user: %s", participant_id, user_id)
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


@router.put("/{participant_id}", response_model=ParticipantResponse, summary="Update an existing participant")
async def update_participant_endpoint(participant_id: str, participant: ParticipantUpdate, current_user: UserClaims = Depends(validate_token)):
    try:
        participant.user_id = current_user.email
        logger.info("Attempting to update participant: %s", participant_id)
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


@router.delete("/{participant_id}", response_model=DeleteResponse, summary="Delete a participant")
async def delete_participant_endpoint(participant_id: str, current_user: UserClaims = Depends(validate_token)):
    try:
        user_id = current_user.email
        logger.info("Attempting to delete participant: %s for user: %s", participant_id, user_id)
        result = await delete_participant(participant_id, user_id)
        logger.info("Successfully deleted participant: %s by user %s", participant_id, user_id)
        return result
    except Exception as e:
        logger.error("Failed to delete participant %s for user %s: %s", participant_id, user_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete participant: {str(e)}")
